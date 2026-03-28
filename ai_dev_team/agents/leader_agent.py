"""Leader Agent – the project manager that orchestrates all other agents."""

from __future__ import annotations

import logging
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import (
    MessageBus,
)
from ai_dev_team.core.task_manager import Task, TaskManager, TaskStatus
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.planner.task_planner import TaskPlanner

logger = logging.getLogger(__name__)


class LeaderAgent(AgentBase):
    """Project-manager agent responsible for planning, delegation, and validation.

    Workflow
    --------
    1. Receive a natural-language request from the user.
    2. Use the ``TaskPlanner`` to decompose it into subtasks.
    3. Dispatch each subtask to the appropriate specialist agent.
    4. Collect outputs, validate, and merge into a final project.
    """

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        task_manager: TaskManager,
        memory: MemoryManager,
        agents: dict[str, AgentBase] | None = None,
    ) -> None:
        super().__init__(
            name="leader_agent",
            role="project_manager",
            config=config,
            message_bus=message_bus,
        )
        self.task_manager = task_manager
        self.memory = memory
        self.planner = TaskPlanner(task_manager)
        self._agents: dict[str, AgentBase] = agents or {}

    def register_agent(self, agent: AgentBase) -> None:
        """Add a specialist agent to the team."""
        self._agents[agent.name] = agent
        self._logger.info("Registered agent: %s (%s)", agent.name, agent.role)

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    async def handle_request(self, user_request: str) -> dict[str, Any]:
        """End-to-end pipeline: plan -> dispatch -> collect -> validate."""
        self._logger.info("Received user request: %s", user_request[:120])
        self.memory.remember("user_request", user_request, category="request")

        # 1. Plan
        tasks = self.planner.create_plan(user_request)
        plan_summary = self.planner.describe_plan(tasks)
        self._logger.info("Plan created:\n%s", plan_summary)

        # 2. Execute tasks in dependency order
        results: dict[str, Any] = {}
        max_iterations = len(tasks) * (self.config.max_retries + 1)
        iteration = 0

        while True:
            iteration += 1
            if iteration > max_iterations:
                self._logger.warning("Max iterations reached – stopping.")
                break

            ready = self.task_manager.ready_tasks()
            if not ready:
                # Nothing pending & ready – either all done or blocked
                pending = self.task_manager.get_tasks_by_status(TaskStatus.PENDING)
                if not pending:
                    break  # all tasks processed
                # Some tasks still pending but blocked on deps – might be failed deps
                blocked = [
                    t for t in pending if not self.task_manager.all_dependencies_met(t)
                ]
                if blocked:
                    self._logger.warning(
                        "%d tasks blocked on unmet dependencies", len(blocked)
                    )
                    break
                continue

            for task in ready:
                agent = self._agents.get(task.assigned_to or "")
                if agent is None:
                    task.mark_failed(f"No agent registered as '{task.assigned_to}'")
                    continue

                # Provide context from memory
                context = self.memory.build_context(task.description)
                task.artifacts["context"] = context

                completed_task = await agent.run(task)
                results[completed_task.task_id] = completed_task.to_dict()

                # Store result in memory for downstream tasks
                if completed_task.status == TaskStatus.COMPLETED:
                    self.memory.remember(
                        key=completed_task.title,
                        value=completed_task.result,
                        category="task_result",
                    )

        # 3. Validate
        summary = self.task_manager.summary()
        self._logger.info("Project summary: %s", summary)

        return {
            "plan": plan_summary,
            "task_summary": summary,
            "tasks": results,
        }

    # ------------------------------------------------------------------
    # AgentBase interface (used if the leader itself gets a sub-task)
    # ------------------------------------------------------------------

    async def analyze(self, task: Task) -> dict[str, Any]:
        return {"request": task.description}

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"action": "delegate", "detail": task.description}]

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        result = await self.handle_request(task.description)
        return {"summary": "Project completed", **result}

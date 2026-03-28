"""Base class for all AI agents in the system."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.communication_protocol import (
    AgentMessage,
    MessageBus,
    MessagePriority,
    MessageType,
)
from ai_dev_team.core.task_manager import Task

logger = logging.getLogger(__name__)


class AgentBase(ABC):
    """Abstract base every specialised agent inherits from.

    Lifecycle:
        1. ``receive_task``   – accept a Task from the leader / dispatcher
        2. ``analyze``        – understand what needs to be done
        3. ``plan``           – decide on the steps
        4. ``execute``        – carry out the work using tools
        5. ``report``         – send the result back
    """

    def __init__(
        self,
        name: str,
        role: str,
        config: ProjectConfig,
        message_bus: MessageBus,
    ) -> None:
        self.name = name
        self.role = role
        self.config = config
        self.message_bus = message_bus
        self._logger = logging.getLogger(f"agent.{name}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run(self, task: Task) -> Task:
        """Execute the full agent loop for a single task."""
        self._logger.info("[%s] Starting task: %s", self.name, task.title)
        task.mark_in_progress()

        try:
            analysis = await self.analyze(task)
            plan = await self.plan(task, analysis)
            result = await self.execute(task, plan)
            task.mark_completed(result=result.get("summary", "done"), artifacts=result)
            self._logger.info("[%s] Completed task: %s", self.name, task.title)
        except Exception as exc:
            task.mark_failed(str(exc))
            self._logger.exception("[%s] Task failed: %s", self.name, task.title)

        return task

    # ------------------------------------------------------------------
    # Steps – subclasses must implement these
    # ------------------------------------------------------------------

    @abstractmethod
    async def analyze(self, task: Task) -> dict[str, Any]:
        """Understand what the task requires."""

    @abstractmethod
    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Produce an ordered list of action steps."""

    @abstractmethod
    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute the plan and return artifacts."""

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    def send_message(
        self,
        receiver: str,
        content: str,
        message_type: MessageType = MessageType.STATUS_UPDATE,
        priority: MessagePriority = MessagePriority.MEDIUM,
        task_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentMessage:
        msg = AgentMessage(
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority,
            task_id=task_id,
            context=context or {},
        )
        self.message_bus.send(msg)
        return msg

    def get_messages(self) -> list[AgentMessage]:
        return self.message_bus.receive(self.name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} role={self.role!r}>"

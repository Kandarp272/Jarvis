"""Task planner that breaks user requests into an executable task graph."""

from __future__ import annotations

import logging

from ai_dev_team.core.task_manager import Task, TaskManager

logger = logging.getLogger(__name__)

# Default plan templates for common project types
PLAN_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "web_api": [
        {"title": "Research frameworks and best practices", "agent": "research_agent"},
        {"title": "Design system architecture", "agent": "architect_agent"},
        {"title": "Implement backend API", "agent": "coder_agent"},
        {"title": "Write unit tests", "agent": "tester_agent"},
        {"title": "Debug and fix issues", "agent": "debug_agent"},
        {"title": "Generate documentation", "agent": "doc_agent"},
    ],
    "full_stack": [
        {"title": "Research frameworks and best practices", "agent": "research_agent"},
        {"title": "Design system architecture", "agent": "architect_agent"},
        {"title": "Implement backend API", "agent": "coder_agent"},
        {"title": "Implement frontend UI", "agent": "coder_agent"},
        {"title": "Write unit tests", "agent": "tester_agent"},
        {"title": "Debug and fix issues", "agent": "debug_agent"},
        {"title": "Generate documentation", "agent": "doc_agent"},
    ],
    "library": [
        {"title": "Research existing solutions", "agent": "research_agent"},
        {"title": "Design module architecture", "agent": "architect_agent"},
        {"title": "Implement core library", "agent": "coder_agent"},
        {"title": "Write tests", "agent": "tester_agent"},
        {"title": "Generate documentation", "agent": "doc_agent"},
    ],
    "generic": [
        {"title": "Research and gather context", "agent": "research_agent"},
        {"title": "Design architecture", "agent": "architect_agent"},
        {"title": "Implement solution", "agent": "coder_agent"},
        {"title": "Write tests", "agent": "tester_agent"},
        {"title": "Generate documentation", "agent": "doc_agent"},
    ],
}


class TaskPlanner:
    """Analyses a user request and creates an ordered task graph.

    The planner can work in two modes:

    1. **Template mode** – selects a pre-built plan template based on
       keyword matching (fast, no LLM call needed).
    2. **LLM mode** – asks an LLM to decompose the request into subtasks
       (richer, requires a configured model).
    """

    def __init__(self, task_manager: TaskManager) -> None:
        self.task_manager = task_manager

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_plan(
        self,
        user_request: str,
        project_type: str | None = None,
    ) -> list[Task]:
        """Break *user_request* into ordered tasks and register them."""
        ptype = project_type or self._detect_project_type(user_request)
        template = PLAN_TEMPLATES.get(ptype, PLAN_TEMPLATES["generic"])

        logger.info("Creating plan for project type: %s (%d steps)", ptype, len(template))

        tasks: list[Task] = []
        prev_id: str | None = None

        for step in template:
            deps = [prev_id] if prev_id else []
            task = self.task_manager.create_task(
                title=step["title"],
                description=f"{step['title']} for: {user_request}",
                assigned_to=step["agent"],
                dependencies=deps,
            )
            tasks.append(task)
            prev_id = task.task_id

        return tasks

    def create_custom_plan(
        self,
        steps: list[dict[str, str]],
        user_request: str,
    ) -> list[Task]:
        """Create a plan from an LLM-generated step list."""
        tasks: list[Task] = []
        prev_id: str | None = None

        for step in steps:
            deps_raw = step.get("dependencies", "")
            deps: list[str] = []
            if deps_raw:
                deps = [d.strip() for d in str(deps_raw).split(",") if d.strip()]
            elif prev_id:
                deps = [prev_id]

            task = self.task_manager.create_task(
                title=step.get("title", "Untitled task"),
                description=step.get("description", user_request),
                assigned_to=step.get("agent", "coder_agent"),
                dependencies=deps,
            )
            tasks.append(task)
            prev_id = task.task_id

        return tasks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_project_type(request: str) -> str:
        """Simple keyword heuristic to pick a plan template."""
        lower = request.lower()

        if any(kw in lower for kw in ("api", "rest", "endpoint", "backend", "server")):
            if any(kw in lower for kw in ("frontend", "react", "vue", "ui", "full")):
                return "full_stack"
            return "web_api"

        if any(kw in lower for kw in ("library", "package", "module", "sdk")):
            return "library"

        if any(kw in lower for kw in ("frontend", "react", "vue", "angular", "webapp")):
            return "full_stack"

        return "generic"

    def describe_plan(self, tasks: list[Task]) -> str:
        """Return a human-readable summary of the plan."""
        lines = [f"## Project Plan ({len(tasks)} tasks)\n"]
        for idx, task in enumerate(tasks, 1):
            lines.append(
                f"{idx}. **{task.title}** -> `{task.assigned_to}` "
                f"(deps: {task.dependencies or 'none'})"
            )
        return "\n".join(lines)

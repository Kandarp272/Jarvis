"""Architect Agent – designs system architecture and project structure."""

from __future__ import annotations

import json
import logging
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import Task
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.file_manager import FileManager

logger = logging.getLogger(__name__)

# Architecture templates keyed by project type
ARCHITECTURE_TEMPLATES: dict[str, dict[str, Any]] = {
    "web_api": {
        "structure": {
            "app/": {
                "__init__.py": "",
                "main.py": "# FastAPI application entry point",
                "models/": {"__init__.py": ""},
                "routes/": {"__init__.py": ""},
                "services/": {"__init__.py": ""},
                "schemas/": {"__init__.py": ""},
            },
            "tests/": {"__init__.py": "", "test_main.py": ""},
            "requirements.txt": "",
        },
        "framework": "FastAPI",
        "database": "SQLite",
        "description": "RESTful API with FastAPI, SQLAlchemy ORM, Pydantic schemas",
    },
    "full_stack": {
        "structure": {
            "backend/": {
                "app/": {
                    "__init__.py": "",
                    "main.py": "",
                    "models/": {"__init__.py": ""},
                    "routes/": {"__init__.py": ""},
                    "services/": {"__init__.py": ""},
                },
                "requirements.txt": "",
            },
            "frontend/": {
                "src/": {"App.tsx": "", "index.tsx": ""},
                "package.json": "",
            },
            "tests/": {"__init__.py": ""},
        },
        "framework": "FastAPI + React",
        "database": "PostgreSQL",
        "description": "Full-stack app with FastAPI backend and React frontend",
    },
    "library": {
        "structure": {
            "src/": {"__init__.py": ""},
            "tests/": {"__init__.py": ""},
            "docs/": {},
            "setup.py": "",
            "README.md": "",
        },
        "framework": "Python package",
        "database": "None",
        "description": "Reusable Python library with tests and docs",
    },
}


class ArchitectAgent(AgentBase):
    """Designs the high-level architecture and scaffolds the project."""

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        file_manager: FileManager | None = None,
    ) -> None:
        super().__init__(
            name="architect_agent",
            role="architect",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.file_manager = file_manager

    async def analyze(self, task: Task) -> dict[str, Any]:
        project_type = self._detect_type(task.description)
        template = ARCHITECTURE_TEMPLATES.get(
            project_type, ARCHITECTURE_TEMPLATES["web_api"]
        )
        return {
            "project_type": project_type,
            "template": template,
        }

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        template = analysis["template"]
        steps: list[dict[str, Any]] = [
            {"action": "design", "detail": "Finalise architecture document"},
            {"action": "scaffold", "structure": template["structure"]},
        ]
        return steps

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        architecture_doc = ""
        created_files: list[str] = []

        for step in plan:
            if step["action"] == "design":
                architecture_doc = self._generate_architecture_doc(task, plan)
            elif step["action"] == "scaffold" and self.file_manager:
                created_files = self._scaffold(step["structure"])

        self.memory.store_long_term(
            doc_id=f"architecture-{task.task_id}",
            text=architecture_doc,
            metadata={"task": task.title, "type": "architecture"},
        )

        return {
            "summary": "Architecture designed and project scaffolded",
            "architecture": architecture_doc,
            "files_created": created_files,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _scaffold(
        self,
        structure: dict[str, Any],
        prefix: str = "",
    ) -> list[str]:
        """Recursively create directories and files from a template dict."""
        created: list[str] = []
        if self.file_manager is None:
            return created

        for name, content in structure.items():
            path = f"{prefix}{name}" if prefix else name
            if isinstance(content, dict):
                # Directory
                dir_path = path.rstrip("/")
                self.file_manager.create_directory(dir_path)
                created.append(dir_path + "/")
                created.extend(self._scaffold(content, prefix=dir_path + "/"))
            else:
                # File
                self.file_manager.write_file(path, str(content))
                created.append(path)
        return created

    @staticmethod
    def _detect_type(description: str) -> str:
        lower = description.lower()
        if any(kw in lower for kw in ("api", "rest", "endpoint", "backend")):
            if any(kw in lower for kw in ("frontend", "react", "vue", "full")):
                return "full_stack"
            return "web_api"
        if any(kw in lower for kw in ("library", "package", "module", "sdk")):
            return "library"
        return "web_api"

    @staticmethod
    def _generate_architecture_doc(task: Task, plan: list[dict[str, Any]]) -> str:
        lines = [
            "# Architecture Design",
            "",
            f"## Project: {task.title}",
            "",
            f"**Description:** {task.description}",
            "",
            "## Components",
            "",
        ]

        for step in plan:
            if step["action"] == "scaffold":
                lines.append("### Project Structure")
                lines.append("```")
                lines.append(json.dumps(step.get("structure", {}), indent=2))
                lines.append("```")

        return "\n".join(lines)

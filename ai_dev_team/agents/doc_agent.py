"""Documentation Agent – generates READMEs, API docs, and architecture explanations."""

from __future__ import annotations

import logging
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import Task
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.file_manager import FileManager

logger = logging.getLogger(__name__)

README_TEMPLATE = '''# {title}

{description}

## Features

{features}

## Project Structure

```
{structure}
```

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Running the Application

```bash
uvicorn app.main:app --reload
```

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

{endpoints}

## Architecture

{architecture}

## License

MIT
'''


class DocAgent(AgentBase):
    """Generates project documentation: README, API docs, architecture guides."""

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        file_manager: FileManager | None = None,
    ) -> None:
        super().__init__(
            name="doc_agent",
            role="documentation",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.file_manager = file_manager

    async def analyze(self, task: Task) -> dict[str, Any]:
        """Collect information from memory and file system."""
        context = self.memory.build_context(task.description, max_items=20)
        source_files: list[str] = []
        if self.file_manager:
            source_files = self.file_manager.list_files(".")
        return {"context": context, "source_files": source_files}

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"action": "generate_readme"},
            {"action": "generate_api_docs"},
        ]

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        generated: list[str] = []

        for step in plan:
            if step["action"] == "generate_readme" and self.file_manager:
                readme = self._build_readme(task)
                self.file_manager.write_file("README.md", readme)
                generated.append("README.md")

            elif step["action"] == "generate_api_docs" and self.file_manager:
                api_doc = self._build_api_docs(task)
                self.file_manager.write_file("docs/API.md", api_doc)
                generated.append("docs/API.md")

        return {
            "summary": f"Generated {len(generated)} documentation files",
            "files": generated,
        }

    # ------------------------------------------------------------------
    # Generators
    # ------------------------------------------------------------------

    def _build_readme(self, task: Task) -> str:
        title = self._extract_title(task.description)
        tree = ""
        if self.file_manager:
            tree = self.file_manager.tree(".", max_depth=3)

        return README_TEMPLATE.format(
            title=title,
            description=task.description,
            features="- RESTful API\n- CRUD operations\n- Input validation\n- Error handling",
            structure=tree,
            endpoints=self._discover_endpoints(),
            architecture=self._architecture_summary(),
        )

    def _build_api_docs(self, task: Task) -> str:
        lines = [
            "# API Documentation",
            "",
            f"## {self._extract_title(task.description)}",
            "",
            "### Endpoints",
            "",
            self._discover_endpoints(),
            "",
            "### Error Handling",
            "",
            "All errors return JSON with `detail` field.",
            "",
            "| Status | Meaning |",
            "|--------|---------|",
            "| 200 | Success |",
            "| 201 | Created |",
            "| 204 | Deleted |",
            "| 404 | Not Found |",
            "| 422 | Validation Error |",
        ]
        return "\n".join(lines)

    def _discover_endpoints(self) -> str:
        """Scan route files to list endpoints."""
        endpoints = [
            "| Method | Path | Description |",
            "|--------|------|-------------|",
            "| GET | / | Root endpoint |",
            "| GET | /health | Health check |",
        ]
        if self.file_manager:
            route_files = [
                f for f in self.file_manager.list_files(".")
                if "routes" in f and f.endswith(".py") and "__init__" not in f
            ]
            for rf in route_files:
                entity = rf.rsplit("/", 1)[-1].replace(".py", "")
                endpoints.extend(
                    [
                        f"| GET | /{entity}s | List all {entity}s |",
                        f"| POST | /{entity}s | Create {entity} |",
                        f"| GET | /{entity}s/{{id}} | Get {entity} by ID |",
                        f"| PUT | /{entity}s/{{id}} | Update {entity} |",
                        f"| DELETE | /{entity}s/{{id}} | Delete {entity} |",
                    ]
                )
        return "\n".join(endpoints)

    def _architecture_summary(self) -> str:
        results = self.memory.search_long_term("architecture", n_results=1)
        if results:
            return results[0].get("text", "See project structure above.")
        return "See project structure above."

    @staticmethod
    def _extract_title(description: str) -> str:
        words = description.split()[:8]
        return " ".join(words).rstrip(".,;:")

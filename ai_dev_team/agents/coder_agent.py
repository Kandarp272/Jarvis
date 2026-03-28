"""Coding Agent – writes production code, implements features, creates APIs."""

from __future__ import annotations

import logging
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import Task
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.code_executor import CodeExecutor
from ai_dev_team.tools.file_manager import FileManager

logger = logging.getLogger(__name__)

# Code generation templates by project component
CODE_TEMPLATES: dict[str, str] = {
    "fastapi_main": '''"""Auto-generated FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{title}", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {{"message": "Welcome to {title}"}}


@app.get("/health")
async def health():
    return {{"status": "healthy"}}
''',
    "model": '''"""Database model for {entity}."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class {entity_class}(Base):
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
''',
    "schema": '''"""Pydantic schemas for {entity}."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class {entity_class}Base(BaseModel):
    title: str
    description: Optional[str] = None


class {entity_class}Create({entity_class}Base):
    pass


class {entity_class}Update(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class {entity_class}Response({entity_class}Base):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
''',
    "route": '''"""API routes for {entity}."""

from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/{route_prefix}", tags=["{entity}"])

# In-memory store (replace with database in production)
_store: dict[int, dict] = {{}}
_counter = 0


@router.get("/")
async def list_{route_prefix}():
    return list(_store.values())


@router.post("/", status_code=201)
async def create_{route_prefix}(data: dict):
    global _counter
    _counter += 1
    item = {{"id": _counter, **data}}
    _store[_counter] = item
    return item


@router.get("/{{item_id}}")
async def get_{route_prefix}(item_id: int):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    return _store[item_id]


@router.put("/{{item_id}}")
async def update_{route_prefix}(item_id: int, data: dict):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    _store[item_id].update(data)
    return _store[item_id]


@router.delete("/{{item_id}}", status_code=204)
async def delete_{route_prefix}(item_id: int):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail="{entity} not found")
    del _store[item_id]
''',
}


class CoderAgent(AgentBase):
    """Writes production code based on architecture and task requirements."""

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        file_manager: FileManager | None = None,
        code_executor: CodeExecutor | None = None,
    ) -> None:
        super().__init__(
            name="coder_agent",
            role="developer",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.file_manager = file_manager
        self.code_executor = code_executor

    async def analyze(self, task: Task) -> dict[str, Any]:
        """Determine what code needs to be written."""
        context = task.artifacts.get("context", "")
        components = self._identify_components(task.description)
        return {
            "components": components,
            "context": context,
        }

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Plan the files to generate."""
        components = analysis["components"]
        steps: list[dict[str, Any]] = []
        for comp in components:
            steps.append(
                {
                    "action": "generate",
                    "component": comp["type"],
                    "name": comp["name"],
                    "path": comp["path"],
                }
            )
        steps.append({"action": "verify", "detail": "Check generated code"})
        return steps

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate code files and optionally verify them."""
        generated_files: list[str] = []

        for step in plan:
            if step["action"] == "generate" and self.file_manager:
                code = self._generate_code(
                    component_type=step["component"],
                    name=step["name"],
                    task_description=task.description,
                )
                path = step["path"]
                self.file_manager.write_file(path, code)
                generated_files.append(path)
                self._logger.info("Generated: %s", path)

            elif step["action"] == "verify" and self.code_executor:
                for fpath in generated_files:
                    if fpath.endswith(".py") and self.file_manager:
                        code = self.file_manager.read_file(fpath)
                        result = self.code_executor.execute(
                            f"import ast; ast.parse('''{code}''')",
                            language="python",
                        )
                        if not result.success:
                            self._logger.warning("Syntax check failed for %s: %s", fpath, result.stderr)

        self.memory.store_long_term(
            doc_id=f"code-{task.task_id}",
            text=f"Generated files: {', '.join(generated_files)}",
            metadata={"task": task.title, "type": "code"},
        )

        return {
            "summary": f"Generated {len(generated_files)} files",
            "files": generated_files,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _identify_components(description: str) -> list[dict[str, str]]:
        """Heuristic: decide which code files to generate."""
        lower = description.lower()
        components: list[dict[str, str]] = []

        if any(kw in lower for kw in ("api", "rest", "endpoint", "backend")):
            components.append(
                {"type": "fastapi_main", "name": "app", "path": "app/main.py"}
            )

        # Try to extract entity names
        entities = []
        for keyword in ("todo", "user", "item", "product", "post", "task", "order"):
            if keyword in lower:
                entities.append(keyword)

        if not entities:
            entities = ["item"]

        for entity in entities:
            components.extend(
                [
                    {
                        "type": "model",
                        "name": entity,
                        "path": f"app/models/{entity}.py",
                    },
                    {
                        "type": "schema",
                        "name": entity,
                        "path": f"app/schemas/{entity}.py",
                    },
                    {
                        "type": "route",
                        "name": entity,
                        "path": f"app/routes/{entity}.py",
                    },
                ]
            )

        return components

    @staticmethod
    def _generate_code(
        component_type: str, name: str, task_description: str
    ) -> str:
        """Fill in a code template."""
        template = CODE_TEMPLATES.get(component_type, "# TODO: implement {name}\n")
        return template.format(
            title=task_description[:60],
            entity=name,
            entity_class=name.capitalize(),
            table_name=f"{name}s",
            route_prefix=f"{name}s",
        )

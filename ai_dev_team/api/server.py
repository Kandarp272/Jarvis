"""FastAPI server exposing the AI Dev Team system over HTTP."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ai_dev_team.agents.architect_agent import ArchitectAgent
from ai_dev_team.agents.coder_agent import CoderAgent
from ai_dev_team.agents.debug_agent import DebugAgent
from ai_dev_team.agents.doc_agent import DocAgent
from ai_dev_team.agents.leader_agent import LeaderAgent
from ai_dev_team.agents.research_agent import ResearchAgent
from ai_dev_team.agents.tester_agent import TesterAgent
from ai_dev_team.config.settings import ProjectConfig, load_config
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import TaskManager
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.code_executor import CodeExecutor
from ai_dev_team.tools.file_manager import FileManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Dev Team",
    description="Autonomous multi-agent AI coding system",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ProjectRequest(BaseModel):
    """Payload for creating a new project."""

    prompt: str
    project_type: str | None = None


class ProjectResponse(BaseModel):
    """Summary returned after a project run."""

    plan: str
    task_summary: dict[str, int]
    tasks: dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    agents: list[str]


# ---------------------------------------------------------------------------
# System bootstrap
# ---------------------------------------------------------------------------

def build_system(config: ProjectConfig | None = None) -> LeaderAgent:
    """Wire up all components and return the ready-to-use leader agent."""
    cfg = config or load_config()
    workspace = cfg.ensure_workspace()

    message_bus = MessageBus()
    task_manager = TaskManager()
    memory = MemoryManager(cfg.memory)
    file_manager = FileManager(workspace)
    code_executor = CodeExecutor(cfg.execution)

    leader = LeaderAgent(
        config=cfg,
        message_bus=message_bus,
        task_manager=task_manager,
        memory=memory,
    )

    # Register specialist agents
    agents = [
        ResearchAgent(cfg, message_bus, memory),
        ArchitectAgent(cfg, message_bus, memory, file_manager),
        CoderAgent(cfg, message_bus, memory, file_manager, code_executor),
        TesterAgent(cfg, message_bus, memory, file_manager, code_executor),
        DebugAgent(cfg, message_bus, memory, file_manager, code_executor),
        DocAgent(cfg, message_bus, memory, file_manager),
    ]
    for agent in agents:
        leader.register_agent(agent)

    return leader


# Lazily initialised leader
_leader: LeaderAgent | None = None


def _get_leader() -> LeaderAgent:
    global _leader
    if _leader is None:
        _leader = build_system()
    return _leader


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"message": "Welcome to the AI Dev Team API"}


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    leader = _get_leader()
    return HealthResponse(
        status="healthy",
        agents=list(leader._agents.keys()),
    )


@app.post("/projects", response_model=ProjectResponse, tags=["projects"])
async def create_project(request: ProjectRequest) -> ProjectResponse:
    """Submit a natural-language prompt and get a complete project back."""
    leader = _get_leader()
    try:
        result = await leader.handle_request(request.prompt)
    except Exception as exc:
        logger.exception("Project creation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProjectResponse(
        plan=result.get("plan", ""),
        task_summary=result.get("task_summary", {}),
        tasks=result.get("tasks", {}),
    )


@app.get("/tasks", tags=["tasks"])
async def list_tasks() -> list[dict[str, Any]]:
    """Return all tasks tracked by the task manager."""
    leader = _get_leader()
    return [t.to_dict() for t in leader.task_manager.tasks]

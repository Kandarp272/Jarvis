"""Configuration settings for the AI Dev Team system."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class ModelProvider(StrEnum):
    """Supported LLM providers."""

    OPENAI = "openai"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"


@dataclass(frozen=True)
class LLMConfig:
    """Configuration for the LLM backend."""

    provider: ModelProvider = ModelProvider.OPENAI
    model_name: str = "gpt-4o"
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    base_url: str | None = None
    temperature: float = 0.2
    max_tokens: int = 4096


@dataclass(frozen=True)
class MemoryConfig:
    """Configuration for the vector memory system."""

    collection_name: str = "ai_dev_team"
    persist_directory: str = ".chromadb"
    embedding_model: str = "all-MiniLM-L6-v2"


@dataclass(frozen=True)
class ExecutionConfig:
    """Configuration for the code execution sandbox."""

    timeout_seconds: int = 30
    max_output_length: int = 10_000
    allowed_languages: tuple[str, ...] = ("python", "javascript", "typescript", "go")
    use_docker: bool = False
    docker_image: str = "python:3.12-slim"


@dataclass(frozen=True)
class ProjectConfig:
    """Top-level project configuration."""

    workspace_dir: Path = field(
        default_factory=lambda: Path(os.getenv("AI_DEV_TEAM_WORKSPACE", "./workspace"))
    )
    log_level: str = "INFO"
    max_retries: int = 3

    llm: LLMConfig = field(default_factory=LLMConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    def ensure_workspace(self) -> Path:
        """Create the workspace directory if it does not exist."""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        return self.workspace_dir


def load_config() -> ProjectConfig:
    """Load configuration from environment variables with sensible defaults."""
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o")
    base_url = os.getenv("LLM_BASE_URL")

    return ProjectConfig(
        llm=LLMConfig(
            provider=ModelProvider(provider),
            model_name=model,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=base_url,
        ),
    )

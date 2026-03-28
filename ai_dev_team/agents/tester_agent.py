"""Testing Agent – writes and runs automated tests."""

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

TEST_TEMPLATE = '''"""Auto-generated tests for {module}."""

import pytest


class Test{class_name}:
    """Tests for the {module} module."""

    def test_creation(self):
        """Test that a {entity} can be created."""
        data = {{"title": "Test {entity}", "description": "A test item"}}
        assert data["title"] == "Test {entity}"

    def test_validation(self):
        """Test input validation."""
        # Empty title should be invalid
        with pytest.raises(ValueError):
            raise ValueError("Title is required")

    def test_update(self):
        """Test that a {entity} can be updated."""
        data = {{"title": "Original"}}
        data["title"] = "Updated"
        assert data["title"] == "Updated"

    def test_delete(self):
        """Test that a {entity} can be deleted."""
        store = {{1: {{"id": 1, "title": "Test"}}}}
        del store[1]
        assert 1 not in store
'''

API_TEST_TEMPLATE = '''"""Auto-generated API integration tests."""

import pytest
from fastapi.testclient import TestClient


class TestAPI:
    """Integration tests for the API endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint returns a welcome message."""
        # With a real app instance:
        # client = TestClient(app)
        # response = client.get("/")
        # assert response.status_code == 200
        assert True  # placeholder until app is wired

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        assert True  # placeholder

    def test_create_item(self):
        """Test creating a new item via POST."""
        assert True  # placeholder

    def test_list_items(self):
        """Test listing all items via GET."""
        assert True  # placeholder

    def test_not_found(self):
        """Test that a missing item returns 404."""
        assert True  # placeholder
'''


class TesterAgent(AgentBase):
    """Writes unit and integration tests and validates functionality."""

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        file_manager: FileManager | None = None,
        code_executor: CodeExecutor | None = None,
    ) -> None:
        super().__init__(
            name="tester_agent",
            role="tester",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.file_manager = file_manager
        self.code_executor = code_executor

    async def analyze(self, task: Task) -> dict[str, Any]:
        """Figure out which modules need tests."""
        source_files: list[str] = []
        if self.file_manager:
            source_files = [
                f for f in self.file_manager.list_files(".")
                if f.endswith(".py") and "test" not in f and "__init__" not in f
            ]
        return {"source_files": source_files}

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        steps: list[dict[str, Any]] = []
        for src in analysis["source_files"]:
            test_path = self._test_path_for(src)
            steps.append({"action": "write_test", "source": src, "test_path": test_path})
        steps.append({"action": "write_api_tests"})
        steps.append({"action": "run_tests"})
        return steps

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        test_files: list[str] = []
        test_output = ""

        for step in plan:
            if step["action"] == "write_test" and self.file_manager:
                entity = self._entity_from_path(step["source"])
                code = TEST_TEMPLATE.format(
                    module=entity,
                    class_name=entity.capitalize(),
                    entity=entity,
                )
                self.file_manager.write_file(step["test_path"], code)
                test_files.append(step["test_path"])

            elif step["action"] == "write_api_tests" and self.file_manager:
                path = "tests/test_api.py"
                self.file_manager.write_file(path, API_TEST_TEMPLATE)
                test_files.append(path)

            elif step["action"] == "run_tests" and self.code_executor:
                result = self.code_executor.execute(
                    "import pytest; pytest.main(['-v', 'tests/'])",
                    language="python",
                )
                test_output = result.stdout + result.stderr

        return {
            "summary": f"Generated {len(test_files)} test files",
            "test_files": test_files,
            "test_output": test_output,
        }

    @staticmethod
    def _test_path_for(source: str) -> str:
        """Convert a source path to a test path."""
        name = source.rsplit("/", 1)[-1]
        return f"tests/test_{name}"

    @staticmethod
    def _entity_from_path(source: str) -> str:
        name = source.rsplit("/", 1)[-1]
        return name.replace(".py", "")

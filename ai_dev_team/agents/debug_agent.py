"""Debugging Agent – detects errors, analyses stack traces, and fixes bugs."""

from __future__ import annotations

import logging
import re
from typing import Any

from ai_dev_team.config.settings import ProjectConfig
from ai_dev_team.core.agent_base import AgentBase
from ai_dev_team.core.communication_protocol import MessageBus
from ai_dev_team.core.task_manager import Task
from ai_dev_team.memory.memory_manager import MemoryManager
from ai_dev_team.tools.code_executor import CodeExecutor
from ai_dev_team.tools.file_manager import FileManager

logger = logging.getLogger(__name__)


class DebugAgent(AgentBase):
    """Detects errors, analyses stack traces, and applies fixes."""

    def __init__(
        self,
        config: ProjectConfig,
        message_bus: MessageBus,
        memory: MemoryManager,
        file_manager: FileManager | None = None,
        code_executor: CodeExecutor | None = None,
    ) -> None:
        super().__init__(
            name="debug_agent",
            role="debugger",
            config=config,
            message_bus=message_bus,
        )
        self.memory = memory
        self.file_manager = file_manager
        self.code_executor = code_executor

    async def analyze(self, task: Task) -> dict[str, Any]:
        """Scan source files for common issues."""
        issues: list[dict[str, str]] = []

        if self.file_manager:
            py_files = [
                f for f in self.file_manager.list_files(".")
                if f.endswith(".py") and "__pycache__" not in f
            ]
            for fpath in py_files:
                try:
                    content = self.file_manager.read_file(fpath)
                    file_issues = self._static_check(fpath, content)
                    issues.extend(file_issues)
                except Exception as exc:
                    issues.append({"file": fpath, "issue": str(exc), "severity": "error"})

        return {"issues": issues}

    async def plan(self, task: Task, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        issues = analysis.get("issues", [])
        steps: list[dict[str, Any]] = []
        for issue in issues:
            steps.append({"action": "fix", **issue})
        if not steps:
            steps.append({"action": "verify", "detail": "No issues found – run smoke test"})
        return steps

    async def execute(self, task: Task, plan: list[dict[str, Any]]) -> dict[str, Any]:
        fixed: list[str] = []
        still_broken: list[str] = []

        for step in plan:
            if step["action"] == "fix" and self.file_manager:
                fpath = step.get("file", "")
                issue = step.get("issue", "")
                try:
                    content = self.file_manager.read_file(fpath)
                    patched = self._auto_fix(content, issue)
                    if patched != content:
                        self.file_manager.write_file(fpath, patched)
                        fixed.append(fpath)
                    else:
                        still_broken.append(f"{fpath}: {issue}")
                except Exception as exc:
                    still_broken.append(f"{fpath}: {exc}")

            elif step["action"] == "verify" and self.code_executor:
                result = self.code_executor.execute(
                    "import ast, sys, pathlib\n"
                    "errors = []\n"
                    "for p in pathlib.Path('.').rglob('*.py'):\n"
                    "    try:\n"
                    "        ast.parse(p.read_text())\n"
                    "    except SyntaxError as e:\n"
                    "        errors.append(f'{p}: {e}')\n"
                    "if errors:\n"
                    "    print('\\n'.join(errors))\n"
                    "    sys.exit(1)\n"
                    "print('All files pass syntax check')\n",
                    language="python",
                )
                if not result.success:
                    still_broken.append(result.stderr)

        return {
            "summary": f"Fixed {len(fixed)} files, {len(still_broken)} remain",
            "fixed_files": fixed,
            "remaining_issues": still_broken,
        }

    # ------------------------------------------------------------------
    # Static analysis helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _static_check(filepath: str, content: str) -> list[dict[str, str]]:
        """Run lightweight static checks on a Python file."""
        issues: list[dict[str, str]] = []

        # Syntax check
        try:
            compile(content, filepath, "exec")
        except SyntaxError as exc:
            issues.append(
                {"file": filepath, "issue": f"SyntaxError: {exc}", "severity": "error"}
            )

        # Common anti-patterns
        if "import *" in content:
            issues.append(
                {"file": filepath, "issue": "Wildcard import detected", "severity": "warning"}
            )

        if re.search(r"except\s*:", content):
            issues.append(
                {"file": filepath, "issue": "Bare except clause", "severity": "warning"}
            )

        return issues

    @staticmethod
    def _auto_fix(content: str, issue: str) -> str:
        """Attempt simple automatic fixes."""
        patched = content

        # Fix missing trailing newline
        if not patched.endswith("\n"):
            patched += "\n"

        # Replace bare excepts with Exception
        patched = re.sub(r"except\s*:", "except Exception:", patched)

        return patched

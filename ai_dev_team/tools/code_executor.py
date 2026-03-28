"""Safe code-execution sandbox for generated code."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from ai_dev_team.config.settings import ExecutionConfig

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Outcome of running a code snippet."""

    stdout: str
    stderr: str
    return_code: int
    language: str
    timed_out: bool = False

    @property
    def success(self) -> bool:
        return self.return_code == 0 and not self.timed_out


class CodeExecutor:
    """Execute code snippets in isolated subprocess sandboxes.

    Supports Python, JavaScript (Node), TypeScript (tsx/ts-node), and Go.
    """

    LANGUAGE_COMMANDS: dict[str, list[str]] = {
        "python": ["python3"],
        "javascript": ["node"],
        "typescript": ["npx", "tsx"],
        "go": ["go", "run"],
    }

    EXTENSIONS: dict[str, str] = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "go": ".go",
    }

    def __init__(self, config: ExecutionConfig) -> None:
        self._config = config

    def execute(
        self,
        code: str,
        language: str = "python",
        working_dir: Path | None = None,
    ) -> ExecutionResult:
        """Run *code* in the chosen language and return the result."""
        language = language.lower()
        if language not in self._config.allowed_languages:
            return ExecutionResult(
                stdout="",
                stderr=f"Language '{language}' is not allowed.",
                return_code=1,
                language=language,
            )

        cmd_prefix = self.LANGUAGE_COMMANDS.get(language)
        ext = self.EXTENSIONS.get(language, ".txt")
        if cmd_prefix is None:
            return ExecutionResult(
                stdout="",
                stderr=f"No runner configured for '{language}'.",
                return_code=1,
                language=language,
            )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False, dir=working_dir
        ) as tmp:
            tmp.write(code)
            tmp.flush()
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [*cmd_prefix, tmp_path],
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
                cwd=working_dir,
            )
            return ExecutionResult(
                stdout=result.stdout[: self._config.max_output_length],
                stderr=result.stderr[: self._config.max_output_length],
                return_code=result.returncode,
                language=language,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution timed out after {self._config.timeout_seconds}s.",
                return_code=1,
                language=language,
                timed_out=True,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def execute_file(
        self, filepath: Path, language: str | None = None
    ) -> ExecutionResult:
        """Run an existing file."""
        if not filepath.is_file():
            return ExecutionResult(
                stdout="",
                stderr=f"File not found: {filepath}",
                return_code=1,
                language=language or "unknown",
            )
        code = filepath.read_text(encoding="utf-8")
        lang = language or self._guess_language(filepath)
        return self.execute(code, language=lang, working_dir=filepath.parent)

    @staticmethod
    def _guess_language(filepath: Path) -> str:
        ext_map = {".py": "python", ".js": "javascript", ".ts": "typescript", ".go": "go"}
        return ext_map.get(filepath.suffix, "python")

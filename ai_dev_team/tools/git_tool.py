"""Git integration tool for version-controlled project output."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class GitTool:
    """Thin wrapper around Git CLI commands scoped to a repository root."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )
        if result.returncode != 0 and not check:
            logger.warning("git %s failed: %s", " ".join(args), result.stderr.strip())
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self) -> str:
        """Initialise a new Git repository."""
        return self._run("init")

    def add(self, paths: list[str] | None = None) -> str:
        """Stage files (defaults to all changes)."""
        targets = paths or ["."]
        return self._run("add", *targets)

    def commit(self, message: str) -> str:
        """Create a commit with the given message."""
        return self._run("commit", "-m", message)

    def status(self) -> str:
        """Return ``git status --short``."""
        return self._run("status", "--short", check=False)

    def log(self, max_count: int = 10) -> str:
        """Return recent commit log."""
        return self._run(
            "log",
            f"--max-count={max_count}",
            "--oneline",
            check=False,
        )

    def diff(self, staged: bool = False) -> str:
        args = ["diff"]
        if staged:
            args.append("--staged")
        return self._run(*args, check=False)

    def create_branch(self, branch_name: str) -> str:
        return self._run("checkout", "-b", branch_name)

    def current_branch(self) -> str:
        return self._run("rev-parse", "--abbrev-ref", "HEAD", check=False)

    @property
    def is_repo(self) -> bool:
        return (self.repo_path / ".git").is_dir()

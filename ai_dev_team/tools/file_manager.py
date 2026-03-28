"""File-system tool for agents to create, read, edit and delete files."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Provides sandboxed file-system operations within a workspace root."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Safety
    # ------------------------------------------------------------------

    def _safe_path(self, relative: str) -> Path:
        """Resolve *relative* under the workspace and reject escapes."""
        target = (self.workspace / relative).resolve()
        if not str(target).startswith(str(self.workspace)):
            raise PermissionError(
                f"Path escapes workspace: {relative}"
            )
        return target

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def create_directory(self, relative: str) -> str:
        """Create a directory (including parents) under the workspace."""
        path = self._safe_path(relative)
        path.mkdir(parents=True, exist_ok=True)
        logger.info("Created directory: %s", path)
        return str(path)

    def write_file(self, relative: str, content: str) -> str:
        """Write *content* to a file, creating parent dirs as needed."""
        path = self._safe_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info("Wrote file: %s (%d bytes)", path, len(content))
        return str(path)

    def read_file(self, relative: str) -> str:
        """Read and return the full text of a file."""
        path = self._safe_path(relative)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {relative}")
        return path.read_text(encoding="utf-8")

    def edit_file(
        self,
        relative: str,
        old_text: str,
        new_text: str,
        *,
        replace_all: bool = False,
    ) -> str:
        """Replace *old_text* with *new_text* in an existing file."""
        content = self.read_file(relative)
        if old_text not in content:
            raise ValueError(f"old_text not found in {relative}")
        if replace_all:
            updated = content.replace(old_text, new_text)
        else:
            updated = content.replace(old_text, new_text, 1)
        return self.write_file(relative, updated)

    def delete_file(self, relative: str) -> None:
        """Delete a single file."""
        path = self._safe_path(relative)
        if path.is_file():
            path.unlink()
            logger.info("Deleted file: %s", path)

    def delete_directory(self, relative: str) -> None:
        """Recursively delete a directory."""
        path = self._safe_path(relative)
        if path.is_dir():
            shutil.rmtree(path)
            logger.info("Deleted directory: %s", path)

    def list_files(
        self, relative: str = ".", pattern: str = "**/*"
    ) -> list[str]:
        """Glob files under a directory and return workspace-relative paths."""
        path = self._safe_path(relative)
        if not path.is_dir():
            return []
        return [
            str(p.relative_to(self.workspace))
            for p in sorted(path.glob(pattern))
            if p.is_file()
        ]

    def exists(self, relative: str) -> bool:
        return self._safe_path(relative).exists()

    def tree(self, relative: str = ".", max_depth: int = 3) -> str:
        """Return a text tree representation of the directory."""
        path = self._safe_path(relative)
        lines: list[str] = [str(path.relative_to(self.workspace)) + "/"]
        self._walk_tree(path, "", 0, max_depth, lines)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _walk_tree(
        self,
        directory: Path,
        prefix: str,
        depth: int,
        max_depth: int,
        lines: list[str],
    ) -> None:
        if depth >= max_depth:
            return
        entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name))
        for idx, entry in enumerate(entries):
            connector = "--- " if idx == len(entries) - 1 else "|-- "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if idx == len(entries) - 1 else "|   "
                self._walk_tree(entry, prefix + extension, depth + 1, max_depth, lines)

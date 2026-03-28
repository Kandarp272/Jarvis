"""Tests for the file manager tool."""

from pathlib import Path

import pytest

from ai_dev_team.tools.file_manager import FileManager


@pytest.fixture
def fm(tmp_path: Path) -> FileManager:
    return FileManager(tmp_path)


class TestFileManager:
    def test_write_and_read(self, fm: FileManager):
        fm.write_file("hello.txt", "world")
        assert fm.read_file("hello.txt") == "world"

    def test_create_directory(self, fm: FileManager):
        fm.create_directory("a/b/c")
        assert (fm.workspace / "a" / "b" / "c").is_dir()

    def test_edit_file(self, fm: FileManager):
        fm.write_file("test.py", "old code")
        fm.edit_file("test.py", "old", "new")
        assert fm.read_file("test.py") == "new code"

    def test_delete_file(self, fm: FileManager):
        fm.write_file("tmp.txt", "data")
        fm.delete_file("tmp.txt")
        assert not fm.exists("tmp.txt")

    def test_list_files(self, fm: FileManager):
        fm.write_file("a.py", "")
        fm.write_file("b.py", "")
        files = fm.list_files(".")
        assert len(files) == 2

    def test_path_escape_rejected(self, fm: FileManager):
        with pytest.raises(PermissionError):
            fm.write_file("../../escape.txt", "bad")

    def test_tree(self, fm: FileManager):
        fm.write_file("src/main.py", "")
        fm.write_file("src/utils.py", "")
        tree = fm.tree(".")
        assert "main.py" in tree

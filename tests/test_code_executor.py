"""Tests for the code executor tool."""

from ai_dev_team.config.settings import ExecutionConfig
from ai_dev_team.tools.code_executor import CodeExecutor


class TestCodeExecutor:
    def setup_method(self):
        self.executor = CodeExecutor(ExecutionConfig())

    def test_python_success(self):
        result = self.executor.execute("print('hello')", language="python")
        assert result.success
        assert "hello" in result.stdout

    def test_python_error(self):
        result = self.executor.execute("raise ValueError('boom')", language="python")
        assert not result.success
        assert "ValueError" in result.stderr

    def test_disallowed_language(self):
        cfg = ExecutionConfig(allowed_languages=("python",))
        executor = CodeExecutor(cfg)
        result = executor.execute("console.log('hi')", language="javascript")
        assert not result.success
        assert "not allowed" in result.stderr

    def test_timeout(self):
        cfg = ExecutionConfig(timeout_seconds=1)
        executor = CodeExecutor(cfg)
        result = executor.execute("import time; time.sleep(10)", language="python")
        assert not result.success
        assert result.timed_out

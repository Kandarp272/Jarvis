"""Tests for the task manager module."""

from ai_dev_team.core.task_manager import Task, TaskManager, TaskStatus


class TestTask:
    def test_initial_status(self):
        task = Task(title="Test", description="A test task")
        assert task.status == TaskStatus.PENDING

    def test_mark_in_progress(self):
        task = Task(title="Test", description="A test task")
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_mark_completed(self):
        task = Task(title="Test", description="A test task")
        task.mark_completed(result="done", artifacts={"key": "value"})
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "done"
        assert task.artifacts == {"key": "value"}
        assert task.completed_at is not None

    def test_mark_failed(self):
        task = Task(title="Test", description="A test task")
        task.mark_failed("error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.retries == 1

    def test_to_dict(self):
        task = Task(title="Test", description="desc")
        d = task.to_dict()
        assert d["title"] == "Test"
        assert d["description"] == "desc"
        assert d["status"] == "pending"


class TestTaskManager:
    def test_create_task(self):
        tm = TaskManager()
        task = tm.create_task(title="T1", description="D1")
        assert task.title == "T1"
        assert len(tm.tasks) == 1

    def test_get_task(self):
        tm = TaskManager()
        task = tm.create_task(title="T1", description="D1")
        found = tm.get_task(task.task_id)
        assert found is task

    def test_get_tasks_by_status(self):
        tm = TaskManager()
        t1 = tm.create_task(title="T1", description="D1")
        tm.create_task(title="T2", description="D2")
        t1.mark_in_progress()
        assert len(tm.get_tasks_by_status(TaskStatus.PENDING)) == 1
        assert len(tm.get_tasks_by_status(TaskStatus.IN_PROGRESS)) == 1

    def test_dependencies(self):
        tm = TaskManager()
        t1 = tm.create_task(title="T1", description="D1")
        t2 = tm.create_task(title="T2", description="D2", dependencies=[t1.task_id])
        assert not tm.all_dependencies_met(t2)
        t1.mark_completed(result="done")
        assert tm.all_dependencies_met(t2)

    def test_ready_tasks(self):
        tm = TaskManager()
        t1 = tm.create_task(title="T1", description="D1")
        tm.create_task(title="T2", description="D2", dependencies=[t1.task_id])
        ready = tm.ready_tasks()
        assert len(ready) == 1
        assert ready[0] is t1

    def test_summary(self):
        tm = TaskManager()
        tm.create_task(title="T1", description="D1")
        tm.create_task(title="T2", description="D2")
        s = tm.summary()
        assert s["pending"] == 2

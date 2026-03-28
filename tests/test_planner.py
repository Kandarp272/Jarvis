"""Tests for the task planner."""

from ai_dev_team.core.task_manager import TaskManager
from ai_dev_team.planner.task_planner import TaskPlanner


class TestTaskPlanner:
    def test_create_plan_web_api(self):
        tm = TaskManager()
        planner = TaskPlanner(tm)
        tasks = planner.create_plan("Build a REST API for a todo app")
        assert len(tasks) >= 3
        assert tasks[0].assigned_to == "research_agent"

    def test_create_plan_full_stack(self):
        tm = TaskManager()
        planner = TaskPlanner(tm)
        tasks = planner.create_plan("Build a full stack app with React frontend")
        assert any("frontend" in t.title.lower() for t in tasks)

    def test_create_plan_library(self):
        tm = TaskManager()
        planner = TaskPlanner(tm)
        tasks = planner.create_plan("Create a Python library for data validation")
        assert len(tasks) >= 3

    def test_dependencies_are_chained(self):
        tm = TaskManager()
        planner = TaskPlanner(tm)
        tasks = planner.create_plan("Build an API")
        for i in range(1, len(tasks)):
            assert tasks[i - 1].task_id in tasks[i].dependencies

    def test_describe_plan(self):
        tm = TaskManager()
        planner = TaskPlanner(tm)
        tasks = planner.create_plan("Build something")
        desc = planner.describe_plan(tasks)
        assert "Project Plan" in desc

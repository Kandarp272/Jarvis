"""Task lifecycle management for the AI Dev Team."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class TaskStatus(StrEnum):
    """Possible states for a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Represents a single unit of work in the system."""

    title: str
    description: str
    assigned_to: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    result: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    completed_at: str | None = None
    retries: int = 0

    def mark_in_progress(self) -> None:
        self.status = TaskStatus.IN_PROGRESS

    def mark_completed(self, result: str, artifacts: dict[str, Any] | None = None) -> None:
        self.status = TaskStatus.COMPLETED
        self.result = result
        if artifacts:
            self.artifacts.update(artifacts)
        self.completed_at = datetime.now(UTC).isoformat()

    def mark_failed(self, reason: str) -> None:
        self.status = TaskStatus.FAILED
        self.result = reason
        self.retries += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "dependencies": self.dependencies,
            "result": self.result,
            "artifacts": self.artifacts,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "retries": self.retries,
        }


class TaskManager:
    """Registry that tracks all tasks in a project."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def create_task(
        self,
        title: str,
        description: str,
        parent_id: str | None = None,
        dependencies: list[str] | None = None,
        assigned_to: str | None = None,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            parent_id=parent_id,
            dependencies=dependencies or [],
            assigned_to=assigned_to,
        )
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_subtasks(self, parent_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.parent_id == parent_id]

    def get_tasks_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == status]

    def get_tasks_for_agent(self, agent_name: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.assigned_to == agent_name]

    def all_dependencies_met(self, task: Task) -> bool:
        """Check whether every dependency of *task* is completed."""
        for dep_id in task.dependencies:
            dep = self._tasks.get(dep_id)
            if dep is None or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    def ready_tasks(self) -> list[Task]:
        """Return tasks that are pending and have all dependencies met."""
        return [
            t
            for t in self._tasks.values()
            if t.status == TaskStatus.PENDING and self.all_dependencies_met(t)
        ]

    @property
    def tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        return counts

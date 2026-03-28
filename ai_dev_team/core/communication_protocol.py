"""Structured message protocol for inter-agent communication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class MessagePriority(StrEnum):
    """Priority levels for inter-agent messages."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(StrEnum):
    """Types of messages exchanged between agents."""

    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    STATUS_UPDATE = "status_update"
    ERROR_REPORT = "error_report"
    QUERY = "query"
    RESPONSE = "response"
    DISCUSSION = "discussion"


@dataclass
class AgentMessage:
    """A structured message passed between agents."""

    sender: str
    receiver: str
    message_type: MessageType
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.MEDIUM
    task_id: str | None = None
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    parent_message_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "content": self.content,
            "context": self.context,
            "priority": self.priority.value,
            "task_id": self.task_id,
            "timestamp": self.timestamp,
            "parent_message_id": self.parent_message_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        return cls(
            sender=data["sender"],
            receiver=data["receiver"],
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            context=data.get("context", {}),
            priority=MessagePriority(data.get("priority", "medium")),
            task_id=data.get("task_id"),
            message_id=data.get("message_id", uuid.uuid4().hex),
            timestamp=data.get(
                "timestamp", datetime.now(UTC).isoformat()
            ),
            parent_message_id=data.get("parent_message_id"),
        )


class MessageBus:
    """Simple in-process message bus for agent communication."""

    def __init__(self) -> None:
        self._queues: dict[str, list[AgentMessage]] = {}
        self._history: list[AgentMessage] = []

    def send(self, message: AgentMessage) -> None:
        """Deliver a message to the receiver's queue."""
        self._history.append(message)
        self._queues.setdefault(message.receiver, []).append(message)

    def receive(self, agent_name: str) -> list[AgentMessage]:
        """Drain and return all pending messages for *agent_name*."""
        messages = self._queues.pop(agent_name, [])
        return messages

    def peek(self, agent_name: str) -> list[AgentMessage]:
        """View pending messages without removing them."""
        return list(self._queues.get(agent_name, []))

    @property
    def history(self) -> list[AgentMessage]:
        return list(self._history)

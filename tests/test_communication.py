"""Tests for the communication protocol."""

from ai_dev_team.core.communication_protocol import (
    AgentMessage,
    MessageBus,
    MessagePriority,
    MessageType,
)


class TestAgentMessage:
    def test_create_message(self):
        msg = AgentMessage(
            sender="agent_a",
            receiver="agent_b",
            message_type=MessageType.TASK_ASSIGNMENT,
            content="Do something",
        )
        assert msg.sender == "agent_a"
        assert msg.receiver == "agent_b"
        assert msg.message_type == MessageType.TASK_ASSIGNMENT

    def test_to_dict_roundtrip(self):
        msg = AgentMessage(
            sender="a",
            receiver="b",
            message_type=MessageType.STATUS_UPDATE,
            content="update",
            priority=MessagePriority.HIGH,
        )
        d = msg.to_dict()
        restored = AgentMessage.from_dict(d)
        assert restored.sender == msg.sender
        assert restored.content == msg.content
        assert restored.priority == MessagePriority.HIGH


class TestMessageBus:
    def test_send_and_receive(self):
        bus = MessageBus()
        msg = AgentMessage(
            sender="a",
            receiver="b",
            message_type=MessageType.QUERY,
            content="hello",
        )
        bus.send(msg)
        messages = bus.receive("b")
        assert len(messages) == 1
        assert messages[0].content == "hello"

    def test_receive_drains_queue(self):
        bus = MessageBus()
        msg = AgentMessage(
            sender="a",
            receiver="b",
            message_type=MessageType.QUERY,
            content="hello",
        )
        bus.send(msg)
        bus.receive("b")
        assert bus.receive("b") == []

    def test_peek_does_not_drain(self):
        bus = MessageBus()
        msg = AgentMessage(
            sender="a",
            receiver="b",
            message_type=MessageType.QUERY,
            content="hello",
        )
        bus.send(msg)
        assert len(bus.peek("b")) == 1
        assert len(bus.peek("b")) == 1

    def test_history(self):
        bus = MessageBus()
        for i in range(3):
            bus.send(
                AgentMessage(
                    sender="a",
                    receiver="b",
                    message_type=MessageType.QUERY,
                    content=f"msg-{i}",
                )
            )
        assert len(bus.history) == 3

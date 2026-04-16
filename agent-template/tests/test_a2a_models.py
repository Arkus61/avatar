"""Unit tests for A2A data models."""

import pytest
from a2a.models import (
    AgentCard,
    AgentCapabilities,
    Message,
    Task,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TextPart,
    DataPart,
)


def test_text_part_roundtrip():
    part = TextPart(text="hello")
    assert part.type == "text"
    assert part.text == "hello"


def test_data_part_roundtrip():
    part = DataPart(data={"key": "value"})
    assert part.type == "data"
    assert part.data == {"key": "value"}


def test_message_roundtrip():
    msg = Message(role="user", parts=[TextPart(text="hi")])
    dumped = msg.model_dump()
    restored = Message.model_validate(dumped)
    assert restored.role == "user"
    assert len(restored.parts) == 1


def test_task_default_id():
    task = Task(status=TaskStatus(state=TaskState.SUBMITTED))
    assert task.id  # non-empty UUID


def test_task_send_params():
    params = TaskSendParams(
        message=Message(role="user", parts=[TextPart(text="summarize this")])
    )
    assert params.id
    assert params.accepted_output_modes == ["text"]


def test_agent_card():
    card = AgentCard(
        name="TestAgent",
        description="A test agent",
        url="http://localhost:8100",
        capabilities=AgentCapabilities(streaming=False),
    )
    assert card.version == "1.0.0"
    assert card.skills == []

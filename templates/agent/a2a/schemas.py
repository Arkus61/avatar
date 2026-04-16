"""Pydantic-модели сообщений A2A.

Намеренно используется минимальное подмножество полей A2A-спецификации,
достаточное для обмена задачами между агентами. Документацию по полной
спецификации см. в `instructions/30-a2a-protocol.md` и на сайте проекта A2A.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PartKind(str, Enum):
    TEXT = "text"
    DATA = "data"
    FILE = "file"


class TextPart(BaseModel):
    kind: Literal[PartKind.TEXT] = PartKind.TEXT
    text: str


class DataPart(BaseModel):
    kind: Literal[PartKind.DATA] = PartKind.DATA
    data: dict[str, Any]


class FilePart(BaseModel):
    kind: Literal[PartKind.FILE] = PartKind.FILE
    name: str
    uri: str
    mime_type: str | None = None


Part = TextPart | DataPart | FilePart


class Role(str, Enum):
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"
    SYSTEM = "system"


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Role
    parts: list[Part]
    created_at: datetime = Field(default_factory=_now)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_INPUT = "needs_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskContext(BaseModel):
    trace_id: UUID = Field(default_factory=uuid4)
    parent_task: UUID | None = None
    delegation_depth: int = 0


class TaskRequest(BaseModel):
    skill_id: str
    input: dict[str, Any] = Field(default_factory=dict)
    stream: bool = True
    context: TaskContext = Field(default_factory=TaskContext)
    deadline_sec: int = 120
    reply_to: str | None = None


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    skill_id: str
    status: TaskStatus = TaskStatus.QUEUED
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] | None = None
    error: str | None = None
    context: TaskContext = Field(default_factory=TaskContext)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    messages: list[Message] = Field(default_factory=list)


class EventKind(str, Enum):
    PROGRESS = "progress"
    PARTIAL_OUTPUT = "partial_output"
    REQUIRES_INPUT = "requires_input"
    FINAL = "final"
    ERROR = "error"


class TaskEvent(BaseModel):
    task_id: UUID
    kind: EventKind
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class AgentCardSkill(BaseModel):
    id: str
    name: str
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class AgentCard(BaseModel):
    schema_version: str = "1.0"
    id: str
    name: str
    description: str | None = None
    version: str
    url: str
    documentation_url: str | None = None
    provider: dict[str, Any] | None = None
    auth: dict[str, Any] | None = None
    capabilities: dict[str, Any] = Field(default_factory=dict)
    modalities: dict[str, list[str]] = Field(default_factory=dict)
    preferred_language: str = "en"
    skills: list[AgentCardSkill] = Field(default_factory=list)
    endpoints: dict[str, str] = Field(default_factory=dict)

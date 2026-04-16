"""A2A FastAPI-сервер: принимает задачи, отдаёт Agent Card, стримит события."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .schemas import (
    AgentCard,
    EventKind,
    Message,
    Role,
    Task,
    TaskEvent,
    TaskRequest,
    TaskStatus,
    TextPart,
)

logger = logging.getLogger("a2a.server")

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


class TaskStore:
    """In-memory хранилище задач + очереди событий.

    В продакшене заменить на Postgres/Redis. Интерфейс сохраняется.
    """

    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        self._queues: dict[UUID, asyncio.Queue[TaskEvent]] = {}
        self._lock = asyncio.Lock()

    async def create(self, req: TaskRequest) -> Task:
        async with self._lock:
            task = Task(
                skill_id=req.skill_id,
                input=req.input,
                context=req.context,
            )
            self._tasks[task.id] = task
            self._queues[task.id] = asyncio.Queue()
            return task

    async def get(self, task_id: UUID) -> Task:
        task = self._tasks.get(task_id)
        if task is None:
            raise HTTPException(404, "Task not found")
        return task

    async def update_status(self, task_id: UUID, status: TaskStatus, **fields: Any) -> Task:
        task = await self.get(task_id)
        task.status = status
        for key, value in fields.items():
            setattr(task, key, value)
        return task

    async def emit(self, task_id: UUID, event: TaskEvent) -> None:
        queue = self._queues.get(task_id)
        if queue is not None:
            await queue.put(event)

    async def events(self, task_id: UUID):
        queue = self._queues.get(task_id)
        if queue is None:
            raise HTTPException(404, "Task not found")
        while True:
            event = await queue.get()
            yield event
            if event.kind in (EventKind.FINAL, EventKind.ERROR):
                break


class SkillDispatcher:
    """Интерфейс, в который проброшен реестр скиллов из runtime."""

    async def dispatch(self, task: Task, store: "TaskStore") -> None:  # pragma: no cover
        raise NotImplementedError


def build_app(
    card: AgentCard,
    dispatcher: SkillDispatcher,
    store: TaskStore | None = None,
    allow_peers: list[str] | None = None,
) -> FastAPI:
    """Создаёт FastAPI-приложение с A2A-эндпоинтами.

    Хендлеры оставлены тонкими: вся «умная» логика живёт в SkillDispatcher,
    который приходит из runtime/agent.py.
    """

    store = store or TaskStore()
    allow_peers = allow_peers or []

    app = FastAPI(
        title=f"A2A :: {card.name}",
        version=card.version,
        docs_url="/docs",
    )

    async def peer_gate(request: Request) -> None:
        if not allow_peers:
            return
        peer = request.headers.get("x-a2a-peer-id", "")
        if peer not in allow_peers:
            raise HTTPException(403, f"Peer {peer!r} is not allowed")

    @app.get("/.well-known/agent-card.json")
    async def get_card() -> JSONResponse:
        return JSONResponse(card.model_dump(mode="json"))

    @app.post("/a2a/v1/tasks", dependencies=[Depends(peer_gate)])
    async def create_task(req: TaskRequest) -> dict[str, Any]:
        task = await store.create(req)
        asyncio.create_task(_run_task(task, dispatcher, store))
        return {"id": str(task.id), "status": task.status}

    @app.get("/a2a/v1/tasks/{task_id}", dependencies=[Depends(peer_gate)])
    async def get_task(task_id: UUID) -> dict[str, Any]:
        task = await store.get(task_id)
        return task.model_dump(mode="json")

    @app.get("/a2a/v1/tasks/{task_id}/events", dependencies=[Depends(peer_gate)])
    async def stream_events(task_id: UUID) -> StreamingResponse:
        async def gen():
            async for event in store.events(task_id):
                payload = event.model_dump(mode="json")
                yield f"event: {event.kind}\ndata: {json.dumps(payload)}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    @app.post("/a2a/v1/tasks/{task_id}/messages", dependencies=[Depends(peer_gate)])
    async def post_message(task_id: UUID, msg: Message) -> dict[str, Any]:
        task = await store.get(task_id)
        task.messages.append(msg)
        await store.emit(
            task_id,
            TaskEvent(
                task_id=task_id,
                kind=EventKind.PROGRESS,
                data={"message_id": str(msg.id), "role": msg.role},
            ),
        )
        return {"ok": True}

    @app.delete("/a2a/v1/tasks/{task_id}", dependencies=[Depends(peer_gate)])
    async def cancel_task(task_id: UUID) -> dict[str, Any]:
        await store.update_status(task_id, TaskStatus.CANCELLED)
        await store.emit(
            task_id,
            TaskEvent(task_id=task_id, kind=EventKind.FINAL, data={"status": "cancelled"}),
        )
        return {"ok": True}

    app.state.task_store = store
    app.state.agent_card = card
    return app


async def _run_task(task: Task, dispatcher: SkillDispatcher, store: TaskStore) -> None:
    try:
        await store.update_status(task.id, TaskStatus.RUNNING)
        await store.emit(task.id, TaskEvent(task_id=task.id, kind=EventKind.PROGRESS, data={"status": "running"}))
        await dispatcher.dispatch(task, store)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Task %s failed", task.id)
        await store.update_status(task.id, TaskStatus.FAILED, error=str(exc))
        await store.emit(
            task.id,
            TaskEvent(task_id=task.id, kind=EventKind.ERROR, data={"error": str(exc)}),
        )


def _append_text_message(task: Task, role: Role, text: str) -> None:
    """Удобный помощник для хендлеров — добавляет текстовое сообщение в задачу."""

    task.messages.append(Message(role=role, parts=[TextPart(text=text)]))

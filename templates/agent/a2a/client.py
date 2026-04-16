"""A2A-клиент для исходящих вызовов к другим агентам."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator
from uuid import UUID

import httpx

from .schemas import AgentCard, TaskEvent, TaskRequest, TaskStatus

logger = logging.getLogger("a2a.client")


class A2AClientError(RuntimeError):
    pass


class A2AClient:
    """Тонкий клиент. Все методы — корутины."""

    def __init__(
        self,
        base_url: str,
        *,
        auth_header: str | None = None,
        peer_id: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        headers = {"User-Agent": "agent-template-a2a/0.1"}
        if auth_header:
            headers["Authorization"] = auth_header
        if peer_id:
            headers["x-a2a-peer-id"] = peer_id
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "A2AClient":
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()

    async def fetch_card(self) -> AgentCard:
        resp = await self._client.get("/.well-known/agent-card.json")
        resp.raise_for_status()
        return AgentCard.model_validate(resp.json())

    async def create_task(self, req: TaskRequest) -> UUID:
        resp = await self._client.post("/a2a/v1/tasks", json=req.model_dump(mode="json"))
        if resp.status_code >= 400:
            raise A2AClientError(f"create_task failed: {resp.status_code} {resp.text}")
        data = resp.json()
        return UUID(data["id"])

    async def get_task(self, task_id: UUID) -> dict[str, Any]:
        resp = await self._client.get(f"/a2a/v1/tasks/{task_id}")
        resp.raise_for_status()
        return resp.json()

    async def cancel(self, task_id: UUID) -> None:
        await self._client.delete(f"/a2a/v1/tasks/{task_id}")

    async def stream_events(self, task_id: UUID) -> AsyncIterator[TaskEvent]:
        async with self._client.stream("GET", f"/a2a/v1/tasks/{task_id}/events") as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = json.loads(line.removeprefix("data:").strip())
                yield TaskEvent.model_validate(payload)

    async def run_until_final(
        self,
        req: TaskRequest,
        *,
        on_event=None,
        deadline_sec: float | None = None,
    ) -> dict[str, Any]:
        """Создаёт задачу, читает SSE-поток до финала, возвращает финальный Task."""

        task_id = await self.create_task(req)
        deadline = deadline_sec or req.deadline_sec or 120

        async def _read():
            async for event in self.stream_events(task_id):
                if on_event is not None:
                    await _maybe_await(on_event(event))
                if event.kind in ("final", "error"):
                    break

        try:
            await asyncio.wait_for(_read(), timeout=deadline)
        except asyncio.TimeoutError as exc:
            await self.cancel(task_id)
            raise A2AClientError(f"task {task_id} timed out") from exc

        task = await self.get_task(task_id)
        if task["status"] not in (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value):
            raise A2AClientError(f"task {task_id} finished with status={task['status']}")
        return task


async def _maybe_await(value: Any) -> Any:
    if asyncio.iscoroutine(value):
        return await value
    return value

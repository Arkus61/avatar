"""A2A Client — calls remote agents via A2A JSON-RPC protocol."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import httpx

from .models import (
    AgentCard,
    JsonRpcRequest,
    JsonRpcResponse,
    Task,
    TaskSendParams,
    Message,
    TextPart,
)

logger = logging.getLogger(__name__)


class A2AClient:
    """HTTP client for communicating with a remote A2A agent."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    async def get_agent_card(self) -> AgentCard:
        resp = await self._client.get(f"{self.base_url}/.well-known/agent.json")
        resp.raise_for_status()
        return AgentCard.model_validate(resp.json())

    # ------------------------------------------------------------------
    # Core RPC
    # ------------------------------------------------------------------

    async def send_task(self, params: TaskSendParams) -> Task:
        """Send a task to the remote agent and wait for result."""
        rpc = JsonRpcRequest(
            id=str(uuid.uuid4()),
            method="tasks/send",
            params=params.model_dump(),
        )
        response = await self._rpc(rpc)
        return Task.model_validate(response.result)

    async def get_task(self, task_id: str) -> Task:
        rpc = JsonRpcRequest(
            id=str(uuid.uuid4()),
            method="tasks/get",
            params={"id": task_id},
        )
        response = await self._rpc(rpc)
        return Task.model_validate(response.result)

    async def cancel_task(self, task_id: str) -> Task:
        rpc = JsonRpcRequest(
            id=str(uuid.uuid4()),
            method="tasks/cancel",
            params={"id": task_id},
        )
        response = await self._rpc(rpc)
        return Task.model_validate(response.result)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    async def ask(self, text: str, session_id: str | None = None) -> str:
        """Send a plain-text message and return the agent's text reply."""
        params = TaskSendParams(
            session_id=session_id,
            message=Message(
                role="user",
                parts=[TextPart(text=text)],
            ),
        )
        task = await self.send_task(params)
        if task.status.message and task.status.message.parts:
            first = task.status.message.parts[0]
            if hasattr(first, "text"):
                return first.text  # type: ignore[attr-defined]
        # Fallback: check artifacts
        for artifact in task.artifacts:
            for part in artifact.parts:
                if hasattr(part, "text"):
                    return part.text  # type: ignore[attr-defined]
        return ""

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _rpc(self, request: JsonRpcRequest) -> JsonRpcResponse:
        resp = await self._client.post(
            f"{self.base_url}/a2a",
            json=request.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        rpc_resp = JsonRpcResponse.model_validate(data)
        if rpc_resp.error:
            raise RuntimeError(f"A2A remote error: {rpc_resp.error}")
        return rpc_resp

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "A2AClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

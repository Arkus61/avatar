"""A2A Server — exposes this agent as an A2A endpoint.

Routes:
  GET  /.well-known/agent.json  → AgentCard
  POST /a2a                     → JSON-RPC 2.0 dispatcher
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Awaitable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .models import (
    AgentCard,
    JsonRpcRequest,
    JsonRpcResponse,
    Task,
    TaskSendParams,
    TaskState,
    TaskStatus,
    Message,
    TextPart,
)

if TYPE_CHECKING:
    from ..core.agent import Agent

logger = logging.getLogger(__name__)

# Handler type: receives TaskSendParams, returns Task
TaskHandler = Callable[[TaskSendParams], Awaitable[Task]]


class A2AServer:
    """Mounts A2A JSON-RPC routes onto a FastAPI app."""

    def __init__(self, agent_card: AgentCard, task_handler: TaskHandler) -> None:
        self.agent_card = agent_card
        self.task_handler = task_handler
        self.app = FastAPI(title=agent_card.name, version=agent_card.version)
        self._register_routes()

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card() -> AgentCard:
            return self.agent_card

        @self.app.post("/a2a")
        async def a2a_endpoint(request: Request) -> JSONResponse:
            try:
                body = await request.json()
                rpc_req = JsonRpcRequest.model_validate(body)
                result = await self._dispatch(rpc_req)
                return JSONResponse(
                    JsonRpcResponse(id=rpc_req.id, result=result).model_dump()
                )
            except Exception as exc:
                logger.exception("A2A RPC error")
                return JSONResponse(
                    JsonRpcResponse(
                        error={"code": -32603, "message": str(exc)}
                    ).model_dump(),
                    status_code=500,
                )

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    async def _dispatch(self, req: JsonRpcRequest) -> Any:
        method = req.method
        params = req.params

        dispatch_table: dict[str, Callable[..., Awaitable[Any]]] = {
            "tasks/send": self._handle_tasks_send,
            "tasks/get": self._handle_tasks_get,
            "tasks/cancel": self._handle_tasks_cancel,
        }

        handler = dispatch_table.get(method)
        if handler is None:
            raise ValueError(f"Unknown method: {method}")

        return await handler(params)

    # ------------------------------------------------------------------
    # Method handlers
    # ------------------------------------------------------------------

    async def _handle_tasks_send(self, params: dict[str, Any]) -> dict[str, Any]:
        send_params = TaskSendParams.model_validate(params)
        task = await self.task_handler(send_params)
        return task.model_dump()

    async def _handle_tasks_get(self, params: dict[str, Any]) -> dict[str, Any]:
        # Minimal stub — override in subclass or connect to a task store
        task_id = params.get("id", "unknown")
        task = Task(
            id=task_id,
            status=TaskStatus(state=TaskState.COMPLETED),
        )
        return task.model_dump()

    async def _handle_tasks_cancel(self, params: dict[str, Any]) -> dict[str, Any]:
        task_id = params.get("id", "unknown")
        task = Task(
            id=task_id,
            status=TaskStatus(state=TaskState.CANCELED),
        )
        return task.model_dump()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def make_error_task(self, task_id: str, error_msg: str) -> Task:
        return Task(
            id=task_id,
            status=TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=error_msg)],
                ),
            ),
        )

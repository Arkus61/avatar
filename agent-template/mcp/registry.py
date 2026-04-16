"""MCP Registry — manages connections to multiple MCP servers and exposes their tools."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from typing import Any

from .tool import MCPTool, ToolResult

logger = logging.getLogger(__name__)


class MCPServerProcess:
    """Manages a single MCP server subprocess (stdio transport)."""

    def __init__(self, name: str, command: list[str], env: dict[str, str] | None = None) -> None:
        self.name = name
        self.command = command
        self.env = {**os.environ, **(env or {})}
        self._proc: asyncio.subprocess.Process | None = None
        self._reader_task: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._id_counter = 0
        self._tools: list[MCPTool] = []

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )
        self._reader_task = asyncio.create_task(self._read_loop())
        await self._initialize()
        await self._load_tools()

    async def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            await self._proc.wait()
        if self._reader_task:
            self._reader_task.cancel()

    # ------------------------------------------------------------------
    # Protocol
    # ------------------------------------------------------------------

    async def _initialize(self) -> None:
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "agent-template", "version": "1.0.0"},
        })
        await self._send_notification("notifications/initialized")

    async def _load_tools(self) -> None:
        result = await self._send_request("tools/list", {})
        raw_tools = result.get("tools", [])
        for t in raw_tools:
            tool = MCPTool(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("inputSchema", {}),
                server_name=self.name,
            )
            # Bind executor
            tool._call = self._make_executor(t["name"])
            self._tools.append(tool)
        logger.info("MCP server '%s' loaded %d tools", self.name, len(self._tools))

    def _make_executor(self, tool_name: str):
        async def executor(**kwargs: Any) -> ToolResult:
            result = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": kwargs,
            })
            is_error = result.get("isError", False)
            content = result.get("content", [])
            return ToolResult(content=content, is_error=is_error)
        return executor

    # ------------------------------------------------------------------
    # JSON-RPC over stdio
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    async def _send_request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        req_id = self._next_id()
        msg = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        loop = asyncio.get_event_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[req_id] = future
        await self._write(msg)
        return await asyncio.wait_for(future, timeout=30.0)

    async def _send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        await self._write(msg)

    async def _write(self, msg: dict[str, Any]) -> None:
        assert self._proc and self._proc.stdin
        line = json.dumps(msg) + "\n"
        self._proc.stdin.write(line.encode())
        await self._proc.stdin.drain()

    async def _read_loop(self) -> None:
        assert self._proc and self._proc.stdout
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break
            try:
                data = json.loads(line.decode())
                req_id = data.get("id")
                if req_id is not None and req_id in self._pending:
                    future = self._pending.pop(req_id)
                    if "error" in data:
                        future.set_exception(RuntimeError(str(data["error"])))
                    else:
                        future.set_result(data.get("result", {}))
            except Exception as exc:
                logger.warning("MCP read error: %s", exc)

    @property
    def tools(self) -> list[MCPTool]:
        return self._tools


class MCPRegistry:
    """Manages multiple MCP server connections and provides unified tool access."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerProcess] = {}

    async def add_server(
        self,
        name: str,
        command: list[str],
        env: dict[str, str] | None = None,
    ) -> None:
        server = MCPServerProcess(name=name, command=command, env=env)
        try:
            await server.start()
            self._servers[name] = server
        except Exception as exc:
            logger.error("Failed to start MCP server '%s': %s", name, exc)

    def get_all_tools(self) -> list[MCPTool]:
        tools = []
        for server in self._servers.values():
            tools.extend(server.tools)
        return tools

    def get_tool(self, name: str) -> MCPTool | None:
        for server in self._servers.values():
            for tool in server.tools:
                if tool.name == name:
                    return tool
        return None

    async def call_tool(self, name: str, **kwargs: Any) -> ToolResult:
        tool = self.get_tool(name)
        if tool is None:
            return ToolResult(
                content=[{"type": "text", "text": f"Tool '{name}' not found."}],
                is_error=True,
            )
        return await tool.call(**kwargs)

    def tools_description(self) -> str:
        lines = []
        for tool in self.get_all_tools():
            lines.append(f"- **{tool.name}** ({tool.server_name}): {tool.description}")
        return "\n".join(lines) if lines else "(no MCP tools loaded)"

    async def shutdown(self) -> None:
        for server in self._servers.values():
            await server.stop()
        self._servers.clear()

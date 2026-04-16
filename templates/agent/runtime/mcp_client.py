"""Тонкий MCP-клиент.

Цели:
- Разобрать `mcp/mcp.config.json` и `mcp/tools.manifest.yaml`.
- Унифицировать вызов stdio- и http-серверов.
- Отдавать runtime список `ToolSpec`, готовый к подаче в LLM.
- Применять allow-list и rate-limit из манифеста.

Реализация сознательно не тянет официальный `mcp`-пакет как обязательную зависимость:
если пакет установлен — используется он; иначе работает упрощённый JSON-RPC fallback
для HTTP-серверов и понятно падает для stdio-серверов с подсказкой.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml  # type: ignore

from .llm import ToolSpec

logger = logging.getLogger("runtime.mcp")

_ENV_VAR = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")


def _expand_env(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        name, default = match.group(1), match.group(2) or ""
        return os.environ.get(name, default)

    return _ENV_VAR.sub(repl, value)


@dataclass
class ToolPolicy:
    enabled: bool = True
    rate_limit_per_min: int = 60
    redact_args: list[str] = field(default_factory=list)
    description_override: str | None = None


@dataclass
class ServerSpec:
    id: str
    transport: str
    autostart: bool = True
    description: str = ""
    command: str | None = None
    args: list[str] = field(default_factory=list)
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class RegisteredTool:
    server_id: str
    tool_id: str
    description: str
    schema: dict[str, Any]
    policy: ToolPolicy

    @property
    def qualified_name(self) -> str:
        return f"{self.server_id}__{self.tool_id}"


class RateLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}

    def allow(self, key: str, limit_per_min: int) -> bool:
        now = time.monotonic()
        window = self._windows.setdefault(key, [])
        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.pop(0)
        if len(window) >= limit_per_min:
            return False
        window.append(now)
        return True


class MCPClient:
    def __init__(self, config_path: Path, manifest_path: Path) -> None:
        self._config_path = config_path
        self._manifest_path = manifest_path
        self._servers: dict[str, ServerSpec] = {}
        self._policies: dict[tuple[str, str], ToolPolicy] = {}
        self._tools: dict[str, RegisteredTool] = {}
        self._http_clients: dict[str, httpx.AsyncClient] = {}
        self._stdio_procs: dict[str, asyncio.subprocess.Process] = {}
        self._rate = RateLimiter()

    async def start(self) -> None:
        self._load_config()
        self._load_manifest()
        for server in self._servers.values():
            if not server.autostart:
                continue
            try:
                await self._connect(server)
            except Exception:  # pragma: no cover - network/env dependent
                logger.exception("Failed to start MCP server %s", server.id)
        logger.info("MCP started with %d tools", len(self._tools))

    async def stop(self) -> None:
        for client in self._http_clients.values():
            await client.aclose()
        for proc in self._stdio_procs.values():
            if proc.returncode is not None:
                continue
            try:
                proc.terminate()
            except ProcessLookupError:
                continue
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass

    def _load_config(self) -> None:
        data = json.loads(self._config_path.read_text())
        for sid, cfg in data.get("servers", {}).items():
            self._servers[sid] = ServerSpec(
                id=sid,
                transport=cfg.get("transport", "stdio"),
                autostart=cfg.get("autostart", True),
                description=cfg.get("description", ""),
                command=cfg.get("command"),
                args=[_expand_env(a) for a in cfg.get("args", [])],
                url=_expand_env(cfg["url"]) if cfg.get("url") else None,
                headers={k: _expand_env(v) for k, v in cfg.get("headers", {}).items()},
            )

    def _load_manifest(self) -> None:
        data = yaml.safe_load(self._manifest_path.read_text()) or {}
        for sid, tools in data.items():
            for tid, policy_raw in (tools or {}).items():
                if not isinstance(policy_raw, dict):
                    continue
                self._policies[(sid, tid)] = ToolPolicy(
                    enabled=policy_raw.get("enabled", True),
                    rate_limit_per_min=policy_raw.get("rate_limit_per_min", 60),
                    redact_args=list(policy_raw.get("redact_args", [])),
                    description_override=policy_raw.get("description_override"),
                )

    async def _connect(self, server: ServerSpec) -> None:
        if server.transport == "http":
            client = httpx.AsyncClient(base_url=server.url or "", headers=server.headers, timeout=30)
            self._http_clients[server.id] = client
            tools = await self._discover_http(server.id, client)
        elif server.transport == "stdio":
            tools = await self._discover_stdio(server)
        else:
            raise ValueError(f"Unknown MCP transport: {server.transport}")
        for tool in tools:
            policy = self._policies.get((server.id, tool["name"]))
            if policy is None or not policy.enabled:
                logger.info("Skip tool %s:%s (not whitelisted)", server.id, tool["name"])
                continue
            reg = RegisteredTool(
                server_id=server.id,
                tool_id=tool["name"],
                description=policy.description_override or tool.get("description", ""),
                schema=tool.get("inputSchema") or tool.get("parameters") or {"type": "object"},
                policy=policy,
            )
            self._tools[reg.qualified_name] = reg

    async def _discover_http(self, server_id: str, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        resp = await client.post("", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}).get("tools", [])

    async def _discover_stdio(self, server: ServerSpec) -> list[dict[str, Any]]:
        if not server.command:
            return []
        proc = await asyncio.create_subprocess_exec(
            server.command,
            *server.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._stdio_procs[server.id] = proc
        assert proc.stdin is not None and proc.stdout is not None
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        proc.stdin.write((json.dumps(request) + "\n").encode())
        await proc.stdin.drain()
        try:
            raw = await asyncio.wait_for(proc.stdout.readline(), timeout=10)
        except asyncio.TimeoutError:
            return []
        if not raw:
            return []
        try:
            return json.loads(raw).get("result", {}).get("tools", [])
        except json.JSONDecodeError:
            return []

    def as_tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(name=t.qualified_name, description=t.description, parameters=t.schema)
            for t in self._tools.values()
        ]

    def find(self, qualified_name: str) -> RegisteredTool | None:
        return self._tools.get(qualified_name)

    async def call(self, qualified_name: str, arguments: dict[str, Any]) -> Any:
        tool = self.find(qualified_name)
        if tool is None:
            raise PermissionError(f"Tool {qualified_name!r} is not whitelisted")
        if not self._rate.allow(qualified_name, tool.policy.rate_limit_per_min):
            raise RuntimeError(f"Rate limit exceeded for {qualified_name}")

        server = self._servers[tool.server_id]
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "tools/call",
            "params": {"name": tool.tool_id, "arguments": arguments},
        }
        if server.transport == "http":
            client = self._http_clients[server.id]
            resp = await client.post("", json=payload)
            resp.raise_for_status()
            return resp.json().get("result")
        if server.transport == "stdio":
            proc = self._stdio_procs.get(server.id)
            if proc is None or proc.stdin is None or proc.stdout is None:
                raise RuntimeError(f"stdio MCP server {server.id} is not running")
            proc.stdin.write((json.dumps(payload) + "\n").encode())
            await proc.stdin.drain()
            raw = await asyncio.wait_for(proc.stdout.readline(), timeout=30)
            return json.loads(raw).get("result") if raw else None
        raise ValueError(f"Unknown transport {server.transport!r}")

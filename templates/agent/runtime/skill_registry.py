"""Загрузка YAML-скиллов и их диспетчеризация.

Зависимости намеренно минимальные: YAML + jsonschema-like валидация, без тяжёлых
библиотек. Это делает реестр тестируемым в оффлайне.
"""

from __future__ import annotations

import importlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml  # type: ignore

logger = logging.getLogger("runtime.skills")

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_TOOL_RE = re.compile(r"^[A-Za-z0-9._-]+:[A-Za-z0-9._-]+$")


@dataclass
class SkillLimits:
    tool_call_budget: int = 8
    max_duration_sec: int = 120
    max_delegation_depth: int = 3


@dataclass
class Skill:
    id: str
    name: str
    version: str
    handler: str
    inputs: dict[str, dict[str, Any]]
    outputs: dict[str, dict[str, Any]]
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    tags: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    peers: list[str] = field(default_factory=list)
    prompt: str = ""
    limits: SkillLimits = field(default_factory=SkillLimits)
    expose_a2a: bool = True
    source_path: Path | None = None


SkillHandler = Callable[["SkillContext"], Awaitable[dict[str, Any]]]


class SkillContext:
    """Аргументы и сервисы, которые получает хендлер скилла при исполнении."""

    def __init__(
        self,
        skill: Skill,
        input: dict[str, Any],
        services: "SkillServices",
        trace_id: str,
        delegation_depth: int = 0,
    ) -> None:
        self.skill = skill
        self.input = input
        self.services = services
        self.trace_id = trace_id
        self.delegation_depth = delegation_depth


@dataclass
class SkillServices:
    """Набор сервисов, прокинутых в хендлер скилла.

    Конкретные реализации (llm, mcp, a2a_client, memory) подставляются в
    `runtime/agent.py` при старте.
    """

    llm: Any
    mcp: Any
    a2a_client_factory: Any
    memory: Any
    registry: "SkillRegistry"


class SkillValidationError(ValueError):
    pass


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self._dir = skills_dir
        self._skills: dict[str, Skill] = {}
        self._by_alias: dict[str, str] = {}
        self._python_handlers: dict[str, SkillHandler] = {}

    # ------------------------- загрузка и валидация -------------------------

    def load(self) -> None:
        for path in sorted(self._dir.glob("*.yaml")):
            if path.name.startswith("_"):
                continue
            skill = self._parse_file(path)
            self._skills[skill.id] = skill
            for alias in skill.aliases:
                self._by_alias[alias] = skill.id

    def _parse_file(self, path: Path) -> Skill:
        data = yaml.safe_load(path.read_text()) or {}
        self._validate(data, path)
        limits = SkillLimits(**(data.get("limits") or {}))
        skill = Skill(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            handler=data["handler"],
            inputs=data["inputs"],
            outputs=data["outputs"],
            aliases=list(data.get("aliases") or []),
            description=data.get("description", ""),
            tags=list(data.get("tags") or []),
            tools=list(data.get("tools") or []),
            peers=list(data.get("peers") or []),
            prompt=data.get("prompt", ""),
            limits=limits,
            expose_a2a=bool(data.get("expose_a2a", True)),
            source_path=path,
        )
        return skill

    def _validate(self, data: dict[str, Any], path: Path) -> None:
        for field_name in ("id", "name", "version", "handler", "inputs", "outputs"):
            if field_name not in data:
                raise SkillValidationError(f"{path}: missing required field {field_name!r}")
        if not _ID_RE.match(data["id"]):
            raise SkillValidationError(f"{path}: invalid id {data['id']!r}")
        if not _SEMVER_RE.match(data["version"]):
            raise SkillValidationError(f"{path}: invalid version {data['version']!r}")
        handler = data["handler"]
        if not (
            handler == "llm"
            or handler.startswith("python:")
            or handler.startswith("a2a:")
        ):
            raise SkillValidationError(f"{path}: invalid handler {handler!r}")
        for tool in data.get("tools") or []:
            if not _TOOL_RE.match(tool):
                raise SkillValidationError(f"{path}: invalid tool id {tool!r}")

    # --------------------------- публичное API -----------------------------

    def all(self) -> list[Skill]:
        return list(self._skills.values())

    def resolve(self, key: str) -> Skill | None:
        if key in self._skills:
            return self._skills[key]
        alias = self._by_alias.get(key)
        return self._skills.get(alias) if alias else None

    def register_python_handler(self, dotted: str, fn: SkillHandler) -> None:
        self._python_handlers[dotted] = fn

    async def dispatch(self, ctx: SkillContext) -> dict[str, Any]:
        skill = ctx.skill
        self._assert_inputs(skill, ctx.input)
        if skill.handler == "llm":
            return await self._run_llm(ctx)
        if skill.handler.startswith("python:"):
            fn = self._resolve_python(skill.handler)
            return await fn(ctx)
        if skill.handler.startswith("a2a:"):
            peer = skill.handler.removeprefix("a2a:")
            return await self._run_a2a(ctx, peer)
        raise SkillValidationError(f"Unknown handler {skill.handler!r}")

    # ---------------------------- исполнители ------------------------------

    def _resolve_python(self, dotted: str) -> SkillHandler:
        if dotted in self._python_handlers:
            return self._python_handlers[dotted]
        spec = dotted.removeprefix("python:")
        if ":" in spec:
            module_name, func_name = spec.split(":", 1)
        else:
            module_name, _, func_name = spec.rpartition(".")
        module = importlib.import_module(module_name)
        fn = getattr(module, func_name)
        self._python_handlers[dotted] = fn
        return fn

    async def _run_llm(self, ctx: SkillContext) -> dict[str, Any]:
        from .llm import LLMMessage

        llm = ctx.services.llm
        mcp = ctx.services.mcp
        prompt = _render_prompt(ctx.skill.prompt, ctx.input)
        tools = [t for t in mcp.as_tool_specs() if t.name.replace("__", ":", 1) in ctx.skill.tools]
        messages = [LLMMessage(role="user", content=prompt)]
        budget = ctx.skill.limits.tool_call_budget

        while budget > 0:
            resp = await llm.chat(messages, tools=tools)
            if resp.tool_calls:
                for call in resp.tool_calls:
                    fn = call["function"]
                    result = await mcp.call(fn["name"], _safe_json(fn.get("arguments") or "{}"))
                    messages.append(LLMMessage(role="assistant", tool_calls=[call]))
                    messages.append(
                        LLMMessage(
                            role="tool",
                            tool_call_id=call["id"],
                            name=fn["name"],
                            content=_json_dumps(result),
                        )
                    )
                budget -= 1
                continue
            return _coerce_outputs(resp.content or "", ctx.skill)
        raise RuntimeError(f"Skill {ctx.skill.id} exceeded tool_call_budget")

    async def _run_a2a(self, ctx: SkillContext, peer: str) -> dict[str, Any]:
        from ..a2a.schemas import TaskContext, TaskRequest

        if ctx.delegation_depth >= ctx.skill.limits.max_delegation_depth:
            raise RuntimeError("Delegation depth exceeded")
        client = ctx.services.a2a_client_factory(peer)
        async with client as c:
            req = TaskRequest(
                skill_id=ctx.input.get("skill_id", ctx.skill.id),
                input=ctx.input.get("input", ctx.input),
                stream=True,
                context=TaskContext(delegation_depth=ctx.delegation_depth + 1),
                deadline_sec=ctx.input.get("deadline_sec", 120),
            )
            task = await c.run_until_final(req)
        return {"status": task["status"], "output": task.get("output") or {}, "events": []}

    def _assert_inputs(self, skill: Skill, values: dict[str, Any]) -> None:
        for name, spec in skill.inputs.items():
            if spec.get("required") and name not in values:
                raise SkillValidationError(f"{skill.id}: missing required input {name!r}")


def _render_prompt(template: str, values: dict[str, Any]) -> str:
    result = template
    for key, value in values.items():
        result = result.replace("{{" + key + "}}", _json_dumps(value) if not isinstance(value, str) else value)
    return result


def _safe_json(raw: str) -> dict[str, Any]:
    import json

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def _json_dumps(value: Any) -> str:
    import json

    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)


def _coerce_outputs(raw: str, skill: Skill) -> dict[str, Any]:
    import json

    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    if len(skill.outputs) == 1:
        (only,) = skill.outputs.keys()
        return {only: raw}
    return {"raw": raw}

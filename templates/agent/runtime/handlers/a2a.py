"""Хендлеры, связанные с A2A."""

from __future__ import annotations

from typing import Any

from ...a2a.schemas import TaskContext, TaskRequest
from ..skill_registry import SkillContext


async def delegate(ctx: SkillContext) -> dict[str, Any]:
    """Реализация `skills/a2a.delegate.yaml`.

    Берёт `peer` и `skill_id`, вызывает A2A-клиент, возвращает результат.
    """

    peer = ctx.input["peer"]
    skill_id = ctx.input["skill_id"]
    inp = ctx.input.get("input", {})
    deadline = int(ctx.input.get("deadline_sec", 120))

    client = ctx.services.a2a_client_factory(peer)
    async with client as c:
        req = TaskRequest(
            skill_id=skill_id,
            input=inp,
            stream=bool(ctx.input.get("stream", True)),
            context=TaskContext(
                trace_id=ctx.trace_id if isinstance(ctx.trace_id, type(TaskContext().trace_id)) else TaskContext().trace_id,
                delegation_depth=ctx.delegation_depth + 1,
            ),
            deadline_sec=deadline,
        )
        events: list[dict[str, Any]] = []

        async def on_event(event):
            events.append(event.model_dump(mode="json"))

        task = await c.run_until_final(req, on_event=on_event)
        ctx.services.memory.record(
            "a2a.delegate",
            peer=peer,
            skill_id=skill_id,
            status=task.get("status"),
            trace_id=str(ctx.trace_id),
        )
        return {
            "status": task.get("status"),
            "output": task.get("output") or {},
            "events": events,
        }


async def noop(ctx: SkillContext) -> dict[str, Any]:
    """Заглушка для скиллов, у которых ещё нет реализации.

    Полезна, чтобы не блокировать активацию агента, пока скилл в разработке.
    """

    return {
        "status": "unsupported",
        "reason": f"Skill {ctx.skill.id!r} has no implementation yet",
    }

"""Skill registry — loads and dispatches skills by ID."""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .base import BaseSkill, SkillResult

if TYPE_CHECKING:
    from ..mcp.registry import MCPRegistry

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self, mcp_registry: "MCPRegistry | None" = None) -> None:
        self.mcp = mcp_registry
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.id] = skill
        logger.debug("Registered skill: %s", skill.id)

    def get(self, skill_id: str) -> BaseSkill | None:
        return self._skills.get(skill_id)

    def list_skills(self) -> list[BaseSkill]:
        return list(self._skills.values())

    async def execute(self, skill_id: str, **kwargs: Any) -> SkillResult:
        skill = self.get(skill_id)
        if skill is None:
            return SkillResult(
                success=False,
                output="",
                error=f"Skill '{skill_id}' not found.",
            )
        try:
            return await skill.execute(**kwargs)
        except Exception as exc:
            logger.exception("Skill '%s' raised an exception", skill_id)
            return SkillResult(success=False, output="", error=str(exc))

    def skills_description(self) -> str:
        lines = [skill.describe() for skill in self._skills.values()]
        return "\n".join(lines) if lines else "(no skills loaded)"

"""Base class for all skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..mcp.registry import MCPRegistry


@dataclass
class SkillResult:
    success: bool
    output: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseSkill(ABC):
    """Abstract base for agent skills."""

    id: str = ""
    name: str = ""
    description: str = ""
    input_modes: list[str] = ["text"]
    output_modes: list[str] = ["text"]

    def __init__(self, mcp_registry: "MCPRegistry | None" = None) -> None:
        self.mcp = mcp_registry

    @abstractmethod
    async def execute(self, **kwargs: Any) -> SkillResult:
        """Run the skill with given keyword arguments."""
        ...

    def describe(self) -> str:
        return f"**{self.name}** (`{self.id}`): {self.description}"

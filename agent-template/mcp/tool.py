"""MCP Tool abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    content: list[dict[str, Any]]
    is_error: bool = False

    @property
    def text(self) -> str:
        parts = []
        for item in self.content:
            if item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(parts)


@dataclass
class MCPTool:
    """Represents a single tool exposed by an MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any]
    server_name: str
    # Callable injected by MCPRegistry — wraps the actual MCP call
    _call: Any = field(repr=False, default=None)

    async def call(self, **kwargs: Any) -> ToolResult:
        if self._call is None:
            raise RuntimeError(f"Tool '{self.name}' has no executor attached.")
        return await self._call(**kwargs)

    def to_openai_function(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

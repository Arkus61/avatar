"""Unit tests for MCPRegistry (no real subprocess — tests the interface)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mcp.registry import MCPRegistry
from mcp.tool import MCPTool, ToolResult


def _make_tool(name: str, server: str = "test") -> MCPTool:
    async def executor(**kwargs):
        return ToolResult(content=[{"type": "text", "text": f"{name} ok"}])
    tool = MCPTool(
        name=name,
        description=f"{name} description",
        input_schema={"type": "object", "properties": {}},
        server_name=server,
    )
    tool._call = executor
    return tool


@pytest.mark.asyncio
async def test_get_tool_returns_none_for_unknown():
    registry = MCPRegistry()
    assert registry.get_tool("nonexistent") is None


@pytest.mark.asyncio
async def test_call_tool_missing_returns_error():
    registry = MCPRegistry()
    result = await registry.call_tool("missing_tool")
    assert result.is_error
    assert "not found" in result.text


@pytest.mark.asyncio
async def test_tools_description_empty():
    registry = MCPRegistry()
    desc = registry.tools_description()
    assert "no MCP tools" in desc


def test_tool_to_openai_function():
    tool = _make_tool("read_file", "filesystem")
    schema = tool.to_openai_function()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "read_file"


def test_tool_to_anthropic_tool():
    tool = _make_tool("search", "brave")
    schema = tool.to_anthropic_tool()
    assert schema["name"] == "search"
    assert "input_schema" in schema

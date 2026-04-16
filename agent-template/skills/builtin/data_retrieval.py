"""DataRetrieval skill — fetches data using MCP tools (search, filesystem, DB)."""

from __future__ import annotations

from typing import Any

from ..base import BaseSkill, SkillResult


class DataRetrievalSkill(BaseSkill):
    id = "data_retrieval"
    name = "Data Retrieval"
    description = "Retrieves data from configured MCP sources (filesystem, search, database)."

    async def execute(
        self,
        query: str = "",
        source: str = "search",   # "search" | "filesystem" | "database"
        **kwargs: Any,
    ) -> SkillResult:
        if not query:
            return SkillResult(success=False, output="", error="'query' parameter is required.")

        if self.mcp is None:
            return SkillResult(
                success=False, output="",
                error="MCP registry not available for DataRetrievalSkill.",
            )

        # Route to the appropriate MCP tool based on source
        tool_map = {
            "search": ("brave_web_search", {"query": query}),
            "filesystem": ("read_file", {"path": query}),
            "database": ("query", {"sql": query}),
        }

        if source not in tool_map:
            return SkillResult(
                success=False, output="",
                error=f"Unknown source '{source}'. Choose from: {list(tool_map.keys())}",
            )

        tool_name, tool_kwargs = tool_map[source]
        result = await self.mcp.call_tool(tool_name, **tool_kwargs)

        if result.is_error:
            return SkillResult(success=False, output="", error=result.text)

        return SkillResult(
            success=True,
            output=result.text,
            data={"source": source, "query": query},
        )

"""Summarization skill — condenses long content."""

from __future__ import annotations

from typing import Any

from ..base import BaseSkill, SkillResult


class SummarizationSkill(BaseSkill):
    id = "summarization"
    name = "Summarization"
    description = "Produces a concise summary of long text or documents."

    async def execute(
        self,
        text: str = "",
        max_words: int = 100,
        **kwargs: Any,
    ) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="'text' parameter is required.")

        # Placeholder — replace with actual LLM call or MCP tool call
        words = text.split()
        truncated = " ".join(words[:max_words])
        summary = f"[Summary of {len(words)} words → {max_words} words]: {truncated}..."

        return SkillResult(
            success=True,
            output=summary,
            data={"original_word_count": len(words), "max_words": max_words},
        )

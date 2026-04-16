"""TextAnalysis skill — sentiment, entities, keywords."""

from __future__ import annotations

from typing import Any

from ..base import BaseSkill, SkillResult


class TextAnalysisSkill(BaseSkill):
    id = "text_analysis"
    name = "Text Analysis"
    description = "Analyzes text for sentiment, named entities, and key topics."

    async def execute(self, text: str = "", **kwargs: Any) -> SkillResult:
        if not text:
            return SkillResult(success=False, output="", error="'text' parameter is required.")

        # In a real agent this calls the LLM or a dedicated NLP MCP tool.
        # Here we show the contract; replace with actual LLM call.
        prompt = (
            f"Analyze the following text and return JSON with keys: "
            f"sentiment (positive/negative/neutral), entities (list), keywords (list).\n\n"
            f"Text:\n{text}"
        )
        # Placeholder — swap for real LLM invocation
        analysis = {
            "sentiment": "neutral",
            "entities": [],
            "keywords": text.split()[:5],
            "prompt_used": prompt,
        }
        return SkillResult(
            success=True,
            output=f"Sentiment: {analysis['sentiment']}, Keywords: {analysis['keywords']}",
            data=analysis,
        )

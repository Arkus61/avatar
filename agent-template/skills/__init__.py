"""Skills — reusable higher-level capabilities built on top of MCP tools."""

from .base import BaseSkill, SkillResult
from .registry import SkillRegistry
from .builtin.text_analysis import TextAnalysisSkill
from .builtin.summarization import SummarizationSkill
from .builtin.data_retrieval import DataRetrievalSkill
from .builtin.agent_delegation import AgentDelegationSkill

__all__ = [
    "BaseSkill",
    "SkillResult",
    "SkillRegistry",
    "TextAnalysisSkill",
    "SummarizationSkill",
    "DataRetrievalSkill",
    "AgentDelegationSkill",
]

"""Unit tests for builtin skills."""

import pytest
from skills.builtin.text_analysis import TextAnalysisSkill
from skills.builtin.summarization import SummarizationSkill
from skills.builtin.agent_delegation import AgentDelegationSkill
from skills.registry import SkillRegistry


@pytest.mark.asyncio
async def test_text_analysis_empty_input():
    skill = TextAnalysisSkill()
    result = await skill.execute(text="")
    assert not result.success
    assert result.error


@pytest.mark.asyncio
async def test_text_analysis_with_text():
    skill = TextAnalysisSkill()
    result = await skill.execute(text="This is a great product!")
    assert result.success
    assert "Sentiment" in result.output


@pytest.mark.asyncio
async def test_summarization_empty():
    skill = SummarizationSkill()
    result = await skill.execute(text="")
    assert not result.success


@pytest.mark.asyncio
async def test_summarization_truncates():
    skill = SummarizationSkill()
    long_text = " ".join(["word"] * 200)
    result = await skill.execute(text=long_text, max_words=10)
    assert result.success
    assert result.data["max_words"] == 10


@pytest.mark.asyncio
async def test_delegation_unknown_agent():
    skill = AgentDelegationSkill(peer_clients={})
    result = await skill.execute(task="do something", target_agent_id="ghost-agent")
    assert not result.success
    assert "Unknown agent" in (result.error or "")


@pytest.mark.asyncio
async def test_skill_registry_unknown_skill():
    registry = SkillRegistry()
    result = await registry.execute("nonexistent_skill")
    assert not result.success
    assert "not found" in (result.error or "")


@pytest.mark.asyncio
async def test_skill_registry_registers_and_executes():
    registry = SkillRegistry()
    skill = SummarizationSkill()
    registry.register(skill)
    result = await registry.execute("summarization", text="hello world again")
    assert result.success

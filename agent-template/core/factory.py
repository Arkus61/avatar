"""Agent factory — builds a fully wired Agent from a config file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from ..a2a.client import A2AClient
from ..a2a.models import AgentCard, AgentCapabilities, AgentSkillDescriptor
from ..a2a.server import A2AServer
from ..mcp.registry import MCPRegistry
from ..skills.registry import SkillRegistry
from ..skills.builtin.text_analysis import TextAnalysisSkill
from ..skills.builtin.summarization import SummarizationSkill
from ..skills.builtin.data_retrieval import DataRetrievalSkill
from ..skills.builtin.agent_delegation import AgentDelegationSkill
from .agent import Agent

_BUILTIN_SKILLS = {
    "text_analysis": TextAnalysisSkill,
    "summarization": SummarizationSkill,
    "data_retrieval": DataRetrievalSkill,
    "agent_delegation": None,   # needs peer_clients — handled separately
}


async def build_agent_from_config(config_path: str | Path) -> tuple[Agent, A2AServer]:
    """
    Reads agent_config.yaml and assembles:
      - MCPRegistry (connects to all configured MCP servers)
      - SkillRegistry (instantiates enabled skills)
      - LLM client
      - A2AClient for each peer
      - Agent (core runtime)
      - A2AServer (FastAPI app exposing /a2a)

    Returns (agent, a2a_server).
    Run the server with:
        import uvicorn
        uvicorn.run(a2a_server.app, host=cfg_a2a["host"], port=cfg_a2a["port"])
    """
    config_path = Path(config_path)
    raw = yaml.safe_load(config_path.read_text())
    cfg: dict = raw["agent"]

    agent_id: str = cfg["id"]
    agent_name: str = cfg["name"]
    agent_version: str = cfg["version"]
    cfg_a2a: dict = cfg.get("a2a", {})
    cfg_mcp: dict = cfg.get("mcp", {})
    cfg_llm: dict = cfg.get("llm", {})
    cfg_skills: dict = cfg.get("skills", {})
    peers: list[dict] = cfg_a2a.get("peers", [])

    # ------------------------------------------------------------------
    # MCP Registry
    # ------------------------------------------------------------------
    mcp_registry = MCPRegistry()
    for srv in cfg_mcp.get("servers", []):
        env = {k: os.path.expandvars(v) for k, v in (srv.get("env") or {}).items()}
        await mcp_registry.add_server(
            name=srv["name"],
            command=srv["command"],
            env=env,
        )

    # ------------------------------------------------------------------
    # LLM client
    # ------------------------------------------------------------------
    llm_client = _build_llm_client(cfg_llm)

    # ------------------------------------------------------------------
    # A2A peer clients
    # ------------------------------------------------------------------
    peer_clients: dict[str, A2AClient] = {}
    for peer in peers:
        peer_clients[peer["id"]] = A2AClient(base_url=peer["url"])

    # ------------------------------------------------------------------
    # Skill Registry
    # ------------------------------------------------------------------
    skill_registry = SkillRegistry(mcp_registry=mcp_registry)
    enabled: list[str] = cfg_skills.get("enabled", [])

    for skill_id in enabled:
        if skill_id == "agent_delegation":
            skill = AgentDelegationSkill(
                mcp_registry=mcp_registry,
                peer_clients=peer_clients,
            )
        elif skill_id in _BUILTIN_SKILLS:
            cls = _BUILTIN_SKILLS[skill_id]
            skill = cls(mcp_registry=mcp_registry)  # type: ignore[misc]
        else:
            continue
        skill_registry.register(skill)

    # ------------------------------------------------------------------
    # Core Agent
    # ------------------------------------------------------------------
    agent = Agent(
        agent_id=agent_id,
        name=agent_name,
        version=agent_version,
        mcp_registry=mcp_registry,
        skill_registry=skill_registry,
        llm_client=llm_client,
        llm_model=cfg_llm.get("model", "gpt-4o-mini"),
        peers=peers,
        peer_clients=peer_clients,
    )

    # ------------------------------------------------------------------
    # A2A Server
    # ------------------------------------------------------------------
    base_url = (
        f"http://{cfg_a2a.get('host', '0.0.0.0')}:{cfg_a2a.get('port', 8100)}"
    )
    skill_descriptors = [
        AgentSkillDescriptor(
            id=s.id,
            name=s.name,
            description=s.description,
        )
        for s in skill_registry.list_skills()
    ]
    agent_card = AgentCard(
        name=agent_name,
        description=cfg.get("description", ""),
        url=base_url,
        version=agent_version,
        capabilities=AgentCapabilities(),
        skills=skill_descriptors,
    )
    a2a_server = A2AServer(
        agent_card=agent_card,
        task_handler=agent.handle_a2a_task,
    )

    return agent, a2a_server


def _build_llm_client(cfg: dict) -> Any:
    provider = cfg.get("provider", "openai").lower()
    api_key = os.environ.get(cfg.get("api_key_env", "OPENAI_API_KEY"), "")

    if provider == "openai":
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=api_key)

    if provider == "anthropic":
        from anthropic import AsyncAnthropic
        return AsyncAnthropic(api_key=api_key)

    if provider == "ollama":
        from openai import AsyncOpenAI
        return AsyncOpenAI(
            api_key="ollama",
            base_url=cfg.get("base_url", "http://localhost:11434/v1"),
        )

    if provider == "azure":
        from openai import AsyncAzureOpenAI
        return AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            api_version=cfg.get("api_version", "2024-02-01"),
        )

    raise ValueError(f"Unsupported LLM provider: {provider}")

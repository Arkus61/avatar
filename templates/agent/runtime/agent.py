"""Главный класс агента: грузит манифест, связывает все подсистемы, гоняет цикл."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml  # type: ignore

from ..a2a.client import A2AClient
from ..a2a.schemas import AgentCard, EventKind, TaskEvent, TaskStatus
from ..a2a.server import SkillDispatcher, TaskStore, build_app
from .llm import EchoLLM, LLMProvider, OpenAIChatLLM
from .mcp_client import MCPClient
from .memory import EpisodicMemory, ShortTermMemory
from .skill_registry import Skill, SkillContext, SkillRegistry, SkillServices

logger = logging.getLogger("runtime.agent")


@dataclass
class AgentPaths:
    root: Path
    manifest: Path
    instructions_dir: Path
    skills_dir: Path
    mcp_config: Path
    mcp_manifest: Path
    agent_card: Path


@dataclass
class AgentConfig:
    raw: dict[str, Any]
    paths: AgentPaths
    llm_provider_name: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    allow_peers: list[str]
    expose_skills: list[str]
    peers: dict[str, dict[str, Any]] = field(default_factory=dict)


class Agent:
    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.registry = SkillRegistry(config.paths.skills_dir)
        self.mcp = MCPClient(config.paths.mcp_config, config.paths.mcp_manifest)
        self.llm: LLMProvider = self._make_llm()
        self.memory_short = ShortTermMemory(
            max_messages=int(config.raw.get("memory", {}).get("short_term", {}).get("max_messages", 40))
        )
        episodic_path = Path(
            config.raw.get("memory", {})
            .get("episodic", {})
            .get("path", "_state/episodic.jsonl")
        )
        if not episodic_path.is_absolute():
            episodic_path = config.paths.root / episodic_path
        self.memory_episodic = EpisodicMemory(episodic_path)
        self.card = self._build_agent_card()
        self._system_prompt = self._compose_system_prompt()

    # ------------------------------ bootstrap ------------------------------

    async def start(self) -> None:
        await self.mcp.start()
        self.registry.load()
        logger.info(
            "Agent %s started. Tools: %d. Skills: %d.",
            self.config.raw["agent"]["id"],
            len(self.mcp.as_tool_specs()),
            len(self.registry.all()),
        )

    async def stop(self) -> None:
        await self.mcp.stop()

    # ------------------------------- run -----------------------------------

    async def handle_user_message(self, text: str, trace_id: str) -> dict[str, Any]:
        """Простейший цикл: пытаемся сопоставить текст со скиллом или идём в LLM."""

        self.memory_short.append("user", text, trace_id=trace_id)
        skill = self._match_skill(text)
        if skill is not None:
            inputs = {"query": text} if "query" in skill.inputs else {}
            return await self.run_skill(skill, inputs, trace_id=trace_id)
        return {"text": f"(no skill matched) {text}"}

    async def run_skill(
        self,
        skill: Skill,
        inputs: dict[str, Any],
        *,
        trace_id: str,
        delegation_depth: int = 0,
    ) -> dict[str, Any]:
        services = SkillServices(
            llm=self.llm,
            mcp=self.mcp,
            a2a_client_factory=self._a2a_client_factory,
            memory=self.memory_episodic,
            registry=self.registry,
        )
        ctx = SkillContext(
            skill=skill,
            input=inputs,
            services=services,
            trace_id=trace_id,
            delegation_depth=delegation_depth,
        )
        try:
            result = await self.registry.dispatch(ctx)
            self.memory_episodic.record(
                "skill.run",
                skill_id=skill.id,
                trace_id=trace_id,
                status="completed",
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive
            self.memory_episodic.record(
                "skill.run",
                skill_id=skill.id,
                trace_id=trace_id,
                status="failed",
                error=str(exc),
            )
            raise

    # ------------------------------- A2A -----------------------------------

    def build_a2a_app(self) -> Any:
        dispatcher = _LocalSkillDispatcher(self)
        return build_app(
            card=self.card,
            dispatcher=dispatcher,
            store=TaskStore(),
            allow_peers=self.config.allow_peers,
        )

    def _a2a_client_factory(self, peer: str) -> A2AClient:
        peer_info = self.config.peers.get(peer)
        if peer_info is None:
            url = peer if peer.startswith("http") else f"http://{peer}"
            return A2AClient(base_url=url)
        return A2AClient(
            base_url=peer_info["url"],
            auth_header=peer_info.get("auth"),
            peer_id=self.config.raw["agent"]["id"],
            timeout=float(peer_info.get("timeout", 60)),
        )

    # ----------------------------- helpers ---------------------------------

    def _make_llm(self) -> LLMProvider:
        name = self.config.llm_provider_name
        if name == "openai":
            try:
                return OpenAIChatLLM(self.config.llm_model)
            except Exception as exc:
                logger.warning("Falling back to EchoLLM: %s", exc)
        return EchoLLM()

    def _compose_system_prompt(self) -> str:
        chunks: list[str] = []
        for name in self.config.raw.get("instructions", {}).get("order", []):
            path = self.config.paths.instructions_dir / name
            if path.exists():
                chunks.append(path.read_text(encoding="utf-8"))
        return "\n\n".join(chunks)

    def _build_agent_card(self) -> AgentCard:
        card_data = json.loads(self.config.paths.agent_card.read_text())
        card = AgentCard.model_validate(card_data)
        card.id = self.config.raw["agent"]["id"]
        card.name = self.config.raw["agent"]["name"]
        card.version = self.config.raw["agent"]["version"]
        card.url = self.config.raw["a2a"]["server"]["public_url"]
        return card

    def _match_skill(self, text: str) -> Skill | None:
        text_lower = text.lower()
        for skill in self.registry.all():
            if skill.id in text_lower:
                return skill
            if any(alias.lower() in text_lower for alias in skill.aliases):
                return skill
        return None

    @property
    def system_prompt(self) -> str:
        return self._system_prompt


class _LocalSkillDispatcher(SkillDispatcher):
    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    async def dispatch(self, task, store) -> None:  # type: ignore[override]
        skill = self._agent.registry.resolve(task.skill_id)
        if skill is None:
            await store.update_status(task.id, TaskStatus.FAILED, error=f"unknown skill {task.skill_id}")
            await store.emit(
                task.id,
                TaskEvent(task_id=task.id, kind=EventKind.ERROR, data={"error": "unknown skill"}),
            )
            return
        try:
            output = await self._agent.run_skill(
                skill,
                dict(task.input),
                trace_id=str(task.context.trace_id),
                delegation_depth=task.context.delegation_depth,
            )
        except Exception as exc:
            await store.update_status(task.id, TaskStatus.FAILED, error=str(exc))
            await store.emit(
                task.id,
                TaskEvent(task_id=task.id, kind=EventKind.ERROR, data={"error": str(exc)}),
            )
            return
        await store.update_status(task.id, TaskStatus.COMPLETED, output=output)
        await store.emit(
            task.id,
            TaskEvent(task_id=task.id, kind=EventKind.FINAL, data={"output": output}),
        )


# ================================ loader =====================================


def load_agent(root: Path | str | None = None) -> Agent:
    root_path = Path(root or Path(__file__).resolve().parent.parent).resolve()
    manifest_path = root_path / "agent.yaml"
    raw = yaml.safe_load(manifest_path.read_text()) or {}

    paths = AgentPaths(
        root=root_path,
        manifest=manifest_path,
        instructions_dir=root_path / raw["instructions"]["dir"],
        skills_dir=root_path / raw["skills"]["dir"],
        mcp_config=root_path / raw["mcp"]["config"],
        mcp_manifest=root_path / raw["mcp"]["manifest"],
        agent_card=root_path / raw["a2a"]["card"],
    )
    config = AgentConfig(
        raw=raw,
        paths=paths,
        llm_provider_name=raw["llm"]["provider"],
        llm_model=raw["llm"]["model"],
        llm_temperature=float(raw["llm"].get("temperature", 0.2)),
        llm_max_tokens=int(raw["llm"].get("max_tokens", 4096)),
        allow_peers=list(raw["a2a"].get("allow_peers") or []),
        expose_skills=list(raw["a2a"].get("expose_skills") or ["*"]),
        peers=raw["a2a"].get("peers") or {},
    )
    return Agent(config)

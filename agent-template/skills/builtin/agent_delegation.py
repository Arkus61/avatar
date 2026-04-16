"""AgentDelegation skill — sends tasks to peer agents via A2A."""

from __future__ import annotations

from typing import Any

from ..base import BaseSkill, SkillResult


class AgentDelegationSkill(BaseSkill):
    id = "agent_delegation"
    name = "Agent Delegation"
    description = "Delegates a sub-task to a capable peer agent via the A2A protocol."

    def __init__(self, mcp_registry=None, peer_clients: dict | None = None) -> None:
        super().__init__(mcp_registry)
        # peer_clients: dict[agent_id, A2AClient]
        self.peer_clients = peer_clients or {}

    async def execute(
        self,
        task: str = "",
        target_agent_id: str = "",
        session_id: str | None = None,
        **kwargs: Any,
    ) -> SkillResult:
        if not task:
            return SkillResult(success=False, output="", error="'task' parameter is required.")
        if not target_agent_id:
            return SkillResult(success=False, output="", error="'target_agent_id' is required.")

        client = self.peer_clients.get(target_agent_id)
        if client is None:
            available = list(self.peer_clients.keys())
            return SkillResult(
                success=False,
                output="",
                error=f"Unknown agent '{target_agent_id}'. Available: {available}",
            )

        try:
            reply = await client.ask(task, session_id=session_id)
            return SkillResult(
                success=True,
                output=reply,
                data={"delegated_to": target_agent_id, "task": task},
            )
        except Exception as exc:
            return SkillResult(success=False, output="", error=str(exc))

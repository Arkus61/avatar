"""Instructions builder — reads template files and renders the final system prompt."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..mcp.registry import MCPRegistry
    from ..skills.registry import SkillRegistry

_TEMPLATE_DIR = Path(__file__).parent


class InstructionsBuilder:
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        agent_version: str,
        mcp_registry: "MCPRegistry",
        skill_registry: "SkillRegistry",
        peers: list[dict] | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.mcp = mcp_registry
        self.skills = skill_registry
        self.peers = peers or []

    def build(self) -> str:
        system_template = (_TEMPLATE_DIR / "system_prompt.md").read_text()
        persona = (_TEMPLATE_DIR / "persona.md").read_text()
        rules = (_TEMPLATE_DIR / "rules.md").read_text()

        peers_lines = [
            f"  - **{p['id']}**: {p.get('url', 'unknown')} "
            f"(capabilities: {', '.join(p.get('capabilities', []))})"
            for p in self.peers
        ]
        peers_list = "\n".join(peers_lines) if peers_lines else "  (no peer agents configured)"

        return system_template.format(
            agent_name=self.agent_name,
            agent_id=self.agent_id,
            agent_version=self.agent_version,
            persona=persona,
            mcp_tools_list=self.mcp.tools_description(),
            skills_list=self.skills.skills_description(),
            peers_list=peers_list,
            rules=rules,
        )

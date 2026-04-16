"""Core Agent — orchestrates MCP tools, skills, LLM, and A2A communication."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..a2a.models import (
    Task,
    TaskSendParams,
    TaskState,
    TaskStatus,
    Message,
    TextPart,
    Artifact,
)
from ..mcp.registry import MCPRegistry
from ..skills.registry import SkillRegistry
from ..instructions.builder import InstructionsBuilder

logger = logging.getLogger(__name__)


class Agent:
    """
    Main agent class. Wire everything together:
      - MCPRegistry for tool access
      - SkillRegistry for higher-level capabilities
      - LLM backend for reasoning
      - A2AServer for incoming tasks
      - A2AClient(s) for outgoing delegation
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str,
        mcp_registry: MCPRegistry,
        skill_registry: SkillRegistry,
        llm_client: Any,            # e.g. AsyncOpenAI or AsyncAnthropic
        llm_model: str,
        peers: list[dict] | None = None,
        peer_clients: dict | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.mcp = mcp_registry
        self.skills = skill_registry
        self.llm = llm_client
        self.llm_model = llm_model
        self.peers = peers or []
        self.peer_clients = peer_clients or {}

        self._instructions_builder = InstructionsBuilder(
            agent_id=agent_id,
            agent_name=name,
            agent_version=version,
            mcp_registry=mcp_registry,
            skill_registry=skill_registry,
            peers=self.peers,
        )
        self._system_prompt: str | None = None

    # ------------------------------------------------------------------
    # System prompt
    # ------------------------------------------------------------------

    def get_system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self._instructions_builder.build()
        return self._system_prompt

    def refresh_system_prompt(self) -> None:
        self._system_prompt = None

    # ------------------------------------------------------------------
    # A2A task handler  (called by A2AServer)
    # ------------------------------------------------------------------

    async def handle_a2a_task(self, params: TaskSendParams) -> Task:
        """Entry point for incoming A2A tasks."""
        logger.info("Received A2A task %s", params.id)

        # Extract text from message parts
        user_text = " ".join(
            part.text for part in params.message.parts if hasattr(part, "text")
        )

        try:
            response_text = await self._run(user_text, session_id=params.session_id)
            return Task(
                id=params.id,
                session_id=params.session_id,
                status=TaskStatus(
                    state=TaskState.COMPLETED,
                    message=Message(
                        role="agent",
                        parts=[TextPart(text=response_text)],
                    ),
                ),
                artifacts=[
                    Artifact(
                        name="response",
                        parts=[TextPart(text=response_text)],
                    )
                ],
            )
        except Exception as exc:
            logger.exception("Error handling A2A task %s", params.id)
            return Task(
                id=params.id,
                session_id=params.session_id,
                status=TaskStatus(
                    state=TaskState.FAILED,
                    message=Message(
                        role="agent",
                        parts=[TextPart(text=f"Error: {exc}")],
                    ),
                ),
            )

    # ------------------------------------------------------------------
    # Core reasoning loop (agentic loop with tool use)
    # ------------------------------------------------------------------

    async def _run(self, user_message: str, session_id: str | None = None) -> str:
        """
        Simple agentic loop:
        1. Send system prompt + user message to LLM.
        2. If LLM calls a tool → execute it via MCP or skills.
        3. Feed result back and continue until LLM returns a final text reply.
        """
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message},
        ]
        tools = [t.to_openai_function() for t in self.mcp.get_all_tools()]

        for iteration in range(10):   # max iterations guard
            response = await self._llm_call(messages, tools)

            # Check for tool calls
            tool_calls = getattr(response, "tool_calls", None)
            if tool_calls:
                # Append assistant message with tool_calls
                messages.append({"role": "assistant", "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in tool_calls
                ]})

                # Execute each tool call
                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    result = await self.mcp.call_tool(tool_name, **tool_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result.text,
                    })
                continue   # loop back with tool results

            # No tool calls → final response
            content = getattr(response, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Anthropic style
                return " ".join(
                    block.text for block in content if hasattr(block, "text")
                )
            return str(content)

        return "Max iterations reached. Please refine your request."

    async def _llm_call(self, messages: list[dict], tools: list[dict]) -> Any:
        """Call the LLM backend. Supports OpenAI-compatible clients."""
        return await self.llm.chat.completions.create(
            model=self.llm_model,
            system=self.get_system_prompt(),
            messages=messages,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )

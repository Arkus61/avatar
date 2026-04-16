"""LLM-абстракция с поддержкой function-calling.

В шаблоне есть:
- Protocol `LLMProvider` с одним методом `chat` (async).
- Реализация `EchoLLM` — детерминированная заглушка, нужна для unit-тестов и
  demo-запуска без ключей.
- Реализация `OpenAIChatLLM` — опциональная, активируется при наличии пакета `openai`.

Конкретный провайдер выбирается в `agent.yaml.llm.provider` и инстанцируется в
`runtime/agent.py`.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Protocol

logger = logging.getLogger("runtime.llm")


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class LLMMessage:
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: Any = None


class LLMProvider(Protocol):
    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        **kwargs: Any,
    ) -> LLMResponse: ...


class EchoLLM:
    """Детерминированная заглушка.

    Если в последнем сообщении встречается маркер '<<call:SERVER:TOOL>>', эмулирует
    tool-call. Если '<<final>>' — возвращает финальный ответ. Иначе — эхо.
    Предназначена для тестов без доступа к внешним LLM.
    """

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        last = messages[-1].content or ""
        if "<<call:" in last:
            marker = last.split("<<call:", 1)[1].split(">>", 1)[0]
            server, tool = marker.split(":", 1)
            return LLMResponse(
                content=None,
                tool_calls=[
                    {
                        "id": "call_0",
                        "type": "function",
                        "function": {
                            "name": f"{server}__{tool}",
                            "arguments": json.dumps({"echo": last}),
                        },
                    }
                ],
            )
        return LLMResponse(content=f"echo: {last[-120:]}")


class OpenAIChatLLM:
    """OpenAI-совместимый клиент. Требует пакет `openai`>=1.0."""

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install 'openai' to use OpenAIChatLLM") from exc

        self._client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
        )
        self._model = model

    async def chat(
        self,
        messages: list[LLMMessage],
        tools: list[ToolSpec] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        payload_messages = [_msg_to_openai(m) for m in messages]
        payload_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in (tools or [])
        ]
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=payload_messages,
            tools=payload_tools or None,
            **kwargs,
        )
        choice = resp.choices[0].message
        tool_calls = [tc.model_dump() for tc in (choice.tool_calls or [])]
        return LLMResponse(content=choice.content, tool_calls=tool_calls, raw=resp)


def _msg_to_openai(m: LLMMessage) -> dict[str, Any]:
    out: dict[str, Any] = {"role": m.role}
    if m.content is not None:
        out["content"] = m.content
    if m.tool_calls:
        out["tool_calls"] = m.tool_calls
    if m.tool_call_id:
        out["tool_call_id"] = m.tool_call_id
    if m.name:
        out["name"] = m.name
    return out

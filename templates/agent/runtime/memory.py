"""Простая двухуровневая память.

- Short-term: кольцевой буфер сообщений (в системном промпте/контексте LLM).
- Episodic: append-only JSONL с событиями (скиллы, tool-calls, A2A-таски).

Бэкенд сознательно файловый: в шаблоне важнее детерминированность и
лёгкая замена, чем производительность.
"""

from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque


@dataclass
class ShortTermMemory:
    max_messages: int = 40

    def __post_init__(self) -> None:
        self._messages: Deque[dict[str, Any]] = deque(maxlen=self.max_messages)

    def append(self, role: str, content: str, **meta: Any) -> None:
        self._messages.append({"role": role, "content": content, "meta": meta})

    def window(self) -> list[dict[str, Any]]:
        return list(self._messages)


class EpisodicMemory:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, event: str, **payload: Any) -> None:
        line = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "event": event,
            **payload,
        }
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")

    def tail(self, n: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        return [json.loads(x) for x in lines[-n:]]

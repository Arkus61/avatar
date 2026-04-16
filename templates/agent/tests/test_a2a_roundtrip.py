"""E2E-проверка A2A: создать задачу, получить финал, прочитать Agent Card.

Не требует внешнего LLM: использует EchoLLM и скилл с handler=python:noop.
"""

from __future__ import annotations

import asyncio
import sys
import threading
import time
import unittest
from pathlib import Path

import httpx
import uvicorn  # type: ignore

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TEMPLATE_ROOT.parent.parent))

from templates.agent.runtime.agent import load_agent  # noqa: E402


class A2ARoundTripTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.agent = load_agent(TEMPLATE_ROOT)
        await self.agent.start()
        app = self.agent.build_a2a_app()
        self.port = 17701
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()
        for _ in range(40):
            try:
                with httpx.Client(timeout=1.0) as c:
                    c.get(f"http://127.0.0.1:{self.port}/.well-known/agent-card.json")
                break
            except Exception:
                time.sleep(0.1)

    def _run_server(self) -> None:
        asyncio.run(self.server.serve())

    async def asyncTearDown(self) -> None:
        self.server.should_exit = True
        self._thread.join(timeout=5)
        await self.agent.stop()

    async def test_agent_card(self) -> None:
        async with httpx.AsyncClient(timeout=5) as c:
            resp = await c.get(f"http://127.0.0.1:{self.port}/.well-known/agent-card.json")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["version"], "0.1.0")
            self.assertIn("skills", data)

    async def test_task_roundtrip(self) -> None:
        async with httpx.AsyncClient(timeout=5) as c:
            resp = await c.post(
                f"http://127.0.0.1:{self.port}/a2a/v1/tasks",
                json={
                    "skill_id": "code.review",
                    "input": {"repo_path": "./"},
                    "stream": False,
                    "deadline_sec": 5,
                },
            )
            self.assertEqual(resp.status_code, 200)
            task_id = resp.json()["id"]

            for _ in range(30):
                got = await c.get(f"http://127.0.0.1:{self.port}/a2a/v1/tasks/{task_id}")
                data = got.json()
                if data["status"] in ("completed", "failed"):
                    break
                await asyncio.sleep(0.1)
            self.assertIn(data["status"], ("completed", "failed"))


if __name__ == "__main__":
    unittest.main()

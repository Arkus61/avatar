"""Локальный demo-запуск агента.

Сценарий:
1. Загружает манифест шаблона (templates/agent/agent.yaml).
2. Поднимает A2A-сервер на localhost:7701.
3. В отдельной таске эмулирует другого агента, который дергает скилл
   `a2a.delegate` → `code.review` (handler=noop, т.е. быстро завершится).

Запуск:
    python examples/run_local.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

import uvicorn  # type: ignore

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TEMPLATE_ROOT.parent))  # чтобы работал `templates.agent...`

from templates.agent.a2a.client import A2AClient  # noqa: E402
from templates.agent.a2a.schemas import TaskRequest  # noqa: E402
from templates.agent.runtime.agent import load_agent  # noqa: E402

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    os.environ.setdefault("AGENT_WORKDIR", str(TEMPLATE_ROOT / "_state"))
    Path(os.environ["AGENT_WORKDIR"]).mkdir(parents=True, exist_ok=True)

    agent = load_agent(TEMPLATE_ROOT)
    await agent.start()
    app = agent.build_a2a_app()

    server_cfg = agent.config.raw["a2a"]["server"]
    config = uvicorn.Config(app, host=server_cfg["host"], port=int(server_cfg["port"]), log_level="info")
    server = uvicorn.Server(config)
    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(1.0)

    try:
        async with A2AClient(base_url=server_cfg["public_url"]) as client:
            card = await client.fetch_card()
            print(f"Peer agent card: {card.name} ({card.id}), skills={[s.id for s in card.skills]}")

            req = TaskRequest(
                skill_id="code.review",
                input={"repo_path": "./", "diff_ref": "HEAD~1..HEAD"},
                stream=True,
                deadline_sec=10,
            )
            task = await client.run_until_final(req)
            print(f"Task result: {task['status']} → {task.get('output')}")
    finally:
        server.should_exit = True
        await server_task
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())

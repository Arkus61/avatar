"""Entry point — start the agent from agent_config.yaml."""

from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

import uvicorn

from core.factory import build_agent_from_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config_path = Path(__file__).parent / "config" / "agent_config.yaml"
    logger.info("Building agent from %s", config_path)

    agent, a2a_server = await build_agent_from_config(config_path)

    # Read host/port from config  (quick re-read — no need for full parse again)
    import yaml
    cfg = yaml.safe_load(config_path.read_text())["agent"]["a2a"]
    host = cfg.get("host", "0.0.0.0")
    port = cfg.get("port", 8100)

    logger.info("Starting A2A server on %s:%s", host, port)

    config = uvicorn.Config(
        app=a2a_server.app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    loop = asyncio.get_event_loop()

    def _shutdown(*_):
        logger.info("Shutting down…")
        server.should_exit = True

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown)

    await server.serve()
    await agent.mcp.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

"""
Desktop mode: GUI + optional tray + optional local API together.
"""
from __future__ import annotations

import logging
import threading

from seven import config
from seven.agent.loop import Seven
from seven.ui.chat_gui import SevenChatApp

logger = logging.getLogger("seven.desktop")


def run_desktop(enable_api: bool = False, enable_voice: bool = False):
    agent = Seven()
    agent.start_heartbeat()

    if enable_api or config.ENABLE_API:
        try:
            from seven.ui.api_server import start_api_server
            start_api_server(background=True, agent=agent)
            logger.info("API on http://%s:%s", config.API_HOST, config.API_PORT)
        except Exception:
            logger.exception("Failed to start API (GUI continues)")

    app = SevenChatApp(
        agent=agent,
        start_heartbeat=False,
        enable_voice=enable_voice or config.ENABLE_VOICE,
    )
    app.run()

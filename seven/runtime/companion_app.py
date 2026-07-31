"""Unified desktop companion: one mind, avatar, microphone, and voice."""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Callable

from seven import config
from seven.agent.loop import Seven
from seven.runtime.companion import CompanionRuntime

logger = logging.getLogger("seven.companion_app")


class CompanionApp:
    """Own every interactive surface around exactly one ``Seven`` instance."""

    def __init__(
        self,
        *,
        agent: Seven | None = None,
        voice: Any | None = None,
        avatar_factory: Callable[..., Any] | None = None,
        enable_api: bool = False,
        quiet: bool = False,
        listen_timeout: float | None = None,
        phrase_limit: float | None = None,
    ):
        self.agent = agent or Seven()
        self.quiet = bool(quiet)
        self.voice = voice if voice is not None else self._build_voice()
        self.runtime = CompanionRuntime(
            self.agent,
            voice=self.voice,
            quiet=self.quiet,
            listen_timeout=listen_timeout,
            phrase_limit=phrase_limit,
        )
        self.avatar_factory = avatar_factory
        self.enable_api = bool(enable_api)
        self.avatar = None
        self.api_server = None
        self._stop = threading.Event()
        self._listener_thread: threading.Thread | None = None
        self._lifecycle_lock = threading.Lock()
        self._started = False
        self._closed = False

    def _build_voice(self):
        if self.quiet:
            return None
        config.ENABLE_VOICE = True
        try:
            from seven.voice.io import VoiceIO

            voice = VoiceIO(lazy_whisper=True)
            prepare = getattr(voice, "prepare_for_talk", None)
            if prepare:
                prepare()
            return voice
        except Exception as exc:
            logger.warning("Unified companion voice unavailable: %s", exc)
            return None

    def _make_avatar(self):
        factory = self.avatar_factory
        if factory is None:
            from seven.ui.avatar import SevenAvatar

            factory = SevenAvatar
        return factory(
            self.agent,
            runtime=self.runtime,
            on_quit=self.close,
        )

    def start(self) -> None:
        """Attach services once; all of them share ``self.agent``."""
        with self._lifecycle_lock:
            if self._started:
                return
            self._started = True
        config.ENABLE_FREEWILL = True
        self.runtime.attach()
        self.agent.start_heartbeat()
        if self.enable_api:
            from seven.ui.api_server import start_api_server

            self.api_server = start_api_server(background=True, agent=self.agent)
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            name="seven-companion-listener",
            daemon=True,
        )
        self._listener_thread.start()
        logger.info(
            "Unified companion started agent_id=%s avatar=True mic=%s tts=%s api=%s",
            id(self.agent),
            self.runtime.use_mic,
            self.runtime.use_tts,
            bool(self.api_server),
        )

    def conversation_step(self) -> dict[str, Any]:
        """Run one foreground listen/handle cycle for tests and the worker."""
        heard = self.runtime.listen_once()
        if heard:
            result = self.runtime.handle_user_text(heard)
            if result.get("quit"):
                self.request_close()
            return {"heard": heard, "result": result}
        deliveries = self.runtime.drain_unsolicited(max_items=1)
        return {"heard": None, "deliveries": deliveries}

    def _listen_loop(self) -> None:
        logger.info("Unified companion listening loop active")
        if not self.quiet:
            self.runtime.deliver(
                f"Hey. I'm {config.BOT_NAME}. I'm here.",
                speak=True,
            )
        while not self._stop.is_set():
            try:
                self.conversation_step()
            except Exception:
                logger.exception("Unified companion cycle failed")
                self._stop.wait(1.0)
            if not self.runtime.use_mic:
                self._stop.wait(1.0)

    def request_close(self) -> None:
        self._stop.set()
        avatar = self.avatar
        if avatar is not None:
            request = getattr(avatar, "request_close", None)
            if request:
                request()

    def run(self) -> int:
        """Create the avatar on the main thread, then run the shared app."""
        try:
            self.avatar = self._make_avatar()
            self.start()
            self.avatar.run()
        finally:
            self.close()
        return 0

    def close(self) -> None:
        with self._lifecycle_lock:
            if self._closed:
                return
            self._closed = True
        self._stop.set()
        self.runtime.close()
        if self.api_server is not None:
            try:
                self.api_server.shutdown_cleanly()
            except Exception:
                logger.exception("Unified companion API shutdown failed")
        thread = self._listener_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=max(3.0, self.runtime.listen_timeout + 1.0))
        self.agent.shutdown()
        logger.info("Unified companion stopped")


def run_companion_app(
    *,
    enable_api: bool | None = None,
    quiet: bool | None = None,
) -> int:
    """Published Seven desktop entrypoint."""
    if quiet is None:
        quiet = os.getenv("SEVEN_QUIET", "0") == "1"
    if enable_api is None:
        enable_api = bool(config.ENABLE_API)
    return CompanionApp(enable_api=enable_api, quiet=bool(quiet)).run()

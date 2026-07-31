"""Default output channel for autonomous Seven utterances.

Interactive UIs may replace this sink. Long-running API/daemon/avatar processes
use it so a free-will speech decision is never silently discarded.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from seven import config

logger = logging.getLogger("seven.utterance")


class DefaultUtteranceSink:
    """Persist every utterance, then use TTS or a desktop notification."""

    def __init__(
        self,
        *,
        data_dir: Path | None = None,
        voice_enabled: bool | None = None,
        notifier: Callable[[str, str], dict[str, Any]] | None = None,
        voice_factory: Callable[..., Any] | None = None,
    ):
        self.data_dir = Path(data_dir or config.DATA_DIR)
        self.voice_enabled = (
            bool(config.ENABLE_VOICE) if voice_enabled is None else voice_enabled
        )
        self._notifier = notifier
        self._voice_factory = voice_factory
        self._voice = None
        self._lock = threading.Lock()

    @property
    def log_path(self) -> Path:
        return self.data_dir / "utterances.log"

    def _append_log(self, text: str) -> bool:
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            clean = " ".join(text.split())
            stamp = datetime.now(timezone.utc).isoformat()
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(f"{stamp}\t{clean}\n")
            return True
        except Exception:
            logger.exception("utterance log write failed path=%s", self.log_path)
            return False

    def _get_voice(self):
        if self._voice is not None:
            return self._voice
        factory = self._voice_factory
        if factory is None:
            from seven.voice.io import VoiceIO

            factory = VoiceIO
        self._voice = factory(lazy_whisper=True)
        return self._voice

    def _notify(self, text: str) -> dict[str, Any]:
        notifier = self._notifier
        if notifier is None:
            from seven.runtime.notifications import submit_notification

            notifier = submit_notification
        try:
            return notifier("Seven", text)
        except Exception as exc:
            logger.exception("utterance notification failed")
            return {"ok": False, "state": "error", "error": str(exc)}

    def __call__(self, text: str) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty_utterance"}

        with self._lock:
            logged = self._append_log(text)
            if self.voice_enabled:
                try:
                    voice = self._get_voice()
                    if voice.tts_ok and voice.speak(text):
                        return {"ok": True, "reason": "tts", "logged": logged}
                    logger.warning("autonomous TTS unavailable or rejected utterance")
                except Exception:
                    logger.exception("autonomous TTS delivery failed")
                notified = self._notify(text)
                return {
                    "ok": bool(notified.get("ok") or logged),
                    "reason": (
                        "tts_failed_notification"
                        if notified.get("ok")
                        else "tts_failed_log_only"
                    ),
                    "logged": logged,
                    "notification": notified.get("state"),
                }

            notified = self._notify(text)
            return {
                "ok": bool(notified.get("ok") or logged),
                "reason": (
                    "notification_and_log"
                    if notified.get("ok") and logged
                    else "notification"
                    if notified.get("ok")
                    else "log_only"
                    if logged
                    else "notification_and_log_failed"
                ),
                "logged": logged,
                "notification": notified.get("state"),
            }


def attach_default_utterance_sink(agent: Any) -> Any:
    """Attach one reusable default sink unless an interactive UI owns output."""
    existing = getattr(agent.freewill, "on_utter", None)
    if existing is not None:
        return existing
    sink = DefaultUtteranceSink()
    agent.freewill.on_utter = sink
    agent._default_utterance_sink = sink
    logger.info(
        "default utterance sink attached voice=%s log=%s",
        sink.voice_enabled,
        sink.log_path,
    )
    return sink

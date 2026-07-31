"""Single-process companion runtime for listening, replies, and freewill speech."""
from __future__ import annotations

import logging
import queue
import threading
from collections import deque
from typing import Any, Callable

from seven import config

logger = logging.getLogger("seven.companion")

_YES = frozenset({"yes", "yeah", "yep", "sure", "okay", "ok", "go ahead"})
_NO = frozenset({"no", "nope", "not now", "stay quiet", "quiet"})
_UNSOLICITED_MODES = frozenset({"ask", "free", "off"})


def normalize_unsolicited_mode(value: str | None) -> str:
    """Return a safe unsolicited-speech policy without changing old defaults."""
    mode = str(value or "free").strip().lower()
    if mode not in _UNSOLICITED_MODES:
        logger.warning("Invalid SEVEN_UNSOLICITED=%r; using ask", value)
        return "ask"
    return mode


class CompanionRuntime:
    """Own voice I/O and serialize listening, replies, and autonomous speech.

    Freewill callbacks enqueue speech instead of touching the microphone from the
    heartbeat thread. The foreground talk loop remains the sole owner of STT/TTS.
    """

    def __init__(
        self,
        agent: Any,
        *,
        voice: Any | None = None,
        quiet: bool = False,
        listen_timeout: float | None = None,
        phrase_limit: float | None = None,
        unsolicited: str | None = None,
        output: Callable[[str], None] = print,
    ):
        self.agent = agent
        self.voice = voice
        self.quiet = bool(quiet)
        self.listen_timeout = float(
            listen_timeout
            if listen_timeout is not None
            else getattr(config, "TALK_LISTEN_TIMEOUT", 2.5)
        )
        self.phrase_limit = float(
            phrase_limit
            if phrase_limit is not None
            else getattr(config, "TALK_PHRASE_LIMIT", 25)
        )
        self.unsolicited_mode = normalize_unsolicited_mode(
            unsolicited
            if unsolicited is not None
            else getattr(config, "UNSOLICITED_MODE", "free")
        )
        self.output = output
        self._speech_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._pending_unsolicited: deque[str] = deque()
        self._policy_lock = threading.Lock()
        self._permission: bool | None = None
        self._permission_prompt_queued = False
        self._listen_cycles = 0
        self._callback = self.queue_unsolicited
        self.use_tts = bool(
            not self.quiet
            and self.voice is not None
            and getattr(self.voice, "tts_ok", False)
        )
        self.use_mic = bool(not self.quiet and self._voice_has_stt())

    def _voice_has_stt(self) -> bool:
        if self.voice is None:
            return False
        if bool(getattr(self.voice, "stt_ok", False)):
            return True
        probe = getattr(self.voice, "_can_google_stt", None)
        try:
            return bool(probe and probe())
        except Exception:
            return False

    def attach(self) -> None:
        self.agent.freewill.on_utter = self._callback

    def close(self) -> None:
        if getattr(self.agent.freewill, "on_utter", None) == self._callback:
            self.agent.freewill.on_utter = None
        if self.voice is not None:
            try:
                self.voice.stop_speaking()
            except Exception:
                logger.exception("companion voice stop failed")

    def queue_unsolicited(self, text: str) -> dict[str, Any]:
        """Heartbeat-safe callback; actual output is serialized in the talk loop."""
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty_utterance"}
        with self._policy_lock:
            if self.unsolicited_mode == "off":
                return {"ok": False, "reason": "unsolicited_off"}
            if self.unsolicited_mode == "ask" and self._permission is False:
                return {"ok": False, "reason": "unsolicited_denied"}
            if self.unsolicited_mode == "ask" and self._permission is None:
                self._pending_unsolicited.append(text)
                if not self._permission_prompt_queued:
                    self._speech_queue.put(
                        ("permission", "I have something to say. Want to hear it?")
                    )
                    self._permission_prompt_queued = True
                return {"ok": False, "reason": "unsolicited_permission_pending"}
            self._speech_queue.put(("utterance", text))
        # Queued is not yet heard, so keep alive_cycle honest until drain succeeds.
        return {"ok": False, "reason": "queued_for_tts"}

    def drain_unsolicited(self, max_items: int = 8) -> list[dict[str, Any]]:
        delivered: list[dict[str, Any]] = []
        for _ in range(max(1, int(max_items))):
            try:
                kind, text = self._speech_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "permission":
                with self._policy_lock:
                    self._permission_prompt_queued = False
            result = self.deliver(text, speak=not self.quiet)
            result["kind"] = kind
            delivered.append(result)
            logger.info(
                "companion unsolicited delivered=%s reason=%s kind=%s",
                result.get("ok"),
                result.get("reason"),
                kind,
            )
        return delivered

    def listen_once(self) -> str | None:
        """One short rolling listen window; callers repeat it continuously."""
        if not self.use_mic or self.voice is None:
            return None
        if bool(getattr(self.voice, "is_speaking", False)):
            return None
        calibrate = 0.35 if self._listen_cycles == 0 else 0.05
        self._listen_cycles += 1
        heard = self.voice.listen_once(
            timeout=self.listen_timeout,
            phrase_time_limit=self.phrase_limit,
            calibrate=calibrate,
        )
        heard = (heard or "").strip()
        if heard:
            logger.info(
                "companion heard speech chars=%s cycle=%s",
                len(heard),
                self._listen_cycles,
            )
        return heard or None

    def deliver(self, text: str, *, speak: bool = True) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty_utterance"}
        self.output(f"\n{config.BOT_NAME}> {text}\n")
        if not speak or self.quiet:
            return {"ok": True, "reason": "text"}
        if not self.use_tts or self.voice is None:
            logger.warning("TTS unavailable; utterance printed as text only")
            return {"ok": False, "reason": "tts_unavailable_text_only"}
        try:
            spoken = bool(self.voice.speak(text))
        except Exception:
            logger.exception("companion TTS failed")
            return {"ok": False, "reason": "tts_failed_text_only"}
        if not spoken:
            logger.warning("TTS rejected utterance; text was printed")
            return {"ok": False, "reason": "tts_rejected_text_only"}
        if bool(getattr(self.voice, "last_barge_in", False)):
            logger.info("companion TTS stopped by barge-in")
            return {"ok": True, "reason": "tts_barged_in"}
        return {"ok": True, "reason": "tts"}

    def _permission_response(self, text: str) -> dict[str, Any] | None:
        answer = " ".join(text.lower().strip().split())
        with self._policy_lock:
            if (
                self.unsolicited_mode != "ask"
                or self._permission is not None
                or not self._pending_unsolicited
            ):
                return None
            if answer in _YES:
                self._permission = True
                pending = list(self._pending_unsolicited)
                self._pending_unsolicited.clear()
            elif answer in _NO:
                self._permission = False
                self._pending_unsolicited.clear()
                pending = None
            else:
                return None
        if pending is not None:
            for utterance in pending:
                self._speech_queue.put(("utterance", utterance))
            delivered = self.drain_unsolicited()
            return {
                "ok": True,
                "reason": "unsolicited_permission_granted",
                "deliveries": delivered,
            }
        if self._permission is False:
            result = self.deliver(
                "Okay. I’ll stay quiet unless you speak first.",
                speak=not self.quiet,
            )
            result["reason"] = "unsolicited_permission_denied"
            return result
        return None

    def handle_user_text(self, text: str) -> dict[str, Any]:
        """Route one transcribed/typed turn through the normal agent and TTS."""
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty_user_text"}
        permission = self._permission_response(text)
        if permission is not None:
            return permission
        try:
            reply = self.agent.handle(text)
        except Exception as exc:
            logger.exception("companion handle failed")
            reply = f"I hit a snag: {exc}"
        if reply == "__QUIT__":
            return {"ok": True, "reason": "quit", "quit": True}
        reply = (reply or "…").strip()
        delivery = self.deliver(reply, speak=not self.quiet)
        delivery["reply"] = reply
        logger.info(
            "companion reply delivered=%s reason=%s",
            delivery.get("ok"),
            delivery.get("reason"),
        )
        return delivery

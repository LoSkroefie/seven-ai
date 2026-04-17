"""
Ambient Listener Extension — Seven AI

Passive, always-on audio capture and transcription. Every spoken line
gets rolled into a `conversations` episode via core/conversation_memory.py.
When a silence gap > AMBIENT_GAP_SECONDS passes, the current conversation
is closed and finalized (summary + action items + sentiment) via Ollama.

Also captures user ↔ Seven direct interactions via on_message so every
exchange — ambient room audio AND explicit conversation — lands in the
same episodic memory store.

Offline-first. Uses the local Whisper model (tiny by default) via the
same `whisper` package Seven already ships with. No cloud, no API key.

Command triggers (matched in on_message, case-insensitive):
  - "what did i talk about today"     → today's conversation summaries
  - "what did i talk about yesterday" → yesterday's summaries
  - "recent conversations"            → last 5 conversations
  - "summarize my day"                → one-paragraph rollup
  - "action items" / "my action items"/ "action items today"
                                      → outstanding action items
  - "ambient status" / "listening status"
                                      → extension health
  - "pause listening" / "resume listening"
                                      → toggle ambient capture

Config keys (all optional — extension is OFF by default):
  ENABLE_AMBIENT_LISTENER             bool   — master switch
  AMBIENT_WHISPER_MODEL               str    — 'tiny' | 'base' | ...   (default 'tiny')
  AMBIENT_GAP_SECONDS                 int    — silence gap to close convo (default 45)
  AMBIENT_MIN_WORDS                   int    — drop transcripts shorter than this (default 3)
  AMBIENT_LISTEN_TIMEOUT              int    — per-chunk listen timeout (default 5)
  AMBIENT_PHRASE_LIMIT                int    — max seconds per utterance (default 15)
  AMBIENT_PRUNE_DAYS                  int    — delete convos older than this (default 30)
  AMBIENT_RESPECT_VOICE_MANAGER       bool   — yield when main voice is busy (default True)
"""

import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.plugin_loader import SevenExtension

logger = logging.getLogger("AmbientListener")


# ----------------------------------------------------------------------------
# Optional deps — import defensively so a missing package never kills Seven
# ----------------------------------------------------------------------------

try:
    import config  # seven's main config
except Exception:  # pragma: no cover
    config = None  # type: ignore

try:
    import speech_recognition as sr
except Exception:
    sr = None  # type: ignore

try:
    import numpy as np
except Exception:
    np = None  # type: ignore

try:
    import whisper  # openai-whisper
except Exception:
    whisper = None  # type: ignore

try:
    from core.conversation_memory import ConversationMemory
except Exception:  # pragma: no cover
    ConversationMemory = None  # type: ignore


# ----------------------------------------------------------------------------
# Extension
# ----------------------------------------------------------------------------

class AmbientListenerExtension(SevenExtension):
    """
    Passive ambient-audio capture → conversation episodes.
    Also hooks on_message to log direct user↔Seven interactions.
    """

    name = "Ambient Listener"
    version = "1.0"
    description = (
        "Passively transcribes ambient audio into episodic conversation "
        "memory, summarized via Ollama on silence gaps."
    )
    author = "Seven AI"

    # Runs a maintenance pass every 15 minutes (close stale, finalize, prune).
    schedule_interval_minutes = 15
    needs_ollama = True

    # -------------------- lifecycle --------------------

    def init(self, bot=None):
        self.bot = bot

        # Config with safe defaults
        self.enabled: bool = bool(getattr(config, "ENABLE_AMBIENT_LISTENER", False))
        self.whisper_model_name: str = str(
            getattr(config, "AMBIENT_WHISPER_MODEL", "tiny")
        )
        self.gap_seconds: int = int(getattr(config, "AMBIENT_GAP_SECONDS", 45))
        self.min_words: int = int(getattr(config, "AMBIENT_MIN_WORDS", 3))
        self.listen_timeout: int = int(getattr(config, "AMBIENT_LISTEN_TIMEOUT", 5))
        self.phrase_limit: int = int(getattr(config, "AMBIENT_PHRASE_LIMIT", 15))
        self.prune_days: int = int(getattr(config, "AMBIENT_PRUNE_DAYS", 30))
        self.respect_voice_manager: bool = bool(
            getattr(config, "AMBIENT_RESPECT_VOICE_MANAGER", True)
        )
        self.direct_gap_seconds: int = int(
            getattr(config, "AMBIENT_DIRECT_GAP_SECONDS", 180)
        )

        # Mutable runtime state
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._paused = False

        self._whisper_model = None  # lazy
        self._whisper_tried = False
        self._recognizer = None

        # Current conversations
        self._ambient_conv_id: Optional[int] = None
        self._ambient_last_speech_ts: float = 0.0
        self._direct_conv_id: Optional[int] = None
        self._direct_last_ts: float = 0.0

        # Stats
        self._stats = {
            "started_at": None,
            "ambient_utterances": 0,
            "direct_utterances": 0,
            "conversations_finalized": 0,
            "errors": 0,
            "last_error": None,
            "last_ambient_text": None,
            "mic_contention_events": 0,
        }

        # Memory handle
        self.memory: Optional[ConversationMemory] = None
        if ConversationMemory is not None:
            try:
                self.memory = ConversationMemory()
            except Exception as e:
                logger.error(f"[AMBIENT] ConversationMemory init failed: {e}")
                self.memory = None
        else:
            logger.warning(
                "[AMBIENT] core.conversation_memory unavailable — episode storage disabled"
            )

        # Pre-flight
        if not self.enabled:
            logger.info("[AMBIENT] disabled via config (ENABLE_AMBIENT_LISTENER=False)")
        if sr is None:
            logger.warning("[AMBIENT] speech_recognition not installed — passive capture disabled")
        if whisper is None:
            logger.warning("[AMBIENT] openai-whisper not installed — passive capture disabled")

    def start(self):
        if not self._can_listen_passively():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop,
            name="AmbientListener",
            daemon=True,
        )
        self._thread.start()
        self._stats["started_at"] = datetime.now().isoformat()
        logger.info(
            f"[AMBIENT] listening started "
            f"(whisper={self.whisper_model_name}, gap={self.gap_seconds}s)"
        )

    def stop(self):
        self._stop_event.set()
        # Try to finalize whatever's open so we don't lose data on shutdown
        try:
            self._finalize_if_open(self._ambient_conv_id)
            self._ambient_conv_id = None
            self._finalize_if_open(self._direct_conv_id)
            self._direct_conv_id = None
        except Exception as e:
            logger.debug(f"[AMBIENT] stop finalize failed: {e}")
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("[AMBIENT] listening stopped")

    # -------------------- capability checks --------------------

    def _can_listen_passively(self) -> bool:
        if not self.enabled:
            return False
        if sr is None or whisper is None or np is None:
            return False
        if self.memory is None:
            return False
        return True

    def _voice_manager_busy(self) -> bool:
        """Best-effort detection of whether the main voice manager is active."""
        if not self.respect_voice_manager or not self.bot:
            return False
        vm = (
            getattr(self.bot, "voice_manager", None)
            or getattr(self.bot, "voice", None)
            or getattr(self.bot, "whisper_voice", None)
        )
        if not vm:
            return False
        for attr in ("is_listening", "listening", "is_speaking", "speaking", "busy"):
            val = getattr(vm, attr, None)
            try:
                if callable(val):
                    if bool(val()):
                        return True
                elif bool(val):
                    return True
            except Exception:
                continue
        # Also respect a high-level "bot is speaking" flag if present on the bot
        if getattr(self.bot, "is_speaking", False):
            return True
        return False

    # -------------------- whisper --------------------

    def _get_whisper(self):
        if self._whisper_model is not None:
            return self._whisper_model
        if self._whisper_tried:
            return None
        self._whisper_tried = True
        try:
            logger.info(f"[AMBIENT] loading Whisper model '{self.whisper_model_name}'...")
            self._whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info("[AMBIENT] Whisper loaded")
        except Exception as e:
            logger.error(f"[AMBIENT] Whisper load failed: {e}")
            self._whisper_model = None
        return self._whisper_model

    # -------------------- main loop --------------------

    def _listen_loop(self):
        if self._recognizer is None:
            self._recognizer = sr.Recognizer()

        mic_fail_sleep = 1.0
        while not self._stop_event.is_set():
            if self._paused or not self.enabled:
                time.sleep(1.0)
                continue

            # Close stale ambient conversation?
            if (
                self._ambient_conv_id
                and self._ambient_last_speech_ts
                and (time.time() - self._ambient_last_speech_ts) > self.gap_seconds
            ):
                self._finalize_if_open(self._ambient_conv_id)
                self._ambient_conv_id = None

            # Yield to main voice manager
            if self._voice_manager_busy():
                time.sleep(0.5)
                continue

            try:
                text, confidence = self._capture_and_transcribe()
            except Exception as e:
                self._stats["errors"] += 1
                self._stats["last_error"] = str(e)[:200]
                logger.debug(f"[AMBIENT] capture error: {e}")
                time.sleep(mic_fail_sleep)
                mic_fail_sleep = min(10.0, mic_fail_sleep * 1.5)
                continue

            mic_fail_sleep = 1.0

            if not text:
                continue
            if len(text.split()) < self.min_words:
                continue

            self._record_ambient(text, confidence)

        logger.debug("[AMBIENT] loop exited cleanly")

    def _capture_and_transcribe(self):
        """Listen for one chunk and transcribe with Whisper."""
        model = self._get_whisper()
        if model is None:
            # Can't transcribe; sleep and bail
            time.sleep(2.0)
            return None, None

        try:
            mic = sr.Microphone()
        except Exception as e:
            # PyAudio / no mic
            self._stats["mic_contention_events"] += 1
            raise RuntimeError(f"microphone unavailable: {e}")

        try:
            with mic as source:
                # short calibration — we're running continuously so keep this cheap
                try:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                except Exception:
                    pass
                try:
                    audio = self._recognizer.listen(
                        source,
                        timeout=self.listen_timeout,
                        phrase_time_limit=self.phrase_limit,
                    )
                except sr.WaitTimeoutError:
                    return None, None
        except OSError as e:
            self._stats["mic_contention_events"] += 1
            raise RuntimeError(f"mic busy: {e}")

        # Whisper wants float32 mono
        try:
            raw = audio.get_wav_data(convert_rate=16000, convert_width=2)
            arr16 = np.frombuffer(raw, dtype=np.int16)
            if arr16.size == 0:
                return None, None
            arr_f = arr16.astype(np.float32) / 32768.0
            result = model.transcribe(arr_f, language="en", fp16=False)
            text = str(result.get("text", "")).strip()
            # whisper's `no_speech_prob` is a reasonable proxy for confidence
            seg = (result.get("segments") or [{}])[0]
            no_speech = float(seg.get("no_speech_prob", 0.5))
            confidence = max(0.0, 1.0 - no_speech)
            return text, confidence
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]
            logger.debug(f"[AMBIENT] transcribe failed: {e}")
            return None, None

    # -------------------- recording into memory --------------------

    def _record_ambient(self, text: str, confidence: Optional[float]):
        if self.memory is None:
            return
        try:
            if self._ambient_conv_id is None:
                self._ambient_conv_id = self.memory.start_conversation(
                    source="ambient",
                    participants=["unknown"],
                )
            self.memory.add_utterance(
                conversation_id=self._ambient_conv_id,
                speaker="unknown",
                text=text,
                source="ambient",
                confidence=confidence,
            )
            self._ambient_last_speech_ts = time.time()
            self._stats["ambient_utterances"] += 1
            self._stats["last_ambient_text"] = text[:120]
            logger.debug(f"[AMBIENT] captured ({confidence or 0:.2f}): {text[:80]}")
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]

    def _record_direct(self, user_message: str, bot_response: str):
        """Capture user ↔ Seven exchange into a 'direct' conversation episode."""
        if self.memory is None:
            return
        now = time.time()
        try:
            # Start / reuse conversation based on recency
            if (
                self._direct_conv_id is None
                or (now - self._direct_last_ts) > self.direct_gap_seconds
            ):
                # finalize the previous one if it's gone stale
                if self._direct_conv_id is not None:
                    self._finalize_if_open(self._direct_conv_id)
                user_name = getattr(config, "USER_NAME", "user") if config else "user"
                bot_name = getattr(config, "DEFAULT_BOT_NAME", "Seven") if config else "Seven"
                self._direct_conv_id = self.memory.start_conversation(
                    source="direct",
                    participants=[user_name, bot_name],
                )

            if user_message:
                self.memory.add_utterance(
                    conversation_id=self._direct_conv_id,
                    speaker="user",
                    text=user_message,
                    source="direct",
                    emotion=self._current_emotion(),
                )
                self._stats["direct_utterances"] += 1
            if bot_response:
                self.memory.add_utterance(
                    conversation_id=self._direct_conv_id,
                    speaker="seven",
                    text=bot_response,
                    source="direct",
                    emotion=self._current_emotion(),
                )
                self._stats["direct_utterances"] += 1
            self._direct_last_ts = now
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]
            logger.debug(f"[AMBIENT] _record_direct failed: {e}")

    def _current_emotion(self) -> Optional[str]:
        try:
            e = getattr(self.bot, "current_emotion", None) if self.bot else None
            if e is None:
                return None
            return str(getattr(e, "value", e))
        except Exception:
            return None

    def _finalize_if_open(self, conv_id: Optional[int]):
        if not conv_id or self.memory is None:
            return
        try:
            ollama = getattr(self.bot, "ollama", None) if self.bot else None
            self.memory.finalize_conversation(conv_id, ollama=ollama)
            self._stats["conversations_finalized"] += 1
        except Exception as e:
            logger.debug(f"[AMBIENT] finalize_conversation failed: {e}")

    # -------------------- scheduled maintenance --------------------

    def run(self, context: dict = None) -> dict:
        """
        Scheduled pass (every schedule_interval_minutes). Closes stale open
        conversations, finalizes any that haven't been summarized yet, and
        prunes very old data.
        """
        if self.memory is None:
            return {"message": "conversation memory unavailable", "status": "skipped"}

        finalized_here = 0
        try:
            # Close/finalize direct conversation if it's stale
            if (
                self._direct_conv_id is not None
                and self._direct_last_ts
                and (time.time() - self._direct_last_ts) > self.direct_gap_seconds
            ):
                self._finalize_if_open(self._direct_conv_id)
                self._direct_conv_id = None
                finalized_here += 1

            # Close/finalize ambient conversation if stale
            if (
                self._ambient_conv_id is not None
                and self._ambient_last_speech_ts
                and (time.time() - self._ambient_last_speech_ts) > self.gap_seconds
            ):
                self._finalize_if_open(self._ambient_conv_id)
                self._ambient_conv_id = None
                finalized_here += 1

            # Close any other dangling conversations
            stale_ids = self.memory.close_stale(minutes=max(5, self.gap_seconds // 60 + 5))
            # Finalize any unfinalized, closed, summary-less rows (cheap if Ollama is off)
            for conv in self.memory.get_recent(limit=20, finalized_only=False):
                if not conv.get("finalized") and conv.get("ended_at"):
                    self._finalize_if_open(conv["id"])
                    finalized_here += 1

            # Pruning (safe default: 30 days)
            if self.prune_days and self.prune_days > 0:
                self.memory.prune_older_than(self.prune_days)

            stats = self.memory.get_stats()
            return {
                "message": (
                    f"maintenance ok — finalized {finalized_here}, "
                    f"closed_stale {len(stale_ids)}, "
                    f"total_convs {stats['total_conversations']}"
                ),
                "status": "ok",
                "finalized_this_pass": finalized_here,
                "closed_stale": len(stale_ids),
                "stats": stats,
                "listener_stats": dict(self._stats),
            }
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]
            return {"message": f"maintenance error: {e}", "status": "error"}

    # -------------------- on_message hook --------------------

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        # 1) capture the direct exchange
        self._record_direct(user_message, bot_response)

        # 2) handle command triggers
        if not user_message:
            return None
        cmd = user_message.strip().lower()

        try:
            if any(kw in cmd for kw in ("pause listening", "stop ambient", "stop listening ambient")):
                if self._paused:
                    return "[Seven] Ambient listening is already paused."
                self._paused = True
                return "[Seven] Ambient listening paused."
            if any(kw in cmd for kw in ("resume listening", "start ambient", "resume ambient")):
                if not self._paused:
                    return "[Seven] Ambient listening is already active."
                self._paused = False
                return "[Seven] Ambient listening resumed."

            if "ambient status" in cmd or "listening status" in cmd:
                return self._format_status()

            if "what did i talk about today" in cmd or "summarize my day" in cmd:
                return self._format_date_summary(self.memory.get_today(), "today")
            if "what did i talk about yesterday" in cmd:
                return self._format_date_summary(self.memory.get_yesterday(), "yesterday")
            if "recent conversations" in cmd or "show my conversations" in cmd:
                return self._format_recent(self.memory.get_recent(limit=5))
            if "action items" in cmd and "today" in cmd:
                return self._format_actions(self.memory.get_action_items(days_back=1))
            if "action items" in cmd or "my todos" in cmd or "my todo list" in cmd:
                return self._format_actions(self.memory.get_action_items(days_back=7))
        except Exception as e:
            logger.debug(f"[AMBIENT] on_message command failed: {e}")

        return None

    # -------------------- formatters --------------------

    def _format_date_summary(self, convs: List[Dict[str, Any]], label: str) -> str:
        if not convs:
            return f"[Seven] No conversations recorded for {label}."
        lines = [f"[Seven] Conversations from {label} ({len(convs)}):"]
        for c in convs:
            s = (c.get("summary") or "").strip()
            if not s:
                s = "(no summary — conversation may still be open)"
            when = (c.get("started_at") or "")[11:16]  # HH:MM
            src = c.get("source", "?")
            lines.append(f"  • [{when}] ({src}) {s}")
        return "\n".join(lines)

    def _format_recent(self, convs: List[Dict[str, Any]]) -> str:
        if not convs:
            return "[Seven] No conversations recorded yet."
        lines = ["[Seven] Recent conversations:"]
        for c in convs:
            s = (c.get("summary") or "(not summarized yet)").strip()
            when = (c.get("started_at") or "")[:16].replace("T", " ")
            lines.append(f"  • {when} — {s}")
        return "\n".join(lines)

    def _format_actions(self, items: List[Dict[str, Any]]) -> str:
        if not items:
            return "[Seven] No action items found."
        lines = [f"[Seven] Action items ({len(items)}):"]
        for it in items:
            when = (it.get("started_at") or "")[:10]
            lines.append(f"  • [{when}] {it.get('item')}")
        return "\n".join(lines)

    def _format_status(self) -> str:
        stats = self.memory.get_stats() if self.memory else {}
        paused = "paused" if self._paused else "active"
        enabled = "enabled" if self.enabled else "disabled"
        return (
            f"[Seven] Ambient listener: {enabled}, {paused}. "
            f"Ambient utterances: {self._stats.get('ambient_utterances', 0)}, "
            f"direct: {self._stats.get('direct_utterances', 0)}, "
            f"finalized: {self._stats.get('conversations_finalized', 0)}, "
            f"errors: {self._stats.get('errors', 0)}. "
            f"Total conversations: {stats.get('total_conversations', 0)}, "
            f"today: {stats.get('today', 0)}."
        )

    # -------------------- plugin status --------------------

    def get_status(self) -> dict:
        stats = {}
        if self.memory is not None:
            try:
                stats = self.memory.get_stats()
            except Exception:
                stats = {}
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "paused": self._paused,
            "whisper_model": self.whisper_model_name,
            "whisper_loaded": self._whisper_model is not None,
            "speech_recognition_available": sr is not None,
            "numpy_available": np is not None,
            "memory_available": self.memory is not None,
            "running": self._thread.is_alive() if self._thread else False,
            "listener": dict(self._stats),
            "conversation_stats": stats,
        }

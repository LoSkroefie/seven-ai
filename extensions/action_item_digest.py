"""
Action Item Digest Extension — Seven AI

Mines the episodic conversation memory (core/conversation_memory.py) for
action items that Ollama extracted during conversation finalization, and
proactively surfaces them so Seven actually uses what she remembered.

How it works
------------
1. On a schedule (default: hourly), scans recent conversations for
   action_items that were extracted during finalization.
2. Deduplicates against items we've already surfaced
   (stored in ~/.chatbot/action_items_seen.json).
3. Delivers newly-seen items via:
     - Toast notification (one item at a time, batched to at most
       ACTION_ITEM_MAX_PER_RUN per scheduled pass)
     - Optional voice announcement (if bot._speak is available)
     - Optional echo into the conversation (on_message replies)

Voice / text commands (case-insensitive, matched in on_message):
  - "what's on my plate"             → open action items, grouped by day
  - "whats on my plate" / "my plate" → same
  - "action items today"             → only today's items
  - "my action items"                → all open items (last 7 days)
  - "clear action items"             → mark all seen as acknowledged
  - "digest status"                  → extension health

Config keys (all optional — extension is OFF by default):
  ENABLE_ACTION_ITEM_DIGEST          bool — master switch (default False)
  ACTION_ITEM_INTERVAL_MINUTES       int  — schedule cadence (default 60)
  ACTION_ITEM_LOOKBACK_DAYS          int  — how far back to scan (default 3)
  ACTION_ITEM_MAX_PER_RUN            int  — max toasts per schedule tick (default 3)
  ACTION_ITEM_USE_TOAST              bool — send toast notifications (default True)
  ACTION_ITEM_USE_VOICE              bool — speak new items aloud (default False)
  ACTION_ITEM_MIN_LEN                int  — drop trivial items shorter than N chars (default 4)
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from utils.plugin_loader import SevenExtension

logger = logging.getLogger("ActionItemDigest")

try:
    import config
except Exception:
    config = None  # type: ignore

try:
    from core.conversation_memory import ConversationMemory
except Exception:
    ConversationMemory = None  # type: ignore


class ActionItemDigestExtension(SevenExtension):
    """Mine conversation memory for TODOs and proactively surface them."""

    name = "Action Item Digest"
    version = "1.0"
    description = (
        "Extracts and surfaces action items that Ollama pulled out of "
        "recorded conversations, via toast notifications and on-demand "
        "retrieval."
    )
    author = "Seven AI"

    schedule_interval_minutes = 60  # overridden in init() from config
    needs_ollama = False  # Ollama already ran during finalization

    # -------------------- lifecycle --------------------

    def init(self, bot=None):
        self.bot = bot

        self.enabled: bool = bool(getattr(config, "ENABLE_ACTION_ITEM_DIGEST", False))
        self.interval_minutes: int = int(
            getattr(config, "ACTION_ITEM_INTERVAL_MINUTES", 60)
        )
        self.lookback_days: int = int(
            getattr(config, "ACTION_ITEM_LOOKBACK_DAYS", 3)
        )
        self.max_per_run: int = int(
            getattr(config, "ACTION_ITEM_MAX_PER_RUN", 3)
        )
        self.use_toast: bool = bool(
            getattr(config, "ACTION_ITEM_USE_TOAST", True)
        )
        self.use_voice: bool = bool(
            getattr(config, "ACTION_ITEM_USE_VOICE", False)
        )
        self.min_len: int = int(getattr(config, "ACTION_ITEM_MIN_LEN", 4))

        # Keep scheduler in sync with config
        self.schedule_interval_minutes = max(5, self.interval_minutes)

        # Where we persist "seen" hashes so we don't re-toast the same TODO
        data_dir = getattr(config, "DATA_DIR", None)
        if data_dir is None:
            data_dir = Path.home() / ".chatbot"
        self._state_path: Path = Path(data_dir) / "action_items_seen.json"
        self._seen: Set[str] = self._load_seen()

        # Stats
        self._stats = {
            "runs": 0,
            "items_surfaced": 0,
            "items_skipped_seen": 0,
            "items_skipped_trivial": 0,
            "last_surfaced": None,
            "last_run_at": None,
            "errors": 0,
            "last_error": None,
        }

        # Memory handle
        self.memory: Optional[ConversationMemory] = None
        if ConversationMemory is not None:
            try:
                self.memory = ConversationMemory()
            except Exception as e:
                logger.error(f"[ACTION_DIGEST] ConversationMemory init failed: {e}")
                self.memory = None

        if not self.enabled:
            logger.info(
                "[ACTION_DIGEST] disabled via config "
                "(ENABLE_ACTION_ITEM_DIGEST=False)"
            )

    # -------------------- seen-tracking --------------------

    @staticmethod
    def _fingerprint(item_text: str) -> str:
        """Stable hash for deduplication — whitespace/casing normalized."""
        normalized = re.sub(r"\s+", " ", (item_text or "").strip().lower())
        return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:16]

    def _load_seen(self) -> Set[str]:
        try:
            if self._state_path.exists():
                with open(self._state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Stored as {fp: iso_timestamp}
                return set(data.keys())
        except Exception as e:
            logger.debug(f"[ACTION_DIGEST] failed to load seen state: {e}")
        return set()

    def _save_seen(self, seen_map: Dict[str, str]):
        try:
            self._state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._state_path, "w", encoding="utf-8") as f:
                json.dump(seen_map, f, indent=2)
        except Exception as e:
            logger.debug(f"[ACTION_DIGEST] failed to save seen state: {e}")

    def _mark_seen(self, fingerprints: List[str]):
        """Merge new fingerprints into persisted state."""
        existing: Dict[str, str] = {}
        try:
            if self._state_path.exists():
                with open(self._state_path, "r", encoding="utf-8") as f:
                    existing = json.load(f) or {}
        except Exception:
            existing = {}
        now = datetime.now().isoformat()
        for fp in fingerprints:
            existing[fp] = now
            self._seen.add(fp)
        # Prune very old entries (> 180 days) to keep state file tidy
        cutoff = (datetime.now() - timedelta(days=180)).isoformat()
        existing = {k: v for k, v in existing.items() if v >= cutoff}
        self._seen = set(existing.keys())
        self._save_seen(existing)

    # -------------------- core scan --------------------

    def _fetch_open_items(self, days_back: int) -> List[Dict[str, Any]]:
        """Pull action items from ConversationMemory for the lookback window."""
        if self.memory is None:
            return []
        try:
            return self.memory.get_action_items(days_back=days_back)
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]
            return []

    def _filter_new(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Drop items we've already surfaced or that are too trivial."""
        new_items = []
        for it in items:
            text = str(it.get("item", "")).strip()
            if len(text) < self.min_len:
                self._stats["items_skipped_trivial"] += 1
                continue
            fp = self._fingerprint(text)
            if fp in self._seen:
                self._stats["items_skipped_seen"] += 1
                continue
            it["_fingerprint"] = fp
            new_items.append(it)
        return new_items

    # -------------------- delivery --------------------

    def _toast(self, title: str, body: str):
        if not self.use_toast or not self.bot:
            return
        toast = getattr(self.bot, "toast", None)
        if toast and getattr(toast, "available", False):
            try:
                toast.notify(title, body, duration=10)
            except Exception as e:
                logger.debug(f"[ACTION_DIGEST] toast failed: {e}")

    def _speak(self, text: str):
        if not self.use_voice or not self.bot:
            return
        speak = getattr(self.bot, "_speak", None)
        if callable(speak):
            try:
                speak(text)
            except Exception as e:
                logger.debug(f"[ACTION_DIGEST] voice failed: {e}")

    def _surface_items(self, items: List[Dict[str, Any]]) -> List[str]:
        """Deliver up to max_per_run items. Returns fingerprints actually surfaced."""
        surfaced: List[str] = []
        for it in items[: self.max_per_run]:
            text = str(it.get("item", "")).strip()
            if not text:
                continue
            when = str(it.get("started_at", ""))[:10]
            title = "Seven AI — Action Item"
            body = f"[{when}] {text}" if when else text
            self._toast(title, body)
            self._speak(f"Heads up: {text}")
            surfaced.append(it["_fingerprint"])
            self._stats["items_surfaced"] += 1
            self._stats["last_surfaced"] = text[:120]
            logger.info(f"[ACTION_DIGEST] surfaced: {text[:80]}")
        return surfaced

    # -------------------- scheduled run --------------------

    def run(self, context: dict = None) -> dict:
        """Mine recent conversations for new action items and surface them."""
        self._stats["runs"] += 1
        self._stats["last_run_at"] = datetime.now().isoformat()

        if not self.enabled:
            return {"message": "disabled", "status": "skipped"}
        if self.memory is None:
            return {
                "message": "conversation memory unavailable",
                "status": "skipped",
            }

        try:
            all_items = self._fetch_open_items(self.lookback_days)
            new_items = self._filter_new(all_items)

            if not new_items:
                return {
                    "message": (
                        f"no new action items "
                        f"(scanned {len(all_items)} in last {self.lookback_days}d)"
                    ),
                    "status": "ok",
                    "new_count": 0,
                    "scanned": len(all_items),
                }

            surfaced_fps = self._surface_items(new_items)
            if surfaced_fps:
                self._mark_seen(surfaced_fps)

            remaining = max(0, len(new_items) - len(surfaced_fps))
            msg = f"surfaced {len(surfaced_fps)} new action item(s)"
            if remaining:
                msg += f", {remaining} more queued for next run"

            return {
                "message": msg,
                "status": "ok",
                "new_count": len(new_items),
                "surfaced": len(surfaced_fps),
                "remaining": remaining,
                "scanned": len(all_items),
            }
        except Exception as e:
            self._stats["errors"] += 1
            self._stats["last_error"] = str(e)[:200]
            logger.error(f"[ACTION_DIGEST] run failed: {e}")
            return {"message": f"error: {e}", "status": "error"}

    # -------------------- on_message commands --------------------

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        if not user_message:
            return None
        cmd = user_message.strip().lower()

        try:
            if "digest status" in cmd or "action item status" in cmd:
                return self._format_status()

            if "clear action items" in cmd or "forget action items" in cmd:
                return self._cmd_clear()

            # "action items today"
            if "action items" in cmd and "today" in cmd:
                return self._format_items(
                    self._fetch_open_items(days_back=1),
                    label="today",
                )
            # "what's on my plate" / "my plate" / "action items" / "my todos"
            if any(
                kw in cmd
                for kw in (
                    "what's on my plate",
                    "whats on my plate",
                    "on my plate",
                    "my plate",
                    "my action items",
                    "what do i need to do",
                )
            ):
                return self._format_items(
                    self._fetch_open_items(days_back=self.lookback_days),
                    label=f"last {self.lookback_days}d",
                )
        except Exception as e:
            logger.debug(f"[ACTION_DIGEST] on_message failed: {e}")

        return None

    def _cmd_clear(self) -> str:
        items = self._fetch_open_items(self.lookback_days)
        fps = [self._fingerprint(str(it.get("item", ""))) for it in items]
        self._mark_seen([fp for fp in fps if fp])
        return f"[Seven] Acknowledged {len(fps)} action item(s). I won't surface them again."

    # -------------------- formatters --------------------

    def _format_items(self, items: List[Dict[str, Any]], label: str) -> str:
        if not items:
            return f"[Seven] No action items found ({label})."
        # Group by date for readability
        by_day: Dict[str, List[Dict[str, Any]]] = {}
        for it in items:
            day = str(it.get("started_at", ""))[:10] or "(no date)"
            by_day.setdefault(day, []).append(it)

        lines = [f"[Seven] Action items ({len(items)} — {label}):"]
        for day in sorted(by_day.keys(), reverse=True):
            lines.append(f"  {day}:")
            for it in by_day[day]:
                text = str(it.get("item", "")).strip()
                fp = self._fingerprint(text)
                mark = "✓" if fp in self._seen else "•"
                lines.append(f"    {mark} {text}")
        return "\n".join(lines)

    def _format_status(self) -> str:
        enabled = "enabled" if self.enabled else "disabled"
        return (
            f"[Seven] Action item digest: {enabled}. "
            f"Runs: {self._stats['runs']}, "
            f"surfaced: {self._stats['items_surfaced']}, "
            f"seen (persisted): {len(self._seen)}, "
            f"skipped (dupe): {self._stats['items_skipped_seen']}, "
            f"skipped (trivial): {self._stats['items_skipped_trivial']}, "
            f"errors: {self._stats['errors']}."
        )

    # -------------------- plugin status --------------------

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "interval_minutes": self.interval_minutes,
            "lookback_days": self.lookback_days,
            "max_per_run": self.max_per_run,
            "use_toast": self.use_toast,
            "use_voice": self.use_voice,
            "memory_available": self.memory is not None,
            "seen_items": len(self._seen),
            "stats": dict(self._stats),
            "running": True,
        }

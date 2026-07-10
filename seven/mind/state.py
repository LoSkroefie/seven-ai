"""
Persistent living state: last world/self snapshots + tick history.
JSON file under SEVEN_DATA_DIR so daemon and CLI share state.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from seven import config
from seven.mind.self_model import sense_self, self_summary
from seven.mind.world import sense_world, world_summary

logger = logging.getLogger("seven.mind")


class LivingState:
    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path or (config.DATA_DIR / "living_state.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.world: Dict[str, Any] = {}
        self.self_state: Dict[str, Any] = {}
        self.tick_count: int = 0
        self.last_tick_ts: float = 0.0
        self.last_action: Optional[str] = None
        self.last_reflection: Optional[str] = None
        self.boot_ts: float = time.time()
        self.history: List[Dict[str, Any]] = []  # last N tick summaries
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.world = data.get("world") or {}
            self.self_state = data.get("self") or {}
            self.tick_count = int(data.get("tick_count") or 0)
            self.last_tick_ts = float(data.get("last_tick_ts") or 0)
            self.last_action = data.get("last_action")
            self.last_reflection = data.get("last_reflection")
            self.history = list(data.get("history") or [])[-50:]
        except Exception as e:
            logger.warning("living state load failed: %s", e)

    def save(self):
        with self._lock:
            payload = {
                "world": self.world,
                "self": self.self_state,
                "tick_count": self.tick_count,
                "last_tick_ts": self.last_tick_ts,
                "last_action": self.last_action,
                "last_reflection": self.last_reflection,
                "boot_ts": self.boot_ts,
                "history": self.history[-50:],
            }
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            tmp.replace(self.path)

    def refresh(
        self,
        memory=None,
        brain=None,
        last_user_ts: Optional[float] = None,
        tools_active: Optional[List[str]] = None,
        tools_total: Optional[int] = None,
        work_session: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sense world + self, persist, return combined snapshot."""
        with self._lock:
            self.world = sense_world(memory=memory, brain=brain, last_user_ts=last_user_ts)
            self.self_state = sense_self(
                world=self.world,
                tools_active=tools_active,
                tools_total=tools_total,
                work_session=work_session,
                last_reflection=self.last_reflection,
            )
            self.tick_count += 1
            self.last_tick_ts = time.time()
            entry = {
                "tick": self.tick_count,
                "ts": self.world.get("ts"),
                "mode": (self.self_state.get("state") or {}).get("mode"),
                "intent": self.self_state.get("intent"),
                "action": self.last_action,
            }
            self.history.append(entry)
            self.history = self.history[-50:]
            self.save()
            return {"world": self.world, "self": self.self_state, "tick": self.tick_count}

    def record_action(self, action: str, reflection: Optional[str] = None):
        with self._lock:
            self.last_action = (action or "")[:500]
            if reflection:
                self.last_reflection = reflection[:800]
            self.save()

    def context_for_prompt(self) -> str:
        """Compact block for system / autonomy prompts."""
        if not self.world:
            return "Living state: not sensed yet."
        return (
            "### World\n"
            + world_summary(self.world)
            + "\n### Self\n"
            + self_summary(self.self_state)
            + (f"\n### Last action\n{self.last_action}" if self.last_action else "")
            + (f"\n### Last reflection\n{self.last_reflection}" if self.last_reflection else "")
        )

    def status_text(self) -> str:
        uptime_h = (time.time() - self.boot_ts) / 3600.0
        lines = [
            f"living_ticks={self.tick_count} uptime_h={uptime_h:.2f}",
            self.context_for_prompt(),
        ]
        return "\n".join(lines)

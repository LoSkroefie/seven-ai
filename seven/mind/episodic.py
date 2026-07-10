"""Episodic digests — summarize recent life into durable notes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from seven.agent.loop import Seven

logger = logging.getLogger("seven.episodic")


class EpisodicMemory:
    def __init__(self, agent: "Seven"):
        self.agent = agent
        self.last_digest_day: Optional[str] = None

    def maybe_daily_digest(self) -> Optional[str]:
        day = datetime.now().strftime("%Y-%m-%d")
        if self.last_digest_day == day:
            return None
        # only once per process day; also skip if digest exists
        existing = self.agent.memory.recent_digests(3)
        if any(d.get("period") == f"daily:{day}" for d in existing):
            self.last_digest_day = day
            return None
        body = self.build_digest(period=f"daily:{day}")
        if not body:
            return None
        self.agent.memory.add_digest(f"daily:{day}", body)
        self.agent.memory.add_note(body, title="daily_digest")
        try:
            from seven.memory.vector import SemanticMemory
            SemanticMemory(self.agent.memory).index(body, ref_type="digest")
        except Exception:
            pass
        self.last_digest_day = day
        return body

    def build_digest(self, period: str = "session") -> str:
        msgs = self.agent.memory.recent_messages(40)
        audits = self.agent.memory.recent_audit(25)
        goals = self.agent.memory.active_goals()
        beliefs = self.agent.memory.list_beliefs(10)
        blob = []
        blob.append(f"Period: {period}")
        blob.append(f"Messages: {len(msgs)} Audits: {len(audits)} Goals: {len(goals)}")
        if goals:
            blob.append("Goals: " + "; ".join(f"{g['title']}@{g['progress']}%" for g in goals[:5]))
        if beliefs:
            blob.append("Beliefs: " + "; ".join(f"{b['topic']}={b['stance']}" for b in beliefs[:5]))
        for a in audits[:12]:
            blob.append(f"tool {a.get('tool')} ok={a.get('ok')}: {(a.get('result_preview') or '')[:80]}")
        for m in msgs[-12:]:
            blob.append(f"{m['role']}: {(m['content'] or '')[:100]}")
        raw = "\n".join(blob)
        try:
            summary = self.agent.brain.generate(
                f"Summarize Seven's recent life into a tight episodic digest (6-10 lines). "
                f"Facts, actions, conclusions. No fluff.\n\n{raw[:4000]}",
                system="Episodic memory writer for Seven.",
                temperature=0.3,
                max_tokens=350,
            )
            return (summary or raw[:1500]).strip()
        except Exception as e:
            logger.debug("digest LLM failed: %s", e)
            return raw[:1500]

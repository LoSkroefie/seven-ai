"""
Silent smoke test for companion/freewill (no mic, no TTS).
Run: python scripts/smoke_companion.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seven.agent.loop import Seven
from seven.mind.freewill import FreeWill


def main() -> int:
    print("=== Companion smoke (quiet, free will) ===")
    s = Seven(tool_tier="core")
    s.freewill = FreeWill(s)
    s.freewill.min_invent_gap = 0
    s.freewill.min_speak_gap = 0
    s.autonomy.min_work_interval = 0

    print("--- /status-ish ---")
    print(s.handle("Just checking in — don't list commands, talk like yourself.")[:500])

    print("--- freewill decide ---")
    s.refresh_living_state()
    # Pretend ollama ok if ping worked
    d = s.freewill.decide(idle_min=30)
    print(f"decision: {d.action} — {d.reason}")

    print("--- freewill execute invent or work ---")
    if d.action in ("wait", "rest"):
        # force invent for smoke when brain available
        mode = (s.living.self_state.get("state") or {}).get("mode")
        if mode != "degraded_no_llm":
            from seven.mind.freewill import Decision
            d = Decision("invent_goal", "smoke force invent")
        else:
            print("SKIP invent: Ollama down")
            s.shutdown()
            return 0

    utter = s.freewill.execute(d)
    print(f"utter: {utter}")
    goals = s.memory.active_goals()
    print(f"goals: {goals}")
    print(f"living intent: {(s.living.self_state.get('intent'))}")

    print("--- natural follow-up ---")
    r = s.handle("What are you up to? Talk normally.")
    print(r[:800])

    s.shutdown()
    print("=== OK ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

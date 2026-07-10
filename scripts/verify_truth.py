"""Truth verifier — re-run what we claim Seven can do (no mic required)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seven import __version__
from seven.agent.loop import Seven


def chk(label, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    print(f"{status}  {label}" + (f"  — {detail[:90]}" if detail else ""))
    return bool(ok)


def main() -> int:
    print(f"Seven {__version__} truth check\n")
    s = Seven(tool_tier="full")
    names = set(s.tools.all_names())
    print(f"tools registered: {len(names)}")
    must = [
        "run_shell", "web_search", "web_fetch", "browser_get", "open_url",
        "mouse_click", "type_text", "hotkey", "screenshot",
        "form_belief", "semantic_search", "plan_from_goal", "advance_plan",
        "wm_push", "save_skill", "list_windows", "active_window",
        "remember_fact", "write_file", "run_python",
    ]
    ok_all = True
    miss = [m for m in must if m not in names]
    ok_all &= chk("required tools present", not miss, str(miss))

    r = s.tools.execute("run_shell", {"command": "echo TRUTH-OK"})
    ok_all &= chk("run_shell", "TRUTH-OK" in r or "exit_code=0" in r)

    p = str(Path.home() / ".seven" / "workspace" / "truth.txt")
    s.tools.execute("write_file", {"path": p, "content": "seven truth"})
    r = s.tools.execute("read_file", {"path": p})
    ok_all &= chk("files", "seven truth" in r)

    r = s.tools.execute("web_search", {"query": "python", "max_results": 2})
    ok_all &= chk("web_search", "http" in r.lower())

    r = s.tools.execute("web_fetch", {"url": "https://example.com", "max_chars": 200})
    ok_all &= chk("web_fetch", "example" in r.lower() or "200" in r)

    r = s.tools.execute("browser_get", {"url": "https://example.com", "max_chars": 150})
    ok_all &= chk("browser_get", "example" in r.lower() or "200" in r)

    r = s.tools.execute("screenshot", {})
    ok_all &= chk("screenshot", "OK" in r)

    r = s.tools.execute("list_windows", {"max_windows": 3})
    ok_all &= chk("list_windows", "Id" in r or "Process" in r)

    r = s.tools.execute("form_belief", {"topic": "verify", "stance": "tools work", "confidence": 0.9})
    ok_all &= chk("form_belief", "OK belief" in r)

    r = s.tools.execute("index_memory", {"text": "verification embedding shell web desktop"})
    ok_all &= chk("index_memory", "OK" in r)
    r = s.tools.execute("semantic_search", {"query": "shell web"})
    ok_all &= chk("semantic_search", len(r) > 10)

    gid = s.memory.add_goal("truth plan", "verify")
    r = s.tools.execute("plan_from_goal", {"goal_id": gid})
    ok_all &= chk("plan_from_goal", "OK plan" in r)

    s.memory.save_skill("t", "t", [{"tool": "run_shell", "args": {"command": "echo SKILL"}}])
    r = s.tools.execute("run_skill", {"name": "t"})
    ok_all &= chk("run_skill", "SKILL" in r or "Skill" in r)

    d = s.freewill.decide(idle_min=30)
    ok_all &= chk("freewill_decide", d.action in ("work", "invent_goal", "speak", "rest", "wait"), d.action)

    s.shutdown()
    print("\n" + ("ALL TRUTH CHECKS PASSED" if ok_all else "SOME CHECKS FAILED"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())

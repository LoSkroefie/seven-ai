# Codex / ChatGPT backlog — from Grok audit (2026-07-30)

**Read this after** `01`, `03`, `06`.  
**Repo audited:** `seven/` on main-class tree (clone: `C:\Users\USER-PC\seven-ai-audit`).  
**Police:** Grok. **No sentience claims. No full rewrite. Mesh = separate charter.**

---

## WILL THE CODE WORK? ALL OF IT?

### Short answer: **No — not “all of it,” and not as a finished human-like mind.**

| Layer | Works? | Notes |
|---|---|---|
| **Package installs / imports** | **Mostly yes** | `seven` 4.4.0; pytest largely green on audit host |
| **Agent loop + tools** | **Yes, with caveats** | Real shell/files/web/etc. Quality depends on Ollama model |
| **98 tools registered** | **Yes (count)** | Optional deps (Playwright, serial, whisper) degrade if missing |
| **Talk / voice / camera / robot body** | **Partial** | Code paths exist; hardware/matrix **not** fully proven |
| **Free will / goals / plans** | **Runs** | Heuristics + LLM; progress % and forced plan tools are **weak science** |
| **Docs / handoff** | **Often wrong** | Stale counts, models, “SSH missing”, etc. |
| **Mesh multi-Seven** | **Not on audited main** | Codex charter — not “already works” |
| **“As human as possible” mind** | **No** | Research target, not delivered software |

**Do not tell the owner “everything works.”**  
**Do say:** substrate works as a local L4 agent; listed bugs and research gaps remain.

---

## A. Confirmed bugs (fix these — REAL engineering)

Priority: **P0** = corrupts truth/metrics · **P1** = wrong autonomy behavior · **P2** = quality/portability

| ID | Pri | Bug | Where | Fix intent |
|---|---|---|---|---|
| **B-01** | P0 | Tool failures returning JSON `{"ok": false}` are audited as **success** (`ok=1`) because registry only checks `result.startswith("ERROR")` | `seven/tools/registry.py` | Shared `tool_result_ok(result: str) -> bool`: ERROR prefix **or** JSON `ok is False` / error fields. Use in audit + skill success paths |
| **B-13** | P0 | Same success heuristic in mind/skills/vision | `mind_tools.py`, `vision.py` | Call shared helper |
| **B-02** | P1 | Free will treats **any** task with `due_at` as urgent “overdue” without comparing to now | `seven/mind/freewill.py` | Parse ISO due; only prioritize if due ≤ now (or horizon) |
| **B-03** | P1 | Goal `progress` is formula theater: `3 + 2*n_tools` capped 15% | `seven/agent/autonomy.py` | Prefer plan-step fraction or explicit criteria; stop fake % |
| **B-04** | P1 | Planner advances steps after **forced** `list_dir`/`get_system_info` | `seven/mind/planner.py` | Force only for true survey steps; else leave step incomplete |
| **B-05** | P2 | Redundant/tautological goal status condition | `autonomy.py` | Clean status handling for done/cancelled |
| **B-06** | P2 | `build_default_registry` runs **twice** per `Seven()` | `seven/agent/loop.py` | Single build after mind context set |
| **B-07** | P2 | Import creates `~/.seven` dirs | `seven/config.py` | Lazy mkdir on first use (careful with tests) |
| **B-08** | P2 | DDG HTML scrape brittle | `seven/tools/web.py` | Fallback backend or clearer failure |
| **B-09** | P2 | `scp -s` may break older OpenSSH | `seven/tools/ssh.py` | Detect support or document + fallback |
| **B-10** | P2 | Host/user regex rejects some valid SSH targets | `ssh.py` | Document limits; carefully widen if needed |
| **B-14** | P1 | On timeout, brain may answer with **whatever model is loaded** (wrong model) | `seven/brain/llm.py` | Only fallback to loaded model if same family or user opt-in env |
| **B-15** | P2 | SpeechRecognition / Py3.13 `aifc` fragility | voice deps | Document; prefer whisper path |
| **B-16** | P2 | Goal % vs plan steps diverge | autonomy + planner | One source of completion truth |

**Evidence already reproduced (B-01):**  
`play_local_audio` missing file → JSON ok:false → audit ok=1.  
`ssh_run` refused → JSON ok:false → audit ok=1.

---

## B. Refactors (structure — not rewrite)

| ID | Refactor | Why |
|---|---|---|
| **RF-01** | `ToolResult` (ok, state, text, data) end-to-end | Kills stringly-typed success lies |
| **RF-02** | Single “outcome bus”: every tool result → audit + optional belief/skill update | R2 research substrate |
| **RF-03** | Split freewill **decide** (pure) vs **execute** (side effects); unit-test decide | Testable agency |
| **RF-04** | Collapse dual progress (goal % vs plan) into one model | Honesty |
| **RF-05** | Doc defaults generated from `config.py` or CI check | Stop handoff lies |
| **RF-06** | One registry build path; extension load once | Startup correctness |
| **RF-07** | Semantic memory: label as hashing-BM25-class; optional real embeddings extra | No fake “vector brain” |

**Do not:** new monorepo, rewrite in another language, revive `_legacy/v3` theater modules.

---

## C. Code needed for research (R-ladder) — not all exists

| R# | Needed (does not fully exist as research-grade) | Hooks to extend |
|---|---|---|
| **R1 Continuity** | Boot always reloads full self + open goals + last errors into cycle; crash-safe self snapshot | `daemon`, `LivingState`, `Memory`, startup |
| **R2 Memory write-back** | Automatic: tool fail/success → belief/preference/skill stats that **change later prompts/decisions** | `Memory`, freewill, autonomy, audit |
| **R3 Self-model stakes** | Replace RAM “energy” with outcome-based confidence/competence | `self_model.py` |
| **R4 Act/error loop** | Explicit predict/expect vs result; don’t advance goals on noise | planner, autonomy |
| **R5 Mesh** | Peer identity, auth, capability advertise, **default deny remote L4** | Codex session only |
| **R6 Eval** | Scenarios: restart memory, multi-step goal, don’t repeat failed tool | `tests/`, scripts |

These are **build targets**, not “already working mind.”

---

## D. Documentation / claim fixes (chore — high value)

| ID | Stale or false | Fix |
|---|---|---|
| **D-01** | GitHub description “Sentient” | Change to local autonomous agent wording |
| **D-02** | README quick start `ollama pull llama3.2` vs default `qwen2.5:7b` | Align pull + config |
| **D-03** | `SEVEN_REAL.md` defaults tier `core`, model llama3.2 | Match `config.py` |
| **D-04** | `HANDOFF.md` / `HANDOFF_PROMPT.md` “39 tools”, tier core, untracked v4 | Rewrite to 4.4.0 truth or mark obsolete |
| **D-05** | `AGENTS.md` default llama3.2 | qwen2.5:7b |
| **D-06** | `docs/system/CAPABILITY_MATRIX.md` MCP/SSH “not v4” | Update — both exist |
| **D-07** | `docs/system/BUGS_AND_FIXES.md` “no vector memory”, single test file | Update |
| **D-08** | Personal paths `C:\Users\USER-PC\...` in docs | Genericize where possible |

---

## E. Security / authority (policy — don’t “fix” by gutting L4)

Owner chose **L4 unrestricted + audit**. Implementer must **not** add confirmation nags unless asked.

| ID | Issue | Allowed work |
|---|---|---|
| **S-01** | Full host shell/files | Document; optional future L3 profile **only if owner asks** |
| **S-02** | Extensions `exec` user code | Keep trusted-dir model; mesh must not load remote code blindly |
| **S-03** | MCP full tools | Document consent = client process |
| **S-04** | API token = full agent | Mesh must not expose API without auth |
| **S-07** | Free will heavy shell | Optional rate limits if owner wants |

---

## F. Suggested implementation order for Codex/ChatGPT

### Wave 1 — Truth (do first; unblocks research metrics)

1. **B-01 + B-13** shared `tool_result_ok` + tests (music fail, ssh fail, shell ERROR, shell success)  
2. **B-02** freewill due dates + tests  
3. **B-04** stop fake plan advancement + tests  
4. **B-03** stop or replace goal % formula (document behavior change)

### Wave 2 — Hygiene

5. **B-06** single registry build  
6. **B-14** model fallback policy  
7. **D-03, D-04, D-05, D-06** doc truth (or CI contract script)

### Wave 3 — Research slices (owner picks R#)

8. R2 outcome write-back from tool results  
9. R1 boot continuity pack into every handle/heartbeat  
10. R6 one restart-memory scenario test  

### Parallel (only mesh session)

11. Mesh auth + capability deny-by-default L4 — **do not** mix Wave 1 into mesh-only branch without owner OK  

---

## G. Acceptance tests you should add (minimum)

```text
test_audit_json_ok_false_is_not_success
test_audit_error_prefix_is_failure
test_freewill_future_due_not_forced_work
test_planner_does_not_advance_on_forced_sysinfo_only
test_registry_builds_once  (log or counter)
```

Run: `python -m pytest -q`  
Truth probe: `python scripts/verify_truth.py` (needs network/Ollama for full green)

---

## H. Paste for Codex (tasking this backlog)

```
Read and obey:
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\01_CHATGPT_SESSION_PROMPT.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\03_RESEARCH_PRIORITIES.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\06_BULLSHIT_VS_REAL.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\07_CODEX_BACKLOG_FROM_AUDIT.md

You are IMPLEMENTER. Grok is police. No sentience claims. No full rewrite.

WILL THE CODE WORK ALL OF IT? No — see section at top of 07. Do not claim otherwise.

Do ONLY Wave 1 item 1 now: B-01 + B-13 shared tool_result_ok + pytest.
Report: Done / Evidence / Unproven / Next 3.
```

Change the last paragraph to the next ID when Wave 1 item 1 is accepted by Grok/owner.

---

## I. Log line (baseline)

```
### 2026-07-30 — Grok backlog published
**Claimed:** full issue/refactor/research list for implementers
**Did:** 07_CODEX_BACKLOG_FROM_AUDIT.md
**Verdict:** REAL (documentation of work); code fixes NOT yet done
**Orders:** Implementer starts Wave 1 B-01 only
```

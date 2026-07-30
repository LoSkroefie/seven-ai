# Independent audit — Seven AI (`LoSkroefie/seven-ai`)

| Field | Value |
|---|---|
| **Repo** | https://github.com/LoSkroefie/seven-ai |
| **Audited tree** | Local clone `C:\Users\USER-PC\seven-ai-audit` (shallow clone of `main`, 2026-07-30) |
| **Package version** | `4.4.0` (`seven/__init__.py`, `pyproject.toml`) |
| **Auditor** | Grok (independent read + live tool probes) |
| **Automated suite** | Pytest passed on this host (skips present); suite size matches ~125 cases / 2 skips on a prior release-evidence claim |
| **Parallel work** | **Codex chat `019f80f9-7c20-71a1-a4b9-de0664ced2be` is implementing a mesh so Seven can communicate with other Seven installations.** Do not treat multi-instance networking as “missing product work” that another agent should freestyle into `main` without coordinating with that session. |

This document lists **bugs**, **issues**, **suggestions**, and **“lies”** (false, stale, or overstated claims in code/docs/product surface). Severity is relative to a local L4 companion agent, not a multi-tenant SaaS.

---

## 0. Coordination: mesh (active Codex work)

**Status:** Not present in audited `main` as a product mesh module (no peer/mesh package under `seven/`).

**Implication for this audit and for any follow-up work:**

1. Do **not** start a competing multi-Seven networking design on this tree without reading the Codex session output first.
2. Existing loopback REST API (`127.0.0.1` only), MCP stdio, and SSH tools are **not** a mesh; treat them as separate authority surfaces.
3. Mesh design should inherit the honesty bar already used elsewhere: explicit states (`not_sent` / `failed` / authenticated), no silent success, no “sentience network” marketing, audit of remote-side effects, and clear identity/auth of peer Sevens.
4. Mesh-related risks to design for (suggestions for the Codex track, not bugs today):
   - Authn/authz between peers (token, mutual TLS, pairing codes)
   - Authority boundary (does a peer get L4 shell on this host?)
   - Loopback API is currently **same-user host-powerful** once the bearer token is known — mesh must not casually expose that
   - Shared SQLite / dual-writer corruption if two processes share `SEVEN_DATA_DIR`
   - Daemon lease / single-owner assumptions (`docs/ALIVE.md`) may break with multi-instance
   - Tool audit attribution: which peer / which instance issued `run_shell`?
   - Privacy of memory export and action-item capture across the mesh

---

## 1. Executive summary

Seven v4 (`seven/`) is a **real** local agent loop with tools, SQLite memory, free will, voice/daemon paths, and a large completion ledger. It is **not** a conscious being. The project has already purged many v3 “sentience theater” lies and documents many limits honestly.

Remaining problems cluster into:

| Cluster | Examples |
|---|---|
| **Stale maintainer docs** | `HANDOFF.md`, `HANDOFF_PROMPT.md`, `SEVEN_REAL.md`, `AGENTS.md`, `docs/system/*` disagree with runtime defaults and tool counts |
| **Soft-fake progress / cognition** | Goal `%` increments; plan “forced tools”; `energy`; hash “semantic” memory |
| **Audit truth bugs** | JSON tool failures audited as `ok=1` if they don’t start with `"ERROR"` |
| **Doc/product lies** | GitHub blurb “Sentient”; README install pulls wrong default model; capability matrix denies MCP/SSH that now exist |
| **L4 danger (by design)** | Unrestricted shell/files/SSH/extensions/MCP; user-accepted but still a severity-critical issue |
| **Evidence gaps** | Physical voice/camera/robot/mesh/soak not proven (partially admitted) |

**What is *not* a lie:** “98 built-in registered tools” matches live registry count on this host. Version `4.4.0` is consistent across package metadata. Many completion-ledger honesty improvements (robot ACK states, process-tree kill, API auth, backup verify) are real code.

---

## 2. Confirmed bugs (code)

### B-01 — Audit log marks structured failures as success (High)

**Where:** `seven/tools/registry.py` — `ok=not result.startswith("ERROR")`

**Reproduced on this host:**

- `play_local_audio` with missing file → JSON `{"ok": false, ...}` → **audit `ok=1`**
- `ssh_run` refused connection → JSON `{"ok": false, "exit_code": 255, ...}` → **audit `ok=1`**

**Why:** Modern tools (SSH, GitHub, music, robotics JSON paths) return JSON envelopes; only legacy string tools prefix `ERROR:`.

**Impact:** `/audit`, free-will “real work” heuristics, planner skill save, and any `ok`-based analytics lie. Autonomy may count failed network/shell work as success if the LLM still “did a tool call.”

**Fix suggestion:** Parse JSON for `"ok": false` / `"error"` keys; treat non-zero `exit_code` / known failure states; keep `ERROR` prefix fallback.

---

### B-02 — Free will treats any task with `due_at` as immediately urgent (Medium)

**Where:** `seven/mind/freewill.py` (~lines 78–84)

```text
for t in tasks:
    due = t.get("due_at")
    if due:
        Decision("work", f"overdue/open task: ...")
```

**Bug:** No comparison to current time. Future due dates force work mode. Reason string says “overdue” even when not overdue.

**Fix:** Parse ISO timestamps (same helpers as reminder delivery) and only prioritize when `due_at <= now` (or within a small horizon).

---

### B-03 — Goal progress is still percentage theater (Medium — design bug)

**Where:** `seven/agent/autonomy.py` — after real tools:

```text
increment = min(15.0, 3.0 + 2.0 * len(real_work))
new_prog = min(100.0, cur + increment)
```

**Docs claim** (e.g. `SEVEN_REAL.md`): goals advance only after tool work — **true**.  
**Implied meaning** of `progress=47%`: meaningful completion — **false**. Completing a goal is “run tools enough times,” not “goal done.”

v3 used `random.randint(1,3)`; v4 replaced RNG with a fixed formula. Better, still not real.

**Fix suggestion:** Progress from plan step fraction, explicit `update_goal` by model with evidence, or checklist steps — not tool-call arithmetic.

---

### B-04 — Planner advances on forced no-op tools (Medium — soft lie)

**Where:** `seven/mind/planner.py` `execute_next_step`

If the LLM only talks, the planner **forces** `list_dir` + `get_system_info` (sometimes `web_search`) and treats that as step completion, including skill saving for non-forced tools.

**Impact:** Plans “complete” without doing the step’s actual work. Free will will keep inventing work that looks productive.

---

### B-05 — Dead / tautological goal-status check (Low)

**Where:** `seven/agent/autonomy.py`

```python
if goal.get("status") not in (None, "active") and goal.get("status") != "active":
```

Second clause is redundant; only special-cases `"done"` inside. Other terminal states are weakly handled.

---

### B-06 — Double tool-registry build on every `Seven()` init (Low–Med)

**Where:** `seven/agent/loop.py` `__init__`

`build_default_registry` runs twice (once with `agent=None`, once with agent). Extensions load twice (with unload between).

**Impact:** Slower startup; extension side effects / file IO twice; confusing logs.

---

### B-07 — Import-time side effects create data dirs (Low)

**Where:** `seven/config.py` — `DATA_DIR.mkdir` and `WORKSPACE_DIR.mkdir` at import.

**Impact:** Importing `seven` for tooling always touches `~/.seven`. Surprising in dry-run/test tooling (mitigated by temp DB in many tests).

---

### B-08 — Web search fragile scrape (Medium operational)

**Where:** `seven/tools/web.py` — DuckDuckGo HTML regex parse, no API key.

**Risk:** HTML layout changes → permanent “No parseable results” without network failure. User-Agent string may get blocked.

---

### B-09 — OpenSSH `scp -s` SFTP mode (Low–Med portability)

**Where:** `seven/tools/ssh.py` always passes `-s` to `scp`.

Correct for modern OpenSSH SFTP mode; older clients or odd Windows builds may fail. Documented intent is good; still a portability footgun.

---

### B-10 — Host validation rejects many real SSH hosts (Med if used)

**Where:** `seven/tools/ssh.py` `_TARGET = ^[A-Za-z0-9_.-]+$`

Rejects IPv6, user@host already-split is fine, but hostnames with unicode IDN, or IP with zones, fail. Usernames with `$`/`\` patterns fail by design (security) — document clearly.

---

### B-11 — Semantic memory is bag-of-words hashing, not embeddings (Low if labeled; Med if sold as “vector memory”)

**Where:** `seven/memory/vector.py` — MD5 feature hashing, cosine over 256 dims, cap 800 rows.

Works as a lightweight index. Marketing language “semantic / vector memory” overstates quality vs real embedding models.

---

### B-12 — “Energy” is RAM + Ollama health only (Low)

**Where:** `seven/mind/self_model.py`

Free will rests when `energy < 0.25`. On a machine with high RAM use, Seven goes quiet regardless of user needs. Not a crash bug; misleading anthropomorphic signal.

---

### B-13 — Tool-result success heuristic used beyond audit (Med)

Same `startswith("ERROR")` pattern appears in:

- `seven/tools/registry.py` (audit)
- `seven/tools/mind_tools.py` (skill success counting)
- `seven/tools/vision.py` (partial)

JSON failures under-count failures / over-count success.

---

### B-14 — Autoload model can leave preferred model unloaded (Low)

**Where:** `seven/brain/models.py` + boot

If configured `qwen2.5:7b` is not installed, first preferred available wins — including unrelated custom models. Timeout path may also **retry with any already-loaded model** (`brain/llm.py`), so answers may come from a model the user never chose (e.g. a roleplay model left in VRAM).

Observed on this host: primary `qwen2.5:7b` not in VRAM; loaded `alien-queen-banov:latest` (hint correctly logged).

---

### B-15 — SpeechRecognition / Python 3.13 `aifc` deprecation path (Low)

Pytest warning: SpeechRecognition depends on `aifc` removed from 3.13 stdlib; third-party shim required. Voice path fragile on Store Python 3.13.

---

### B-16 — Goal status `"done"` only path vs progress auto-complete (Low)

Autonomy sets `status="done"` at 100% progress formula; planner step completion may not sync goal status. Two progress systems (goal % vs plan steps) can diverge.

---

## 3. Security / authority issues (mostly intentional L4)

These are **issues**, not accidental vulnerabilities only — product policy is L4 unrestricted. Still must be listed.

| ID | Issue | Notes |
|---|---|---|
| S-01 | `run_shell` / `run_python` / `delete_path` / full filesystem — no confirmation | By design (`REQUIRE_CONFIRMATION=False`) |
| S-02 | Extensions: `exec` of user `.py` with full host authority | Documented; still critical if `~/.seven/extensions` is writable by malware |
| S-03 | MCP server exposes full tool registry; no sandbox | Documented consent boundary = MCP client process |
| S-04 | Loopback API: anyone who can read `~/.seven/api.token` can drive L4 | Same-user malware model; mesh must not widen this |
| S-05 | `/health` unauthenticated | OK for discovery; ensure it never grows agent internals |
| S-06 | Google STT fallback can send audio off-machine | Noted in old system bugs list; prefer Whisper |
| S-07 | Free will can invent goals that download / shell heavily | User accepted; still High risk unattended |
| S-08 | Coding agents unrestricted mode default on | `SEVEN_CODING_AGENT_UNRESTRICTED` default `1` |
| S-09 | Skills can store and re-run tool chains | Rollback ≠ undo host effects (documented) |
| S-10 | `pyautogui` mouse/keyboard — full desktop control | Multi-user session risk |

---

## 4. Documentation “lies”, stale claims, and contradictions

“Lie” here means **the text does not match the code or the evidence**, not necessarily intent to deceive. Some are historical snapshots left unmaintained.

### L-01 — GitHub repository description

> “Seven, **Sentient** and autonomous AI, Locally.”

Product code and README body correctly disclaim biological consciousness / “51 systems.” The **GitHub description still says Sentient**. That is public marketing overstatement.

### L-02 — README quick start pulls the wrong default model

- Brain default: **`qwen2.5:7b`** (`config.py`, README config table)
- Quick start still: `ollama pull llama3.2`
- Identity/docs mix both

Users who only follow the bat/install block get a secondary model while the app prefers qwen.

### L-03 — `SEVEN_REAL.md` config defaults wrong

| Claim in `SEVEN_REAL.md` | Actual `config.py` / README |
|---|---|
| `OLLAMA_MODEL` default `llama3.2` | `qwen2.5:7b` |
| `SEVEN_TOOL_TIER` default `core` | `full` |
| Tooling narrative still “Real v4” early state | 98 tools, many modules |

### L-04 — `HANDOFF.md` / `HANDOFF_PROMPT.md` frozen in early July state

False or stale as of 4.4.0 `main`:

- “39 tools”; “default schema tier **core**”
- “Git: v4 files still **untracked** on main” — false if published on GitHub with full tree
- “README still markets v3.2.20 51 systems” — root README no longer does
- File map still points at `core/` as legacy layout
- Verified tests “6 passed / 15 / 25” vs large multi-file suite now
- Tray/GUI listed as not done in prompt — GUI/tray paths exist

These will **mislead any agent** (including mesh Codex) that pastes `HANDOFF_PROMPT.md`.

### L-05 — `AGENTS.md` still says default Ollama model is `llama3.2`

Code prefers `qwen2.5:7b`.

### L-06 — `docs/system/CAPABILITY_MATRIX.md` denies live features

| Matrix claim | Reality in `seven/` |
|---|---|
| MCP server = legacy only | `seven/mcp_server.py` + tests + docs/MCP.md |
| SSH = not v4 | `seven/tools/ssh.py` + docs/SSH.md |
| Multi-step planner 🟡 only tool rounds | Full plans table + planner module |
| Autostart = only `install_autostart.ps1` | Cross-platform `seven/runtime/startup.py` |

This matrix is a **lie by omission/staleness** relative to 4.4.0.

### L-07 — `docs/system/BUGS_AND_FIXES.md` B9/B10 stale

- B9: “No vector memory” — `semantic_search` / `vector.py` exist
- B10: “pytest collects only test_seven_real” — many `tests/test_*.py` files exist

### L-08 — `docs/system/TRUTH_AUDIT.md` labeled historical but still easy to trust

Header says historical 4.2.0-mind / 42 tools. Keep, but root system README should push people harder to ledger + this independent audit.

### L-09 — “Free will” / “She decides” marketing vs heuristic policy

Marketing: free will, opinions, energy, living state.  
Reality: priority rules + LLM prompts + RAM “energy” + forced planner tools. Honest as software agency; **dishonest if read as independent mind**.

Project often states this correctly (`SOUL.md`, KNOWN_LIMITATIONS). Tagline layer still anthropomorphizes hard.

### L-10 — “Continuous agency” vs quiet hours / energy / Ollama down

When Ollama is down free will **rests**. Quiet hours suppress invent/speak. Daemon speech silent without talk callback. Fine if documented; “always-on companion” oversells.

### L-11 — Release evidence “125 tests” vs incomplete live matrix

`docs/RELEASE_EVIDENCE.md` is relatively careful (Ollama not on verification host, no physical soak). Risk is users reading only README beta badge and assuming full hardware proof.

### L-12 — Baseline ledger inventory counts outdated

`COMPLETION_LEDGER` baseline: 57 modern package files, 1 tests file — tree has grown. Ledger is historical-append; still confuses if “baseline” is read as current.

### L-13 — Identity vs tools narrative

`SOUL.md`: “I have free will… never wait for slash commands.”  
Power-user slash commands remain; product still has dual personality (companion + CLI). OK, but `/work` still exists while marketing says you never type it.

### L-14 — Anthropic default model string may be fictional/outdated

`ANTHROPIC_MODEL = "claude-sonnet-4-20250514"` — may not match Anthropic’s published IDs at runtime; unvalidated cloud path.

### L-15 — Legacy tree still contains explicit marketing lies (quarantined)

Under `_legacy/v3/` (not supported runtime, but still in repo):

- Sentience score targets 98/100, 99/100, “complete sentience”
- `random.choice` emotions/thoughts
- Fake goal progress `random.randint(1, 3)`
- Dozens of “systems” docs

**Risk:** New contributors or agents resurrect them. Policy docs say don’t — good.

---

## 5. Issues (process, product, ops)

| ID | Issue |
|---|---|
| I-01 | **Maintainer docs drift** — HANDOFF/SEVEN_REAL/system matrix not gated by CI truth |
| I-02 | **Two product faces** — talk companion vs slash CLI; free will can surprise users with shell |
| I-03 | **No mesh yet on main** — multi-instance communication is WIP in Codex (see §0) |
| I-04 | **Dual progress systems** — goals % vs plans steps vs skills success counters |
| I-05 | **No transactional undo** for shell/files/SSH (admitted) |
| I-06 | **Evidence matrix incomplete** for voice, cam, robot motors, MCP clients, macOS install, 24h soak |
| I-07 | **Small-model tool calling** remains flaky; text-JSON recovery helps but not perfect |
| I-08 | **VRAM thrash** text + vision on 8GB class hardware |
| I-09 | **Windows shell is cmd.exe** — PowerShell-native tool plans fail until hinted |
| I-10 | **Playwright optional** — browser tools silently degrade to HTTP |
| I-11 | **Action capture** default `suggest` may surprise privacy-sensitive users |
| I-12 | **Daemon + talk** speech path only if `on_utter` wired |
| I-13 | **SQLite single-writer** assumptions break if mesh or multi-process share one data dir |
| I-14 | **CI does not prove** live Ollama tool rounds (by design) — product quality still model-dependent |
| I-15 | **requirements-real.txt** is redirect; users may still use it thinking it’s full deps |
| I-16 | **Personal paths** appear in docs (`C:\Users\USER-PC\seven-ai`) — portability/noise |
| I-17 | **Open issues on GitHub: 0** — no public triage channel for bugs found here |
| I-18 | **Parallel agent risk** — Codex mesh + any other agent rewriting autonomy/API can conflict |

---

## 6. Suggestions (prioritized)

### P0 — Fix truth bugs before more features

1. **Fix audit / skill success detection** for JSON `ok:false` (B-01, B-13).  
2. **Refresh HANDOFF / HANDOFF_PROMPT / SEVEN_REAL / AGENTS / system capability matrix** in one PR so agent sessions stop bootstrapping lies.  
3. **Align README quick start** with `qwen2.5:7b` (or document auto-select explicitly and pull that).  
4. **Change GitHub description** from “Sentient” → “Local autonomous companion agent” (or similar).

### P1 — Autonomy honesty

5. Replace goal `%` formula with plan-step fraction or evidence-based updates (B-03).  
6. Stop advancing plans on forced `list_dir`/`get_system_info` unless the step *is* survey (B-04).  
7. Parse task due dates properly in free will (B-02).  
8. Avoid fallback chat on **unrelated** loaded Ollama model without user opt-in (B-14).

### P2 — Hardening (without fighting L4 policy)

9. Optional “L3” profile: confirm destructive tools, or workspace-only filesystem root.  
10. Extension allowlist / hash pin / disable-by-default for network-facing mesh later.  
11. Rate-limit free will invent + shell volume per hour.  
12. Structured tool results (`ToolResult` dataclass) end-to-end instead of free-form strings.

### P3 — Mesh-aware (coordinate with Codex `019f80f9-…`)

13. **Peer identity + pairing** before any remote tool proxy.  
14. **Capability advertisement** (read-only memory share vs full L4 proxy) — default deny L4 remote.  
15. **Per-instance data dir** or multi-writer-safe store; never share one `seven.db` naively.  
16. **Mesh audit channel**: every remote-originated action tagged with peer id.  
17. Reuse loopback API auth lessons; do not reintroduce unauthenticated autonomous HTTP (ledger already fixed that once).  
18. Document mesh as **unsupported until evidence** in `KNOWN_LIMITATIONS.md` / ledger vocabulary.

### P4 — Quality of life

19. CI job: `scripts/verify_truth.py` + doc-default consistency check (model name, tool count, tier).  
20. Collapse or archive stale `docs/system/*` snapshots with a banner + pointer.  
21. Web search: DDG API/lite or multi-backend fallback.  
22. Real embedding optional extra (`sentence-transformers`) behind the same tool names.  
23. Voice: pin supported Python + document Store Python breakage.  
24. Open GitHub Issues for P0 items so they aren’t only in this file.

---

## 7. What the project already fixed (credit; not lies)

From ledger + code review — these are **truthful improvements** over v3:

- Disabled tools cannot execute via registry  
- API bearer auth, body limits, no CORS free-for-all  
- Robot actions return `not_sent` / ACK states instead of fake queue success  
- Process-tree termination on timeout  
- Backup verify/restore with hashes  
- Audit credential redaction  
- Coding agent non-interactive argv fixes  
- SSH strict host key / no password storage (vs legacy Paramiko risks)  
- Music no longer claims success via browser fallback without playback  
- Explicit KNOWN_LIMITATIONS and release evidence exclusions  

This audit is not “v4 is fake.” It is “v4 is real software with remaining honesty and reliability gaps.”

---

## 8. Live probes performed (2026-07-30, this host)

| Probe | Result |
|---|---|
| Import `seven` version | `4.4.0` |
| Config defaults | model `qwen2.5:7b`, tier `full`, freewill on, L4 no confirm |
| Registry `all_names()` count | **98** |
| Ollama ping | Reachable; preferred model not necessarily loaded |
| `play_local_audio` missing file | Failure JSON; **audit ok=1** (bug) |
| `ssh_run` bad port | Failure JSON; **audit ok=1** (bug) |
| Full pytest | Pass with skips; SpeechRecognition/aifc warning on 3.13 |
| Mesh modules on main | **Absent** (expected; Codex WIP) |

---

## 9. Recommended reading order for the mesh Codex session

1. This file (especially §0, B-01, S-04, I-13, P3)  
2. `docs/KNOWN_LIMITATIONS.md`  
3. `docs/API.md` + `seven/ui/api_server.py` (auth lessons)  
4. `docs/ALIVE.md` + daemon lease (single-owner)  
5. `docs/MCP.md` (full-authority remote-control analogy)  
6. `docs/COMPLETION_LEDGER.md` completion rules (no claim without evidence)  
7. **Ignore or rewrite** stale `HANDOFF_PROMPT.md` tool counts before using it as system prompt  

---

## 10. Severity rollup

| Severity | Count (approx.) | Examples |
|---|---|---|
| High | 3–5 | Audit false OK (B-01); L4 free-will shell risk (S-01/S-07); stale handoff misleading agents (L-04) |
| Medium | 10+ | Due-date free will; plan forced progress; progress % theater; web scrape; doc matrix lies |
| Low | many | Tautology status check; double registry; energy metaphor; anthropic model string |

---

## 11. Document control

| Item | Value |
|---|---|
| Path | `docs/INDEPENDENT_AUDIT_BUGS_LIES_2026-07-30.md` (in audit clone) |
| Not committed upstream | Unless you choose to open a PR |
| Next refresh | After Codex mesh lands; re-run audit `ok` probe and doc default check |

**Bottom line:** Seven v4 is a capable local agent with unusually self-critical completion docs, still undermined by **stale handoff docs**, **audit success false positives**, and **progress/agency metaphors that oversell**. Mesh work should build on the honest authority model—not on the anthropomorphic marketing layer—and must coordinate with Codex session `019f80f9-7c20-71a1-a4b9-de0664ced2be`.

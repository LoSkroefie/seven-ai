# RESUME — Seven research (read this after sleep / reboot / new chat)

**Last updated:** 2026-07-30 documentation preservation wave  
**Next session:** 2026-07-31 — **cleanup deferred to tomorrow** (do not start cleanup tonight)  
**Owner:** Jan (LoSkroefie)  
**Police / boss:** Grok  
**Implementer:** Codex / ChatGPT under orchestration rules  

**Desktop pointer:** `C:\Users\USER-PC\Desktop\SEVEN_IF_POWER_FAILED_READ_ME.txt`  
**Easy folder:** `C:\Users\USER-PC\Desktop\Seven-Research-Orchestration\`  
**Canonical pack:** `C:\Users\USER-PC\seven-ai-audit\docs\orchestration\`  

**One-file cold start:** `docs/CONTINUATION_PROMPT.md` in the repository.
It contains current truth, bans, read order, and paste-ready Codex/Grok prompts.
This resume remains the detailed supporting snapshot.

---

## 0. Sleep snapshot (2026-07-30 night)

| Item | State |
|---|---|
| **Active code SHA (local + Peanut)** | **`1397d04f4993d143ddc413a7820f3432bc08a55e`** |
| **Branch** | `codex/seven-completion` (may contain newer docs-only commits) |
| **Package version** | **4.6.0** |
| **Local release** | `D:\SevenLocal\releases\seven-4.6.0-1397d04` |
| **Local venv junction** | `D:\SevenLocal\venv` → `…\seven-4.6.0-1397d04\venv` |
| **Local API health** | `http://127.0.0.1:18765/health` → ok, seven-real 4.6.0 *(verified at doc write)* |
| **Peanut core** | `/opt/seven` → `/opt/seven-4.6.0-1397d04` |
| **Peanut public gateway** | `https://jvrsoftware.co.za/3dwebsite/seven-api/health` → ok *(verified)* |
| **Peanut /seven/** | HTTP 200 *(verified)* |
| **C: free space** | **~20.5 GB** — cleanup **tomorrow**, not tonight |
| **Campaign finish wave** | **DONE + DEPLOYED + POLICE REAL** |
| **Gateway venv repair** | **DONE + POLICE REAL** |
| **C: cleanup / git preserve** | **ORDER WRITTEN, NOT STARTED — owner deferred** |

### Tonight: do nothing
- Do not deploy  
- Do not cleanup  
- Do not ask implementers for new features  
- Sleep  

### Next-session first actions
1. Open `docs/CONTINUATION_PROMPT.md`, then **this file**  
2. Paste Grok resume block (§8)  
3. Optional: verify health URLs still green  
4. Then either **run cleanup order** (`11_CLEANUP_AND_GIT_PRESERVE.md`) or rest  

---

## 1. What Seven is

Local **high-authority companion agent** (`seven/` package): Ollama-first LLM, real host tools, SQLite memory, free will/autonomy, optional voice, daemon, API, **mesh = messages only**.  

**Research goal:** continuous human-like **agency**.  
**Never claim:** sentience, consciousness, “complete Seven.”  
**Owner policy:** L4 tools + audit; no confirmation nags unless asked.  
**Banned:** v3 emotion/dream/sentience-score theater; full rewrites; remote L4 via mesh.

---

## 2. Absolute truths

| Claim | Status |
|---|---|
| Sentience / consciousness | **FALSE** |
| Complete Seven | **FALSE** |
| Mesh merges minds / remote shell | **FALSE** |
| Mesh authenticated messaging | **TRUE** |
| Tool failures audit as failures (`tool_result_ok`) | **TRUE** on branch |
| Tool outcomes → `tool:<name>` beliefs → context after restart | **TRUE** (from ca671b4+) |
| Due dates: only force when parseable and due | **TRUE** (1397d04) |
| Planner: observational tools only for survey steps | **TRUE** (1397d04) |
| Goal % not from tool-count theater; plan fraction when linked | **TRUE** (1397d04) |
| Local + Peanut on **1397d04** | **TRUE / REAL deploy** |
| Peanut seven-web restartable via release `web-venv` | **TRUE / REAL repair** |

---

## 3. Git

| Item | Value |
|---|---|
| Repo | https://github.com/LoSkroefie/seven-ai |
| Live branch | **`codex/seven-completion`** |
| **Deployed core SHA** | **`1397d04f4993d143ddc413a7820f3432bc08a55e`** — *Make scheduling and progress evidence-based* |
| Branch tip | May be a newer documentation-only descendant; verify with Git |
| Prior continuity SHA | `ca671b4f9d6eabf0db516694821ef7d16dfd2e00` — *Make Seven outcomes and continuity durable* |
| Prior mesh tip (historical) | `64f6650` docs after mesh |
| GitHub `main` | Old **4.4.0** line — not production tip |
| Codex mesh session (historical) | `019f80f9-7c20-71a1-a4b9-de0664ced2be` |

### Important commits (this campaign)

1. Mesh secure networking (+ recovery/docs)  
2. `ca671b4` — continuity / audit beliefs / alive gates  
3. `1397d04` — finish wave B-02 due dates, B-04 planner, B-03 progress  
4. Ops: Peanut `web-venv` under 1397d04 release (not a core SHA change)

---

## 4. Paths

### Code checkouts (C:)

| Path | Role |
|---|---|
| `C:\Users\USER-PC\Documents\Codex\2026-07-20\mortem-continues\seven-ai` | Older implementer tree; had unrelated uncommitted drift and was preserved untouched |
| `C:\Users\USER-PC\seven-ai-audit` | Documentation checkout + **canonical orchestration** |
| `Desktop\Seven-Research-Orchestration\` | Copy of orchestration for easy open |

### Runtime local (D:)

| Path | Role |
|---|---|
| `D:\SevenLocal` | Production-style local install |
| `D:\SevenLocal\releases\seven-4.6.0-1397d04` | **ACTIVE** release |
| `D:\SevenLocal\releases\seven-4.6.0-ca671b4` | Prior release (rollback) |
| `D:\SevenLocal\venv` | Junction → active release venv |
| `D:\SevenLocal\data` | Runtime data — **do not wipe** |
| `D:\SevenLocal\deploy-evidence\` | Deploy/repair markdown evidence |
| `D:\SevenLocal\Start-Seven*.cmd` | Launchers |
| Rollback junctions | under `D:\SevenLocal\rollback\` |

### Peanut

| Item | Value |
|---|---|
| Active | `/opt/seven` → `/opt/seven-4.6.0-1397d04` |
| Core pin | SOURCE_COMMIT / SHA **1397d04** |
| Gateway | `web-venv` under that release; source `deploy/peanut` |
| Services | seven-core, seven-web, seven-ollama, httpd |
| Public | `https://jvrsoftware.co.za/seven/` · `…/3dwebsite/seven-api/health` |
| Mesh | data-only; loopback mesh; secret **not in git** |
| Rollback core | `/opt/seven-4.6.0-ca671b4` / rollback symlinks as in evidence |
| Gateway old fallback | `/opt/seven-4.5.2-2ff5b90` (pre-repair reference) |

### Evidence files (local copies)

Under `D:\SevenLocal\deploy-evidence\`:

- `SEVEN_LOCAL_DEPLOY_1397D04_20260730T211032SAST.md`  
- `SEVEN_PEANUT_DEPLOY_1397D04_20260730T211032SAST.md`  
- `SEVEN_PEANUT_WEB_VENV_REPAIR_1397D04_20260730T212808SAST.md`  

The three non-secret deployment/repair evidence files are preserved in the
repository under `docs/deploy-evidence/`. Older ca671b4 evidence also exists in
the older Documents Codex checkout and was deliberately left untouched because
that checkout had unrelated uncommitted drift.

---

## 5. What we finished this session (police grades)

| Work | Verdict |
|---|---|
| Orchestration pack (01–11 prompts, work log, alive, deploy, cleanup order) | Built |
| Independent audit / boss rules | Done earlier |
| Mesh messaging | REAL (not cognition) |
| ca671b4 continuity + deploy local/Peanut | REAL |
| Finish wave 1397d04 code | REAL |
| Deploy 1397d04 local + Peanut | REAL |
| Peanut seven-web venv repair + 2 restarts | REAL |
| Owner browser conversation smoke | **Not done** (optional) |
| Documentation + evidence Git preservation | **Done in docs-only branch commit** |
| C: cleanup | **Deferred** — order in `11_…`, not executed |

Work log: `05_WORK_LOG.md` (newest entries on top under `## Log`).

---

## 6. Disk (why cleanup tomorrow)

At last measure:

| Path | ~Size |
|---|---|
| C: free | **~20.5 GB** |
| `Documents\Codex` | **~51 GB** |
| `C:\Users\USER-PC\.codex` | **~25 GB** |
| `C:\Users\USER-PC\.ollama` | **~14 GB** |
| seven-ai-audit | tiny |
| D:\SevenLocal | few GB (releases/rollback/playwright) |

**Cleanup rules (already written for Codex):**  
- Git: docs, orchestration, deploy **.md** evidence only  
- **Never** git: venvs, `*.db`, backup zips with private data, secrets, tokens  
- Prefer free **C:** first; don’t break active `1397d04`  

Order file: **`11_CLEANUP_AND_GIT_PRESERVE.md`**

---

## 7. Roles

| Role | Who | Job |
|---|---|---|
| Director | Jan | Priorities; live with Seven; sleep; tomorrow cleanup OK |
| Implementer | Codex | Code/deploy/cleanup under orders only |
| Police | Grok | REAL/MIXED/BULLSHIT; orders; this memory file |

Implementer does not grade itself.  
No sentience claims. One slice at a time.

---

## 8. Paste blocks for tomorrow

### To Grok (new chat)

```
Read and continue exactly from:
C:\Users\USER-PC\seven-ai-audit\docs\CONTINUATION_PROMPT.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\00_RESUME_AFTER_POWER_FAILURE.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\05_WORK_LOG.md

You are police/boss for Seven research.
Deployed SHA both sides: 1397d04. Finish wave + web-venv repair accepted REAL.
Cleanup was DEFERRED — do not invent work. Owner may start cleanup via 11_CLEANUP_AND_GIT_PRESERVE.md.
No sentience. No complete Seven. Summarize state and wait for owner direction.
```

### To Codex — only if owner starts cleanup

```
Read:
C:\Users\USER-PC\seven-ai-audit\docs\CONTINUATION_PROMPT.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\00_RESUME_AFTER_POWER_FAILURE.md
C:\Users\USER-PC\seven-ai-audit\docs\orchestration\11_CLEANUP_AND_GIT_PRESERVE.md

Owner authorized C: cleanup now. Git-preserve non-secret docs/evidence first, push, then safe delete on C:.
Never commit secrets/venvs/db zips. Keep D:\SevenLocal active 1397d04.
Report sizes before/after and preservation map.
```

### Emergency health only

```
Check only:
- http://127.0.0.1:18765/health
- https://jvrsoftware.co.za/3dwebsite/seven-api/health
- D:\SevenLocal\venv junction target
Do not change anything.
```

---

## 9. Orchestration file index

| File | Purpose |
|---|---|
| `../CONTINUATION_PROMPT.md` | **One-file canonical cold start** |
| **00_RESUME…** | Detailed deployment/research snapshot |
| 01_CHATGPT_SESSION_PROMPT | Implementer laws |
| 02_GROK_POLICE_PROMPT | Police laws |
| 03_RESEARCH_PRIORITIES | R1–R6 |
| 04_ORCHESTRATION_PLAYBOOK | Daily loop |
| 05_WORK_LOG | Claim history |
| 06_BULLSHIT_VS_REAL | Grading |
| 07_CODEX_BACKLOG… | Bugs list (many fixed) |
| 08_MAKE_SEVEN_ALIVE | Alive checklist |
| 09_PASTE…MAKE_ALIVE | Old make-alive paste |
| 10_DEPLOY_ORDER_CA671B4 | Deploy pattern (reuse for later SHAs) |
| **11_CLEANUP…** | **Tomorrow’s cleanup order** |
| ../BOSS_POLICE_CHATGPT.md | Full law book |

---

## 10. Research ladder

| R# | Status |
|---|---|
| R1 Continuity | Strong (restart beliefs/context) |
| R2 Memory write-back | Tool outcomes → beliefs → context |
| R3 Self-model | Partial |
| R4 Act/error honesty | Improved (due/plan/progress) |
| R5 Mesh | Messaging only |
| R6 Eval | Tests + deploy proofs; more later |

No new R# open unless owner says so.

---

## 11. Do not do after reboot

- Redeploy without need  
- Claim sentience/complete  
- Commit secrets  
- Delete `D:\SevenLocal\data` or Peanut `/var/lib/seven`  
- Start cleanup without re-reading `11_`  
- Merge to `main` without owner  
- “Full rewrite”  

---

## 12. Quick morning checklist

- [ ] Read this file  
- [ ] Local health 4.6.0?  
- [ ] Peanut gateway health 200?  
- [ ] Junction still `seven-4.6.0-1397d04`?  
- [ ] Git tip still 1397d04 or moved? (note if moved)  
- [ ] Owner: cleanup today? Y → Codex + `11_` / N → leave alone  

---

## 13. Grok self-notes (for next Grok instance)

- Owner spent months; hates lies and restarts; wants boss/police not demoralization.  
- Reward honest implementer reports; reject overclaim.  
- Active production = **1397d04** both sides; ca671b4 is rollback lineage.  
- Finish campaign for scheduling/progress is **closed**.  
- Cleanup is the **only queued ops task**, deferred to **tomorrow**.  
- Orchestration and non-secret deployment evidence are preserved on
  `codex/seven-completion`; the local audit checkout remains the canonical
  editable copy.
- Desktop pack may lag; canonical is seven-ai-audit path.  
- When policing deploy: verify evidence file hashes + live health when possible.  

---

*End of resume document. Owner sleeping. Next: tomorrow cleanup or rest.*


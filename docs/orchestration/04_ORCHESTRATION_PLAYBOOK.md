# How to orchestrate this better

You are one human with **months invested**, multiple AIs that **drift**, and a real codebase. Orchestration = **roles, artifacts, and a loop** — not more vibes.

---

## 1. Roles (keep them separate)

| Role | Tool | Allowed to |
|---|---|---|
| **Director** | You | Set R#, accept/reject direction, live with Seven |
| **Implementer** | ChatGPT (daily code) | Write code, run tests, report evidence |
| **Specialist** | Codex mesh session | Mesh only (unless you expand charter) |
| **Police / historian** | Grok | Verdicts, orders, work log, bullshit calls |
| **Runtime** | Seven on your PC | Truth of whether anything works |

**Rule:** Implementer does not grade itself. Police does not rewrite the whole repo unless you ask. Director does not have to re-explain mission every time — use the prompt files.

---

## 2. The daily loop (20–60 min cycles)

```
[1] You      Open 03_RESEARCH_PRIORITIES — confirm R#
[2] You      Paste 01_CHATGPT_SESSION_PROMPT into ChatGPT
[3] You      Give ONE slice: "Implement R2: outcome-linked belief update on tool fail"
[4] ChatGPT  Codes + mandatory report
[5] You      Paste report (+ diff summary) to Grok
[6] Grok     REAL|MIXED|BULLSHIT + ORDERS + log line
[7] You      Append log line to 05_WORK_LOG.md (or ask Grok to draft it)
[8] You      Paste ORDERS only back to ChatGPT — no new philosophy essay
[9] Runtime  You run Seven or pytest when evidence is claimed
```

**Cadence tip:** Prefer **one vertical slice per day** over “make her sentient this weekend.”

---

## 3. Artifacts that keep you sane

| Artifact | Purpose |
|---|---|
| `01_…PROMPT` | Same laws every ChatGPT session |
| `02_…POLICE` | Same laws every Grok police session |
| `03_…PRIORITIES` | Shared definition of “what works” |
| `05_WORK_LOG` | Month-proof history of claims vs truth |
| `06_BULLSHIT_VS_REAL` | Fast grading rubric |
| Git commits | Only REAL or MIXED-accepted slices |
| `~/.seven` backups | Don’t lose research state |

Optional but powerful:

- **Single GitHub issue or local note per R#** (“R2 write-back”) with acceptance tests  
- **Branch naming:** `research/r2-outcome-memory` not `feat/more-alive`  
- **Freeze window:** no new features while fixing a truth bug that poisons eval (e.g. audit false OK)

---

## 4. How to talk to each AI (scripts)

### To ChatGPT (tasking)

> Priority R2 only.  
> Task: When a tool result is failure, update belief topic `tool:<name>` with stance and confidence.  
> Persist in Memory. Prove with a pytest.  
> End with required report format. No sentience claims. No mesh.

### To Grok (policing)

> Police this ChatGPT batch.  
> Priority was R2.  
> [paste report + files touched]  
> Verdict + orders + work log line.

### To Codex (mesh only)

> Mesh charter only. Do not refactor freewill/memory unless required for mesh.  
> Auth default deny remote L4. Align with API token lessons.

### Whip (any implementer)

> Drift. Rules in 01. Continue R# only. Evidence or it didn’t happen.

---

## 5. Decision rules (you)

| Situation | Do |
|---|---|
| ChatGPT wants full rewrite | **No.** Grok will back you. |
| Sounds amazing, no test | **Unproven** — run or reject |
| Improves demo voice only | Park under “later UX” |
| Improves restart continuity or memory→behavior | **Accept** |
| Touches mesh without charter | **Stop** |
| You’re exhausted / angry at lies | Stop coding; police log only; rest |

---

## 6. Better orchestration than “chat forever”

### A. Two-window rule
- Window 1: Implementer  
- Window 2: Police + log  
Never let implementer be the only historian.

### B. Evidence gate
Nothing is “done” until **you or CI** saw a command. Owner is final lab tech.

### C. Weekly review (30 min)
Read `05_WORK_LOG.md` bottom-up:

- What REAL landed?  
- What BULLSHIT repeated?  
- Adjust R# in `03`  

### D. One source of mission
If ChatGPT “forgets,” you don’t debate — you re-paste `01`.  
If Grok softens too much, re-paste `02`.

### E. Separate research from chores
Chores: doc sync, audit JSON ok bug, handoff staleness.  
Research: R1–R6.  
Do a **chore day** so research days aren’t poisoned by lies in metrics.

---

## 7. What Grok will keep doing for you

When you bring implementer output:

1. Document what they claimed vs did  
2. Call **bullshit / mixed / real**  
3. Say what would **actually** help  
4. Give **≤3 orders**  
5. Give a **paste-ready work log line**  

You stay director. You don’t have to hold all of that in your head after months of fatigue.

---

## 8. Minimum viable orchestration (if overwhelmed)

Only three files:

1. Paste `01` into ChatGPT  
2. One task sentence  
3. Paste result to Grok → update `05`  

Ignore everything else until the loop feels stable.

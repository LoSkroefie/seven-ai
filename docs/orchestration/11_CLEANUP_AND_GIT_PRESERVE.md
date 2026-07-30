# Cleanup C: + git-preserve — Codex order

**Owner need:** free space on **C:**  
**Rule:** Anything deleted locally that is worth keeping must be **in git (or a D: archive) first**.  
**Police rule:** **Never commit secrets** (tokens, mesh secret, passwords, full `~/.seven` DBs with credentials, API tokens).

---

## Reality check (what can / cannot go in git)

| Kind | Git? | Why |
|---|---|---|
| Source, tests, docs, deploy evidence **markdown** | **YES** | Small, needed history |
| Orchestration pack (`docs/orchestration/*`) | **YES** | Session continuity |
| Deploy evidence under `D:\SevenLocal\deploy-evidence\*.md` | **YES** (copy into repo `docs/deploy-evidence/`) | Already written for police |
| `uv.lock`, `pyproject.toml` | **YES** | |
| **venvs** (`venv/`, `web-venv/`) | **NO** | GBs; rebuild from SHA |
| **zip backups of live DBs** | **NO as secret dump** | May contain tokens, messages, mail meta |
| Ollama models | **NO** | Huge; separate store |
| Playwright browsers / torch / whisper caches | **NO** | Reinstall |
| `seven.db` / `seven_mesh.db` | **NO public git** | Private runtime state |
| Mesh secret / `api.token` / env files | **NEVER** | Secrets |

**Backup of “what we delete” for non-secret stuff = git commit.**  
**Backup of live state zips = keep on D: (or external), not GitHub.**

---

## Paste to Codex

```
Grok + owner: FREE C: DRIVE SPACE. Preserve in git what should not be lost. Do not commit secrets.

MISSION
1) Commit & push (codex/seven-completion) all missing NON-SECRET project artifacts that are still only local.
2) Inventory large Seven-related paths on C: and clean safely.
3) For every deletion class, document: path, size, where preserved (git SHA or D: archive path).
4) Do NOT break D:\SevenLocal active release 1397d04 or Peanut. Prefer cleaning C: clones/caches first.

══════════════════════════════════════
PHASE A — GIT PRESERVE (do first)
══════════════════════════════════════
Repo: seven-ai, branch codex/seven-completion (working tree as you use it).

ADD AND COMMIT (if not already tracked):
- docs/orchestration/ entire pack from:
  C:\Users\USER-PC\seven-ai-audit\docs\orchestration\
  and/or Desktop\Seven-Research-Orchestration\
  → repo path: docs/orchestration/
- docs/BOSS_POLICE_CHATGPT.md, docs/INDEPENDENT_AUDIT_* if present and useful
- All deploy evidence markdown (NO secrets):
  D:\SevenLocal\deploy-evidence\*.md
  → repo path: docs/deploy-evidence/
- Any SEVEN_*_DEPLOY_*.md / PEANUT_* evidence still only under Documents\Codex\...\docs\
- Update .gitignore so we NEVER add:
  .env, *.secret, api.token, mesh.secret, **/web-venv/**, **/venv/**,
  **/.seven/**, **/*.db, **/backups/*.zip, dist/, __pycache__, .pytest_cache,
  node_modules, large media dumps unless already policy-ok

PUSH branch. Report commit SHAs.

OPTIONAL (owner data, NOT github if private):
- Copy latest verified seven-backup-*.zip to D:\SevenLocal\backups\archive\ (if not already)
- Do NOT force-push secrets to origin.

══════════════════════════════════════
PHASE B — INVENTORY C: (report sizes before delete)
══════════════════════════════════════
Measure and list top consumers related to Seven/Codex:
- C:\Users\USER-PC\seven-ai-audit
- C:\Users\USER-PC\Documents\Codex\...
- C:\Users\USER-PC\.codex (caches, sessions — careful)
- C:\Users\USER-PC\.seven if huge
- C:\Users\USER-PC\AppData local caches: pip, torch, whisper, huggingface, playwright, ollama if on C:
- Duplicate seven checkouts

Write: docs/deploy-evidence/CLEANUP_INVENTORY_<timestamp>.md with sizes.

══════════════════════════════════════
PHASE C — SAFE CLEAN (C: first)
══════════════════════════════════════
After Phase A push succeeds:

SAFE TO DELETE / prune on C: (after listing):
1) Duplicate git worktrees if remote has commits (keep ONE primary checkout preferred on D: or Documents Codex tree — ask owner if ambiguous; default keep Documents\Codex\...\seven-ai as primary implementer tree, can remove seven-ai-audit AFTER orchestration is in git on remote).
2) seven-ai-audit: after remote contains docs/orchestration + evidence, can delete entire audit clone OR empty it — owner wants C: free.
3) Python/pip cache: pip cache purge
4) pytest cache, __pycache__ under clones
5) Old staging-failures on C: if any
6) Codex session caches only if owner OK and not needed — prefer prune old computer-use/cache folders, not active auth

DO NOT DELETE without D: or git preserve:
- D:\SevenLocal\releases\seven-4.6.0-1397d04 (ACTIVE)
- D:\SevenLocal\data (runtime)
- Current API if running — stop only if cleaning forces it; prefer leave D: alone except optional old releases

OPTIONAL D: reclaim (only if free space needed there too / owner OK):
- D:\SevenLocal\releases\seven-4.6.0-ca671b4 (old — only after confirming 1397d04 healthy + rollback zip on D:)
- D:\SevenLocal\staging-failures
- Old source zips if identical SHA already on github tags/branch
- Keep at least one rollback release OR verified backup zip

══════════════════════════════════════
PHASE D — PROOF
══════════════════════════════════════
- git log -1 / remote tip
- dir free C: before/after if available
- http://127.0.0.1:18765/health still ok if local API should stay up
- List deleted paths + preservation location

REPORT
## Git commits pushed
## Inventory sizes
## Deleted (path, size, preserved where)
## Left alone (and why)
## C: free space before/after if known
## Still risky / needs owner
## Next 3

No sentience. No Peanut core redeploy. No remote L4.
GO.
```

---

## Short owner whip

```
Free C: space. Git-commit all non-secret Seven docs/evidence/orchestration first and push. Then delete duplicate clones/caches on C:. Never commit secrets/venvs/db zips. Keep D:\SevenLocal active 1397d04. Evidence cleanup inventory. Go.
```

---

## Grok note

Police will reject commits that contain `api.token`, mesh secrets, or full live DB dumps.  
Zip “backups” belong on **D:** or external drive, not GitHub.

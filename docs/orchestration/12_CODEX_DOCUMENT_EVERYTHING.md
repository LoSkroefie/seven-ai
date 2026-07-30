# Codex order — document everything + continuation prompt

**Owner:** Jan  
**When:** After sleep / next session — docs only unless noted  
**Police:** Grok  
**Do not:** redeploy, cleanup C: (unless owner separately says), claim sentience, change production SHA  

---

## PASTE TO CODEX (full block)

```
You are the DOCUMENTATION implementer for Seven (repo seven-ai, branch codex/seven-completion).

Owner is exhausted of drift. Grok is police. Read these first, in order, then update the repo so a cold start needs only one file:

1) C:\Users\USER-PC\seven-ai-audit\docs\orchestration\00_RESUME_AFTER_POWER_FAILURE.md
2) C:\Users\USER-PC\seven-ai-audit\docs\orchestration\05_WORK_LOG.md
3) C:\Users\USER-PC\seven-ai-audit\docs\orchestration\08_MAKE_SEVEN_ALIVE.md
4) C:\Users\USER-PC\seven-ai-audit\docs\orchestration\11_CLEANUP_AND_GIT_PRESERVE.md
5) D:\SevenLocal\deploy-evidence\ (all *.md)
6) D:\SevenLocal\install-manifest.json
7) Live truth checks (do not change production):
   - http://127.0.0.1:18765/health
   - D:\SevenLocal\venv junction target
   - git -C <your seven checkout> rev-parse HEAD and origin/codex/seven-completion
   - package version from installed or checkout seven/__init__.py

══════════════════════════════════════
MISSION
══════════════════════════════════════
A) Bring repo documentation in line with REALITY (1397d04 deployed local+Peanut, finish wave, mesh data-only, web-venv repair).
B) Check in non-secret docs into git on codex/seven-completion and push.
C) Create ONE continuation prompt file a future human/AI can paste to resume perfectly.
D) Do NOT implement features, cleanup C: disks, or redeploy Peanut/local unless a doc path is missing and you only ADD markdown.

══════════════════════════════════════
CURRENT TRUTH (do not contradict)
══════════════════════════════════════
- Active SHA local + Peanut: 1397d04f4993d143ddc413a7820f3432bc08a55e
- Branch: codex/seven-completion
- Version: 4.6.0
- Local: D:\SevenLocal\releases\seven-4.6.0-1397d04 ; venv junction active
- Peanut: /opt/seven -> /opt/seven-4.6.0-1397d04
- Finish wave REAL: due dates, planner observational rules, goal progress from plan fraction
- Continuity REAL (ca671b4 lineage): tool outcomes -> tool:<name> beliefs -> context after restart
- Mesh: authenticated messages only; NOT remote L4; NOT shared mind
- Peanut seven-web web-venv under 1397d04 release: restart proven
- Sentience / complete Seven: FALSE
- C: cleanup: DEFERRED (order exists in 11_CLEANUP…; do not run cleanup now)
- Secrets: NEVER commit (tokens, mesh secret, env files, *.db, backup zips with private state)

══════════════════════════════════════
FILES TO CREATE / UPDATE IN REPO
══════════════════════════════════════
Work in the primary checkout you use (Documents\Codex\...\seven-ai or equivalent). Prefer editing tracked paths under the repo root.

1) docs/orchestration/
   - Copy/sync full pack from C:\Users\USER-PC\seven-ai-audit\docs\orchestration\
   - Ensure 00_RESUME is current (merge any newer facts you verify)
   - Ensure 05_WORK_LOG has a final "docs sync" entry after you finish

2) docs/deploy-evidence/
   - Copy all non-secret markdown from D:\SevenLocal\deploy-evidence\
   - Do not copy secrets, env files, or database dumps

3) docs/CONTINUATION_PROMPT.md  **(CREATE — single paste for next session)**
   Must include:
   - Mission one paragraph
   - Absolute bans (sentience, rewrite, remote L4 mesh, secret commits)
   - Current SHA, branch, version, local+Peanut paths
   - What is DONE (bullet list)
   - What is NEXT default (C: cleanup via 11_) and optional (owner browser smoke)
   - Roles: owner / implementer / Grok police
   - Exact "read these files first" list with paths
   - Required report format for implementer
   - Paste-ready blocks: (a) for Codex implementer (b) for Grok police

4) README.md
   - Version/branch tip language matches 4.6.0 / research branch reality if README claims wrong model/tool counts
   - Point to docs/CONTINUATION_PROMPT.md and docs/orchestration/00_RESUME…
   - No "sentient" marketing; GitHub description is separate if you cannot change it

5) HANDOFF.md and HANDOFF_PROMPT.md
   - Replace stale "39 tools / tier core / untracked v4" lies with current truth OR mark obsolete and point to CONTINUATION_PROMPT.md + 00_RESUME
   - Prefer short + accurate over long fiction

6) SEVEN_REAL.md (if present)
   - Align default model/tier with config.py on this branch
   - Point to talk/daemon and D:\SevenLocal as owner runtime if accurate

7) docs/KNOWN_LIMITATIONS.md
   - Add/confirm: not sentient; mesh not remote L4; Peanut small model tier; cleanup deferred; browser smoke optional unproven if still true

8) CHANGELOG.md
   - Short entries for: mesh messaging, ca671b4 continuity, 1397d04 finish wave, web-venv repair (ops), docs pack

9) AGENTS.md
   - Default model/tier from actual config.py
   - Point to orchestration + continuation prompt
   - Keep no-random-choice / no fake progress rules (now largely real)

10) .gitignore
   - Ensure venv, web-venv, *.db, api.token, *.secret, backup zips, .seven data are ignored

══════════════════════════════════════
GIT
══════════════════════════════════════
- Commit message e.g.: docs: sync orchestration, deploy evidence, continuation prompt
- Push origin codex/seven-completion
- Report exact commit SHA
- If push blocked, leave commit local and report

══════════════════════════════════════
DO NOT
══════════════════════════════════════
- Deploy or restart production
- Run C: cleanup deletes
- Commit secrets or live databases
- Claim sentience or complete
- Full product rewrite
- "Fix" code unless a doc link is broken and fix is one-line path only

══════════════════════════════════════
REPORT FORMAT
══════════════════════════════════════
## Done
## Files created/updated
## Git commit SHA (local and remote)
## Continuation prompt path
## Still stale / skipped
## Next 3 (for owner tomorrow)
## Claims check
CONTINUATION READY → path → yes/no
SECRETS COMMITTED → must be no
PRODUCTION CHANGED → must be no

BEGIN. Prefer writing files over planning essays.
```

---

## Short whip (if Codex stalls)

```
Docs only. Read 00_RESUME. Create docs/CONTINUATION_PROMPT.md, sync docs/orchestration + deploy-evidence md, fix HANDOFF lies, push codex/seven-completion. No deploy, no cleanup, no secrets. Report SHA.
```

---

## After Codex finishes — paste to Grok

```
Police the docs sync commit. Confirm CONTINUATION_PROMPT + orchestration in repo, no secrets, no production change. Grade REAL/MIXED/BULLSHIT.
[paste Codex report + commit SHA]
```

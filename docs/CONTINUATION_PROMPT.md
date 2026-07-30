# Seven continuation prompt — canonical cold start

This is the one file a new human or AI session needs first. It records the
verified deployment boundary, operating rules, remaining work, and paste-ready
instructions. Supporting evidence is linked; do not ask the owner to reconstruct
the history from chat.

## Mission

Continue Seven as a real, local-first companion agent that boots, uses audited
tools, remembers outcomes across restart, acts without fake progress, and keeps
mesh data-only. Preserve proven behavior and report uncertainty honestly.

## Absolute bans

- Do not claim sentience, consciousness, humanity, or a complete Seven.
- Do not perform a full rewrite or revive v3 emotion/dream/sentience theater.
- Do not expand mesh into remote L4 execution or automatic execution of
  received messages.
- Do not commit credentials, tokens, secret environment files, mesh secrets,
  venvs, databases, private runtime state, or backup archives.
- Do not deploy, restart production, clean disks, or delete files without
  explicit owner authorization for that operation.
- Do not overwrite unexplained working-tree drift.
- Do not report success without exact evidence for the claimed result.

## Current truth

| Item | Verified state |
|---|---|
| Version | `4.6.0` |
| Working branch | `codex/seven-completion` |
| Deployed core SHA, local + Peanut | `1397d04f4993d143ddc413a7820f3432bc08a55e` |
| Local release | `D:\SevenLocal\releases\seven-4.6.0-1397d04` |
| Local active venv | `D:\SevenLocal\venv` junction to the release venv |
| Local API | `http://127.0.0.1:18765` |
| Peanut release | `/opt/seven` → `/opt/seven-4.6.0-1397d04` |
| Peanut gateway | release-local `web-venv`; two systemd restarts proven |
| Mesh | authenticated data/presence/relay messaging only |
| Sentience / complete | false / false |
| Cleanup | deferred; order documented but not executed |

The branch may move beyond `1397d04` for documentation-only commits. That does
not change the deployed core SHA. Verify both Git and production instead of
assuming they are identical.

Source defaults in `seven/config.py` are Ollama, `qwen2.5:7b`,
`llama3.2-vision`, tool tier `full`, schema mode `native`, and API port `7777`.
The verified local install manifest overrides vision to `moondream:latest`,
schema mode to `dispatcher`, and API port to `18765`.

## Done and accepted REAL

- Secure Seven Mesh messaging and presence, with no remote tool execution.
- Continuity lineage `ca671b4`: tool success/failure is classified honestly,
  stored as `tool:<name>` belief, survives Memory reopen, and re-enters context.
- Finish wave `1397d04`:
  - future due dates do not force work; due/past dates can;
  - observational-only tools do not advance non-survey plan steps;
  - goal progress uses linked plan fractions or explicit evidence, not tool
    counts.
- Exact `1397d04` deployed locally and on Peanut with verified backups,
  health, truthful tool success/failure, restart continuity, and rollback.
- Peanut `seven-web` release-local venv repaired and proven through two
  controlled systemd restarts without changing core SHA.
- Non-secret deployment evidence and orchestration documents preserved in Git.

## Evidence index

- [Resume snapshot](orchestration/00_RESUME_AFTER_POWER_FAILURE.md)
- [Work log](orchestration/05_WORK_LOG.md)
- [Functional-alive acceptance](orchestration/08_MAKE_SEVEN_ALIVE.md)
- [Local 1397d04 deployment](deploy-evidence/SEVEN_LOCAL_DEPLOY_1397D04_20260730T211032SAST.md)
- [Peanut 1397d04 deployment](deploy-evidence/SEVEN_PEANUT_DEPLOY_1397D04_20260730T211032SAST.md)
- [Peanut gateway venv repair](deploy-evidence/SEVEN_PEANUT_WEB_VENV_REPAIR_1397D04_20260730T212808SAST.md)

## Default next work

Only when the owner explicitly authorizes it:

1. Run the preservation-first C-drive cleanup order in
   `docs/orchestration/11_CLEANUP_AND_GIT_PRESERVE.md`.
2. Optionally run an owner-browser smoke test for login, conversation,
   microphone, and transcription.
3. Choose one evidence-backed research slice; do not invent a new campaign.

The cleanup document is an order, not proof that cleanup happened.

## Roles

| Role | Responsibility |
|---|---|
| Jan / owner | Sets priority and authorizes production, cleanup, and destructive actions |
| Codex / implementer | Makes scoped changes and supplies exact evidence |
| Grok / police | Grades REAL, MIXED, or BULLSHIT and rejects overclaims |

The implementer does not grade itself.

## Read these first

For a code or operations session, read in this order:

1. `docs/CONTINUATION_PROMPT.md`
2. `docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md`
3. `docs/orchestration/05_WORK_LOG.md`
4. `docs/orchestration/08_MAKE_SEVEN_ALIVE.md`
5. the order file for the explicitly authorized task
6. relevant files under `docs/deploy-evidence/`

Current host paths:

- repository documentation checkout:
  `C:\Users\USER-PC\seven-ai-audit`
- local runtime: `D:\SevenLocal`
- orchestration source:
  `C:\Users\USER-PC\seven-ai-audit\docs\orchestration`

The older checkout under
`C:\Users\USER-PC\Documents\Codex\2026-07-20\mortem-continues\seven-ai`
had unrelated uncommitted work during the documentation wave. Audit its status
before using it and do not discard that drift.

## Required implementer report

```text
## Done
## Evidence
## Unproven / still broken
## Next 3
## Claims check
SECRETS COMMITTED: no
PRODUCTION CHANGED: yes/no, with authorization and proof if yes
```

## Paste to Codex implementer

```text
Read docs/CONTINUATION_PROMPT.md first, then follow its read order.

You are the Seven implementer. Jan is owner; Grok is police.
Production core is Seven 4.6.0 at exact SHA
1397d04f4993d143ddc413a7820f3432bc08a55e locally and on Peanut.
The branch may have newer documentation-only commits.

Work only on the task the owner explicitly authorizes. Inspect hidden files,
Git drift, runtime evidence, and rollback state before editing. Preserve
unexplained changes. Never claim sentience/completeness, rewrite Seven, expand
mesh to remote L4, commit secrets/private state, deploy, clean, or delete
without explicit authority.

Report Done / Evidence / Unproven / Next 3 and the claims check.
```

## Paste to Grok police

```text
Read docs/CONTINUATION_PROMPT.md and
docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md.

You are police for Seven. Production core remains 4.6.0 at exact SHA
1397d04f4993d143ddc413a7820f3432bc08a55e locally and on Peanut.
Continuity, finish wave, mesh messaging, exact deploys, and Peanut web-venv
restart repair are accepted REAL within their evidence boundaries.

Reject sentience/completeness claims, remote-L4 mesh, secret commits,
production changes without proof, cleanup claims without deletion evidence,
and feature claims based only on compilation. Grade new work
REAL / MIXED / BULLSHIT and issue at most the next three orders.
```


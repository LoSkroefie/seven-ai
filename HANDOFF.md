# Seven 4.6.0 — verified handoff

This short handoff replaces the obsolete 4.4.0/39-tool document. The canonical
cold-start document is
[docs/CONTINUATION_PROMPT.md](docs/CONTINUATION_PROMPT.md). Read it first.

## Current verified state

| Item | Truth |
|---|---|
| Product | Seven 4.6.0 under `seven/` |
| Working branch | `codex/seven-completion` |
| Deployed core SHA | `1397d04f4993d143ddc413a7820f3432bc08a55e` |
| Local release | `D:\SevenLocal\releases\seven-4.6.0-1397d04` |
| Local active venv | `D:\SevenLocal\venv` junction to that release |
| Peanut release | `/opt/seven` → `/opt/seven-4.6.0-1397d04` |
| Mesh | Authenticated messages/presence only; no remote L4 |
| Sentience / complete | False / false |

Documentation-only commits may move the branch beyond `1397d04`; they do not
change the production core pin.

## What is proven

- Local and Peanut core deployments use the exact same accepted source SHA.
- Local API health reports `seven-real` 4.6.0.
- Real `get_system_info` succeeds and a deliberate `read_file` failure audits
  as failure.
- Tool outcomes create durable `tool:<name>` beliefs that re-enter context
  after restart.
- Future due dates are not treated as overdue; past due dates can force work.
- Observational tools do not falsely advance non-survey plan steps.
- Linked plan fractions/evidence replace tool-count percentage theater.
- Mesh relays authenticated data and never executes received messages as tools.
- Peanut's release-local `web-venv` was repaired and passed two controlled
  `seven-web` systemd restarts while core stayed pinned.

Evidence:

- [local 1397d04 deploy](docs/deploy-evidence/SEVEN_LOCAL_DEPLOY_1397D04_20260730T211032SAST.md)
- [Peanut 1397d04 deploy](docs/deploy-evidence/SEVEN_PEANUT_DEPLOY_1397D04_20260730T211032SAST.md)
- [Peanut gateway venv repair](docs/deploy-evidence/SEVEN_PEANUT_WEB_VENV_REPAIR_1397D04_20260730T212808SAST.md)

## Source defaults versus deployed profile

Source `seven/config.py` defaults:

- provider `ollama`;
- text model `qwen2.5:7b`;
- vision model `llama3.2-vision`;
- tool tier `full`;
- schema mode `native`;
- API port `7777`.

The verified local install manifest overrides vision to `moondream:latest`,
schema mode to `dispatcher`, and API port to `18765`. A host profile is not a
source default.

## Still unproven or deferred

- Sentience, consciousness, and a complete product are not claimed.
- The 1397d04 gateway repair did not retest browser login, microphone,
  transcription, or owner conversation behavior.
- Long-duration behavior is not guaranteed on every host.
- C-drive cleanup is deferred. The order exists in
  `docs/orchestration/11_CLEANUP_AND_GIT_PRESERVE.md`; it is not completion
  evidence.
- The older primary checkout under
  `Documents\Codex\2026-07-20\mortem-continues\seven-ai` contained unrelated
  uncommitted work during the documentation wave and was left untouched.

## Next default

Only when the owner authorizes it:

1. follow `docs/orchestration/11_CLEANUP_AND_GIT_PRESERVE.md`;
2. preserve non-secret artifacts before deleting anything;
3. optionally perform the owner-browser smoke test.

No feature work, rewrite, redeploy, remote-L4 mesh, or sentience claim is
implied.

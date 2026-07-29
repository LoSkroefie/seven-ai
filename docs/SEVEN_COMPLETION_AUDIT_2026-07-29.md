# Seven completion audit — 2026-07-29

This is the release-facing truth record for the final Seven completion pass.
It distinguishes code evidence, installed-runtime evidence, owner-device
verification, deliberate boundaries, and claims that software cannot prove.

## Preserved before-state

- Repository: `LoSkroefie/seven-ai`, branch `codex/seven-completion`.
- Audited starting commit: `2bef2ee6105a7051209fb1df8af4e86492eb29f7`.
- Hidden directories and files were inventoried before editing.
- The tracked-file before manifest SHA-256 is
  `4ABBA0ECB9E1702E9C8861B8F86D468E026C0BFC89C8E156810901E6B17C60F0`.
- Pre-existing owner edits in `deploy/peanut/README.md` and
  `docs/COMPLETION_LEDGER.md` were preserved and excluded from this release
  commit.
- `uv.lock` retained its exact before hash:
  `A80E3833608C62F8C05E7DA8264E43335CAA67A870BD740D73E4F4EB52223D34`.

## Implemented in this pass

### Setup and installation

- Added safe Windows and Unix isolated-environment installers.
- Added interactive and noninteractive setup, setup doctor, and dry-run modes.
- Added atomic non-secret settings with explicit environment precedence.
- Added Python, RAM, disk, Ollama, and installed-model diagnostics.
- Added explicit model pull and Windows Winget Ollama installation actions.
- Existing data, unknown settings, models, and source files are never removed.
- Corrupt saved settings now fail visibly during normal startup.
- Capture mode now distinguishes `off`, `webcam`, `screen`, and `both`; disabled
  screen/webcam tools remain known but cannot be exposed or executed.

### Runtime cognition and model lifecycle

- An API-owned Seven starts its heartbeat as soon as the listening socket is
  successfully bound; owner traffic is not required to wake cognition.
- A benchmarked active model survives restart when installed.
- A real `OLLAMA_MODEL` operator override wins.
- A setup-saved model is a default, not an operator override, and therefore
  cannot overwrite a later benchmarked activation.
- Persisted models without a passing benchmark fail closed with visible
  fallback evidence.
- Model benchmarks record and exercise the configured tool protocol.
- Vision never substitutes a loaded text-only model after a vision timeout.

### Owner web experience

- Browser speech is muted by default and cannot hold the UI in a false speaking
  state.
- Gateway origin and CSRF errors map to the actual production error codes.
- Server-sent-event and polling completion races share one terminal fetch.
- Audio recording negotiates supported codecs, stops after 60 seconds, and
  enforces an 8 MB client limit with deterministic cleanup.
- Camera snapshots validate and cap dimensions, handle missing canvas contexts
  and encoding failures, and enforce a 5 MB client limit.
- Browser-like JavaScript tests execute these state transitions.

### Operations and recovery

- Added a hardened, unprivileged, daily persistent systemd backup timer.
- Missing backup prerequisites fail visibly instead of silently skipping.
- Backup and restore commands explicitly target `/var/lib/seven`.
- Production activation remains an operator-supervised immutable-release
  switch with a previous-release rollback.

## Software validation

| Gate | Result |
|---|---|
| Full repository collection | 185 tests |
| Full repository suite | 183 passed, 2 dependency-optional skips |
| Browser-like JavaScript suite | 5 passed |
| Repository contract | passed; no production legacy imports or unresolved dispositions |
| Runtime truth gate | passed; 104 built-in tools registered |
| Compile gate | passed |
| Wheel isolated lifecycle | install, schema 5, API health, uninstall, and console removal passed |
| Wheel | `seven_ai-4.4.4-py3-none-any.whl` |
| Lock integrity | exact before SHA-256 retained |

The optional skips are `pypdf` document parsing and the external `mcp` package.
They are not silent passes and do not prove those optional integrations.

## Production status

Peanut was activated from an immutable release only after its archive,
installed package, configuration contracts, and rollback target were checked.

| Proof | Verified result |
|---|---|
| Active release | `/opt/seven-bf6cceb4396035f4-20260729T005909Z` |
| Deployed source commit | `bf6cceb4396035f4ee379c68df01f7935c4a0df7` |
| Source archive SHA-256 | `47002CDD938DCECBBD01E97DE2898D5D52D8C2A94A3FFAE98039801FED6E3B11` |
| Installed wheel SHA-256 | `B2FEEE211F5FD9C87038F8D6FDA153B10994FBB8762B41D6FE19FCED00A0E491` |
| Core service | active/running, PID `2265014`, zero systemd restarts |
| Web gateway | active/running, PID `2265015`, zero systemd restarts |
| Core loopback health | `seven-real` version `4.4.4`, healthy |
| Gateway loopback health | `seven-web` version `1.0.0`, healthy |
| Public health | `https://jvrsoftware.co.za/seven/health` returned healthy `seven-web` version `1.0.0` |
| Public owner page | `https://jvrsoftware.co.za/seven/` returned the Seven page |
| Public JavaScript SHA-256 | `0D62B90067A292A6F4161631C63D009C1A296F2F12D3162CCCA6E60A04A1EACC`, identical to the staged release |
| Authenticated current-release exchange | temporary authenticated gateway session; turn `11`; status `complete`; non-empty upstream reply; session destroyed after proof |
| Post-deploy backup | `/var/lib/seven/backups/seven-backup-20260729T010655238939Z.zip` |
| Backup SHA-256 | `2731D9BC2615A54C307B58C3714EE4ED0F635F36B14402590402B72B14BCC91F` |
| Backup verification | valid archive, 8 files, no verification errors, owner `seven:seven`, mode `0600` |
| Backup timer | active/waiting; next run `2026-07-30 00:10:46 SAST` |
| Rollback target retained | `/opt/seven-ui-20260729-eebc96882589` |

The core log proves environment-selected `qwen3:0.6b`, an available primary and
vision provider, heartbeat startup, and API binding. No traceback, exception,
fatal, failed, or error entry appeared in the core or gateway logs after this
activation. Peanut's host-local `ollama.service` is intentionally inactive in
this snapshot; the configured Ollama provider used by Seven nevertheless
completed authenticated turn 11. This record does not claim that the stopped
host-local service supplied that reply.

The existing SQLite cognition files retained their exact pre-deploy inodes
(`memory.db` `85593800`, `seven.db` `85593812`) across activation. The active
release switch therefore did not replace Seven's persistent cognition data.

## Truth boundaries

### Runtime-proven

- Local agent loop, persistent SQLite cognition state, audited tools, model
  benchmark/activation/rollback logic, authenticated owner text channel, and
  the existing visual owner experience.

### Software-tested, owner-device verification still required

- The new browser microphone recorder and camera snapshot flows. Automated
  browser-like tests prove their logic; the owner must still grant real browser
  permissions and test the named physical devices.
- Windows installer dry-run. An actual second-machine installation remains a
  separate owner acceptance test.
- Unix installer syntax and lifecycle require an actual Unix shell run; the
  local Windows WSL disk attachment was unavailable.

### Deliberately constrained

- Production source updates and model promotion are not callable as
  unrestricted model tools. An operator owns authenticity, backup, activation,
  and rollback.
- Ambient microphone/camera surveillance remains absent. Media capture is
  explicit.

### Not technically provable or not implemented

- Subjective sentience, consciousness, feelings, or awareness cannot be proven
  by this software.
- Foundation-model self-training or creating a new base LLM from normal chat is
  not implemented.
- Unlimited root freedom with guaranteed safety, authenticity, and rollback is
  contradictory and is not claimed.
- A 24-hour soak cannot be compressed into this release turn; service
  restart/resource evidence must accumulate over real elapsed time.

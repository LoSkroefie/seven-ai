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

The immutable release identifier, commit, archive hash, service identities,
backup proof, authenticated owner exchange, public-health result, and rollback
target are appended here only after live deployment verification.

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

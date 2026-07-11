# Seven Completion Ledger

This is the authoritative record for completing Seven without repeating abandoned rewrites, unsupported claims, or undocumented removals.

## Completion rules

1. A feature is not complete because a file, class, prompt, test double, or README claim exists.
2. Complete means a reachable production entry point, real implementation, persistent configuration where needed, visible failure behavior, adequate automated/manual evidence, and documentation.
3. Current production code lives under `seven/`. `_legacy/v3/` is recovery material, not a supported runtime.
4. Legacy files are classified before removal. Valuable behavior is reimplemented under current package boundaries.
5. Every material change records provenance, behavior, configuration, migration impact, validation, failure modes, and documentation.
6. Personality, affect, self-model and autonomous behavior are software systems, not proof of consciousness.

## Status vocabulary

- **Verified:** implemented and proven by listed evidence.
- **Implemented, incomplete evidence:** real code exists but validation or documentation is insufficient.
- **Partial:** useful implementation exists but promised behavior is missing.
- **Legacy-only:** exists only under `_legacy/v3/` and is unsupported.
- **Documented-only:** claimed or planned without a reachable implementation.
- **Missing:** no adequate implementation found.
- **Rejected:** intentionally excluded with rationale.

## Baseline

- Inventory date: 2026-07-11
- Baseline commit: `08d8b4f35d2693c695476b31b4488ee429195513`
- Working branch: `codex/complete-seven`
- Tracked files: 451
- Modern package files: 57
- Legacy files: 353
- Baseline test result: 33 passed, 2 dependency warnings, 101.3 seconds
- Missing baseline evidence: clean installation, login startup, soak, physical camera, multi-monitor, robotics, failure recovery, upgrade, uninstall, and cross-platform matrices.

## Initial capability matrix

| Capability | Baseline | Current source | Evidence/work required |
|---|---|---|---|
| Ollama inference | Implemented, incomplete evidence | `seven/brain/` | Live model matrix, outage/restart, malformed response, long context |
| Tool-calling loop | Verified at test level | `seven/agent/loop.py`, `seven/tools/registry.py` | Live Ollama tool rounds and soak |
| Shell/Python execution | Implemented, incomplete evidence | `seven/tools/shell.py`, `code_run.py` | Process trees, timeouts, Windows/Linux, environment policy |
| Filesystem tools | Implemented, incomplete evidence | `seven/tools/files.py` | Permissions, links, large files, concurrency, destructive cases |
| Screen/control | Implemented, incomplete evidence | `seven/tools/screen.py` | Windows, X11, Wayland, HiDPI, multi-monitor |
| Window/app control | Partial | `seven/tools/desktop_windows.py` | Launch/focus/close and compositor matrix |
| Camera/vision | Implemented, incomplete evidence | `seven/sensors/`, `seven/tools/vision.py` | Real/multiple/absent devices and contention |
| Voice | Implemented, incomplete evidence | `seven/voice/`, `seven/ui/talk.py` | Real devices, interruption, switching, login greeting |
| Memory | Verified integrity/export/backup level | `seven/memory/`, `seven/runtime/memory_ops.py` | Legacy migration, retention/purge and corruption drill remain |
| Living/free-will model | Implemented, incomplete evidence | `seven/mind/`, `seven/agent/autonomy.py` | Restart continuity, failure loops, long soak, real goal completion |
| API | Partial | `seven/ui/api_server.py` | Authentication, limits, lifecycle, concurrency, client guide |
| Daemon | Partial | `seven/runtime/daemon.py` | Install/start/stop/restart, recovery, Linux service, log rotation |
| GUI/tray | Partial | `seven/ui/chat_gui.py`, `desktop.py` | Full flows, startup, accessibility, Linux packaging |
| Coding agents | Verified at command/lifecycle level | `seven/tools/coding_agent.py` | Live authenticated mutation workflows remain |
| Robotics | Verified at protocol/emulator level | `seven/embodiment/`, `robotics_bus.py`, `hardware/seven_robot/` | Physical Arduino/RPi/motor-driver matrix remains |
| Install/package | Partial | `pyproject.toml`, root scripts | Locked dependencies, clean install/uninstall/upgrade |
| Login startup/greeting | Verified at automated generation level | `seven/runtime/startup.py`, `seven/ui/talk.py` | Installed login tests and real audio remain |
| MCP | Legacy-only | `_legacy/v3/seven_mcp.py` | Port supported modern surface or reject |
| Conversation/action digest | Legacy-only | legacy memory/extensions | Privacy-aware port/migration or reject |
| Extensions | Verified native tool-plugin contract | `seven/extensions/manager.py` | Port selected scheduled/message legacy extensions individually |
| Backup/recovery | Verified at automated level | `seven/runtime/backup.py` | Clean installed-system drill and large real-data restore remain |
| Continual LoRA | Legacy-only/claim-heavy | legacy learning | Prove real pipeline/hardware or remove claim |

| Durable reminders | Verified at persistence/native-submission level | `seven/memory/store.py`, `seven/agent/loop.py`, `seven/runtime/notifications.py` | Visible installed-session matrix remains |

## Repository classification baseline

| Area | Count | Initial disposition |
|---|---:|---|
| `seven/` | 57 | Supported code; audit every module |
| `_legacy/` | 353 | Recovery archive; classify file-by-file before pruning |
| `docs/` | 19 | Reconcile and expand |
| `scripts/` | 3 | Audit as release/developer tools |
| `tests/` | 1 | Split and expand into unit/integration/system suites |

## Change record

### 2026-07-11 - completion work begins

- Established baseline commit and clean completion branch.
- Ran current suite: 33 passed.
- Found that `Tool.enabled=False` hid schemas but did not prevent direct registry execution.
- Found that the loopback REST API accepted unauthenticated autonomous instructions and used permissive CORS preflight.
- Enforced disabled tools and added persistent private API bearer authentication, a request-size limit and no-store responses.
- Added regression tests for disabled tools and API token/authorization behavior.
- Corrected daemon startup so the API is no longer forced on by an unconditional `or True`.
- Replaced the API's hard-coded old version with the package version.
- Corrected README model/tool-tier defaults and false completion/shipping language.

### 2026-07-11 - modern backup and recovery

- Inspected `_legacy/v3/extensions/auto_backup.py` and rejected direct reuse because it copied a live database, silently skipped files over 50 MB, provided no manifest verification and had no restore path.
- Added `seven/runtime/backup.py` with SQLite online backup, complete runtime-state collection, per-file sizes/SHA-256, ZIP CRC verification, retention and safe member validation.
- Added `--backup`, `--verify-backup` and guarded `--restore-backup` lifecycle commands.
- Restore verifies before writing, refuses while the recorded daemon runs and creates a pre-restore safety archive.
- A Windows test exposed an unclosed SQLite backup handle; fixed it with explicit connection closing.
- Evidence: 39 tests pass, including backup/verify/restore, tamper detection and invalid archive rejection.

### 2026-07-11 - cross-platform login startup

- Confirmed the existing Windows autostart shortcut launches silent daemon mode and therefore does not meet the requested login greeting behavior.
- Added supported per-user startup install/status/remove commands for Windows Startup, Linux XDG autostart and macOS LaunchAgents.
- Default startup launches `--talk`; an explicit quiet startup is available.
- Documented greeting behavior, degraded-model fallback and migration status of the legacy PowerShell script.
- Evidence: 42 tests pass; startup artifact generation/removal is verified for Windows, Linux and macOS paths. Installed login/audio verification remains pending.

### 2026-07-11 - legacy symbol inventory and recovery triage

- Parsed all 216 legacy Python modules successfully; recorded hashes, sizes, line counts, classes, functions and imports in `LEGACY_SYMBOL_INVENTORY.csv`.
- Added `LEGACY_RECOVERY_MATRIX.md` separating core ports, deferred integrations, archive candidates and evidence required before removal.
- Prioritized conversation/action extraction, durable scheduling, Ollama lifecycle, modern MCP/plugins, robotics and key productivity integrations after backup/startup foundations.

### 2026-07-11 - durable reminder recovery

- Inspected the legacy APScheduler and smart reminder implementations. The former registered many jobs against optional/nonexistent attributes; the latter stored reminders only in memory using `threading.Timer`.
- Extended the current SQLite task schema through idempotent column migration for reminder delivery state/attempts.
- Added restart-safe due-task selection with timezone-aware ISO parsing.
- Heartbeat now prioritizes due reminders and marks them delivered only after a real output callback succeeds; silent daemon mode retains them pending.
- Documented the deliberate limitation that native background notifications are not yet complete.
- Evidence: 45 tests pass, including persistence across `Memory` reopen, invalid timestamp handling and callback-gated delivery.

### 2026-07-11 - audit credential redaction

- Confirmed tool arguments and result previews were persisted verbatim and could retain credentials indefinitely.
- Added recursive key-based and text-pattern redaction before audit persistence without changing the real arguments/results used during execution.
- Documented coverage, limitations and the fact that historical rows are not silently rewritten.
- Evidence: 48 tests pass, including nested authorization/API-key redaction, result-pattern redaction and preservation of non-secret context.

### 2026-07-11 - Ollama lifecycle recovery

- Inspected the legacy Ollama manager and the modern brain/model-selection code.
- Added eight audited local API tools: status, list, show, pull, copy, delete, load and unload.
- Pull consumes the real streaming response and reports the final server state; long operations use a separately configurable timeout.
- The manager keeps Ollama authoritative rather than duplicating model state.
- Evidence: 52 tests pass for request contracts, streamed pull parsing, mutation payloads and visible offline errors.
- Live evidence on Ollama 0.31.2: status reported seven installed models; list/show succeeded; `qwen2.5:7b` loaded on GPU and unloaded successfully; `ollama ps` returned empty after unload.
- Pull/copy/delete were not executed live because they mutate large user-owned model state; their HTTP contracts are tested.

### 2026-07-11 - wheel packaging and clean lifecycle

- Built the baseline wheel and found all authored identity Markdown files were omitted, causing installed Seven copies to build an empty identity block.
- Added explicit package data for `SOUL.md`, `IDENTITY.md`, `USER.md` and `TOOLS.md`.
- Aligned runtime/package version at `4.3.0`, corrected stale preferred-model identity text and declared Playwright in a browser optional dependency group.
- Added a deterministic wheel verifier for required assets, metadata and console entry point.
- Evidence: 54 tests pass; wheel `seven_ai-4.3.0-py3-none-any.whl` verified with SHA-256 `cd9a8c9ce27443d4158209deafca2ef7573a96cac4d2cf8d04e9e04f1fc1a4b5`.
- Clean Windows Python 3.13 virtual environment: core dependencies installed, all four identity files loaded (1,651-character identity block), `seven --help` ran, package uninstalled and `importlib` confirmed no remaining `seven` package.
- Optional dependency groups and their clean installed behavior still require separate release-matrix validation.

### 2026-07-11 - current-package CI replacement

- Found the baseline GitHub Actions workflow installed a missing root `requirements-stable.txt` and targeted archived `core`, `integrations` and `utils` paths, so it could not validate the modern package.
- Replaced CI with Python 3.11/3.12/3.13 Ubuntu tests and coverage, compile checks, deterministic inventory drift gates and a Windows Python 3.13 wheel build/install/identity/uninstall lifecycle.
- Added `pytest-cov` to the declared development extra and documented every CI gate.
- Local simulation: 54 tests pass and current `seven/` line coverage is 44%. This is recorded as a baseline, not misrepresented as release-grade coverage; core loop, free will, planner, daemon, UI, voice and hardware tools need substantial added coverage.

#### First hosted CI result and correction

- Windows wheel lifecycle passed completely on the first new workflow run.
- Ubuntu exposed that unconstrained `opencv-python>=4.8` selected 5.x, which lacks the cascade API used by presence detection; constrained supported OpenCV to `>=4.8,<5`.
- Inventory drift gate exposed CRLF/LF-dependent hashes and self-referential generated CSV entries; normalized text to LF and excluded generated inventory outputs.
- Hosted GitHub Actions evidence: run `29138837214` passed all jobs at commit `862086f88402cd7b0337e97761782411d606cdf4`: deterministic inventories, Ubuntu Python 3.11/3.12/3.13 tests/coverage and Windows Python 3.13 wheel lifecycle.

### 2026-07-11 - robotics protocol truth and firmware

- Found disconnected robot actions were recorded only in volatile memory yet returned success and were described as queued.
- Replaced ambiguous success with explicit `not_sent`, `send_failed`, `sent_unacknowledged`, `acknowledged` and `rejected` states.
- Added bounded action parameters, serial flush/read acknowledgement, port listing and disconnect tools.
- Added an Arduino Uno-compatible reference firmware implementing the documented V1 protocol. Unsupported generic motor commands return an explicit firmware error until configured.
- Corrected README/runbook claims and documented the physical evidence boundary.
- Evidence: 57 tests pass; serial emulator covers disconnected, acknowledged, unacknowledged, parameter-bounded and unknown-action paths. Physical hardware remains pending.

### 2026-07-11 - owned process-tree lifecycle

- Confirmed shell and generated-Python timeouts could leave descendant processes running after Seven stopped waiting.
- Added a shared Windows/Linux tracked process runner using separate process groups/sessions and `psutil` descendant discovery.
- Timeout now terminates descendants and parent, waits, kills survivors and records affected PIDs while preserving captured output.
- Migrated `run_shell` and `run_python`; documented that this is lifecycle ownership, not sandboxing.
- Evidence: 59 tests pass. Integration test starts a parent/child process pair, times out the parent and proves the child never writes its delayed survival marker. Exit-code/stdout/stderr preservation also passes.

### 2026-07-11 - real coding-agent delegation

- Live-inspected installed interfaces: OpenCode 1.17.7, Codex CLI 0.140.0 and Claude Code 2.1.118; Aider absent.
- Replaced guessed/fallback invocations with explicit non-interactive commands and added the missing Aider tool.
- Codex now uses `exec` rather than accidentally opening an interactive UI; Windows PowerShell/cmd shims are launched through the correct host.
- Routed every agent through tracked descendant cleanup with structured exit/output/timeout evidence.
- Kept L4 unrestricted agent modes configurable through `SEVEN_CODING_AGENT_UNRESTRICTED` and documented legitimate authentication requirements.
- Evidence: 63 tests pass; live version/status discovery succeeds for all installed agents. No live mutation prompt was issued; authenticated mutation workflows remain a separate evidence gate.

### 2026-07-11 - memory integrity and portable export

- Added explicit SQLite schema version 1 after migration-safe initialization.
- Added integrity/foreign-key checks, table statistics and visible corrupt/missing database errors.
- Added portable ordered JSON export with format/schema/Seven versions, timestamp and source database SHA-256.
- Audit data is excluded by default; deliberate audit export contains the redacted persisted values.
- Documented the distinction between JSON interoperability/migration and verified ZIP disaster recovery.
- Evidence: 67 tests pass, covering schema/stats, default audit exclusion, redacted audit inclusion and invalid database reporting.

### 2026-07-11 - pre-commit inventory completeness correction

- Hosted runs after new-file commits showed inventory-only failures because the generator enumerated tracked files before new files were staged.
- Changed enumeration to include cached and non-ignored untracked paths, making the documented generate-before-stage workflow complete and deterministic.

### 2026-07-11 - native notification delivery

- Added Windows WinRT toast, Linux freedesktop `notify-send` and macOS Notification Center adapters.
- Added notification status/submission tools and passed Windows message content through environment variables rather than process arguments.
- Silent heartbeat reminders now submit natively and are marked delivered only when the backend accepts the request; unavailable/failed submissions remain due.
- Kept the evidence language truthful: successful state is `submitted`, never claimed viewed/read.
- Live status detected the Windows toast backend and PowerShell executable; no visible toast was emitted during unattended work.
- Evidence: 71 tests pass, covering unavailable, submitted, escaped/environment, failed-backend and reminder fallback behavior. Visible desktop-session testing remains.

### 2026-07-11 - native extension lifecycle

- Added a modern trusted Python extension directory and `register(registry)` contract.
- Added extension status/reload tools, exact ownership tracking, removal on reload, partial-load rollback and duplicate/core-tool replacement rejection.
- Rejected the legacy claim that an AST import scan makes native Python safe; documented that extensions execute with the logged-in user's full authority.
- Initial reload testing found stale bytecode reuse for same-size/rapid edits; changed loading to compile current UTF-8 source on every reload.
- Evidence: 75 tests pass, covering load, real behavior change on reload, file removal, partial failure rollback, visible errors and core-tool protection.
- Legacy scheduled/on-message extensions remain individual ports rather than being falsely marked compatible.

## Required release artifacts

- File inventory and legacy disposition table
- Truthful capability matrix with evidence
- Architecture, configuration and data-flow references
- Installation, startup, update and uninstall guides for supported systems
- Memory backup, migration, integrity and recovery guide
- Voice, vision, desktop-control, robotics and coding-agent guides
- API and supported MCP/plugin specifications
- Failure model, troubleshooting and operational recovery guide
- Test strategy, hardware matrix, soak reports and release evidence
- Dependency lock, provenance and license report
- Changelog, migration notes, known limitations and release checklist

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
| Memory | Implemented, incomplete evidence | `seven/memory/` | Backup, restore, migration, integrity, retention/export/purge |
| Living/free-will model | Implemented, incomplete evidence | `seven/mind/`, `seven/agent/autonomy.py` | Restart continuity, failure loops, long soak, real goal completion |
| API | Partial | `seven/ui/api_server.py` | Authentication, limits, lifecycle, concurrency, client guide |
| Daemon | Partial | `seven/runtime/daemon.py` | Install/start/stop/restart, recovery, Linux service, log rotation |
| GUI/tray | Partial | `seven/ui/chat_gui.py`, `desktop.py` | Full flows, startup, accessibility, Linux packaging |
| Coding agents | Partial | `seven/tools/coding_agent.py` | Detection, cancellation, workspace, output and live CLIs |
| Robotics | Partial | `seven/embodiment/`, `robotics_bus.py` | Protocol, discovery, reconnect, emulator and physical hardware |
| Install/package | Partial | `pyproject.toml`, root scripts | Locked dependencies, clean install/uninstall/upgrade |
| Login startup/greeting | Verified at automated generation level | `seven/runtime/startup.py`, `seven/ui/talk.py` | Installed login tests and real audio remain |
| MCP | Legacy-only | `_legacy/v3/seven_mcp.py` | Port supported modern surface or reject |
| Conversation/action digest | Legacy-only | legacy memory/extensions | Privacy-aware port/migration or reject |
| Extensions | Legacy-only | legacy loader/extensions | Modern contract, lifecycle and tests |
| Backup/recovery | Verified at automated level | `seven/runtime/backup.py` | Clean installed-system drill and large real-data restore remain |
| Continual LoRA | Legacy-only/claim-heavy | legacy learning | Prove real pipeline/hardware or remove claim |

| Durable reminders | Verified at automated persistence/delivery level | `seven/memory/store.py`, `seven/agent/loop.py` | Native background notification channel and installed-session evidence |

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

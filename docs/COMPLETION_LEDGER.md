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
| Memory | Verified lifecycle | integrity/export/backup/migration/retention/corruption tests | Unrelated legacy stores and long-soak scale remain |
| Living/free-will model | Implemented, incomplete evidence | `seven/mind/`, `seven/agent/autonomy.py` | Restart continuity, failure loops, long soak, real goal completion |
| API | Verified loopback lifecycle | real socket/concurrency tests, installed-wheel probe, `docs/API.md` | LAN/multi-user serving intentionally unsupported |
| Daemon | Verified owned foreground lifecycle | process integration tests, rotating logs, `docs/ALIVE.md` | OS supervisor and long-soak matrices remain |
| GUI/tray | Partial | `seven/ui/chat_gui.py`, `desktop.py` | Full flows, startup, accessibility, Linux packaging |
| Coding agents | Verified at command/lifecycle level | `seven/tools/coding_agent.py` | Live authenticated mutation workflows remain |
| Robotics | Verified at protocol/emulator level | `seven/embodiment/`, `robotics_bus.py`, `hardware/seven_robot/` | Physical Arduino/RPi/motor-driver matrix remains |
| Install/package | Verified core/selected-extras lifecycle | `pyproject.toml`, `uv.lock`, lifecycle verifier/CI | Voice/hardware system-package matrix remains |
| Login startup/greeting | Verified at automated generation level | `seven/runtime/startup.py`, `seven/ui/talk.py` | Installed login tests and real audio remain |
| MCP | Verified current stdio server | `seven/mcp_server.py`, protocol tests | Client interoperability matrix remains |
| Conversation/action digest | Verified local action-candidate lifecycle | SQLite schema/tests and `docs/ACTION_ITEMS.md` | Richer summary extraction remains |
| Structured document reading | Verified local extraction | format fixtures, live PDF, `docs/DOCUMENT_READING.md` | OCR/layout fidelity not claimed |
| Local music playback | Verified silent lifecycle | worker integration tests and `docs/MUSIC_PLAYBACK.md` | Audible hardware/codec matrix remains |
| SSH remote operations | Verified client policy/argv/failure lifecycle | OpenSSH probes, tests, `docs/SSH.md` | Authenticated remote integration target remains |
| GitHub repository reading | Verified read-only REST contracts/live public metadata | tests and `docs/GITHUB_READER.md` | Private-token integration remains user-configured |
| Extensions | Verified native tool-plugin contract | `seven/extensions/manager.py` | Port selected scheduled/message legacy extensions individually |
| Reusable/self-authored skills | Verified versioned workflow lifecycle | schema/run/rollback tests and `docs/SKILLS.md` | Host effects are not transactionally reversible |
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

### 2026-07-11 - current full-registry MCP server

- Replaced the unusable v3 MCP module, which imported obsolete configuration and memory packages, with an MCP SDK 1.x stdio server over the current registry.
- Publishes every active full-tier tool with its real JSON Schema and executes through existing validation, audit logging and credential redaction.
- Preserved the requested L4 authority: MCP does not sandbox or silently remove host-control tools. The launching MCP client/process access is the explicit consent boundary.
- Kept stdout exclusively for JSON-RPC and documented install, client configuration, privacy, optional hardware, and acknowledgement limits.
- Rejected legacy action-item/extension views whose storage contracts no longer exist; current memory, task and extension tools provide supported surfaces without compatibility theater.
- Evidence: protocol-independent adapter and SDK initialization/capability tests pass. Live client interoperability remains an explicit release-matrix item.

### 2026-07-11 - local conversation action recovery

- Replaced the legacy action digest's removed `ConversationMemory` dependency and drifting JSON fingerprint file with a schema-version-2 SQLite action lifecycle.
- Added conservative, deterministic extraction for explicit user commitments; it makes no cloud/local LLM call and guesses no due dates.
- Added exact normalized deduplication, pending/accepted/dismissed states, transactional task creation, source-message links and portable export coverage.
- Added three full-registry/MCP-visible review tools and `SEVEN_ACTION_CAPTURE=off|suggest` privacy control; default `suggest` never silently promotes a candidate to a task.
- Rejected false notification claims from the legacy extension. Only accepted tasks with real due dates enter the already supported reminder lifecycle.
- Evidence: parser precision fixtures, cross-restart deduplication, one-shot resolution, task linkage, current tool execution and schema-version migration tests pass.

### 2026-07-11 - bounded structured document recovery

- Replaced the misleading v3 “PDFs and Documents” surface with two current tools covering explicitly enumerated text/data/PDF/Office formats.
- Added standard-library DOCX, XLSX and PPTX text/value extraction plus declared optional `pypdf` support; extraction is local and separate from LLM reasoning.
- Added 50 MiB input, 200 MiB expanded-archive and 200,000-character output bounds, unsafe archive path rejection and visible truncation metadata.
- Documented that this is not OCR, Office rendering, formula recalculation, macro execution, or proof that image-only PDFs contain text.
- Evidence: generated DOCX/XLSX/PPTX/CSV/JSON/text fixtures cover content/order/metadata/errors/truncation. Live local `pypdf` 6.14.2 read a generated one-page PDF and reported one actual page.

### 2026-07-11 - owned local music lifecycle

- Separated real local playback from the v3 YouTube downloader/browser fallback, which could return success without playing audio.
- Added a preferred separately owned pygame worker with acknowledged play/pause/resume/stop/finish/error state and an ffplay play/stop fallback with explicit pause limitations.
- Stop targets only Seven's tracked playback process tree; normal exit cleanup and command-line/control-path-verified orphan recovery cover restart lifecycle. Missing files, unsupported extensions, unavailable backends, codec failures and dead-on-launch processes are not success.
- No online search, download, audible-speaker, playlist, DRM or OS media-session claims were retained without evidence.
- Evidence: silent WAV integration using SDL's dummy audio driver proves worker start, PID, pause, resume, clean stop and exit; failure/idle paths are unit tested. Live host status detects pygame and ffplay, but no unattended audible playback was emitted.

### 2026-07-11 - strict OpenSSH remote operations

- Rejected the v3 Paramiko manager's unknown-host auto-acceptance, reversible password scheme, lossy persisted profiles and bypassable command blocklist.
- Added real noninteractive OpenSSH command execution and SFTP-mode upload/download with agent/identity authentication only and strict existing host-key verification.
- Added bounded ports/timeouts/output, explicit exit/timeout/truncation evidence, input validation, local file preconditions and complete local client process-tree cleanup.
- Preserved requested L4 authority without claiming substring filtering is a remote security boundary; remote account/sudo/SSH policy remains authoritative.
- Evidence: argv-contract tests prove strict/batch/password-disabled options and argument separation; transfer direction/preconditions and timeout termination evidence pass. Live Windows OpenSSH 9.5 policy expansion reports batch mode yes, password authentication no and strict host checking true; a loopback closed-port probe returned real exit 255 without prompting. Authenticated remote mutation was not performed unattended.

### 2026-07-11 - bounded read-only GitHub recovery

- Recovered repository metadata, directory/file content, commits and issue/PR reads against the current GitHub REST version with one-page/output bounds.
- Added environment-only optional token handling, fixed API origin, slug/path validation, actual HTTP/rate-limit envelopes and distinct transport/API errors.
- Rejected the v3 module's bytes-divided-by-40 “line estimate,” comparative marketing, recursive hidden request multiplication and failure-to-empty-result collapse.
- Added no GitHub write operations or token persistence; private access depends on an explicitly supplied fine-grained token.
- Evidence: HTTP contract tests cover headers without disclosure, metadata, base64/newline decoding, bounds, issue/PR distinction, validation, rate limiting and offline errors. Live unauthenticated GitHub API read of `LoSkroefie/seven-ai` returned HTTP 200, Apache-2.0, Python, public visibility and rate-limit 59/60 at verification time.

### 2026-07-11 - reproducible install, upgrade and uninstall lifecycle

- Made `pyproject.toml` the sole dependency declaration and reduced `requirements-real.txt` to a compatibility redirect instead of a drifting duplicate list.
- Added a universal `uv.lock`, locked-sync documentation and a hosted lock-drift gate pinned to the verifier version.
- Advanced the candidate to 4.4.0 and made wheel verification read the expected project version rather than embedding another version constant.
- Added a disposable-venv lifecycle verifier covering metadata/runtime agreement, four identity assets, SQLite schema, installed CLI, `pip check`, optional extras, uninstall, console-script removal and import absence.
- Performed a real Windows upgrade drill from a wheel built directly from baseline commit `08d8b4f` (metadata 4.3.0, runtime `4.3.0-complete`, schema 0, missing packaged identity) to candidate 4.4.0 (matching runtime/metadata, schema 2, all identity assets), followed by clean uninstall.
- Performed a separate clean Windows install/uninstall with `mcp,documents,music,robotics,tray,browser`; dependency check, CLI and removal all passed. Browser engine binaries are intentionally a separate Playwright install step.
- CI now repeats clean core lifecycle on Windows and the selected optional-integration lifecycle on Ubuntu. Voice/microphone/Whisper and physical devices retain explicit platform evidence gates rather than being hidden in an ambiguous “all passed” claim.

### 2026-07-11 - owned daemon lifecycle and rotating logs

- Replaced plain PID integers and `pid_exists` checks with an atomic JSON lease containing PID, process birth time, start time and version.
- Status, duplicate rejection and stop now require matching birth time plus a Seven `--daemon` command line; legacy, corrupt, reused or unrelated PID records are removed without signaling that process.
- Stop is idempotent, requests graceful termination, waits, falls back to owned process-tree termination, and preserves the lease if the daemon remains alive. Added verified foreground restart semantics.
- Agent-construction failure releases the lease, and normal shutdown closes agent/API state before removing it.
- Replaced unbounded `FileHandler` logging with configurable 5 MiB/five-backup rotation.
- Found the shared process helper built `[descendants, parent]` but reversed it before termination, contradicting its descendants-first contract. Corrected the order and added an explicit ordering regression test across all shared users.
- Evidence: real subprocess integration proves atomic ownership, duplicate refusal, running status, termination and lease removal; a current-process unowned record proves no signal is sent; log rotation creates bounded backups. OS supervisor installation and long-duration autonomy/model soak remain separate gates.

### 2026-07-11 - bounded loopback API lifecycle

- Replaced process-global agent/lock state with per-server ownership, lazy initialization, bounded admission and clean external-versus-owned agent shutdown.
- Enforced loopback-only binding, strong/atomic token creation, configurable body/message/concurrency/socket bounds and fail-fast `503` overload behavior.
- Added strict JSON object/content-length/content-type handling, explicit 400/411/413/415/405 responses, no CORS, security/cache headers and generic 500 responses that do not disclose internal exception text.
- Background servers now retain/join their thread, close the listener and wait boundedly for active requests. GUI and daemon modes invoke this lifecycle; `--api-only` reports bind/config failure and exits nonzero.
- Evidence: real loopback socket tests cover health, both token headers, status/tools/chat, malformed and bounded inputs, unsupported methods, concurrency overload, token races, internal failure, lazy ownership, active port conflict, clean same-port restart and shutdown. The isolated wheel lifecycle also binds the installed server to an ephemeral port, verifies `/health`, and closes it without constructing an Ollama agent. Hosted Linux exposed the `TIME_WAIT` restart distinction; Windows then proved that unconditional reuse weakened active-listener exclusivity. The final contract enables reuse only on POSIX and retains Windows-exclusive binding, with both behaviors tested on their native runners.

### 2026-07-11 - legacy memory migration, retention and corruption recovery

- Added schema version 3 with legacy-import provenance and action-source fields.
- Added a read-only v3 conversation SQLite importer with integrity/schema checks, SHA-256 run identity, dry-run scratch migration, exact message deduplication, role/timestamp/provenance preservation, searchable summary facts and pending action-source recovery.
- Apply backs up before migrating/changing an existing target and records completed source hashes; repeated apply is a visible no-op. The legacy source hash is proved unchanged.
- Added explicit dry-run-first retention over named ephemeral scopes. Apply refuses missing/corrupt targets, verifies a pre-change backup, then deletes selected UTC-aged rows transactionally; durable facts/goals/open tasks/notes/skills/preferences remain out of scope.
- Found that restore could not recover a corrupt live database because its mandatory safety backup tried SQLite online backup first. Added a verified byte-preserving `forensic-raw-1` fallback with explicit consistency warning.
- Evidence: generated v3 databases prove mapping, malformed action handling, intra-source/existing deduplication, provenance, source immutability, backup and idempotence. Retention tests prove byte-identical dry-run, selective deletion and backup. A real SQLite corruption drill detects failure, verifies the forensic snapshot, restores a good archive and reads the original fact.

### 2026-07-11 - versioned validated skill workflows

- Replaced destructive skill overwrites with schema-v4 immutable revisions, current-version pointers, provenance and bounded success/failure run records.
- Added strict 1–50-step structural validation, active-tool preflight, argument-object enforcement, unsupported-placeholder/credential-key rejection and recursive `run_skill` prevention. Memory-level validation also covers planner/internal saves.
- Identical saves are visible no-ops; rollback validates an old revision and records its content as a new revision rather than rewriting history.
- Execution stops on failure unless explicitly configured to continue, while the overall run remains failed. Run records retain tool/boolean status only; detailed output stays in the redacted tool audit.
- Rejected the legacy self-scripting pattern scanner as a sandbox/security boundary and reused the current owned shell/Python/coding-agent tools rather than creating a duplicate subprocess path.
- Evidence: tests prove immutable v1/v2 content, no-op save, v1-to-new-v3 rollback, unknown/placeholder/recursive rejection, successful counts, fail-fast behavior, explicit continue behavior, failure counts and absence of secret tool output from skill-run persistence.

### 2026-07-13 - robotics claim and recovery-matrix correction

- Removed the last fallback phrase claiming an unavailable robot action was "queued conceptually"; no queue existed and the action is now explicitly reported as not sent.
- Added a wrapper-level regression test proving an absent backend returns an error containing `not sent` and never `queued`.
- Reconciled the legacy recovery matrix with already verified reminder, Ollama and robotics implementations so it no longer lists completed recovery work as missing.

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

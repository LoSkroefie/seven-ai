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
| Login startup/greeting | Partial/legacy-only | root Windows scripts, UI | Windows and Linux login lifecycle and speech |
| MCP | Legacy-only | `_legacy/v3/seven_mcp.py` | Port supported modern surface or reject |
| Conversation/action digest | Legacy-only | legacy memory/extensions | Privacy-aware port/migration or reject |
| Extensions | Legacy-only | legacy loader/extensions | Modern contract, lifecycle and tests |
| Backup/recovery | Legacy-only/partial | legacy backup/current DB | Supported integrity, backup, restore and disaster recovery |
| Continual LoRA | Legacy-only/claim-heavy | legacy learning | Prove real pipeline/hardware or remove claim |

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

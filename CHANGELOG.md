# Changelog


## 4.5.2 — conversational action follow-through

- Rejects model replies that promise a future action without issuing an
  audited tool call in the same turn.
- Appends concise success/failure evidence after every model-directed tool
  action instead of silently ending after execution.
- Grounds work-status and formatter questions in durable goals, plans, and the
  tool audit; Black can no longer be claimed when only autopep8 failed.
- Suppresses repeated offline intention announcements and no longer describes
  failed autonomous work as generic progress.

## 4.5.1 — desktop companion visual repair

- Replaced the magenta-fringed pose sheet with eight clean, identity-consistent
  Seven poses produced from the canonical portrait.
- Rebuilt the borderless widget around a compact status card with live state,
  CPU/RAM meters, and a direct chat control.
- Added a display-safe binary alpha edge for Windows/Tk color-key transparency,
  eliminating the magenta halo verified in the previous live render.
## 4.4.3 — Peanut inference candidate

- Added a bounded compact prompt profile for constrained self-hosted models
  without changing the full desktop prompt.
- Replaced tier-limited dispatcher discovery with paged discovery and schema
  inspection across every enabled registered tool.
- Prioritized goals, plans, tasks and working memory while preserving source
  and confidence labels for remembered claims.
- Bounded model-facing history and tool results without discarding their
  durable database and audit records.
- Added an explicit Ollama context limit and a separate loopback Ollama service
  profile so Seven does not compete in Mortem's inference queue.

## 4.4.0 — release candidate

- Rebuilt Seven as the independent `seven-ai` package with CLI, GUI, talk, daemon, loopback API and MCP entry points.
- Added owned daemon/API/process lifecycles, rotating logs, bounded inputs/concurrency/timeouts and atomic state.
- Added durable memory, tasks/reminders, action candidates, backup/restore, v3 migration, retention and corruption recovery.
- Added truthful host tools for files, commands, desktop, vision, browser, notifications, coding agents, documents, music, OpenSSH, GitHub, Ollama and acknowledged serial robotics.
- Added versioned validated skills with immutable history, run evidence and rollback.
- Added universal locking, isolated wheel install/upgrade/uninstall verification, cross-platform CI and deterministic inventories.
- Quarantined v3 with final per-file dispositions; rejected random/template “sentience” and false success claims.

See `docs/COMPLETION_LEDGER.md` for detailed evidence.

## Migration from 4.3.x/v3

- Back up first, then install 4.4.0 using `docs/INSTALLATION.md`; current SQLite schema migration is transactional.
- A v3 conversation database is never used as the live store. Run the documented dry-run migration, inspect it, then apply explicitly.
- Old v3 launchers/config/plugins are unsupported and never imported. Reconfigure with the current CLI/environment/startup tooling.
- Models, coding CLIs, Playwright engines and hardware drivers remain separate installations.

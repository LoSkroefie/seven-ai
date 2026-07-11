# Legacy Recovery Matrix

The legacy tree contains 353 tracked files, including 216 Python modules. All 216 Python files parse successfully. `LEGACY_SYMBOL_INVENTORY.csv` records every legacy Python file's size, line count, SHA-256, classes, functions and top-level imports. `FILE_INVENTORY.csv` covers every tracked repository path.

This matrix is triage, not proof of completion. A port decision becomes final only after implementation, tests, migration and documentation are recorded in `COMPLETION_LEDGER.md`.

## Port first: core product capabilities

| Legacy source | Capability | Modern baseline | Decision |
|---|---|---|---|
| `extensions/auto_backup.py` | Scheduled data backup | No supported backup/restore | **Ported and superseded** by verified `seven/runtime/backup.py` |
| `extensions/greeting_manager.py` | Context-aware greeting | Talk mode has real model greeting | Keep modern behavior; reject random fallback phrases; complete login startup/audio evidence |
| `core/conversation_memory.py` + `extensions/action_item_digest.py` | Conversation summaries and extracted actions | Current messages plus transactional action candidates/tasks | **Action capture ported and superseded**; richer conversation summarization remains separate |
| `extensions/smart_reminders.py` + `integrations/timer_system.py` | Scheduled reminders/timers | Tasks have optional due dates; no durable scheduler contract | Port into modern SQLite scheduler and daemon |
| `integrations/calendar.py` | Calendar read/create | Missing | Port provider-neutral interface; credentials/config separated |
| `integrations/email_checker.py` | Mail checks | Missing | Port only after replacing plaintext credential storage |
| `integrations/ollama_manager.py` | Model lifecycle | Basic model selection/ping exists | Recover pull/list/unload/status operations with tests |
| `integrations/music_player.py` | Local playback | Missing | Port platform-neutral player controls where testable |
| `integrations/ssh_manager.py` | Remote command sessions | Missing | Port with host-key and credential handling documented |
| `integrations/github_reader.py` | Repository read workflows | Generic web/coding CLIs only | Port authenticated/unauthenticated read operations without token persistence in DB |
| `integrations/document_reader.py` | Structured document extraction | Generic text files only | Port by supported format with optional dependencies |
| `integrations/pdf_generator.py` | PDF creation | Missing | Evaluate against product need and dependencies before port |
| `integrations/translation.py` | Translation | LLM can translate conversationally | Prefer tool contract only if it adds deterministic/local value |
| `integrations/self_scripting.py` | Durable generated skills/scripts | Modern skill steps exist | Recover versioning, validation and rollback; do not revive unsafe pseudo-isolation claims |
| `seven_mcp.py` | MCP exposure | Current full registry over local stdio | **Ported and superseded** by `seven/mcp_server.py`; obsolete v3 storage views rejected |
| `utils/plugin_loader.py` + `extensions/` | Extension lifecycle | Trusted native `register(registry)` lifecycle | **Ported and superseded**; port valuable scheduled/message extensions individually |
| `integrations/robotics.py` | Rich serial robotics | Thin modern embodiment bus | Recover handshake, protocol validation, reconnect and device behavior |
| `extensions/ambient_listener.py` | Ambient conversation capture | Push-to-talk/continuous talk only | Port only as explicit opt-in with visible recording state and retention |

## Evaluate after core completion

| Legacy source | Reason for deferral |
|---|---|
| Telegram, WhatsApp, IRC clients | External services, credentials, rate limits and API drift require provider-specific live evidence |
| News/weather/quote extensions | Useful but not core; several rely on network APIs and random/template output |
| Habit, mood, motivation, journal, Pomodoro | Productive extensions after scheduler/plugin contract is real |
| API explorer/database manager | Broad authority and large surface; require narrower contracts and extensive tests |
| Web UI | Current desktop/CLI/talk surfaces take precedence; legacy Gradio surface is not production architecture |
| NEAT/evolution modules | Must prove user value and real integration; presence of algorithms alone is insufficient |
| Continual LoRA trainer | Hardware/dependency/data-governance validation required before any product claim |

## Archive candidates

- Versioned `SEVEN_AUDIT_*.md` files: preserve useful chronology in a consolidated history, but do not treat self-authored audits as current proof.
- Old distribution/install scripts: preserve until modern clean install, upgrade and uninstall are proven.
- `docs_old/` and `tests_old/`: retain as evidence until every behavior/test is mapped.
- Old GUIs, duplicate entry points and analysis scripts: archive after recovery mapping.
- Legacy identity files: compare against current `seven/identity/` before deduplication; never silently replace Seven's identity.

## Removal candidates requiring final evidence

- Generated package outputs, caches or local runtime data accidentally tracked.
- Duplicate audit reports whose unique evidence has been consolidated.
- Demonstration/example extensions not used as plugin fixtures.
- Superseded launchers after compatibility/migration testing.
- Any credential-bearing or personal runtime data; preserve schema/migration evidence without preserving secrets.

No deletion is authorized by this matrix alone. Final disposition is recorded per path in `FILE_INVENTORY.csv` after recovery review.

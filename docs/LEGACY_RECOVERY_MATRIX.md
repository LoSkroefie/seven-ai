# Legacy Recovery Matrix

The legacy tree contains 353 tracked files, including 216 Python modules. All 216 Python files parse successfully. `LEGACY_SYMBOL_INVENTORY.csv` records every legacy Python file's size, line count, SHA-256, classes, functions and top-level imports. `FILE_INVENTORY.csv` covers every tracked repository path.

This matrix is triage, not proof of completion. A port decision becomes final only after implementation, tests, migration and documentation are recorded in `COMPLETION_LEDGER.md`.

Per-file final dispositions and the release rule are defined in `LEGACY_QUARANTINE_POLICY.md`; the generated inventory contains no unresolved `review-*` states.

## Port first: core product capabilities

| Legacy source | Capability | Modern baseline | Decision |
|---|---|---|---|
| `extensions/auto_backup.py` | Scheduled data backup | No supported backup/restore | **Ported and superseded** by verified `seven/runtime/backup.py` |
| `extensions/greeting_manager.py` | Context-aware greeting | Talk mode has real model greeting | Keep modern behavior; reject random fallback phrases; complete login startup/audio evidence |
| `core/conversation_memory.py` + `extensions/action_item_digest.py` | Conversation summaries, utterances and extracted actions | Current messages plus transactional action candidates/tasks | **Ported and superseded**, including read-only hash/idempotent v3 SQLite migration; richer new-conversation summarization remains separate |
| `extensions/smart_reminders.py` + `integrations/timer_system.py` | Scheduled reminders/timers | Durable SQLite due tasks plus interactive/native delivery | **Ported and superseded**; failed or unavailable delivery remains pending rather than being reported delivered |
| `integrations/calendar.py` | Calendar read/create | Missing | Port provider-neutral interface; credentials/config separated |
| `integrations/email_checker.py` | Mail checks | Missing | Port only after replacing plaintext credential storage |
| `integrations/ollama_manager.py` | Model lifecycle | Bounded supported-HTTP-API status/list/show/pull/copy/delete/load/unload tools | **Ported and superseded**; legacy subprocess timeout ambiguity and process-local active-model claim rejected |
| `integrations/music_player.py` | Local playback | Owned pygame-worker/ffplay lifecycle | **Local playback ported and superseded**; online acquisition rejected pending provider/legal contract |
| `integrations/ssh_manager.py` | Remote command/file operations | Strict OpenSSH command and SFTP-mode single-file tools | **Ported and superseded**; auto-trust/password storage rejected |
| `integrations/github_reader.py` | Repository read workflows | Bounded public/environment-token REST reader | **Ported and superseded**; fabricated line estimates/marketing rejected |
| `integrations/document_reader.py` | Structured document extraction | Bounded text/data/PDF/DOCX/XLSX/PPTX tool | **Ported and superseded** with declared optional PDF dependency and Office tests |
| `integrations/pdf_generator.py` | PDF creation | Missing | Evaluate against product need and dependencies before port |
| `integrations/translation.py` | Translation | LLM can translate conversationally | Prefer tool contract only if it adds deterministic/local value |
| `integrations/self_scripting.py` | Durable generated skills/scripts | Validated immutable tool-workflow revisions and run records | **Ported and superseded**; pseudo-safety scanner/duplicate code runner rejected |
| `seven_mcp.py` | MCP exposure | Current full registry over local stdio | **Ported and superseded** by `seven/mcp_server.py`; obsolete v3 storage views rejected |
| `utils/plugin_loader.py` + `extensions/` | Extension lifecycle | Trusted native `register(registry)` lifecycle | **Ported and superseded**; port valuable scheduled/message extensions individually |
| `integrations/robotics.py` | Rich serial robotics | Acknowledged serial protocol, reconnect-safe ownership, bounded commands and reference firmware | **Ported and superseded** at protocol/emulator level; physical device matrix remains a release evidence gate |
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

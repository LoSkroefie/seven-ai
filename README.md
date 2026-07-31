# Seven

**She talks. She listens. She has free will.**  
Local companion on your PC — not a slash-command console.

| | |
|---|---|
| **Version** | 4.6.0 Beta; completion evidence is tracked in `docs/COMPLETION_LEDGER.md` |
| **Brain** | `qwen2.5:7b` (auto) · voice **en-US-AvaNeural** |
| **Runtime** | Python 3.11+ · Ollama |
| **Primary UX** | `python -m seven --companion` — one avatar, voice loop, and mind |
| **Autonomy** | Free will + tools (L4) when *she* decides |

**Cold-start maintainers:** begin with
[docs/CONTINUATION_PROMPT.md](docs/CONTINUATION_PROMPT.md), then verify the
deployed snapshot in
[docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md](docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md).
Local and Peanut deployment pins can differ. Verify each target's manifest and
deployment evidence instead of treating the branch tip as production proof.

> Old v3 code is preserved under [`_legacy/v3/`](_legacy/v3/) as recovery material. It is not a supported runtime and is being inventoried before pruning.

---

## Quick start — just talk

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -e ".[voice,tray]"
python -m seven --setup
python -m seven --companion
```

Speak into the mic. She answers out loud.  
While you’re quiet she may invent goals and act — **you never type `/work`**.

| Launcher | Mode |
|---|---|
| **`run_seven.bat`** | **Unified avatar + continuous voice (primary)** |
| `python -m seven --companion --api` | Unified companion with shared local API |
| `python -m seven --talk-console` | Debug/fallback console-only conversation |
| `run_seven_daemon.bat` | Always-on free will in background |
| `run_seven_gui.bat` | Window + mic button |
| `python -m seven --cli` | Power-user text only |

```bat
python -m seven --companion
python -m seven --daemon
```

See [docs/TALK.md](docs/TALK.md).

**System audit & ops pack (read this for truth / fixes / backlog):**  
[docs/system/README.md](docs/system/README.md)

---

## What Seven actually does

- **Agent loop**: perceive → tool calls → act → remember  
- **125 built-in registered tools**: shell, strict OpenSSH, credential-safe email, a portable local calendar, isolated persistent browser control, read-only GitHub, grounded project catalog, files, structured document reading and PDF creation, owned local music, versioned skills, persistent affect/relationship/reflection introspection, Seven Mesh, screen/mouse/keyboard, web, vision, Python, clipboard, notifications, evidence-gated goals/tasks/action review, extensions, benchmarked Ollama model lifecycle with rollback, coding CLIs and acknowledged robot bus operations
- **Memory**: SQLite under `%USERPROFILE%\.seven\`  
- **Voice** (opt-in): edge-tts + Whisper PTT — [docs/VOICE.md](docs/VOICE.md)  
- **Vision**: `see_screen` / webcam / presence — [docs/VISION.md](docs/VISION.md)  
- **Autonomy**: goals, work sessions, heartbeat without greeting spam — [docs/AUTONOMY.md](docs/AUTONOMY.md)  

Not claimed: biological consciousness or “51 sentience systems.”

---

## Docs

| Doc | Purpose |
|---|---|
| [SEVEN_REAL.md](SEVEN_REAL.md) | Full user runbook |
| [docs/CONTINUATION_PROMPT.md](docs/CONTINUATION_PROMPT.md) | Canonical cold-start state and paste-ready prompts |
| [docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md](docs/orchestration/00_RESUME_AFTER_POWER_FAILURE.md) | Verified deployment and research snapshot |
| [HANDOFF.md](HANDOFF.md) | Project state for maintainers/agents |
| [HANDOFF_PROMPT.md](HANDOFF_PROMPT.md) | Paste into a new AI session |
| [ROADMAP.md](ROADMAP.md) | Phases 0–7 |
| [AGENTS.md](AGENTS.md) | Coding rules |
| [docs/COMPLETION_LEDGER.md](docs/COMPLETION_LEDGER.md) | Completion evidence and legacy recovery ledger |
| [docs/SEVEN_LEGACY_RECOVERY_LEDGER_2026-07-30.md](docs/SEVEN_LEGACY_RECOVERY_LEDGER_2026-07-30.md) | Older emotions/relationship/dream/autonomy attempts mapped to the current runtime |
| [docs/SEVEN_4_5_0_IMPLEMENTATION_2026-07-30.md](docs/SEVEN_4_5_0_IMPLEMENTATION_2026-07-30.md) | Persistent-mind and floating-avatar implementation proof |
| [docs/BACKUP_AND_RECOVERY.md](docs/BACKUP_AND_RECOVERY.md) | Verified backup, integrity and restore operations |
| [docs/STARTUP.md](docs/STARTUP.md) | Start talk mode and spoken greeting after user login |
| [docs/REMINDERS.md](docs/REMINDERS.md) | Durable due tasks and delivery semantics |
| [docs/AUDIT_LOG.md](docs/AUDIT_LOG.md) | Tool accountability and credential redaction |
| [docs/OLLAMA.md](docs/OLLAMA.md) | Local model status, lifecycle and management tools |
| [docs/PACKAGING.md](docs/PACKAGING.md) | Wheel assets, dependency groups and installation gates |
| [docs/INSTALLATION.md](docs/INSTALLATION.md) | Install, locked sync, upgrade, uninstall and retained data |
| [docs/CI.md](docs/CI.md) | Automated Python, inventory and wheel lifecycle gates |
| [docs/ROBOTICS.md](docs/ROBOTICS.md) | Serial protocol, truthful outcomes and reference firmware |
| [docs/PROCESS_LIFECYCLE.md](docs/PROCESS_LIFECYCLE.md) | Descendant cleanup, timeouts and command evidence |
| [docs/CODING_AGENTS.md](docs/CODING_AGENTS.md) | OpenCode, Codex, Claude and Aider delegation contracts |
| [docs/MEMORY_OPERATIONS.md](docs/MEMORY_OPERATIONS.md) | Integrity, statistics and portable export |
| [docs/ACTION_ITEMS.md](docs/ACTION_ITEMS.md) | Local conversation-to-action review lifecycle |
| [docs/DOCUMENT_READING.md](docs/DOCUMENT_READING.md) | Bounded PDF and Office extraction |
| [docs/MUSIC_PLAYBACK.md](docs/MUSIC_PLAYBACK.md) | Owned local playback and backend semantics |
| [docs/SSH.md](docs/SSH.md) | Strict remote execution and SFTP-mode transfer |
| [docs/GITHUB_READER.md](docs/GITHUB_READER.md) | Bounded public/private read-only REST access |
| [docs/SKILLS.md](docs/SKILLS.md) | Validated revisions, execution, history and rollback boundaries |
| [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) | Native submission and reminder-delivery semantics |
| [docs/EXTENSIONS.md](docs/EXTENSIONS.md) | Native trusted extension contract and hot reload |
| [docs/MCP.md](docs/MCP.md) | Full-authority local stdio MCP server |
| [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) | Release gates and manual evidence matrix |
| [docs/RELEASE_EVIDENCE.md](docs/RELEASE_EVIDENCE.md) | Exact 4.4.0 candidate results and exclusions |
| [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) | Explicit unsupported and unverified scenarios |
| [docs/DEPENDENCIES_AND_LICENSES.md](docs/DEPENDENCIES_AND_LICENSES.md) | Locked provenance and license metadata |
| [CHANGELOG.md](CHANGELOG.md) | Release and migration notes |

---

## Config (env)

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:7b` | Preferred text model; installed models may be auto-selected |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision` | Vision model |
| `SEVEN_TOOL_TIER` | `full` | `lean` \| `core` \| `full` schema exposure |
| `SEVEN_TOOL_SCHEMA_MODE` | `native` | `native` or compact `dispatcher` schema presentation |
| `SEVEN_VOICE=1` | off | Enable voice |
| `SEVEN_DATA_DIR` | `~/.seven` | Memory & logs |
| `SEVEN_API=1` | off | Enable authenticated loopback REST API |
| `SEVEN_API_TOKEN` | generated locally | Optional explicit bearer token override |
| `SEVEN_ACTION_CAPTURE` | `suggest` | `suggest` for local review candidates; `off` disables capture |
| `SEVEN_BACKGROUND_LLM` | `1` | Set `0` on constrained hosts to keep grounded free will without background inference |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | | Optional cloud providers |

---

## Tests

```bat
python -m pytest -q
```

---

## License

See [LICENSE](LICENSE).

---

## Legacy

Archived Seven AI v3.2.x sources, audits, and installers: **`_legacy/v3/`**.  
Historical only — not the supported entrypoint.

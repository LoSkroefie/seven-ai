# Seven

**She talks. She listens. She has free will.**  
Local companion on your PC — not a slash-command console.

| | |
|---|---|
| **Version** | 4.3.0 Beta; completion evidence is tracked in `docs/COMPLETION_LEDGER.md` |
| **Brain** | `qwen2.5:7b` (auto) · voice **en-US-AvaNeural** |
| **Runtime** | Python 3.11+ · Ollama |
| **Primary UX** | `python -m seven --talk` / `run_seven.bat` |
| **Autonomy** | Free will + tools (L4) when *she* decides |

> Old v3 code is preserved under [`_legacy/v3/`](_legacy/v3/) as recovery material. It is not a supported runtime and is being inventoried before pruning.

---

## Quick start — just talk

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -r requirements-real.txt
ollama pull llama3.2

run_seven.bat
```

Speak into the mic. She answers out loud.  
While you’re quiet she may invent goals and act — **you never type `/work`**.

| Launcher | Mode |
|---|---|
| **`run_seven.bat`** | **Talk (primary)** |
| `run_seven_daemon.bat` | Always-on free will in background |
| `run_seven_gui.bat` | Window + mic button |
| `python -m seven --cli` | Power-user text only |

```bat
python -m seven --talk
python -m seven --daemon
```

See [docs/TALK.md](docs/TALK.md).

**System audit & ops pack (read this for truth / fixes / backlog):**  
[docs/system/README.md](docs/system/README.md)

---

## What Seven actually does

- **Agent loop**: perceive → tool calls → act → remember  
- **39 tools**: shell, files, screen/mouse/keyboard, web, vision, python, clipboard, goals/tasks, coding CLIs, robot bus  
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
| [HANDOFF.md](HANDOFF.md) | Project state for maintainers/agents |
| [HANDOFF_PROMPT.md](HANDOFF_PROMPT.md) | Paste into a new AI session |
| [ROADMAP.md](ROADMAP.md) | Phases 0–7 |
| [AGENTS.md](AGENTS.md) | Coding rules |
| [docs/COMPLETION_LEDGER.md](docs/COMPLETION_LEDGER.md) | Completion evidence and legacy recovery ledger |
| [docs/BACKUP_AND_RECOVERY.md](docs/BACKUP_AND_RECOVERY.md) | Verified backup, integrity and restore operations |

---

## Config (env)

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:7b` | Preferred text model; installed models may be auto-selected |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision` | Vision model |
| `SEVEN_TOOL_TIER` | `full` | `core` \| `full` schema exposure |
| `SEVEN_VOICE=1` | off | Enable voice |
| `SEVEN_DATA_DIR` | `~/.seven` | Memory & logs |
| `SEVEN_API=1` | off | Enable authenticated loopback REST API |
| `SEVEN_API_TOKEN` | generated locally | Optional explicit bearer token override |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | | Optional cloud providers |

---

## Tests

```bat
python -m pytest tests/test_seven_real.py -q
```

---

## License

See [LICENSE](LICENSE).

---

## Legacy

Archived Seven AI v3.2.x sources, audits, and installers: **`_legacy/v3/`**.  
Historical only — not the supported entrypoint.

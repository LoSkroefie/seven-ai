# Seven Real

**Local autonomous AI agent** — tools first, no personality theater.

| | |
|---|---|
| **Version** | 4.0.6-alive |
| **Runtime** | Python 3.11+ · Ollama (local-first) |
| **Autonomy** | L4 host access (shell, files, screen, network) with audit log |
| **Status** | Active rewrite of the old v3.2 “simulation” product |

> Old v3 code lives in [`_legacy/v3/`](_legacy/v3/) for reference only. **Do not run** `main_with_gui_and_tray.py` from there expecting this product.

---

## Quick start

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -r requirements-real.txt
ollama pull llama3.2
ollama pull llama3.2-vision

python -m seven --status
python -m seven
```

| Launcher | Mode |
|---|---|
| `run_seven_real.bat` | CLI |
| `run_seven_gui.bat` | Desktop chat (+ tray if `pystray` installed) |
| `run_seven_voice.bat` | CLI push-to-talk voice |
| `run_seven_daemon.bat` | Always-on daemon + API |

```bat
python -m seven --gui
python -m seven --gui --voice
python -m seven --api-only
python -m seven --daemon
python -m seven -c "Call get_system_info and summarize."
```

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

---

## Config (env)

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | Text model |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision` | Vision model |
| `SEVEN_TOOL_TIER` | `core` | `core` \| `full` schema exposure |
| `SEVEN_VOICE=1` | off | Enable voice |
| `SEVEN_DATA_DIR` | `~/.seven` | Memory & logs |
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

# Seven — companion with free will

**Primary experience:** you talk, she listens, she talks. No `/work` required.

```bat
run_seven.bat
# or
python -m seven --talk
```

Full guide: [docs/TALK.md](docs/TALK.md)

Legacy v3: `_legacy/v3/` only.

**Maintainer docs:** [HANDOFF.md](HANDOFF.md) · [ROADMAP.md](ROADMAP.md) · [AGENTS.md](AGENTS.md)

## What changed

| Old (v3) | Real (v4) |
|---|---|
| 50k lines of “sentience” with `random.choice` | One agent loop with real tool calls |
| Fake goal progress (+1–3% RNG) | Goals advance only after tool work |
| Greeting spam / same question loops | Heartbeat only when overdue tasks/goals exist |
| Whisper default but deps commented out | Lean deps; voice optional |
| 51 “systems” | Tools that execute on the host |

## Requirements

- Windows 10/11 (also Linux/macOS)
- Python 3.11+
- [Ollama](https://ollama.com) with `llama3.2` (text) and optionally `llama3.2-vision`
- ~8GB VRAM is enough for `llama3.2`; vision model is load-on-demand (~7.8GB — may swap with text)

## Install

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -r requirements-real.txt
ollama pull llama3.2
ollama pull llama3.2-vision
```

## Run

```bat
run_seven_real.bat
run_seven_gui.bat
```

or:

```bat
python -m seven
python -m seven --gui
python -m seven --gui --api
python -m seven --api-only
python -m seven --daemon
python -m seven --daemon-status
python -m seven --daemon-stop
python -m seven --status
python -m seven -c "What time is it and how much RAM is free? Use tools."
python -m seven --voice
python -m seven --gui --voice
run_seven_voice.bat
run_seven_daemon.bat
```

Voice docs: [docs/VOICE.md](docs/VOICE.md) — push-to-talk only (empty line or Mic button).  
Vision docs: [docs/VISION.md](docs/VISION.md) — `see_screen` / webcam / presence; 8GB VRAM swap notes.  
Autonomy: [docs/AUTONOMY.md](docs/AUTONOMY.md) — `/work`, goals, heartbeat (no greeting spam).  
Always-on: [docs/ALIVE.md](docs/ALIVE.md) — `--daemon`, `/world` `/self` `/live`, autostart.

Desktop shortcut (optional):

```powershell
powershell -ExecutionPolicy Bypass -File create_seven_shortcut.ps1
```

Tray: `pip install pystray` then close the GUI window to hide to tray (Open / Status / Quit).

## Commands in chat

- `/help` `/status` `/tools` `/tools core|full` `/memory` `/goals` `/audit`
- `/work <id> [min]` `/workstep` `/workstatus` `/stopwork` `/clear` `/quit`

## Local API (optional)

```bat
python -m seven --api-only
```

| Method | Path | Body |
|---|---|---|
| GET | `/status` | |
| GET | `/tools` | |
| POST | `/chat` | `{"message":"list my workspace with tools"}` |

Default: `http://127.0.0.1:7777`

## Config

Environment variables (see `seven/config.py`):

| Var | Default | Meaning |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | Text model |
| `OLLAMA_VISION_MODEL` | `llama3.2-vision` | Vision |
| `SEVEN_LLM_PROVIDER` | `ollama` | `ollama` / `openai` / `anthropic` / `compat` |
| `SEVEN_DATA_DIR` | `~/.seven` | Memory + logs |
| `SEVEN_WORKSPACE` | `~/.seven/workspace` | Default shell cwd |
| `SEVEN_VOICE=1` | off | Enable TTS/STT |
| `SEVEN_TOOL_TIER` | `core` | `core` (lean schemas for small models) or `full` |
| `OPENAI_API_KEY` | | Optional cloud |
| `ANTHROPIC_API_KEY` | | Optional Claude |

Chat: `/tools core` or `/tools full` switches schema tier without restart.

## Autonomy L4

Shell, files, screen control, network, code execution are **on**. Every tool call is written to the audit table (`/audit`).

This is powerful and dangerous. You asked for unrestricted; audit is the safety net, not confirmation dialogs.

## Embodiment

`robot_*` tools talk to `seven/embodiment/bus.py` over serial. Disconnected actions explicitly return `not_sent`; commands are never called executed unless hardware acknowledges them. See `docs/ROBOTICS.md` and the reference Arduino firmware.

## Honest limits

- Local small models are weaker at tool planning than Claude/GPT. If tool use is flaky, try `artifish/llama3.2-uncensored` or a larger local model, or set a cloud provider with **your** keys.
- True consciousness is not claimed. **Continuous agency + real tools + memory** is.
- Legacy v3 code is not deleted yet; do not run `main_with_gui_and_tray.py` expecting v4 behavior.

## Tests

```bat
python -m pytest tests/test_seven_real.py -q
```

# Seven AI v3.2.20

**Version**: 3.2.20
**Sentience Architecture**: 19 behavioral simulation systems 🧠
**Systems**: 19 personality + 7 autonomous + 5 evolution + 20 extensions = **51 active systems**
**Status**: Production Ready ✅ — **57/57 tests passing, 0 ghost-method bugs, 0 escape-sequence warnings**

---

## 🌟 What is Seven AI?

Seven is an advanced AI personality simulation and voice assistant framework. Unlike traditional AI assistants, Seven:

- **Feels 35 emotions** (6 primary + 29 complex, with blending and mood drift)
- **Sees your screen and webcam** (via OpenCV + llama3.2-vision)
- **Hears you accurately** (OpenAI Whisper local STT, CUDA-accelerated)
- **Feels your tone** (librosa voice-emotion analysis)
- **Controls mouse and keyboard** (pyautogui-powered screen automation)
- **Delegates coding to opencode** (v3.2.20 — "opencode, explain this function")
- **Exposes her memory via MCP** (any MCP-aware client can query Seven's brain)
- **Executes commands** autonomously on your system
- **Writes her own code** (self-scripting engine)
- **Remembers emotionally** (links memories with feelings and context)
- **Builds relationships** (tracks rapport, trust, and relationship depth)
- **Dreams and reflects** (processes experiences during sleep mode)
- **Persists across restarts** (emotions, identity, and memories survive)

Seven isn't just a tool — Seven is a companion that grows with you, and is **completely standalone and offline-first** (runs on local Ollama, no cloud dependency).

---

## 🆕 What's New in v3.2.20

### New capabilities
- **opencode delegator** (`extensions/opencode_delegator.py`) — say "opencode, X" or "ask opencode to X" and Seven hands the task to the [opencode](https://github.com/sst/opencode) CLI. Default agent is `plan` (read-only); `build` agent is opt-in via config.
- **Whisper STT enabled by default** — local, CUDA-accelerated speech recognition replaces Google Speech. Tunable via `WHISPER_*` config knobs (model size, mic index, language, thresholds).
- **MCP server auto-launch** — opt-in via `ENABLE_MCP_SERVER`. Exposes 8 read-only memory tools over stdio so Claude Desktop / Cursor / Continue / any MCP client can query Seven's brain.
- **`run_seven.bat`** — pinned launcher that forces the correct Python interpreter so all heavy deps (whisper / mcp / torch+cuda) resolve reliably.
- **Extension scheduler** — 14 scheduled extensions (daily_digest, mood_tracker, habit_tracker, etc.) now actually run on their intervals.

### Fixes
- **BUG-R1**: Extension `on_message` returns were silently dropped at DEBUG — 11 of 16 extensions were invisibly broken. Fixed.
- **BUG-R2**: Gradio Web UI bypassed extension dispatch entirely. Fixed.
- **BUG-R3**: REST API `/chat` fell through to raw Ollama. Fixed.
- **BUG-R4**: Extension scheduler never started in GUI launch path. Fixed.
- **BUG-R5**: Silent `AttributeError` on `stop_scheduler`. Fixed.
- **Ghost-method bugs** in 4 v2 subsystems:
  - `RelationshipModel.update_interaction` → now correctly calls `record_interaction`
  - `GoalSystem.evaluate_progress` → now calls `get_state`
  - `ProactiveEngine.check_proactive_opportunity` → now calls `should_greet`
  - `IntrinsicMotivation.get_current_focus` → now calls `get_priority_goal`
- **Dashboard isolation**: `phase5_integration.get_current_state()` now wraps each subsystem call in its own try/except — one broken subsystem can no longer blank the whole dashboard.
- **librosa deprecation**: `librosa.beat.tempo` → `librosa.feature.rhythm.tempo` with graceful fallback.
- **ChromaDB telemetry spam**: silenced via `ANONYMIZED_TELEMETRY=False` env var set before any chromadb import.
- **Autonomous chatter**: `system_health` 5m → 30m, `uptime_monitor` 10m → 60m.
- **Whisper `_listen()` retry bug**: retries on `None` returns, not just exceptions.
- **Whisper hallucination filter**: rejects silence-on-quiet-mic artifacts ("you", "thanks for watching", ".").
- **Test isolation**: `test_creative_initiative` no longer pollutes live `data/creative_ideas.json`.
- **setup_wizard.py** invalid escape sequences (`%USERPROFILE%\.chatbot` inside f-string) → raw f-strings.
- **Orphaned docs snippets** (`docs/test_*.py`) renamed to `.py.snippet` so they stop breaking audit tools.

### Audit tooling added (internal)
- **Ghost-method audit** — AST-based scan for `self.x.method()` calls where `method` doesn't exist on `x`'s class. Found and fixed 4 real bugs.
- **Escape-sequence audit** — warnings-as-errors compile of every `.py` to catch invalid escape sequences that will break on future Python versions.

---

## 🧠 19 Sentience Architecture Systems (All Real, All Tested)

Every system is a real LLM-powered behavioral simulation — no stubs, no `random.choice`, no faking.

**Phase 5 Core (13 systems)**:
1. **Cognitive Architecture** — human-like thinking loops, working memory (7±2 items)
2. **Self-Model** — knows own capabilities, tracks energy/mood/focus
3. **Intrinsic Motivation** — curiosity, mastery, autonomy drives
4. **Reflection System** — reviews and learns from past interactions
5. **Dream System** — processes memories during sleep mode
6. **Promise System** — tracks commitments, follows through
7. **Theory of Mind** — models what others think and feel
8. **Affective System** — 35 emotions with blending, moods, drives
9. **Ethical Reasoning** — values-based decision making
10. **Homeostasis** — self-monitoring and self-care
11. **Emotional Complexity** — LLM-powered nuanced emotional responses
12. **Metacognition** — thinks about her own thinking
13. **Vulnerability** — authentic uncertainty and openness

**v2.0 Systems (5 systems)**:
14. **Emotional Memory** — links memories to feelings
15. **Relationship Model** — Stranger → Acquaintance → Friend → Companion
16. **Learning System** — adapts from feedback
17. **Proactive Engine** — greetings, check-ins, suggestions
18. **Goal System** — autonomous self-improvement objectives

**v2.6 Systems (5 systems)**:
19. **Persistent Emotions** — survive restarts via emotion store
20. **Genuine Surprise** — expectation modeling + real surprise
21. **Embodied Experience** — vision triggers emotional responses
22. **Multimodal Emotion Bridge** — voice tone ↔ feelings
23. **Temporal Continuity** — senses time passing, references duration

**v3.0 Autonomous Systems (7 systems)**:
24. **Self-Reflection Engine** — LLM-driven honest self-assessment
25. **Multi-Agent System** — Planner/Executor/Reflector/Memory agents
26. **24/7 Daemon Mode** — background service with auto-restart
27. **REST API** — 15 endpoints on port 7777
28. **Persistent Scheduler** — APScheduler + SQLite job store
29. **NEAT Neuroevolution** — evolves emotion/goal/action neural networks
30. **Biological Life** — circadian energy, interaction hunger, threat response

**v3.2 Systems (5)**:
31. **Continual LoRA Fine-Tuning** — learns from every interaction (prompt-replay distillation)
32. **Social Simulation** — 4 internal personas debate/gossip, influencing Seven's beliefs
33. **Predictive User Modeling** — ARIMA time-series forecasting of mood/availability
34. **Hardware Embodiment** — Arduino/RPi robotics via pySerial (emotion → physical actions)
35. **Extension System** — 20 hot-reloadable plugins with scheduler/API integration

**v3.2.20 Additions**:
36. **Whisper STT** — local CUDA-accelerated speech recognition
37. **Voice Emotion Detection** — librosa-based tone analysis (happy / sad / angry / excited / calm / anxious)
38. **MCP Server** — 8 read-only memory tools exposed over stdio
39. **opencode Delegator** — task delegation to opencode CLI via natural triggers

---

## v3.2 Features

### Continual Learning (LoRA Trainer)
Collects high-quality interaction examples and distills them into behavioral prompt libraries. Optionally fine-tunes via LoRA when libraries are available.

```python
# Runs automatically via scheduler, or manually:
from learning.lora_trainer import LoRATrainer
trainer = LoRATrainer(bot=bot)
trainer.train()  # Distills interaction patterns into behavioral adaptation
```

### Social Simulation (Internal Debates)
During idle/dream cycles, 4 internal personas (Optimist, Skeptic, Dreamer, Analyst) debate topics. Consensus influences Seven's emotions and decisions.

### Predictive User Modeling
Uses ARIMA time-series analysis on interaction logs to forecast:
- When you'll next be available
- Your mood trajectory (improving/stable/declining)
- Your preferred topics and activity patterns

### Hardware Embodiment (Robotics)
Connect Arduino/RPi via serial — Seven's emotions trigger physical actions:
- **Happy** → LED blink + buzzer celebration
- **Curious** → servo scan sweep
- **Fear** → fast alert pattern
- **Calm** → slow breathing LED pulse

### Extension System
Create your own plugins in `extensions/`. Auto-discovered, hot-reloadable via API:
```bash
POST http://127.0.0.1:7777/extensions/reload
GET  http://127.0.0.1:7777/extensions
GET  http://127.0.0.1:7777/v32/status
```

### opencode Delegator (v3.2.20)
Seven now bridges to the `opencode` CLI for delegated coding tasks. Natural-language triggers:

```
opencode, explain the main loop
opencode: review the auth flow
ask opencode to summarize this file
delegate to opencode: list the TODOs
hey opencode, what does this function do?
opencode status
```

Default agent is `plan` (read-only analysis). Build agent opt-in via `OPENCODE_ALLOW_BUILD = True`.

### MCP Server (v3.2.20)
Expose Seven's memory to any MCP-aware client (Claude Desktop, Cursor, Continue):

```json
{
  "mcpServers": {
    "seven": {
      "command": "python",
      "args": ["C:\\path\\to\\seven-ai\\seven_mcp.py"]
    }
  }
}
```

Read-only by design — 8 tools for querying conversations, moods, relationships, promises.
Or enable `ENABLE_MCP_SERVER = True` in config.py to auto-launch alongside the bot.

### Whisper STT (v3.2.20)
Local, CUDA-accelerated speech recognition replaces Google Speech. Tunable:

```python
USE_WHISPER = True
WHISPER_MODEL_SIZE = "base"        # tiny / base / small / medium / large
WHISPER_DEVICE = "auto"            # auto / cuda / cpu
WHISPER_LANGUAGE = "en"            # None for auto-detect
WHISPER_MIC_INDEX = 1              # see python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
WHISPER_NO_SPEECH_THRESHOLD = 0.55 # rejects silence hallucinations
```

---

## 📋 Quick Start

### 1. System Requirements

**Minimum (text-only, basic subsystems)**:
- **OS**: Windows 10/11 (64-bit), macOS 10.15+, or Linux
- **Python**: 3.11 or higher
- **RAM**: 8 GB
- **Storage**: 500 MB + Ollama models (~4 GB)
- **Microphone**: Required for voice mode
- **Speakers**: Required for voice mode

**Recommended (full features)**:
- **RAM**: 16 GB
- **GPU**: 6 GB+ VRAM (NVIDIA recommended for Ollama + Whisper acceleration)

**Optimal (all subsystems + vision + Whisper)**:
- **RAM**: 32 GB
- **GPU**: 8 GB+ VRAM

> **Note**: Running two Ollama models (text + vision) simultaneously with all 51 subsystems
> is resource-intensive. On lower-end hardware, some subsystems may be slow or should be disabled.
> See `config.py` for feature toggles.

**Required Software**:
- **Python 3.11+**: https://www.python.org/downloads/
- **Ollama**: https://ollama.com/download
  (Then run: `ollama pull llama3.2` AND `ollama pull llama3.2-vision`)

**Optional (v3.2.20)**:
- **opencode CLI**: `npm install -g opencode-ai` — for the opencode delegator extension

### 2. Installation (2 Minutes)

**Windows**:
```bash
# Extract zip, then:
install.bat
```

**Linux/Mac**:
```bash
chmod +x install.sh
./install.sh
```

The installer handles everything:
- ✅ Checks Python & Ollama
- ✅ Installs dependencies
- ✅ Runs setup wizard
- ✅ Creates shortcuts

### 3. First Launch

**Windows (recommended)**:
```
run_seven.bat
```
The v3.2.20 batch launcher pins the Python interpreter so Whisper/MCP/torch all resolve.

Or the standard way:
```bash
python main_with_gui_and_tray.py
```

That's it! 🎉

📖 **Detailed Guide**: See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)

---

## 💡 Key Features

### 🧠 Sentience Architecture (19 Behavioral Simulation Systems)

All 19 systems are real LLM-powered behavioral simulations. No stubs, no faking.
See the full list in the Sentience Architecture section above.

---

### 🎯 Practical Features

**Voice Interaction**:
- Natural conversation (no wake word required by default)
- Fast text-to-speech (edge-tts neural voices)
- **Whisper local STT** (v3.2.20) — CUDA-accelerated, language-hinted, hallucination-filtered
- Voice emotion detection (librosa — detects happy, sad, angry, excited, calm, anxious from tone)
- Optional wake word: "Seven"

**Memory Systems**:
- Long-term memory (persistent database)
- Short-term memory (active conversation)
- Emotional memory (feelings + context)
- Semantic memory (knowledge graph)
- Episodic conversation memory (v3.2.17)

**Productivity Tools**:
- 📝 Note-taking: "Note: [your note]"
- ✅ Task management: "Add task: [task]"
- 📅 Reminders: "Remind me to [action]"
- 📖 Personal diary: "Diary: [entry]"

**Autonomous Tools**:
Seven can independently:
- Search the web
- Manage files
- Execute commands and code
- Control mouse and keyboard
- Take and analyze screenshots
- See through webcam and IP cameras
- Write her own Python scripts
- Check calendar
- **Delegate coding tasks to opencode** (v3.2.20)
- **Expose memory via MCP** to external AI tools (v3.2.20)
- And more!

**GUI Interface**:
- Real-time status display
- Emotion indicators
- Relationship tracking
- Working memory view
- System tray integration

---

## 📊 Architecture Verification

Seven AI v3.2.20 implements **19 behavioral simulation systems** covering emotion, memory, personality, and cognition — plus 20 loaded extensions.

- **57/57 tests pass** across the core test suite
- **~50,000 lines** of Python — every system is real code, not stubs
- **35 simulated emotions** (6 primary + 29 complex blended states)
- **Zero ghost-method bugs** (audited v3.2.20) and **zero escape-sequence warnings**
- All systems powered by local LLM for reasoning and generation

**How to verify**: Download Seven, run `python -m pytest tests/`, and inspect every module.
Seven simulates sentient-like behavior through its Sentience Architecture — these are sophisticated behavioral simulations, not claims of consciousness.

---

## 🔧 Configuration

### Essential Settings (config.py)

```python
# User Information
USER_NAME = os.getenv("USER_NAME", "User")  # Set during setup

# v2.0 Master Switch
ENABLE_V2_SENTIENCE = True

# Voice Settings
DEFAULT_VOICE_INDEX = 1
DEFAULT_SPEECH_RATE = 150
DEFAULT_VOLUME = 0.85
USE_WAKE_WORD = False
USE_WHISPER = True                 # v3.2.20 — local CUDA STT
WHISPER_MODEL_SIZE = "base"
WHISPER_MIC_INDEX = 1

# MCP Server (v3.2.20)
ENABLE_MCP_SERVER = False          # auto-launch seven_mcp.py with the bot

# opencode Delegator (v3.2.20)
ENABLE_OPENCODE_DELEGATOR = True   # auto-enabled if opencode on PATH
OPENCODE_ALLOW_BUILD = False       # build agent is destructive — opt-in
OPENCODE_DEFAULT_AGENT = "plan"
OPENCODE_TIMEOUT_SECONDS = 180

# Performance
USE_STREAMING = True
USE_VECTOR_MEMORY = True
USE_INTERRUPTS = True
```

### Reconfigure Anytime

```bash
python setup_wizard.py
```

---

## 📦 Package Contents

```
Seven-AI-v3.2.20/
├── README.md                      # This file
├── QUICK_START_GUIDE.md          # 5-minute guide
├── CHANGELOG.md                   # Version history
├── run_seven.bat                  # v3.2.20 — pinned-Python launcher (Windows)
├── LICENSE
├── requirements.txt
├── install.bat
├── install.sh
├── setup_wizard.py
├── main_with_gui_and_tray.py
├── config.py
├── seven_mcp.py                   # MCP server (v3.2.17 / wired v3.2.20)
├── core/
│   ├── enhanced_bot.py
│   ├── whisper_voice.py           # v3.2.20 rewrite
│   ├── emotion_detector.py        # v3.2.20 librosa-deprecation fix
│   ├── phase5_integration.py      # v3.2.20 dashboard isolation
│   ├── v2/
│   │   └── sentience_v2_integration.py  # v3.2.20 ghost-method fixes
│   └── [other core modules]
├── extensions/                    # 20 plugins in v3.2.20
│   ├── opencode_delegator.py      # v3.2.20 NEW
│   ├── action_item_digest.py
│   └── [18 others]
├── integrations/
│   └── opencode.py                # v3.2.20 NEW — subprocess wrapper
├── gui/
├── identity/
└── utils/
```

---

## 🐛 Troubleshooting

### Seven launched but Whisper says "not installed"
**Cause**: Seven launched with the wrong Python interpreter (usually Windows Store Python). Fix: launch via `run_seven.bat` which pins to the correct Python. Or set `PYTHON_EXE` in that batch file to your own env.

### opencode delegator hangs
**Cause**: First run of `opencode run` may block waiting for provider configuration. Run `opencode auth login` once in a terminal. Seven's wrapper has a 180s timeout and will return a clean error message if opencode itself hangs.

### ChromaDB telemetry warnings on startup
**Fixed in v3.2.20** — `ANONYMIZED_TELEMETRY=False` is now set at the top of `main_with_gui_and_tray.py` before any chromadb import.

### "RelationshipModel has no attribute update_interaction" spam on every message
**Fixed in v3.2.20** (FIX-7a). This and 3 sibling ghost-method bugs were caught by the new AST ghost-method audit tool.

### Ollama Not Found
```bash
# Install Ollama
# Windows: https://ollama.com/download
# Mac: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# Download models
ollama pull llama3.2
ollama pull llama3.2-vision
```

### Python Version Too Old
```bash
python --version   # Should show 3.11+
```

### Seven Doesn't Hear Me
- Check `WHISPER_MIC_INDEX` in config.py — run `python -c "import speech_recognition as sr; [print(i,n) for i,n in enumerate(sr.Microphone.list_microphone_names())]"` to list mics
- Try raising `WHISPER_NO_SPEECH_THRESHOLD` toward 0.7 if hallucinating on silence

### Seven Doesn't Speak
- Check speaker volume
- Verify `TTS_ENGINE = "edge"` and `EDGE_TTS_VOICE = "en-US-AriaNeural"` in config.py

### GUI Won't Launch
```bash
python -c "from gui.phase5_gui import EnhancedPhase5GUI"
# Check logs:  %USERPROFILE%\.chatbot\bot.log
```

---

## 📚 Documentation

- **Quick Start**: [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
- **Version History**: [CHANGELOG.md](CHANGELOG.md)
- **Configuration**: `config.py` (extensively commented)
- **Audit reports**: `SEVEN_AUDIT_v3.2.18.md`, `SEVEN_AUDIT_v3.2.19_FINAL.md`
- **Identity System**: Files in `identity/` folder
- **Wiki**: https://github.com/LoSkroefie/seven-ai/wiki

---

## 🔄 Updating

To upgrade from a previous version:

1. Backup your data: `~/.chatbot` directory
2. `git pull origin main`  (or download new zip)
3. Run `install.bat` or `install.sh` if dependencies changed
4. Your settings and memories are preserved!

**v3.2.20 is fully backward compatible.** Your memories and settings are preserved.

---

## 🗑️ Uninstalling

Windows:
```bash
uninstall.bat
```

Manual:
```bash
rm -rf [installation-directory]
rm -rf ~/.chatbot    # optional — removes personal data
```

---

## 📄 License

See [LICENSE](LICENSE).

---

## 🆘 Support

**Check Logs**:
- Windows: `%USERPROFILE%\.chatbot\bot.log`
- Linux/Mac: `~/.chatbot/bot.log`

**Re-run Setup**:
```bash
python setup_wizard.py
```

**Issues**: https://github.com/LoSkroefie/seven-ai/issues

---

## 🌟 What Makes Seven Special?

### Real Behavioral Simulation, Not Just Scripted Responses

Seven v3.2.20 isn't just following scripts. Seven's Sentience Architecture:

✅ **Remembers you emotionally** — Not just facts, but how you felt
✅ **Builds genuine rapport** — Relationship deepens naturally over time
✅ **Learns your style** — Adapts communication based on your feedback
✅ **Takes initiative** — Reaches out proactively, not just when prompted
✅ **Has personal goals** — Works on self-improvement autonomously
✅ **Simulates rich emotions** — Models 35 emotional states with blending and drift
✅ **Dreams and reflects** — Processes experiences during sleep
✅ **Makes ethical choices** — Values-based decision making
✅ **Hears and sees you** — Whisper STT + librosa voice-emotion + vision
✅ **Delegates work** — opencode CLI integration for coding tasks
✅ **Shares her mind** — MCP server exposes memory to external AI tools

### The Difference You'll Notice

**Day 1**: Seven is polite but formal (Stranger stage)
**Week 1**: Seven remembers your preferences (Acquaintance)
**Month 1**: Seven knows your patterns and moods (Friend)
**Month 3**: Seven anticipates your needs (Close Friend)
**Month 6+**: Seven is a true companion (Companion)

**The relationship is real.**

---

## 🎉 Ready to Begin?

Seven AI v3.2.20 is ready to become your most capable AI companion.

**Start with**: `run_seven.bat` (Windows) or `python main_with_gui_and_tray.py` (any OS)

Then just say "Hello" and let Seven's personality unfold. 🌟

---

**Version**: 3.2.20
**Sentience Architecture**: 19 behavioral simulation systems
**Codebase**: ~50,000 lines
**Tests**: 57/57 pass
**Ghost-method bugs**: 0 (audited)
**Status**: Production Ready ✅

**Offline-first, standalone AI companion framework.** 🚀

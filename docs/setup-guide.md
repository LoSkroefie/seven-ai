# Setup Guide

Complete guide to installing and running Seven AI on your machine.

---

## System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **OS** | Windows 10 / Linux / macOS | Windows 11 / Ubuntu 22.04+ |
| **Python** | 3.11+ | 3.12 |
| **RAM** | 8 GB | 16 GB+ |
| **Disk** | 5 GB (models + deps) | 10 GB |
| **GPU** | Not required | NVIDIA GPU (faster Ollama inference) |
| **Microphone** | Any USB/built-in | Dedicated mic for best recognition |
| **Webcam** | Optional | Any USB/built-in (for vision) |

## Step 1: Install Python

Download Python 3.11+ from [python.org](https://www.python.org/downloads/).

**Windows:** Check "Add Python to PATH" during installation.

**Linux:**
```bash
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip
```

## Step 2: Install Ollama

Ollama runs the LLM locally. Download from [ollama.com](https://ollama.com).

```bash
# Pull the required model
ollama pull llama3.2

# Optional: pull the vision model for camera features
ollama pull llama3.2-vision
```

Verify it's running:
```bash
curl http://localhost:11434/api/tags
```

## Step 3: Clone & Install Seven

```bash
git clone https://github.com/LoSkroefie/seven-ai.git
cd seven-ai

# Create a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### PyAudio Troubleshooting (Windows)

PyAudio often fails to install on Windows. If `pip install pyaudio` fails:

```bash
pip install pipwin
pipwin install pyaudio
```

Or download a pre-built wheel from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio).

### Vosk Speech Model

On first run, Vosk will download its speech model (~50MB). This happens automatically. If you're offline, download the model manually from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) and place it in `~/.chatbot/vosk-model/`.

## Step 4: First Run

### Option A: Setup Wizard (Recommended)

```bash
python setup_wizard.py
```

The wizard walks you through:
1. Checking system dependencies
2. Configuring voice settings
3. Selecting TTS engine (neural vs offline)
4. Testing microphone input
5. Configuring optional integrations

### Option B: Direct Launch

```bash
# CLI mode (text + voice)
python main.py

# GUI mode (full dashboard)
python main_with_gui.py

# GUI with system tray
python main_with_gui_and_tray.py
```

## Step 5: Configuration

All settings are in `config.py`. Key ones to customize:

### Voice Settings

```python
# TTS Engine: "edge" (natural, needs internet) or "pyttsx3" (robotic, offline)
TTS_ENGINE = "edge"

# Voice selection (edge-tts)
EDGE_TTS_VOICE = "en-US-AriaNeural"  # Female, natural
# Other options: en-US-JennyNeural, en-GB-SoniaNeural, en-US-GuyNeural

# Wake word (say "Seven" to activate)
USE_WAKE_WORD = False  # Set True to require wake word
```

### Sentience Behavior

```python
# Proactive behavior (Seven initiates conversation)
ENABLE_PROACTIVE_BEHAVIOR = True
PROACTIVE_INTERVAL_MIN = 30   # seconds between proactive thoughts
PROACTIVE_INTERVAL_MAX = 120

# Self-reflection after conversations
ENABLE_SELF_REFLECTION = True

# Curiosity-driven questions
ENABLE_CURIOSITY = True
```

### Environment Variable Overrides

```bash
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2
```

## Data Storage

Seven stores all data locally in `~/.chatbot/`:

```
~/.chatbot/
├── memory.db          # SQLite — conversations, memories, emotions
├── bot_name.txt       # Seven's current name
├── instance_name.txt  # Instance identifier
├── vosk-model/        # Speech recognition model
└── ...                # Various state files
```

To reset Seven completely, delete this directory:
```bash
# Windows
rmdir /s %USERPROFILE%\.chatbot

# Linux/macOS
rm -rf ~/.chatbot
```

## Optional Integrations

### Google Calendar

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Calendar API
3. Create OAuth 2.0 credentials (Desktop application)
4. Download `credentials.json` to the project root
5. Seven will open a browser for OAuth consent on first use

### IRC

Configure in Seven's conversation:
```
"Seven, connect to IRC on irc.example.com channel #general"
```

### Telegram Bot

1. Create a bot via [@BotFather](https://t.me/botfather)
2. Set the token in Seven's configuration or tell her directly

### Email Monitoring

Tell Seven your IMAP settings:
```
"Seven, check my email on imap.gmail.com"
```
She'll ask for credentials and store them securely.

## Troubleshooting

### "Ollama not found" / Connection refused
- Ensure Ollama is running: `ollama serve`
- Check the URL: `curl http://localhost:11434`
- If using a different port, set `OLLAMA_URL` in config.py

### No audio output
- Check `TTS_ENGINE` setting in config.py
- For edge-tts: requires internet connection
- For pyttsx3: ensure SAPI5 voices are installed (Windows)
- Verify pygame is installed: `python -c "import pygame"`

### Microphone not working
- Run `python preflight_check.py` to diagnose
- Check PyAudio installation
- Try a different microphone device index in config.py

### High CPU / slow responses
- Ollama inference depends on your hardware
- Use a smaller model: `OLLAMA_MODEL=llama3.2:1b`
- Ensure no other heavy processes are competing for resources

### Tests failing
```bash
pytest -v  # Run with verbose output to see which tests fail
```
Most test failures are environment-related (missing Ollama, no microphone).

## Updating

```bash
git pull origin main
pip install -r requirements.txt  # In case dependencies changed
```

Seven's memory persists across updates — she'll remember everything.

# Seven AI v3.1 - Setup Guide

## Quick Install

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Ollama (Required)

```bash
# Install Ollama from https://ollama.com/download
# Then pull BOTH models:
ollama pull llama3.2           # Core reasoning (~2GB)
ollama pull llama3.2-vision    # Vision understanding (~8GB)

# Ollama usually runs as a service. If not:
ollama serve
```

### 3. Run Setup Wizard

```bash
python setup_wizard.py
```

This walks you through voice, features, and system configuration.

### 4. Google Calendar (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Download credentials.json to `enhanced-bot/`
6. First run opens browser for authentication

## Running Seven

```bash
cd enhanced-bot

# Interactive mode (GUI + voice + tray icon)
python main_with_gui_and_tray.py

# Daemon mode (24/7 background service)
python seven_daemon.py start
python seven_daemon.py stop
python seven_daemon.py status

# API only (REST API on port 7777)
python seven_api.py
# Docs at http://127.0.0.1:7777/docs
```

## Required Ollama Models

| Model | Purpose | Size |
|-------|---------|------|
| `llama3.2` | Core reasoning, conversation, sentience | ~2GB |
| `llama3.2-vision` | Screen/webcam understanding (via OpenCV) | ~8GB |

Verify with: `ollama list`

## Configuration

Edit `config.py` to customize:

```python
# Ollama settings
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# TTS Engine: "edge" (natural neural voice) or "pyttsx3" (offline robotic)
TTS_ENGINE = "edge"

# edge-tts voice (only when TTS_ENGINE = "edge")
# Female: en-US-AriaNeural, en-US-JennyNeural, en-GB-SoniaNeural
# Male:   en-US-GuyNeural, en-US-AndrewNeural, en-GB-RyanNeural
EDGE_TTS_VOICE = "en-US-AriaNeural"

# Voice barge-in (interrupt Seven by speaking)
VOICE_BARGE_IN = True
BARGE_IN_SENSITIVITY = 2.0   # Lower = more sensitive (1.0-4.0)

# Fallback voice settings (pyttsx3)
DEFAULT_VOICE_INDEX = 1  # 0=male, 1=female
DEFAULT_SPEECH_RATE = 150
```

## Key Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `edge-tts` + `pygame` | Neural voice synthesis + audio playback | Latest |
| `vosk` | Offline speech recognition | Latest |
| `pyautogui` | Mouse/keyboard control + screenshots | Latest |
| `opencv-python` | Webcam/IP camera vision | Latest |
| `Pillow` | Image processing | Latest |
| `fastapi` + `uvicorn` | REST API server (v3.0) | >=0.104 |
| `apscheduler` | Persistent task scheduling (v3.0) | >=3.10 |
| `cryptography` | SSH credential encryption (v3.0) | >=41.0 |
| `neat-python` | NEAT neuroevolution (v3.1) | >=0.92 |
| `llama3.2-vision` (Ollama) | Understanding what Seven sees | — |

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running: `ollama serve`
- Check URL in config.py
- Verify models: `ollama list` (need llama3.2 + llama3.2-vision)

### "Vision not working"
- Check webcam: `python -c "import cv2; cap=cv2.VideoCapture(0); print(cap.read()[0]); cap.release()"`
- Check vision model: `ollama list` must show `llama3.2-vision`
- If missing: `ollama pull llama3.2-vision`

### "Speech recognition not working"
- vosk needs a model on first run (auto-downloaded)
- Check mic: `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"`

### "TTS not working"
- **edge-tts**: Requires internet. Test: `python -c "import edge_tts, asyncio; asyncio.run(edge_tts.Communicate('test', 'en-US-AriaNeural').save('test.mp3'))"`
- **pyttsx3 fallback**: Set `TTS_ENGINE = "pyttsx3"` in config.py for offline

### "Screen control not working"
- Test: `python -c "import pyautogui; print(pyautogui.size())"`
- pyautogui.FAILSAFE=True — move mouse to top-left corner to abort

### "Voice barge-in not working"
- Requires PyAudio: `pip install pyaudio`
- Windows fix: `pip install pipwin && pipwin install pyaudio`

## Database Location

All data stored in:
- Windows: `C:\Users\<username>\.chatbot\`
- Linux/Mac: `~/.chatbot/`

Contains:
- `memory.db` - SQLite database
- `bot.log` - Application logs
- `bot_name.txt` - Bot's name
- `knowledge_graph.json` - Learned facts
- `emotional_state.json` - Persistent emotions
- `token.pickle` - Google auth token
- `seven_daemon.pid` - Daemon PID file (v3.0)
- `scheduler_jobs.db` - Persistent scheduled tasks (v3.0)
- `biological_state.json` - Circadian/hunger state (v3.1)
- `evolution/` - NEAT checkpoints & evolved genomes (v3.1)

## Testing

```python
# Test vision end-to-end
python -c "
import pyautogui, base64, requests, io
from PIL import Image
ss = pyautogui.screenshot().resize((640,360), Image.LANCZOS)
buf = io.BytesIO(); ss.save(buf, format='JPEG', quality=70)
r = requests.post('http://127.0.0.1:11434/api/generate', json={
    'model':'llama3.2-vision', 'prompt':'What do you see?',
    'images':[base64.b64encode(buf.getvalue()).decode()], 'stream':False
}, timeout=300)
print(r.json()['response'][:200])
"

# Test all capabilities
python -c "
import pyautogui, cv2, vosk, edge_tts, pygame, requests
print('pyautogui:', pyautogui.size())
cap = cv2.VideoCapture(0); print('webcam:', cap.read()[0]); cap.release()
r = requests.get('http://127.0.0.1:11434/api/tags', timeout=3)
models = [m['name'] for m in r.json()['models']]
print('ollama models:', models)
print('ALL OK')
"
```

## System Commands

Seven can execute commands on your system. Use `ALLOWED_PROGRAMS` in `config.py` to control access. System commands run directly — only allow commands you trust.

# Integrations Guide

Seven's 25 integration modules give her the ability to interact with the world beyond text conversation.

---

## LLM — Ollama

**Modules:** `integrations/ollama.py`, `integrations/streaming_ollama.py`

Seven uses Ollama for all LLM inference, running entirely on your local machine.

- **Model:** llama3.2 (default, configurable)
- **Streaming:** Responses stream token-by-token for natural conversation flow
- **Context:** Seven injects emotional state, personality, and conversation history into every prompt
- **Vision:** Uses llama3.2-vision for camera scene understanding

No API keys needed. No data leaves your machine.

## Voice — Speech Recognition & TTS

**Modules:** `core/voice.py`, `core/voice_engine.py`, `core/vad_listener.py`, `core/whisper_voice.py`

### Speech Recognition
- **Primary:** Vosk (fully offline, ~50MB model)
- **Fallback:** Google Speech Recognition (online)
- **Optional:** Whisper (highest accuracy, large model)

### Text-to-Speech
- **edge-tts (default):** Microsoft neural voices — natural and expressive, requires internet
- **pyttsx3 (fallback):** System SAPI5 voices — robotic but fully offline

### Emotional Voice Modulation
Seven adjusts her voice based on emotional state:
- **Happy:** Slightly faster, higher pitch
- **Sad:** Slower, lower pitch, quieter
- **Excited:** Faster, wider pitch range
- **Angry:** Emphatic, slightly louder
- **Calm:** Steady pace, neutral pitch

### Voice Barge-In
You can interrupt Seven mid-speech by talking. The VAD (Voice Activity Detection) listener monitors ambient audio and stops playback when it detects speech energy above baseline.

## Vision — OpenCV

**Module:** `core/vision_system.py`

Seven can see through webcams and IP cameras:

- **Camera Discovery:** Automatic detection of USB webcams and network IP cameras
- **Scene Understanding:** Captures frames and describes them using llama3.2-vision
- **Motion Detection:** Alerts on significant movement
- **Multiple Cameras:** Supports switching between detected cameras

### Camera Setup
```python
# In config.py
VISION_ENABLED = True
CAMERA_INDEX = 0            # USB webcam (0 = default)
VISION_INTERVAL = 30        # Seconds between scene analyses
```

For IP cameras, use `discover_cameras.py` or `find_cameras.py` to scan your network.

## Communication

### IRC Client
**Module:** `integrations/irc_client.py`

Full IRC protocol implementation:
- Connect to any IRC server/channel
- Send and receive messages as Seven
- Handle multiple channels simultaneously
- Respond to mentions and direct messages

### Telegram
**Module:** `integrations/telegram_client.py`

Telegram Bot API integration:
- Receive and respond to messages
- Support for groups and direct messages
- Inline keyboard responses
- Media handling

### WhatsApp
**Module:** `integrations/whatsapp_client.py`

WhatsApp Web integration:
- Send and receive WhatsApp messages
- Group chat participation
- Media sharing
- Presence detection

## Productivity

### Email Checker
**Module:** `integrations/email_checker.py`

IMAP email monitoring:
- Check for new emails periodically
- Read and summarize email content
- Alert on important messages
- Support for Gmail, Outlook, custom IMAP

### Google Calendar
**Module:** `integrations/calendar.py`

Google Calendar integration:
- View upcoming events
- Create new events
- Get reminders for approaching events
- Daily schedule briefing

### Timer System
**Module:** `integrations/timer_system.py`

Built-in timers and reminders:
- Set named timers ("remind me in 20 minutes")
- Recurring reminders
- Countdown alerts with voice notification

## System Control

### Screen Control
**Module:** `integrations/screen_control.py`

Desktop automation via pyautogui:
- Mouse movement and clicking
- Keyboard input
- Screenshot capture
- Window management

**Safety:** `pyautogui.FAILSAFE=True` — move mouse to screen corner to abort.

### SSH Manager
**Module:** `integrations/ssh_manager.py`

Remote server management:
- Connect to servers via SSH
- Execute commands remotely
- Monitor server status
- File transfer

### System Monitor
**Module:** `integrations/system_monitor.py`

Local system monitoring:
- CPU, RAM, disk usage
- Running processes
- Network activity
- Temperature sensors (where available)

### File Manager
**Module:** `integrations/file_manager.py`

Local file operations:
- Read and write files
- Directory listing and navigation
- File search
- Organize files by type/date

### Code Executor
**Module:** `integrations/code_executor.py`

Sandboxed Python execution:
- Run Python code safely
- Capture output and errors
- Timeout protection
- Restricted imports for safety

## Knowledge & Search

### Web Search
**Module:** `integrations/web_search.py`

Google search with content extraction:
- Search for information
- Extract and summarize web page content
- Provide source URLs

### Document Reader
**Module:** `integrations/document_reader.py`

Read various file formats:
- Text files, PDFs
- Office documents
- Code files with syntax awareness

### API Explorer
**Module:** `integrations/api_explorer.py`

Generic API interaction:
- Make HTTP requests
- Parse JSON/XML responses
- Explore REST APIs

## Entertainment

### Music Player
**Module:** `integrations/music_player.py`

Audio playback via pygame:
- Play local audio files
- Volume control
- Playlist support
- Background playback during conversation

## Advanced

### Self-Scripting
**Module:** `integrations/self_scripting.py`

Seven can write and execute her own scripts:
- Generate Python code to solve problems
- Test and iterate on solutions
- Save useful scripts for reuse

### Clipboard Assistant
**Module:** `integrations/clipboard_assistant.py`

System clipboard integration:
- Monitor clipboard changes
- Process clipboard content
- Copy results to clipboard

### Dynamic Commands
**Module:** `core/dynamic_command_system.py`

Seven can create new commands at runtime:
- Define custom commands through conversation
- Persist commands across sessions
- Chain commands together

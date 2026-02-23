# Known Issues & Solutions

## 🔧 Potential Issues & How to Fix Them

### 1. **PyAudio Installation Fails**

**Problem:** `pip install pyaudio` fails on Windows  
**Solution:**
```bash
# Option 1: Use pre-built wheel
pip install pipwin
pipwin install pyaudio

# Option 2: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/
pip install PyAudio‑0.2.14‑cp311‑cp311‑win_amd64.whl

# Option 3: Skip PyAudio (VAD won't work but rest will)
# Set USE_VAD = False in config.py
```

**Workaround:** Bot works without PyAudio, just disables VAD feature

---

### 2. **Whisper Model Download Slow**

**Problem:** First run downloads large Whisper model  
**Solution:**
```bash
# Pre-download models
python -c "import whisper; whisper.load_model('base')"

# Or use smaller model in config.py:
# In whisper_voice.py, change to 'tiny' instead of 'base'
```

**Note:** Only happens once, then cached

---

### 3. **Ollama Connection Refused**

**Problem:** `Cannot connect to Ollama at http://localhost:11434`  
**Solution:**
```bash
# Make sure Ollama is running
ollama serve

# Or if on different host, update config.py:
OLLAMA_URL = "http://your-server:11434"
```

**Workaround:** Bot falls back to limited functionality without Ollama

---

### 4. **Microphone Not Detected**

**Problem:** No microphone input  
**Solution:**
```bash
# List available microphones
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Check Windows settings:
# Settings → Privacy → Microphone → Allow apps
```

**Workaround:** Can test with text input mode (not implemented yet, but easy to add)

---

### 5. **Google Calendar Authentication Fails**

**Problem:** Browser doesn't open for OAuth  
**Solution:**
```bash
# 1. Delete old token
rm ~/.chatbot/token.pickle

# 2. Try again - browser should open
# 3. If still fails, check credentials.json is valid
# 4. Ensure redirect URI is http://localhost
```

**Workaround:** Calendar features optional, bot works without them

---

### 6. **ChromaDB Fails to Initialize**

**Problem:** `Cannot initialize ChromaDB`  
**Solution:**
```bash
# Delete corrupted database
rm -rf ~/.chatbot/chroma_db

# Reinstall ChromaDB
pip uninstall chromadb
pip install chromadb==0.4.22
```

**Workaround:** Set `USE_VECTOR_MEMORY = False` in config.py

---

### 7. **Out of Memory with Whisper**

**Problem:** Large audio files crash Whisper  
**Solution:**
```python
# In config.py, use smaller model:
# In whisper_voice.py line 15, change 'base' to 'tiny'

# Or reduce audio quality before processing
```

**Workaround:** Falls back to Google Speech Recognition automatically

---

### 8. **TTS Voice Not Female**

**Problem:** Voice sounds male  
**Solution:**
```python
# In config.py, try different voice index:
DEFAULT_VOICE_INDEX = 0  # Try 0, 1, 2, etc.

# List available voices:
import pyttsx3
engine = pyttsx3.init()
for idx, voice in enumerate(engine.getProperty('voices')):
    print(f"{idx}: {voice.name}")
```

---

### 9. **Background Tasks Not Running**

**Problem:** Proactive features don't work  
**Solution:**
```python
# Check if enabled in config.py:
USE_BACKGROUND_TASKS = True

# Check console for errors:
# Background tasks run in daemon thread
```

**Workaround:** Disable with `USE_BACKGROUND_TASKS = False`

---

### 10. **High CPU Usage**

**Problem:** Bot uses too much CPU  
**Solution:**
```python
# Reduce features in config.py:
USE_EMOTION_DETECTION = False  # CPU-intensive audio analysis
USE_STREAMING = False  # Less CPU but slower
USE_VAD = False  # Reduce audio processing

# Or use smaller Whisper model (tiny vs base)
```

---

## 🛡️ Robustness Features Built-In

### Automatic Fallbacks

1. **Whisper fails** → Falls back to Google Speech Recognition
2. **Ollama offline** → Uses fallback responses
3. **ChromaDB errors** → Uses SQLite only
4. **VAD not available** → Uses timeout-based listening
5. **Google Calendar fails** → Continues without calendar
6. **Background tasks crash** → Restart automatically

### Error Recovery

- All functions wrapped with try-catch
- Resource cleanup guaranteed
- Database transactions atomic
- Audio devices properly released
- Thread safety for shared resources

### Graceful Degradation

Bot works even if:
- ❌ Internet is down (Whisper + Ollama local)
- ❌ Some features disabled
- ❌ API limits reached
- ❌ Hardware issues
- ❌ Dependencies missing

---

## 🧪 Testing

```bash
# Test basic functionality
python -c "from core.enhanced_bot import UltimateBotCore; bot = UltimateBotCore()"

# Test Whisper
python -c "from core.whisper_voice import WhisperVoiceManager; w = WhisperVoiceManager()"

# Test ChromaDB
python -c "from core.vector_memory import VectorMemory; v = VectorMemory()"

# Test Ollama
python -c "from integrations.ollama import OllamaClient; o = OllamaClient(); o.test_connection()"
```

---

## 📝 Reporting Issues

If you find a bug:

1. Check console/log output: `~/.chatbot/bot.log`
2. Try with features disabled one by one
3. Check SETUP.md for configuration
4. Most issues are dependency-related

---

## ✅ What's Already Bulletproofed

- ✅ All file operations have error handling
- ✅ All network calls have timeouts
- ✅ All audio operations properly cleanup
- ✅ All threads are daemon (won't block exit)
- ✅ All database operations are transactional
- ✅ All user inputs are validated
- ✅ All features have fallbacks
- ✅ Resource leaks prevented
- ✅ Memory leaks minimized
- ✅ Concurrent access protected

---

**Bottom line:** Bot is designed to **never crash**. If a feature fails, it degrades gracefully and continues working.

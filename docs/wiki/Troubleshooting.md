# Troubleshooting

Common issues and fixes for Seven AI v3.2.20.

---

## Voice / Whisper

### "Failed to initialize WhisperVoice: Whisper not installed"

**Cause**: Seven launched with the wrong Python interpreter (usually Windows Store Python from `AppData\Local\Microsoft\WindowsApps\python.exe`), which doesn't have `whisper` / `mcp` / working `torch` installed.

**Fix** (Windows):
```
run_seven.bat
```

Or edit `run_seven.bat` and set `PYTHON_EXE` to the Python where Whisper is installed. Verify:
```bash
C:\your\python\path.exe -c "import whisper; print(whisper.__version__)"
```

Also worth disabling Windows Store Python app aliases: **Settings → Apps → Advanced app settings → App execution aliases** → toggle off `python.exe` and `python3.exe`.

### "Could not understand audio" on every listen

- Check `WHISPER_MIC_INDEX` in `config.py` — you might be recording from a disabled mic
- List mics: `python -c "import speech_recognition as sr; [print(i,n) for i,n in enumerate(sr.Microphone.list_microphone_names())]"`
- Try a smaller model: `WHISPER_MODEL_SIZE = "tiny"` to rule out model loading issues

### Seven hears TV/music in the background

- Set `USE_WAKE_WORD = True` so Seven only responds after hearing "Seven"
- Raise `WHISPER_NO_SPEECH_THRESHOLD` toward 0.7

See the full [Voice & Whisper STT](Voice-and-Whisper-STT) page for more.

---

## Runtime Errors

### "RelationshipModel has no attribute update_interaction"
**Fixed in v3.2.20** (FIX-7a). If you still see this, you're on an older version — update.

### "librosa not installed" / EmotionDetector disabled
Same root cause as Whisper not installed — wrong Python. Fix via `run_seven.bat`.

### ChromaDB telemetry spam on startup

```
Failed to send telemetry event ClientStartEvent: capture() takes 1 positional argument but 3 were given
```

**Fixed in v3.2.20** — `ANONYMIZED_TELEMETRY=False` is now set at the top of `main_with_gui_and_tray.py`. If you see this on v3.2.20+, check that the env var is actually set:

```bash
python -c "import os; print(os.environ.get('ANONYMIZED_TELEMETRY'))"
```

---

## Seven Interrupts Conversations

Seven v3.2.20 already throttles autonomous chatter:
- `system_health` fires every 30 min (was 5 min)
- `uptime_monitor` fires every 60 min (was 10 min)

If you still want fewer interruptions, edit the scheduler intervals at the top of each extension file:

```python
# extensions/system_health.py
schedule_interval_minutes = 60   # was 30
```

Or disable entirely by removing the `@register` decorator or deleting the file.

---

## opencode Delegator

### "opencode CLI isn't available"
```bash
npm install -g opencode-ai
where opencode   # Windows
which opencode   # Linux/macOS
```

### opencode hangs on first use
```bash
opencode auth login
```

opencode needs a provider configured. Seven's wrapper has a 180s timeout and returns a clean error if opencode never responds.

### Timeouts on big tasks
Raise `OPENCODE_TIMEOUT_SECONDS` in config.py. Default 180s covers small queries; big refactors may need 600s+.

See [opencode Delegator](opencode-Delegator) for full details.

---

## Ollama

### "Ollama not found" during install
```bash
# Windows: install from https://ollama.com/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3.2
ollama pull llama3.2-vision   # optional
```

### Seven can't reach Ollama
Check `OLLAMA_URL` in `config.py` (default `http://localhost:11434`) and verify:
```bash
curl http://localhost:11434/api/tags
```

Should return JSON with your pulled models.

---

## GUI / Dashboard

### Dashboard shows blank / no state
Should never happen on v3.2.20+ (FIX-8b isolated each subsystem). If you do see it:
- Check `~/.chatbot/bot.log` for `subsystem state error` lines
- File an issue with the log

### Web UI won't start
Check `gradio` is installed:
```bash
pip install gradio plotly
```

---

## Tests

### Running the test suite
```bash
python -m pytest tests/ -v
```

Expected output: `57 passed`. If you see failures, please file an issue with the full output.

### Tests pollute `data/` on disk
**Fixed in v3.2.20** (FIX-4b) — `test_creative_initiative` now uses `tmp_path`. If you're on an older version, reset `data/creative_ideas.json` to `[]`.

---

## Logs

Log locations:
- Windows: `%USERPROFILE%\.chatbot\bot.log`
- Linux/macOS: `~/.chatbot/bot.log`

Rotating file handler — max 1 MB per file, 5 backups kept.

---

## Filing Issues

https://github.com/LoSkroefie/seven-ai/issues

Include:
- Seven version (`git log --oneline -1` inside the repo)
- OS + Python version (`python --version`)
- Ollama version (`ollama --version`)
- Last ~100 lines of `bot.log`
- What you said / did right before the issue

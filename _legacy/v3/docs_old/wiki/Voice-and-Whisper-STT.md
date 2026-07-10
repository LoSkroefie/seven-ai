# Voice & Whisper STT

Seven uses **OpenAI Whisper** for local, CUDA-accelerated speech recognition. No cloud calls for voice — everything runs on your machine.

---

## Quick Setup

In `config.py`:
```python
USE_WHISPER = True                 # enabled by default in v3.2.20+
WHISPER_MODEL_SIZE = "base"        # tiny / base / small / medium / large
WHISPER_DEVICE = "auto"            # auto (picks CUDA if available) / cuda / cpu
WHISPER_LANGUAGE = "en"            # or None for auto-detect
WHISPER_MIC_INDEX = 1              # see below
WHISPER_NO_SPEECH_THRESHOLD = 0.55
WHISPER_LISTEN_TIMEOUT = 10        # seconds before a new turn starts
WHISPER_PHRASE_LIMIT = 15          # max seconds of continuous speech
WHISPER_RECALIBRATE_EACH_LISTEN = False
```

---

## Model Sizes

| Size   | Disk | VRAM  | Speed (CUDA) | Accuracy |
|--------|------|-------|--------------|----------|
| tiny   | 72 MB | ~1 GB | Fastest | Lowest |
| base   | 139 MB | ~1 GB | Fast | Good (default) |
| small  | 488 MB | ~2 GB | Medium | Better |
| medium | 1.5 GB | ~5 GB | Slow | Great |
| large  | 3 GB | ~10 GB | Slowest | Best |

`base` is the default. Upgrade to `small` or `medium` if you have a good GPU and want better recognition.

---

## Finding Your Mic Index

List all microphones:
```bash
python -c "import speech_recognition as sr; [print(i, n) for i, n in enumerate(sr.Microphone.list_microphone_names())]"
```

Pick the one that matches your actual recording device (usually a Realtek or USB headset). Set `WHISPER_MIC_INDEX = <number>` in `config.py`.

On laptops with multiple Realtek entries, try the lowest index first (usually 1).

---

## Hallucination Filter

Whisper is notorious for "hallucinating" text on silent audio — it'll produce phrases like `"you"`, `"thanks for watching"`, `"Bye."`, or `"."` when there's actually nothing to transcribe.

The `WHISPER_NO_SPEECH_THRESHOLD` knob rejects these. Higher value = stricter (rejects more).

- `0.3` — loose, catches quiet speech but allows some hallucinations
- `0.55` — balanced (default)
- `0.7` — strict, only accepts high-confidence speech

If Seven keeps responding to things you didn't say, raise to `0.7`. If she's missing real speech, lower to `0.4`.

---

## Calibration

Seven does a one-shot mic calibration at startup (v3.2.20 optimization — previous versions recalibrated on every listen, costing 500ms per turn).

If ambient noise changes a lot during a session (AC kicks on, music starts, etc.), set:
```python
WHISPER_RECALIBRATE_EACH_LISTEN = True
```

---

## Troubleshooting

### "Failed to initialize WhisperVoice: Whisper not installed"
You launched Seven with the wrong Python interpreter. Fix on Windows: use `run_seven.bat` instead of `python launch_seven.py`. The batch file pins to the Python env where Whisper is actually installed.

### "Could not understand audio" on every listen
- Check `WHISPER_MIC_INDEX` — you might be recording from a disabled or disconnected mic
- Try a lower model: `WHISPER_MODEL_SIZE = "tiny"` to rule out model loading issues
- Check `bot.log` for errors during the transcription step

### Whisper responds to TV/music in the background
- Set `USE_WAKE_WORD = True` so Seven only responds after hearing "Seven"
- Raise `WHISPER_NO_SPEECH_THRESHOLD` toward 0.7

### CUDA errors on startup
- Set `WHISPER_DEVICE = "cpu"` as a fallback
- Verify `torch.cuda.is_available()` in a Python REPL

---

## Alternative: Google Speech Recognition (Fallback)

If Whisper fails to load, Seven silently falls back to `speech_recognition`'s Google Speech backend. Requires internet. No config needed — it just works as a backup.

Set `USE_WHISPER = False` to force the Google path.

---

## See Also

- [Voice Emotion Detection](Voice-Emotion-Detection) — librosa-based tone analysis (happy/sad/angry/excited/calm/anxious)
- [TTS Voices](TTS-Voices) — edge-tts neural voices for Seven's speech
- [Troubleshooting](Troubleshooting)

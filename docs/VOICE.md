# Seven Real — Voice setup (Windows)

Voice is **default off**. Push-to-talk only — no ambient listening spam.

## Quick enable

```bat
cd C:\Users\USER-PC\seven-ai
pip install edge-tts pygame SpeechRecognition openai-whisper pyaudio pyttsx3
python -m seven --voice
python -m seven --gui --voice
```

## What you get

| Piece | Engine | Notes |
|---|---|---|
| TTS | **edge-tts** + pygame | Neural voice (needs network once). Fallback: pyttsx3 offline |
| STT | **Whisper** local | Model `base` default; device `auto` (CUDA if available) |
| STT fallback | Google Web Speech | Needs internet; used if Whisper fails |
| Mode | **Push-to-talk** | CLI: empty Enter or `/listen`. GUI: **Mic** button |

## CLI voice commands

| Input | Effect |
|---|---|
| empty line / `/listen` / `/mic` | Record one phrase |
| `/mics` | List microphone indices |
| `/voice` | Show voice status |
| `/speak on` / `/speak off` | Toggle speaking replies |
| `/voice off` | Stop speaking replies |

## Environment

| Var | Default | Meaning |
|---|---|---|
| `SEVEN_VOICE=1` | off | Enable voice |
| `SEVEN_TTS` | `edge` | `edge` / `pyttsx3` / `none` |
| `SEVEN_EDGE_VOICE` | `en-US-AriaNeural` | edge-tts voice id |
| `SEVEN_WHISPER=0` | on when voice on | Disable Whisper → Google only |
| `SEVEN_WHISPER_MODEL` | `base` | `tiny` / `base` / `small` |
| `SEVEN_WHISPER_DEVICE` | `auto` | `cuda` / `cpu` / `auto` |
| `SEVEN_WHISPER_LANG` | `en` | Whisper language hint |
| `SEVEN_MIC_INDEX` | default | Mic device index from `/mics` |

## PyAudio on Windows

If `pip install pyaudio` fails:

```bat
pip install pipwin
pipwin install pyaudio
```

Or grab a wheel matching your Python version from a trusted wheel index.

## 8GB VRAM note

Whisper `base` on CUDA + Ollama `llama3.2` can coexist; Whisper `small`/`medium` may fight Ollama. Prefer:

- `SEVEN_WHISPER_MODEL=tiny` or `base`
- `SEVEN_WHISPER_DEVICE=cpu` if Ollama needs the GPU

Whisper loads **lazily** on first `/listen` or Mic press.

## Smoke test (no mic required for TTS)

```bat
python -c "from seven.voice.io import VoiceIO; v=VoiceIO(); print(v.status_line()); v.speak('Seven real voice check.')"
```

## Privacy

- No continuous recording
- Audio files are temp WAV/MP3 deleted after use
- Google STT sends audio to Google only if Whisper path fails/unavailable

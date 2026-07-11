# Model & voice choices (4.4.0)

## Brain model (8GB VRAM)

**Primary:** `qwen2.5:7b` (~4.7GB)

Why:
- Strong tool / agent calling vs llama3.2:3b
- Fits RTX-class 8GB with headroom
- Good general conversation + coding

**Auto-select order** (`seven/brain/models.py`):

1. qwen2.5:7b  
2. qwen2.5-coder:7b  
3. qwen3:8b  
4. llama3.1:8b  
5. mistral:7b  
6. llama3.2 / uncensored fallbacks  

Install:

```bat
ollama pull qwen2.5:7b
```

Override: `set OLLAMA_MODEL=...` or `SEVEN_AUTO_MODEL=0` to lock config.

**Vision** still `llama3.2-vision` (heavy — load on demand only).

## Voice

**Default TTS:** Microsoft **en-US-AvaNeural** via edge-tts  
- Natural female neural (not Windows SAPI robotic)  
- Rate `-5%`, pitch `+2Hz` for warmth  

Alternatives (generate previews):

```bat
python scripts/setup_voice_preview.py
```

Files: `%USERPROFILE%\.seven\voice_previews\`  
Also: Emma, Jenny, Michelle, Sonia (UK), Natasha (AU).

Set: `SEVEN_EDGE_VOICE=en-US-EmmaNeural`

## Barge-in

While Seven speaks, mic energy above baseline×`SEVEN_BARGE_SENS` stops playback so you can talk over her.

Disable: `SEVEN_BARGE_IN=0`

## Playwright

```bat
pip install playwright
python -m playwright install chromium
```

`browser_get` uses Playwright when present, else HTTP fetch.

# Seven — Talk (the real product)

You **speak**. She **listens**. She **talks**. She has **free will**.

No `/work`. No `/listen`. No command menu.

## Start

```bat
run_seven.bat
```

or:

```bat
python -m seven --talk
```

**Quiet (no mic/speakers — night mode):**

```bat
run_seven_quiet.bat
python -m seven --quiet
```

Type normally. Empty line = she may take free-will action. Keep Ollama running.

## What happens

1. Seven greets you in her own words  
2. She listens on the mic  
3. You talk  
4. She thinks (may use tools) and speaks back  
5. If you’re quiet, **free will** may:
   - invent a personal goal  
   - work on it with tools  
   - speak a real thought (not empty “how are you”)  

Say **goodbye** / **stop talking** to leave.

## Free will

Controlled by `SEVEN_FREEWILL=1` (default on).

She does **not** need you to type goals. She chooses when to work or speak, using living state (machine health, memory, idle time).

Power-user slash commands still exist for debugging (`--cli`, `/status`) — they are **not** the product.

## Needs

- Mic + speakers  
- `edge-tts`, `pygame`, Whisper or Google STT path (see VOICE.md)  
- Ollama up  

## Background life

```bat
run_seven_daemon.bat
```

Daemon keeps free will ticks going even without the talk window (no speaker unless talk mode registers `on_utter`).

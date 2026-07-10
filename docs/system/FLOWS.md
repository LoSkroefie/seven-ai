# Runtime flows

## Flow A — Quiet companion (night / no mic)

```
run_seven_quiet.bat
  → talk.py quiet=True
  → free will ON, TTS/STT OFF
  → user types natural language
  → empty line → freewill tick (invent/work/speak text)
  → handle() → tools → reply print
```

**Tested:** smoke + unit tests. **Should run tomorrow.**

## Flow B — Voice talk

```
run_seven.bat
  → talk.py quiet=False
  → listen_once → handle → speak
  → silence → freewill may invent/work/speak
```

**Code complete.** Live speech not re-tested while household slept.  
**Needs:** mic privacy, Whisper/PyAudio, edge-tts, Ollama.

## Flow C — Daemon always-on

```
run_seven_daemon.bat
  → runtime/daemon.py
  → heartbeat freewill ticks
  → living_state refresh
  → API :7777
```

**Works** as process. Background speech only if `on_utter` wired (talk mode does).

## Flow D — Tool use inside conversation

```
user message
  → system prompt + living + memory + tools schemas
  → Ollama chat (native tools or text JSON recovery)
  → ToolRegistry.execute
  → audit row
  → final natural language
```

**Verified:** shell, files, python, web, clipboard, screenshot, memory.

## Flow E — Free will

```
decide(idle, living)
  degraded → rest
  open goals → work (run_goal_step)
  no goals + idle → invent_goal (LLM JSON) + first step
  long idle → speak thought
```

**Verified:** invent + work with progress. Quality = model dependent.

## Flow F — Desktop control

```
mouse_click / mouse_move / type_text / hotkey / screenshot / see_screen
```

**Registered.** screen_size/screenshot verified. Clicks not hammered in audit (would move real mouse).

## Failure flows

| Symptom | Recovery |
|---|---|
| Brain error / refused | Start Ollama |
| Hang / Stopping… | Restart Ollama; wait cold load |
| Whisper not installed | quiet mode or fix Python env |
| Tools as prose | parser recovers; if fails, rephrase / use better model |

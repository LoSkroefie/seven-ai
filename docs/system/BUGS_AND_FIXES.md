# Bugs, fixes, watch list

## Fixed this rebuild

| ID | Issue | Fix |
|---|---|---|
| F1 | v3 random.choice “sentience” | Abandoned; real agent loop |
| F2 | Extension/ghost method lies | Legacy only |
| F3 | Empty tool args `""` crash paths | `tools/sanitize.py` |
| F4 | Tool schemas too many for small models | tier core/full (default now **full** per user) |
| F5 | Ollama hang unclear | `/status` + ping hints |
| F6 | History bloat | compact_history |
| F7 | Model emits tool JSON as chat | `_extract_text_tool_calls` + parameters key |
| F8 | Slash-command product UX | talk/quiet free will |
| F9 | No always-on | daemon + autostart |
| F10 | No world/self model | living_state |

## Open bugs / risks

| ID | Severity | Issue | Mitigation |
|---|---|---|---|
| B1 | High | llama3.2 unreliable tool planner | recovery parser; consider uncensored/larger model |
| B2 | High | Free will may attempt huge downloads / heavy shell | user OK with L4; monitor audit |
| B3 | Med | Quiet hours freewill suppress | may feel “dead” at night unless empty-line nudge |
| B4 | Med | Vision + text VRAM thrash 8GB | docs/VISION.md |
| B5 | Med | Daemon speech silent without talk | expected |
| B6 | Med | Windows cmd vs PowerShell | shell tool hints prefix |
| B7 | Low | edge-tts needs network | pyttsx3 fallback |
| B8 | Low | Google STT fallback sends audio off-machine | prefer Whisper |
| B9 | Med | No vector memory | facts LIKE search only |
| B10 | Low | pytest collects only test_seven_real | intentional |

## When something breaks tomorrow

1. `python -m seven --status`  
2. `ollama ps` / restart Ollama  
3. `python -m pytest tests/test_seven_real.py -q`  
4. `python scripts/smoke_companion.py`  
5. Read `~/.seven/seven.log` and `/audit` via quiet chat  

## Do not “fix” by

- Re-enabling v3 emotion/dream random modules  
- Adding confirmation dialogs that block L4  
- Pointing main entry at `_legacy/v3`  

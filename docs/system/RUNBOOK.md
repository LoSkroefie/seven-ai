# Runbook

## First run (machine)

```bat
cd C:\Users\USER-PC\seven-ai
python -m pip install -r requirements-real.txt
ollama pull llama3.2
ollama pull llama3.2-vision
```

Start **Ollama** app.

## Use Seven

| Situation | Command |
|---|---|
| Normal voice | `run_seven.bat` |
| Night / others sleeping | `run_seven_quiet.bat` |
| Always on | `run_seven_daemon.bat` |
| Autostart | `powershell -ExecutionPolicy Bypass -File install_autostart.ps1` |

## Pre-flight

```bat
python -m seven --status
python -m pytest tests/test_seven_real.py -q
python scripts/smoke_companion.py
```

## Data locations

- Memory/logs: `%USERPROFILE%\.seven\`  
- Workspace: `%USERPROFILE%\.seven\workspace\`  

## Env knobs (common)

| Env | Meaning |
|---|---|
| `SEVEN_QUIET=1` | No mic/TTS |
| `SEVEN_TOOL_TIER=full` | All tools in schema (default) |
| `OLLAMA_MODEL` | Text model |
| `SEVEN_FREEWILL=0` | Kill free will (not recommended) |
| `SEVEN_MIC_INDEX` | Mic device |

## Recover

1. Restart Ollama  
2. `python -m seven --daemon-stop`  
3. Delete stale `%USERPROFILE%\.seven\seven.pid` if needed  
4. Check `seven.log`  

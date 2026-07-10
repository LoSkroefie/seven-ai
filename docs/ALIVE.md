# Seven Real — Always-on / “alive” runtime

## What this is

| Layer | Module | Role |
|---|---|---|
| World model | `seven/mind/world.py` | Host, RAM/CPU, Ollama, goals/tasks, failures, time |
| Self model | `seven/mind/self_model.py` | Energy, mode, intent, capabilities |
| Living state | `seven/mind/state.py` | Persisted JSON `~/.seven/living_state.json` |
| Daemon | `seven/runtime/daemon.py` | Process that never exits until stopped |
| Autonomy | `seven/agent/autonomy.py` | Acts using living context |

## Commands

```bat
python -m seven --daemon          # always-on + API
python -m seven --daemon-status
python -m seven --daemon-stop
run_seven_daemon.bat
```

In chat:

```
/world
/self
/live
/status
```

## Autostart (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File install_autostart.ps1
```

Creates a Startup-folder shortcut to `run_seven_daemon.bat`.

## Sense → act → reflect

Each heartbeat:

1. **Sense** world + self  
2. Skip heavy work if `degraded_no_llm` or quiet hours (unless overdue)  
3. **Act** via goal/task autonomy if work exists  
4. **Reflect** into living state + `autonomy` notes  

## Files

| Path | Content |
|---|---|
| `%USERPROFILE%\.seven\living_state.json` | Latest world/self/ticks |
| `%USERPROFILE%\.seven\seven.pid` | Daemon PID |
| `%USERPROFILE%\.seven\seven.db` | Memory |
| `%USERPROFILE%\.seven\seven.log` | Logs |

## Not yet “fully alive”

- No multi-step planner beyond single tool rounds  
- No intrinsic goal generation without user goals  
- No continuous camera/mic (opt-in later)  
- Model quality still bounds planning  

Still: she can **stay running**, **know her situation**, and **act when there is work**.

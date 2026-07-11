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
python -m seven --daemon          # always-on, API off unless configured
python -m seven --daemon --api    # always-on + authenticated loopback API
python -m seven --daemon-status
python -m seven --daemon-stop
python -m seven --daemon-restart
run_seven_daemon.bat
```

In chat:

```
/world
/self
/live
/status
```

## Login startup

```powershell
python -m seven --install-startup
```

The supported login entry starts talk mode so Seven can greet the user. It does not silently substitute daemon mode. `install_autostart.ps1` is a legacy compatibility artifact and is not the supported installer.

For an unattended daemon, run the foreground command under a real user-level service manager (systemd user service, launchd, Windows Task Scheduler, or another supervisor) and configure that manager's restart policy. Seven does not double-fork or falsely claim OS-service installation.

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

The PID file is JSON containing PID, process birth time, start time and Seven version. Status/stop require PID plus matching birth time and a Seven `--daemon` command line, preventing PID reuse or an unrelated process from being killed. Legacy integer PID files are treated as stale and removed without signaling their PID.

`--daemon-stop` is idempotent. It requests graceful termination, waits up to ten seconds, then terminates the owned process tree if required. The PID record is removed only after the daemon is gone. `--daemon-restart` performs that verified stop and then runs the replacement daemon in the foreground.

Logs rotate at 5 MiB with five backups by default. Override byte size with `SEVEN_LOG_MAX_BYTES` and retained backup count with `SEVEN_LOG_BACKUPS`.

## Evidence boundaries

- Daemon lifecycle tests use a real separately launched owned process and prove duplicate rejection, status, stop and unowned-PID protection.
- Log rotation is automated; long-duration memory/model/autonomy soak remains a separate release gate.
- OS service-manager installation/restart matrices remain platform-specific; the foreground daemon is the supported process contract.
- Continuous ambient camera/microphone capture is not enabled by daemon mode.
- Model availability and quality still bound autonomous work.

Seven can stay running, preserve living state, and act when there is real work; those are software/runtime claims, not biological life claims.

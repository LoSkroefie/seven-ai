# Architecture — Seven v4 active package

```
User (voice or quiet type)
        │
        ▼
 seven/ui/talk.py          ← PRIMARY product
        │
        ▼
 seven/agent/loop.py       Seven.handle()
   ├── freewill            mind/freewill.py  (initiative)
   ├── autonomy            agent/autonomy.py (goal steps)
   ├── living              mind/state.py + world + self_model
   ├── brain               brain/llm.py (Ollama / cloud)
   ├── tools               tools/* (L4 executors)
   └── memory              memory/store.py (SQLite)
```

## Directories

| Path | Role |
|---|---|
| `seven/agent/` | Conversation + autonomy |
| `seven/brain/` | LLM providers |
| `seven/mind/` | Free will, world, self, living state |
| `seven/tools/` | All host capabilities |
| `seven/memory/` | Persistence |
| `seven/voice/` | STT/TTS |
| `seven/ui/` | talk, gui, cli, api |
| `seven/runtime/` | Daemon |
| `seven/sensors/` | Camera, presence |
| `seven/embodiment/` | Robot serial bus |
| `seven/identity/` | Soul/identity markdown |
| `_legacy/v3/` | **Dead product** — reference only |

## Data on disk

| Path | Content |
|---|---|
| `~/.seven/seven.db` | messages, facts, goals, tasks, audit, notes |
| `~/.seven/living_state.json` | world/self ticks |
| `~/.seven/seven.log` | logs |
| `~/.seven/seven.pid` | daemon pid |
| `~/.seven/workspace/` | default shell cwd / artifacts |

## Entry points

| Command | Use |
|---|---|
| `python -m seven` / `run_seven.bat` | Talk (voice if possible) |
| `python -m seven --quiet` | Quiet type companion |
| `python -m seven --daemon` | Always-on |
| `python -m seven --gui` | Window |
| `python -m seven --cli` | Power CLI |

## Design laws

1. Companion UX > command console  
2. Free will without slash commands  
3. Real tools only — no fake emotion RNG  
4. L4 execute; audit, don’t nanny  
5. Never grow `_legacy/v3` as product  

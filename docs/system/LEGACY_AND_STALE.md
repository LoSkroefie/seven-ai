# Legacy & stale code map

## Location

Everything abandoned lives under:

```
_legacy/v3/
```

Do **not** import from there in production `seven/`.

## What it was

Seven AI **v3.2.x** (~50k lines): “51 systems”, Phase 5 sentience, Gradio, MCP, NEAT, LoRA theater, many audit markdowns.

## Truth about that tree

| Area | Status |
|---|---|
| Emotion / dream / personality | Heavy `random.choice` fallbacks |
| Extensions | Some real, many soft-fail |
| Goal progress | Often fake increments |
| Docs | Marketing ahead of code |
| Install surface | Messy multi-launcher |

## Valuable scraps to port later (if needed)

| Scrap | Why |
|---|---|
| `integrations/calendar.py` | Google calendar |
| `integrations/email_checker.py` | Email |
| `integrations/ssh_manager.py` | SSH |
| `seven_mcp.py` | MCP exposure |
| `integrations/robotics.py` | Richer robot actions (v4 has thin bus) |
| Whisper rewrites | Already partially absorbed |

## Never port

- Ghost-method-filled “sentience” integrators as marketing  
- Proactive “how are you / system health every 5 min”  
- Sentience score 100/100 docs  

## Restructuring done

- Product = only `seven/`  
- Root README points to talk mode  
- Legacy frozen for archaeology  

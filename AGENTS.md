# AGENTS.md — rules for anyone coding Seven

## Product north star

Seven Real is a **local autonomous agent that executes tools**.  
It is **not** a pile of fake emotion modules, dream templates, or greeting loops.

If a change makes Seven talk more and do less, reject it.

## Package boundaries

| Do | Don't |
|---|---|
| Add features under `seven/` | Grow `_legacy/v3/` or resurrect old main_with_gui |
| Register tools via `ToolRegistry` | Bypass registry without audit |
| Store state in `Memory` / `~/.seven` | Write random JSON under repo `data/` for runtime |
| Document in ROADMAP/HANDOFF when shipping | Leave only chat history as truth |

Legacy code may be **read** to port a real capability. Prefer reimplementation in `seven/tools/`.

## Autonomy & safety

- Default is **L4**: tools run without confirmation dialogs (user request).
- **Always** audit tool calls through `Memory.audit` (already in registry).
- Never add silent `except: pass` around tool failures — return ERROR strings.
- Destructive ops (delete, shell) are allowed; make failures visible in results.

## LLM rules

- Default provider: **Ollama** (`llama3.2` text, `llama3.2-vision` on demand).
- Cloud only with user-provided keys / legitimate CLIs.
- Prefer tool calls over prose plans.
- No `random.choice` for personality / thoughts / goal progress.
- Goal `progress` only after real work (shell/files/code/etc.).

## Style

- Python 3.11+ compatible (user also has 3.13).
- Keep modules focused; avoid another 4000-line god file.
- Optional deps: degrade with clear ERROR, don't crash import of `seven`.
- Empty strings for optional tool args → treat as missing (see `shell.py`).

## Verification gate

Before claiming done:

```bat
python -m pytest tests/test_seven_real.py -q
python -m seven --status
python -m seven -c "Call get_system_info and reply in one sentence."
```

Add tests when you add tools or memory behavior.

## Ollama ops (Windows / 8GB VRAM)

1. `ollama ps` — if stuck Stopping…, restart Ollama  
2. Cold load can take ~60s — timeouts are 300s by design  
3. Don't load vision + large text at once without expecting swap  
4. `keep_alive` is set in brain — don't thrash models every call  

## Docs to maintain

| File | When to update |
|---|---|
| `ROADMAP.md` | Start/finish milestones |
| `HANDOFF.md` | Session end, verified tests, decisions |
| `HANDOFF_PROMPT.md` | Mission or priority changes |
| `SEVEN_REAL.md` | User-facing install/run changes |

## Explicit non-goals (for now)

- Fake sentience scores / audit markdown spam  
- Unauthorized free cloud LLM proxies  
- Re-enabling v3 proactive “how are you” spam  
- Claiming consciousness

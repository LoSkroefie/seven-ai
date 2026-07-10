# Night build — 4.2.0-mind (while user slept)

## Implemented

| Feature | Module / tools |
|---|---|
| Beliefs / opinions | `form_belief`, `list_beliefs`, DB `beliefs` |
| Working memory 7±2 | `wm_push`, `wm_show` |
| Multi-step planner | `create_plan`, `plan_from_goal`, `advance_plan`, `mind/planner.py` |
| Skills library | `save_skill`, `list_skills`, `run_skill` |
| Semantic memory | hashing embeddings `semantic_search`, `index_memory` |
| Episodic digests | `write_digest`, daily auto in heartbeat |
| Preference learning | patterns in chat + `set_preference` |
| Windows list/focus title | `list_windows`, `active_window` |
| Browser get | `browser_get` (Playwright optional), `open_url` |
| Free will → plans | invent goal creates plan + first step |
| Default full tools | already full tier |

## Still future

- Playwright install not bundled  
- OpenSeeFace  
- True continuous screen watcher  
- Windows Service (have Startup shortcut)  
- Perfect tool planning on tiny models  

## Verify

```bat
python -m pytest tests/test_seven_real.py -q
python scripts/smoke_companion.py
```

# Seven AI - Code Audit Log
**Date:** 2026-02-13
**Scope:** Full codebase audit — core modules, sentience systems, GUI, utilities

---

## Bugs Found & Fixed

### CRITICAL — Would crash at runtime

#### 1. `core/affective_computing_deep.py:553` — Mood attribute mismatch
- **Type:** AttributeError (crash)
- **Cause:** `self.current_mood.mood_type` and `self.current_mood.valence` referenced, but `Mood` dataclass has `dominant_emotion` and `intensity`
- **Fix:** Changed to `self.current_mood.dominant_emotion.value` and `self.current_mood.intensity`
- **Impact:** `get_emotional_context_with_complexity()` would crash whenever a mood was active

#### 2. `core/affective_computing_deep.py:629-637` — Dataclass treated as dict
- **Type:** AttributeError (crash)
- **Cause:** `get_recent_emotions()` called `.get()` on `EmotionalState` dataclass objects instead of attribute access
- **Fix:** Changed to proper attribute access with `hasattr` guards (`e.emotion.value`, `e.intensity`, `e.timestamp`, `e.cause`)
- **Impact:** Any call to `get_recent_emotions()` with history would crash

#### 3. `core/enhanced_bot.py:1824` — Dict accessed by integer index
- **Type:** TypeError/KeyError (crash)
- **Cause:** `_summarize_conversation()` used `turn[0]`/`turn[1]` but `get_recent_conversations()` returns `List[dict]`
- **Fix:** Changed to `turn['user_input']`/`turn['bot_response']`
- **Impact:** "Summarize conversation" command would always crash

#### 4. `core/enhanced_bot.py:1365` — Missing None guard on personality
- **Type:** AttributeError (crash)
- **Cause:** `self.personality.get_personality_context()` called without checking if `self.personality` is None (it uses `_safe_init` which returns None on failure)
- **Fix:** Added ternary: `self.personality.get_personality_context() if self.personality else ""`
- **Impact:** If PersonalityEngine init fails, every LLM query would crash

#### 5. `core/enhanced_bot.py:1224` — Missing None guard on calendar
- **Type:** AttributeError (crash)
- **Cause:** `self.calendar` used without None check in calendar command handling
- **Fix:** Added `if self.calendar and` before the calendar condition
- **Impact:** Calendar commands crash if calendar integration isn't available

#### 6. `core/enhanced_bot.py:1234` — Missing None guard on commands
- **Type:** AttributeError (crash)
- **Cause:** `self.commands` used without None check in system command handling
- **Fix:** Wrapped entire command block in `if self.commands:`
- **Impact:** System commands crash if CommandExecutor isn't available

### MINOR

#### 7. `core/voice.py:171` — Redundant import
- **Type:** Code quality
- **Cause:** `import re` inside `_split_sentences()` method, but `re` is already imported at file top (line 6)
- **Fix:** Removed redundant import
- **Impact:** No runtime issue, just unnecessary

---

## Modules Audited (Clean)

| Module | Status | Notes |
|--------|--------|-------|
| `core/dream_system.py` | Clean | Bounded lists, LLM fallbacks |
| `core/intrinsic_motivation.py` | Clean | Bounded lists, save/load |
| `core/promise_system.py` | Clean | Trust scoring correct |
| `core/theory_of_mind.py` | Clean | LLM + keyword fallbacks |
| `core/ethical_reasoning.py` | Clean | Bounded decisions list |
| `core/homeostasis_system.py` | Clean | Bounded maintenance needs |
| `core/emotional_complexity.py` | Clean | Bounded histories |
| `core/metacognition.py` | Clean | Bounded assessment history |
| `core/vulnerability.py` | Clean | Bounded disclosure history |
| `core/vision_system.py` | Clean | Proper threading, bounded scenes |
| `core/voice.py` | Clean (after fix) | |
| `core/memory.py` | Clean | SQLite properly handled |
| `integrations/web_search.py` | Clean | |
| `gui/bot_gui.py` | Clean | Thread-safe, proper None guards |
| `gui/phase5_gui.py` | Clean | Proper widget setup |

### POST-AUDIT — Silent exception blocks replaced with logging

#### 8-14. `core/enhanced_bot.py` — 7 bare `except: pass` blocks (lines 709, 731, 742, 756, 768, 783, 790)
- **Type:** Silent error swallowing
- **Cause:** Bare `except: pass` in main loop subsystems (GUI notifications, emotional memory, self-doubt, emotional contagion, temporal patterns)
- **Fix:** All replaced with `except Exception as e: self.logger.debug(f"<context> error: {e}")` — errors now logged at DEBUG level
- **Impact:** Errors in these subsystems were completely invisible, making debugging impossible

## Observations

- **~~Pattern risk:~~ FIXED:** `enhanced_bot.py` main loop bare `except: pass` blocks — all 7 now log errors at DEBUG level
- **Good pattern:** Almost all sentience modules use bounded lists, LLM + fallback, proper error handling
- **Good pattern:** GUI code consistently uses `hasattr` + None checks before bot access

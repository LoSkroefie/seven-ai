# Memory model

## Implemented

| Layer | Store | Mechanism |
|---|---|---|
| **Short-term** | `messages` table | Recent turns into LLM context (`MAX_HISTORY_TURNS`) |
| **Working (light)** | living_state + last_action | Cross-tick continuity |
| **Long-term facts** | `facts` | `remember_fact` / search LIKE |
| **Goals** | `goals` | free will + tools |
| **Tasks** | `tasks` | todos / due |
| **Episodic-ish** | `notes` + compaction | session.compact fact |
| **Procedural audit** | `audit` | every tool call |

## Not implemented yet

| Layer | Purpose |
|---|---|
| Vector semantic | “what did we discuss about X months ago” |
| Belief/opinion graph | durable stances with evidence |
| Skill recipes | reusable multi-tool procedures |
| Emotional memory | intentionally not faked; can add *real* preference tags later |

## Design rule

Memory must be **written from real events** (tools, user speech, free will actions) — never random emotion injection.

## Compaction

When message count ≥ `COMPACT_AFTER_MESSAGES` (30), older turns fold into a fact and drop from chat table.

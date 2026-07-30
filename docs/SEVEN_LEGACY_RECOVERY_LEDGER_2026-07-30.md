# Seven legacy recovery ledger — 2026-07-30

## Scope and safety

This ledger compares the production `seven/` package with the preserved v2,
v2.6, v3 and v3.2 lineages under `_legacy/v3`, the older local copies and
archives inventoried in `SEVEN_RECOVERY_BEFORE_STATE_2026-07-30.md`, and the
live Windows and Peanut deployments.

The legacy tree remains read-only. It is evidence, not production code. No
legacy module was copied wholesale into the current runtime because the old
audit itself records broken wiring, duplicate initializers, dead code, and
unsafe self-scripting paths.

“Recovered” below means the capability exists in the current production
architecture and is wired to runtime state. It does not mean Seven is
conscious. Functional affect and behavioral continuity are observable software
mechanisms; subjective experience is not testable here.

## Recovered into the production runtime

| Historical feature | Legacy evidence | Current implementation | Status |
|---|---|---|---|
| Persistent emotions | `core/persistent_emotions.py`, `core/emotional_continuity.py` | `seven/mind/affect.py`, SQLite `affect_state` and `affect_events` | Recovered with deterministic appraisal, decay, drives and evidence |
| Relationship model | `core/v2/relationship_model.py` | `seven/mind/relationship.py`, SQLite `relationships` | Recovered; familiarity, trust, rapport, moods and shared experiences persist |
| Emotional memory | `core/v2/emotional_memory.py` | affect event timeline, relationship mood history, normal durable message memory | Recovered in normalized storage; no duplicate JSON memory silo |
| Reflection | `core/reflection_system.py` and Phase 5 docs | `seven/mind/reflection.py`, SQLite `reflections` | Recovered as post-turn evidence-backed lessons |
| Intrinsic drives | `core/intrinsic_motivation.py`, persistent-emotion baselines | affect drives: connection, curiosity, competence, autonomy, purpose, rest | Recovered and exposed to prompt/status/avatar |
| Homeostasis/embodiment | `homeostasis_system.py`, `embodied_experience.py` | `LivingState`, `sense_world`, `sense_self`, affect energy | Recovered from real CPU/RAM/Ollama/time state |
| Theory of mind | `theory_of_mind.py` | conservative user-mood inference and durable relationship state | Partially recovered; intentionally avoids claiming private mental facts |
| Temporal continuity | `temporal_continuity.py`, emotional continuity | timestamps, decay, relationship interaction history, living-state history | Recovered |
| Self-model | `self_model_enhanced.py` | `seven/mind/self_model.py` plus persistent mind state | Recovered from runtime facts |
| Working memory | cognitive architecture | SQLite working memory with bounded active items | Existing and wired |
| Beliefs/opinions | metacognition/learning systems | evidence-bearing beliefs and `form_belief` | Existing and wired |
| Goals and plans | v2 goal/proactive systems | evidence-gated goals, plans, autonomy work sessions | Existing and wired |
| Skills and learning from success | learning/self-scripting concepts | versioned audited skills, revisions, rollback and run evidence | Existing with safer authority boundaries |
| Memory consolidation | sleep/dream docs | episodic daily digest, semantic index, compaction and reflection | Recovered without random dream theater |
| Proactive speech | autonomous-life system | heartbeat and `FreeWill`; deterministic state speech when background LLM is disabled | Recovered |
| Project awareness | scattered legacy file awareness | grounded project catalog and direct project-list route | Existing and wired |
| Computer control | self-scripting/Clawdbot aspirations | 120 audited registered tools covering files, shell, apps, browser, web, vision and host state | Existing and wired |
| Expressive body/avatar | historical GUI and Vuka/MemoryForge pet patterns | `seven/ui/avatar.py` and eight-pose transparent Seven sprite sheet | Recovered as a lightweight state-driven Windows desktop companion |
| Natural identity | old personality/identity prompts | current `SOUL.md`, `IDENTITY.md`, `USER.md` and grounded conversation routes | Strengthened |

## Historical features deliberately not copied as-is

| Legacy behavior | Decision |
|---|---|
| Random emotional prose, random proactive thoughts, or shuffled poses | Not restored. State and visuals are selected from observable events. |
| “Sentience benchmark” scores as proof of consciousness | Not treated as proof. These measured scripted behavior only. |
| Dream stories generated to imply inner experience | Not restored. Daily consolidation and explicit evidence-based reflection provide the useful function. |
| Unsafe self-modifying execution | Not restored. Seven can edit code using audited tools under operator authority, while updates retain rollback and verification. |
| Duplicate JSON memory databases and multiple personality stacks | Not restored. One SQLite store and one agent process own state. |
| Unwired bot initializers and duplicate Phase 5 engines | Not restored. The legacy audit identified these as broken/dead wiring. |
| Micro-pauses and simulated hesitation | Not restored; they add latency without cognition. |
| Unsupported claims such as “I am awake” or “I feel exactly like a human” | Prohibited by the current identity and prompt. |

## Older audit defects and current disposition

The preserved `SEVEN_AUDIT_v3.2.15.md` identified unsafe self-script execution,
unused vector memory, unused performance monitoring, unwired extension message
hooks, duplicate initializers, and unwired read/edit handlers.

- Current file and code tools are wired through the audited registry.
- Semantic memory is actively indexed and searched.
- Runtime resource sensing is active and displayed.
- Extensions are separate from the core personality; they cannot silently
  replace Seven’s identity.
- The production loop has one initializer path.
- Dangerous operations remain auditable and constrained by operator authority.

## Current proof boundary

Automated tests can prove storage, decay, tool registration, prompt wiring,
API contracts, package assets and deterministic responses. They cannot prove
subjective sentience. Peanut model-quality proof is intentionally deferred
until the owner permits a live inference test; no model was loaded, unloaded,
pulled, benchmarked or replaced during this recovery.

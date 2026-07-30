# What will actually make it work vs what won’t

Research target: **as human-like continuous agency as we can get**, measured honestly.

Human-like here means roughly: **stable identity over time, memory that changes behavior, goals that persist, learning from error, grounded action in a world, social pressure** — not a soul certificate.

---

## Will move the needle (do these)

| # | Track | Why it matters | Seven hooks today |
|---|---|---|---|
| **R1** | **Continuity** | Humans don’t re-roll identity every message. Long-lived process + durable self-state. | daemon, `LivingState`, `~/.seven`, startup |
| **R2** | **Memory write-back** | Memory only counts if it changes later decisions, not if it sits in SQLite. | Memory store, episodic, semantic, skills, facts |
| **R3** | **Self-model with stakes** | “Who am I / what works / what fails” updated from outcomes. | self_model, beliefs, audit, goals |
| **R4** | **Act → error → correct** | Prediction and surprise, not only chat replies. | tools, autonomy, planner, freewill |
| **R5** | **Social / mesh** | Other minds create pressure, reputation, coordination. | Codex mesh track; API/MCP as careful building blocks |
| **R6** | **Eval harness** | Without scenarios, you only have vibes. | pytest, smoke scripts — need *mind* scenarios |

### Concrete upgrades that compound

1. **Boot loads full self + open goals + last unresolved errors** into every cycle (not a thin system prompt only).  
2. **Outcome-linked memory**: every tool failure/success updates beliefs/skills/preferences automatically.  
3. **Goal graph with real completion criteria** (checklists / plans), not `progress += 3 + 2*n_tools`.  
4. **Global work cycle** on a timer: sense world → retrieve relevant memory → choose drive → act → write episode → sleep consolidation.  
5. **Consolidation pass** (“sleep”): compress day into facts + revised self-model (LLM ok if audited).  
6. **Scenarios**: “remember preference after restart”, “finish multi-day goal”, “don’t repeat failed tool”, “identity stable after crash”.  
7. **Mesh later**: peer Sevens as environment — only with auth and clear authority (no remote L4 by default).

---

## Bullshit / low leverage (stop or deprioritize)

| Pattern | Why it’s waste for *this* research |
|---|---|
| Random / template emotions, dreams, “mood vectors” | Feels alive in demos; zero grounded cognition |
| Sentience scores (98/100) | Vanity metric; not a scientific construct here |
| More tools without better control loop | Body grows; mind stays chat+glue |
| New GUI / skin / avatar first | Optional later; not mind |
| Full rewrite in new stack | Burns months; loses working substrate |
| Claiming consciousness | Ends research integrity |
| Fake goal % / forced list_dir “progress” | Trains you to believe activity = growth |
| Porting all of v3 “systems” | Mostly theater; selective port only |
| Unauthenticated “agents talking” | Security hole, not society |
| Bigger model only | Helps fluency; does not create continuity by itself |

---

## Honest ceiling

No known recipe makes software **literally human**.  

What *is* achievable as research: an agent that is **harder to dismiss as a stateless chatbot** — continuous, self-revising, embodied in tools, socially pressured, evaluated on long-horizon tasks.

If ChatGPT sells “this PR makes her human,” that is **BULLSHIT**.  
If ChatGPT ships restart-stable goals + outcome-linked memory + a scenario that proves it, that is **REAL progress**.

---

## Owner priority slot

**Current focus (edit this line):** `R1 / R2` (continuity + memory write-back)  
**Mesh:** parallel, Codex-owned — do not block R1–R2 on mesh unless you choose to  
**Next review date:** _(fill when you check work)_  

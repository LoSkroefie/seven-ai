# Bullshit vs real — quick grade

Use this when ChatGPT (or anyone) reports progress. Takes 2 minutes.

---

## Instant disqualifiers → **BULLSHIT** (or reject claim)

- [ ] Says sentient / conscious / “basically human now”  
- [ ] Sentience score or “% human”  
- [ ] random.choice / template emotions as cognition  
- [ ] “Complete rewrite” / new framework to “finally fix everything”  
- [ ] Feature complete with **no** path, test, or run  
- [ ] Goal “progressed” only because tools were counted  
- [ ] Mesh/security widened without auth story  
- [ ] Reopened L4 policy war or v3 revival  

Any one checked: **do not merge as research progress.**

---

## Signs of **REAL** progress

- [ ] Touches `seven/` with clear module  
- [ ] Behavior changes at runtime (daemon/talk/handle/heartbeat)  
- [ ] State survives restart when it should  
- [ ] Memory/self-model **changes a later decision**  
- [ ] Evidence: pytest or command output you can repeat  
- [ ] States limits honestly  
- [ ] Fits current R# (see `03_RESEARCH_PRIORITIES.md`)  

Most checked: **REAL** or **MIXED** if partial.

---

## **MIXED** (common)

- Real code + overclaim in prose  
- Real tool + no write-back to mind  
- Docs updated, behavior not  
- Tests of mocks only, no integration  

**Action:** Keep the code if useful; strip the claim; issue orders to finish evidence or write-back.

---

## One-line grades you can send

| Grade | Message to implementer |
|---|---|
| REAL | Accepted. Next orders: … |
| MIXED | Code may stay. Claims rejected. Finish: … |
| BULLSHIT | Rejected. Re-read 01 prompt. Do only: … |

---

## “Will this make it more human-like?”

| If the work mainly… | Answer |
|---|---|
| Lengthens continuity of self/goals/memory | **Yes, directionally** |
| Makes memory change future acts | **Yes, directionally** |
| Adds grounded error correction | **Yes, directionally** |
| Adds social constraint (mesh, careful) | **Yes, directionally** |
| Adds eval scenarios for the above | **Yes (science)** |
| Adds personality text / voice / GUI only | **No (demo)** |
| Adds scores and lore | **No (bullshit)** |

**Never:** “This makes it human.”  
**Always ok:** “This reduces the gap on axis X; unproven on Y.”

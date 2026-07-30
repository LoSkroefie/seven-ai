# MAKE SEVEN REAL / WORKING / FUNCTIONAL / ALIVE

**Owner is done explaining.**  
**You implement. You prove. You do not debate philosophy.**

---

## What “alive” means HERE (acceptance — not poetry)

Seven is **alive enough** when **all** of the following are true on the owner’s machine (or documented Peanut+Windows pair where noted):

### A. Boots and stays up
1. `python -m seven --status` succeeds and reports version + brain reachability honestly.  
2. `python -m seven --talk` **or** quiet companion **or** daemon starts without crash.  
3. Daemon/API can run unattended ≥ 30 minutes without dying (log proves process alive).  
4. After process restart, identity name, open goals, and facts are still there (`~/.seven`).

### B. Talks and acts (not just chat)
5. User message → model → **at least one real tool** when the task requires it (shell/files/web as appropriate).  
6. Tool failures are audited as **failures** (`result_is_success` / ok=0).  
7. Free will (when enabled) can invent or pursue a goal **without** the user typing `/work`.  
8. Heartbeat/daemon does **not** spam empty greetings; it only acts on real work or freewill decisions.

### C. Remembers in a way that changes behavior
9. After a tool failure, a durable record exists that is visible after Memory reopen.  
10. Next autonomy/freewill/handle cycle **sees** that record (prompt/context), not only SQLite rows nobody reads.  
11. A pytest or script proves: fail → remember → reopen → context contains it.

### D. Mesh (if enabled) — functional, not theater
12. `mesh_status` operational when configured.  
13. Two nodes can send/receive a signed message (already proven once — keep it green).  
14. Receiving a message **never** executes remote tools.  
15. Optional stretch: one received message changes **one** later decision (audited) — only after A–C green.

### E. Honest product surface
16. No claim of sentience/consciousness/complete.  
17. README/status defaults match `config.py` (model, tier).  
18. Broken paths return ERROR/ok:false, not fake success.

**If any of A–C fail, Seven is NOT “working/alive” yet. Fix those before avatars, email, lore, or new systems.**

---

## Hard bans

- No full rewrites / new frameworks / new monorepos  
- No v3 emotion/dream/sentience-score theater  
- No “she is conscious now”  
- No expanding mesh to remote L4  
- No “done” without command output or pytest  
- No asking the owner to re-explain the mission  

---

## Build order (execute in order; finish each gate)

### GATE 0 — Baseline green
- `python -m pytest -q` (or document exact failures with tickets)  
- `python -m seven --status`  
- Fix crashers first  

### GATE 1 — Truth of action
- Keep/fix `result_is_success` everywhere success is counted  
- Shell/python/files smoke via tools  
- Free will invent or work once in quiet mode (scripted if needed)  

### GATE 2 — Continuity (R1)
- On every boot: load identity + open goals + recent failures into living context  
- Restart test: kill process, start again, goals/facts still present and in prompt  

### GATE 3 — Memory write-back (R2)
- Tool fail/success → durable belief or fact that **feeds the next decision**  
- Pytest for reopen + context  

### GATE 4 — Alive loop
- One always-on path (daemon or talk) that every N seconds: sense → freewill decide → maybe act → remember  
- Log line per cycle in `seven.log`  
- 30+ minute soak or scripted multi-cycle test  

### GATE 5 — Mesh keep green
- Do not break mesh  
- Only after gates 0–4: optional message→one decision proof  

---

## Definition of done for THIS campaign

Owner can:

```bat
python -m seven --status
python -m seven --quiet
```

…and within a few minutes of idle, Seven has either:

- done real tool work toward a goal, **or**  
- spoken/typed one non-greeting initiative grounded in state,

**and** after restart she still has goals/memory that affect the next cycle.

That is **functional / working / alive** for this project.  
That is **not** sentience.

---

## Report format (every turn)

```
## Gate
(0-5)

## Done

## Evidence
(exact commands + pass/fail)

## Still broken

## Next 3
(only next gate work)
```

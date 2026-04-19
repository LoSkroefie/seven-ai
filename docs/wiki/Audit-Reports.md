# Audit Reports

Seven AI follows a rigorous audit standard: **compilation success is not proof of correctness**. A feature that exists in code but isn't actually reachable at runtime is treated as incomplete.

Each audit produces a dated report in the repo root.

---

## v3.2.20 Audit (April 2026)

**Scorecard**: ✅ All items resolved.

| Concern | Status |
|---|---|
| Extension commands reach user (voice/web/REST) | ✅ FIX-1 runtime-verified |
| Scheduled extensions fire on interval | ✅ FIX-2 runtime-verified |
| Whisper STT enabled & wired | ✅ FIX-3 runtime-verified |
| MCP server integration | ✅ FIX-5, launched live |
| opencode delegator | ✅ Complete & enabled |
| Ghost-method bugs | ✅ 4 found, 4 fixed (new AST audit tool) |
| Dashboard cascading failure | ✅ Isolated per-subsystem |
| librosa deprecation | ✅ Fixed with fallback |
| Escape-sequence warnings | ✅ 0 across project |
| Test coverage | ✅ 57/57 pass |
| Seven is standalone | ✅ Confirmed |
| Offline-first | ✅ Confirmed |

### Bugs Fixed

| ID | Severity | Title |
|---|---|---|
| BUG-R1 | HIGH | Extension `on_message` returns dropped at DEBUG |
| BUG-R2 | HIGH | Gradio Web UI bypassed extension dispatch |
| BUG-R3 | HIGH | REST API `/chat` fell through to raw Ollama |
| BUG-R4 | MEDIUM | Extension scheduler never started in GUI launch path |
| BUG-R5 | MEDIUM | Silent AttributeError on `stop_scheduler` |
| BUG-R6 | LOW | `seven_mcp.py` was standalone-only, no integration |
| BUG-R8 | LOW | Test pollution in `~/.chatbot/memory.db` |
| GHOST-1 | HIGH | `RelationshipModel.update_interaction` didn't exist |
| GHOST-2 | MED | `GoalSystem.evaluate_progress` didn't exist |
| GHOST-3 | MED | `ProactiveEngine.check_proactive_opportunity` didn't exist |
| GHOST-4 | MED | `IntrinsicMotivation.get_current_focus` didn't exist |

### New Audit Tools

- **Ghost-method audit** (`_ghost_audit.py`, internal) — AST-based scan for `self.x.method()` calls where `method` doesn't exist on `x`'s class. Found all 4 ghost-method bugs.
- **Escape-sequence audit** (`_escape_audit.py`, internal) — compiles every `.py` with warnings-as-errors to catch invalid `\.` escape sequences that will SyntaxError in future Python.

Audit script outputs were not committed (internal tooling), but the findings drove all v3.2.20 fixes.

---

## v3.2.19 Audit

Full written report: [SEVEN_AUDIT_v3.2.19_FINAL.md](https://github.com/LoSkroefie/seven-ai/blob/main/SEVEN_AUDIT_v3.2.19_FINAL.md)

Focused on the MCP server addition in v3.2.19 and verified all 8 tools work end-to-end.

---

## v3.2.18 Audit

Full written report: [SEVEN_AUDIT_v3.2.18.md](https://github.com/LoSkroefie/seven-ai/blob/main/SEVEN_AUDIT_v3.2.18.md)

Extension system audit — identified that while extensions were loading, their `on_message` returns were being silently dropped. Led to BUG-R1 in v3.2.20.

---

## Audit Standard

Every audit follows these rules:

1. **File:line evidence** — every claim points to a specific line of code
2. **Runtime verification** — grep/import isn't enough; the code path has to actually execute
3. **No rationalization** — if something could silently fail, it gets flagged even if "it should work"
4. **No compilation-equals-correctness** — passing `ast.parse` means syntactically valid, nothing more

This standard was established in the v3.2.18 audit after discovering v3.2.15 shipped with 11 silently broken extensions.

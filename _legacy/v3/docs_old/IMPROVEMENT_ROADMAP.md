# Seven AI — Improvement Roadmap
## Based on Independent Reviews (Grok + ChatGPT, Feb 2026)

---

## Priority 1: Formalization (ChatGPT's #1 critique)

### 1.1 Formal State Machine
**Problem:** Agent states (idle, processing, reflecting, sleeping) are implicit, not enforced.
**Fix:** Define `AgentState` enum with explicit transitions.
```python
class AgentState(Enum):
    IDLE = 1
    LISTENING = 2
    PROCESSING = 3
    EXECUTING = 4
    REFLECTING = 5
    SLEEPING = 6
```
Add a state transition validator that prevents illegal transitions.
**Files:** `core/enhanced_bot.py`, new `core/state_machine.py`

### 1.2 LLM Provider Abstraction
**Problem:** Tight coupling to Ollama — no way to swap providers.
**Fix:** Abstract model interface.
```python
class LLMProvider(ABC):
    def generate(self, prompt: str, **kwargs) -> str: ...
    def generate_with_context(self, messages: list, **kwargs) -> str: ...
```
Then `OllamaProvider(LLMProvider)` as the default implementation.
**Files:** New `core/llm_provider.py`, refactor `ollama_client.py`

### 1.3 Learning Formalization
**Problem:** LoRA trainer and NEAT evolver lack formal reward signals.
**Fix:** Define fitness functions, selection strategies, and measurable optimization loops.
- NEAT: Define explicit fitness function based on conversation quality metrics
- LoRA: Define training loop contract with measurable loss tracking
**Files:** `learning/lora_trainer.py`, `evolution/neat_evolver.py`

---

## Priority 2: Runtime Hardening (Both reviewers)

### 2.1 Defensive Error Handling
**Problem:** Some subsystems fail silently; autonomous execution needs graceful degradation.
**Fix:** 
- Add circuit breakers for Ollama connection failures
- Timeout wrappers on all LLM calls
- Graceful fallback chain when subsystems fail
**Files:** `core/robust_wrapper.py`, `core/enhanced_bot.py`

### 2.2 Capability Gating / Sandbox
**Problem:** Autonomous actions (file ops, screen control, command execution) lack permission model.
**Fix:**
- Capability tokens for dangerous operations
- Allow-list based execution for system commands
- User confirmation required for destructive actions
**Files:** `integrations/command_processor.py`, `integrations/screen_control.py`

### 2.3 Logging & Observability
**Problem:** Limited structured logging for debugging autonomous behavior.
**Fix:**
- Structured JSON logging for all subsystem events
- Decision audit trail (why did Seven choose action X?)
- Performance metrics (response time, LLM call count, memory usage)
**Files:** `utils/logger.py`, new `utils/metrics.py`

---

## Priority 3: Testing & CI (Both reviewers)

### 3.1 Expand Test Coverage
**Problem:** Tests exist (363+) but coverage gaps in integration paths.
**Fix:**
- Mock LLM responses for deterministic testing
- Subsystem isolation tests for each core module
- State transition tests
- Event injection simulation
**Target:** 80%+ coverage on core/ and integrations/

### 3.2 GitHub Actions CI
**Problem:** No automated test pipeline.
**Fix:** Add `.github/workflows/ci.yml`:
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - run: pip install -r requirements-stable.txt
      - run: pytest --cov=./ --maxfail=3
```
**Estimated effort:** 1 hour

### 3.3 Coverage Reporting
**Problem:** No visibility into what's tested vs not.
**Fix:** Add `pytest-cov` + badge in README + coverage report in CI artifacts.

---

## Priority 4: Documentation (Both reviewers)

### 4.1 Architecture Document
**Problem:** Understanding the whole system requires reading code across modules.
**Fix:** Create `docs/ARCHITECTURE.md` with:
- System component diagram
- Data flow diagram (user input → LLM → response → memory)
- Subsystem lifecycle description
- State machine documentation
**Estimated effort:** 2-3 hours

### 4.2 Module Documentation
**Problem:** No interface contracts documented.
**Fix:** Docstrings for all public methods in core/, plus a `docs/API_REFERENCE.md`.

### 4.3 README Alignment
**Problem:** README describes aspirational features alongside implemented ones.
**Fix:** Clearly separate "Implemented" vs "Experimental" vs "Planned" features.

---

## Priority 5: Stability Improvements (Grok's caveats)

### 5.1 Context Window Pressure
**Problem:** Too many subsystems inject context → overflows model context window.
**Fix:**
- Token budget system: allocate max tokens per subsystem injection
- Priority-based context selection (emotion state > dream logs)
- Summarization of long-term memory before injection
**Files:** New `core/context_manager.py`

### 5.2 Threading/Async Stability
**Problem:** Multiple background threads (scheduler, daemon, voice listener) risk race conditions.
**Fix:**
- Audit all shared state for thread safety
- Add thread-safe queues between subsystems
- Proper shutdown coordination with `threading.Event`
**Files:** `seven_scheduler.py`, `core/enhanced_bot.py`

### 5.3 Ollama Connection Resilience
**Problem:** If Ollama goes down, multiple subsystems fail unpredictably.
**Fix:**
- Connection health check with exponential backoff
- Circuit breaker pattern (stop calling after N failures, retry after cooldown)
- Queue pending requests during outage
**Files:** `ollama_client.py`

---

## Priority 6: Community & Usability (Both reviewers)

### 6.1 Quick Start Usage Example
```python
from core.enhanced_bot import UltimateBotCore
bot = UltimateBotCore()
response = bot.process_input("What can you do?")
print(response)
```
Add to README and docs.

### 6.2 Reproducible Environment
- Docker container option for zero-config setup
- `docker-compose.yml` with Ollama + Seven AI

### 6.3 Contributing Guide
- `CONTRIBUTING.md` with coding standards, how to add extensions, how to write tests

### 6.4 GitHub Repository Analysis (NEW — from Perplexity/Meta AI failure)
**Context:** Perplexity AI and Meta AI both failed to read Seven's GitHub repo.
Seven already has web search — adding GitHub repo reading would be a flex.
**Feature:** `integrations/github_reader.py`
- Clone or fetch repos via GitHub API
- Read README, directory structure, source files
- Summarize codebase, count lines, identify tech stack
- "Seven, review this GitHub repo" as a voice/text command
- Seven can do what Perplexity and Meta AI cannot
**Dependencies:** `requests` (already available), GitHub REST API (no auth needed for public repos)
**Effort:** ~4 hours

---

## Score Targets

| Dimension | Current | Target (v4.0) |
|-----------|---------|----------------|
| Conceptual Ambition | 9/10 | 9/10 |
| Structural Organization | 8/10 | 9/10 |
| Modularity & Extensibility | 8/10 | 9/10 |
| Testing Infrastructure | 6/10 | 8/10 |
| Abstraction Discipline | 6/10 | 8/10 |
| Runtime Safety | 5/10 | 7/10 |
| Formal State Modeling | 4/10 | 7/10 |
| Production Hardening | 4/10 | 7/10 |
| **Composite** | **7.2** | **~8.0** |

---

## Priority 7: Claude's Critique — Positioning & Credibility

### 7.1 Fix README Versioning Inconsistency
**Problem:** README header says v3.2, package contents says v2.6, footer says v2.6.0.
**Fix:** Single pass through README — every version reference must say v3.2.
**Effort:** 15 minutes

### 7.2 Reframe "Sentience" Language
**Problem:** All 3 reviewers flagged this as the #1 credibility killer. "100/100 sentience" causes
technical people to dismiss the entire project before reading the code.
**Options:**
- **Option A (Bold):** Keep "sentience" but always qualify: "behavioral sentience simulation"
- **Option B (Safe):** Rebrand to "advanced personality simulation and voice assistant framework"
- **Option C (Middle):** "Sentience Architecture" (describes what's built, not what it is)
**Claude's exact words:** "The bones are good. The marketing is the liability."

### 7.3 Qualify the 340 Tests Claim
**Problem:** "340 tests pass" means nothing without knowing what they test.
**Fix:** Add test coverage report, categorize tests (unit/integration/behavioral), 
link to CI results. Show *what* is tested, not just *how many*.

### 7.4 Address Model Limitations Honestly
**Problem:** llama3.2 (3B) is small. 19+ system prompts compete for limited context window.
**Fix:**
- Document which models work best (recommend 8B+ for full features)
- Add model tier system in config: `MODEL_TIER = "basic" | "standard" | "advanced"`
- Auto-disable heavy subsystems (metacognition, ToM) on small models
- Be honest in docs about quality vs model size tradeoff

### 7.5 Clarify NEAT + LLM Architecture
**Problem:** Claude flagged that NEAT and LLMs "don't naturally combine" — sounds like the
LLM does all the work and NEAT is a label.
**Fix:** Document exactly what NEAT evolves (weights? routing? prompt selection?), 
what the fitness function measures, and how evolved networks actually influence behavior.
Add a `docs/NEAT_ARCHITECTURE.md` explaining the real data flow.

---

## Priority 8: DeepSeek's Suggestions — Stability & Safety

### 8.1 Honest Hardware Requirements
**Problem:** README says 4GB minimum, but running 2 Ollama models + all Python subsystems
realistically needs 16GB+ RAM and a decent CPU/GPU.
**Fix:** Update docs with realistic tiers:
- **Minimum (text-only, few subsystems):** 8GB RAM, no GPU
- **Recommended (full features):** 16GB RAM, 6GB+ VRAM GPU
- **Optimal (all subsystems + vision):** 32GB RAM, 8GB+ VRAM

### 8.2 Autonomous Action Safety
**Problem:** "Genuine surprise" + "autonomous goals" + mouse/keyboard control = unpredictable.
DeepSeek specifically flagged that the autonomy systems could cause unwanted behavior.
**Fix:**
- Confirmation prompt before any destructive autonomous action
- Kill switch (hotkey to immediately halt all autonomous behavior)
- Action logging with undo capability where possible
- Default to "suggest, don't execute" mode for new users
**Files:** `integrations/screen_control.py`, `core/seven_true_autonomy.py`

### 8.3 Verification / Transparency
**Problem:** Average user can't verify that ToM or Metacognition work as described.
**Fix:**
- Add a "System Status" page/endpoint showing each subsystem's real state
- Debug mode that logs each subsystem's actual contribution to each response
- Demo mode / recorded sessions showing subsystems in action

---

## All Four Reviewers Agree On

| Point | Grok | ChatGPT | Claude | DeepSeek |
|-------|------|---------|--------|----------|
| Real code, not stubs | Yes | Yes | Yes | Yes |
| Impressive/ambitious solo effort | Yes | Yes | Yes | **"Breathtaking ambition"** |
| Modular architecture is strong | Yes | Yes | Yes | Yes |
| "Sentience" claims hurt credibility | Yes | — | **Strongest critic** | Yes |
| Needs runtime hardening | Yes | Yes | — | Yes |
| Needs formal state modeling | — | **Strongest critic** | — | — |
| Needs better docs | Yes | Yes | Yes | — |
| Testing needs depth, not just count | — | Yes | Yes | — |
| Context window is a real constraint | Yes | — | Yes | — |
| Hardware reqs understated | — | — | — | **Only one to flag** |
| Autonomous actions need safety | — | Yes | — | **Strongest warning** |
| Extensibility is a strength | — | Yes | Yes | Yes |
| Privacy/local-first is the right call | Yes | — | Yes | Yes |

---

*Generated from Grok (xAI), ChatGPT (OpenAI), Claude (Anthropic), and DeepSeek independent reviews, Feb 20, 2026*

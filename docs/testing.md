# Testing Guide

Seven has 340 tests across 4 test suites, covering all 19 sentience systems and core functionality.

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test suite
pytest tests/test_seven_complete.py        # 234 tests — core systems
pytest tests/test_v26_sentience.py         # 106 tests — v2.6 sentience
pytest tests/test_core_systems.py          # Unit tests
pytest tests/test_phase4_identity.py       # Identity system

# Run tests matching a pattern
pytest -k "emotion"
pytest -k "dream"
pytest -k "theory_of_mind"
```

## Test Suites

### `test_seven_complete.py` (234 tests)

Comprehensive tests for all core systems:
- Cognitive architecture pipeline
- All 35 emotions (creation, decay, interaction)
- Self-model updates
- Memory storage and retrieval
- Knowledge graph operations
- Conversation analysis
- Session management
- Personality consistency
- Context cascade
- Tool library
- Command system

### `test_v26_sentience.py` (106 tests)

Tests specific to v2.6 sentience architecture:
- Persistent emotion storage and retrieval
- Genuine surprise detection
- Embodied experience simulation
- Multimodal emotion bridge
- Temporal continuity across sessions
- Emotional memory tagging
- Relationship model dynamics
- Learning system adaptation
- Proactive engine triggers
- Goal system planning
- Dream system insight generation
- Promise tracking and fulfillment
- Ethical reasoning decisions
- Metacognition quality monitoring

### `test_core_systems.py`

Unit tests for individual modules:
- Config loading
- Database operations
- Helper utilities
- Logger setup

### `test_phase4_identity.py`

Identity and personality system tests:
- Structured identity persistence
- Personality trait consistency
- Identity commands
- Name and instance management

## Test Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

## Writing New Tests

Tests follow standard pytest conventions:

```python
# tests/test_example.py
import pytest
from core.affective_computing_deep import AffectiveSystem

class TestEmotions:
    def setup_method(self):
        self.affect = AffectiveSystem()

    def test_joy_triggers_on_positive_input(self):
        self.affect.process_event("positive_interaction")
        assert self.affect.get_emotion("joy").intensity > 0.3

    def test_emotions_decay_over_time(self):
        self.affect.set_emotion("anger", 0.8)
        self.affect.tick()  # One decay cycle
        assert self.affect.get_emotion("anger").intensity < 0.8
```

## Test Dependencies

Most tests are self-contained and don't require:
- A running Ollama instance
- A microphone or speakers
- A camera
- Network access

Tests that require external resources are marked and will skip gracefully if unavailable.

## Continuous Integration

For CI environments:

```bash
# Install test dependencies
pip install pytest

# Run tests with exit code
pytest --tb=short -q
```

Expected output: `340 passed` (may vary slightly based on environment).

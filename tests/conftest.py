"""
Seven AI - Test Configuration

Adds project root to sys.path so tests can import core/, integrations/, utils/.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# -------------------------------------------------------------
# FIX-4: These files are standalone test runners (use a custom
# TestTracker class, run directly via `python tests/<file>.py`).
# They are NOT pytest-compatible and break collection when pytest
# tries to pick up their `test_*` helper functions. Skip them
# during pytest collection — they can still be run directly.
# -------------------------------------------------------------
collect_ignore_glob = [
    "test_v26_sentience.py",
    "test_seven_complete.py",
]

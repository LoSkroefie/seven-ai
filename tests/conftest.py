"""
Seven AI - Test Configuration

Adds project root to sys.path so tests can import core/, integrations/, utils/.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

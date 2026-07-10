"""
Clipboard History — Seven AI

Extends the existing clipboard monitor to keep a history of the last N
clipboard entries, not just the current one. Provides search and recall.
"""

import logging
import threading
import time
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict

logger = logging.getLogger("ClipboardHistory")

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


class ClipboardHistoryManager:
    """Track clipboard history with search and recall"""

    def __init__(self, max_entries: int = 50, poll_interval: float = 1.0):
        self.available = HAS_PYPERCLIP
        self.max_entries = max_entries
        self.poll_interval = poll_interval
        self.history: deque = deque(maxlen=max_entries)
        self._last_content = ""
        self._running = False
        self._thread = None

        if self.available:
            logger.info(f"[OK] Clipboard history ready (max {max_entries} entries)")
        else:
            logger.info("[INFO] Clipboard history unavailable — install pyperclip")

    def start(self):
        """Start monitoring clipboard in background"""
        if not self.available or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("[ClipboardHistory] Monitoring started")

    def stop(self):
        """Stop monitoring"""
        self._running = False

    def _monitor_loop(self):
        """Background loop to detect clipboard changes"""
        while self._running:
            try:
                current = pyperclip.paste()
                if current and current != self._last_content:
                    self._last_content = current
                    self.history.append({
                        'content': current,
                        'timestamp': datetime.now().isoformat(),
                        'length': len(current),
                    })
            except Exception:
                pass
            time.sleep(self.poll_interval)

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent clipboard entries"""
        entries = list(self.history)
        return entries[-limit:]

    def get_current(self) -> Optional[str]:
        """Get current clipboard content"""
        if not self.available:
            return None
        try:
            return pyperclip.paste()
        except Exception:
            return None

    def search_history(self, query: str) -> List[Dict]:
        """Search clipboard history for matching entries"""
        query_lower = query.lower()
        return [
            entry for entry in self.history
            if query_lower in entry['content'].lower()
        ]

    def get_entry(self, index: int) -> Optional[Dict]:
        """Get a specific history entry by index (0 = oldest)"""
        entries = list(self.history)
        if 0 <= index < len(entries):
            return entries[index]
        return None

    def clear_history(self):
        """Clear clipboard history"""
        self.history.clear()
        logger.info("[ClipboardHistory] History cleared")

    def get_stats(self) -> Dict:
        """Get clipboard history stats"""
        return {
            'total_entries': len(self.history),
            'max_entries': self.max_entries,
            'monitoring': self._running,
            'available': self.available,
        }

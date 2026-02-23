"""
Uptime Monitor Extension — Seven AI

Tracks Seven's session duration, uptime stats, restart count,
and provides session-aware context. Logs session history.
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("UptimeMonitor")


class UptimeMonitorExtension(SevenExtension):
    """Track Seven's uptime, session stats, and availability"""

    name = "Uptime Monitor"
    version = "1.0"
    description = "Tracks session duration, uptime stats, and restart history"
    author = "Seven AI"

    schedule_interval_minutes = 10  # Log stats every 10 min
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.session_start = datetime.now()
        self.messages_this_session = 0
        self.peak_messages_per_hour = 0
        self._hourly_count = 0
        self._last_hour = datetime.now().hour

        # Persistence
        self._stats_file = Path.home() / ".chatbot" / "uptime_stats.json"
        self._history = self._load_history()

        # Record session start
        self._history['sessions'].append({
            'start': self.session_start.isoformat(),
            'end': None,
        })
        self._history['total_sessions'] = len(self._history['sessions'])
        self._save_history()

    def run(self, context: dict = None) -> dict:
        """Report current uptime stats"""
        now = datetime.now()
        uptime = now - self.session_start
        hours = uptime.total_seconds() / 3600
        days = uptime.days

        # Track hourly message rate
        if now.hour != self._last_hour:
            if self._hourly_count > self.peak_messages_per_hour:
                self.peak_messages_per_hour = self._hourly_count
            self._hourly_count = 0
            self._last_hour = now.hour

        # Format uptime
        if days > 0:
            uptime_str = f"{days}d {uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
        elif hours >= 1:
            uptime_str = f"{int(hours)}h {int((uptime.total_seconds() % 3600) // 60)}m"
        else:
            uptime_str = f"{int(uptime.total_seconds() // 60)}m"

        msg = (
            f"Session uptime: {uptime_str} | "
            f"Messages: {self.messages_this_session} | "
            f"Peak rate: {self.peak_messages_per_hour}/hr | "
            f"Total sessions: {self._history.get('total_sessions', 1)}"
        )

        # Update session end time
        if self._history['sessions']:
            self._history['sessions'][-1]['end'] = now.isoformat()
            self._history['sessions'][-1]['messages'] = self.messages_this_session
            self._save_history()

        return {
            "message": msg,
            "uptime_seconds": int(uptime.total_seconds()),
            "uptime_str": uptime_str,
            "messages": self.messages_this_session,
            "peak_per_hour": self.peak_messages_per_hour,
            "total_sessions": self._history.get('total_sessions', 1),
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Track messages and respond to uptime queries"""
        self.messages_this_session += 1
        self._hourly_count += 1

        lower = user_message.lower()

        if any(p in lower for p in ["uptime", "how long have you been", "session time",
                                     "how long running", "when did you start",
                                     "session stats", "session info"]):
            result = self.run()
            return result["message"]

        return None

    def stop(self):
        """Record session end on shutdown"""
        if self._history['sessions']:
            self._history['sessions'][-1]['end'] = datetime.now().isoformat()
            self._history['sessions'][-1]['messages'] = self.messages_this_session
            self._save_history()

    def _load_history(self) -> dict:
        """Load session history from disk"""
        try:
            if self._stats_file.exists():
                data = json.loads(self._stats_file.read_text(encoding='utf-8'))
                if 'sessions' not in data:
                    data['sessions'] = []
                # Keep only last 50 sessions
                data['sessions'] = data['sessions'][-50:]
                return data
        except Exception:
            pass
        return {'sessions': [], 'total_sessions': 0}

    def _save_history(self):
        """Persist session history"""
        try:
            self._stats_file.parent.mkdir(parents=True, exist_ok=True)
            self._stats_file.write_text(json.dumps(self._history, indent=2), encoding='utf-8')
        except Exception:
            pass

    def get_status(self) -> dict:
        uptime = (datetime.now() - self.session_start).total_seconds()
        return {
            "name": self.name,
            "version": self.version,
            "uptime_seconds": int(uptime),
            "messages": self.messages_this_session,
            "peak_per_hour": self.peak_messages_per_hour,
            "total_sessions": self._history.get('total_sessions', 1),
            "running": True,
        }

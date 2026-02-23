"""
Smart Reminders Extension — Seven AI

Set timed reminders via voice or text. Seven will notify you
when the time comes using toast notifications or voice.

Examples:
  "remind me in 10 minutes to check the oven"
  "remind me at 3pm to call Jan"
  "list reminders"
  "cancel reminder 1"
"""

import logging
import threading
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("SmartReminders")


class SmartRemindersExtension(SevenExtension):
    """Timed reminders with toast notification delivery"""

    name = "Smart Reminders"
    version = "1.0"
    description = "Set timed reminders — Seven notifies you when it's time"
    author = "Seven AI"

    schedule_interval_minutes = 1  # Check every minute
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.reminders: List[Dict] = []
        self._next_id = 1
        self._timers: Dict[int, threading.Timer] = {}

    def run(self, context: dict = None) -> dict:
        """Check for due reminders (backup — timers handle most)"""
        now = datetime.now()
        fired = []
        for reminder in self.reminders[:]:
            if reminder['status'] == 'active' and now >= reminder['due']:
                self._fire_reminder(reminder)
                fired.append(reminder['text'])

        active = [r for r in self.reminders if r['status'] == 'active']
        return {
            "message": f"{len(active)} active reminder(s)" + (f", just fired: {', '.join(fired)}" if fired else ""),
            "active_count": len(active),
            "fired": fired,
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Parse reminder commands from conversation"""
        lower = user_message.lower()

        # "remind me in X minutes/hours to ..."
        match = re.search(
            r"remind\s+me\s+in\s+(\d+)\s*(minute|min|hour|hr|second|sec)s?\s+(?:to\s+)?(.+)",
            user_message, re.IGNORECASE
        )
        if match:
            amount = int(match.group(1))
            unit = match.group(2).lower()
            text = match.group(3).strip()

            if unit in ('hour', 'hr'):
                delta = timedelta(hours=amount)
                unit_str = f"{amount} hour(s)"
            elif unit in ('second', 'sec'):
                delta = timedelta(seconds=amount)
                unit_str = f"{amount} second(s)"
            else:
                delta = timedelta(minutes=amount)
                unit_str = f"{amount} minute(s)"

            due = datetime.now() + delta
            rid = self._add_reminder(text, due)
            return f"Reminder #{rid} set: '{text}' in {unit_str} (at {due.strftime('%H:%M')})"

        # "remind me at HH:MM to ..."
        match = re.search(
            r"remind\s+me\s+at\s+(\d{1,2})[:\.]?(\d{2})?\s*(am|pm)?\s+(?:to\s+)?(.+)",
            user_message, re.IGNORECASE
        )
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            text = match.group(4).strip()

            if ampm:
                if ampm.lower() == 'pm' and hour != 12:
                    hour += 12
                elif ampm.lower() == 'am' and hour == 12:
                    hour = 0

            now = datetime.now()
            due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if due <= now:
                due += timedelta(days=1)

            rid = self._add_reminder(text, due)
            return f"Reminder #{rid} set: '{text}' at {due.strftime('%H:%M')}"

        # "list reminders"
        if any(p in lower for p in ["list reminder", "my reminder", "show reminder", "active reminder"]):
            active = [r for r in self.reminders if r['status'] == 'active']
            if not active:
                return "No active reminders."
            lines = [f"Active reminders ({len(active)}):"]
            for r in active:
                lines.append(f"  #{r['id']}: '{r['text']}' — due {r['due'].strftime('%H:%M')}")
            return "\n".join(lines)

        # "cancel reminder N"
        match = re.search(r"cancel\s+reminder\s+#?(\d+)", user_message, re.IGNORECASE)
        if match:
            rid = int(match.group(1))
            return self._cancel_reminder(rid)

        # "clear all reminders"
        if "clear all reminder" in lower or "cancel all reminder" in lower:
            count = self._clear_all()
            return f"Cleared {count} reminder(s)."

        return None

    def _add_reminder(self, text: str, due: datetime) -> int:
        """Add a reminder and start a timer"""
        rid = self._next_id
        self._next_id += 1

        reminder = {
            'id': rid,
            'text': text,
            'due': due,
            'created': datetime.now(),
            'status': 'active',
        }
        self.reminders.append(reminder)

        # Start a threading timer
        delay = max(0, (due - datetime.now()).total_seconds())
        timer = threading.Timer(delay, self._fire_reminder, args=[reminder])
        timer.daemon = True
        timer.start()
        self._timers[rid] = timer

        logger.info(f"[Reminders] #{rid} set: '{text}' due at {due.strftime('%H:%M:%S')}")
        return rid

    def _fire_reminder(self, reminder: Dict):
        """Fire a reminder — toast + voice if available"""
        if reminder['status'] != 'active':
            return

        reminder['status'] = 'fired'
        text = reminder['text']
        logger.info(f"[Reminders] FIRING #{reminder['id']}: {text}")

        # Toast notification
        if self.bot:
            toast = getattr(self.bot, 'toast', None)
            if toast and toast.available:
                toast.notify("Seven AI — Reminder", text, duration=10)

            # Voice notification
            speak = getattr(self.bot, '_speak', None)
            if speak:
                try:
                    speak(f"Reminder: {text}")
                except Exception:
                    pass

        # Cleanup timer ref
        self._timers.pop(reminder['id'], None)

    def _cancel_reminder(self, rid: int) -> str:
        """Cancel a reminder by ID"""
        for r in self.reminders:
            if r['id'] == rid and r['status'] == 'active':
                r['status'] = 'cancelled'
                timer = self._timers.pop(rid, None)
                if timer:
                    timer.cancel()
                return f"Reminder #{rid} cancelled."
        return f"Reminder #{rid} not found or already fired."

    def _clear_all(self) -> int:
        """Cancel all active reminders"""
        count = 0
        for r in self.reminders:
            if r['status'] == 'active':
                r['status'] = 'cancelled'
                count += 1
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
        return count

    def stop(self):
        """Cleanup timers on shutdown"""
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()

    def get_status(self) -> dict:
        active = [r for r in self.reminders if r['status'] == 'active']
        return {
            "name": self.name,
            "version": self.version,
            "active_reminders": len(active),
            "total_created": len(self.reminders),
            "running": True,
        }

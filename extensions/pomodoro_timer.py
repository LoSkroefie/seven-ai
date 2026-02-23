"""
Pomodoro Timer Extension — Seven AI

Focus/break cycle timer. Default: 25 min work, 5 min break.
Seven announces transitions via toast + voice. Tracks sessions.

Commands:
  "start pomodoro"
  "pomodoro status"
  "stop pomodoro"
  "pomodoro 50/10" (custom work/break)
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("PomodoroTimer")


class PomodoroTimerExtension(SevenExtension):
    """Focus timer with work/break cycles and notifications"""

    name = "Pomodoro Timer"
    version = "1.0"
    description = "Focus/break cycle timer with voice and toast notifications"
    author = "Seven AI"

    schedule_interval_minutes = 0  # Passive — driven by on_message
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.active = False
        self.phase = None          # 'work' or 'break'
        self.work_minutes = 25
        self.break_minutes = 5
        self.sessions_completed = 0
        self.total_focus_minutes = 0
        self.started_at = None
        self.phase_end = None
        self._timer = None

    def run(self, context: dict = None) -> dict:
        """Return current pomodoro status"""
        if not self.active:
            return {
                "message": f"Pomodoro inactive. {self.sessions_completed} sessions completed today.",
                "status": "idle",
            }

        remaining = (self.phase_end - datetime.now()).total_seconds() if self.phase_end else 0
        remaining = max(0, remaining)
        mins = int(remaining // 60)
        secs = int(remaining % 60)

        return {
            "message": f"Pomodoro: {self.phase} phase — {mins}:{secs:02d} remaining",
            "phase": self.phase,
            "remaining_seconds": int(remaining),
            "sessions_completed": self.sessions_completed,
            "status": "active",
        }

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Handle pomodoro commands"""
        lower = user_message.lower()

        # Start pomodoro
        if any(p in lower for p in ["start pomodoro", "begin pomodoro", "start focus",
                                     "pomodoro start", "focus mode"]):
            # Custom timing: "pomodoro 50/10"
            import re
            match = re.search(r"(\d+)\s*/\s*(\d+)", user_message)
            if match:
                self.work_minutes = int(match.group(1))
                self.break_minutes = int(match.group(2))

            return self._start_work()

        # Stop pomodoro
        if any(p in lower for p in ["stop pomodoro", "cancel pomodoro", "end pomodoro",
                                     "stop focus", "exit focus"]):
            return self._stop()

        # Status
        if any(p in lower for p in ["pomodoro status", "focus status", "pomodoro time",
                                     "how much time", "timer status"]):
            result = self.run()
            return result["message"]

        # Skip to next phase
        if any(p in lower for p in ["skip break", "skip to work", "next phase", "skip phase"]):
            if self.active:
                if self.phase == 'break':
                    return self._start_work()
                else:
                    return self._start_break()

        return None

    def _start_work(self) -> str:
        """Start a work phase"""
        self._cancel_timer()
        self.active = True
        self.phase = 'work'
        self.started_at = datetime.now()
        self.phase_end = datetime.now() + timedelta(minutes=self.work_minutes)

        # Set timer for end of work phase
        self._timer = threading.Timer(self.work_minutes * 60, self._on_work_done)
        self._timer.daemon = True
        self._timer.start()

        self._notify(f"Focus time! {self.work_minutes} minutes of work starts now.")
        logger.info(f"[Pomodoro] Work phase started: {self.work_minutes} min")
        return f"Pomodoro started: {self.work_minutes} min work / {self.break_minutes} min break. Focus!"

    def _start_break(self) -> str:
        """Start a break phase"""
        self._cancel_timer()
        self.phase = 'break'
        self.phase_end = datetime.now() + timedelta(minutes=self.break_minutes)

        self._timer = threading.Timer(self.break_minutes * 60, self._on_break_done)
        self._timer.daemon = True
        self._timer.start()

        self._notify(f"Break time! Rest for {self.break_minutes} minutes.")
        logger.info(f"[Pomodoro] Break phase started: {self.break_minutes} min")
        return f"Break time! {self.break_minutes} minutes. Relax."

    def _on_work_done(self):
        """Called when work phase ends"""
        self.sessions_completed += 1
        self.total_focus_minutes += self.work_minutes
        self._notify(f"Work session #{self.sessions_completed} complete! Time for a {self.break_minutes}-minute break.")
        self._start_break()

    def _on_break_done(self):
        """Called when break phase ends"""
        self._notify("Break's over! Ready for another focus session? Say 'start pomodoro'.")
        self.active = False
        self.phase = None
        self.phase_end = None

    def _stop(self) -> str:
        """Stop the pomodoro"""
        self._cancel_timer()
        was_active = self.active
        self.active = False
        self.phase = None
        self.phase_end = None

        if was_active:
            return f"Pomodoro stopped. {self.sessions_completed} sessions completed, {self.total_focus_minutes} minutes focused today."
        return "No pomodoro running."

    def _cancel_timer(self):
        """Cancel the current timer"""
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _notify(self, message: str):
        """Send notification via toast and/or voice"""
        if not self.bot:
            return

        toast = getattr(self.bot, 'toast', None)
        if toast and toast.available:
            toast.notify("Seven AI — Pomodoro", message, duration=8)

        speak = getattr(self.bot, '_speak', None)
        if speak:
            try:
                speak(message)
            except Exception:
                pass

    def stop(self):
        """Cleanup on shutdown"""
        self._cancel_timer()

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "active": self.active,
            "phase": self.phase,
            "sessions_completed": self.sessions_completed,
            "total_focus_minutes": self.total_focus_minutes,
            "work_minutes": self.work_minutes,
            "break_minutes": self.break_minutes,
            "running": True,
        }

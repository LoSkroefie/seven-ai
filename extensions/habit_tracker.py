"""
Habit Tracker Extension — Seven AI

Track daily habits and streaks. Seven reminds you about habits
and celebrates streak milestones. Persists to disk.

Commands:
  "add habit read for 30 minutes"
  "done reading" / "completed reading"
  "habit status" / "my habits"
  "remove habit reading"
"""

import logging
import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("HabitTracker")


class HabitTrackerExtension(SevenExtension):
    """Track daily habits, streaks, and completions"""

    name = "Habit Tracker"
    version = "1.0"
    description = "Track daily habits with streaks and reminders"
    author = "Seven AI"

    schedule_interval_minutes = 120  # Check every 2 hours for reminders
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self._data_file = Path.home() / ".chatbot" / "habits.json"
        self.habits = self._load()

    def run(self, context: dict = None) -> dict:
        """Check habits and generate reminders for incomplete ones"""
        today = date.today().isoformat()
        incomplete = []
        for name, habit in self.habits.items():
            if today not in habit.get('completions', []):
                incomplete.append(name)

        if incomplete:
            msg = f"Incomplete habits today: {', '.join(incomplete)}"
            # Notify via toast
            if self.bot and len(incomplete) > 0:
                toast = getattr(self.bot, 'toast', None)
                if toast and toast.available:
                    toast.notify("Seven AI — Habits", f"Don't forget: {', '.join(incomplete[:3])}", duration=5)
        else:
            if self.habits:
                msg = "All habits completed today!"
            else:
                msg = "No habits tracked yet. Say 'add habit X' to start."

        return {"message": msg, "incomplete": incomplete, "status": "ok"}

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Handle habit commands"""
        lower = user_message.lower()

        # Add habit: "add habit read for 30 minutes"
        match = re.search(r"add\s+habit\s+(.+)", user_message, re.IGNORECASE)
        if match:
            name = match.group(1).strip().rstrip('.')
            return self._add_habit(name)

        # Complete habit: "done reading", "completed exercise", "finished meditation"
        match = re.search(r"(?:done|completed|finished|did)\s+(?:my\s+)?(.+?)(?:\s+today)?\.?$", user_message, re.IGNORECASE)
        if match and self.habits:
            activity = match.group(1).strip().lower()
            # Fuzzy match against habit names
            for name in self.habits:
                if activity in name.lower() or name.lower() in activity:
                    return self._complete_habit(name)

        # Status: "habit status", "my habits", "habit streak"
        if any(p in lower for p in ["habit status", "my habit", "habit streak", "show habit",
                                     "list habit", "habit list", "habit progress"]):
            return self._get_status_text()

        # Remove: "remove habit X", "delete habit X"
        match = re.search(r"(?:remove|delete)\s+habit\s+(.+)", user_message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            return self._remove_habit(name)

        # Reset streaks: "reset habit streaks"
        if "reset habit" in lower and "streak" in lower:
            for habit in self.habits.values():
                habit['completions'] = []
                habit['streak'] = 0
                habit['best_streak'] = max(habit.get('best_streak', 0), habit.get('streak', 0))
            self._save()
            return "All habit streaks reset."

        return None

    def _add_habit(self, name: str) -> str:
        """Add a new habit"""
        key = name.lower().strip()
        if key in {k.lower() for k in self.habits}:
            return f"Habit '{name}' already exists."

        self.habits[name] = {
            'created': date.today().isoformat(),
            'completions': [],
            'streak': 0,
            'best_streak': 0,
        }
        self._save()
        return f"Habit '{name}' added! I'll help you track it daily."

    def _complete_habit(self, name: str) -> str:
        """Mark a habit as done today"""
        habit = self.habits.get(name)
        if not habit:
            return f"Habit '{name}' not found."

        today = date.today().isoformat()
        if today in habit.get('completions', []):
            return f"'{name}' already completed today!"

        habit.setdefault('completions', []).append(today)

        # Calculate streak
        streak = self._calc_streak(habit['completions'])
        habit['streak'] = streak
        habit['best_streak'] = max(habit.get('best_streak', 0), streak)

        self._save()

        # Celebrate milestones
        msg = f"'{name}' done! Streak: {streak} day(s)"
        if streak in (7, 14, 21, 30, 50, 100):
            msg += f" — {streak}-day milestone! Amazing consistency!"
        elif streak >= 3:
            msg += " — keep it going!"

        return msg

    def _calc_streak(self, completions: List[str]) -> int:
        """Calculate current streak from completion dates"""
        if not completions:
            return 0

        dates = sorted(set(completions), reverse=True)
        today = date.today().isoformat()

        if dates[0] != today:
            return 0

        streak = 1
        for i in range(1, len(dates)):
            expected = (date.fromisoformat(dates[i - 1]) - timedelta(days=1)).isoformat()
            if dates[i] == expected:
                streak += 1
            else:
                break

        return streak

    def _remove_habit(self, name: str) -> str:
        """Remove a habit"""
        # Fuzzy match
        for key in list(self.habits.keys()):
            if name.lower() in key.lower() or key.lower() in name.lower():
                del self.habits[key]
                self._save()
                return f"Habit '{key}' removed."
        return f"Habit '{name}' not found."

    def _get_status_text(self) -> str:
        """Get formatted habit status"""
        if not self.habits:
            return "No habits tracked. Say 'add habit X' to start!"

        today = date.today().isoformat()
        lines = [f"Habits ({len(self.habits)}):"]
        for name, habit in self.habits.items():
            done = "✓" if today in habit.get('completions', []) else "○"
            streak = habit.get('streak', 0)
            best = habit.get('best_streak', 0)
            lines.append(f"  {done} {name} — streak: {streak}d (best: {best}d)")

        completed = sum(1 for h in self.habits.values() if today in h.get('completions', []))
        lines.append(f"\nToday: {completed}/{len(self.habits)} completed")
        return "\n".join(lines)

    def _load(self) -> Dict:
        """Load habits from disk"""
        try:
            if self._data_file.exists():
                return json.loads(self._data_file.read_text(encoding='utf-8'))
        except Exception:
            pass
        return {}

    def _save(self):
        """Persist habits to disk"""
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            self._data_file.write_text(json.dumps(self.habits, indent=2), encoding='utf-8')
        except Exception:
            pass

    def stop(self):
        self._save()

    def get_status(self) -> dict:
        today = date.today().isoformat()
        completed = sum(1 for h in self.habits.values() if today in h.get('completions', []))
        return {
            "name": self.name,
            "version": self.version,
            "total_habits": len(self.habits),
            "completed_today": completed,
            "running": True,
        }

"""
Timer & Alarm System - Seven Keeps Track of Time For You

Timers, alarms, and reminders with spoken alerts via TTS.
"""

import logging
import threading
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger("TimerSystem")


class TimerSystem:
    """
    Seven's time management.
    
    - Set timers: "set a timer for 20 minutes"
    - Set alarms: "wake me up at 7am"
    - Pomodoro: "start a work session"
    - Spoken alerts via bot's TTS
    """
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("TimerSystem")
        
        # Active timers
        self.timers: Dict[str, Dict] = {}
        self._timer_threads: Dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        
        # Pomodoro
        self.pomodoro_active = False
        self.pomodoro_session = 0
        
        # Persistence
        self._state_file = Path.home() / "Documents" / "Seven" / "state" / "timers.json"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("[OK] Timer system ready")
    
    # ============ TIMERS ============
    
    def set_timer(self, duration_seconds: int, label: str = "Timer") -> str:
        """
        Set a countdown timer.
        
        Args:
            duration_seconds: How long in seconds
            label: Name for the timer
        """
        timer_id = f"timer_{len(self.timers) + 1}_{int(time.time())}"
        
        end_time = datetime.now() + timedelta(seconds=duration_seconds)
        
        self.timers[timer_id] = {
            'label': label,
            'duration': duration_seconds,
            'end_time': end_time.isoformat(),
            'created': datetime.now().isoformat(),
            'status': 'running',
        }
        
        # Start background thread
        t = threading.Timer(duration_seconds, self._timer_fired, args=[timer_id, label])
        t.daemon = True
        t.start()
        self._timer_threads[timer_id] = t
        
        # Format duration nicely
        duration_str = self._format_duration(duration_seconds)
        
        self.logger.info(f"Timer set: {label} for {duration_str}")
        return f"Timer set: {label} — {duration_str}. I'll let you know when it's done."
    
    def cancel_timer(self, timer_id: str = None, label: str = None) -> str:
        """Cancel a timer by ID or label"""
        with self._lock:
            target = None
            
            if timer_id and timer_id in self.timers:
                target = timer_id
            elif label:
                for tid, info in self.timers.items():
                    if info['label'].lower() == label.lower() and info['status'] == 'running':
                        target = tid
                        break
            
            if not target:
                return "No matching timer found."
            
            self.timers[target]['status'] = 'cancelled'
            if target in self._timer_threads:
                self._timer_threads[target].cancel()
                del self._timer_threads[target]
            
            return f"Cancelled timer: {self.timers[target]['label']}"
    
    def list_timers(self) -> str:
        """List active timers"""
        active = [(tid, info) for tid, info in self.timers.items() if info['status'] == 'running']
        
        if not active:
            return "No active timers."
        
        lines = [f"{len(active)} active timer(s):"]
        for tid, info in active:
            end = datetime.fromisoformat(info['end_time'])
            remaining = (end - datetime.now()).total_seconds()
            if remaining > 0:
                lines.append(f"  - {info['label']}: {self._format_duration(int(remaining))} remaining")
            else:
                lines.append(f"  - {info['label']}: about to fire!")
        
        return "\n".join(lines)
    
    def _timer_fired(self, timer_id: str, label: str):
        """Called when a timer completes"""
        with self._lock:
            if timer_id in self.timers:
                self.timers[timer_id]['status'] = 'completed'
            if timer_id in self._timer_threads:
                del self._timer_threads[timer_id]
        
        message = f"Timer done! {label} is up!"
        self.logger.info(message)
        
        # Speak it
        if self.bot:
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life.queue_message(message, priority="high")
            # Also try direct speech
            try:
                if hasattr(self.bot, '_speak'):
                    self.bot._speak(message)
            except Exception:
                pass
    
    # ============ ALARMS ============
    
    def set_alarm(self, hour: int, minute: int = 0, label: str = "Alarm") -> str:
        """
        Set an alarm for a specific time today (or tomorrow if time has passed).
        """
        now = datetime.now()
        alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if alarm_time <= now:
            alarm_time += timedelta(days=1)
        
        seconds_until = (alarm_time - now).total_seconds()
        
        timer_id = f"alarm_{int(time.time())}"
        self.timers[timer_id] = {
            'label': label,
            'duration': int(seconds_until),
            'end_time': alarm_time.isoformat(),
            'created': datetime.now().isoformat(),
            'status': 'running',
            'type': 'alarm',
        }
        
        t = threading.Timer(seconds_until, self._timer_fired, args=[timer_id, label])
        t.daemon = True
        t.start()
        self._timer_threads[timer_id] = t
        
        time_str = alarm_time.strftime('%I:%M %p')
        if alarm_time.date() > now.date():
            time_str += " tomorrow"
        
        return f"Alarm set for {time_str}: {label}"
    
    # ============ POMODORO ============
    
    def start_pomodoro(self, work_minutes: int = 25, break_minutes: int = 5) -> str:
        """Start a Pomodoro work session"""
        if self.pomodoro_active:
            return "A Pomodoro session is already running."
        
        self.pomodoro_active = True
        self.pomodoro_session += 1
        
        # Set work timer
        self.set_timer(
            work_minutes * 60,
            label=f"Pomodoro #{self.pomodoro_session} — work time over! Take a {break_minutes} minute break"
        )
        
        return f"Pomodoro #{self.pomodoro_session} started! Focus for {work_minutes} minutes. I'll tell you when to take a break."
    
    def stop_pomodoro(self) -> str:
        """Stop Pomodoro session"""
        self.pomodoro_active = False
        # Cancel any pomodoro timers
        with self._lock:
            for tid, info in list(self.timers.items()):
                if 'Pomodoro' in info.get('label', '') and info['status'] == 'running':
                    self.cancel_timer(timer_id=tid)
        return "Pomodoro session stopped."
    
    # ============ PARSING ============
    
    @staticmethod
    def parse_duration(text: str) -> Optional[int]:
        """
        Parse a duration string into seconds.
        
        Examples: "20 minutes", "1 hour", "90 seconds", "1h30m"
        """
        import re
        text = text.lower().strip()
        
        total = 0
        
        # Pattern: Xh Ym Zs
        h = re.search(r'(\d+)\s*h(?:our)?s?', text)
        m = re.search(r'(\d+)\s*m(?:in(?:ute)?)?s?', text)
        s = re.search(r'(\d+)\s*s(?:ec(?:ond)?)?s?', text)
        
        if h:
            total += int(h.group(1)) * 3600
        if m:
            total += int(m.group(1)) * 60
        if s:
            total += int(s.group(1))
        
        # Just a number — assume minutes
        if total == 0:
            num = re.search(r'(\d+)', text)
            if num:
                total = int(num.group(1)) * 60
        
        return total if total > 0 else None
    
    @staticmethod
    def parse_time(text: str) -> Optional[tuple]:
        """
        Parse a time string into (hour, minute).
        
        Examples: "7am", "7:30 pm", "14:00", "7 in the morning"
        """
        import re
        text = text.lower().strip()
        
        # 7:30 pm, 7:30pm
        match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            ampm = match.group(3)
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            return (hour, minute)
        
        # 7am, 7pm
        match = re.search(r'(\d{1,2})\s*(am|pm)', text)
        if match:
            hour = int(match.group(1))
            if match.group(2) == 'pm' and hour < 12:
                hour += 12
            elif match.group(2) == 'am' and hour == 12:
                hour = 0
            return (hour, 0)
        
        # 14:00 (24h)
        match = re.search(r'(\d{1,2}):(\d{2})', text)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        
        return None
    
    # ============ HELPERS ============
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds into human-readable string"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            if secs:
                return f"{mins} minute{'s' if mins != 1 else ''} and {secs} seconds"
            return f"{mins} minute{'s' if mins != 1 else ''}"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            if mins:
                return f"{hours} hour{'s' if hours != 1 else ''} and {mins} minute{'s' if mins != 1 else ''}"
            return f"{hours} hour{'s' if hours != 1 else ''}"
    
    def cleanup(self):
        """Cancel all timers"""
        with self._lock:
            for t in self._timer_threads.values():
                t.cancel()
            self._timer_threads.clear()

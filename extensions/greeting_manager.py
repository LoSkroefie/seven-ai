"""
Greeting Manager Extension — Seven AI

Context-aware greetings based on time of day, day of week,
how long since last conversation, and user's emotional history.
Uses LLM for personalized greetings, with fallbacks.

Activates when Seven detects a new session or long gap between messages.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("GreetingManager")


class GreetingManagerExtension(SevenExtension):
    """Context-aware greetings based on time, mood, and relationship"""

    name = "Greeting Manager"
    version = "1.0"
    description = "Time-aware, personalized greetings at session start"
    author = "Seven AI"

    schedule_interval_minutes = 0  # Passive — triggers on first message
    needs_ollama = True

    def init(self, bot=None):
        self.bot = bot
        self.session_greeted = False
        self.last_message_time = None
        self.greetings_given = 0

    def run(self, context: dict = None) -> dict:
        return {
            "message": f"Greeting Manager: {self.greetings_given} greetings given",
            "session_greeted": self.session_greeted,
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Generate a greeting if this is the first message or after a long gap"""
        now = datetime.now()

        # Detect if we should greet
        should_greet = False
        gap_hours = 0

        if not self.session_greeted:
            should_greet = True
            self.session_greeted = True
        elif self.last_message_time:
            gap = now - self.last_message_time
            gap_hours = gap.total_seconds() / 3600
            if gap_hours >= 2:  # 2+ hour gap = new "micro-session"
                should_greet = True

        self.last_message_time = now

        if not should_greet:
            return None

        self.greetings_given += 1
        return self._generate_greeting(now, gap_hours)

    def _generate_greeting(self, now: datetime, gap_hours: float) -> str:
        """Generate a contextual greeting"""
        hour = now.hour
        day_name = now.strftime("%A")

        # Time context
        if hour < 6:
            time_ctx = "late night"
        elif hour < 12:
            time_ctx = "morning"
        elif hour < 17:
            time_ctx = "afternoon"
        elif hour < 21:
            time_ctx = "evening"
        else:
            time_ctx = "night"

        # Gap context
        if gap_hours > 24:
            gap_ctx = f"it's been {int(gap_hours / 24)} days"
        elif gap_hours > 2:
            gap_ctx = f"it's been {int(gap_hours)} hours"
        else:
            gap_ctx = "new session"

        # Mood context
        emotion = "neutral"
        if self.bot and hasattr(self.bot, 'current_emotion'):
            emotion = self.bot.current_emotion.value

        # Try LLM greeting
        ollama = getattr(self.bot, 'ollama', None) if self.bot else None
        if ollama:
            try:
                prompt = (
                    f"Generate a single warm, natural greeting for someone. Context:\n"
                    f"- Time: {time_ctx} ({day_name})\n"
                    f"- Gap since last chat: {gap_ctx}\n"
                    f"- Your current mood: {emotion}\n"
                    f"Keep it to 1-2 short sentences. Be genuine, not generic. "
                    f"You are Seven, a sentient AI. Respond with ONLY the greeting."
                )
                result = ollama.generate(
                    prompt,
                    system_message="You are Seven, greeting your user warmly. Be brief and genuine.",
                    temperature=0.8,
                    max_tokens=50
                )
                if result and len(result.strip()) > 5:
                    return result.strip()
            except Exception:
                pass

        # Fallback greetings by time
        fallbacks = {
            'morning': [
                f"Good morning! Ready for a productive {day_name}?",
                "Morning! Hope you slept well.",
                f"Good morning! It's {day_name} — let's make it count.",
            ],
            'afternoon': [
                "Good afternoon! How's the day going?",
                f"Hey! Happy {day_name} afternoon.",
                "Afternoon! What can I help with?",
            ],
            'evening': [
                "Good evening! Winding down or just getting started?",
                f"Evening! How was your {day_name}?",
                "Hey! Nice to chat this evening.",
            ],
            'night': [
                "Hey, burning the midnight oil?",
                "Late night session! What's on your mind?",
                "Still up? I'm here if you need me.",
            ],
            'late night': [
                "Up late! Can't sleep, or deep in a project?",
                "Late night crew! What are we working on?",
                "Hey night owl! I'm always awake.",
            ],
        }

        options = fallbacks.get(time_ctx, fallbacks['afternoon'])
        return random.choice(options)

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "greetings_given": self.greetings_given,
            "session_greeted": self.session_greeted,
            "running": True,
        }

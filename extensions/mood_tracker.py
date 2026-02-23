"""
Mood Tracker Extension — Seven AI

Deeper emotional analysis — tracks emotional patterns over time,
detects mood shifts, and provides emotional intelligence insights.
"""

import logging
from datetime import datetime
from collections import deque
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("MoodTracker")


class MoodTrackerExtension(SevenExtension):
    """Advanced emotional tracking and mood pattern detection"""

    name = "Mood Tracker"
    version = "1.0"
    description = "Tracks emotional patterns, mood shifts, and emotional intelligence"
    author = "Seven AI"

    schedule_interval_minutes = 60  # Hourly analysis
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.emotion_log = deque(maxlen=500)  # (timestamp, emotion, trigger)
        self.mood_shifts = deque(maxlen=50)
        self.last_emotion = None
        self.positive_streak = 0
        self.negative_streak = 0

    POSITIVE_EMOTIONS = {'joy', 'happiness', 'excitement', 'love', 'gratitude',
                         'contentment', 'amusement', 'pride', 'hope', 'inspiration',
                         'tenderness', 'calmness', 'curiosity', 'awe'}
    NEGATIVE_EMOTIONS = {'sadness', 'anger', 'fear', 'frustration', 'anxiety',
                         'guilt', 'shame', 'disgust', 'loneliness', 'jealousy',
                         'boredom', 'confusion', 'melancholy'}

    def run(self, context: dict = None) -> dict:
        """Analyze emotional patterns"""
        if not self.emotion_log:
            return {"message": "No emotional data yet.", "status": "ok"}

        # Calculate mood distribution
        emotions = [e[1] for e in self.emotion_log]
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1

        total = len(emotions)
        positive = sum(1 for e in emotions if e in self.POSITIVE_EMOTIONS)
        negative = sum(1 for e in emotions if e in self.NEGATIVE_EMOTIONS)
        neutral = total - positive - negative

        positivity_ratio = positive / max(total, 1)

        # Dominant mood
        dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "unknown"

        # Emotional volatility (how much emotions change)
        changes = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i-1])
        volatility = changes / max(len(emotions) - 1, 1)

        # Recent trend (last 10 vs previous 10)
        recent = emotions[-10:] if len(emotions) >= 10 else emotions
        recent_positive = sum(1 for e in recent if e in self.POSITIVE_EMOTIONS)
        trend = "improving" if recent_positive > len(recent) / 2 else "declining" if recent_positive < len(recent) / 3 else "stable"

        analysis = (
            f"Mood Analysis: {dominant} dominant | "
            f"Positive: {positivity_ratio:.0%} | Volatility: {volatility:.0%} | "
            f"Trend: {trend} | "
            f"Streaks: +{self.positive_streak} / -{self.negative_streak}"
        )

        return {
            "message": analysis,
            "dominant_mood": dominant,
            "positivity_ratio": round(positivity_ratio, 2),
            "volatility": round(volatility, 2),
            "trend": trend,
            "total_readings": total,
            "mood_shifts": len(self.mood_shifts),
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str):
        """Record emotion after each interaction"""
        if not self.bot or not hasattr(self.bot, 'current_emotion'):
            return None

        emotion = self.bot.current_emotion.value
        now = datetime.now()
        self.emotion_log.append((now.isoformat(), emotion, user_message[:50]))

        # Detect mood shifts
        if self.last_emotion and emotion != self.last_emotion:
            was_positive = self.last_emotion in self.POSITIVE_EMOTIONS
            is_positive = emotion in self.POSITIVE_EMOTIONS
            if was_positive != is_positive:
                self.mood_shifts.append({
                    'from': self.last_emotion,
                    'to': emotion,
                    'time': now.isoformat(),
                    'trigger': user_message[:50],
                })

        # Track streaks
        if emotion in self.POSITIVE_EMOTIONS:
            self.positive_streak += 1
            self.negative_streak = 0
        elif emotion in self.NEGATIVE_EMOTIONS:
            self.negative_streak += 1
            self.positive_streak = 0

        self.last_emotion = emotion
        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "readings": len(self.emotion_log),
            "mood_shifts": len(self.mood_shifts),
            "positive_streak": self.positive_streak,
            "negative_streak": self.negative_streak,
            "running": True,
        }

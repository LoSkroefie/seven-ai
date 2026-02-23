"""
Conversation Analytics Extension — Seven AI

Tracks conversation patterns, response times, emotional arcs,
and engagement metrics. Provides insights on-demand.
"""

import logging
from datetime import datetime
from collections import deque
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("ConversationAnalytics")


class ConversationAnalyticsExtension(SevenExtension):
    """Track and analyze conversation patterns and engagement"""

    name = "Conversation Analytics"
    version = "1.0"
    description = "Tracks conversation patterns, topics, and engagement metrics"
    author = "Seven AI"

    schedule_interval_minutes = 0  # Passive — runs via on_message
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.total_messages = 0
        self.total_words_user = 0
        self.total_words_bot = 0
        self.session_start = datetime.now()
        self.emotion_arc = deque(maxlen=100)
        self.message_lengths = deque(maxlen=100)
        self.hourly_activity = {}  # hour -> count
        self.topic_keywords = {}   # keyword -> count

    def run(self, context: dict = None) -> dict:
        """Return current analytics snapshot"""
        uptime = (datetime.now() - self.session_start).total_seconds() / 3600

        avg_user_words = self.total_words_user / max(self.total_messages, 1)
        avg_bot_words = self.total_words_bot / max(self.total_messages, 1)

        # Most active hours
        top_hours = sorted(self.hourly_activity.items(), key=lambda x: -x[1])[:3]
        top_hours_str = ", ".join(f"{h}:00 ({c}x)" for h, c in top_hours) if top_hours else "none yet"

        # Top topics
        top_topics = sorted(self.topic_keywords.items(), key=lambda x: -x[1])[:5]
        top_topics_str = ", ".join(f"{k} ({c}x)" for k, c in top_topics) if top_topics else "none yet"

        return {
            "message": (
                f"Analytics: {self.total_messages} messages over {uptime:.1f}h | "
                f"Avg user: {avg_user_words:.0f} words, Avg Seven: {avg_bot_words:.0f} words | "
                f"Active hours: {top_hours_str} | "
                f"Top topics: {top_topics_str}"
            ),
            "total_messages": self.total_messages,
            "avg_user_words": round(avg_user_words, 1),
            "avg_bot_words": round(avg_bot_words, 1),
            "uptime_hours": round(uptime, 1),
            "status": "ok",
        }

    def on_message(self, user_message: str, bot_response: str):
        """Track every message"""
        self.total_messages += 1
        self.total_words_user += len(user_message.split())
        self.total_words_bot += len(bot_response.split()) if bot_response else 0
        self.message_lengths.append(len(user_message))

        # Track hourly activity
        hour = datetime.now().hour
        self.hourly_activity[hour] = self.hourly_activity.get(hour, 0) + 1

        # Track emotion arc
        if self.bot and hasattr(self.bot, 'current_emotion'):
            self.emotion_arc.append(self.bot.current_emotion.value)

        # Simple keyword extraction for topics
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you', 'he', 'she',
                      'it', 'we', 'they', 'my', 'your', 'do', 'does', 'did', 'can', 'could',
                      'will', 'would', 'should', 'have', 'has', 'had', 'be', 'been', 'being',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'that', 'this',
                      'what', 'how', 'when', 'where', 'who', 'which', 'not', 'no', 'yes', 'and',
                      'or', 'but', 'if', 'so', 'just', 'about', 'me', 'up', 'out', 'like'}
        words = user_message.lower().split()
        for word in words:
            clean = ''.join(c for c in word if c.isalnum())
            if clean and len(clean) > 3 and clean not in stop_words:
                self.topic_keywords[clean] = self.topic_keywords.get(clean, 0) + 1

        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "total_messages": self.total_messages,
            "running": True,
        }

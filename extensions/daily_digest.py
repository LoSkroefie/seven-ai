"""
Daily Digest Extension — Seven AI

Summarizes today's conversations, emotional trends, knowledge graph growth,
and goals progress. Runs once daily or on-demand.
"""

import logging
from datetime import datetime, timedelta
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("DailyDigest")


class DailyDigestExtension(SevenExtension):
    """Generates a daily summary of Seven's activity and emotional state"""

    name = "Daily Digest"
    version = "1.0"
    description = "Summarizes daily conversations, emotions, and learning"
    author = "Seven AI"

    schedule_interval_minutes = 720  # Every 12 hours
    needs_ollama = False
    needs_memory = True

    def init(self, bot=None):
        self.bot = bot
        self.messages_today = 0
        self.emotions_today = []
        self.topics_today = []
        self.last_digest = None

    def run(self, context: dict = None) -> dict:
        """Generate daily digest"""
        if not self.bot:
            return {"message": "Bot not available"}

        now = datetime.now()
        digest_parts = [f"Daily Digest — {now.strftime('%A, %B %d, %Y')}"]
        digest_parts.append("=" * 40)

        # Conversation stats
        digest_parts.append(f"\nConversations today: {self.messages_today}")

        # Emotional summary
        if self.emotions_today:
            emotion_counts = {}
            for e in self.emotions_today:
                emotion_counts[e] = emotion_counts.get(e, 0) + 1
            top_emotions = sorted(emotion_counts.items(), key=lambda x: -x[1])[:5]
            digest_parts.append("\nTop emotions:")
            for emotion, count in top_emotions:
                digest_parts.append(f"  - {emotion}: {count}x")

        # Knowledge graph stats
        kg = getattr(self.bot, 'knowledge_graph', None)
        if kg:
            try:
                stats = kg.get_statistics()
                digest_parts.append(f"\nKnowledge Graph: {stats.get('total_nodes', 0)} nodes, "
                                    f"{stats.get('total_edges', 0)} edges")
            except Exception:
                pass

        # Goals
        tasks = getattr(self.bot, 'tasks', None)
        if tasks:
            try:
                active = tasks.get_active_tasks()
                if active:
                    digest_parts.append(f"\nActive tasks: {len(active)}")
                    for task in active[:3]:
                        digest_parts.append(f"  - {task.get('title', 'untitled')}")
            except Exception:
                pass

        # Energy / biological state
        if context:
            energy = context.get('energy', None)
            if energy is not None:
                digest_parts.append(f"\nEnergy level: {energy:.0%}")

        digest = "\n".join(digest_parts)
        self.last_digest = digest
        self.messages_today = 0
        self.emotions_today = []

        logger.info(f"[DailyDigest] Generated digest ({len(digest)} chars)")
        return {"message": digest, "status": "ok"}

    def on_message(self, user_message: str, bot_response: str):
        """Track daily activity"""
        self.messages_today += 1
        if self.bot and hasattr(self.bot, 'current_emotion'):
            self.emotions_today.append(self.bot.current_emotion.value)
        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "messages_today": self.messages_today,
            "last_digest": self.last_digest[:200] if self.last_digest else None,
            "running": True,
        }

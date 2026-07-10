"""
Learning Journal Extension — Seven AI

Tracks what Seven learned today — new knowledge graph nodes, facts,
user preferences, and behavioral patterns. Summarizes learning daily.
"""

import logging
from datetime import datetime
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("LearningJournal")


class LearningJournalExtension(SevenExtension):
    """Track and summarize what Seven learns each day"""

    name = "Learning Journal"
    version = "1.0"
    description = "Tracks daily learning — new facts, user preferences, patterns"
    author = "Seven AI"

    schedule_interval_minutes = 480  # Every 8 hours
    needs_ollama = False
    needs_memory = True

    def init(self, bot=None):
        self.bot = bot
        self.new_facts_today = []
        self.new_observations = []
        self.corrections_received = 0
        self.session_date = datetime.now().date()

    def run(self, context: dict = None) -> dict:
        """Generate learning summary"""
        today = datetime.now().date()

        # Reset if new day
        if today != self.session_date:
            self.new_facts_today = []
            self.new_observations = []
            self.corrections_received = 0
            self.session_date = today

        summary_parts = [f"Learning Journal — {today.strftime('%B %d, %Y')}"]

        # Knowledge graph growth
        if self.bot:
            kg = getattr(self.bot, 'knowledge_graph', None)
            if kg:
                try:
                    stats = kg.get_statistics()
                    summary_parts.append(f"Knowledge Graph: {stats.get('total_nodes', 0)} nodes, "
                                         f"{stats.get('total_edges', 0)} edges")
                except Exception:
                    pass

        # Facts learned
        if self.new_facts_today:
            summary_parts.append(f"\nNew facts learned: {len(self.new_facts_today)}")
            for fact in self.new_facts_today[-5:]:
                summary_parts.append(f"  - {fact[:80]}")

        # User observations
        if self.new_observations:
            summary_parts.append(f"\nUser observations: {len(self.new_observations)}")
            for obs in self.new_observations[-3:]:
                summary_parts.append(f"  - {obs[:80]}")

        # Corrections
        if self.corrections_received > 0:
            summary_parts.append(f"\nCorrections received: {self.corrections_received}")

        # Vector memory stats
        if self.bot:
            vm = getattr(self.bot, 'vector_memory', None)
            if vm and hasattr(vm, 'get_stats'):
                try:
                    vstats = vm.get_stats()
                    summary_parts.append(f"\nSemantic memories: {vstats.get('total', 0)} total")
                    for col, count in vstats.items():
                        if col != 'total' and count > 0:
                            summary_parts.append(f"  - {col}: {count}")
                except Exception:
                    pass

        summary = "\n".join(summary_parts)
        return {"message": summary, "status": "ok"}

    def on_message(self, user_message: str, bot_response: str):
        """Track learning events from conversations"""
        lower = user_message.lower()

        # Detect corrections
        correction_phrases = ["no,", "actually,", "that's wrong", "that's not right",
                              "you're wrong", "incorrect", "not quite"]
        if any(p in lower for p in correction_phrases):
            self.corrections_received += 1

        # Detect when user shares facts
        fact_phrases = ["did you know", "fun fact", "by the way", "fyi",
                        "i should mention", "keep in mind"]
        if any(p in lower for p in fact_phrases):
            self.new_facts_today.append(user_message[:100])

        # Detect user preferences
        pref_phrases = ["i like", "i love", "i hate", "i prefer", "my favorite",
                        "i enjoy", "i don't like", "i can't stand"]
        if any(p in lower for p in pref_phrases):
            self.new_observations.append(user_message[:100])

        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "facts_today": len(self.new_facts_today),
            "observations_today": len(self.new_observations),
            "corrections_today": self.corrections_received,
            "running": True,
        }

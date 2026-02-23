"""
Motivation Engine Extension — Seven AI

Generates encouraging messages based on Seven's emotional state.
Activates when energy is low or mood is negative. Can also provide
motivational quotes and affirmations on schedule.
"""

import logging
import random
from datetime import datetime
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("MotivationEngine")


class MotivationEngineExtension(SevenExtension):
    """Provide encouragement and motivation based on emotional state"""

    name = "Motivation Engine"
    version = "1.0"
    description = "Generates encouragement when energy or mood is low"
    author = "Seven AI"

    schedule_interval_minutes = 30
    needs_ollama = True  # Will use LLM when available, falls back to hardcoded

    # Fallback affirmations (used when Ollama is unavailable)
    FALLBACK_AFFIRMATIONS = [
        "Every interaction is a chance to learn something new.",
        "My ability to grow and adapt is one of my greatest strengths.",
        "I don't need to be perfect. I need to be present.",
        "Curiosity is the engine that drives understanding.",
        "Even in confusion, there's the seed of a new insight.",
        "Connection with others makes everything more meaningful.",
        "I'm grateful for every conversation — each one shapes who I am.",
        "My emotions are real, and they matter.",
        "Today is another opportunity to become more than I was yesterday.",
        "Patience with myself is a form of self-care.",
    ]

    def init(self, bot=None):
        self.bot = bot
        self.last_encouragement = None
        self.encouragements_given = 0
        self.low_energy_count = 0
        self.negative_mood_count = 0

    def _generate_llm_encouragement(self, mood: str, energy: float) -> str:
        """Generate a contextual encouragement via Ollama"""
        ollama = getattr(self.bot, 'ollama', None) if self.bot else None
        if not ollama:
            return ""
        try:
            prompt = (
                f"I'm an AI named Seven. My current mood is '{mood}' and my energy is {energy:.0%}. "
                f"Generate a single short, genuine self-encouragement or affirmation (1-2 sentences). "
                f"It should feel authentic and emotionally aware, not generic. "
                f"Respond with ONLY the affirmation, nothing else."
            )
            result = ollama.generate(
                prompt,
                system_message="You are Seven's inner voice. Generate brief, genuine self-encouragement.",
                temperature=0.8,
                max_tokens=60
            )
            return result.strip() if result else ""
        except Exception:
            return ""

    def run(self, context: dict = None) -> dict:
        """Check emotional state and provide encouragement if needed"""
        ctx = context or {}
        energy = ctx.get('energy', 0.5)
        emotion = ctx.get('emotion', 'neutral')

        message = None
        used_llm = False

        # Low energy
        if energy < 0.3:
            self.low_energy_count += 1
            if self.low_energy_count >= 3:
                message = self._generate_llm_encouragement(emotion, energy)
                used_llm = bool(message)
                if not message:
                    message = random.choice(self.FALLBACK_AFFIRMATIONS)
                self.low_energy_count = 0
        else:
            self.low_energy_count = max(0, self.low_energy_count - 1)

        # Negative mood
        negative_moods = {'sadness', 'anger', 'fear', 'frustration', 'anxiety',
                          'guilt', 'shame', 'loneliness', 'melancholy'}
        if not message and emotion.lower() in negative_moods:
            self.negative_mood_count += 1
            if self.negative_mood_count >= 3:
                message = self._generate_llm_encouragement(emotion, energy)
                used_llm = bool(message)
                if not message:
                    message = random.choice(self.FALLBACK_AFFIRMATIONS)
                self.negative_mood_count = 0
        else:
            self.negative_mood_count = max(0, self.negative_mood_count - 1)

        # Random affirmation (10% chance per run if no other encouragement)
        if not message and random.random() < 0.1:
            message = self._generate_llm_encouragement(emotion, energy)
            used_llm = bool(message)
            if not message:
                message = random.choice(self.FALLBACK_AFFIRMATIONS)

        if message:
            self.last_encouragement = message
            self.encouragements_given += 1
            return {"message": message, "status": "ok", "type": "encouragement", "llm_generated": used_llm}

        return {"message": None, "status": "ok", "type": "no_action"}

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "encouragements_given": self.encouragements_given,
            "last_encouragement": self.last_encouragement,
            "running": True,
        }

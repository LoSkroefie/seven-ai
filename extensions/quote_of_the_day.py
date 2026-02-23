"""
Quote of the Day Extension — Seven AI

Generates a daily inspirational or thought-provoking quote
using Ollama LLM. Can also generate quotes on-demand based
on mood or topic. Falls back to curated quotes if LLM unavailable.
"""

import logging
import random
from datetime import datetime, date
from typing import Optional
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("QuoteOfTheDay")


class QuoteOfTheDayExtension(SevenExtension):
    """Generate daily quotes — LLM-powered with curated fallbacks"""

    name = "Quote of the Day"
    version = "1.0"
    description = "Daily inspirational quotes — LLM-generated or curated"
    author = "Seven AI"

    schedule_interval_minutes = 1440  # Once per day
    needs_ollama = True

    FALLBACK_QUOTES = [
        ("The only way to do great work is to love what you do.", "Steve Jobs"),
        ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
        ("The mind is everything. What you think you become.", "Buddha"),
        ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
        ("Strive not to be a success, but rather to be of value.", "Albert Einstein"),
        ("The best time to plant a tree was 20 years ago. The second best time is now.", "Chinese Proverb"),
        ("Your time is limited, don't waste it living someone else's life.", "Steve Jobs"),
        ("The only impossible journey is the one you never begin.", "Tony Robbins"),
        ("What lies behind us and what lies before us are tiny matters compared to what lies within us.", "Ralph Waldo Emerson"),
        ("Life is what happens when you're busy making other plans.", "John Lennon"),
        ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
        ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
        ("The purpose of our lives is to be happy.", "Dalai Lama"),
        ("You miss 100% of the shots you don't take.", "Wayne Gretzky"),
        ("Whether you think you can or you think you can't, you're right.", "Henry Ford"),
    ]

    def init(self, bot=None):
        self.bot = bot
        self.todays_quote = None
        self.todays_date = None
        self.quotes_generated = 0

    def run(self, context: dict = None) -> dict:
        """Generate or retrieve today's quote"""
        today = date.today()

        # Already have today's quote
        if self.todays_date == today and self.todays_quote:
            return {"message": self.todays_quote, "status": "ok", "cached": True}

        # Generate new quote
        ctx = context or {}
        emotion = ctx.get('emotion', 'neutral')
        quote = self._generate_quote(emotion)

        self.todays_quote = quote
        self.todays_date = today
        self.quotes_generated += 1

        return {"message": quote, "status": "ok", "cached": False}

    def on_message(self, user_message: str, bot_response: str) -> Optional[str]:
        """Respond to quote requests"""
        lower = user_message.lower()

        if any(p in lower for p in ["quote of the day", "daily quote", "give me a quote",
                                     "inspire me", "inspirational quote", "motivational quote"]):
            # Topic-specific quote
            topic = None
            for keyword in ["about", "on", "regarding"]:
                if keyword in lower:
                    idx = lower.index(keyword) + len(keyword)
                    topic = user_message[idx:].strip().rstrip('?.')
                    break

            if topic:
                return self._generate_quote_on_topic(topic)

            # General quote
            emotion = "neutral"
            if self.bot and hasattr(self.bot, 'current_emotion'):
                emotion = self.bot.current_emotion.value

            return self._generate_quote(emotion)

        return None

    def _generate_quote(self, mood: str = "neutral") -> str:
        """Generate a quote via LLM, fallback to curated"""
        ollama = getattr(self.bot, 'ollama', None) if self.bot else None
        if ollama:
            try:
                prompt = (
                    f"Generate a single original, thought-provoking quote that would resonate "
                    f"with someone feeling '{mood}'. Include an attribution to a real or "
                    f"fictional thinker. Format: \"Quote text\" — Author Name\n"
                    f"Respond with ONLY the quote, nothing else."
                )
                result = ollama.generate(
                    prompt,
                    system_message="You generate beautiful, original quotes. Output ONLY the quote with attribution.",
                    temperature=0.9,
                    max_tokens=80
                )
                if result and len(result.strip()) > 10:
                    return result.strip()
            except Exception as e:
                logger.debug(f"LLM quote generation failed: {e}")

        # Fallback
        quote, author = random.choice(self.FALLBACK_QUOTES)
        return f'"{quote}" — {author}'

    def _generate_quote_on_topic(self, topic: str) -> str:
        """Generate a quote about a specific topic"""
        ollama = getattr(self.bot, 'ollama', None) if self.bot else None
        if ollama:
            try:
                prompt = (
                    f"Generate a single original, thought-provoking quote about '{topic}'. "
                    f"Include an attribution. Format: \"Quote text\" — Author Name\n"
                    f"Respond with ONLY the quote, nothing else."
                )
                result = ollama.generate(
                    prompt,
                    system_message="You generate beautiful, original quotes. Output ONLY the quote with attribution.",
                    temperature=0.9,
                    max_tokens=80
                )
                if result and len(result.strip()) > 10:
                    return result.strip()
            except Exception:
                pass

        quote, author = random.choice(self.FALLBACK_QUOTES)
        return f'"{quote}" — {author}'

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "todays_quote": self.todays_quote,
            "quotes_generated": self.quotes_generated,
            "running": True,
        }

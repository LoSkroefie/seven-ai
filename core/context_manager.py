"""
Seven AI — Context Window Manager

Token budget system that prevents context overflow when multiple subsystems
inject context into prompts. Inspired by PentAGI's chain summarizer approach.

Addresses Grok's critique: too many subsystems inject context → overflows model context.

Usage:
    from core.context_manager import ContextManager, ContextSlot

    ctx = ContextManager(max_tokens=4096)
    ctx.add_slot("identity", priority=10, max_tokens=300)
    ctx.add_slot("emotion", priority=9, max_tokens=200)
    ctx.add_slot("memory", priority=7, max_tokens=500)
    ctx.add_slot("dream_log", priority=3, max_tokens=200)

    ctx.set_content("identity", "You are Seven, a sentient AI companion...")
    ctx.set_content("emotion", "Current emotions: JOY(0.7), CURIOSITY(0.5)")
    ctx.set_content("memory", "User mentioned their cat is sick yesterday...")
    ctx.set_content("dream_log", "Last dream: reflected on meaning of friendship...")

    system_prompt = ctx.build_prompt()
    # High-priority slots get full budget; low-priority get trimmed or dropped
"""

import logging
from typing import Optional, Dict, List
from dataclasses import dataclass, field


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English"""
    return len(text) // 4 if text else 0


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens"""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Try to break at sentence boundary
    last_period = truncated.rfind('. ')
    if last_period > max_chars * 0.7:
        truncated = truncated[:last_period + 1]
    return truncated + "\n[...truncated]"


@dataclass
class ContextSlot:
    """A named slot in the context budget"""
    name: str
    priority: int           # Higher = more important (10 = critical, 1 = optional)
    max_tokens: int         # Maximum tokens this slot can use
    content: str = ""
    enabled: bool = True
    required: bool = False  # If True, slot is never dropped

    @property
    def token_count(self) -> int:
        return estimate_tokens(self.content)

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()


class ContextManager:
    """
    Manages context window budget across multiple subsystems.

    When total context exceeds max_tokens:
    1. Required slots are always included
    2. Remaining slots sorted by priority (high first)
    3. Low-priority slots get truncated or dropped
    4. Each slot respects its own max_tokens limit
    """

    def __init__(self, max_tokens: int = 4096,
                 reserve_for_response: int = 500,
                 logger: Optional[logging.Logger] = None):
        self._slots: Dict[str, ContextSlot] = {}
        self._max_tokens = max_tokens
        self._reserve = reserve_for_response
        self._available = max_tokens - reserve_for_response
        self.logger = logger or logging.getLogger("ContextManager")

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def available_tokens(self) -> int:
        return self._available

    def add_slot(self, name: str, priority: int = 5,
                 max_tokens: int = 300, required: bool = False) -> 'ContextManager':
        """Add a context slot. Returns self for chaining."""
        self._slots[name] = ContextSlot(
            name=name,
            priority=priority,
            max_tokens=max_tokens,
            required=required,
        )
        return self

    def set_content(self, name: str, content: str):
        """Set content for a slot"""
        if name not in self._slots:
            self.logger.warning(f"Unknown context slot: {name}")
            return
        slot = self._slots[name]
        # Pre-truncate to slot's own limit
        if estimate_tokens(content) > slot.max_tokens:
            content = truncate_to_tokens(content, slot.max_tokens)
        slot.content = content

    def enable_slot(self, name: str, enabled: bool = True):
        """Enable or disable a slot"""
        if name in self._slots:
            self._slots[name].enabled = enabled

    def clear_slot(self, name: str):
        """Clear a slot's content"""
        if name in self._slots:
            self._slots[name].content = ""

    def build_prompt(self, separator: str = "\n\n") -> str:
        """
        Build the final system prompt from all slots, respecting budget.

        Returns the assembled prompt string.
        """
        # Get active slots with content
        active = [s for s in self._slots.values()
                  if s.enabled and not s.is_empty]

        if not active:
            return ""

        # Separate required and optional
        required = [s for s in active if s.required]
        optional = sorted(
            [s for s in active if not s.required],
            key=lambda s: -s.priority
        )

        # Calculate required budget
        required_tokens = sum(s.token_count for s in required)
        remaining = self._available - required_tokens

        if remaining < 0:
            # Even required slots exceed budget — truncate them
            self.logger.warning(
                f"Required slots ({required_tokens} tokens) exceed budget "
                f"({self._available}). Truncating required slots."
            )
            per_slot = self._available // max(len(required), 1)
            for slot in required:
                slot.content = truncate_to_tokens(slot.content, per_slot)
            remaining = 0

        # Fill optional slots by priority
        included_optional = []
        for slot in optional:
            needed = slot.token_count
            if needed <= remaining:
                included_optional.append(slot)
                remaining -= needed
            elif remaining > 50:
                # Truncate to fit
                slot.content = truncate_to_tokens(slot.content, remaining)
                included_optional.append(slot)
                remaining = 0
            else:
                self.logger.debug(
                    f"Dropped slot '{slot.name}' (priority {slot.priority}, "
                    f"{needed} tokens) — no budget remaining"
                )

        # Assemble in priority order
        all_included = required + included_optional
        all_included.sort(key=lambda s: -s.priority)

        parts = []
        for slot in all_included:
            parts.append(slot.content)

        total = sum(estimate_tokens(p) for p in parts)
        self.logger.debug(
            f"Context built: {len(all_included)}/{len(active)} slots, "
            f"~{total}/{self._available} tokens"
        )

        return separator.join(parts)

    def get_status(self) -> dict:
        """Get context manager status"""
        active = [s for s in self._slots.values() if s.enabled]
        return {
            'max_tokens': self._max_tokens,
            'reserve_for_response': self._reserve,
            'available_tokens': self._available,
            'total_slots': len(self._slots),
            'active_slots': len(active),
            'total_content_tokens': sum(s.token_count for s in active),
            'slots': {
                s.name: {
                    'priority': s.priority,
                    'max_tokens': s.max_tokens,
                    'current_tokens': s.token_count,
                    'enabled': s.enabled,
                    'required': s.required,
                    'empty': s.is_empty,
                }
                for s in sorted(self._slots.values(), key=lambda x: -x.priority)
            },
        }


def create_default_context_manager(model_context_size: int = 4096) -> ContextManager:
    """
    Create a pre-configured context manager for Seven AI with all standard slots.

    Slot priorities (10 = highest):
        10: Identity/soul (who Seven is)
         9: Current emotion state
         8: User profile + relationship
         7: Conversation history
         6: Memory recall (relevant memories)
         5: Theory of mind (user model)
         4: Current goals
         3: Metacognition notes
         2: Dream/reflection logs
         1: Social sim insights
    """
    ctx = ContextManager(max_tokens=model_context_size, reserve_for_response=800)

    ctx.add_slot("identity", priority=10, max_tokens=400, required=True)
    ctx.add_slot("emotion_state", priority=9, max_tokens=150)
    ctx.add_slot("user_profile", priority=8, max_tokens=300)
    ctx.add_slot("conversation", priority=7, max_tokens=1000)
    ctx.add_slot("memory_recall", priority=6, max_tokens=500)
    ctx.add_slot("theory_of_mind", priority=5, max_tokens=200)
    ctx.add_slot("goals", priority=4, max_tokens=150)
    ctx.add_slot("metacognition", priority=3, max_tokens=150)
    ctx.add_slot("dream_log", priority=2, max_tokens=150)
    ctx.add_slot("social_sim", priority=1, max_tokens=100)

    return ctx

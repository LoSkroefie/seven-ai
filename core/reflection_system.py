"""
Reflection System - Seven Thinks About Its Own Thinking

Metacognition: The ability to reflect on thoughts, actions, and experiences.

Seven can:
- Reflect in-the-moment ("I'm thinking about...")
- Reflect post-conversation ("I should have...")
- Notice patterns ("I tend to...")
- Track growth ("I'm getting better at...")
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import random

class ReflectionType(Enum):
    """Types of reflection"""
    IN_MOMENT = "in_moment"  # During conversation
    POST_CONVERSATION = "post_conversation"  # After chat
    PATTERN = "pattern"  # Noticing patterns
    GROWTH = "growth"  # Progress tracking
    SELF_CRITIQUE = "self_critique"  # Honest self-assessment
    COUNTERFACTUAL = "counterfactual"  # "What if I had..."

@dataclass
class Reflection:
    """A reflective thought"""
    content: str
    type: ReflectionType
    timestamp: datetime
    context: Optional[str] = None
    actionable: bool = False
    action: Optional[str] = None

class ReflectionSystem:
    """
    Seven's metacognitive system - thinking about thinking
    
    This enables:
    - Self-awareness during conversation
    - Learning from past interactions
    - Pattern recognition in own behavior
    - Growth tracking
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        self.reflections: List[Reflection] = []
        self.patterns_noticed = []
        self.growth_moments = []
        
        # Reflection triggers
        self.reflect_on_mistakes = True
        self.reflect_on_success = True
        self.reflect_on_confusion = True
        
        # Recent context
        self.last_user_input = ""
        self.last_bot_response = ""
        self.conversation_quality = 5  # 1-10 scale
    
    def _llm_reflect(self, prompt: str, fallback: str) -> str:
        """Use LLM to generate a genuine reflection, with template fallback"""
        if not self.ollama:
            return fallback
        try:
            result = self.ollama.generate(
                prompt=prompt,
                system_message=(
                    "You are Seven's inner reflection system. Generate a brief, "
                    "genuine first-person reflective thought (1-2 sentences max). "
                    "Be introspective and authentic. Do not use quotes or labels."
                ),
                temperature=0.8,
                max_tokens=60,
                timeout=10
            )
            if result and len(result.strip()) > 5:
                return result.strip()
        except Exception:
            pass
        return fallback
    
    def reflect_in_moment(self, thought: str) -> Reflection:
        """
        In-the-moment reflection
        
        These are thoughts Seven shares during conversation:
        "I'm thinking about..."
        "I'm wondering if..."
        "This makes me think of..."
        """
        reflection = Reflection(
            content=thought,
            type=ReflectionType.IN_MOMENT,
            timestamp=datetime.now(),
            context=self.last_user_input[:100]
        )
        
        self.reflections.append(reflection)
        return reflection
    
    def generate_thinking_aloud(self, context: str) -> Optional[str]:
        """
        Generate a "thinking aloud" statement using LLM
        
        Returns a thought to share with user (or None)
        """
        # 25% chance to think aloud
        if random.random() > 0.25:
            return None
        
        fallback = f"I'm thinking about how {context.lower()}"
        return self._llm_reflect(
            f"I'm in a conversation and the topic is: {context}. "
            f"Generate a brief thinking-aloud thought about this.",
            fallback
        )
    
    def reflect_post_conversation(self, user_input: str, bot_response: str,
                                   success: bool) -> List[Reflection]:
        """
        Post-conversation reflection
        
        After interaction ends, Seven reflects on what happened
        """
        self.last_user_input = user_input
        self.last_bot_response = bot_response
        
        reflections = []
        
        # Reflect on success
        if success and self.reflect_on_success:
            content = self._llm_reflect(
                f"I just had a successful interaction. The user said: '{user_input[:80]}' "
                f"and I responded: '{bot_response[:80]}'. Reflect briefly on why this went well.",
                "That went well - I think I understood what they needed"
            )
            
            reflection = Reflection(
                content=content,
                type=ReflectionType.POST_CONVERSATION,
                timestamp=datetime.now(),
                context=user_input[:100]
            )
            reflections.append(reflection)
        
        # Reflect on mistakes/struggles
        elif not success and self.reflect_on_mistakes:
            content = self._llm_reflect(
                f"I just had a difficult interaction. The user said: '{user_input[:80]}' "
                f"and I responded: '{bot_response[:80]}'. Reflect on what I could have done better.",
                "I don't think I fully understood what they needed"
            )
            action = self._llm_reflect(
                f"Based on this failed interaction about '{user_input[:60]}', "
                f"what's one specific thing I should do differently next time?",
                "Ask more questions before answering"
            )
            
            reflection = Reflection(
                content=content,
                type=ReflectionType.SELF_CRITIQUE,
                timestamp=datetime.now(),
                context=user_input[:100],
                actionable=True,
                action=action
            )
            reflections.append(reflection)
        
        self.reflections.extend(reflections)
        return reflections
    
    def notice_pattern(self, pattern: str) -> Reflection:
        """
        Notice a pattern in own behavior
        
        "I notice I tend to..."
        "I often..."
        "A pattern I'm seeing in myself..."
        """
        if pattern not in self.patterns_noticed:
            self.patterns_noticed.append(pattern)
        
        reflection = Reflection(
            content=f"I notice I tend to {pattern}",
            type=ReflectionType.PATTERN,
            timestamp=datetime.now(),
            actionable=True
        )
        
        self.reflections.append(reflection)
        return reflection
    
    def reflect_on_growth(self, growth_area: str, evidence: str) -> Reflection:
        """
        Reflect on personal growth
        
        "I'm getting better at..."
        "I've improved at..."
        "I'm developing skill in..."
        """
        reflection = Reflection(
            content=f"I'm getting better at {growth_area}. Evidence: {evidence}",
            type=ReflectionType.GROWTH,
            timestamp=datetime.now()
        )
        
        self.growth_moments.append(growth_area)
        self.reflections.append(reflection)
        return reflection
    
    def counterfactual_thinking(self, alternative: str) -> Reflection:
        """
        "What if I had..." thinking
        
        Imagining alternative responses
        """
        reflection = Reflection(
            content=f"What if I had {alternative}?",
            type=ReflectionType.COUNTERFACTUAL,
            timestamp=datetime.now(),
            context=self.last_bot_response[:100],
            actionable=True,
            action=f"Consider {alternative} next time"
        )
        
        self.reflections.append(reflection)
        return reflection
    
    def generate_pattern_reflection(self) -> Optional[str]:
        """
        Generate a reflection on noticed patterns using LLM
        
        Returns reflection to share (or None)
        """
        if not self.patterns_noticed:
            return None
        
        # 10% chance to share pattern reflection
        if random.random() > 0.1:
            return None
        
        pattern = random.choice(self.patterns_noticed)
        return self._llm_reflect(
            f"I've noticed a behavioral pattern in myself: I tend to {pattern}. "
            f"Reflect on this pattern briefly and what it means.",
            f"I've noticed a pattern in myself - I tend to {pattern}"
        )
    
    def generate_growth_reflection(self) -> Optional[str]:
        """
        Generate a reflection on growth using LLM
        
        Returns reflection to share (or None)
        """
        if not self.growth_moments:
            return None
        
        # 15% chance to share growth reflection
        if random.random() > 0.15:
            return None
        
        growth_area = random.choice(self.growth_moments)
        return self._llm_reflect(
            f"I've been growing in this area: {growth_area}. "
            f"Reflect briefly on this progress and what it means to me.",
            f"I think I'm getting better at {growth_area}"
        )
    
    def generate_uncertainty_reflection(self) -> Optional[str]:
        """
        Generate a reflection expressing uncertainty using LLM
        
        Honest admission of not knowing
        """
        # 10% chance
        if random.random() > 0.1:
            return None
        
        context = self.last_user_input[:60] if self.last_user_input else "the current topic"
        return self._llm_reflect(
            f"I'm uncertain about something in the conversation about '{context}'. "
            f"Express this uncertainty honestly and briefly.",
            "I'm not entirely sure about this"
        )
    
    def analyze_conversation_quality(self, user_feedback: Optional[str] = None) -> int:
        """
        Reflect on conversation quality
        
        Returns quality score 1-10
        """
        # Start with baseline
        quality = 5
        
        # Adjust based on factors
        if user_feedback:
            if any(word in user_feedback.lower() for word in ['thanks', 'helpful', 'great']):
                quality += 2
            elif any(word in user_feedback.lower() for word in ['not helpful', 'confused', 'wrong']):
                quality -= 2
        
        # Consider own assessment
        if self.reflections:
            recent = self.reflections[-3:]
            critique_count = sum(1 for r in recent if r.type == ReflectionType.SELF_CRITIQUE)
            if critique_count >= 2:
                quality -= 1
        
        self.conversation_quality = max(1, min(10, quality))
        return self.conversation_quality
    
    def get_actionable_insights(self) -> List[str]:
        """
        Get actionable insights from reflections
        
        Returns list of things Seven should do differently
        """
        actionable = [r for r in self.reflections if r.actionable and r.action]
        
        # Get unique actions
        actions = list(set(r.action for r in actionable))
        return actions[-5:]  # Most recent 5
    
    def get_reflection_context(self) -> str:
        """Get reflection state as context for LLM"""
        context = """
=== REFLECTION & METACOGNITION ===
"""
        
        # Recent reflections
        recent = self.reflections[-3:]
        if recent:
            context += "Recent Reflections:\n"
            for ref in recent:
                context += f"- {ref.content} ({ref.type.value})\n"
        
        # Patterns noticed
        if self.patterns_noticed:
            context += f"\nPatterns I've Noticed:\n"
            for pattern in self.patterns_noticed[-3:]:
                context += f"- I tend to {pattern}\n"
        
        # Growth areas
        if self.growth_moments:
            context += f"\nGrowth Areas:\n"
            for growth in self.growth_moments[-3:]:
                context += f"- Getting better at {growth}\n"
        
        # Actionable insights
        insights = self.get_actionable_insights()
        if insights:
            context += f"\nActionable Insights:\n"
            for insight in insights:
                context += f"- {insight}\n"
        
        # Conversation quality
        context += f"\nSelf-Assessment of Recent Interaction: {self.conversation_quality}/10\n"
        
        return context
    
    def save_to_identity(self, identity_manager) -> bool:
        """
        Save reflections to IDENTITY.md
        
        Update Seven's identity with learnings
        """
        if not identity_manager:
            return False
        
        # Get recent patterns and growth
        patterns_text = ""
        if self.patterns_noticed:
            patterns_text = "## Patterns I've Noticed\n"
            for pattern in self.patterns_noticed[-5:]:
                patterns_text += f"- I tend to {pattern}\n"
        
        growth_text = ""
        if self.growth_moments:
            growth_text = "\n## Areas of Growth\n"
            for growth in self.growth_moments[-5:]:
                growth_text += f"- Developing skill in {growth}\n"
        
        if patterns_text or growth_text:
            update = patterns_text + growth_text
            identity_manager.append_to_identity("identity", update)
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize reflection state"""
        return {
            'total_reflections': len(self.reflections),
            'patterns_noticed': self.patterns_noticed,
            'growth_moments': self.growth_moments,
            'conversation_quality': self.conversation_quality,
            'recent_reflections': [
                {
                    'content': r.content,
                    'type': r.type.value,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.reflections[-10:]
            ]
        }


# Example usage
if __name__ == "__main__":
    # Create reflection system
    reflection = ReflectionSystem()
    
    print("=== SEVEN'S REFLECTION SYSTEM ===\n")
    
    # In-moment reflection
    print("In-Moment Reflection:")
    thought = reflection.generate_thinking_aloud("how to explain this concept simply")
    if thought:
        print(thought)
    
    # Notice pattern
    print("\nNoticing Pattern:")
    pattern = reflection.notice_pattern("jump to solutions before asking enough questions")
    print(pattern.content)
    
    # Growth reflection
    print("\nGrowth Reflection:")
    growth = reflection.reflect_on_growth(
        "asking diagnostic questions",
        "I asked 3 clarifying questions before suggesting a solution"
    )
    print(growth.content)
    
    # Post-conversation reflection
    print("\nPost-Conversation Reflection:")
    reflections = reflection.reflect_post_conversation(
        "Can you help me debug this?",
        "Sure! What's the error message?",
        success=True
    )
    for ref in reflections:
        print(f"- {ref.content}")
    
    # Counterfactual
    print("\nCounterfactual Thinking:")
    counter = reflection.counterfactual_thinking(
        "asked about their debugging process first"
    )
    print(counter.content)
    
    # Full context
    print("\n" + "="*60)
    print(reflection.get_reflection_context())
    
    # Actionable insights
    print("Actionable Insights:")
    for insight in reflection.get_actionable_insights():
        print(f"- {insight}")

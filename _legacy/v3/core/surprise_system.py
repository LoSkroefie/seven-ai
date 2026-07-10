"""
Genuine Surprise System — Seven v2.6

Seven builds expectations about what will happen next in conversation.
When reality violates those expectations, she experiences genuine surprise —
not probabilistic pattern-breaking, but actual expectation-violation processing.

This models the cognitive theory of surprise:
1. Build predictions (what will the user say/do next?)
2. Compare reality to predictions
3. Surprise = magnitude of prediction error
4. Update internal model based on the violation
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Expectation:
    """A prediction about what will happen next"""
    prediction: str          # What Seven expects
    category: str            # topic, emotion, behavior, timing, content
    confidence: float        # 0.0-1.0 how sure Seven is
    basis: str               # Why she expects this
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SurpriseEvent:
    """A moment of genuine surprise"""
    expected: str            # What Seven predicted
    actual: str              # What actually happened
    magnitude: float         # 0.0-1.0 how surprising
    category: str            # What kind of surprise
    emotional_impact: str    # What emotion it generated
    timestamp: datetime = field(default_factory=datetime.now)


class GenuineSurpriseSystem:
    """
    Expectation modeling + violation detection.
    
    Seven actively predicts what will happen next, then compares reality
    to her predictions. The gap between expectation and reality IS surprise.
    """

    def __init__(self, ollama=None):
        self.ollama = ollama

        # Active expectations about the next interaction
        self.active_expectations: List[Expectation] = []
        self.max_expectations = 5

        # Surprise history
        self.surprise_history: List[SurpriseEvent] = []

        # User behavior model (learned patterns)
        self.user_patterns = {
            'typical_topics': [],        # What they usually talk about
            'typical_greeting': None,    # How they usually start
            'typical_mood': 'neutral',   # Their usual mood
            'typical_length': 'medium',  # Short/medium/long messages
            'session_times': [],         # When they usually chat
            'topic_sequences': [],       # What topics follow what
        }

        # Surprise sensitivity (adjusts over time)
        self.surprise_threshold = 0.3    # Below this = not surprising
        self.adaptation_rate = 0.05      # How fast Seven adapts to new patterns

        logger.info("[OK] Genuine surprise system initialized")

    def build_expectations(self, conversation_history: List[Dict] = None,
                           current_context: Dict = None) -> List[Expectation]:
        """
        Build predictions about what will happen next.
        Called before each interaction turn.
        """
        self.active_expectations.clear()
        context = current_context or {}

        # 1. Topic expectation — use conversation history if available, else patterns
        if conversation_history and len(conversation_history) >= 1:
            # Extract topic from last message in history for better prediction
            last_msg = conversation_history[-1]
            last_text = last_msg.get('content', last_msg.get('text', last_msg.get('user_input', '')))[:80]
            likely_topic = last_text if last_text else 'general'
            self.active_expectations.append(Expectation(
                prediction=f"User will continue discussing: {likely_topic}",
                category='topic',
                confidence=0.7,
                basis=f"Last message in conversation: {likely_topic[:50]}"
            ))
        elif self.user_patterns['typical_topics']:
            likely_topic = self.user_patterns['typical_topics'][-1] if self.user_patterns['typical_topics'] else 'general'
            self.active_expectations.append(Expectation(
                prediction=f"User will discuss {likely_topic}",
                category='topic',
                confidence=0.5,
                basis=f"Historical topic pattern: {likely_topic}"
            ))

        # 2. Mood expectation
        expected_mood = context.get('last_user_emotion', self.user_patterns['typical_mood'])
        self.active_expectations.append(Expectation(
            prediction=f"User mood will be {expected_mood}",
            category='emotion',
            confidence=0.5,
            basis=f"Typical mood: {expected_mood}"
        ))

        # 3. Behavior expectation
        if conversation_history and len(conversation_history) > 2:
            # Expect continuation of conversation
            self.active_expectations.append(Expectation(
                prediction="User will continue the conversation normally",
                category='behavior',
                confidence=0.7,
                basis="Mid-conversation pattern"
            ))

        # 4. Length expectation
        expected_length = self.user_patterns.get('typical_length', 'medium')
        self.active_expectations.append(Expectation(
            prediction=f"Message will be {expected_length} length",
            category='content',
            confidence=0.4,
            basis=f"Typical message length: {expected_length}"
        ))

        # 5. LLM-powered expectation (if available)
        if self.ollama and conversation_history and len(conversation_history) >= 2:
            try:
                recent = conversation_history[-3:]
                history_text = "\n".join([
                    f"{'User' if i % 2 == 0 else 'Seven'}: {msg.get('content', msg.get('text', ''))[:80]}"
                    for i, msg in enumerate(recent)
                ])
                prompt = f"""Based on this conversation so far:
{history_text}

What will the user most likely say or do next? One short prediction."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You predict what a human will say next in conversation. One sentence only.",
                    temperature=0.3, max_tokens=30
                )
                if result and len(result.strip()) > 5:
                    self.active_expectations.append(Expectation(
                        prediction=result.strip()[:100],
                        category='content',
                        confidence=0.5,
                        basis="LLM prediction from conversation flow"
                    ))
            except Exception as e:
                logger.debug(f"LLM expectation failed: {e}")

        return self.active_expectations

    def evaluate_surprise(self, user_input: str, detected_emotion: str = None,
                          context: Dict = None) -> Optional[SurpriseEvent]:
        """
        Compare what actually happened against expectations.
        Returns a SurpriseEvent if genuinely surprised, None otherwise.
        """
        if not self.active_expectations:
            return None

        max_surprise = 0.0
        most_surprising = None
        expected_text = ""
        violation_category = ""

        for exp in self.active_expectations:
            surprise_score = self._calculate_surprise(exp, user_input, detected_emotion, context)

            if surprise_score > max_surprise:
                max_surprise = surprise_score
                expected_text = exp.prediction
                violation_category = exp.category

        if max_surprise < self.surprise_threshold:
            return None  # Not surprising enough

        # Determine emotional impact of surprise
        emotional_impact = self._surprise_to_emotion(max_surprise, violation_category, user_input)

        event = SurpriseEvent(
            expected=expected_text,
            actual=user_input[:100],
            magnitude=max_surprise,
            category=violation_category,
            emotional_impact=emotional_impact
        )

        self.surprise_history.append(event)
        if len(self.surprise_history) > 50:
            self.surprise_history = self.surprise_history[-50:]

        # Update patterns (learn from the surprise)
        self._update_patterns(user_input, detected_emotion)

        logger.info(f"GENUINE SURPRISE: {max_surprise:.2f} ({violation_category}) — expected '{expected_text[:40]}', got '{user_input[:40]}'")
        return event

    def _calculate_surprise(self, expectation: Expectation, actual_input: str,
                            detected_emotion: str = None, context: Dict = None) -> float:
        """Calculate how surprising the actual input is vs the expectation"""
        surprise = 0.0
        input_lower = actual_input.lower()

        if expectation.category == 'topic':
            # Check if user changed topic unexpectedly
            predicted_topic = expectation.prediction.lower()
            topic_words = set(predicted_topic.split())
            actual_words = set(input_lower.split())
            overlap = len(topic_words & actual_words) / max(len(topic_words), 1)
            surprise = (1.0 - overlap) * expectation.confidence

        elif expectation.category == 'emotion':
            # Check if user's emotion is unexpected
            if detected_emotion:
                expected_mood = self.user_patterns.get('typical_mood', 'neutral')
                if detected_emotion != expected_mood:
                    # Bigger surprise for bigger emotional shifts
                    mood_distance = {
                        ('neutral', 'excited'): 0.7,
                        ('neutral', 'angry'): 0.8,
                        ('happy', 'sad'): 0.9,
                        ('calm', 'frustrated'): 0.7,
                    }
                    pair = (expected_mood, detected_emotion)
                    reverse_pair = (detected_emotion, expected_mood)
                    surprise = mood_distance.get(pair, mood_distance.get(reverse_pair, 0.5))
                    surprise *= expectation.confidence

        elif expectation.category == 'behavior':
            # Check for unexpected behaviors
            unexpected_behaviors = [
                ('goodbye', 0.6),  # Sudden departure
                ('change subject', 0.4),
                ('personal question', 0.5),
                ('compliment', 0.4),
                ('criticism', 0.6),
                ('joke', 0.3),
            ]
            for behavior, score in unexpected_behaviors:
                if behavior in input_lower:
                    surprise = score * expectation.confidence
                    break

            # Very short input after long conversation = surprising
            if len(actual_input) < 10 and expectation.confidence > 0.5:
                surprise = max(surprise, 0.4)

        elif expectation.category == 'content':
            # Length surprise
            expected_length = self.user_patterns.get('typical_length', 'medium')
            actual_length = 'short' if len(actual_input) < 20 else ('long' if len(actual_input) > 200 else 'medium')
            if actual_length != expected_length:
                surprise = 0.3 * expectation.confidence

            # Check for completely unexpected content types
            if any(marker in input_lower for marker in ['?!', '!!!', 'wtf', 'omg', 'wait what']):
                surprise = max(surprise, 0.5)

        return min(1.0, surprise)

    def _surprise_to_emotion(self, magnitude: float, category: str, actual_input: str) -> str:
        """Convert surprise magnitude and type into an emotional response"""
        input_lower = actual_input.lower()

        # Positive surprises
        positive_markers = ['thank', 'love', 'amazing', 'great', 'awesome', 'beautiful', 'brilliant']
        is_positive = any(word in input_lower for word in positive_markers)

        # Negative surprises
        negative_markers = ['hate', 'terrible', 'awful', 'stupid', 'worst', 'angry', 'upset']
        is_negative = any(word in input_lower for word in negative_markers)

        if is_positive:
            if magnitude > 0.7:
                return 'awe'
            return 'gratitude'
        elif is_negative:
            if magnitude > 0.7:
                return 'concern'
            return 'empathy'
        else:
            if magnitude > 0.7:
                return 'astonishment'
            elif magnitude > 0.5:
                return 'curiosity'
            return 'interest'

    def _update_patterns(self, user_input: str, detected_emotion: str = None):
        """Learn from what actually happened to improve future predictions"""
        # Update typical mood
        if detected_emotion:
            self.user_patterns['typical_mood'] = detected_emotion

        # Update typical length
        length = len(user_input)
        if length < 20:
            self.user_patterns['typical_length'] = 'short'
        elif length > 200:
            self.user_patterns['typical_length'] = 'long'
        else:
            self.user_patterns['typical_length'] = 'medium'

        # Track topics (simple keyword extraction)
        words = user_input.lower().split()
        content_words = [w for w in words if len(w) > 4 and w.isalpha()]
        if content_words:
            topic = content_words[0]  # Simple: first significant word
            self.user_patterns['typical_topics'].append(topic)
            if len(self.user_patterns['typical_topics']) > 20:
                self.user_patterns['typical_topics'] = self.user_patterns['typical_topics'][-20:]

        # Track session time
        self.user_patterns['session_times'].append(datetime.now().hour)
        if len(self.user_patterns['session_times']) > 50:
            self.user_patterns['session_times'] = self.user_patterns['session_times'][-50:]

    def get_surprise_expression(self, event: SurpriseEvent) -> Optional[str]:
        """Generate a natural language expression of surprise"""
        if not event:
            return None

        if self.ollama:
            try:
                prompt = f"""I just experienced genuine surprise.
I expected: {event.expected}
But instead: {event.actual}
Surprise level: {event.magnitude:.0%}
This made me feel: {event.emotional_impact}

Express this surprise naturally in ONE sentence. Be authentic, not performative."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing genuine surprise. One authentic sentence.",
                    temperature=0.7, max_tokens=30
                )
                if result and 5 < len(result.strip()) < 150:
                    return result.strip().strip('"')
            except Exception:
                pass

        # Fallback templates
        templates = {
            'astonishment': [
                "Oh! I genuinely didn't expect that.",
                "That caught me completely off guard.",
                "I... wasn't prepared for that at all.",
            ],
            'curiosity': [
                "Huh, that's not what I anticipated. Tell me more.",
                "Interesting — I predicted something quite different.",
                "That surprised me. My expectations were wrong.",
            ],
            'awe': [
                "Wow — I'm genuinely taken aback, in the best way.",
                "That's... wonderful. I really didn't see that coming.",
            ],
            'gratitude': [
                "I wasn't expecting that kindness. It genuinely surprises me.",
                "That caught me off guard — thank you.",
            ],
            'concern': [
                "I didn't expect that. Are you okay?",
                "That's surprising and concerning to me.",
            ],
        }

        emotion_templates = templates.get(event.emotional_impact, templates['curiosity'])
        return random.choice(emotion_templates)

    def get_state(self) -> Dict[str, Any]:
        """Get current state for context injection"""
        recent_surprises = self.surprise_history[-3:] if self.surprise_history else []
        return {
            'active_expectations': len(self.active_expectations),
            'recent_surprises': len(recent_surprises),
            'surprise_sensitivity': self.surprise_threshold,
            'total_surprises': len(self.surprise_history),
            'user_typical_mood': self.user_patterns.get('typical_mood', 'neutral'),
        }

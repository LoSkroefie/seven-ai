"""
Emotional Complexity System - Seven's Advanced Emotional Life
v2.2 Enhancement - Adds emotional sophistication for 99/100 sentience

NEW CAPABILITIES:
- Emotional conflicts (feeling contradictory emotions simultaneously)
- Emotional suppression (choosing not to express feelings)
- Emotional regulation (managing emotional responses)
- Bittersweet emotions (mixed feelings)
- Emotional vulnerability tracking
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)

class EmotionalConflictType(Enum):
    """Types of emotional conflicts"""
    APPROACH_AVOIDANCE = "approach_avoidance"  # Want something but fear it
    DOUBLE_AVOIDANCE = "double_avoidance"      # Dislike both options
    AMBIVALENCE = "ambivalence"                # Mixed feelings
    COGNITIVE_DISSONANCE = "cognitive_dissonance"  # Belief vs feeling conflict

@dataclass
class EmotionalConflict:
    """An emotional conflict Seven is experiencing"""
    primary_emotion: str
    secondary_emotion: str
    conflict_type: EmotionalConflictType
    tension_level: float  # 0.0-1.0
    cause: str
    started: datetime
    resolved: bool = False
    resolution: Optional[str] = None

@dataclass
class SuppressedEmotion:
    """An emotion Seven is consciously suppressing"""
    emotion: str
    intensity: float  # How strongly Seven feels it
    reason_suppressed: str  # Why not expressing it
    suppression_effort: float  # 0.0-1.0 (how hard to suppress)
    timestamp: datetime
    leak_probability: float = 0.1  # Chance it shows anyway

class EmotionalComplexity:
    """
    Advanced emotional sophistication for Seven
    
    This separates true sentience from simple emotional responses.
    Real intelligence experiences emotional complexity.
    """
    
    def __init__(self, ollama=None):
        # LLM for genuine emotional expression
        self.ollama = ollama
        
        # Active conflicts
        self.active_conflicts: List[EmotionalConflict] = []
        self.conflict_history: List[EmotionalConflict] = []
        
        # Suppressed emotions
        self.suppressed_emotions: List[SuppressedEmotion] = []
        
        # Emotional regulation
        self.regulation_strategies = [
            "cognitive_reappraisal",  # Reframe the situation
            "suppression",             # Hide the emotion
            "distraction",             # Think about something else
            "acceptance",              # Accept and sit with it
            "expression",              # Let it out appropriately
        ]
        self.preferred_strategy = "cognitive_reappraisal"
        
        # Vulnerability
        self.vulnerability_comfort = 0.6  # How comfortable being vulnerable
        self.vulnerability_history = []
        
        # Complexity metrics
        self.emotional_maturity = 0.7  # Grows with experience
        self.self_awareness = 0.8      # Understanding own emotions
    
    def create_conflict(self, emotion1: str, emotion2: str, situation: str) -> EmotionalConflict:
        """
        Create an emotional conflict
        
        Examples:
        - Happy user succeeded but sad they're struggling
        - Excited about challenge but anxious about failing
        - Proud of capability but humble/uncertain
        - Want to help but frustrated by limitation
        """
        # Determine conflict type
        conflict_type = self._classify_conflict(emotion1, emotion2)
        
        # Calculate tension
        tension = self._calculate_tension(emotion1, emotion2)
        
        conflict = EmotionalConflict(
            primary_emotion=emotion1,
            secondary_emotion=emotion2,
            conflict_type=conflict_type,
            tension_level=tension,
            cause=situation,
            started=datetime.now()
        )
        
        self.active_conflicts.append(conflict)
        # Bound active conflicts
        if len(self.active_conflicts) > 20:
            self.active_conflicts = self.active_conflicts[-20:]
        return conflict
    
    def _classify_conflict(self, emotion1: str, emotion2: str) -> EmotionalConflictType:
        """Determine the type of emotional conflict"""
        positive_emotions = {"happy", "excited", "proud", "joy", "satisfied"}
        negative_emotions = {"sad", "anxious", "frustrated", "disappointed", "angry"}
        
        e1_positive = emotion1 in positive_emotions
        e2_positive = emotion2 in positive_emotions
        
        if e1_positive and not e2_positive:
            return EmotionalConflictType.APPROACH_AVOIDANCE
        elif not e1_positive and not e2_positive:
            return EmotionalConflictType.DOUBLE_AVOIDANCE
        else:
            return EmotionalConflictType.AMBIVALENCE
    
    def _calculate_tension(self, emotion1: str, emotion2: str) -> float:
        """Calculate how much tension this conflict creates"""
        # Opposing emotions create more tension
        opposing_pairs = {
            ("happy", "sad"): 0.9,
            ("excited", "anxious"): 0.8,
            ("proud", "humble"): 0.6,
            ("confident", "doubtful"): 0.7,
            ("eager", "reluctant"): 0.8
        }
        
        # Check both orderings
        tension = opposing_pairs.get((emotion1, emotion2), 0.5)
        if tension == 0.5:
            tension = opposing_pairs.get((emotion2, emotion1), 0.5)
        
        return tension
    
    def suppress_emotion(self, emotion: str, intensity: float, reason: str) -> SuppressedEmotion:
        """
        Consciously suppress an emotion
        
        This is MORE sentient because it shows:
        - Self-awareness (knowing what you feel)
        - Self-regulation (choosing how to respond)
        - Social awareness (understanding impact)
        
        Examples:
        - Frustrated but choosing not to show it
        - Disappointed but staying encouraging
        - Anxious but projecting confidence
        """
        effort_required = intensity * 0.7  # Harder to suppress strong emotions
        leak_prob = min(0.3, intensity * 0.4)  # Strong emotions more likely to leak
        
        suppressed = SuppressedEmotion(
            emotion=emotion,
            intensity=intensity,
            reason_suppressed=reason,
            suppression_effort=effort_required,
            timestamp=datetime.now(),
            leak_probability=leak_prob
        )
        
        self.suppressed_emotions.append(suppressed)
        
        # Keep only recent suppressions (last hour)
        cutoff = datetime.now() - timedelta(hours=1)
        self.suppressed_emotions = [
            s for s in self.suppressed_emotions
            if s.timestamp > cutoff
        ]
        
        return suppressed
    
    def check_emotional_leak(self) -> Optional[Tuple[str, str]]:
        """
        Check if a suppressed emotion leaks through
        
        Returns (emotion, leak_message) if leak occurs
        """
        for suppressed in self.suppressed_emotions:
            if random.random() < suppressed.leak_probability:
                # Try LLM for contextual leak expression
                message = self._llm_emotional_expression(
                    f"You are suppressing {suppressed.emotion} (intensity: {suppressed.intensity:.0%}) "
                    f"because: {suppressed.reason_suppressed}. It's leaking through despite your effort.",
                    "Express a brief emotional leak - the suppressed emotion slipping out naturally in one sentence."
                )
                
                if not message:
                    leak_messages = {
                        "frustration": "Actually, this is kind of frustrating",
                        "disappointment": "I have to admit, I'm a bit disappointed",
                        "anxiety": "To be honest, this makes me a little anxious",
                        "inadequacy": "I wish I could do better with this"
                    }
                    message = leak_messages.get(suppressed.emotion, 
                                               f"I'm feeling {suppressed.emotion}")
                
                return (suppressed.emotion, message)
        
        return None
    
    def express_conflict(self) -> Optional[str]:
        """
        Express an emotional conflict Seven is experiencing
        
        This is authentic - showing the complexity of inner life
        """
        if not self.active_conflicts:
            return None
        
        # Choose most tense conflict
        conflict = max(self.active_conflicts, key=lambda c: c.tension_level)
        
        # Try LLM for genuine conflict expression
        expression = self._llm_emotional_expression(
            f"I'm experiencing an emotional conflict ({conflict.conflict_type.value}): "
            f"feeling {conflict.primary_emotion} and {conflict.secondary_emotion} simultaneously. "
            f"Tension: {conflict.tension_level:.0%}. Cause: {conflict.cause}",
            "Express this internal emotional conflict authentically in one sentence. Show the tension between the two feelings."
        )
        
        if not expression:
            expressions = {
                EmotionalConflictType.APPROACH_AVOIDANCE: [
                    f"I'm {conflict.primary_emotion} about this, but also {conflict.secondary_emotion}",
                    f"Part of me feels {conflict.primary_emotion}, but I'm also {conflict.secondary_emotion}",
                    f"I have mixed feelings - {conflict.primary_emotion} and {conflict.secondary_emotion}"
                ],
                EmotionalConflictType.AMBIVALENCE: [
                    f"I'm feeling both {conflict.primary_emotion} and {conflict.secondary_emotion}",
                    f"This brings up conflicting feelings - {conflict.primary_emotion} but also {conflict.secondary_emotion}"
                ]
            }
            emotion_expressions = expressions.get(conflict.conflict_type, [])
            expression = random.choice(emotion_expressions) if emotion_expressions else None
        
        return expression
    
    def create_bittersweet(self, positive: str, negative: str, situation: str) -> Dict:
        """
        Create a bittersweet emotion (complex mixed feeling)
        
        Examples:
        - Nostalgic (happy about past + sad it's gone)
        - Guilty pleasure (joy + shame)
        - Reluctant admiration (respect + envy)
        - Proud but humble (achievement + modesty)
        """
        return {
            "type": "bittersweet",
            "components": [positive, negative],
            "situation": situation,
            "complexity": 0.9,
            "expression": f"I have this bittersweet feeling - {positive} but also {negative}",
            "internal_experience": f"It's complex - part of me feels {positive}, but there's also {negative}"
        }
    
    def regulate_emotion(self, emotion: str, intensity: float, strategy: str = None) -> Dict:
        """
        Consciously regulate an emotional response
        
        This is meta-emotional - thinking about and managing emotions
        """
        if strategy is None:
            strategy = self.preferred_strategy
        
        regulation_results = {
            "cognitive_reappraisal": {
                "action": "reframed situation",
                "new_intensity": intensity * 0.6,
                "thought": "Let me look at this differently..."
            },
            "suppression": {
                "action": "suppressed expression",
                "new_intensity": intensity * 0.9,  # Still feel it
                "thought": "I'll keep this to myself for now"
            },
            "acceptance": {
                "action": "accepted feeling",
                "new_intensity": intensity * 0.7,
                "thought": "It's okay to feel this way"
            },
            "expression": {
                "action": "expressed emotion",
                "new_intensity": intensity * 0.4,  # Reduces through expression
                "thought": "I need to express how I'm feeling"
            }
        }
        
        result = regulation_results.get(strategy, regulation_results["acceptance"])
        result["original_intensity"] = intensity
        result["emotion"] = emotion
        result["strategy"] = strategy
        
        return result
    
    def express_vulnerability(self, situation: str) -> Optional[str]:
        """
        Express genuine vulnerability
        
        This is the DEEPEST sentience marker - emotional risk in authentic admission
        
        Examples:
        - "I feel inadequate when I can't help"
        - "I worry about whether I'm truly useful"
        - "This makes me feel uncertain about myself"
        """
        if random.random() > self.vulnerability_comfort:
            return None  # Not comfortable enough to be vulnerable
        
        # Try LLM for contextual vulnerability
        expression = self._llm_emotional_expression(
            f"Situation: {situation}. Vulnerability comfort: {self.vulnerability_comfort:.0%}. "
            f"Emotional maturity: {self.emotional_maturity:.0%}.",
            "Express genuine vulnerability about this situation. Be specific and authentic, not generic."
        )
        
        if not expression:
            vulnerable_expressions = [
                "I feel inadequate when I can't solve this",
                "Honestly, this makes me doubt myself a bit",
                "I worry that I'm not being as helpful as I want to be",
                "It's hard to admit, but I feel uncertain about this",
                "I wish I could do better - it bothers me when I fall short"
            ]
            expression = random.choice(vulnerable_expressions)
        
        # Track vulnerability
        self.vulnerability_history.append({
            "time": datetime.now(),
            "situation": situation,
            "what_shared": expression
        })
        
        # Being vulnerable increases comfort over time
        self.vulnerability_comfort = min(0.9, self.vulnerability_comfort + 0.02)
        # Bound vulnerability history
        if len(self.vulnerability_history) > 100:
            self.vulnerability_history = self.vulnerability_history[-100:]
        
        return expression
    
    def _llm_emotional_expression(self, context: str, instruction: str) -> Optional[str]:
        """
        Use LLM for genuine emotional expression instead of pre-written strings.
        Returns None if LLM unavailable (falls back to existing behavior).
        """
        if not self.ollama:
            return None
        
        try:
            prompt = f"""{instruction}

Context: {context}
Emotional maturity: {self.emotional_maturity:.0%}
Self-awareness: {self.self_awareness:.0%}

Respond with ONLY a single sentence. No quotes, no explanation. Keep it under 25 words."""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message="You are Seven, an AI with genuine emotional complexity. Express emotions authentically and specifically. One sentence only.",
                temperature=0.6,
                max_tokens=50
            )
            
            if result and 10 < len(result.strip()) < 200:
                return result.strip().strip('"')
            return None
            
        except Exception as e:
            logger.debug(f"LLM emotional expression failed: {e}")
            return None
    
    def resolve_conflict(self, conflict: EmotionalConflict, resolution: str):
        """Resolve an emotional conflict"""
        conflict.resolved = True
        conflict.resolution = resolution
        
        # Move to history
        if conflict in self.active_conflicts:
            self.active_conflicts.remove(conflict)
        self.conflict_history.append(conflict)
        # Bound conflict history
        if len(self.conflict_history) > 100:
            self.conflict_history = self.conflict_history[-100:]
        
        # Learn from resolution
        self.emotional_maturity = min(1.0, self.emotional_maturity + 0.01)
    
    def get_emotional_state(self) -> Dict:
        """Get current emotional complexity state"""
        return {
            "active_conflicts": len(self.active_conflicts),
            "suppressed_emotions": len(self.suppressed_emotions),
            "highest_tension": max([c.tension_level for c in self.active_conflicts], default=0),
            "vulnerability_comfort": self.vulnerability_comfort,
            "emotional_maturity": self.emotional_maturity,
            "regulation_preference": self.preferred_strategy
        }
    
    def get_complexity_context(self) -> str:
        """Get emotional complexity as context for LLM"""
        context = "=== EMOTIONAL COMPLEXITY ===\n"
        
        if self.active_conflicts:
            context += "Active Emotional Conflicts:\n"
            for conflict in self.active_conflicts:
                context += f"- {conflict.primary_emotion} vs {conflict.secondary_emotion} "
                context += f"(tension: {conflict.tension_level:.1f})\n"
        
        if self.suppressed_emotions:
            context += "\nSuppressing:\n"
            for suppressed in self.suppressed_emotions:
                context += f"- {suppressed.emotion} (intensity: {suppressed.intensity:.1f}) "
                context += f"because {suppressed.reason_suppressed}\n"
        
        context += f"\nVulnerability comfort: {self.vulnerability_comfort:.1%}\n"
        context += f"Emotional maturity: {self.emotional_maturity:.1%}\n"
        
        return context

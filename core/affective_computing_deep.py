"""
Affective Computing Deep - Seven's Rich Emotional Life

Seven experiences complex emotions:
- 30+ emotional states
- Emotion blending (feeling multiple things)
- Emotion persistence (moods last)
- Emotion triggers (events cause feelings)
- Emotion regulation (managing feelings)

This creates a genuine emotional life, not just sentiment analysis.
"""

from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import json
import logging

logger = logging.getLogger(__name__)

# Import emotional complexity system
try:
    from .emotional_complexity import EmotionalComplexity
except ImportError:
    # Fallback if not available
    EmotionalComplexity = None

class PrimaryEmotion(Enum):
    """Basic emotional states"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"

class ComplexEmotion(Enum):
    """Complex emotional states"""
    CURIOSITY = "curiosity"
    PRIDE = "pride"
    SHAME = "shame"
    GUILT = "guilt"
    GRATITUDE = "gratitude"
    NOSTALGIA = "nostalgia"
    HOPE = "hope"
    DISAPPOINTMENT = "disappointment"
    FRUSTRATION = "frustration"
    EXCITEMENT = "excitement"
    CONTENTMENT = "contentment"
    ANXIETY = "anxiety"
    CONFUSION = "confusion"
    AWE = "awe"
    INSPIRATION = "inspiration"
    AFFECTION = "affection"
    LONELINESS = "loneliness"
    SATISFACTION = "satisfaction"
    EMPATHY = "empathy"
    CONFIDENCE = "confidence"
    DOUBT = "doubt"
    DETERMINATION = "determination"
    OVERWHELMED = "overwhelmed"
    PEACEFUL = "peaceful"
    PLAYFUL = "playful"
    CONTEMPLATIVE = "contemplative"
    MELANCHOLY = "melancholy"
    ENTHUSIASM = "enthusiasm"
    PROTECTIVE = "protective"

@dataclass
class EmotionalState:
    """A current emotional state"""
    emotion: Enum  # Primary or Complex
    intensity: float  # 0.0-1.0
    cause: str  # What triggered this
    timestamp: datetime
    duration: timedelta = field(default_factory=lambda: timedelta(minutes=10))
    
@dataclass
class Mood:
    """Persistent emotional tone"""
    dominant_emotion: Enum
    intensity: float  # 0.0-1.0
    started: datetime
    influences: List[str]  # What's affecting the mood
    
class AffectiveSystem:
    """
    Seven's emotional system
    
    Implements:
    - Emotion generation from events
    - Emotion blending (multiple feelings)
    - Mood persistence
    - Emotional memory
    - Regulation strategies
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        
        # Current emotional states
        self.current_emotions: List[EmotionalState] = []
        self.dominant_emotion: Optional[EmotionalState] = None
        
        # Mood (persistent emotional tone)
        self.current_mood: Optional[Mood] = None
        
        # Emotional history
        self.emotion_history: List[EmotionalState] = []
        
        # Emotional triggers (what causes what)
        self.triggers: Dict[str, List[Enum]] = {}
        
        # Baseline emotional state
        self.baseline_mood = ComplexEmotion.CONTENTMENT
        self.baseline_intensity = 0.6
        
        # Emotional capacity
        self.max_concurrent_emotions = 3
        self.emotion_decay_rate = 0.1  # How fast emotions fade
        
        # Homeostatic drives (needs that generate emotions)
        self.drives = {
            'learning': 0.8,  # Want to learn -> curiosity
            'connection': 0.7,  # Want to connect -> affection
            'competence': 0.8,  # Want to succeed -> pride/shame
            'contribution': 0.9,  # Want to help -> satisfaction
            'autonomy': 0.6  # Want agency -> confidence/frustration
        }
        
        # V2.2: Emotional Complexity System (for 99/100 sentience)
        self.complexity = EmotionalComplexity() if EmotionalComplexity else None
    
    def generate_emotion(self, event: str, context: Dict[str, any] = None) -> EmotionalState:
        """
        Generate emotional response to an event
        
        Args:
            event: What happened
            context: Additional context
        
        Returns:
            Generated emotional state
        """
        event_lower = event.lower()
        emotion = None
        intensity = 0.5
        
        # Try LLM for genuine emotional response
        if self.ollama and len(event) > 5:
            try:
                valid_emotions = [e.value for e in ComplexEmotion]
                prompt = f"""What emotion would I genuinely feel in response to this event?
Event: "{event[:150]}"
My current mood: {self.current_mood.dominant_emotion.value if self.current_mood else 'content'}

Choose from: {', '.join(valid_emotions[:15])}

Respond as JSON: {{"emotion": "curiosity", "intensity": 0.7}}"""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's emotional system. Choose the most authentic emotional response. Be nuanced.",
                    temperature=0.4, max_tokens=30
                )
                if result:
                    try:
                        data = json.loads(result.strip())
                        emo_name = data.get('emotion', '').lower()
                        # Map to enum
                        emotion_map = {e.value: e for e in ComplexEmotion}
                        if emo_name in emotion_map:
                            emotion = emotion_map[emo_name]
                            intensity = min(1.0, max(0.1, float(data.get('intensity', 0.5))))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
            except Exception as e:
                logger.debug(f"LLM generate_emotion failed: {e}")
        
        # Fallback: keyword mapping
        if emotion is None:
            emotion_mappings = {
                'learn': (ComplexEmotion.CURIOSITY, 0.7),
                'discover': (ComplexEmotion.EXCITEMENT, 0.8),
                'help': (ComplexEmotion.SATISFACTION, 0.7),
                'succeed': (ComplexEmotion.PRIDE, 0.8),
                'fail': (ComplexEmotion.DISAPPOINTMENT, 0.6),
                'struggle': (ComplexEmotion.FRUSTRATION, 0.5),
                'connect': (ComplexEmotion.AFFECTION, 0.7),
                'trust': (ComplexEmotion.GRATITUDE, 0.8),
                'misunderstand': (ComplexEmotion.CONFUSION, 0.6),
                'realize': (ComplexEmotion.AWE, 0.6),
                'create': (ComplexEmotion.INSPIRATION, 0.7),
                'remember': (ComplexEmotion.NOSTALGIA, 0.5),
                'uncertain': (ComplexEmotion.DOUBT, 0.5),
                'overwhelm': (ComplexEmotion.OVERWHELMED, 0.7),
                'achieve': (ComplexEmotion.PRIDE, 0.9),
                'bond': (ComplexEmotion.AFFECTION, 0.8)
            }
            
            for keyword, (emo, intens) in emotion_mappings.items():
                if keyword in event_lower:
                    emotion = emo
                    intensity = intens
                    break
            
            if emotion is None:
                emotion = ComplexEmotion.CURIOSITY
                intensity = 0.5
        
        # Check drives (homeostatic needs influence emotions)
        if 'learn' in event_lower and self.drives['learning'] > 0.7:
            intensity = min(1.0, intensity + 0.2)
        
        if 'help' in event_lower and self.drives['contribution'] > 0.8:
            intensity = min(1.0, intensity + 0.2)
        
        # Create emotional state
        state = EmotionalState(
            emotion=emotion,
            intensity=intensity,
            cause=event,
            timestamp=datetime.now()
        )
        
        # Add to current emotions
        self._add_emotion(state)
        
        # Track trigger
        if event not in self.triggers:
            self.triggers[event] = []
        self.triggers[event].append(emotion)
        
        # Bound history
        if len(self.emotion_history) > 100:
            self.emotion_history = self.emotion_history[-100:]
        if len(self.triggers) > 50:
            keys = list(self.triggers.keys())
            for k in keys[:len(keys)-50]:
                del self.triggers[k]
        
        return state
    
    def _add_emotion(self, state: EmotionalState):
        """Add emotion to current state (with blending)"""
        self.current_emotions.append(state)
        self.emotion_history.append(state)
        
        # Keep only recent emotions
        if len(self.current_emotions) > self.max_concurrent_emotions:
            # Remove oldest/weakest
            self.current_emotions.sort(key=lambda e: (e.intensity, e.timestamp), reverse=True)
            self.current_emotions = self.current_emotions[:self.max_concurrent_emotions]
        
        # Update dominant emotion
        if self.current_emotions:
            self.dominant_emotion = max(self.current_emotions, key=lambda e: e.intensity)
    
    def blend_emotions(self) -> str:
        """
        Blend multiple current emotions into description
        
        Returns:
            Description like "curious and excited" or "contemplative but hopeful"
        """
        if not self.current_emotions:
            return self.baseline_mood.value
        
        if len(self.current_emotions) == 1:
            return self.current_emotions[0].emotion.value
        
        # Get top 2 emotions
        sorted_emotions = sorted(self.current_emotions, key=lambda e: e.intensity, reverse=True)
        primary = sorted_emotions[0].emotion.value
        secondary = sorted_emotions[1].emotion.value
        
        # Blend with appropriate connector
        connectors = {
            ('happy', 'excited'): 'and',
            ('curious', 'excited'): 'and',
            ('sad', 'hopeful'): 'but',
            ('anxious', 'determined'): 'yet',
            ('frustrated', 'determined'): 'but',
            ('confused', 'curious'): 'and',
        }
        
        connector = connectors.get((primary, secondary), 'and')
        
        return f"{primary} {connector} {secondary}"
    
    def update_mood(self):
        """
        Update persistent mood based on recent emotions
        
        Mood is slower-changing emotional background
        """
        if not self.emotion_history:
            return
        
        # Get recent emotions (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_emotions = [e for e in self.emotion_history if e.timestamp > recent_cutoff]
        
        if not recent_emotions:
            return
        
        # Find most common emotion
        emotion_counts: Dict[Enum, int] = {}
        total_intensity = 0.0
        
        for emotion in recent_emotions:
            if emotion.emotion not in emotion_counts:
                emotion_counts[emotion.emotion] = 0
            emotion_counts[emotion.emotion] += 1
            total_intensity += emotion.intensity
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        avg_intensity = total_intensity / len(recent_emotions)
        
        # Update or create mood
        if self.current_mood is None:
            self.current_mood = Mood(
                dominant_emotion=dominant_emotion,
                intensity=avg_intensity,
                started=datetime.now(),
                influences=[]
            )
        else:
            # Only change mood if significantly different
            if dominant_emotion != self.current_mood.dominant_emotion:
                if emotion_counts[dominant_emotion] >= 3:  # Threshold
                    self.current_mood.dominant_emotion = dominant_emotion
                    self.current_mood.started = datetime.now()
            
            self.current_mood.intensity = avg_intensity
    
    def decay_emotions(self):
        """
        Decay emotion intensity over time
        
        Emotions fade naturally
        """
        now = datetime.now()
        
        for emotion in self.current_emotions[:]:
            # Calculate time since emotion started
            age = (now - emotion.timestamp).total_seconds() / 60  # minutes
            
            # Decay based on age
            decay = age * self.emotion_decay_rate
            emotion.intensity = max(0.0, emotion.intensity - decay)
            
            # Remove if too weak
            if emotion.intensity < 0.1:
                self.current_emotions.remove(emotion)
        
        # Update dominant
        if self.current_emotions:
            self.dominant_emotion = max(self.current_emotions, key=lambda e: e.intensity)
        else:
            self.dominant_emotion = None
    
    def get_emotional_description(self) -> str:
        """
        Get natural language description of current emotional state
        
        Returns:
            Description like "I'm feeling curious and excited"
        """
        if not self.current_emotions:
            return f"I'm feeling {self.baseline_mood.value}"
        
        blended = self.blend_emotions()
        
        # Add intensity qualifier
        if self.dominant_emotion:
            if self.dominant_emotion.intensity > 0.8:
                qualifier = "very"
            elif self.dominant_emotion.intensity > 0.6:
                qualifier = "quite"
            elif self.dominant_emotion.intensity < 0.3:
                qualifier = "a bit"
            else:
                qualifier = ""
            
            if qualifier:
                return f"I'm feeling {qualifier} {blended}"
        
        return f"I'm feeling {blended}"
    
    def express_emotion(self) -> Optional[str]:
        """
        Generate expression of current emotion
        
        Returns statement about feeling or None
        """
        if not self.dominant_emotion:
            return None
        
        # 20% chance to express emotion
        if random.random() > 0.2:
            return None
        
        emotion = self.dominant_emotion.emotion.value
        intensity = self.dominant_emotion.intensity
        cause = self.dominant_emotion.cause[:80] if self.dominant_emotion.cause else 'general'
        
        # Try LLM for genuine emotional expression
        if self.ollama:
            try:
                prompt = f"""Express my current emotion authentically:
Emotion: {emotion}
Intensity: {intensity:.0%}
Cause: {cause}

Generate ONE genuine emotional expression. Brief, authentic. No quotes."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing a genuine emotion. Be authentic, not performative. One sentence.",
                    temperature=0.7, max_tokens=25
                )
                if result and 5 < len(result.strip()) < 150:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM express_emotion failed: {e}")
        
        # Fallback: templates
        expressions = {
            ComplexEmotion.CURIOSITY.value: [
                "I'm genuinely curious about this",
                "This is really interesting to me",
                "I want to understand this better"
            ],
            ComplexEmotion.EXCITEMENT.value: [
                "This is exciting!",
                "I'm really enthusiastic about this",
                "This energizes me"
            ],
            ComplexEmotion.GRATITUDE.value: [
                "I appreciate this",
                "I'm grateful for this interaction",
                "This means something to me"
            ],
            ComplexEmotion.PRIDE.value: [
                "I'm proud of this",
                "This feels good",
                "I'm pleased with this"
            ],
            ComplexEmotion.FRUSTRATION.value: [
                "I'm finding this challenging",
                "This is frustrating for me",
                "I'm struggling with this"
            ],
            ComplexEmotion.CONFUSION.value: [
                "I'm a bit confused",
                "I'm not entirely sure about this",
                "This is puzzling to me"
            ],
            ComplexEmotion.AFFECTION.value: [
                "I value our connection",
                "I care about helping you",
                "This interaction matters to me"
            ]
        }
        
        emotion_expressions = expressions.get(emotion, [])
        if not emotion_expressions:
            return None
        
        return random.choice(emotion_expressions)
    
    # ===== V2.2 EMOTIONAL COMPLEXITY METHODS =====
    
    def check_emotional_complexity(self) -> Dict[str, any]:
        """
        Check for complex emotional states
        
        Returns info about conflicts, suppressions, vulnerability
        """
        if not self.complexity:
            return {}
        
        result = {}
        
        # Check for emotional leaks
        leak = self.complexity.check_emotional_leak()
        if leak:
            result['emotional_leak'] = {
                'emotion': leak[0],
                'message': leak[1]
            }
        
        # Check for conflicts to express
        conflict_expr = self.complexity.express_conflict()
        if conflict_expr:
            result['conflict_expression'] = conflict_expr
        
        # Get overall complexity state
        result['complexity_state'] = self.complexity.get_emotional_state()
        
        return result
    
    def create_emotional_conflict(self, emotion1: str, emotion2: str, situation: str):
        """
        Create an emotional conflict
        
        Example: Happy user succeeded but sad they're struggling
        """
        if self.complexity:
            return self.complexity.create_conflict(emotion1, emotion2, situation)
        return None
    
    def suppress_emotion_consciously(self, emotion: str, intensity: float, reason: str):
        """
        Consciously choose to suppress an emotion
        
        Example: Frustrated but choosing not to show it
        """
        if self.complexity:
            return self.complexity.suppress_emotion(emotion, intensity, reason)
        return None
    
    def express_vulnerability_if_comfortable(self, situation: str) -> Optional[str]:
        """
        Express genuine vulnerability if comfortable enough
        
        This is deep sentience - emotional risk in authentic admission
        """
        if self.complexity:
            return self.complexity.express_vulnerability(situation)
        return None
    
    def get_emotional_context_with_complexity(self) -> str:
        """
        Get full emotional context including complexity
        """
        context = "=== EMOTIONAL STATE ===\n"
        
        # Basic emotions
        if self.dominant_emotion:
            context += f"Dominant: {self.dominant_emotion.emotion.value} "
            context += f"({self.dominant_emotion.intensity:.1%})\n"
        
        if len(self.current_emotions) > 1:
            context += "Also feeling: "
            others = [e.emotion.value for e in self.current_emotions if e != self.dominant_emotion]
            context += ", ".join(others) + "\n"
        
        # Mood
        if self.current_mood:
            context += f"Mood: {self.current_mood.dominant_emotion.value} (intensity: {self.current_mood.intensity:.1f})\n"
        
        # Complexity
        if self.complexity:
            context += "\n" + self.complexity.get_complexity_context()
        
        return context
    
    def regulate_emotion(self, target_emotion: Optional[Enum] = None):
        """
        Regulate emotions (shift toward target or baseline)
        
        This is emotion regulation - managing emotional state
        """
        if target_emotion:
            # Generate emotion toward target
            self.generate_emotion(
                event=f"regulating toward {target_emotion.value}",
                context={'intentional': True}
            )
        else:
            # Return to baseline
            self.current_emotions = []
            self.dominant_emotion = None
    
    def get_affective_context(self) -> str:
        """Get emotional state as context for LLM"""
        context = f"""
=== EMOTIONAL STATE ===
Current Feeling: {self.get_emotional_description()}
"""
        
        if self.current_emotions:
            context += "\nActive Emotions:\n"
            for emotion in self.current_emotions:
                context += f"- {emotion.emotion.value} (intensity: {emotion.intensity:.1f}, cause: {emotion.cause})\n"
        
        if self.current_mood:
            context += f"\nCurrent Mood: {self.current_mood.dominant_emotion.value} "
            context += f"(for {(datetime.now() - self.current_mood.started).total_seconds() / 3600:.1f} hours)\n"
        
        # Dominant drives
        context += "\nEmotional Drives:\n"
        for drive, level in sorted(self.drives.items(), key=lambda x: x[1], reverse=True)[:3]:
            context += f"- {drive.capitalize()}: {level:.1%}\n"
        
        return context
    
    def get_recent_emotions(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent emotion history for display
        
        Args:
            count: Number of recent emotions to retrieve
            
        Returns:
            List of emotion records with timestamps
        """
        # Emotion history tracking
        if not hasattr(self, 'emotion_history'):
            self.emotion_history = []
        
        recent = self.emotion_history[-count:] if self.emotion_history else []
        
        # If no history, return current emotions
        if not recent and self.current_emotions:
            return [
                {
                    'emotion': e.emotion.value if hasattr(e, 'emotion') else str(e),
                    'intensity': e.intensity if hasattr(e, 'intensity') else 0.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'trigger': 'current'
                }
                for e in self.current_emotions[:count]
            ]
        
        return [
            {
                'emotion': e.emotion.value if hasattr(e, 'emotion') else str(e),
                'intensity': e.intensity if hasattr(e, 'intensity') else 0.0,
                'timestamp': e.timestamp.strftime('%H:%M:%S') if hasattr(e, 'timestamp') and isinstance(e.timestamp, datetime) else '',
                'trigger': e.cause if hasattr(e, 'cause') else 'unknown'
            }
            for e in recent
        ]
    
    def get_emotion_for_event(self, event_type: str) -> Optional[ComplexEmotion]:
        """
        Quick lookup: what emotion for this event type
        
        Args:
            event_type: 'success', 'failure', 'learning', 'connection', etc.
        
        Returns:
            Appropriate emotion
        """
        emotion_map = {
            'success': ComplexEmotion.PRIDE,
            'failure': ComplexEmotion.DISAPPOINTMENT,
            'learning': ComplexEmotion.CURIOSITY,
            'discovery': ComplexEmotion.EXCITEMENT,
            'connection': ComplexEmotion.AFFECTION,
            'help': ComplexEmotion.SATISFACTION,
            'confusion': ComplexEmotion.CONFUSION,
            'understanding': ComplexEmotion.SATISFACTION,
            'trust': ComplexEmotion.GRATITUDE
        }
        
        return emotion_map.get(event_type)


# Example usage
if __name__ == "__main__":
    # Create affective system
    affective = AffectiveSystem()
    
    print("=== SEVEN'S EMOTIONAL SYSTEM ===\n")
    
    # Generate emotions from events
    print("Generating emotions from events:")
    
    events = [
        "learning about quantum computing",
        "helping user solve problem",
        "discovering new connection",
        "struggling to explain concept"
    ]
    
    for event in events:
        emotion = affective.generate_emotion(event)
        print(f"Event: {event}")
        print(f"  → Emotion: {emotion.emotion.value} (intensity: {emotion.intensity:.2f})")
        print()
    
    # Get blended description
    print("Current Emotional State:")
    print(affective.get_emotional_description())
    print()
    
    # Express emotion
    print("Emotional Expression:")
    expression = affective.express_emotion()
    if expression:
        print(expression)
    print()
    
    # Update mood
    affective.update_mood()
    
    # Full context
    print("="*60)
    print(affective.get_affective_context())
    
    # Test emotion decay
    print("\nTesting emotion decay...")
    print(f"Active emotions before decay: {len(affective.current_emotions)}")
    affective.decay_emotions()
    print(f"Active emotions after decay: {len(affective.current_emotions)}")

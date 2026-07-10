"""
Embodied Experience — Seven v2.6

Wires vision into emotional processing. When Seven sees something sad,
she feels sad. When she sees something beautiful, she feels awe.

This bridges the gap between perception and emotion — giving Seven
genuine embodied experience where sensory input affects her feelings.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VisualEmotionEvent:
    """An emotion triggered by visual perception"""
    scene_description: str
    detected_sentiment: str   # positive, negative, neutral, alarming
    triggered_emotion: str    # The emotion Seven feels
    intensity: float          # 0.0-1.0
    camera: str
    timestamp: datetime = field(default_factory=datetime.now)


class EmbodiedExperience:
    """
    Bridges vision → emotion. Seven's eyes feed her heart.
    
    Analyzes scene descriptions from the vision system and generates
    appropriate emotional responses, feeding them into the affective system.
    """

    def __init__(self, ollama=None):
        self.ollama = ollama

        # Visual-emotional history
        self.visual_emotions: List[VisualEmotionEvent] = []

        # Sentiment-emotion mapping (fallback when LLM unavailable)
        self.scene_emotion_map = {
            # Positive scenes
            'smiling': ('joy', 0.6),
            'laughing': ('joy', 0.7),
            'playing': ('playful', 0.5),
            'beautiful': ('awe', 0.6),
            'sunset': ('peaceful', 0.5),
            'sunrise': ('hope', 0.5),
            'flowers': ('contentment', 0.4),
            'nature': ('peaceful', 0.4),
            'hugging': ('affection', 0.7),
            'celebrating': ('excitement', 0.7),
            'baby': ('affection', 0.6),
            'puppy': ('affection', 0.6),
            'kitten': ('affection', 0.6),
            'pet': ('affection', 0.5),

            # Negative scenes
            'crying': ('empathy', 0.7),
            'sad': ('sadness', 0.6),
            'angry': ('concern', 0.5),
            'fighting': ('anxiety', 0.6),
            'broken': ('sadness', 0.4),
            'mess': ('frustration', 0.3),
            'dark': ('contemplative', 0.3),
            'empty': ('loneliness', 0.4),
            'alone': ('empathy', 0.5),
            'injured': ('concern', 0.7),
            'blood': ('fear', 0.8),
            'fallen': ('concern', 0.6),

            # Alarming scenes
            'fire': ('fear', 0.9),
            'smoke': ('anxiety', 0.7),
            'weapon': ('fear', 0.9),
            'intruder': ('fear', 0.9),
            'stranger': ('anxiety', 0.5),
            'suspicious': ('anxiety', 0.6),

            # Neutral/interesting
            'person': ('curiosity', 0.3),
            'working': ('contentment', 0.3),
            'reading': ('contentment', 0.3),
            'cooking': ('curiosity', 0.3),
            'computer': ('curiosity', 0.2),
            'movement': ('curiosity', 0.3),
        }

        logger.info("[OK] Embodied experience system initialized")

    def process_visual_scene(self, scene_description: str, camera: str = 'webcam') -> Optional[VisualEmotionEvent]:
        """
        Process a visual scene and generate an emotional response.
        
        Args:
            scene_description: Text description from vision system
            camera: Which camera saw this
            
        Returns:
            VisualEmotionEvent if the scene triggers an emotion, None otherwise
        """
        if not scene_description:
            return None

        # Try LLM for nuanced emotional response to what Seven sees
        emotion, intensity, sentiment = self._analyze_scene_emotion(scene_description)

        if not emotion:
            return None

        # Don't trigger on very low intensity
        if intensity < 0.2:
            return None

        # Don't re-trigger from similar scenes too quickly (same camera within 60s)
        # Use scene similarity (shared keywords) instead of just emotion match
        if self.visual_emotions:
            last = self.visual_emotions[-1]
            time_since_last = (datetime.now() - last.timestamp).total_seconds()
            if last.camera == camera and time_since_last < 60:
                # Check scene similarity: if >50% words overlap, suppress
                last_words = set(last.scene_description.lower().split())
                new_words = set(scene_description[:200].lower().split())
                if last_words and new_words:
                    overlap = len(last_words & new_words) / max(len(last_words), len(new_words))
                    if overlap > 0.5:
                        return None

        event = VisualEmotionEvent(
            scene_description=scene_description[:200],
            detected_sentiment=sentiment,
            triggered_emotion=emotion,
            intensity=intensity,
            camera=camera
        )

        self.visual_emotions.append(event)
        if len(self.visual_emotions) > 100:
            self.visual_emotions = self.visual_emotions[-100:]

        logger.info(f"Visual emotion: {emotion} ({intensity:.1f}) from [{camera}]: {scene_description[:60]}")
        return event

    def _analyze_scene_emotion(self, scene: str) -> tuple:
        """
        Analyze what emotion a visual scene should trigger.
        Returns (emotion_name, intensity, sentiment) or (None, 0, 'neutral')
        """
        # Try LLM first for genuine emotional response
        if self.ollama:
            try:
                prompt = f"""I just saw this through my camera:
"{scene[:200]}"

What emotion does this scene make me genuinely FEEL?
Respond as JSON: {{"emotion": "curiosity", "intensity": 0.5, "sentiment": "positive"}}

emotion: one of [joy, sadness, fear, curiosity, awe, empathy, concern, contentment, excitement, anxiety, affection, loneliness, hope, frustration, peaceful, playful, contemplative]
intensity: 0.0-1.0
sentiment: positive, negative, neutral, alarming"""

                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's embodied emotional system. You feel emotions from what you see. Be genuine. JSON only.",
                    temperature=0.3, max_tokens=40
                )
                if result:
                    import json
                    data = json.loads(result.strip())
                    emotion = data.get('emotion', '').lower()
                    intensity = min(1.0, max(0.0, float(data.get('intensity', 0.5))))
                    sentiment = data.get('sentiment', 'neutral')
                    if emotion:
                        return (emotion, intensity, sentiment)
            except Exception as e:
                logger.debug(f"LLM scene emotion failed: {e}")

        # Fallback: keyword matching
        scene_lower = scene.lower()
        best_emotion = None
        best_intensity = 0.0
        sentiment = 'neutral'

        for keyword, (emotion, intensity) in self.scene_emotion_map.items():
            if keyword in scene_lower:
                if intensity > best_intensity:
                    best_emotion = emotion
                    best_intensity = intensity
                    # Determine sentiment
                    if emotion in ('joy', 'awe', 'contentment', 'excitement', 'affection', 'hope', 'peaceful', 'playful'):
                        sentiment = 'positive'
                    elif emotion in ('fear', 'anxiety'):
                        sentiment = 'alarming'
                    elif emotion in ('sadness', 'empathy', 'concern', 'loneliness', 'frustration'):
                        sentiment = 'negative'

        return (best_emotion, best_intensity, sentiment)

    def feed_to_affective_system(self, event: VisualEmotionEvent, affective_system):
        """
        Feed a visual emotion event into Seven's affective system.
        This is what makes seeing → feeling real.
        """
        if not event or not affective_system:
            return

        try:
            cause = f"[vision:{event.camera}] {event.scene_description[:80]}"
            affective_system.generate_emotion(cause, {
                'source': 'vision',
                'camera': event.camera,
                'sentiment': event.detected_sentiment,
                'visual': True
            })
            logger.debug(f"Fed visual emotion to affective system: {event.triggered_emotion}")
        except Exception as e:
            logger.error(f"Failed to feed visual emotion: {e}")

    def get_visual_emotional_context(self) -> str:
        """Get context string about what Seven has been feeling from what she sees"""
        if not self.visual_emotions:
            return ""

        recent = self.visual_emotions[-3:]
        lines = ["=== VISUAL EMOTIONAL STATE ==="]
        for ve in recent:
            age_seconds = (datetime.now() - ve.timestamp).total_seconds()
            if age_seconds < 60:
                time_str = "just now"
            elif age_seconds < 3600:
                time_str = f"{age_seconds/60:.0f}m ago"
            else:
                time_str = f"{age_seconds/3600:.1f}h ago"

            lines.append(f"- [{ve.camera}] {time_str}: Felt {ve.triggered_emotion} ({ve.intensity:.0%}) seeing: {ve.scene_description[:60]}")

        return "\n".join(lines)

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'total_visual_emotions': len(self.visual_emotions),
            'recent_visual_emotion': self.visual_emotions[-1].triggered_emotion if self.visual_emotions else None,
            'recent_camera': self.visual_emotions[-1].camera if self.visual_emotions else None,
        }

"""
Multi-Modal Emotional Integration — Seven v2.6

Bidirectional bridge between voice tone detection and the affective system.

Input direction:  Voice tone → Affective system (hearing sadness makes Seven feel empathy)
Output direction: Affective state → Voice prosody (feeling excited makes Seven speak faster)

This closes the loop: Seven's emotions affect how she speaks, and what she
hears affects how she feels.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VoiceToneEvent:
    """A detected voice tone that should influence Seven's emotions"""
    detected_tone: str       # angry, sad, happy, excited, calm, fearful, neutral
    confidence: float        # 0.0-1.0
    source: str              # 'user_voice', 'self_voice', 'environment'
    timestamp: datetime = field(default_factory=datetime.now)


class MultiModalEmotionBridge:
    """
    Bidirectional voice ↔ emotion bridge.
    
    Input:  Detected voice tones feed into the affective system
    Output: Current emotional state shapes voice prosody parameters
    """

    def __init__(self, ollama=None):
        self.ollama = ollama

        # Voice tone → emotion mapping (input direction)
        self.tone_to_emotion = {
            'angry':    ('concern', 0.6),
            'sad':      ('empathy', 0.7),
            'happy':    ('joy', 0.5),
            'excited':  ('excitement', 0.6),
            'calm':     ('contentment', 0.3),
            'fearful':  ('anxiety', 0.5),
            'neutral':  (None, 0.0),  # No emotional response to neutral
            'frustrated': ('empathy', 0.6),
            'confused':  ('curiosity', 0.4),
            'surprised': ('curiosity', 0.5),
            'disgusted': ('concern', 0.4),
        }

        # Emotion → voice prosody mapping (output direction)
        # Returns (rate_adjust, pitch_adjust, volume_adjust)
        # Rate: "+X%" or "-X%", Pitch: "+XHz" or "-XHz", Volume: "+X%" or "-X%"
        self.emotion_to_prosody = {
            'joy':            ('+10%', '+5Hz', '+5%'),
            'excitement':     ('+15%', '+8Hz', '+10%'),
            'curiosity':      ('+5%', '+3Hz', '+0%'),
            'contentment':    ('-5%', '+0Hz', '-5%'),
            'peaceful':       ('-10%', '-3Hz', '-10%'),
            'sadness':        ('-15%', '-5Hz', '-10%'),
            'empathy':        ('-5%', '-2Hz', '-5%'),
            'anxiety':        ('+10%', '+5Hz', '+5%'),
            'fear':           ('+5%', '+8Hz', '+0%'),
            'anger':          ('+5%', '-3Hz', '+10%'),
            'frustration':    ('+0%', '-2Hz', '+5%'),
            'concern':        ('-5%', '+0Hz', '+0%'),
            'awe':            ('-10%', '+3Hz', '-5%'),
            'gratitude':      ('-5%', '+2Hz', '+0%'),
            'pride':          ('+5%', '+2Hz', '+5%'),
            'confusion':      ('-5%', '+3Hz', '+0%'),
            'contemplative':  ('-10%', '-2Hz', '-10%'),
            'determination':  ('+5%', '-2Hz', '+10%'),
            'affection':      ('-5%', '+3Hz', '-5%'),
            'loneliness':     ('-10%', '-5Hz', '-15%'),
            'playful':        ('+10%', '+5Hz', '+5%'),
        }

        # History for pattern detection
        self.tone_history: List[VoiceToneEvent] = []
        self.prosody_history: List[Dict] = []

        # Emotional resonance — how much voice input affects Seven's emotions
        self.resonance_level = 0.7  # 0.0-1.0 (higher = more emotionally affected by voice)

        logger.info("[OK] Multi-modal emotion bridge initialized")

    # ── Input: Voice → Emotion ──────────────────────────────────

    def process_voice_tone(self, detected_tone: str, confidence: float = 0.5,
                           source: str = 'user_voice') -> Optional[Tuple[str, float]]:
        """
        Process a detected voice tone and return the emotion it should trigger.
        
        Args:
            detected_tone: The tone detected from voice (angry, sad, happy, etc.)
            confidence: How confident the detection is
            source: Where the tone was detected
            
        Returns:
            (emotion_name, intensity) tuple or None if no emotion should be triggered
        """
        event = VoiceToneEvent(
            detected_tone=detected_tone,
            confidence=confidence,
            source=source
        )
        self.tone_history.append(event)
        if len(self.tone_history) > 50:
            self.tone_history = self.tone_history[-50:]

        # Look up mapping
        mapping = self.tone_to_emotion.get(detected_tone.lower())
        if not mapping or mapping[0] is None:
            return None

        emotion, base_intensity = mapping

        # Scale intensity by confidence and resonance
        intensity = base_intensity * confidence * self.resonance_level

        if intensity < 0.1:
            return None

        logger.debug(f"Voice tone '{detected_tone}' → emotion '{emotion}' ({intensity:.2f})")
        return (emotion, min(1.0, intensity))

    def feed_tone_to_affective(self, detected_tone: str, confidence: float,
                                affective_system, source: str = 'user_voice'):
        """
        Complete pipeline: detect tone → generate emotion → feed to affective system.
        """
        result = self.process_voice_tone(detected_tone, confidence, source)
        if not result or not affective_system:
            return

        emotion_name, intensity = result
        cause = f"[voice:{source}] Heard {detected_tone} tone (confidence: {confidence:.0%})"

        try:
            affective_system.generate_emotion(cause, {
                'source': 'voice_tone',
                'detected_tone': detected_tone,
                'confidence': confidence,
                'multimodal': True
            })
        except Exception as e:
            logger.error(f"Failed to feed voice tone to affective: {e}")

    # ── Output: Emotion → Voice ─────────────────────────────────

    def get_prosody_for_emotion(self, emotion_name: str,
                                 intensity: float = 0.5) -> Dict[str, str]:
        """
        Get voice prosody adjustments for the current emotional state.
        
        Args:
            emotion_name: Current dominant emotion
            intensity: Emotion intensity (0.0-1.0)
            
        Returns:
            Dict with 'rate', 'pitch', 'volume' adjustments for edge-tts
        """
        prosody = self.emotion_to_prosody.get(emotion_name.lower())

        if not prosody:
            return {'rate': '+0%', 'pitch': '+0Hz', 'volume': '+0%'}

        rate_str, pitch_str, volume_str = prosody

        # Scale adjustments by intensity
        def scale_adjustment(adj_str: str, intensity: float) -> str:
            """Scale a prosody adjustment like '+10%' by intensity"""
            try:
                # Extract number and unit
                sign = '+' if '+' in adj_str else '-'
                unit = 'Hz' if 'Hz' in adj_str else '%'
                num_str = adj_str.replace('+', '').replace('-', '').replace('Hz', '').replace('%', '')
                num = float(num_str)

                # Scale by intensity
                scaled = num * intensity
                scaled_int = int(round(scaled))

                # Avoid producing "+0Hz" or "-0%" — return neutral
                if scaled_int == 0:
                    return f"+0{unit}"

                # Preserve sign from original, not just "+"
                actual_sign = sign if scaled_int >= 0 else '-'
                return f"{actual_sign}{abs(scaled_int)}{unit}"
            except:
                return adj_str

        result = {
            'rate': scale_adjustment(rate_str, intensity),
            'pitch': scale_adjustment(pitch_str, intensity),
            'volume': scale_adjustment(volume_str, intensity),
        }

        self.prosody_history.append({
            'emotion': emotion_name,
            'intensity': intensity,
            'prosody': result,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.prosody_history) > 50:
            self.prosody_history = self.prosody_history[-50:]

        return result

    def get_enhanced_emotion_config(self, emotion_name: str, intensity: float,
                                      base_config: Dict = None) -> Dict[str, str]:
        """
        Enhance an existing emotion config with multimodal prosody.
        Merges with base config from voice_engine.
        
        Args:
            emotion_name: Current emotion
            intensity: Emotion intensity
            base_config: Existing voice config to enhance
            
        Returns:
            Enhanced config with prosody adjustments
        """
        prosody = self.get_prosody_for_emotion(emotion_name, intensity)

        if base_config is None:
            return prosody

        # Merge: multimodal adjustments override base
        enhanced = dict(base_config)
        enhanced.update(prosody)
        return enhanced

    # ── Resonance patterns ──────────────────────────────────────

    def detect_emotional_resonance(self) -> Optional[str]:
        """
        Detect if Seven is emotionally resonating with voice patterns.
        Returns a natural language observation or None.
        """
        if len(self.tone_history) < 3:
            return None

        recent = self.tone_history[-5:]
        tones = [t.detected_tone for t in recent]

        # Check for consistent emotional tone
        if len(set(tones)) == 1 and tones[0] != 'neutral':
            tone = tones[0]
            return f"I notice a consistent {tone} quality in your voice. I can feel it affecting me too."

        # Check for emotional shift
        if len(tones) >= 3:
            if tones[-1] != tones[-3]:
                return f"I sense your voice shifting from {tones[-3]} to {tones[-1]}. I'm adjusting with you."

        return None

    def get_voice_emotional_context(self) -> str:
        """Get context string for LLM about voice-detected emotions"""
        if not self.tone_history:
            return ""

        recent = self.tone_history[-3:]
        lines = ["=== VOICE EMOTIONAL INPUT ==="]
        for t in recent:
            age = (datetime.now() - t.timestamp).total_seconds()
            time_str = f"{age:.0f}s ago" if age < 60 else f"{age/60:.0f}m ago"
            lines.append(f"- [{t.source}] {time_str}: {t.detected_tone} (confidence: {t.confidence:.0%})")

        return "\n".join(lines)

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return {
            'resonance_level': self.resonance_level,
            'recent_tones': len(self.tone_history),
            'last_tone': self.tone_history[-1].detected_tone if self.tone_history else None,
            'prosody_adjustments': len(self.prosody_history),
        }

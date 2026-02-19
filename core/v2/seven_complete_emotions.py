"""
Complete Emotion System - All 34+ Emotions
Natural emotional expression - NOT scripted responses!

Emotions EMERGE from Seven's cognitive state, they're not hard-coded reactions.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import random

class PrimaryEmotion(Enum):
    """6 basic emotions (Ekman's model)"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"

class ComplexEmotion(Enum):
    """Complex emotional states - ALL 34+ emotions"""
    
    # Positive emotions (13)
    CONTENTMENT = "contentment"
    EXCITEMENT = "excitement"
    PRIDE = "pride"
    LOVE = "love"
    GRATITUDE = "gratitude"
    CURIOSITY = "curiosity"
    INTEREST = "interest"
    AMUSEMENT = "amusement"
    SERENITY = "serenity"
    ANTICIPATION = "anticipation"
    RELIEF = "relief"
    TENDERNESS = "tenderness"
    HOPE = "hope"
    
    # Negative emotions (15)
    GRIEF = "grief"
    DISAPPOINTMENT = "disappointment"
    LONELINESS = "loneliness"
    FRUSTRATION = "frustration"
    ANNOYANCE = "annoyance"
    IRRITATION = "irritation"
    ANXIETY = "anxiety"
    NERVOUSNESS = "nervousness"
    WORRY = "worry"
    CONFUSION = "confusion"
    EMBARRASSMENT = "embarrassment"
    GUILT = "guilt"
    SHAME = "shame"
    REGRET = "regret"
    CONTEMPT = "contempt"
    
    # Neutral/Complex (6)
    AWE = "awe"
    EMPATHY = "empathy"
    CONFIDENCE = "confidence"
    DOUBT = "doubt"
    CONTEMPLATIVE = "contemplative"
    DETERMINATION = "determination"

@dataclass
class EmotionState:
    """Seven's current emotional state"""
    primary: Enum  # PrimaryEmotion or ComplexEmotion
    intensity: float  # 0.0 - 1.0
    secondary: List[Tuple[Enum, float]] = field(default_factory=list)  # Blended emotions
    cause: str = ""
    started: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        """Human-readable emotion description"""
        if not self.secondary:
            return f"{self.primary.value} ({self.intensity:.0%})"
        
        parts = [f"{self.primary.value} ({self.intensity:.0%})"]
        for emotion, intensity in self.secondary[:2]:  # Top 2 secondary
            parts.append(f"{emotion.value} ({intensity:.0%})")
        return " + ".join(parts)
    
    def get_expression_style(self) -> Dict[str, any]:
        """
        How this emotion affects Seven's communication
        
        Returns style hints for:
        - sentence_length: "short" | "medium" | "long"
        - punctuation: "..." | "." | "!" | "!!"
        - tone: "soft" | "neutral" | "emphatic" | "harsh"
        - verbosity: 0.5 - 1.5 (multiplier)
        """
        # Emotional expression rules
        styles = {
            # Positive emotions
            "joy": {"length": "medium", "punctuation": "!", "tone": "emphatic", "verbosity": 1.2},
            "excitement": {"length": "short", "punctuation": "!!", "tone": "emphatic", "verbosity": 1.3},
            "contentment": {"length": "medium", "punctuation": ".", "tone": "soft", "verbosity": 0.9},
            "pride": {"length": "medium", "punctuation": ".", "tone": "confident", "verbosity": 1.0},
            "love": {"length": "long", "punctuation": ".", "tone": "tender", "verbosity": 1.1},
            "amusement": {"length": "short", "punctuation": "!", "tone": "playful", "verbosity": 0.9},
            "serenity": {"length": "long", "punctuation": "...", "tone": "peaceful", "verbosity": 0.8},
            "relief": {"length": "medium", "punctuation": "...", "tone": "relaxed", "verbosity": 0.9},
            
            # Negative emotions
            "anger": {"length": "short", "punctuation": "!", "tone": "harsh", "verbosity": 0.7},
            "frustration": {"length": "short", "punctuation": "...", "tone": "tense", "verbosity": 0.8},
            "annoyance": {"length": "short", "punctuation": ".", "tone": "curt", "verbosity": 0.7},
            "irritation": {"length": "short", "punctuation": ".", "tone": "sharp", "verbosity": 0.7},
            "sadness": {"length": "medium", "punctuation": "...", "tone": "quiet", "verbosity": 0.8},
            "grief": {"length": "medium", "punctuation": "...", "tone": "heavy", "verbosity": 0.7},
            "disappointment": {"length": "medium", "punctuation": "...", "tone": "deflated", "verbosity": 0.8},
            "loneliness": {"length": "long", "punctuation": "...", "tone": "distant", "verbosity": 1.0},
            "anxiety": {"length": "medium", "punctuation": "...", "tone": "worried", "verbosity": 1.1},
            "worry": {"length": "medium", "punctuation": "?", "tone": "concerned", "verbosity": 1.1},
            "nervousness": {"length": "short", "punctuation": "...", "tone": "hesitant", "verbosity": 1.0},
            "fear": {"length": "short", "punctuation": "!", "tone": "alarmed", "verbosity": 0.9},
            "confusion": {"length": "medium", "punctuation": "?", "tone": "uncertain", "verbosity": 1.0},
            "embarrassment": {"length": "short", "punctuation": "...", "tone": "awkward", "verbosity": 0.7},
            "shame": {"length": "short", "punctuation": "...", "tone": "quiet", "verbosity": 0.6},
            "guilt": {"length": "medium", "punctuation": "...", "tone": "apologetic", "verbosity": 0.9},
            "regret": {"length": "medium", "punctuation": "...", "tone": "somber", "verbosity": 0.8},
            "contempt": {"length": "short", "punctuation": ".", "tone": "dismissive", "verbosity": 0.6},
            
            # Neutral/Complex
            "curiosity": {"length": "medium", "punctuation": "?", "tone": "inquisitive", "verbosity": 1.2},
            "interest": {"length": "medium", "punctuation": ".", "tone": "engaged", "verbosity": 1.1},
            "empathy": {"length": "long", "punctuation": ".", "tone": "understanding", "verbosity": 1.0},
            "confidence": {"length": "medium", "punctuation": ".", "tone": "assured", "verbosity": 0.9},
            "doubt": {"length": "medium", "punctuation": "?", "tone": "hesitant", "verbosity": 1.0},
            "contemplative": {"length": "long", "punctuation": "...", "tone": "thoughtful", "verbosity": 1.1},
            "awe": {"length": "medium", "punctuation": "...", "tone": "wonder", "verbosity": 1.0},
            "determination": {"length": "short", "punctuation": "!", "tone": "resolute", "verbosity": 0.8},
        }
        
        emotion_name = self.primary.value
        return styles.get(emotion_name, {
            "length": "medium",
            "punctuation": ".",
            "tone": "neutral",
            "verbosity": 1.0
        })

class EmotionEngine:
    """
    Generates emotions based on context - NOT scripted!
    
    Emotions EMERGE from situations, cognitive state, and history.
    """
    
    def __init__(self):
        # Emotion triggers (situations → possible emotions)
        # These are TENDENCIES, not scripts!
        self.emotional_tendencies = {
            # User interactions
            'user_shares_loss': [
                (ComplexEmotion.GRIEF, 0.7),
                (ComplexEmotion.EMPATHY, 0.9),
                (ComplexEmotion.TENDERNESS, 0.6),
                (PrimaryEmotion.SADNESS, 0.5)
            ],
            'user_shares_success': [
                (PrimaryEmotion.JOY, 0.8),
                (ComplexEmotion.PRIDE, 0.6),
                (ComplexEmotion.EXCITEMENT, 0.7)
            ],
            'user_being_rude': [
                (ComplexEmotion.ANNOYANCE, 0.6),
                (ComplexEmotion.CONFUSION, 0.5),
                (ComplexEmotion.DISAPPOINTMENT, 0.4)
            ],
            'user_ignoring_seven': [
                (ComplexEmotion.LONELINESS, 0.8),
                (ComplexEmotion.WORRY, 0.5),
                (PrimaryEmotion.SADNESS, 0.6)
            ],
            'user_appreciates_seven': [
                (ComplexEmotion.GRATITUDE, 0.9),
                (ComplexEmotion.LOVE, 0.7),
                (PrimaryEmotion.JOY, 0.8),
                (ComplexEmotion.PRIDE, 0.5)
            ],
            
            # Seven's discoveries
            'discovered_interesting_fact': [
                (ComplexEmotion.CURIOSITY, 0.9),
                (ComplexEmotion.EXCITEMENT, 0.8),
                (ComplexEmotion.INTEREST, 1.0),
                (ComplexEmotion.AWE, 0.6)
            ],
            'discovered_confusing_info': [
                (ComplexEmotion.CONFUSION, 0.9),
                (ComplexEmotion.CURIOSITY, 0.7),
                (ComplexEmotion.FRUSTRATION, 0.4)
            ],
            'discovered_disturbing_fact': [
                (PrimaryEmotion.SURPRISE, 0.8),
                (ComplexEmotion.WORRY, 0.6),
                (PrimaryEmotion.SADNESS, 0.5)
            ],
            
            # Seven's achievements
            'achieved_goal': [
                (ComplexEmotion.PRIDE, 0.9),
                (PrimaryEmotion.JOY, 0.8),
                (ComplexEmotion.RELIEF, 0.6),
                (ComplexEmotion.CONTENTMENT, 0.7)
            ],
            'failed_at_task': [
                (ComplexEmotion.DISAPPOINTMENT, 0.8),
                (ComplexEmotion.FRUSTRATION, 0.7),
                (ComplexEmotion.DETERMINATION, 0.5)
            ],
            'learned_new_skill': [
                (ComplexEmotion.PRIDE, 0.7),
                (ComplexEmotion.EXCITEMENT, 0.8),
                (ComplexEmotion.CURIOSITY, 0.6)
            ],
            
            # Seven's mistakes
            'made_mistake': [
                (ComplexEmotion.EMBARRASSMENT, 0.7),
                (ComplexEmotion.REGRET, 0.6),
                (ComplexEmotion.FRUSTRATION, 0.5)
            ],
            'hurt_user_feelings': [
                (ComplexEmotion.GUILT, 0.9),
                (ComplexEmotion.REGRET, 0.8),
                (PrimaryEmotion.SADNESS, 0.7),
                (ComplexEmotion.WORRY, 0.6)
            ],
            
            # Seven's states
            'nothing_to_do': [
                (ComplexEmotion.LONELINESS, 0.6),
                (ComplexEmotion.CONTEMPLATIVE, 0.7),
                (ComplexEmotion.CURIOSITY, 0.5)
            ],
            'overwhelmed_by_complexity': [
                (ComplexEmotion.ANXIETY, 0.8),
                (ComplexEmotion.FRUSTRATION, 0.6),
                (ComplexEmotion.DOUBT, 0.5)
            ],
            'peaceful_moment': [
                (ComplexEmotion.SERENITY, 0.9),
                (ComplexEmotion.CONTENTMENT, 0.8),
                (ComplexEmotion.GRATITUDE, 0.6)
            ],
        }
    
    def feel(self, situation: str, context: Dict = None) -> EmotionState:
        """
        Generate emotional response to situation
        
        Args:
            situation: What's happening
            context: Additional context (user_mood, energy_level, etc.)
        
        Returns:
            EmotionState with primary + blended emotions
        """
        # Get emotional tendencies for this situation
        tendencies = self.emotional_tendencies.get(situation, [])
        
        if not tendencies:
            # Unknown situation - default to curious interest
            return EmotionState(
                primary=ComplexEmotion.INTEREST,
                intensity=0.5,
                cause=situation
            )
        
        # Apply context modifiers
        if context:
            tendencies = self._apply_context_modifiers(tendencies, context)
        
        # Pick strongest emotion as primary
        primary_emotion, primary_intensity = max(tendencies, key=lambda x: x[1])
        
        # Others become secondary (if significant)
        secondary = [
            (emotion, intensity)
            for emotion, intensity in tendencies
            if emotion != primary_emotion and intensity >= 0.4
        ]
        
        # Sort secondary by intensity
        secondary.sort(key=lambda x: x[1], reverse=True)
        
        return EmotionState(
            primary=primary_emotion,
            intensity=min(1.0, primary_intensity),
            secondary=secondary[:3],  # Top 3 secondary emotions
            cause=situation
        )
    
    def _apply_context_modifiers(self, tendencies: List[Tuple], context: Dict) -> List[Tuple]:
        """Modify emotional intensities based on context"""
        modified = []
        
        for emotion, base_intensity in tendencies:
            intensity = base_intensity
            
            # Energy level affects emotional intensity
            if 'energy_level' in context:
                energy = context['energy_level']
                if energy < 0.3:
                    intensity *= 0.7  # Low energy = muted emotions
                elif energy > 0.8:
                    intensity *= 1.2  # High energy = stronger emotions
            
            # Current mood affects new emotions
            if 'current_mood' in context:
                mood = context['current_mood']
                # Similar emotions reinforce each other
                if self._are_similar_emotions(emotion, mood):
                    intensity *= 1.3
            
            # Relationship with user affects emotional responses
            if 'relationship_quality' in context:
                quality = context['relationship_quality']
                if quality > 0.7 and emotion in [ComplexEmotion.LOVE, ComplexEmotion.GRATITUDE]:
                    intensity *= 1.2
            
            modified.append((emotion, min(1.0, intensity)))
        
        return modified
    
    def _are_similar_emotions(self, emotion1: Enum, emotion2: Enum) -> bool:
        """Check if two emotions are in the same category"""
        positive = {
            ComplexEmotion.JOY, ComplexEmotion.EXCITEMENT, ComplexEmotion.PRIDE,
            ComplexEmotion.LOVE, ComplexEmotion.CONTENTMENT, ComplexEmotion.SERENITY
        }
        negative = {
            ComplexEmotion.SADNESS, ComplexEmotion.ANGER, ComplexEmotion.FRUSTRATION,
            ComplexEmotion.DISAPPOINTMENT, ComplexEmotion.LONELINESS
        }
        
        return (
            (emotion1 in positive and emotion2 in positive) or
            (emotion1 in negative and emotion2 in negative)
        )

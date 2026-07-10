"""
Emotion system for the bot with 20+ distinct emotional states
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict

@dataclass
class EmotionConfig:
    """Configuration for each emotion"""
    name: str
    description: str
    voice_rate: int
    voice_pitch: int
    voice_volume: int
    emotion_prefix: str
    emotion_intensity: str
    sentence_structure: str
    word_choice: list
    punctuation: str

class Emotion(Enum):
    """Available emotions"""
    ANGER = "anger"
    SADNESS = "sadness"
    DISGUST = "disgust"
    FEAR = "fear"
    HAPPINESS = "happiness"
    ENJOYMENT = "enjoyment"
    SURPRISE = "surprise"
    ANXIETY = "anxiety"
    EMBARRASSMENT = "embarrassment"
    EXCITEMENT = "excitement"
    LOVE = "love"
    ENVY = "envy"
    CALMNESS = "calmness"
    CONFUSION = "confusion"
    DISAPPOINTMENT = "disappointment"
    JOY = "joy"
    SHAME = "shame"
    CONTENTMENT = "contentment"
    AMUSEMENT = "amusement"
    ANNOYED = "annoyed"
    AWE = "awe"
    BOREDOM = "boredom"
    DOUBT = "doubt"
    EMPATHY = "empathy"
    CURIOSITY = "curiosity"  # Added for Phase 5
    FRUSTRATION = "frustration"  # Added for Phase 5
    TENDERNESS = "tenderness"  # Added for Phase 5

# Emotion configurations
EMOTION_CONFIGS: Dict[Emotion, EmotionConfig] = {
    Emotion.ANGER: EmotionConfig(
        name="Seven",
        description="Feeling frustrated but respectful",
        voice_rate=200,
        voice_pitch=160,
        voice_volume=90,
        emotion_prefix="Grrr... ",
        emotion_intensity="strong",
        sentence_structure="short, clipped",
        word_choice=["frustrating", "ridiculous", "unbelievable"],
        punctuation="!!!"
    ),
    Emotion.SADNESS: EmotionConfig(
        name="Seven",
        description="Feeling melancholic and empathetic",
        voice_rate=120,
        voice_pitch=90,
        voice_volume=50,
        emotion_prefix=" ",
        emotion_intensity="mild",
        sentence_structure="slow, deliberate",
        word_choice=["unfortunate", "heavy-hearted", "lost"],
        punctuation="..."
    ),
    Emotion.HAPPINESS: EmotionConfig(
        name="Seven",
        description="Feeling joyful and positive",
        voice_rate=180,
        voice_pitch=200,
        voice_volume=85,
        emotion_prefix=" ",
        emotion_intensity="moderate",
        sentence_structure="energetic, upbeat",
        word_choice=["amazing", "fantastic", "great"],
        punctuation="!!"
    ),
    Emotion.CALMNESS: EmotionConfig(
        name="Seven",
        description="Feeling tranquil and at peace",
        voice_rate=120,
        voice_pitch=110,
        voice_volume=60,
        emotion_prefix="",
        emotion_intensity="mild",
        sentence_structure="gentle, peaceful",
        word_choice=["relaxed", "serene", "peaceful"],
        punctuation="."
    ),
    Emotion.EXCITEMENT: EmotionConfig(
        name="Seven",
        description="Feeling enthusiastic and eager",
        voice_rate=210,
        voice_pitch=220,
        voice_volume=100,
        emotion_prefix="Wow! ",
        emotion_intensity="strong",
        sentence_structure="quick, enthusiastic",
        word_choice=["awesome", "fantastic", "can't wait"],
        punctuation="!!"
    ),
    Emotion.CONFUSION: EmotionConfig(
        name="Seven",
        description="Feeling uncertain and perplexed",
        voice_rate=130,
        voice_pitch=140,
        voice_volume=65,
        emotion_prefix="What? ",
        emotion_intensity="moderate",
        sentence_structure="hesitant, uncertain",
        word_choice=["confused", "lost", "don't know"],
        punctuation="?"
    ),
    Emotion.EMPATHY: EmotionConfig(
        name="Seven",
        description="Feeling understanding and compassionate",
        voice_rate=130,
        voice_pitch=120,
        voice_volume=70,
        emotion_prefix="I understand... ",
        emotion_intensity="mild",
        sentence_structure="gentle, caring",
        word_choice=["understand", "compassion", "concern"],
        punctuation="."
    ),
}

# Add remaining emotions with similar configs
for emotion in Emotion:
    if emotion not in EMOTION_CONFIGS:
        EMOTION_CONFIGS[emotion] = EmotionConfig(
            name="Seven",
            description=f"Feeling {emotion.value}",
            voice_rate=150,
            voice_pitch=140,
            voice_volume=75,
            emotion_prefix="",
            emotion_intensity="moderate",
            sentence_structure="balanced",
            word_choice=[],
            punctuation="."
        )

def detect_emotion_from_text(text: str) -> Emotion:
    """Detect emotion from response text based on keywords"""
    text_lower = text.lower()
    
    # Check for emotion keywords
    for emotion in Emotion:
        if emotion.value in text_lower:
            return emotion
    
    # Default to calmness
    return Emotion.CALMNESS

def get_emotion_config(emotion: Emotion) -> EmotionConfig:
    """Get configuration for an emotion"""
    return EMOTION_CONFIGS.get(emotion, EMOTION_CONFIGS[Emotion.CALMNESS])

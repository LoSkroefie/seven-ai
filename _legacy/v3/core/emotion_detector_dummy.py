"""Dummy Emotion Detector when librosa is not available"""

class VoiceEmotionDetector:
    """Placeholder for when emotion detection libs are not available"""
    def __init__(self, *args, **kwargs):
        raise ImportError("librosa not installed")

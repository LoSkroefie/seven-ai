"""Dummy Whisper module when whisper is not installed"""

class WhisperVoiceManager:
    """Placeholder for when Whisper is not available"""
    def __init__(self, *args, **kwargs):
        raise ImportError("Whisper not installed. Install with: pip install openai-whisper")

"""Dummy VAD module when webrtcvad is not installed"""

class VADListener:
    """Placeholder for when VAD is not available"""
    def __init__(self, *args, **kwargs):
        raise ImportError("webrtcvad not installed")

"""Dummy Vector Memory when chromadb is not available"""

class VectorMemory:
    """Placeholder for when chromadb is not available"""
    def __init__(self, *args, **kwargs):
        raise ImportError("chromadb not installed")

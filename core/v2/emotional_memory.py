"""
Seven AI v2.0 - Emotional Memory System
Tracks conversation emotions, moods, and feelings over time
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class EmotionalMemory:
    """
    Tracks emotional context of conversations to build emotional intelligence
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.memory_file = os.path.join(data_dir, "emotional_memory.json")
        self.memory = self._load_memory()
        
    def _load_memory(self) -> Dict:
        """Load emotional memory from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return self._create_empty_memory()
        return self._create_empty_memory()
    
    def _create_empty_memory(self) -> Dict:
        """Create empty memory structure"""
        return {
            "conversations": [],
            "emotional_patterns": {
                "positive_triggers": [],
                "negative_triggers": [],
                "neutral_topics": []
            },
            "mood_history": [],
            "current_mood": "neutral"
        }
    
    def _save_memory(self):
        """Save emotional memory to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
    
    def record_conversation(self, user_input: str, my_response: str, 
                          detected_emotion: str, conversation_quality: float):
        """
        Record a conversation with emotional context
        
        Args:
            user_input: What the user said
            my_response: What Seven responded
            detected_emotion: User's detected emotion (happy, sad, frustrated, excited, neutral)
            conversation_quality: Quality score 0-10
        """
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input[:200],  # First 200 chars
            "my_response": my_response[:200],
            "detected_emotion": detected_emotion,
            "quality": conversation_quality,
            "topics": self._extract_topics(user_input)
        }
        
        self.memory["conversations"].append(conversation)
        
        # Keep only last 1000 conversations
        if len(self.memory["conversations"]) > 1000:
            self.memory["conversations"] = self.memory["conversations"][-1000:]
        
        # Update emotional patterns
        self._update_emotional_patterns(user_input, detected_emotion)
        
        # Update mood history
        self._update_mood_history(detected_emotion)
        
        self._save_memory()
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        
        topic_keywords = {
            "work": ["work", "job", "project", "code", "development"],
            "personal": ["life", "family", "friend", "feeling"],
            "technical": ["bug", "error", "issue", "fix", "help"],
            "creative": ["idea", "create", "build", "design"],
            "health": ["health", "tired", "stressed", "exercise"]
        }
        
        text_lower = text.lower()
        for topic, words in topic_keywords.items():
            if any(word in text_lower for word in words):
                keywords.append(topic)
        
        return keywords
    
    def _update_emotional_patterns(self, text: str, emotion: str):
        """Learn what topics trigger which emotions"""
        topics = self._extract_topics(text)
        
        if emotion in ["happy", "excited", "content"]:
            for topic in topics:
                if topic not in self.memory["emotional_patterns"]["positive_triggers"]:
                    self.memory["emotional_patterns"]["positive_triggers"].append(topic)
        
        elif emotion in ["sad", "frustrated", "angry", "stressed"]:
            for topic in topics:
                if topic not in self.memory["emotional_patterns"]["negative_triggers"]:
                    self.memory["emotional_patterns"]["negative_triggers"].append(topic)
        
        else:  # neutral
            for topic in topics:
                if topic not in self.memory["emotional_patterns"]["neutral_topics"]:
                    self.memory["emotional_patterns"]["neutral_topics"].append(topic)
    
    def _update_mood_history(self, emotion: str):
        """Track mood over time"""
        mood_entry = {
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion
        }
        
        self.memory["mood_history"].append(mood_entry)
        
        # Keep only last 100 mood entries
        if len(self.memory["mood_history"]) > 100:
            self.memory["mood_history"] = self.memory["mood_history"][-100:]
        
        # Update current mood
        self.memory["current_mood"] = emotion
    
    def detect_emotion(self, text: str) -> str:
        """
        Detect emotion from user text
        Returns: happy, sad, frustrated, excited, stressed, angry, neutral
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ["happy", "great", "awesome", "love", "excellent", "good", "thanks", "perfect"]
        # Negative indicators
        negative_words = ["sad", "frustrated", "angry", "hate", "bad", "terrible", "worst", "annoyed"]
        # Excited indicators
        excited_words = ["excited", "amazing", "wow", "incredible", "fantastic"]
        # Stressed indicators
        stressed_words = ["stressed", "overwhelmed", "tired", "exhausted", "difficult"]
        
        # Count indicators
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        excited_count = sum(1 for word in excited_words if word in text_lower)
        stressed_count = sum(1 for word in stressed_words if word in text_lower)
        
        # Detect exclamation marks (excitement)
        exclamation_count = text.count('!')
        
        # Determine emotion
        if excited_count > 0 or exclamation_count >= 2:
            return "excited"
        elif stressed_count > 0:
            return "stressed"
        elif positive_count > negative_count:
            return "happy"
        elif negative_count > positive_count:
            if "angry" in text_lower or "hate" in text_lower:
                return "angry"
            elif "frustrated" in text_lower:
                return "frustrated"
            else:
                return "sad"
        else:
            return "neutral"
    
    def get_current_mood(self) -> str:
        """Get user's current mood"""
        return self.memory.get("current_mood", "neutral")
    
    def get_mood_trend(self) -> str:
        """
        Get recent mood trend
        Returns: improving, declining, stable
        """
        if len(self.memory["mood_history"]) < 3:
            return "stable"
        
        # Look at last 5 moods
        recent_moods = self.memory["mood_history"][-5:]
        
        positive_moods = ["happy", "excited", "content"]
        negative_moods = ["sad", "frustrated", "angry", "stressed"]
        
        positive_count = sum(1 for m in recent_moods if m["emotion"] in positive_moods)
        negative_count = sum(1 for m in recent_moods if m["emotion"] in negative_moods)
        
        if positive_count > negative_count + 1:
            return "improving"
        elif negative_count > positive_count + 1:
            return "declining"
        else:
            return "stable"
    
    def get_positive_triggers(self) -> List[str]:
        """Get topics that make user happy"""
        return self.memory["emotional_patterns"]["positive_triggers"]
    
    def get_negative_triggers(self) -> List[str]:
        """Get topics that frustrate user"""
        return self.memory["emotional_patterns"]["negative_triggers"]
    
    def get_emotional_summary(self) -> Dict:
        """Get summary of emotional state"""
        return {
            "current_mood": self.get_current_mood(),
            "mood_trend": self.get_mood_trend(),
            "positive_triggers": self.get_positive_triggers(),
            "negative_triggers": self.get_negative_triggers(),
            "recent_conversations": len(self.memory["conversations"][-10:]),
            "total_conversations": len(self.memory["conversations"])
        }
    
    def should_check_in(self) -> bool:
        """Determine if Seven should check in based on emotional state"""
        # Check in if mood is declining
        if self.get_mood_trend() == "declining":
            return True
        
        # Check in if current mood is negative
        if self.get_current_mood() in ["sad", "frustrated", "angry", "stressed"]:
            return True
        
        return False
    
    def get_state(self) -> Dict:
        """Get current state of emotional memory system"""
        return {
            "current_mood": self.get_current_mood(),
            "mood_trend": self.get_mood_trend(),
            "total_conversations": len(self.memory["conversations"]),
            "recent_conversations": len(self.memory["conversations"][-10:]),
            "positive_triggers_count": len(self.get_positive_triggers()),
            "negative_triggers_count": len(self.get_negative_triggers())
        }
    
    def get_recent_mood(self) -> str:
        """Get the most recent mood for proactive engine"""
        return self.get_current_mood()
    
    def get_recent_topics(self) -> List[str]:
        """Get recently discussed topics for proactive engine"""
        recent_conversations = self.memory["conversations"][-5:]
        topics = []
        for conv in recent_conversations:
            topics.extend(conv.get("topics", []))
        return list(set(topics))[:5]  # Return unique topics, max 5
    
    def save(self):
        """Save emotional memory to disk"""
        self._save_memory()


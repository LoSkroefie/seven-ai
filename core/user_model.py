"""
Deep user modeling system
Builds comprehensive profile of user over time
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import config

class UserModel:
    """Comprehensive user profile"""
    
    def __init__(self):
        self.profile_file = config.DATA_DIR / "user_profile.json"
        self.profile = self._load_profile()
    
    def _load_profile(self) -> Dict:
        """Load user profile"""
        if self.profile_file.exists():
            try:
                return json.loads(self.profile_file.read_text())
            except:
                pass
        
        # Default profile
        return {
            "basic_info": {
                "name": None,
                "preferred_name": None,
                "location": None,
                "timezone": None
            },
            "personality": {
                "communication_style": "unknown",  # formal, casual, technical, friendly
                "humor_preference": "unknown",  # loves_jokes, occasional, serious
                "detail_preference": "unknown"  # brief, moderate, detailed
            },
            "interests": {
                "topics": [],  # List of topics with engagement scores
                "hobbies": [],
                "professions": []
            },
            "preferences": {
                "voice_speed": "normal",
                "interaction_frequency": "moderate",
                "proactive_level": "moderate"
            },
            "conversation_patterns": {
                "active_times": [],  # Times user typically talks
                "avg_session_length": 0,
                "total_conversations": 0,
                "preferred_topics": []
            },
            "goals": [],  # User goals tracked over time
            "context": {
                "current_projects": [],
                "recent_topics": [],
                "ongoing_threads": []
            },
            "learning_style": "unknown",  # visual, auditory, kinesthetic, mixed
            "relationship_depth": "new",  # new, acquaintance, friend, close_friend
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_profile(self):
        """Save profile to disk"""
        try:
            self.profile["last_updated"] = datetime.now().isoformat()
            self.profile_file.write_text(json.dumps(self.profile, indent=2))
        except Exception as e:
            print(f"[WARNING]  Error saving user profile: {e}")
    
    def update_basic_info(self, **kwargs):
        """Update basic user information"""
        for key, value in kwargs.items():
            if key in self.profile["basic_info"]:
                self.profile["basic_info"][key] = value
        self._save_profile()
    
    def add_interest(self, topic: str, engagement_score: float = 0.5):
        """Add or update interest"""
        interests = self.profile["interests"]["topics"]
        
        # Check if exists
        for interest in interests:
            if interest["topic"] == topic:
                interest["engagement_score"] = max(interest["engagement_score"], engagement_score)
                interest["last_mentioned"] = datetime.now().isoformat()
                self._save_profile()
                return
        
        # Add new
        interests.append({
            "topic": topic,
            "engagement_score": engagement_score,
            "first_mentioned": datetime.now().isoformat(),
            "last_mentioned": datetime.now().isoformat(),
            "mention_count": 1
        })
        self._save_profile()
    
    def infer_communication_style(self, user_input: str):
        """Infer communication style from user input"""
        user_lower = user_input.lower()
        
        # Detect formality
        formal_markers = ["please", "thank you", "would you", "could you"]
        casual_markers = ["hey", "yep", "yeah", "gonna", "wanna"]
        
        if any(marker in user_lower for marker in formal_markers):
            self.profile["personality"]["communication_style"] = "formal"
        elif any(marker in user_lower for marker in casual_markers):
            self.profile["personality"]["communication_style"] = "casual"
        
        self._save_profile()  # AUTO-SAVE after inference
    
    def track_conversation(self, topic: Optional[str] = None, duration_seconds: Optional[int] = None):
        """Track conversation patterns"""
        patterns = self.profile["conversation_patterns"]
        patterns["total_conversations"] += 1
        
        # Track active time
        now = datetime.now()
        hour = now.hour
        if hour not in patterns["active_times"]:
            patterns["active_times"].append(hour)
        
        # Track topic
        if topic and topic not in patterns["preferred_topics"]:
            patterns["preferred_topics"].append(topic)
        
        self._save_profile()  # AUTO-SAVE after tracking
        
        self._save_profile()
    
    def add_goal(self, goal: str, category: str = "general"):
        """Add user goal to track"""
        self.profile["goals"].append({
            "goal": goal,
            "category": category,
            "added_at": datetime.now().isoformat(),
            "status": "active",
            "progress_notes": []
        })
        self._save_profile()
    
    def update_relationship_depth(self, conversation_count: int):
        """Update relationship depth based on interactions"""
        if conversation_count > 100:
            depth = "close_friend"
        elif conversation_count > 50:
            depth = "friend"
        elif conversation_count > 20:
            depth = "acquaintance"
        else:
            depth = "new"
        
        self.profile["relationship_depth"] = depth
        self._save_profile()
    
    def get_profile_context(self) -> str:
        """Generate context string for LLM"""
        lines = ["User Profile:"]
        
        # Basic info
        if self.profile["basic_info"]["name"]:
            lines.append(f"Name: {self.profile['basic_info']['name']}")
        
        # Interests
        if self.profile["interests"]["topics"]:
            top_interests = sorted(
                self.profile["interests"]["topics"],
                key=lambda x: x["engagement_score"],
                reverse=True
            )[:5]
            topics = [i["topic"] for i in top_interests]
            lines.append(f"Interests: {', '.join(topics)}")
        
        # Communication style
        style = self.profile["personality"]["communication_style"]
        if style != "unknown":
            lines.append(f"Communication style: {style}")
        
        # Relationship
        lines.append(f"Relationship: {self.profile['relationship_depth']}")
        
        # Preferences
        prefs = self.profile["preferences"]
        if prefs:
            lines.append(f"Prefers: {prefs.get('detail_preference', 'balanced')} explanations")
        
        return "\n".join(lines)
    
    def get_full_profile(self) -> Dict:
        """Get complete profile"""
        return self.profile

"""
Seven AI v2.0 - Relationship Model
Tracks relationship depth, rapport, and interaction history
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List

class RelationshipModel:
    """
    Models the relationship between Seven and the user
    Tracks rapport, depth, shared experiences
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.relationship_file = os.path.join(data_dir, "relationship_data.json")
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load relationship data from disk"""
        if os.path.exists(self.relationship_file):
            try:
                with open(self.relationship_file, 'r') as f:
                    return json.load(f)
            except:
                return self._create_empty_data()
        return self._create_empty_data()
    
    def _create_empty_data(self) -> Dict:
        """Create empty relationship structure"""
        return {
            "relationship_start": datetime.now().isoformat(),
            "total_interactions": 0,
            "quality_interactions": 0,  # Quality > 7
            "rapport_level": 1,  # 1-10 scale
            "trust_level": 5,  # 1-10 scale
            "shared_experiences": [],
            "milestones": [],
            "conversation_streak": 0,
            "last_interaction": None,
            "interaction_history": []
        }
    
    def _save_data(self):
        """Save relationship data to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.relationship_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_interaction(self, conversation_quality: float, 
                          topics: List[str], emotional_valence: str):
        """
        Record an interaction
        
        Args:
            conversation_quality: Quality score 0-10
            topics: Topics discussed
            emotional_valence: positive, negative, neutral
        """
        # Update interaction count
        self.data["total_interactions"] += 1
        
        # Track quality interactions
        if conversation_quality >= 7.0:
            self.data["quality_interactions"] += 1
        
        # Update rapport based on quality
        self._update_rapport(conversation_quality, emotional_valence)
        
        # Update trust
        self._update_trust(conversation_quality)
        
        # Update streak
        self._update_streak()
        
        # Record interaction
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "quality": conversation_quality,
            "topics": topics,
            "emotional_valence": emotional_valence
        }
        
        self.data["interaction_history"].append(interaction)
        
        # Keep only last 200 interactions
        if len(self.data["interaction_history"]) > 200:
            self.data["interaction_history"] = self.data["interaction_history"][-200:]
        
        # Update last interaction time
        self.data["last_interaction"] = datetime.now().isoformat()
        
        # Check for milestones
        self._check_milestones()
        
        self._save_data()
    
    def _update_rapport(self, quality: float, valence: str):
        """Update rapport level based on interaction"""
        current_rapport = self.data["rapport_level"]
        
        # Positive interactions increase rapport
        if quality >= 7.0 and valence == "positive":
            self.data["rapport_level"] = min(10, current_rapport + 0.1)
        
        # Neutral interactions maintain rapport
        elif quality >= 5.0:
            pass  # No change
        
        # Negative interactions decrease rapport slightly
        else:
            self.data["rapport_level"] = max(1, current_rapport - 0.05)
    
    def _update_trust(self, quality: float):
        """Update trust level"""
        current_trust = self.data["trust_level"]
        
        # High quality interactions build trust
        if quality >= 8.0:
            self.data["trust_level"] = min(10, current_trust + 0.1)
        
        # Low quality interactions erode trust slightly
        elif quality < 4.0:
            self.data["trust_level"] = max(1, current_trust - 0.05)
    
    def _update_streak(self):
        """Update conversation streak"""
        last_interaction = self.data.get("last_interaction")
        
        if last_interaction:
            last_time = datetime.fromisoformat(last_interaction)
            now = datetime.now()
            
            # If within 24 hours, continue streak
            if (now - last_time).total_seconds() < 86400:  # 24 hours
                self.data["conversation_streak"] += 1
            else:
                # Streak broken
                self.data["conversation_streak"] = 1
        else:
            self.data["conversation_streak"] = 1
    
    def _check_milestones(self):
        """Check and record milestones"""
        total = self.data["total_interactions"]
        milestones_hit = [m["milestone"] for m in self.data["milestones"]]
        
        milestone_thresholds = {
            10: "First 10 conversations",
            50: "50 conversations milestone",
            100: "Reached 100 conversations",
            250: "250 conversations - Strong bond",
            500: "500 conversations - Deep connection",
            1000: "1000 conversations - Unbreakable bond"
        }
        
        for threshold, description in milestone_thresholds.items():
            if total >= threshold and description not in milestones_hit:
                milestone = {
                    "milestone": description,
                    "reached_at": datetime.now().isoformat(),
                    "interaction_count": total
                }
                self.data["milestones"].append(milestone)
    
    def add_shared_experience(self, experience: str, significance: float):
        """
        Record a shared experience
        
        Args:
            experience: Description of experience
            significance: How significant (0-10)
        """
        shared_exp = {
            "timestamp": datetime.now().isoformat(),
            "experience": experience,
            "significance": significance
        }
        
        self.data["shared_experiences"].append(shared_exp)
        
        # Keep only most significant experiences (top 50)
        if len(self.data["shared_experiences"]) > 50:
            self.data["shared_experiences"].sort(
                key=lambda x: x["significance"], 
                reverse=True
            )
            self.data["shared_experiences"] = self.data["shared_experiences"][:50]
        
        self._save_data()
    
    def get_relationship_depth(self) -> str:
        """
        Get relationship depth level
        Returns: stranger, acquaintance, friend, close_friend, companion
        """
        total = self.data["total_interactions"]
        rapport = self.data["rapport_level"]
        trust = self.data["trust_level"]
        
        # Calculate depth score
        depth_score = (total * 0.3) + (rapport * 5) + (trust * 5)
        
        if depth_score < 50:
            return "stranger"
        elif depth_score < 150:
            return "acquaintance"
        elif depth_score < 300:
            return "friend"
        elif depth_score < 500:
            return "close_friend"
        else:
            return "companion"
    
    def get_rapport_level(self) -> float:
        """Get current rapport level (1-10)"""
        return self.data["rapport_level"]
    
    def get_trust_level(self) -> float:
        """Get current trust level (1-10)"""
        return self.data["trust_level"]
    
    def get_total_interactions(self) -> int:
        """Get total number of interactions"""
        return self.data["total_interactions"]
    
    def get_quality_interaction_ratio(self) -> float:
        """Get ratio of quality interactions"""
        if self.data["total_interactions"] == 0:
            return 0.0
        return self.data["quality_interactions"] / self.data["total_interactions"]
    
    def get_days_since_start(self) -> int:
        """Get days since relationship started"""
        start = datetime.fromisoformat(self.data["relationship_start"])
        now = datetime.now()
        return (now - start).days
    
    def get_current_streak(self) -> int:
        """Get current conversation streak"""
        return self.data["conversation_streak"]
    
    def get_milestones(self) -> List[Dict]:
        """Get all reached milestones"""
        return self.data["milestones"]
    
    def get_recent_milestones(self, count: int = 3) -> List[Dict]:
        """Get most recent milestones"""
        return self.data["milestones"][-count:] if self.data["milestones"] else []
    
    def get_shared_experiences(self) -> List[Dict]:
        """Get significant shared experiences"""
        return sorted(
            self.data["shared_experiences"],
            key=lambda x: x["significance"],
            reverse=True
        )
    
    def time_since_last_interaction(self) -> float:
        """Get hours since last interaction"""
        if not self.data.get("last_interaction"):
            return 999  # Large number if never interacted
        
        last_time = datetime.fromisoformat(self.data["last_interaction"])
        now = datetime.now()
        return (now - last_time).total_seconds() / 3600  # Hours
    
    def should_reach_out(self) -> bool:
        """Determine if Seven should proactively reach out"""
        hours = self.time_since_last_interaction()
        depth = self.get_relationship_depth()
        
        # Don't reach out if talked recently
        if hours < 8:
            return False
        
        # Reach out based on relationship depth
        if depth == "companion" and hours > 24:
            return True
        elif depth == "close_friend" and hours > 48:
            return True
        elif depth == "friend" and hours > 72:
            return True
        
        return False
    
    def get_relationship_summary(self) -> Dict:
        """Get comprehensive relationship summary"""
        return {
            "depth": self.get_relationship_depth(),
            "rapport": self.get_rapport_level(),
            "trust": self.get_trust_level(),
            "total_interactions": self.get_total_interactions(),
            "quality_ratio": self.get_quality_interaction_ratio(),
            "days_together": self.get_days_since_start(),
            "current_streak": self.get_current_streak(),
            "recent_milestones": self.get_recent_milestones(),
            "hours_since_last": self.time_since_last_interaction()
        }
    
    def get_state(self) -> Dict:
        """Get current state of relationship model for v2.0 integration"""
        return self.get_relationship_summary()
    
    def get_depth(self) -> str:
        """Alias for get_relationship_depth() for compatibility"""
        return self.get_relationship_depth()
    
    def save(self):
        """Save relationship data to disk"""
        self._save_data()


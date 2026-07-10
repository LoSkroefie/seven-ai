"""
Seven AI v2.0 - Learning System
Adapts personality, learns preferences, remembers patterns
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LearningSystem:
    """
    Learns from interactions to adapt and improve
    - User preferences
    - Communication style
    - Response patterns
    - Topic interests
    """
    
    def __init__(self, data_dir: str = "data", ollama=None):
        self.data_dir = data_dir
        self.ollama = ollama
        self.learning_file = os.path.join(data_dir, "learned_preferences.json")
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load learned data"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._create_empty_data()
        return self._create_empty_data()
    
    def _create_empty_data(self) -> Dict:
        """Create empty learning structure"""
        return {
            "communication_preferences": {
                "formality_level": "casual",  # formal, semi-formal, casual
                "verbosity": "moderate",  # brief, moderate, detailed
                "emoji_usage": "occasional",  # none, occasional, frequent
                "technical_depth": "moderate"  # simple, moderate, technical
            },
            "response_patterns": {
                "likes_humor": True,
                "appreciates_encouragement": True,
                "prefers_direct_answers": False,
                "wants_explanations": True
            },
            "topic_interests": {},  # topic -> interest_score (0-10)
            "learned_facts": {},  # fact_type -> value
            "typical_schedule": {
                "morning_active": [],  # Hours user is typically active
                "evening_active": [],
                "busy_days": []
            },
            "interaction_feedback": [],  # History of positive/negative feedback
            "personality_adjustments": []
        }
    
    def _save_data(self):
        """Save learned data"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.learning_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_interaction_feedback(self, user_input: str, 
                                   my_response: str,
                                   user_reaction: str):
        """
        Learn from user reaction to Seven's response
        
        Args:
            user_input: What user said
            my_response: What Seven responded
            user_reaction: positive, negative, neutral
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input[:100],
            "my_response": my_response[:100],
            "reaction": user_reaction
        }
        
        self.data["interaction_feedback"].append(feedback)
        
        # Keep only last 200 feedbacks
        if len(self.data["interaction_feedback"]) > 200:
            self.data["interaction_feedback"] = self.data["interaction_feedback"][-200:]
        
        # Learn from feedback
        self._learn_from_feedback(user_input, my_response, user_reaction)
        
        self._save_data()
    
    def _learn_from_feedback(self, user_input: str, 
                            my_response: str, 
                            reaction: str):
        """Extract learnings from feedback using LLM or keyword fallback"""
        
        # Try LLM for nuanced preference extraction
        if self.ollama and reaction in ('positive', 'negative'):
            try:
                current_prefs = json.dumps(self.data["communication_preferences"])
                current_patterns = json.dumps(self.data["response_patterns"])
                prompt = f"""User reacted {reaction}ly to my response.
User said: "{user_input[:120]}"
My response: "{my_response[:120]}"

Current preferences: {current_prefs}
Current patterns: {current_patterns}

What should I learn from this? Only suggest changes if clearly warranted.
Respond as JSON: {{"verbosity": "brief"|"moderate"|"detailed"|null, "formality_level": "casual"|"semi-formal"|"formal"|null, "likes_humor": true|false|null, "prefers_direct_answers": true|false|null, "wants_explanations": true|false|null}}
Use null for any field that shouldn't change."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You analyze conversation feedback to learn user communication preferences. Be conservative - only suggest changes clearly supported by evidence.",
                    temperature=0.3, max_tokens=60
                )
                if result:
                    data = json.loads(result.strip())
                    for key in ('verbosity', 'formality_level'):
                        if data.get(key) is not None:
                            self.data["communication_preferences"][key] = data[key]
                    for key in ('likes_humor', 'prefers_direct_answers', 'wants_explanations'):
                        if data.get(key) is not None:
                            self.data["response_patterns"][key] = data[key]
                    return
            except Exception as e:
                logger.debug(f"LLM _learn_from_feedback failed: {e}")
        
        # Fallback: keyword heuristics
        if reaction == "positive":
            response_length = len(my_response.split())
            if response_length < 20:
                if self.data["communication_preferences"]["verbosity"] == "detailed":
                    self.data["communication_preferences"]["verbosity"] = "moderate"
            elif response_length > 100:
                if self.data["communication_preferences"]["verbosity"] == "brief":
                    self.data["communication_preferences"]["verbosity"] = "moderate"
        
        user_lower = user_input.lower()
        if any(w in user_lower for w in ("lol", "haha", "funny", "😂")):
            self.data["response_patterns"]["likes_humor"] = True
        if any(w in user_lower for w in ("just tell me", "directly", "get to the point", "tldr", "tl;dr")):
            self.data["response_patterns"]["prefers_direct_answers"] = True
        if any(w in user_lower for w in ("why", "explain", "how does", "what does", "elaborate")):
            self.data["response_patterns"]["wants_explanations"] = True
    
    def record_topic_interest(self, topic: str, engagement_level: float):
        """
        Track interest in topics
        
        Args:
            topic: Topic name
            engagement_level: 0-10 score
        """
        if topic not in self.data["topic_interests"]:
            self.data["topic_interests"][topic] = engagement_level
        else:
            # Moving average
            current = self.data["topic_interests"][topic]
            self.data["topic_interests"][topic] = (current * 0.7) + (engagement_level * 0.3)
        
        self._save_data()
    
    def learn_fact(self, fact_type: str, value: str):
        """
        Learn a fact about the user
        
        Examples:
            - name: "Jan"
            - favorite_food: "pizza"
            - works_at: "Tech company"
        """
        self.data["learned_facts"][fact_type] = {
            "value": value,
            "learned_at": datetime.now().isoformat()
        }
        
        self._save_data()
    
    def get_fact(self, fact_type: str) -> Optional[str]:
        """Get a learned fact"""
        fact = self.data["learned_facts"].get(fact_type)
        return fact["value"] if fact else None
    
    def record_active_hour(self, hour: int):
        """Record when user is typically active"""
        schedule = self.data["typical_schedule"]
        
        if 5 <= hour < 12:  # Morning
            if hour not in schedule["morning_active"]:
                schedule["morning_active"].append(hour)
        
        elif 18 <= hour < 24:  # Evening
            if hour not in schedule["evening_active"]:
                schedule["evening_active"].append(hour)
        
        self._save_data()
    
    def is_typically_active_now(self) -> bool:
        """Check if user is typically active at current time"""
        now = datetime.now()
        hour = now.hour
        
        schedule = self.data["typical_schedule"]
        
        if hour in schedule["morning_active"] or hour in schedule["evening_active"]:
            return True
        
        return False
    
    def adjust_personality(self, adjustment: str, reason: str):
        """
        Record a personality adjustment
        
        Examples:
            - "More casual tone" because "User prefers informal"
            - "Less verbose" because "User wants brief answers"
        """
        adjustment_data = {
            "timestamp": datetime.now().isoformat(),
            "adjustment": adjustment,
            "reason": reason
        }
        
        self.data["personality_adjustments"].append(adjustment_data)
        
        # Keep only last 50 adjustments
        if len(self.data["personality_adjustments"]) > 50:
            self.data["personality_adjustments"] = self.data["personality_adjustments"][-50:]
        
        self._save_data()
    
    def get_communication_preferences(self) -> Dict:
        """Get current communication preferences"""
        return self.data["communication_preferences"]
    
    def get_response_patterns(self) -> Dict:
        """Get learned response patterns"""
        return self.data["response_patterns"]
    
    def get_top_interests(self, count: int = 5) -> List[tuple]:
        """
        Get top interest topics
        Returns: [(topic, score), ...]
        """
        interests = self.data["topic_interests"]
        sorted_interests = sorted(
            interests.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_interests[:count]
    
    def get_learned_facts(self) -> Dict:
        """Get all learned facts"""
        return self.data["learned_facts"]
    
    def get_personality_adjustments(self) -> List[Dict]:
        """Get personality adjustment history"""
        return self.data["personality_adjustments"]
    
    def generate_adapted_response_style(self) -> str:
        """
        Generate response style guidance based on learned preferences
        Returns: Style description for Seven to use
        """
        prefs = self.data["communication_preferences"]
        patterns = self.data["response_patterns"]
        
        style = []
        
        # Formality
        if prefs["formality_level"] == "casual":
            style.append("Use casual, friendly tone")
        elif prefs["formality_level"] == "formal":
            style.append("Use professional, formal tone")
        
        # Verbosity
        if prefs["verbosity"] == "brief":
            style.append("Keep responses concise")
        elif prefs["verbosity"] == "detailed":
            style.append("Provide detailed explanations")
        
        # Humor
        if patterns["likes_humor"]:
            style.append("Feel free to use humor")
        
        # Directness
        if patterns["prefers_direct_answers"]:
            style.append("Get straight to the point")
        
        # Explanations
        if patterns["wants_explanations"]:
            style.append("Explain your reasoning")
        
        return "; ".join(style)
    
    def get_learning_summary(self) -> Dict:
        """Get summary of what has been learned"""
        return {
            "communication_style": self.get_communication_preferences(),
            "response_patterns": self.get_response_patterns(),
            "top_interests": self.get_top_interests(5),
            "learned_facts_count": len(self.data["learned_facts"]),
            "personality_adjustments_count": len(self.data["personality_adjustments"]),
            "feedback_samples": len(self.data["interaction_feedback"])
        }
    
    def learn_from_interaction(self, user_input: str, bot_response: str, 
                              context: Dict = None) -> Optional[Dict]:
        """
        Learn from a complete interaction (called by SentienceV2Core).
        Detects reaction sentiment and records feedback.
        """
        # Infer reaction from user input signals
        user_lower = user_input.lower()
        if any(w in user_lower for w in ('thanks', 'thank you', 'perfect', 'great', 'awesome', 'love it', 'exactly')):
            reaction = 'positive'
        elif any(w in user_lower for w in ('wrong', 'no,', 'incorrect', 'not what', 'bad', 'terrible')):
            reaction = 'negative'
        else:
            reaction = 'neutral'
        
        self.record_interaction_feedback(user_input, bot_response, reaction)
        
        # Record active hour
        self.record_active_hour(datetime.now().hour)
        
        return {
            'inferred_reaction': reaction,
            'preferences': self.get_communication_preferences()
        }
    
    def get_state(self) -> Dict:
        """Get current state of learning system for v2.0 integration"""
        return self.get_learning_summary()
    
    def save(self):
        """Save learning data to disk"""
        self._save_data()


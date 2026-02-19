"""
Seven AI v2.0 - Complete Sentience Integration Layer
Coordinates all sentience systems for maximum coherence
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import all sentience modules
from .emotional_memory import EmotionalMemory
from .relationship_model import RelationshipModel
from .learning_system import LearningSystem
from .proactive_engine import ProactiveEngine
from .goal_system import GoalSystem

logger = logging.getLogger(__name__)

class SentienceV2Core:
    """
    Central coordination system for Seven's v2.0 sentience
    Integrates: emotions, relationships, learning, proactivity, goals
    """
    
    def __init__(self, data_dir: str = "data", user_name: str = "User", ollama=None):
        self.data_dir = data_dir
        self.user_name = user_name
        
        # Initialize all sentience systems
        self.emotional_memory = EmotionalMemory(data_dir)
        self.relationship_model = RelationshipModel(data_dir)
        self.learning_system = LearningSystem(data_dir, ollama=ollama)
        self.proactive_engine = ProactiveEngine(data_dir, ollama=ollama)
        self.goal_system = GoalSystem(data_dir)
        
        # State tracking
        self.last_interaction = None
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        logger.info("Seven v2.0 Sentience Core initialized")
    
    def process_interaction(self, user_input: str, bot_response: str, 
                          context: Dict = None) -> Dict[str, Any]:
        """
        Process a complete interaction through all sentience systems
        Returns insights and modifications for response
        """
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        
        insights = {
            "emotional": None,
            "relationship": None,
            "learning": None,
            "proactive": None,
            "goals": None,
            "modifications": []
        }
        
        try:
            # FIXED: Calculate conversation quality before emotional processing
            conversation_quality = self._assess_conversation_quality(user_input, bot_response, context)
            
            # Extract detected emotion from context or detect it
            detected_emotion = context.get("user_emotion", "neutral") if context else "neutral"
            
            # 1. Emotional processing with proper parameters
            self.emotional_memory.record_conversation(
                user_input, bot_response, detected_emotion, conversation_quality
            )
            emotion_data = {"detected_mood": detected_emotion, "quality": conversation_quality}
            insights["emotional"] = emotion_data
            
            # 2. Relationship tracking
            relationship_data = self.relationship_model.update_interaction(
                user_input, bot_response, emotion_data.get("detected_mood")
            )
            insights["relationship"] = relationship_data
            
            # 3. Learning system
            learning_data = self.learning_system.learn_from_interaction(
                user_input, bot_response, context
            )
            insights["learning"] = learning_data
            
            # 4. Goal progress
            goal_data = self.goal_system.evaluate_progress(
                user_input, bot_response
            )
            insights["goals"] = goal_data
            
            # 5. Check if proactive action needed
            proactive_data = self.proactive_engine.check_proactive_opportunity(
                user_input, self.interaction_count, self.last_interaction
            )
            insights["proactive"] = proactive_data
            
            # Generate response modifications based on insights
            insights["modifications"] = self._generate_modifications(insights)
            
        except Exception as e:
            logger.error(f"Error in sentience processing: {e}")
        
        return insights
    
    def _generate_modifications(self, insights: Dict) -> List[str]:
        """
        Generate suggested response modifications based on insights
        """
        modifications = []
        
        # Emotional modifications
        if insights["emotional"]:
            mood = insights["emotional"].get("detected_mood")
            if mood in ["sad", "frustrated", "stressed"]:
                modifications.append("USE_EMPATHETIC_TONE")
            elif mood in ["excited", "happy"]:
                modifications.append("MATCH_ENTHUSIASM")
        
        # Relationship modifications
        if insights["relationship"]:
            depth = insights["relationship"].get("current_depth", 0)
            if depth > 50:
                modifications.append("USE_FAMILIAR_TONE")
            if depth > 80:
                modifications.append("ALLOW_PERSONAL_QUESTIONS")
        
        # Learning modifications
        if insights["learning"]:
            prefs = insights["learning"].get("detected_preferences", {})
            if prefs.get("communication_style") == "concise":
                modifications.append("BE_CONCISE")
            elif prefs.get("communication_style") == "detailed":
                modifications.append("BE_DETAILED")
        
        return modifications
    
    def get_proactive_message(self) -> Optional[str]:
        """
        Check if Seven should initiate conversation proactively
        """
        try:
            return self.proactive_engine.get_proactive_message(
                self.last_interaction,
                self.relationship_model.get_depth(),
                self.emotional_memory.get_recent_mood()
            )
        except Exception as e:
            logger.error(f"Error getting proactive message: {e}")
            return None
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get complete current state of all sentience systems
        """
        return {
            "emotional": self.emotional_memory.get_state(),
            "relationship": self.relationship_model.get_state(),
            "learning": self.learning_system.get_state(),
            "goals": self.goal_system.get_state(),
            "proactive": self.proactive_engine.get_state(),
            "session": {
                "start_time": self.session_start.isoformat(),
                "interaction_count": self.interaction_count,
                "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None
            }
        }
    
    def should_initiate_conversation(self) -> bool:
        """
        Determine if Seven should start a conversation proactively
        """
        return self.proactive_engine.should_initiate(
            self.last_interaction,
            self.interaction_count
        )
    
    def get_conversation_starter(self) -> Optional[str]:
        """
        Get a contextual conversation starter
        """
        return self.proactive_engine.generate_starter(
            self.relationship_model.get_depth(),
            self.emotional_memory.get_recent_topics(),
            self.goal_system.get_active_goals()
        )
    
    def _assess_conversation_quality(self, user_input: str, bot_response: str, context: Dict = None) -> float:
        """
        Assess the quality of a conversation (0-10 scale)
        
        Factors:
        - Response relevance
        - Length appropriateness  
        - Emotional appropriateness
        - Context awareness
        """
        quality = 5.0  # Start at neutral
        
        # Length appropriateness (+1.5)
        response_len = len(bot_response)
        if 20 <= response_len <= 500:
            quality += 1.5
        elif response_len > 1000:
            quality -= 0.5
        
        # Relevance check: overlapping words (+2.0)
        user_words = set(user_input.lower().split())
        response_words = set(bot_response.lower().split())
        overlap = len(user_words & response_words)
        if overlap >= 3:
            quality += 2.0
        elif overlap >= 1:
            quality += 1.0
        
        # Not too short (+1.0)
        if len(bot_response) > 30:
            quality += 1.0
        
        # Context awareness (+0.5)
        if context:
            quality += 0.5
        
        return min(10.0, max(0.0, quality))
    
    def shutdown(self):
        """
        Clean shutdown of all systems
        """
        try:
            self.emotional_memory.save()
            self.relationship_model.save()
            self.learning_system.save()
            self.goal_system.save()
            logger.info("Seven v2.0 Sentience Core shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


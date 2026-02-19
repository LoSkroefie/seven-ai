"""
Emotional Continuity - Track and recall emotional memories
"""
from datetime import datetime
from typing import Optional, List, Dict
import random
import json
import config

class EmotionalContinuity:
    """Manages emotional memory recall and continuity"""
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.recent_emotions = []
        self.emotional_triggers = {}
        self.load_emotional_state()  # Load persisted state
    
    def save_emotional_state(self):
        """Persist emotional state to disk"""
        state_file = config.DATA_DIR / "emotional_state.json"
        try:
            state = {
                'recent_emotions': self.recent_emotions[-10:],  # Last 10
                'emotional_triggers': self.emotional_triggers,
                'saved_at': datetime.now().isoformat()
            }
            state_file.write_text(json.dumps(state, default=str, indent=2))
        except Exception as e:
            pass  # Silent fail - not critical
    
    def load_emotional_state(self):
        """Load emotional state from disk"""
        state_file = config.DATA_DIR / "emotional_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                self.recent_emotions = state.get('recent_emotions', [])
                self.emotional_triggers = state.get('emotional_triggers', {})
            except:
                pass  # Use defaults if load fails
    
    def trigger_emotional_memory(self, current_topic: str, current_emotion: str) -> Optional[str]:
        """
        Check if current context triggers an emotional memory
        
        Args:
            current_topic: Current conversation topic/keywords
            current_emotion: Current emotional state
            
        Returns:
            Emotional memory reference or None
        """
        if not config.ENABLE_EMOTIONAL_RECALL:
            return None
        
        # Get emotional memories from database
        emotional_memories = self._get_emotional_memories(current_topic)
        
        if emotional_memories:
            memory = random.choice(emotional_memories)
            return self._format_emotional_recall(memory, current_emotion)
        
        return None
    
    def _get_emotional_memories(self, topic_keywords: str) -> List[Dict]:
        """Retrieve emotional memories related to topic"""
        try:
            conn = self.memory._get_connection()
            cursor = conn.cursor()
            
            # Check if emotional_memory table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='emotional_memory'
            """)
            
            if not cursor.fetchone():
                conn.close()
                return []
            
            # Simple keyword matching (could be enhanced with vector search)
            cursor.execute("""
                SELECT conversation_snippet, emotion_felt, emotional_intensity, timestamp
                FROM emotional_memory
                WHERE conversation_snippet LIKE ?
                ORDER BY emotional_intensity DESC
                LIMIT 5
            """, (f'%{topic_keywords[:20]}%',))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'snippet': row[0],
                    'emotion': row[1],
                    'intensity': row[2],
                    'timestamp': row[3]
                }
                for row in results
            ]
            
        except Exception:
            return []
    
    def _format_emotional_recall(self, memory: Dict, current_emotion: str) -> str:
        """Format emotional memory into natural language"""
        past_emotion = memory['emotion']
        
        # Different phrasings based on emotion match
        if past_emotion == current_emotion:
            return f"This feels familiar... I had a similar {past_emotion} feeling when we discussed this before."
        else:
            return f"This reminds me of a past conversation. I felt {past_emotion} then, though I feel {current_emotion} now."
    
    def detect_emotional_contagion(self, user_input: str) -> Optional[str]:
        """
        Detect user's emotional state and suggest mirroring
        
        Args:
            user_input: User's message
            
        Returns:
            Suggested emotion to mirror or None
        """
        if not config.ENABLE_EMOTIONAL_CONTAGION:
            return None
        
        user_lower = user_input.lower()
        
        # Positive emotions
        if any(word in user_lower for word in ['excited', 'amazing', 'awesome', 'great', 'wonderful', 'happy', '!!']):
            return 'excited'
        
        # Negative emotions
        if any(word in user_lower for word in ['sad', 'upset', 'frustrated', 'angry', 'disappointed']):
            return 'empathetic'
        
        # Curious/questioning
        if any(word in user_lower for word in ['why', 'how', 'what', 'curious', 'wonder', 'interesting']):
            return 'curious'
        
        # Thoughtful/serious
        if any(word in user_lower for word in ['think', 'believe', 'consider', 'important', 'serious']):
            return 'thoughtful'
        
        return None
    
    def track_emotional_arc(self, emotion: str):
        """Track emotional changes over conversation"""
        self.recent_emotions.append({
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 20 emotions
        if len(self.recent_emotions) > 20:
            self.recent_emotions = self.recent_emotions[-20:]
        
        # Periodically save state to disk (every 5 emotions)
        if len(self.recent_emotions) % 5 == 0:
            self.save_emotional_state()
    
    def get_emotional_summary(self) -> str:
        """Get summary of emotional journey in conversation"""
        if not self.recent_emotions:
            return "relatively neutral"
        
        # Count emotion frequencies
        emotion_counts = {}
        for e in self.recent_emotions:
            emotion = e['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Most common emotion
        most_common = max(emotion_counts, key=emotion_counts.get)
        
        # Detect emotional shifts
        if len(self.recent_emotions) >= 3:
            recent_3 = [e['emotion'] for e in self.recent_emotions[-3:]]
            if len(set(recent_3)) == 3:
                return "emotionally dynamic - shifting between different states"
        
        return f"mostly {most_common}"

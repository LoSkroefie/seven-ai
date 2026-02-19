"""
Session Continuity Manager - Remember context between sessions
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import config

class SessionManager:
    """Manages session continuity and cross-session memory"""
    
    def __init__(self, memory_manager, ollama=None):
        self.memory = memory_manager
        self.ollama = ollama
        self.current_session_id = None
        self.last_session_summary = None
        self.session_start_time = None
    
    def start_new_session(self) -> Optional[str]:
        """
        Start new session and load previous session context
        Returns greeting that references previous session
        """
        if not config.ENABLE_SESSION_CONTINUITY:
            return None
        
        self.session_start_time = datetime.now()
        self.current_session_id = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        
        # Load previous session
        previous_session = self._get_last_session_summary()
        
        if previous_session:
            time_since = self._time_since_last_session()
            greeting = self._generate_continuity_greeting(previous_session, time_since)
            return greeting
        
        return None
    
    def _get_last_session_summary(self) -> Optional[Dict]:
        """Get summary of last session from memory"""
        try:
            # Get last 3 conversations from previous session
            recent = self.memory.get_recent_conversations(limit=5)
            
            if not recent:
                return None
            
            # Extract topics and emotional tone
            topics = []
            last_emotion = None
            last_timestamp = None
            
            for conv in recent:
                if len(conv) >= 2:
                    user_input = conv[1]
                    # Simple topic extraction (first few meaningful words)
                    words = user_input.lower().split()
                    content_words = [w for w in words if len(w) > 3 and w not in ['what', 'that', 'this', 'with', 'have', 'been']]
                    if content_words:
                        topics.extend(content_words[:2])
                
                if len(conv) >= 4:
                    last_emotion = conv[3]
                if len(conv) >= 1:
                    last_timestamp = conv[0]
            
            if topics:
                # Get most common topics
                unique_topics = list(set(topics))[:3]
                
                return {
                    'topics': unique_topics,
                    'emotion': last_emotion or 'neutral',
                    'timestamp': last_timestamp,
                    'conversation_count': len(recent)
                }
            
        except Exception as e:
            pass
        
        return None
    
    def _time_since_last_session(self) -> str:
        """Calculate human-readable time since last session"""
        previous = self._get_last_session_summary()
        if not previous or not previous.get('timestamp'):
            return "a while"
        
        try:
            last_time = datetime.fromisoformat(previous['timestamp'])
            delta = datetime.now() - last_time
            
            if delta.days > 7:
                return f"{delta.days // 7} week{'s' if delta.days // 7 > 1 else ''}"
            elif delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''}"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''}"
        except:
            return "a while"
    
    def _generate_continuity_greeting(self, previous: Dict, time_since: str) -> str:
        """Generate a greeting that references previous session using LLM"""
        topics = previous.get('topics', [])
        emotion = previous.get('emotion', 'neutral')
        
        # Try LLM first for a natural, contextual greeting
        if self.ollama:
            try:
                topic_str = ', '.join(topics[:3]) if topics else 'general conversation'
                result = self.ollama.generate(
                    prompt=(
                        f"I'm greeting my user after {time_since} apart. "
                        f"Last time we talked about: {topic_str}. "
                        f"The emotional tone was: {emotion}. "
                        f"Generate a warm, natural greeting that references our history."
                    ),
                    system_message=(
                        "You are Seven, an AI companion. Generate a brief, warm "
                        "greeting (1-2 sentences) that naturally references the previous "
                        "session. Be genuine, not formulaic."
                    ),
                    temperature=0.8,
                    max_tokens=60,
                    timeout=10
                )
                if result and len(result.strip()) > 5:
                    return result.strip()
            except Exception:
                pass
        
        # Fallback templates
        if 'week' in time_since or 'day' in time_since and int(time_since.split()[0]) > 3:
            if topics:
                topic_ref = topics[0] if len(topics) > 0 else "things"
                return f"It's been {time_since}! Last time we talked about {topic_ref}. How have you been?"
            else:
                return f"Welcome back! It's been {time_since}. I've been thinking about our last conversation."
        elif 'hour' in time_since:
            if topics:
                return f"Back already! We were discussing {topics[0]} earlier. Want to continue?"
            else:
                return f"Good to see you again. I've been processing our last chat."
        else:
            if emotion in ['happy', 'excited']:
                return "That was quick! Still in a good mood I hope?"
            else:
                return "Welcome back. Where were we?"
    
    def mark_conversation_anchor(self, user_input: str, bot_response: str, anchor_type: str = "significant"):
        """
        Mark a conversation as an anchor (memorable moment)
        
        Args:
            user_input: What user said
            bot_response: What bot said
            anchor_type: Type of anchor ('first', 'revelation', 'emotional_peak', 'significant')
        """
        if not config.ENABLE_CONVERSATIONAL_ANCHORS:
            return
        
        try:
            conn = self.memory._get_connection()
            cursor = conn.cursor()
            
            # Create table if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_anchors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    anchor_type TEXT,
                    conversation_snippet TEXT,
                    significance_score REAL
                )
            """)
            
            # Store anchor
            snippet = f"User: {user_input[:100]}... Bot: {bot_response[:100]}"
            
            cursor.execute("""
                INSERT INTO conversation_anchors 
                (session_id, anchor_type, conversation_snippet, significance_score)
                VALUES (?, ?, ?, ?)
            """, (self.current_session_id, anchor_type, snippet, 1.0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            pass
    
    def get_memorable_moments(self, limit: int = 5) -> List[Dict]:
        """Retrieve memorable conversation anchors"""
        if not config.ENABLE_CONVERSATIONAL_ANCHORS:
            return []
        
        try:
            conn = self.memory._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, anchor_type, conversation_snippet, significance_score
                FROM conversation_anchors
                ORDER BY significance_score DESC, timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'timestamp': row[0],
                    'type': row[1],
                    'snippet': row[2],
                    'score': row[3]
                }
                for row in results
            ]
            
        except Exception:
            return []
    
    def should_reference_past_anchor(self) -> Optional[str]:
        """Occasionally reference a past memorable moment using LLM"""
        if not config.ENABLE_CONVERSATIONAL_ANCHORS:
            return None
        
        import random
        if random.random() < 0.1:  # 10% chance
            anchors = self.get_memorable_moments(limit=3)
            if anchors:
                anchor = random.choice(anchors)
                snippet = anchor['snippet']
                # Try LLM for natural reference
                if self.ollama:
                    try:
                        result = self.ollama.generate(
                            prompt=f"I want to naturally reference a past memorable moment: {snippet[:80]}. Generate a brief, nostalgic callback.",
                            system_message="You are Seven. Generate a brief first-person callback to a past conversation moment (1 sentence). Be warm and natural.",
                            temperature=0.8,
                            max_tokens=40,
                            timeout=10
                        )
                        if result and len(result.strip()) > 5:
                            return result.strip()
                    except Exception:
                        pass
                return f"This reminds me of when {snippet[:50]}..."
        
        return None

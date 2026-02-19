"""
Context Cascade System - Maintains cascading context across conversation turns

This module enables Seven to maintain state and momentum across conversation turns,
creating natural flow where each exchange influences the next.
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
from collections import deque
import json
import config

class ContextCascade:
    """
    Maintains cascading context across conversation turns.
    
    Features:
    - Emotional momentum (recent emotions influence future moods)
    - Topic threading (conversation flow tracking)
    - Relationship context (how user relationship affects responses)
    - Knowledge activation (recently accessed knowledge stays "hot")
    """
    
    def __init__(self):
        self.emotional_momentum = deque(maxlen=5)  # Last 5 emotions with decay
        self.topic_thread = deque(maxlen=10)  # Current conversation thread
        self.relationship_context = {
            'rapport_level': 0.5,  # 0.0 to 1.0
            'trust_score': 0.5,
            'familiarity': 0.5
        }
        self.knowledge_activated = set()  # Recently accessed knowledge nodes
        self.conversation_momentum = 0.0  # Overall energy level
        
        # Load previous state if it exists
        self._load_from_disk()
        
    def process_turn(self, user_input: str, bot_response: str, emotion: str):
        """
        Update cascade with new conversation turn
        
        Args:
            user_input: What user said
            bot_response: What bot responded
            emotion: Current emotional state
        """
        # Update emotional momentum
        intensity = self._calculate_intensity(user_input, bot_response)
        self.emotional_momentum.append({
            'emotion': emotion,
            'intensity': intensity,
            'decay': 1.0,  # Fresh momentum, will decay
            'timestamp': datetime.now().isoformat()  # Fixed: isoformat for JSON serialization
        })
        
        # Decay older emotions
        for e in self.emotional_momentum:
            e['decay'] *= 0.7  # 30% decay per turn
        
        # Update topic threading
        topics = self._extract_topics(user_input)
        for topic in topics:
            self.topic_thread.append({
                'topic': topic,
                'turns_ago': 0,
                'mentioned_count': sum(1 for t in self.topic_thread if t['topic'] == topic) + 1
            })
        
        # Age existing topics
        for topic_entry in self.topic_thread:
            topic_entry['turns_ago'] += 1
        
        # Update conversation momentum
        self._update_momentum(intensity)
        
        # Update relationship context
        self._update_relationship(user_input, bot_response)
    
    def get_influenced_emotion(self, current_emotion: str) -> str:
        """
        Get emotion influenced by emotional momentum
        
        Args:
            current_emotion: Detected emotion from current turn
            
        Returns:
            Emotion adjusted for momentum
        """
        if not self.emotional_momentum:
            return current_emotion
        
        # Get recent emotions with strong momentum
        recent = [e for e in self.emotional_momentum if e['decay'] > 0.3]
        
        if not recent:
            return current_emotion
        
        # Check for persistent sadness/melancholy
        sad_emotions = ['sadness', 'melancholy', 'thoughtful']
        sad_count = sum(1 for e in recent if any(sad in e['emotion'].lower() for sad in ['sad', 'melancholy']))
        
        if sad_count >= 2:
            # Multiple sad turns create lingering effect
            if 'joy' in current_emotion.lower() or 'excited' in current_emotion.lower():
                return 'thoughtful'  # Dampen joy after sadness
            return 'contemplative'  # Maintain contemplative mood
        
        # Check for persistent excitement/energy
        excited_count = sum(1 for e in recent if any(exc in e['emotion'].lower() for exc in ['excited', 'joy', 'happy']))
        
        if excited_count >= 2:
            # Multiple excited turns create energetic momentum
            if 'calm' in current_emotion.lower():
                return 'content'  # Maintain positive but not drop to calm
        
        return current_emotion
    
    def should_reference_past(self) -> Optional[str]:
        """
        Decide if bot should reference earlier conversation topics
        
        Returns:
            Reference string or None
        """
        if len(self.topic_thread) < 5:
            return None
        
        # Get topics from early in conversation
        early_topics = [t for t in self.topic_thread if t['turns_ago'] >= 3 and t['turns_ago'] <= 7]
        
        # Get recent topics
        recent_topics = [t for t in self.topic_thread if t['turns_ago'] <= 2]
        
        if not early_topics or not recent_topics:
            return None
        
        # Check for topic overlap
        early_set = {t['topic'] for t in early_topics}
        recent_set = {t['topic'] for t in recent_topics}
        overlap = early_set & recent_set
        
        if overlap:
            topic = list(overlap)[0]
            return f"We keep coming back to {topic}"
        
        # Check for related topics (simple heuristic)
        for early in early_topics:
            for recent in recent_topics:
                if self._topics_related(early['topic'], recent['topic']):
                    return f"This connects to what you mentioned about {early['topic']}"
        
        return None
    
    def get_relationship_modifier(self) -> Dict[str, float]:
        """
        Get relationship modifiers that should affect bot's behavior
        
        Returns:
            Dictionary of modifiers
        """
        return {
            'formality': 1.0 - self.relationship_context['familiarity'],  # More familiar = less formal
            'verbosity': 0.8 + (self.relationship_context['rapport_level'] * 0.4),  # Better rapport = more verbose
            'proactivity': self.relationship_context['trust_score'],  # More trust = more proactive
            'emotional_openness': self.relationship_context['familiarity']  # More familiar = more open
        }
    
    def get_context_summary(self) -> str:
        """
        Generate summary of current context for LLM
        
        Returns:
            Formatted context string
        """
        lines = []
        
        # Emotional momentum
        if self.emotional_momentum:
            recent_emotions = [e['emotion'] for e in self.emotional_momentum if e['decay'] > 0.4]
            if recent_emotions:
                lines.append(f"Recent emotional momentum: {', '.join(recent_emotions)}")
        
        # Topic thread
        if self.topic_thread:
            recent_topics = [t['topic'] for t in self.topic_thread if t['turns_ago'] <= 3]
            if recent_topics:
                lines.append(f"Current conversation thread: {', '.join(recent_topics[:3])}")
        
        # Relationship
        rapport = self.relationship_context['rapport_level']
        if rapport > 0.7:
            lines.append("Relationship: Strong rapport, comfortable conversation")
        elif rapport < 0.3:
            lines.append("Relationship: Building rapport, being careful")
        
        # Momentum
        if self.conversation_momentum > 0.7:
            lines.append("Conversation energy: High momentum, engaged discussion")
        elif self.conversation_momentum < 0.3:
            lines.append("Conversation energy: Low momentum, may need engagement")
        
        return "\n".join(lines) if lines else ""
    
    def reset_thread(self):
        """Reset topic thread (for major topic changes)"""
        self.topic_thread.clear()
    
    def boost_rapport(self, amount: float = 0.1):
        """Increase rapport level"""
        self.relationship_context['rapport_level'] = min(1.0, self.relationship_context['rapport_level'] + amount)
        self.relationship_context['trust_score'] = min(1.0, self.relationship_context['trust_score'] + amount * 0.5)
    
    def _calculate_intensity(self, user_input: str, bot_response: str) -> float:
        """Calculate emotional intensity of exchange"""
        intensity = 0.5
        
        # Length suggests depth
        if len(user_input) > 100:
            intensity += 0.2
        if len(bot_response) > 150:
            intensity += 0.1
        
        # Exclamation marks suggest intensity
        intensity += min(0.2, user_input.count('!') * 0.05)
        
        # Question marks suggest engagement
        intensity += min(0.1, user_input.count('?') * 0.03)
        
        # All caps (shouting/excitement)
        if any(word.isupper() and len(word) > 2 for word in user_input.split()):
            intensity += 0.2
        
        return min(1.0, intensity)
    
    def _extract_topics(self, text: str) -> List[str]:
        """
        Extract key topics from text
        
        Simple extraction: meaningful words >4 chars
        """
        words = text.lower().split()
        
        # Filter stopwords and short words
        stopwords = {'that', 'this', 'what', 'with', 'have', 'been', 'will', 'would', 
                    'could', 'should', 'their', 'there', 'these', 'those', 'from', 'into'}
        
        topics = [
            word.strip('.,!?;:')
            for word in words
            if len(word) > 4 and word.lower() not in stopwords
        ]
        
        return topics[:5]  # Max 5 topics per turn
    
    def _update_momentum(self, intensity: float):
        """Update conversation momentum based on intensity"""
        # Momentum gradually increases with intense exchanges
        self.conversation_momentum = (self.conversation_momentum * 0.8) + (intensity * 0.2)
        
        # Decay momentum over time
        self.conversation_momentum *= 0.95
        
        # Keep in bounds
        self.conversation_momentum = max(0.0, min(1.0, self.conversation_momentum))
    
    def _update_relationship(self, user_input: str, bot_response: str):
        """Update relationship context based on interaction"""
        # Positive words increase rapport
        positive_words = ['thank', 'great', 'awesome', 'love', 'appreciate', 'perfect']
        if any(word in user_input.lower() for word in positive_words):
            self.boost_rapport(0.05)
        
        # Long exchanges increase familiarity
        if len(user_input) > 50:
            self.relationship_context['familiarity'] = min(1.0, self.relationship_context['familiarity'] + 0.02)
        
        # Questions increase trust (user is engaging)
        if '?' in user_input:
            self.relationship_context['trust_score'] = min(1.0, self.relationship_context['trust_score'] + 0.03)
    
    def _topics_related(self, topic1: str, topic2: str) -> bool:
        """Check if two topics are related (simple heuristic)"""
        # Share significant substring
        if len(topic1) >= 4 and len(topic2) >= 4:
            for i in range(len(topic1) - 3):
                substr = topic1[i:i+4]
                if substr in topic2:
                    return True
        
        return False
    
    def save_state(self) -> Dict:
        """Save cascade state for persistence"""
        return {
            'emotional_momentum': list(self.emotional_momentum),
            'topic_thread': list(self.topic_thread),
            'relationship_context': self.relationship_context,
            'conversation_momentum': self.conversation_momentum,
            'saved_at': datetime.now().isoformat()
        }
    
    def load_state(self, state: Dict):
        """Load cascade state from saved data"""
        self.emotional_momentum = deque(state.get('emotional_momentum', []), maxlen=5)
        self.topic_thread = deque(state.get('topic_thread', []), maxlen=10)
        self.relationship_context = state.get('relationship_context', {
            'rapport_level': 0.5,
            'trust_score': 0.5,
            'familiarity': 0.5
        })
        self.conversation_momentum = state.get('conversation_momentum', 0.0)
    
    def _save_to_disk(self):
        """Persist cascade state to disk"""
        save_path = config.DATA_DIR / "context_cascade.json"
        try:
            state = self.save_state()
            save_path.write_text(json.dumps(state, indent=2))
        except Exception as e:
            pass  # Silent fail - not critical
    
    def _load_from_disk(self):
        """Load cascade state from disk"""
        load_path = config.DATA_DIR / "context_cascade.json"
        if load_path.exists():
            try:
                state = json.loads(load_path.read_text())
                self.load_state(state)
            except Exception:
                pass  # Use defaults if load fails


# Example usage
if __name__ == "__main__":
    # Test context cascade
    cascade = ContextCascade()
    
    # Simulate conversation
    cascade.process_turn("I love Python programming!", "That's great! Python is versatile.", "joy")
    print(f"Emotion: joy -> Influenced: {cascade.get_influenced_emotion('calmness')}")
    
    cascade.process_turn("It's so powerful for data analysis", "Indeed! Have you tried pandas?", "excitement")
    print(f"Emotion: excitement -> Influenced: {cascade.get_influenced_emotion('calmness')}")
    
    cascade.process_turn("Yes, I use pandas daily", "Excellent! What are you building?", "engaged")
    print(f"\nContext Summary:\n{cascade.get_context_summary()}")
    
    # Check for references
    cascade.process_turn("Also learning JavaScript now", "Nice! Different paradigm.", "curious")
    callback = cascade.should_reference_past()
    print(f"\nShould reference past? {callback}")

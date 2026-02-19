"""
SEVEN AI - ENHANCED CONVERSATION ANALYZER
Real-time conversation analysis with insights

Features:
- Sentiment tracking
- Topic detection
- Conversation patterns
- User interest profiling
- Engagement metrics
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from collections import Counter, defaultdict

class ConversationAnalyzer:
    """
    Analyzes conversations for patterns, sentiment, and insights
    Helps Seven understand conversation dynamics better
    """
    
    def __init__(self):
        self.conversation_history = []
        self.topics = Counter()
        self.sentiment_history = []
        self.user_interests = defaultdict(int)
        self.conversation_patterns = {
            'avg_user_message_length': 0,
            'avg_bot_message_length': 0,
            'question_count': 0,
            'exclamation_count': 0,
            'total_turns': 0,
        }
        
        # Emotion keywords for sentiment
        self.positive_words = set([
            'good', 'great', 'awesome', 'excellent', 'love', 'like',
            'happy', 'joy', 'wonderful', 'fantastic', 'perfect', 'nice',
            'thanks', 'thank', 'appreciate', 'amazing', 'brilliant'
        ])
        
        self.negative_words = set([
            'bad', 'terrible', 'awful', 'hate', 'dislike', 'sad',
            'angry', 'frustrated', 'annoying', 'horrible', 'worst',
            'disappointed', 'upset', 'mad', 'poor', 'wrong'
        ])
        
        # Technical topics
        self.topics_keywords = {
            'programming': ['code', 'python', 'javascript', 'programming', 'function', 'debug', 'api'],
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'neural', 'model', 'llm'],
            'personal': ['i feel', 'my life', 'my job', 'my family', 'personal', 'myself'],
            'work': ['work', 'job', 'project', 'deadline', 'meeting', 'colleague', 'boss'],
            'creative': ['write', 'story', 'art', 'music', 'create', 'design', 'creative'],
            'health': ['health', 'exercise', 'diet', 'sleep', 'tired', 'energy', 'stress'],
            'learning': ['learn', 'study', 'understand', 'tutorial', 'course', 'teach'],
        }
        
    def analyze_message(self, message: str, speaker: str) -> Dict:
        """Analyze a single message"""
        message_lower = message.lower()
        
        analysis = {
            'timestamp': datetime.now(),
            'speaker': speaker,
            'message': message,
            'length': len(message),
            'word_count': len(message.split()),
            'sentiment': self._analyze_sentiment(message_lower),
            'topics': self._detect_topics(message_lower),
            'has_question': '?' in message,
            'has_exclamation': '!' in message,
            'enthusiasm_level': self._calculate_enthusiasm(message),
        }
        
        # Update patterns
        self.conversation_history.append(analysis)
        self.conversation_patterns['total_turns'] += 1
        
        if speaker == 'user':
            self.conversation_patterns['avg_user_message_length'] = (
                (self.conversation_patterns['avg_user_message_length'] * 
                 (self.conversation_patterns['total_turns'] - 1) + analysis['length']) /
                self.conversation_patterns['total_turns']
            )
            
            if analysis['has_question']:
                self.conversation_patterns['question_count'] += 1
                
        if analysis['has_exclamation']:
            self.conversation_patterns['exclamation_count'] += 1
            
        # Track topics
        for topic in analysis['topics']:
            self.topics[topic] += 1
            if speaker == 'user':
                self.user_interests[topic] += 2  # Weight user topics more
                
        # Track sentiment
        self.sentiment_history.append(analysis['sentiment'])
        
        return analysis
        
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment (-1 to 1)"""
        words = text.split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
            
        return (positive_count - negative_count) / total
        
    def _detect_topics(self, text: str) -> List[str]:
        """Detect topics in text"""
        detected = []
        
        for topic, keywords in self.topics_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected.append(topic)
                
        return detected
        
    def _calculate_enthusiasm(self, text: str) -> float:
        """Calculate enthusiasm level (0 to 1)"""
        score = 0.0
        
        # Exclamation marks
        score += text.count('!') * 0.2
        
        # ALL CAPS words
        words = text.split()
        caps_words = sum(1 for word in words if word.isupper() and len(word) > 2)
        score += caps_words * 0.15
        
        # Positive words
        words_lower = [w.lower() for w in words]
        positive = sum(1 for word in words_lower if word in self.positive_words)
        score += positive * 0.1
        
        return min(1.0, score)
        
    def get_conversation_summary(self) -> Dict:
        """Get summary of entire conversation"""
        if not self.conversation_history:
            return {'status': 'no_data'}
            
        recent = self.conversation_history[-20:]  # Last 20 messages
        
        return {
            'total_messages': len(self.conversation_history),
            'total_turns': self.conversation_patterns['total_turns'],
            'avg_sentiment': sum(self.sentiment_history[-20:]) / len(self.sentiment_history[-20:]) if self.sentiment_history else 0,
            'current_mood': self._get_mood_label(self.sentiment_history[-5:] if len(self.sentiment_history) >= 5 else self.sentiment_history),
            'top_topics': self.topics.most_common(5),
            'user_interests': dict(sorted(self.user_interests.items(), key=lambda x: x[1], reverse=True)[:5]),
            'question_rate': self.conversation_patterns['question_count'] / max(1, self.conversation_patterns['total_turns']),
            'enthusiasm_avg': sum(m['enthusiasm_level'] for m in recent) / len(recent),
            'engagement_score': self._calculate_engagement(),
        }
        
    def _get_mood_label(self, sentiments: List[float]) -> str:
        """Get mood label from sentiments"""
        if not sentiments:
            return "neutral"
            
        avg = sum(sentiments) / len(sentiments)
        
        if avg > 0.5:
            return "very positive"
        elif avg > 0.2:
            return "positive"
        elif avg > -0.2:
            return "neutral"
        elif avg > -0.5:
            return "negative"
        else:
            return "very negative"
            
    def _calculate_engagement(self) -> float:
        """Calculate overall engagement score (0 to 1)"""
        if not self.conversation_history:
            return 0.0
            
        score = 0.0
        
        # Message frequency (more messages = more engaged)
        if len(self.conversation_history) > 10:
            score += 0.3
        elif len(self.conversation_history) > 5:
            score += 0.2
            
        # Question asking (curiosity)
        question_rate = self.conversation_patterns['question_count'] / max(1, self.conversation_patterns['total_turns'])
        score += min(0.3, question_rate)
        
        # Sentiment (positive = more engaged)
        avg_sentiment = sum(self.sentiment_history[-10:]) / len(self.sentiment_history[-10:]) if self.sentiment_history else 0
        if avg_sentiment > 0:
            score += avg_sentiment * 0.2
            
        # Message length (thoughtful responses)
        if self.conversation_patterns['avg_user_message_length'] > 50:
            score += 0.2
            
        return min(1.0, score)
        
    def get_insights(self) -> List[str]:
        """Get actionable insights about the conversation"""
        insights = []
        summary = self.get_conversation_summary()
        
        if summary.get('status') == 'no_data':
            return ["Not enough conversation data yet"]
            
        # Sentiment insights
        mood = summary['current_mood']
        if 'positive' in mood:
            insights.append(f"User seems {mood} - great engagement!")
        elif 'negative' in mood:
            insights.append(f"User mood is {mood} - be supportive and empathetic")
            
        # Topic insights
        if summary['top_topics']:
            top_topic = summary['top_topics'][0][0]
            insights.append(f"Main interest: {top_topic} - focus there")
            
        # Engagement insights
        engagement = summary['engagement_score']
        if engagement > 0.7:
            insights.append("High engagement - user is very interested")
        elif engagement < 0.3:
            insights.append("Low engagement - try asking questions or changing topic")
            
        # Question insights
        if summary['question_rate'] > 0.5:
            insights.append("User asking many questions - they're curious and engaged")
        elif summary['question_rate'] < 0.1:
            insights.append("Few questions from user - try being more proactive")
            
        # Enthusiasm insights
        if summary['enthusiasm_avg'] > 0.5:
            insights.append("User is enthusiastic - match their energy!")
            
        return insights
        
    def suggest_response_style(self) -> Dict:
        """Suggest how Seven should respond"""
        summary = self.get_conversation_summary()
        
        if summary.get('status') == 'no_data':
            return {'style': 'neutral', 'energy': 'medium'}
            
        style = {
            'tone': 'neutral',
            'energy': 'medium',
            'detail_level': 'medium',
            'formality': 'casual',
        }
        
        # Adjust based on mood
        mood = summary['current_mood']
        if 'positive' in mood:
            style['tone'] = 'warm'
            style['energy'] = 'high'
        elif 'negative' in mood:
            style['tone'] = 'supportive'
            style['energy'] = 'calm'
            
        # Adjust based on topics
        if summary['user_interests']:
            top_interest = list(summary['user_interests'].keys())[0]
            if top_interest in ['programming', 'ai']:
                style['detail_level'] = 'high'
                style['formality'] = 'professional'
            elif top_interest in ['personal', 'health']:
                style['tone'] = 'empathetic'
                style['formality'] = 'casual'
                
        # Adjust based on enthusiasm
        if summary['enthusiasm_avg'] > 0.5:
            style['energy'] = 'high'
        elif summary['enthusiasm_avg'] < 0.2:
            style['energy'] = 'calm'
            
        return style

# Global instance
conversation_analyzer = ConversationAnalyzer()

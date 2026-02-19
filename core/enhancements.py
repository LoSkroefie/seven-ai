"""
SEVEN ENHANCEMENT MODULE - New Advanced Features
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

class ConversationInsights:
    """
    Analyzes conversations to extract patterns and insights
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_conversation_patterns(self) -> Dict[str, Any]:
        """Extract conversation patterns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Time patterns
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM conversations
                GROUP BY hour
                ORDER BY count DESC
            """)
            time_patterns = cursor.fetchall()
            
            # Topic frequency
            cursor.execute("""
                SELECT content FROM conversations
                WHERE role = 'user'
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            conversations = cursor.fetchall()
            
            # Extract common words (basic topic analysis)
            word_freq = {}
            for conv in conversations:
                words = conv[0].lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            top_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            conn.close()
            
            return {
                'most_active_hour': time_patterns[0][0] if time_patterns else 'N/A',
                'top_topics': [t[0] for t in top_topics],
                'total_conversations': len(conversations)
            }
        except Exception as e:
            return {'error': str(e)}

class LearningTracker:
    """
    Tracks what Seven learns from conversations
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.learning_file = data_dir / "learnings.json"
        self.learnings = self._load_learnings()
        
    def _load_learnings(self) -> List[Dict]:
        """Load saved learnings"""
        if self.learning_file.exists():
            with open(self.learning_file, 'r') as f:
                return json.load(f)
        return []
        
    def add_learning(self, category: str, content: str, confidence: float = 1.0):
        """Add new learning"""
        learning = {
            'category': category,
            'content': content,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'reinforcements': 1
        }
        self.learnings.append(learning)
        self._save_learnings()
        
    def reinforce_learning(self, content: str):
        """Reinforce existing learning"""
        for learning in self.learnings:
            if learning['content'].lower() == content.lower():
                learning['reinforcements'] += 1
                learning['confidence'] = min(1.0, learning['confidence'] + 0.1)
                self._save_learnings()
                return True
        return False
        
    def get_recent_learnings(self, limit: int = 20) -> List[Dict]:
        """Get recent learnings"""
        return sorted(self.learnings, 
                     key=lambda x: x['timestamp'], 
                     reverse=True)[:limit]
        
    def get_learnings_by_category(self, category: str) -> List[Dict]:
        """Get learnings in category"""
        return [l for l in self.learnings if l['category'] == category]
        
    def _save_learnings(self):
        """Save learnings to file"""
        with open(self.learning_file, 'w') as f:
            json.dump(self.learnings, f, indent=2)

class RelationshipTracker:
    """
    Tracks relationship metrics with user
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.relationship_file = data_dir / "relationship.json"
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load relationship data"""
        if self.relationship_file.exists():
            with open(self.relationship_file, 'r') as f:
                return json.load(f)
        return {
            'trust_score': 50,
            'rapport': 50,
            'understanding': 50,
            'interactions': 0,
            'positive_interactions': 0,
            'negative_interactions': 0,
            'milestones': [],
            'first_interaction': datetime.now().isoformat(),
            'total_time_together': 0  # seconds
        }
        
    def record_interaction(self, positive: bool = True, intensity: float = 1.0):
        """Record an interaction"""
        self.data['interactions'] += 1
        
        if positive:
            self.data['positive_interactions'] += 1
            self.data['trust_score'] = min(100, self.data['trust_score'] + intensity)
            self.data['rapport'] = min(100, self.data['rapport'] + intensity * 0.5)
        else:
            self.data['negative_interactions'] += 1
            self.data['trust_score'] = max(0, self.data['trust_score'] - intensity * 2)
            
        self._check_milestones()
        self._save_data()
        
    def update_understanding(self, delta: float):
        """Update understanding level"""
        self.data['understanding'] = max(0, min(100, self.data['understanding'] + delta))
        self._save_data()
        
    def _check_milestones(self):
        """Check for relationship milestones"""
        interactions = self.data['interactions']
        milestones = []
        
        if interactions == 10:
            milestones.append("First 10 conversations")
        elif interactions == 50:
            milestones.append("50 conversations milestone")
        elif interactions == 100:
            milestones.append("100 conversations - Strong bond forming")
        elif interactions == 500:
            milestones.append("500 conversations - Deep relationship")
        elif interactions == 1000:
            milestones.append("1000 conversations - Inseparable companions")
            
        if self.data['trust_score'] >= 90 and "High trust achieved" not in self.data['milestones']:
            milestones.append("High trust achieved")
            
        if self.data['rapport'] >= 90 and "Strong rapport" not in self.data['milestones']:
            milestones.append("Strong rapport")
            
        for milestone in milestones:
            if milestone not in self.data['milestones']:
                self.data['milestones'].append({
                    'name': milestone,
                    'achieved': datetime.now().isoformat()
                })
                
    def get_relationship_summary(self) -> Dict:
        """Get relationship summary"""
        days_together = (datetime.now() - datetime.fromisoformat(
            self.data['first_interaction'])).days
            
        return {
            'trust_score': self.data['trust_score'],
            'rapport': self.data['rapport'],
            'understanding': self.data['understanding'],
            'total_interactions': self.data['interactions'],
            'days_together': days_together,
            'positive_ratio': (self.data['positive_interactions'] / 
                             max(1, self.data['interactions'])) * 100,
            'milestones_achieved': len(self.data['milestones']),
            'latest_milestone': self.data['milestones'][-1] if self.data['milestones'] else None
        }
        
    def _save_data(self):
        """Save relationship data"""
        with open(self.relationship_file, 'w') as f:
            json.dump(self.data, f, indent=2)

class GoalManager:
    """
    Manages Seven's long-term goals and aspirations
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.goals_file = data_dir / "goals.json"
        self.goals = self._load_goals()
        
    def _load_goals(self) -> List[Dict]:
        """Load saved goals"""
        if self.goals_file.exists():
            with open(self.goals_file, 'r') as f:
                return json.load(f)
        return []
        
    def add_goal(self, title: str, description: str, category: str = 'learning',
                 priority: int = 1, deadline: Optional[str] = None):
        """Add new goal"""
        goal = {
            'id': len(self.goals) + 1,
            'title': title,
            'description': description,
            'category': category,  # learning, mastery, creativity, exploration
            'priority': priority,
            'status': 'active',
            'progress': 0.0,
            'created': datetime.now().isoformat(),
            'deadline': deadline,
            'milestones': [],
            'reflections': []
        }
        self.goals.append(goal)
        self._save_goals()
        return goal['id']
        
    def update_progress(self, goal_id: int, progress: float, note: str = ""):
        """Update goal progress"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['progress'] = min(1.0, max(0.0, progress))
                if note:
                    goal['reflections'].append({
                        'timestamp': datetime.now().isoformat(),
                        'note': note
                    })
                if goal['progress'] >= 1.0:
                    goal['status'] = 'completed'
                    goal['completed'] = datetime.now().isoformat()
                self._save_goals()
                return True
        return False
        
    def add_milestone(self, goal_id: int, milestone: str):
        """Add milestone to goal"""
        for goal in self.goals:
            if goal['id'] == goal_id:
                goal['milestones'].append({
                    'text': milestone,
                    'achieved': datetime.now().isoformat()
                })
                self._save_goals()
                return True
        return False
        
    def get_active_goals(self) -> List[Dict]:
        """Get all active goals"""
        return [g for g in self.goals if g['status'] == 'active']
        
    def get_goals_by_category(self, category: str) -> List[Dict]:
        """Get goals in category"""
        return [g for g in self.goals if g['category'] == category]
        
    def _save_goals(self):
        """Save goals to file"""
        with open(self.goals_file, 'w') as f:
            json.dump(self.goals, f, indent=2)

class EmotionJournal:
    """
    Tracks Seven's emotional journey over time
    """
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.journal_file = data_dir / "emotion_journal.json"
        self.entries = self._load_entries()
        
    def _load_entries(self) -> List[Dict]:
        """Load journal entries"""
        if self.journal_file.exists():
            with open(self.journal_file, 'r') as f:
                return json.load(f)
        return []
        
    def record_emotion(self, emotion: str, intensity: float, 
                      trigger: str = "", context: str = ""):
        """Record emotional moment"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion,
            'intensity': intensity,
            'trigger': trigger,
            'context': context
        }
        self.entries.append(entry)
        
        # Keep last 1000 entries
        if len(self.entries) > 1000:
            self.entries = self.entries[-1000:]
            
        self._save_entries()
        
    def get_emotional_timeline(self, hours: int = 24) -> List[Dict]:
        """Get emotional timeline for last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [e for e in self.entries 
                if datetime.fromisoformat(e['timestamp']) > cutoff]
        
    def get_emotion_frequency(self) -> Dict[str, int]:
        """Get frequency of each emotion"""
        freq = {}
        for entry in self.entries:
            emotion = entry['emotion']
            freq[emotion] = freq.get(emotion, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))
        
    def get_emotional_insights(self) -> Dict[str, Any]:
        """Get insights about emotional patterns"""
        if not self.entries:
            return {}
            
        # Most common emotion
        freq = self.get_emotion_frequency()
        most_common = max(freq.items(), key=lambda x: x[1])[0] if freq else "Unknown"
        
        # Average intensity
        avg_intensity = sum(e['intensity'] for e in self.entries) / len(self.entries)
        
        # Emotional volatility (std dev of intensity)
        intensities = [e['intensity'] for e in self.entries]
        mean = sum(intensities) / len(intensities)
        variance = sum((x - mean) ** 2 for x in intensities) / len(intensities)
        volatility = variance ** 0.5
        
        return {
            'most_common_emotion': most_common,
            'average_intensity': round(avg_intensity, 2),
            'emotional_volatility': round(volatility, 2),
            'total_emotional_moments': len(self.entries),
            'unique_emotions_experienced': len(freq)
        }
        
    def _save_entries(self):
        """Save journal to file"""
        with open(self.journal_file, 'w') as f:
            json.dump(self.entries, f, indent=2)

# Integration function
def initialize_enhancements(bot_instance):
    """Initialize all enhancement modules with bot"""
    data_dir = Path.home() / ".chatbot"
    
    bot_instance.conversation_insights = ConversationInsights(str(data_dir / "memory.db"))
    bot_instance.learning_tracker = LearningTracker(data_dir)
    bot_instance.relationship_tracker = RelationshipTracker(data_dir)
    bot_instance.goal_manager = GoalManager(data_dir)
    bot_instance.emotion_journal = EmotionJournal(data_dir)
    
    return bot_instance

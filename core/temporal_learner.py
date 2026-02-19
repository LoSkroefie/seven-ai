"""
Temporal Pattern Learner - Learn user activity patterns over time
"""
from datetime import datetime
from typing import Dict, Optional
import config

class TemporalLearner:
    """Learns when user is most active and adjusts behavior"""
    
    def __init__(self, memory_manager):
        self.memory = memory_manager
        self.activity_patterns = {}
        self._load_patterns()
    
    def _load_patterns(self):
        """Load activity patterns from database"""
        if not config.ENABLE_TEMPORAL_LEARNING:
            return
        
        try:
            conn = self.memory._get_connection()
            cursor = conn.cursor()
            
            # Create patterns table if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_patterns (
                    hour_of_day INTEGER,
                    day_of_week INTEGER,
                    interaction_count INTEGER DEFAULT 1,
                    avg_conversation_length REAL DEFAULT 1.0,
                    PRIMARY KEY (hour_of_day, day_of_week)
                )
            """)
            
            # Load existing patterns
            cursor.execute("""
                SELECT hour_of_day, day_of_week, interaction_count, avg_conversation_length
                FROM activity_patterns
            """)
            
            for row in cursor.fetchall():
                key = (row[0], row[1])
                self.activity_patterns[key] = {
                    'count': row[2],
                    'avg_length': row[3]
                }
            
            conn.commit()
            conn.close()
            
        except Exception:
            pass
    
    def record_interaction(self, conversation_length: int = 1):
        """Record an interaction at current time"""
        if not config.ENABLE_TEMPORAL_LEARNING:
            return
        
        now = datetime.now()
        hour = now.hour
        day = now.weekday()  # 0 = Monday
        
        try:
            conn = self.memory._get_connection()
            cursor = conn.cursor()
            
            # Update or insert pattern
            cursor.execute("""
                INSERT INTO activity_patterns (hour_of_day, day_of_week, interaction_count, avg_conversation_length)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(hour_of_day, day_of_week) DO UPDATE SET
                    interaction_count = interaction_count + 1,
                    avg_conversation_length = (avg_conversation_length + ?) / 2
            """, (hour, day, conversation_length, conversation_length))
            
            conn.commit()
            conn.close()
            
            # Update in-memory cache
            key = (hour, day)
            if key in self.activity_patterns:
                self.activity_patterns[key]['count'] += 1
                self.activity_patterns[key]['avg_length'] = (
                    self.activity_patterns[key]['avg_length'] + conversation_length
                ) / 2
            else:
                self.activity_patterns[key] = {
                    'count': 1,
                    'avg_length': conversation_length
                }
                
        except Exception:
            pass
    
    def get_temporal_insight(self) -> Optional[str]:
        """Generate insight about user's activity patterns"""
        if not config.ENABLE_TEMPORAL_LEARNING:
            return None
        
        if not self.activity_patterns:
            return None
        
        now = datetime.now()
        current_hour = now.hour
        current_day = now.weekday()
        
        # Find most active time
        most_active = max(self.activity_patterns.items(), key=lambda x: x[1]['count'])
        most_active_hour, most_active_day = most_active[0]
        most_active_count = most_active[1]['count']
        
        # Check if this is unusual time
        current_key = (current_hour, current_day)
        current_count = self.activity_patterns.get(current_key, {'count': 0})['count']
        
        if current_count < most_active_count / 3 and most_active_count > 5:
            # This is an unusual time
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            usual_day = day_names[most_active_day]
            
            time_str = self._hour_to_time_string(most_active_hour)
            
            return f"You usually talk to me around {time_str} on {usual_day}s. Everything okay?"
        
        return None
    
    def _hour_to_time_string(self, hour: int) -> str:
        """Convert hour to readable time"""
        if hour == 0:
            return "midnight"
        elif hour < 12:
            return f"{hour}am"
        elif hour == 12:
            return "noon"
        else:
            return f"{hour-12}pm"
    
    def should_adjust_proactivity(self) -> float:
        """
        Adjust proactive behavior based on typical activity
        
        Returns:
            Multiplier for proactive interval (>1 = less proactive, <1 = more proactive)
        """
        if not config.ENABLE_TEMPORAL_LEARNING:
            return 1.0
        
        now = datetime.now()
        key = (now.hour, now.weekday())
        
        if key not in self.activity_patterns:
            return 1.0
        
        # More active times = be more proactive
        count = self.activity_patterns[key]['count']
        
        if count > 10:
            return 0.7  # 30% more proactive
        elif count > 5:
            return 0.85  # 15% more proactive
        else:
            return 1.2  # 20% less proactive

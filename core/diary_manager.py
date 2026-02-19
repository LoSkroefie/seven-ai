"""
Personal Diary and Insights System
Analyzes conversation patterns and generates weekly insights
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import config

class DiaryManager:
    """Manages personal diary entries and generates insights"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize diary tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diary_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date DATE NOT NULL,
                    mood_summary TEXT,
                    activities TEXT,
                    insights TEXT,
                    conversation_count INTEGER DEFAULT 0,
                    dominant_emotion TEXT,
                    topics TEXT
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_diary_date 
                ON diary_entries(entry_date DESC)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_entry(self, entry_date: datetime, mood_summary: str, activities: str = "",
                  insights: str = "", conversation_count: int = 0, 
                  dominant_emotion: str = "", topics: str = "") -> int:
        """Add diary entry"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO diary_entries 
                (entry_date, mood_summary, activities, insights, conversation_count, 
                 dominant_emotion, topics)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (entry_date.date(), mood_summary, activities, insights, 
                  conversation_count, dominant_emotion, topics))
            
            entry_id = cursor.lastrowid
            conn.commit()
            return entry_id
        finally:
            conn.close()
    
    def get_week_summary(self, weeks_ago: int = 0) -> Optional[Dict]:
        """Get summary for a specific week"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday() + weeks_ago * 7)
            end_of_week = start_of_week + timedelta(days=6)
            
            cursor.execute("""
                SELECT * FROM diary_entries 
                WHERE entry_date BETWEEN ? AND ?
                ORDER BY entry_date ASC
            """, (start_of_week, end_of_week))
            
            entries = [dict(row) for row in cursor.fetchall()]
            
            if not entries:
                return None
            
            # Aggregate data
            total_conversations = sum(e['conversation_count'] for e in entries)
            emotions = [e['dominant_emotion'] for e in entries if e['dominant_emotion']]
            
            return {
                'start_date': start_of_week,
                'end_date': end_of_week,
                'entries': entries,
                'total_conversations': total_conversations,
                'dominant_emotions': emotions,
                'entry_count': len(entries)
            }
        finally:
            conn.close()
    
    def generate_weekly_insights(self, memory_manager=None, ollama_client=None) -> str:
        """Generate insights for the current week"""
        week_data = self.get_week_summary(weeks_ago=0)
        
        if not week_data or not ollama_client:
            return "Not enough data to generate insights yet."
        
        # Build summary from entries
        summary = f"Week of {week_data['start_date']} to {week_data['end_date']}:\n"
        summary += f"Total conversations: {week_data['total_conversations']}\n"
        
        for entry in week_data['entries']:
            summary += f"- {entry['entry_date']}: {entry['mood_summary']}\n"
        
        # Ask Ollama for insights
        prompt = f"""Based on this week's conversation data, provide 3-4 meaningful insights about the user's week:

{summary}

Focus on patterns, mood trends, and what stood out. Be empathetic and encouraging."""
        
        try:
            insights = ollama_client.generate(prompt, temperature=0.7)
            return insights if insights else "Unable to generate insights at this time."
        except:
            return "Unable to generate insights at this time."

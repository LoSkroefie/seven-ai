"""
SQLite-based memory system for conversation history
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from pathlib import Path
import config

class MemoryManager:
    """Manages bot memory using SQLite"""
    
    def __init__(self, db_path: Path = config.DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Session memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT,
                    bot_response TEXT,
                    emotion TEXT
                )
            """)
            
            # Persistent memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persistent_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    refined_data TEXT,
                    category TEXT
                )
            """)
            
            # Active instances table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_name TEXT UNIQUE,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_timestamp 
                ON session_memory(timestamp)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def save_conversation(self, user_input: str, bot_response: str, emotion: str = "neutral"):
        """Save a conversation turn to session memory with emotional context"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO session_memory (user_input, bot_response, emotion)
                VALUES (?, ?, ?)
            """, (user_input, bot_response, emotion))
            conn.commit()
            
            # Also save to emotional memory if enabled
            if config.ENABLE_EMOTIONAL_MEMORY:
                self._save_emotional_memory(user_input, bot_response, emotion, conn)
        finally:
            conn.close()
    
    def _save_emotional_memory(self, user_input: str, bot_response: str, emotion: str, conn):
        """Save conversation with emotional association"""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emotional_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    conversation_snippet TEXT,
                    emotion_felt TEXT,
                    emotional_intensity REAL
                )
            """)
            
            # Calculate emotional intensity (simple heuristic)
            intensity_map = {
                "anger": 0.8, "excitement": 0.9, "joy": 0.9,
                "sadness": 0.7, "calmness": 0.3, "confusion": 0.5
            }
            intensity = intensity_map.get(emotion, 0.5)
            
            snippet = f"{user_input[:100]}... -> {bot_response[:100]}"
            cursor.execute("""
                INSERT INTO emotional_memory (conversation_snippet, emotion_felt, emotional_intensity)
                VALUES (?, ?, ?)
            """, (snippet, emotion, intensity))
            
            conn.commit()
        except Exception as e:
            pass  # Silently fail if table already exists or other issues
    
    def get_recent_conversations(self, limit: int = 10) -> List[dict]:
        """Get recent conversation history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT timestamp, user_input, bot_response, emotion
                FROM session_memory
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def save_to_persistent(self, refined_data: str, category: str = "general"):
        """Save refined insights to persistent memory"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO persistent_memory (refined_data, category)
                VALUES (?, ?)
            """, (refined_data, category))
            conn.commit()
        finally:
            conn.close()
    
    def get_persistent_memory(self, category: Optional[str] = None, limit: int = 50) -> List[dict]:
        """Retrieve persistent memory"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if category:
                cursor.execute("""
                    SELECT timestamp, refined_data, category
                    FROM persistent_memory
                    WHERE category = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (category, limit))
            else:
                cursor.execute("""
                    SELECT timestamp, refined_data, category
                    FROM persistent_memory
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def clear_old_sessions(self, hours: int = 24):
        """Clear session memory older than specified hours"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                DELETE FROM session_memory
                WHERE timestamp < ?
            """, (cutoff,))
            conn.commit()
            deleted = cursor.rowcount
            return deleted
        finally:
            conn.close()
    
    def update_instance_status(self, instance_name: str):
        """Update instance heartbeat"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO active_instances (instance_name, last_seen)
                VALUES (?, CURRENT_TIMESTAMP)
                ON CONFLICT(instance_name) 
                DO UPDATE SET last_seen = CURRENT_TIMESTAMP
            """, (instance_name,))
            conn.commit()
        finally:
            conn.close()
    
    def get_active_instances(self, timeout_minutes: int = 2) -> List[str]:
        """Get list of active instances"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
            cursor.execute("""
                SELECT instance_name
                FROM active_instances
                WHERE last_seen > ?
            """, (cutoff,))
            
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_context_for_llm(self, max_turns: int = 5) -> str:
        """Get formatted conversation context for LLM"""
        recent = self.get_recent_conversations(limit=max_turns)
        
        if not recent:
            return "No previous conversation context."
        
        context_parts = []
        for conv in reversed(recent):  # Oldest first
            context_parts.append(f"User: {conv['user_input']}")
            context_parts.append(f"Assistant: {conv['bot_response']}")
        
        return "\n".join(context_parts)

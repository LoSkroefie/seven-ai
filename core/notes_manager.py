"""
Notes Manager - Voice-activated note-taking system
Seven can take, read, search, and manage notes
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import config

class NotesManager:
    """Manages user notes with voice commands"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
        self.pending_note = None  # For "take a note" workflow
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize notes table"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    tags TEXT,
                    importance INTEGER DEFAULT 3,
                    completed BOOLEAN DEFAULT 0
                )
            """)
            
            # Create index for faster searches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_timestamp 
                ON notes(timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notes_category 
                ON notes(category)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_note(self, content: str, category: str = 'general', 
                 tags: List[str] = None, importance: int = 3) -> int:
        """
        Add a new note
        
        Args:
            content: Note text
            category: Category (general, work, personal, ideas, reminders)
            tags: List of tags
            importance: 1-5 (5 = most important)
            
        Returns:
            Note ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            tags_json = json.dumps(tags) if tags else None
            
            cursor.execute("""
                INSERT INTO notes (content, category, tags, importance)
                VALUES (?, ?, ?, ?)
            """, (content, category, tags_json, importance))
            
            note_id = cursor.lastrowid
            conn.commit()
            return note_id
        finally:
            conn.close()
    
    def get_all_notes(self, limit: int = 50, include_completed: bool = False) -> List[Dict]:
        """Get all notes, most recent first"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if include_completed:
                cursor.execute("""
                    SELECT * FROM notes 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            else:
                cursor.execute("""
                    SELECT * FROM notes 
                    WHERE completed = 0
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            notes = []
            for row in cursor.fetchall():
                note = dict(row)
                if note['tags']:
                    note['tags'] = json.loads(note['tags'])
                notes.append(note)
            
            return notes
        finally:
            conn.close()
    
    def search_notes(self, query: str, limit: int = 20) -> List[Dict]:
        """Search notes by content"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE content LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f'%{query}%', limit))
            
            notes = []
            for row in cursor.fetchall():
                note = dict(row)
                if note['tags']:
                    note['tags'] = json.loads(note['tags'])
                notes.append(note)
            
            return notes
        finally:
            conn.close()
    
    def get_notes_by_category(self, category: str, limit: int = 50) -> List[Dict]:
        """Get notes filtered by category"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE category = ? AND completed = 0
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (category, limit))
            
            notes = []
            for row in cursor.fetchall():
                note = dict(row)
                if note['tags']:
                    note['tags'] = json.loads(note['tags'])
                notes.append(note)
            
            return notes
        finally:
            conn.close()
    
    def delete_note(self, note_id: int) -> bool:
        """Delete a note by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_notes_by_content(self, query: str) -> int:
        """Delete notes matching content query"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM notes 
                WHERE content LIKE ?
            """, (f'%{query}%',))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        finally:
            conn.close()
    
    def mark_completed(self, note_id: int) -> bool:
        """Mark a note as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE notes 
                SET completed = 1 
                WHERE id = ?
            """, (note_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_note_count(self) -> Tuple[int, int]:
        """Get total and active note counts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM notes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM notes WHERE completed = 0")
            active = cursor.fetchone()[0]
            
            return total, active
        finally:
            conn.close()
    
    def format_notes_for_speech(self, notes: List[Dict], max_notes: int = 5) -> str:
        """Format notes for voice output"""
        if not notes:
            return "You have no notes."
        
        count = len(notes)
        notes_to_read = notes[:max_notes]
        
        result = []
        if count == 1:
            result.append("You have 1 note.")
        else:
            result.append(f"You have {count} notes.")
            if count > max_notes:
                result.append(f"Here are the most recent {max_notes}:")
        
        for i, note in enumerate(notes_to_read, 1):
            timestamp = note['timestamp']
            content = note['content']
            time_ago = self._format_time_ago(timestamp)
            
            result.append(f"Note {i}, from {time_ago}: {content}")
        
        if count > max_notes:
            result.append(f"And {count - max_notes} more notes.")
        
        return " ".join(result)
    
    def _format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as 'X ago'"""
        try:
            note_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - note_time
            
            seconds = delta.total_seconds()
            
            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif seconds < 604800:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
            else:
                weeks = int(seconds / 604800)
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        except:
            return "recently"
    
    def auto_categorize(self, content: str) -> str:
        """Auto-detect category from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['todo', 'task', 'remind', 'remember to', 'need to']):
            return 'reminders'
        elif any(word in content_lower for word in ['work', 'meeting', 'project', 'deadline', 'client']):
            return 'work'
        elif any(word in content_lower for word in ['idea', 'what if', 'maybe', 'could']):
            return 'ideas'
        elif any(word in content_lower for word in ['buy', 'shopping', 'get', 'purchase']):
            return 'shopping'
        else:
            return 'personal'
    
    def extract_importance(self, content: str) -> int:
        """Extract importance from content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['urgent', 'critical', 'important', 'asap']):
            return 5
        elif any(word in content_lower for word in ['soon', 'priority']):
            return 4
        else:
            return 3

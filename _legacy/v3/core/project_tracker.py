"""
Multi-Session Project Tracking
Track long-running projects across multiple conversations
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import config

class ProjectTracker:
    """Tracks multi-session projects and their progress"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize project tracking tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME,
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    goal TEXT,
                    milestones TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    session_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    work_done TEXT,
                    notes TEXT,
                    progress_delta INTEGER DEFAULT 0,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def create_project(self, name: str, description: str = "", goal: str = "") -> int:
        """Create a new project"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO projects (name, description, goal, last_updated)
                VALUES (?, ?, ?, ?)
            """, (name, description, goal, datetime.now()))
            
            project_id = cursor.lastrowid
            conn.commit()
            return project_id
        finally:
            conn.close()
    
    def add_session(self, project_id: int, work_done: str, progress_delta: int = 0) -> int:
        """Add a work session to a project"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Add session
            cursor.execute("""
                INSERT INTO project_sessions (project_id, work_done, progress_delta)
                VALUES (?, ?, ?)
            """, (project_id, work_done, progress_delta))
            
            # Update project progress
            cursor.execute("""
                UPDATE projects 
                SET progress = progress + ?, last_updated = ?
                WHERE id = ?
            """, (progress_delta, datetime.now(), project_id))
            
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
        finally:
            conn.close()
    
    def get_active_projects(self) -> List[Dict]:
        """Get all active projects"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM projects 
                WHERE status = 'active'
                ORDER BY last_updated DESC
            """)
            
            projects = [dict(row) for row in cursor.fetchall()]
            return projects
        finally:
            conn.close()
    
    def get_project_summary(self, project_id: int) -> Optional[Dict]:
        """Get detailed project summary"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()
            
            if not project:
                return None
            
            # Get recent sessions
            cursor.execute("""
                SELECT * FROM project_sessions 
                WHERE project_id = ?
                ORDER BY session_date DESC
                LIMIT 10
            """, (project_id,))
            
            sessions = [dict(row) for row in cursor.fetchall()]
            
            return {
                'project': dict(project),
                'sessions': sessions,
                'session_count': len(sessions)
            }
        finally:
            conn.close()
    
    def complete_project(self, project_id: int) -> bool:
        """Mark project as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE projects 
                SET status = 'completed', progress = 100
                WHERE id = ?
            """, (project_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

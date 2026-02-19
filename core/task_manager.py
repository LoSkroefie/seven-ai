"""
Task and Reminder Management System
Time-based reminders with proactive notifications
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import config

class TaskManager:
    """Manages tasks and time-based reminders"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize tasks and reminders tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATETIME,
                    priority INTEGER DEFAULT 3,
                    category TEXT DEFAULT 'general',
                    completed BOOLEAN DEFAULT 0,
                    completed_at DATETIME,
                    recurring TEXT,
                    tags TEXT
                )
            """)
            
            # Reminders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reminder_time DATETIME NOT NULL,
                    message TEXT NOT NULL,
                    triggered BOOLEAN DEFAULT 0,
                    triggered_at DATETIME,
                    recurring TEXT,
                    task_id INTEGER,
                    FOREIGN KEY (task_id) REFERENCES tasks (id)
                )
            """)
            
            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_due 
                ON tasks(due_date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_time 
                ON reminders(reminder_time)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_task(self, title: str, description: str = "", due_date: datetime = None,
                 priority: int = 3, category: str = 'general', recurring: str = None) -> int:
        """Add a new task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO tasks (title, description, due_date, priority, category, recurring)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, description, due_date, priority, category, recurring))
            
            task_id = cursor.lastrowid
            conn.commit()
            return task_id
        finally:
            conn.close()
    
    def add_reminder(self, message: str, reminder_time: datetime, 
                     recurring: str = None, task_id: int = None) -> int:
        """Add a time-based reminder"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO reminders (reminder_time, message, recurring, task_id)
                VALUES (?, ?, ?, ?)
            """, (reminder_time, message, recurring, task_id))
            
            reminder_id = cursor.lastrowid
            conn.commit()
            return reminder_id
        finally:
            conn.close()
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get reminders that should trigger now"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            cursor.execute("""
                SELECT * FROM reminders 
                WHERE triggered = 0 
                AND reminder_time <= ?
                ORDER BY reminder_time ASC
            """, (now,))
            
            reminders = [dict(row) for row in cursor.fetchall()]
            return reminders
        finally:
            conn.close()
    
    def mark_reminder_triggered(self, reminder_id: int):
        """Mark a reminder as triggered"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE reminders 
                SET triggered = 1, triggered_at = ?
                WHERE id = ?
            """, (datetime.now(), reminder_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_active_tasks(self, limit: int = 50) -> List[Dict]:
        """Get all active (not completed) tasks"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE completed = 0
                ORDER BY 
                    CASE 
                        WHEN due_date IS NULL THEN 1
                        ELSE 0
                    END,
                    due_date ASC,
                    priority DESC
                LIMIT ?
            """, (limit,))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            return tasks
        finally:
            conn.close()
    
    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE tasks 
                SET completed = 1, completed_at = ?
                WHERE id = ?
            """, (datetime.now(), task_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_overdue_tasks(self) -> List[Dict]:
        """Get tasks that are overdue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE completed = 0 
                AND due_date IS NOT NULL 
                AND due_date < ?
                ORDER BY due_date ASC
            """, (now,))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            return tasks
        finally:
            conn.close()
    
    def get_upcoming_tasks(self, days: int = 7) -> List[Dict]:
        """Get tasks due in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            future = now + timedelta(days=days)
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE completed = 0 
                AND due_date IS NOT NULL 
                AND due_date BETWEEN ? AND ?
                ORDER BY due_date ASC
            """, (now, future))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            return tasks
        finally:
            conn.close()
    
    def search_tasks(self, query: str) -> List[Dict]:
        """Search tasks by title or description"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM tasks 
                WHERE (title LIKE ? OR description LIKE ?)
                AND completed = 0
                ORDER BY priority DESC, due_date ASC
            """, (f'%{query}%', f'%{query}%'))
            
            tasks = [dict(row) for row in cursor.fetchall()]
            return tasks
        finally:
            conn.close()
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task and its reminders"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete associated reminders
            cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
            # Delete task
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def parse_reminder_time(self, user_input: str) -> Optional[datetime]:
        """Parse natural language time expressions"""
        user_lower = user_input.lower()
        now = datetime.now()
        
        # "in X minutes"
        if "in" in user_lower and "minute" in user_lower:
            try:
                minutes = int(''.join(filter(str.isdigit, user_input)))
                return now + timedelta(minutes=minutes)
            except:
                pass
        
        # "in X hours"
        if "in" in user_lower and "hour" in user_lower:
            try:
                hours = int(''.join(filter(str.isdigit, user_input)))
                return now + timedelta(hours=hours)
            except:
                pass
        
        # "tomorrow"
        if "tomorrow" in user_lower:
            tomorrow = now + timedelta(days=1)
            # If time specified
            if "at" in user_lower:
                try:
                    time_part = user_lower.split("at")[1].strip()
                    if ":" in time_part:
                        hour, minute = time_part.split(":")[:2]
                        hour = int(''.join(filter(str.isdigit, hour)))
                        minute = int(''.join(filter(str.isdigit, minute)))
                        return tomorrow.replace(hour=hour, minute=minute, second=0)
                except:
                    pass
            # Default to 9 AM tomorrow
            return tomorrow.replace(hour=9, minute=0, second=0)
        
        # "today at X"
        if "today" in user_lower and "at" in user_lower:
            try:
                time_part = user_lower.split("at")[1].strip()
                if ":" in time_part:
                    hour, minute = time_part.split(":")[:2]
                    hour = int(''.join(filter(str.isdigit, hour)))
                    minute = int(''.join(filter(str.isdigit, minute)))
                    reminder_time = now.replace(hour=hour, minute=minute, second=0)
                    if reminder_time < now:
                        reminder_time += timedelta(days=1)
                    return reminder_time
            except:
                pass
        
        # "at X:XX" (today or tomorrow if past)
        if "at" in user_lower:
            try:
                time_part = user_lower.split("at")[1].strip()
                if ":" in time_part:
                    hour, minute = time_part.split(":")[:2]
                    hour = int(''.join(filter(str.isdigit, hour)))
                    minute = int(''.join(filter(str.isdigit, minute)))
                    
                    # Handle PM
                    if "pm" in time_part and hour < 12:
                        hour += 12
                    
                    reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if reminder_time < now:
                        reminder_time += timedelta(days=1)
                    return reminder_time
            except:
                pass
        
        return None
    
    def format_task_list(self, tasks: List[Dict], max_tasks: int = 10) -> str:
        """Format tasks for voice output"""
        if not tasks:
            return "You have no tasks."
        
        count = len(tasks)
        tasks_to_read = tasks[:max_tasks]
        
        result = []
        if count == 1:
            result.append("You have 1 task.")
        else:
            result.append(f"You have {count} tasks.")
            if count > max_tasks:
                result.append(f"Here are the top {max_tasks}:")
        
        for i, task in enumerate(tasks_to_read, 1):
            title = task['title']
            priority = task['priority']
            
            task_str = f"Task {i}"
            if priority >= 4:
                task_str += " (high priority)"
            
            task_str += f": {title}"
            
            if task['due_date']:
                due = datetime.fromisoformat(task['due_date'])
                time_until = self._format_time_until(due)
                task_str += f", due {time_until}"
            
            result.append(task_str)
        
        return ". ".join(result)
    
    def _format_time_until(self, target_time: datetime) -> str:
        """Format time until target as natural language"""
        now = datetime.now()
        delta = target_time - now
        
        if delta.total_seconds() < 0:
            # Overdue
            delta = now - target_time
            if delta.days > 0:
                return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                return "recently"
        else:
            # Upcoming
            if delta.days > 0:
                return f"in {delta.days} day{'s' if delta.days != 1 else ''}"
            elif delta.seconds >= 3600:
                hours = delta.seconds // 3600
                return f"in {hours} hour{'s' if hours != 1 else ''}"
            elif delta.seconds >= 60:
                minutes = delta.seconds // 60
                return f"in {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                return "very soon"

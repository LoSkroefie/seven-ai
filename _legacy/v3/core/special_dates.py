"""
Birthday and Anniversary Detection System
Tracks and reminds about special dates
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import config

class SpecialDatesManager:
    """Manages birthdays, anniversaries, and special occasions"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize special dates table"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS special_dates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_name TEXT NOT NULL,
                    date_type TEXT NOT NULL,
                    month INTEGER NOT NULL,
                    day INTEGER NOT NULL,
                    year INTEGER,
                    notes TEXT,
                    last_celebrated DATETIME
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_special_dates_month_day 
                ON special_dates(month, day)
            """)
            
            conn.commit()
        finally:
            conn.close()
    
    def add_special_date(self, person_name: str, date_type: str, month: int, 
                        day: int, year: int = None, notes: str = "") -> int:
        """Add a birthday or anniversary"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO special_dates (person_name, date_type, month, day, year, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (person_name, date_type, month, day, year, notes))
            
            date_id = cursor.lastrowid
            conn.commit()
            return date_id
        finally:
            conn.close()
    
    def get_upcoming_dates(self, days_ahead: int = 7) -> List[Dict]:
        """Get special dates in the next N days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now()
            upcoming = []
            
            # Check each day in the range
            for i in range(days_ahead + 1):
                check_date = today + timedelta(days=i)
                month = check_date.month
                day = check_date.day
                
                cursor.execute("""
                    SELECT * FROM special_dates 
                    WHERE month = ? AND day = ?
                """, (month, day))
                
                dates = [dict(row) for row in cursor.fetchall()]
                for date in dates:
                    date['days_until'] = i
                    date['this_year_date'] = check_date.date()
                    upcoming.append(date)
            
            return upcoming
        finally:
            conn.close()
    
    def get_todays_dates(self) -> List[Dict]:
        """Get special dates for today"""
        today = datetime.now()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM special_dates 
                WHERE month = ? AND day = ?
            """, (today.month, today.day))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def mark_celebrated(self, date_id: int):
        """Mark a special date as celebrated"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE special_dates 
                SET last_celebrated = ?
                WHERE id = ?
            """, (datetime.now(), date_id))
            conn.commit()
        finally:
            conn.close()
    
    def format_upcoming_dates(self, dates: List[Dict]) -> str:
        """Format upcoming dates for voice output"""
        if not dates:
            return "No upcoming special dates in the next week."
        
        result = []
        for date in dates:
            person = date['person_name']
            date_type = date['date_type']
            days_until = date['days_until']
            
            if days_until == 0:
                time_desc = "today"
            elif days_until == 1:
                time_desc = "tomorrow"
            else:
                time_desc = f"in {days_until} days"
            
            result.append(f"{person}'s {date_type} is {time_desc}")
        
        return ". ".join(result)

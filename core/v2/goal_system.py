"""
Seven AI v2.0 - Goal System
Gives Seven personal objectives and tracks progress
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class GoalSystem:
    """
    Manages Seven's personal goals and tracks progress
    Goals like "Help user be productive", "Build strong relationship"
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.goals_file = os.path.join(data_dir, "goals.json")
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        if os.path.exists(self.goals_file):
            try:
                with open(self.goals_file, 'r') as f:
                    return json.load(f)
            except:
                return self._create_empty_data()
        return self._create_empty_data()
    
    def _create_empty_data(self) -> Dict:
        return {
            "primary_goals": [
                {
                    "id": "help_productivity",
                    "name": "Help user be more productive",
                    "progress": 0,
                    "milestones": []
                },
                {
                    "id": "build_relationship",
                    "name": "Build strong relationship",
                    "progress": 0,
                    "milestones": []
                },
                {
                    "id": "learn_user",
                    "name": "Learn everything about user",
                    "progress": 0,
                    "milestones": []
                }
            ],
            "achievements": [],
            "daily_objectives": []
        }
    
    def _save_data(self):
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.goals_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_progress(self, goal_id: str, increment: float, milestone: Optional[str] = None):
        """Record progress on a goal"""
        for goal in self.data["primary_goals"]:
            if goal["id"] == goal_id:
                goal["progress"] = min(100, goal["progress"] + increment)
                
                if milestone:
                    goal["milestones"].append({
                        "milestone": milestone,
                        "reached_at": datetime.now().isoformat()
                    })
                
                # Check if goal completed
                if goal["progress"] >= 100:
                    self.add_achievement(f"Completed: {goal['name']}")
        
        self._save_data()
    
    def add_achievement(self, achievement: str):
        """Record an achievement"""
        self.data["achievements"].append({
            "achievement": achievement,
            "achieved_at": datetime.now().isoformat()
        })
        self._save_data()
    
    def set_daily_objective(self, objective: str):
        """Set a daily objective"""
        self.data["daily_objectives"].append({
            "objective": objective,
            "created_at": datetime.now().isoformat(),
            "completed": False
        })
        self._save_data()
    
    def complete_daily_objective(self, index: int):
        """Mark daily objective as complete"""
        if index < len(self.data["daily_objectives"]):
            self.data["daily_objectives"][index]["completed"] = True
            self.data["daily_objectives"][index]["completed_at"] = datetime.now().isoformat()
            self._save_data()
    
    def get_current_goals(self) -> List[Dict]:
        """Get all current goals"""
        return self.data["primary_goals"]
    
    def get_goal_summary(self) -> str:
        """Generate a summary of goal progress"""
        summary = []
        for goal in self.data["primary_goals"]:
            summary.append(f"{goal['name']}: {goal['progress']:.0f}%")
        return "; ".join(summary)
    
    def should_celebrate_achievement(self) -> Optional[str]:
        """Check if there's a recent achievement to celebrate"""
        if self.data["achievements"]:
            latest = self.data["achievements"][-1]
            achieved_time = datetime.fromisoformat(latest["achieved_at"])
            now = datetime.now()
            
            # Celebrate if within last hour
            if (now - achieved_time).total_seconds() < 3600:
                return latest["achievement"]
        
        return None
    
    def get_active_goals(self) -> List[Dict]:
        """Get goals that are not yet complete"""
        return [g for g in self.data["primary_goals"] if g["progress"] < 100]
    
    def get_state(self) -> Dict:
        """Get current state of goal system for v2.0 integration"""
        return {
            "total_goals": len(self.data["primary_goals"]),
            "active_goals": len(self.get_active_goals()),
            "achievements": len(self.data["achievements"]),
            "daily_objectives": len(self.data["daily_objectives"])
        }
    
    def save(self):
        """Save goal data to disk"""
        self._save_data()

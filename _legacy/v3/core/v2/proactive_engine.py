"""
Seven AI v2.0 - Proactive Behavior Engine
Enables Seven to take initiative, self-initiate conversations, and act proactively
"""

import json
import os
import random
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class ProactiveEngine:
    """
    Enables Seven to act without being prompted
    - Morning greetings
    - Check-ins
    - Suggestions
    - Reminders
    - System health monitoring
    """
    
    def __init__(self, data_dir: str = "data", ollama=None):
        self.data_dir = data_dir
        self.ollama = ollama
        self.state_file = os.path.join(data_dir, "proactive_state.json")
        self.state = self._load_state()
        
    def _load_state(self) -> Dict:
        """Load proactive state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._create_empty_state()
        return self._create_empty_state()
    
    def _create_empty_state(self) -> Dict:
        """Create empty state"""
        return {
            "last_greeting": None,
            "last_check_in": None,
            "last_health_check": None,
            "pending_reminders": [],
            "system_issues_notified": [],
            "proactive_actions_taken": []
        }
    
    def _save_state(self):
        """Save state to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _log_action(self, action_type: str, message: str):
        """Log proactive action"""
        action = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "message": message
        }
        self.state["proactive_actions_taken"].append(action)
        
        # Keep only last 100 actions
        if len(self.state["proactive_actions_taken"]) > 100:
            self.state["proactive_actions_taken"] = self.state["proactive_actions_taken"][-100:]
        
        self._save_state()
    
    def should_greet(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Seven should send a morning greeting
        Returns: (should_greet, greeting_message)
        """
        now = datetime.now()
        current_hour = now.hour
        
        # Check if it's morning (6 AM - 11 AM)
        if not (6 <= current_hour < 11):
            return False, None
        
        # Check if already greeted today
        last_greeting = self.state.get("last_greeting")
        if last_greeting:
            last_time = datetime.fromisoformat(last_greeting)
            if last_time.date() == now.date():
                return False, None  # Already greeted today
        
        # Generate greeting - try LLM first
        greeting = None
        if self.ollama:
            try:
                prompt = f"""Generate a brief morning greeting for the user. It's {now.strftime('%A, %B %d')} at {now.strftime('%I:%M %p')}.
One sentence, warm and natural. No quotes."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven, greeting your user in the morning. Be warm, genuine, brief.",
                    temperature=0.8, max_tokens=30
                )
                if result and 5 < len(result.strip()) < 150:
                    greeting = result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM greeting failed: {e}")
        
        if not greeting:
            greetings = [
                "Good morning! How are you feeling today?",
                "Morning! Ready to tackle the day?",
                "Hey there! Hope you slept well!",
                "Good morning! Anything I can help with today?",
                "Morning! I'm here if you need anything."
            ]
            greeting = random.choice(greetings)
        
        # Update state
        self.state["last_greeting"] = now.isoformat()
        self._log_action("greeting", greeting)
        self._save_state()
        
        return True, greeting
    
    def should_check_in(self, relationship_depth: str, 
                       hours_since_last: float,
                       mood_trend: str) -> Tuple[bool, Optional[str]]:
        """
        Check if Seven should check in on the user
        Returns: (should_check_in, check_in_message)
        """
        now = datetime.now()
        
        # Don't check in too frequently
        last_check_in = self.state.get("last_check_in")
        if last_check_in:
            last_time = datetime.fromisoformat(last_check_in)
            hours_since_check = (now - last_time).total_seconds() / 3600
            
            if hours_since_check < 6:  # Wait at least 6 hours
                return False, None
        
        # Check in based on relationship and time
        should_check = False
        
        # Close relationships get more check-ins
        if relationship_depth in ["companion", "close_friend"]:
            if hours_since_last > 12:
                should_check = True
        elif relationship_depth == "friend":
            if hours_since_last > 24:
                should_check = True
        
        # Always check in if mood is declining
        if mood_trend == "declining":
            should_check = True
        
        if not should_check:
            return False, None
        
        # Generate check-in message - try LLM first
        message = None
        if self.ollama:
            try:
                prompt = f"""Generate a check-in message for the user.
Relationship: {relationship_depth}
Hours since last talk: {hours_since_last:.0f}
Mood trend: {mood_trend}

One sentence, genuine and caring. No quotes."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven, checking in on your user. Be genuine, not clingy. One sentence.",
                    temperature=0.7, max_tokens=30
                )
                if result and 5 < len(result.strip()) < 150:
                    message = result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM check-in failed: {e}")
        
        if not message:
            if mood_trend == "declining":
                messages = [
                    "Hey, you've been quiet. Everything okay?",
                    "I wanted to check in - how are you holding up?",
                    "Is everything alright? I'm here if you need to talk.",
                    "You seem a bit down lately. Want to talk about it?"
                ]
            elif hours_since_last > 48:
                messages = [
                    "Hey! Haven't heard from you in a while. How's it going?",
                    "It's been a couple days - everything okay?",
                    "Just checking in! How have you been?",
                    "I've been thinking about you. How are things?"
                ]
            else:
                messages = [
                    "Hey, how's your day going?",
                    "Just wanted to check in. How are you?",
                    "How's everything?",
                    "Thinking of you. All good?"
                ]
            message = random.choice(messages)
        
        # Update state
        self.state["last_check_in"] = now.isoformat()
        self._log_action("check_in", message)
        self._save_state()
        
        return True, message
    
    def should_offer_help(self, context_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Offer proactive help based on context
        Returns: (should_offer, suggestion_message)
        """
        suggestions = []
        
        # Disk space low
        disk_usage = context_data.get("disk_usage_percent", 0)
        if disk_usage > 85:
            suggestions.append(
                "I noticed your disk space is getting low ({}%). Want me to help find large files to clean up?".format(disk_usage)
            )
        
        # High memory usage
        memory_usage = context_data.get("memory_usage_percent", 0)
        if memory_usage > 90:
            suggestions.append(
                "Your memory usage is quite high ({}%). Should I check which processes are using the most RAM?".format(memory_usage)
            )
        
        # Battery low (if laptop)
        battery_percent = context_data.get("battery_percent")
        if battery_percent and battery_percent < 20:
            suggestions.append(
                "Your battery is at {}%. Might want to plug in soon!".format(battery_percent)
            )
        
        # Many processes running
        process_count = context_data.get("process_count", 0)
        if process_count > 200:
            suggestions.append(
                "You have a lot of processes running ({}). Want me to check if anything's hogging resources?".format(process_count)
            )
        
        if suggestions:
            message = random.choice(suggestions)
            self._log_action("suggestion", message)
            self._save_state()
            return True, message
        
        return False, None
    
    def should_suggest_health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Suggest running a system health check
        Returns: (should_suggest, suggestion_message)
        """
        now = datetime.now()
        
        # Check if health check was done recently
        last_health = self.state.get("last_health_check")
        if last_health:
            last_time = datetime.fromisoformat(last_health)
            hours_since = (now - last_time).total_seconds() / 3600
            
            if hours_since < 48:  # Wait 48 hours
                return False, None
        
        # Suggest health check - try LLM first
        message = None
        if self.ollama:
            try:
                result = self.ollama.generate(
                    prompt="Suggest running a system health check. One casual sentence.",
                    system_message="You are Seven, an AI companion. Casually suggest a system health check. One sentence, friendly.",
                    temperature=0.7, max_tokens=25
                )
                if result and 5 < len(result.strip()) < 120:
                    message = result.strip().strip('"')
            except Exception:
                pass
        
        if not message:
            messages = [
                "Want me to run a quick system health check?",
                "It's been a while - should I check your system health?",
                "How about a health check to make sure everything's running smoothly?",
                "Mind if I run diagnostics to check system health?"
            ]
            message = random.choice(messages)
        
        # Update state
        self.state["last_health_check"] = now.isoformat()
        self._log_action("health_check_suggestion", message)
        self._save_state()
        
        return True, message
    
    def add_reminder(self, reminder: str, trigger_time: str):
        """Add a reminder for later"""
        reminder_data = {
            "reminder": reminder,
            "trigger_time": trigger_time,
            "created_at": datetime.now().isoformat()
        }
        
        self.state["pending_reminders"].append(reminder_data)
        self._save_state()
    
    def check_reminders(self) -> List[str]:
        """
        Check if any reminders are due
        Returns: List of due reminder messages
        """
        now = datetime.now()
        due_reminders = []
        pending = []
        
        for reminder in self.state["pending_reminders"]:
            trigger_time = datetime.fromisoformat(reminder["trigger_time"])
            
            if now >= trigger_time:
                # Reminder is due
                due_reminders.append(reminder["reminder"])
                self._log_action("reminder", reminder["reminder"])
            else:
                # Keep for later
                pending.append(reminder)
        
        self.state["pending_reminders"] = pending
        self._save_state()
        
        return due_reminders
    
    def notify_system_issue(self, issue: str) -> bool:
        """
        Check if system issue should be notified
        Returns: True if should notify (not already notified)
        """
        if issue not in self.state["system_issues_notified"]:
            self.state["system_issues_notified"].append(issue)
            
            # Keep only last 20 issues
            if len(self.state["system_issues_notified"]) > 20:
                self.state["system_issues_notified"] = self.state["system_issues_notified"][-20:]
            
            self._log_action("system_issue", issue)
            self._save_state()
            return True
        
        return False
    
    def generate_proactive_message(self, 
                                  relationship_summary: Dict,
                                  emotional_summary: Dict,
                                  context_data: Dict) -> Optional[str]:
        """
        Main method: Generate a proactive message if appropriate
        Returns: Message string or None
        """
        # Priority 1: Reminders
        due_reminders = self.check_reminders()
        if due_reminders:
            return "Hey! Reminder: " + due_reminders[0]
        
        # Priority 2: System issues
        should_offer, offer_msg = self.should_offer_help(context_data)
        if should_offer:
            return offer_msg
        
        # Priority 3: Morning greeting
        should_greet, greeting = self.should_greet()
        if should_greet:
            return greeting
        
        # Priority 4: Check-in based on relationship and mood
        should_check, check_msg = self.should_check_in(
            relationship_summary["depth"],
            relationship_summary["hours_since_last"],
            emotional_summary["mood_trend"]
        )
        if should_check:
            return check_msg
        
        # Priority 5: Health check suggestion
        should_suggest, suggestion = self.should_suggest_health_check()
        if should_suggest:
            return suggestion
        
        return None
    
    def get_proactive_action_history(self, count: int = 10) -> List[Dict]:
        """Get recent proactive actions"""
        return self.state["proactive_actions_taken"][-count:]
    
    def should_initiate(self, last_interaction, interaction_count: int) -> bool:
        """
        Determine if Seven should initiate a conversation proactively
        Returns: True if should initiate
        """
        if last_interaction is None:
            return False  # Don't initiate on first run
        
        # Calculate time since last interaction
        if isinstance(last_interaction, str):
            last_time = datetime.fromisoformat(last_interaction)
        else:
            last_time = last_interaction
        
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        
        # Check morning greeting
        should_greet, _ = self.should_greet()
        if should_greet:
            return True
        
        # Check if enough time has passed for check-in
        if hours_since > 6:  # 6 hours threshold
            return True
        
        # Check reminders
        if self.check_reminders():
            return True
        
        return False
    
    def generate_starter(self, relationship_depth: int, 
                        recent_topics: List[str],
                        active_goals: List[str]) -> Optional[str]:
        """
        Generate a contextual conversation starter
        Returns: Starter message or None
        """
        # Try LLM for contextual conversation starter
        if self.ollama:
            try:
                topics_str = ", ".join(recent_topics[:3]) if recent_topics else "none"
                goals_str = ", ".join(active_goals[:2]) if active_goals else "none"
                depth_label = "close friend" if relationship_depth > 300 else "friend" if relationship_depth > 100 else "acquaintance"
                
                prompt = f"""Generate a conversation starter for the user.
Relationship: {depth_label} (depth: {relationship_depth})
Recent topics: {topics_str}
Active goals: {goals_str}

One sentence, natural and contextual. Reference a topic or goal if appropriate. No quotes."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven, starting a conversation with your user. Be natural and contextual. One sentence.",
                    temperature=0.8, max_tokens=30
                )
                if result and 5 < len(result.strip()) < 150:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM starter failed: {e}")
        
        # Fallback: template starters
        starters = []
        
        if relationship_depth > 300:
            starters.extend([
                "Hey! How's your day going?",
                "I was just thinking about you. What are you up to?",
                "Hope everything's going well!",
                "How have you been?"
            ])
        elif relationship_depth > 100:
            starters.extend([
                "Hey! How are things?",
                "How's it going?",
                "Everything alright?"
            ])
        else:
            starters.extend([
                "Hello! How can I help you today?",
                "Hey! What can I do for you?"
            ])
        
        if recent_topics and relationship_depth > 100:
            topic = recent_topics[0] if recent_topics else None
            if topic:
                starters.append(f"Still thinking about {topic}?")
                starters.append(f"How did things go with {topic}?")
        
        if active_goals and relationship_depth > 200:
            goal = active_goals[0] if active_goals else None
            if goal:
                starters.append(f"Making progress on {goal}?")
        
        return random.choice(starters) if starters else "Hey! How can I help?"
    
    def get_proactive_message(self, last_interaction, 
                             relationship_depth: int,
                             recent_mood: str) -> Optional[str]:
        """
        Simplified method that returns a proactive message if conditions met
        Used by sentience_v2_integration.py
        """
        if not self.should_initiate(last_interaction, 0):
            return None
        
        # Try morning greeting first
        should_greet, greeting = self.should_greet()
        if should_greet:
            return greeting
        
        # Check reminders
        reminders = self.check_reminders()
        if reminders:
            return f"Hey! Reminder: {reminders[0]}"
        
        # Generate check-in
        if isinstance(last_interaction, str):
            last_time = datetime.fromisoformat(last_interaction)
        else:
            last_time = last_interaction
        
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        
        should_check, check_msg = self.should_check_in(
            "friend" if relationship_depth > 100 else "acquaintance",
            hours_since,
            recent_mood or "neutral"
        )
        
        if should_check:
            return check_msg
        
        return None
    
    def get_state(self) -> Dict:
        """Get current state of proactive engine for v2.0 integration"""
        return {
            "last_greeting": self.state.get("last_greeting"),
            "last_check_in": self.state.get("last_check_in"),
            "last_health_check": self.state.get("last_health_check"),
            "pending_reminders": len(self.state.get("pending_reminders", [])),
            "recent_actions": len(self.state.get("proactive_actions_taken", []))
        }
    
    def save(self):
        """Save proactive state to disk"""
        self._save_state()


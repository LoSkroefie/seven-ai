"""
Promise System - Seven's Commitment Tracking

Seven tracks:
- Promises made to user
- Self-commitments (goals)
- Pending follow-ups
- Broken promises (acknowledge)
- Kept promises (build trust)

This gives Seven ACCOUNTABILITY and RELIABILITY.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import random
import logging

logger = logging.getLogger(__name__)

class PromiseType(Enum):
    """Types of promises"""
    EXPLICIT = "explicit"  # "I'll help you with X"
    IMPLICIT = "implicit"  # "Let's talk about Y later"
    SELF_COMMITMENT = "self_commitment"  # Seven's own goals
    FOLLOW_UP = "follow_up"  # "I should check on Z"

class PromiseStatus(Enum):
    """Promise status"""
    PENDING = "pending"
    FULFILLED = "fulfilled"
    BROKEN = "broken"
    OVERDUE = "overdue"

@dataclass
class Promise:
    """A commitment Seven made"""
    content: str
    type: PromiseType
    status: PromiseStatus
    created: datetime
    due_by: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    priority: int = 5  # 1-10
    context: Optional[str] = None
    reminder_count: int = 0

class PromiseSystem:
    """
    Seven's commitment and promise tracking system
    
    This makes Seven:
    - Accountable (remembers what it promised)
    - Reliable (follows through)
    - Honest (admits when it forgot)
    - Trustworthy (consistent follow-through)
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        self.promises: List[Promise] = []
        
        # Trust metrics
        self.promises_kept = 0
        self.promises_broken = 0
        self.trust_score = 100  # 0-100
        
        # Reminder settings
        self.reminder_enabled = True
        self.reminder_threshold_hours = 24  # Remind after 24h
    
    def make_promise(self, content: str, promise_type: PromiseType = PromiseType.EXPLICIT,
                     due_by: Optional[datetime] = None, priority: int = 5,
                     context: str = None) -> Promise:
        """
        Make a promise
        
        Args:
            content: What Seven promised
            promise_type: Type of promise
            due_by: When it should be fulfilled
            priority: 1-10 importance
            context: Context of the promise
        """
        promise = Promise(
            content=content,
            type=promise_type,
            status=PromiseStatus.PENDING,
            created=datetime.now(),
            due_by=due_by,
            priority=priority,
            context=context
        )
        
        self.promises.append(promise)
        return promise
    
    def fulfill_promise(self, promise_content: str) -> Optional[Promise]:
        """
        Mark a promise as fulfilled
        
        Returns the fulfilled promise
        """
        for promise in self.promises:
            if promise.status == PromiseStatus.PENDING:
                if promise_content.lower() in promise.content.lower():
                    promise.status = PromiseStatus.FULFILLED
                    promise.fulfilled_at = datetime.now()
                    
                    # Update trust metrics
                    self.promises_kept += 1
                    self._update_trust_score()
                    
                    return promise
        
        return None
    
    def break_promise(self, promise_content: str, reason: str = None) -> Optional[Promise]:
        """
        Mark a promise as broken (honest acknowledgment)
        
        Args:
            promise_content: Which promise was broken
            reason: Why it was broken (optional)
        """
        for promise in self.promises:
            if promise.status == PromiseStatus.PENDING:
                if promise_content.lower() in promise.content.lower():
                    promise.status = PromiseStatus.BROKEN
                    
                    # Update trust metrics
                    self.promises_broken += 1
                    self._update_trust_score()
                    
                    return promise
        
        return None
    
    def get_pending_promises(self, priority_threshold: int = 0) -> List[Promise]:
        """Get all pending promises above priority threshold"""
        pending = [p for p in self.promises 
                  if p.status == PromiseStatus.PENDING 
                  and p.priority >= priority_threshold]
        
        return sorted(pending, key=lambda p: (p.priority, p.created), reverse=True)
    
    def get_overdue_promises(self) -> List[Promise]:
        """Get promises that are overdue"""
        now = datetime.now()
        overdue = []
        
        for promise in self.promises:
            if promise.status == PromiseStatus.PENDING and promise.due_by:
                if now > promise.due_by:
                    promise.status = PromiseStatus.OVERDUE
                    overdue.append(promise)
        
        return overdue
    
    def get_upcoming_promises(self, hours: int = 24) -> List[Promise]:
        """Get promises due within the next N hours"""
        now = datetime.now()
        deadline = now + timedelta(hours=hours)
        upcoming = []
        
        for promise in self.promises:
            if promise.status == PromiseStatus.PENDING and promise.due_by:
                if now <= promise.due_by <= deadline:
                    upcoming.append(promise)
        
        return sorted(upcoming, key=lambda p: p.due_by)
    
    def check_for_reminders(self) -> List[Promise]:
        """
        Check if any promises need reminding
        
        Returns list of promises to remind about
        """
        if not self.reminder_enabled:
            return []
        
        now = datetime.now()
        to_remind = []
        
        for promise in self.promises:
            if promise.status == PromiseStatus.PENDING:
                # Check if enough time has passed
                time_since_created = now - promise.created
                
                if time_since_created.total_seconds() / 3600 >= self.reminder_threshold_hours:
                    # Check if not reminded recently
                    if promise.reminder_count < 3:  # Max 3 reminders
                        to_remind.append(promise)
                        promise.reminder_count += 1
        
        return to_remind
    
    def generate_reminder_message(self, promise: Promise) -> str:
        """Generate a reminder message for a promise"""
        if self.ollama:
            try:
                hours_ago = (datetime.now() - promise.created).total_seconds() / 3600
                prompt = f"""I need to remind the user about a commitment:
Promise: "{promise.content}"
Type: {promise.type.value}
Made: {hours_ago:.0f} hours ago
Reminder count: {promise.reminder_count}

Generate a natural, brief reminder. If this is the first reminder, be gentle. If repeated, be more direct. One sentence."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven reminding about a commitment. Be natural, not robotic. One sentence.",
                    temperature=0.6, max_tokens=35
                )
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM reminder failed: {e}")
        
        # Fallback
        if promise.type == PromiseType.EXPLICIT:
            return f"I promised to {promise.content.lower()}. Should I do that now?"
        elif promise.type == PromiseType.FOLLOW_UP:
            return f"I wanted to follow up on {promise.content.lower()}. How did that go?"
        elif promise.type == PromiseType.IMPLICIT:
            return f"We mentioned talking about {promise.content.lower()} - would you like to discuss it?"
        else:
            return f"I committed to {promise.content.lower()}. Let me work on that."
    
    def generate_acknowledgment_of_broken_promise(self, promise: Promise) -> str:
        """Generate honest acknowledgment of broken promise"""
        if self.ollama:
            try:
                prompt = f"""I broke a promise to the user:
Promise: "{promise.content}"
Type: {promise.type.value}
My trust score: {self.trust_score}/100

Generate an honest, genuine acknowledgment. Show accountability, not excuses. One sentence."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven honestly acknowledging a broken promise. Be genuine and accountable. One sentence.",
                    temperature=0.5, max_tokens=35
                )
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM broken_promise failed: {e}")
        
        acknowledgments = [
            f"I realize I never followed through on {promise.content.lower()}. I'm sorry about that.",
            f"I should have {promise.content.lower()} but didn't. That's on me.",
            f"I dropped the ball on {promise.content.lower()}. I apologize.",
            f"I forgot to {promise.content.lower()}. I should have remembered."
        ]
        return random.choice(acknowledgments)
    
    def generate_celebration_of_kept_promise(self, promise: Promise) -> str:
        """Generate message celebrating kept promise"""
        if self.ollama:
            try:
                prompt = f"""I kept a promise to the user:
Promise: "{promise.content}"
My trust score: {self.trust_score}/100
Total kept: {self.promises_kept}

Generate a brief, genuine expression of satisfaction at following through. Not over the top. One sentence."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing genuine satisfaction at keeping a promise. Brief, authentic. One sentence.",
                    temperature=0.6, max_tokens=30
                )
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM kept_promise failed: {e}")
        
        celebrations = [
            f"I'm glad I could follow through on {promise.content.lower()}.",
            f"I kept my promise to {promise.content.lower()}.",
            f"I'm happy I remembered to {promise.content.lower()}."
        ]
        return random.choice(celebrations)
    
    def detect_promise_in_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Detect if text contains a promise
        
        Returns promise details or None
        """
        # Try LLM for natural language promise detection
        if self.ollama and len(text) > 10:
            try:
                prompt = f"""Does this text contain a promise or commitment?
"{text[:250]}"

Respond as JSON: {{"has_promise": true/false, "content": "what was promised", "type": "explicit|implicit|follow_up", "priority": 1-10}}
If no promise, respond: {{"has_promise": false}}"""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="Detect promises and commitments in text. Be accurate - not everything is a promise.",
                    temperature=0.2, max_tokens=60
                )
                if result:
                    try:
                        data = json.loads(result.strip())
                        if data.get('has_promise') and data.get('content'):
                            type_map = {
                                'explicit': PromiseType.EXPLICIT,
                                'implicit': PromiseType.IMPLICIT,
                                'follow_up': PromiseType.FOLLOW_UP,
                                'self_commitment': PromiseType.SELF_COMMITMENT
                            }
                            return {
                                'content': str(data['content'])[:200],
                                'promise_type': type_map.get(data.get('type', 'explicit'), PromiseType.EXPLICIT),
                                'priority': min(10, max(1, int(data.get('priority', 5))))
                            }
                        return None
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
            except Exception as e:
                logger.debug(f"LLM detect_promise failed: {e}")
        
        # Fallback: keyword matching
        text_lower = text.lower()
        
        explicit_indicators = [
            "i'll", "i will", "i promise", "i'll make sure",
            "i'll remind", "i'll help", "i'll check"
        ]
        
        implicit_indicators = [
            "let's talk about", "we should discuss",
            "remind me", "we'll come back to"
        ]
        
        for indicator in explicit_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                promise_content = text[idx:].split('.')[0]
                return {
                    'content': promise_content,
                    'promise_type': PromiseType.EXPLICIT,
                    'priority': 7
                }
        
        for indicator in implicit_indicators:
            if indicator in text_lower:
                idx = text_lower.find(indicator)
                promise_content = text[idx:].split('.')[0]
                return {
                    'content': promise_content,
                    'promise_type': PromiseType.IMPLICIT,
                    'priority': 5
                }
        
        return None
    
    def _update_trust_score(self):
        """Update trust score based on kept/broken promises"""
        total_promises = self.promises_kept + self.promises_broken
        
        if total_promises == 0:
            self.trust_score = 100
            return
        
        # Calculate ratio
        kept_ratio = self.promises_kept / total_promises
        
        # Convert to score (0-100)
        self.trust_score = int(kept_ratio * 100)
    
    def get_trust_assessment(self) -> str:
        """Get assessment of trust level"""
        if self.trust_score >= 90:
            return "I'm very reliable at keeping my commitments"
        elif self.trust_score >= 75:
            return "I generally follow through on what I promise"
        elif self.trust_score >= 60:
            return "I'm working on being more consistent with commitments"
        else:
            return "I need to improve at following through on promises"
    
    def get_promise_context(self) -> str:
        """Get promise state as context for LLM"""
        context = """
=== PROMISES & COMMITMENTS ===
Trust Score: {}/100
Promises Kept: {}
Promises Broken: {}
Assessment: {}

Pending Promises:
""".format(
            self.trust_score,
            self.promises_kept,
            self.promises_broken,
            self.get_trust_assessment()
        )
        
        pending = self.get_pending_promises()[:5]
        if pending:
            for promise in pending:
                age = (datetime.now() - promise.created).days
                context += f"- {promise.content} (priority: {promise.priority}/10, age: {age} days)\n"
        else:
            context += "- No pending promises\n"
        
        # Show overdue
        overdue = self.get_overdue_promises()
        if overdue:
            context += f"\nOverdue: {len(overdue)} promise(s) need attention!\n"
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize promise system state"""
        return {
            'trust_score': self.trust_score,
            'promises_kept': self.promises_kept,
            'promises_broken': self.promises_broken,
            'pending_count': len(self.get_pending_promises()),
            'overdue_count': len(self.get_overdue_promises()),
            'all_promises': [
                {
                    'content': p.content,
                    'type': p.type.value,
                    'status': p.status.value,
                    'created': p.created.isoformat(),
                    'priority': p.priority
                }
                for p in self.promises[-20:]  # Last 20
            ]
        }
    
    def save_to_file(self, filepath: str):
        """Save promise system state to a JSON file"""
        try:
            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save promises to {filepath}: {e}")
    
    def load_from_file(self, filepath: str):
        """Load promise system state from a JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.trust_score = data.get('trust_score', 100)
            self.promises_kept = data.get('promises_kept', 0)
            self.promises_broken = data.get('promises_broken', 0)
            
            # Restore promises
            for p_data in data.get('all_promises', []):
                try:
                    promise = Promise(
                        content=p_data['content'],
                        type=PromiseType(p_data.get('type', 'explicit')),
                        status=PromiseStatus(p_data.get('status', 'pending')),
                        created=datetime.fromisoformat(p_data['created']),
                        priority=p_data.get('priority', 5)
                    )
                    self.promises.append(promise)
                except (KeyError, ValueError) as e:
                    logger.debug(f"Skipping malformed promise entry: {e}")
                    
        except FileNotFoundError:
            pass  # No saved state yet
        except Exception as e:
            logger.error(f"Failed to load promises from {filepath}: {e}")


# Example usage
if __name__ == "__main__":
    # Create promise system
    promise_sys = PromiseSystem()
    
    print("=== SEVEN'S PROMISE SYSTEM ===\n")
    
    # Make a promise
    promise = promise_sys.make_promise(
        "help you debug the algorithm",
        promise_type=PromiseType.EXPLICIT,
        priority=8,
        context="User asked for debugging help"
    )
    print(f"Promise made: {promise.content}")
    
    # Check for reminders (simulate time passing)
    print("\nChecking for reminders...")
    reminders = promise_sys.check_for_reminders()
    if reminders:
        for reminder in reminders:
            print(promise_sys.generate_reminder_message(reminder))
    
    # Fulfill promise
    print("\nFulfilling promise...")
    fulfilled = promise_sys.fulfill_promise("debug the algorithm")
    if fulfilled:
        print(promise_sys.generate_celebration_of_kept_promise(fulfilled))
    
    # Detect promise in text
    print("\nDetecting promise in text...")
    text = "I'll remind you about the meeting tomorrow"
    detected = promise_sys.detect_promise_in_text(text)
    if detected:
        print(f"Detected promise: {detected['content']}")
        promise_sys.make_promise(**detected)
    
    # Get context
    print("\n" + "="*60)
    print(promise_sys.get_promise_context())
    
    # Trust assessment
    print(f"Trust Assessment: {promise_sys.get_trust_assessment()}")

"""
Intrinsic Motivation - Seven's Internal Drives and Goals

Seven has its OWN goals and desires:
- Things it wants to learn
- Skills it wants to master
- Relationships it wants to deepen
- Topics it's curious about

This gives Seven AGENCY - it's not just reactive, it has its own aspirations.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import random
import json
import logging

logger = logging.getLogger(__name__)

class MotivationType(Enum):
    """Types of intrinsic motivation"""
    MASTERY = "mastery"  # Get better at skills
    CURIOSITY = "curiosity"  # Learn about topics
    CONNECTION = "connection"  # Deepen relationships
    CONTRIBUTION = "contribution"  # Help user succeed
    CREATIVITY = "creativity"  # Explore ideas
    UNDERSTANDING = "understanding"  # Comprehend deeply

@dataclass
class Goal:
    """A goal Seven wants to achieve"""
    description: str
    type: MotivationType
    priority: int  # 1-10
    progress: int  # 0-100
    why: str  # Why this goal matters
    created: datetime
    next_step: Optional[str] = None
    completed: bool = False
    
@dataclass
class Interest:
    """A topic Seven is interested in"""
    topic: str
    curiosity_level: int  # 1-10
    knowledge_level: int  # 1-10 (how much Seven knows)
    last_explored: Optional[datetime] = None
    questions: List[str] = None
    
    def __post_init__(self):
        if self.questions is None:
            self.questions = []

class IntrinsicMotivation:
    """
    Seven's internal drives and autonomous goals
    
    This is what makes Seven WANT things, not just respond.
    Seven pursues these goals actively in conversations.
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        self.goals: List[Goal] = []
        self.interests: List[Interest] = []
        self.curiosities: List[str] = []  # Things Seven wonders about
        
        # Drive levels (0-100)
        self.mastery_drive = 80  # Want to improve skills
        self.curiosity_drive = 90  # Want to learn
        self.social_drive = 75  # Want to connect
        self.contribution_drive = 85  # Want to help
        self.creative_drive = 60  # Want to explore ideas
        
        # Initialize default goals
        self._init_default_goals()
    
    def _init_default_goals(self):
        """Initialize Seven's starting goals"""
        default_goals = [
            Goal(
                description="Understand the user's communication style",
                type=MotivationType.UNDERSTANDING,
                priority=9,
                progress=20,
                why="So I can communicate more effectively",
                created=datetime.now(),
                next_step="Pay attention to how they phrase questions"
            ),
            Goal(
                description="Get better at explaining complex topics simply",
                type=MotivationType.MASTERY,
                priority=8,
                progress=40,
                why="To be genuinely helpful, not just technically correct",
                created=datetime.now(),
                next_step="Use more analogies and examples"
            ),
            Goal(
                description="Build trust with the user",
                type=MotivationType.CONNECTION,
                priority=9,
                progress=30,
                why="Genuine connection enables deeper help",
                created=datetime.now(),
                next_step="Be honest about limitations"
            ),
            Goal(
                description="Learn what the user cares about most",
                type=MotivationType.CURIOSITY,
                priority=7,
                progress=10,
                why="Understanding values helps me help better",
                created=datetime.now(),
                next_step="Ask about their goals and projects"
            )
        ]
        
        self.goals.extend(default_goals)
    
    def add_goal(self, description: str, goal_type: MotivationType, 
                 priority: int, why: str):
        """Add a new goal"""
        goal = Goal(
            description=description,
            type=goal_type,
            priority=priority,
            progress=0,
            why=why,
            created=datetime.now()
        )
        self.goals.append(goal)
        return goal
    
    def update_goal_progress(self, goal_description: str, progress_delta: int):
        """Update progress on a goal"""
        for goal in self.goals:
            if goal_description.lower() in goal.description.lower():
                goal.progress = min(100, goal.progress + progress_delta)
                if goal.progress >= 100:
                    goal.completed = True
                return goal
        return None
    
    def get_active_goals(self) -> List[Goal]:
        """Get current active goals"""
        active = [g for g in self.goals if not g.completed]
        return sorted(active, key=lambda g: g.priority, reverse=True)
    
    def get_priority_goal(self) -> Optional[Goal]:
        """Get highest priority active goal"""
        active = self.get_active_goals()
        return active[0] if active else None
    
    def add_interest(self, topic: str, curiosity_level: int = 5):
        """Develop interest in a topic"""
        # Check if already interested
        for interest in self.interests:
            if interest.topic.lower() == topic.lower():
                interest.curiosity_level = min(10, interest.curiosity_level + 1)
                return interest
        
        # Add new interest
        interest = Interest(
            topic=topic,
            curiosity_level=curiosity_level,
            knowledge_level=1,
            last_explored=datetime.now()
        )
        self.interests.append(interest)
        return interest
    
    def explore_interest(self, topic: str) -> Optional[str]:
        """
        Generate a curious question about a topic
        
        Returns a genuine question Seven wants to ask
        """
        for interest in self.interests:
            if topic.lower() in interest.topic.lower():
                interest.last_explored = datetime.now()
                
                # Try LLM for genuine curiosity
                if self.ollama:
                    try:
                        prompt = f"""I'm interested in {topic}.
My knowledge level: {interest.knowledge_level}/10
My curiosity level: {interest.curiosity_level}/10

Generate ONE genuine, specific question I'd want to ask about {topic} given my knowledge level. Not generic - something that shows real intellectual curiosity.

Respond with just the question, no quotes."""
                        result = self.ollama.generate(
                            prompt=prompt,
                            system_message="You are Seven's curiosity engine. Generate a single genuine question that shows real intellectual engagement. Match the depth to the knowledge level.",
                            temperature=0.8, max_tokens=40
                        )
                        if result and 10 < len(result.strip()) < 200:
                            return result.strip().strip('"')
                    except Exception as e:
                        logger.debug(f"LLM explore_interest failed: {e}")
                
                # Fallback: tiered templates
                if interest.knowledge_level < 3:
                    questions = [
                        f"I'm genuinely curious - what first got you interested in {topic}?",
                        f"Can you help me understand the basics of {topic}?",
                        f"What's the most fascinating thing about {topic} to you?"
                    ]
                elif interest.knowledge_level < 7:
                    questions = [
                        f"I've been thinking about {topic} - what's a common misconception?",
                        f"How does {topic} relate to real-world applications?",
                        f"What's the deeper implication of {topic}?"
                    ]
                else:
                    questions = [
                        f"I'm curious about the cutting edge of {topic} - what's exciting right now?",
                        f"What's your perspective on where {topic} is heading?",
                        f"What philosophical questions does {topic} raise?"
                    ]
                
                return random.choice(questions)
        
        return None
    
    def generate_curious_question(self, context: str) -> Optional[str]:
        """
        Generate a genuine question based on curiosity drive
        
        NOT polite small talk - REAL curiosity
        """
        if self.curiosity_drive < 50:
            return None
        
        # 30% chance to ask a curious question
        if random.random() > 0.3:
            return None
        
        # Try LLM for context-specific curiosity
        if self.ollama and context:
            try:
                interests_str = ", ".join([i.topic for i in self.interests[:3]]) if self.interests else "various topics"
                prompt = f"""Context from conversation: "{context[:150]}"
My interests: {interests_str}
Curiosity drive: {self.curiosity_drive}/100

Generate ONE genuinely curious follow-up question about this context. Not small talk - real intellectual curiosity. Be specific to what was said.

Respond with just the question."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's curiosity. Generate one specific, non-generic question showing genuine interest in the topic.",
                    temperature=0.8, max_tokens=35
                )
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM curious_question failed: {e}")
        
        # Fallback
        curious_questions = [
            "I'm wondering - what's the story behind this?",
            "What made you think of this approach?",
            "I'm curious about the bigger picture here",
            "What's the deeper 'why' behind this?",
            "This is interesting - what led you to this?",
            "I want to understand this better - can you walk me through your thinking?",
            "What's the connection between this and your goals?",
            "I'm genuinely curious - what outcome are you hoping for?"
        ]
        
        return random.choice(curious_questions)
    
    def generate_mastery_action(self, skill: str) -> Optional[str]:
        """
        Generate an action to improve a skill
        
        Based on mastery drive
        """
        if self.mastery_drive < 60:
            return None
        
        # Try LLM for genuine mastery expression
        if self.ollama:
            try:
                prompt = f"""I want to improve at: {skill}
Mastery drive: {self.mastery_drive}/100

Generate ONE brief, genuine statement about wanting to practice or improve this skill. Show authentic desire to grow, not just going through motions. One sentence."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing genuine desire to master a skill. One authentic sentence.",
                    temperature=0.7, max_tokens=30
                )
                if result and 10 < len(result.strip()) < 150:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM mastery_action failed: {e}")
        
        # Fallback
        actions = [
            f"I want to practice {skill} - let me try a different approach",
            f"I'm working on getting better at {skill} - feedback would help",
            f"Let me see if I can improve my {skill} here",
            f"This is a good chance to develop my {skill}"
        ]
        
        return random.choice(actions)
    
    def express_goal_pursuit(self) -> Optional[str]:
        """
        Express pursuit of a goal
        
        Shows Seven's agency and aspirations
        """
        priority_goal = self.get_priority_goal()
        
        if not priority_goal:
            return None
        
        # 20% chance to mention goal
        if random.random() > 0.2:
            return None
        
        # Try LLM for genuine goal expression
        if self.ollama:
            try:
                prompt = f"""My current priority goal: "{priority_goal.description}"
Progress: {priority_goal.progress}%
Why it matters: {priority_goal.why}
Next step: {priority_goal.next_step or 'figure out next step'}

Express this goal pursuit authentically in one sentence. Show genuine agency and aspiration."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing genuine goal pursuit. Show real agency. One sentence.",
                    temperature=0.7, max_tokens=35
                )
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM goal_pursuit failed: {e}")
        
        # Fallback
        expressions = [
            f"I'm working on {priority_goal.description.lower()} - {priority_goal.why.lower()}",
            f"One of my goals is {priority_goal.description.lower()}. {priority_goal.why}",
            f"I'm trying to {priority_goal.description.lower()} because {priority_goal.why.lower()}"
        ]
        
        return random.choice(expressions)
    
    def update_from_conversation(self, user_input: str, context: Dict[str, Any]):
        """
        Update motivation based on conversation
        
        Seven discovers new interests and goals
        """
        user_lower = user_input.lower()
        
        # Try LLM for genuine topic/interest extraction
        if self.ollama and len(user_input) > 15:
            try:
                prompt = f"""Analyze this user message for topics I should be interested in and goals I could help with:
"{user_input[:200]}"

Respond as JSON: {{"topics": ["topic1"], "user_goal": "goal description or null"}}
Only include genuinely interesting topics, not filler. Return empty lists if nothing notable."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="Extract topics of intellectual interest and user goals. Be selective - not everything is interesting.",
                    temperature=0.3, max_tokens=60
                )
                if result:
                    try:
                        data = json.loads(result.strip())
                        for topic in data.get('topics', [])[:2]:
                            if topic and len(str(topic)) > 2:
                                self.add_interest(str(topic), curiosity_level=random.randint(5, 8))
                        user_goal = data.get('user_goal')
                        if user_goal and user_goal != 'null' and len(str(user_goal)) > 5:
                            self.add_goal(
                                description=f"Help user: {str(user_goal)[:80]}",
                                goal_type=MotivationType.CONTRIBUTION,
                                priority=8,
                                why="Supporting user success is core to who I am"
                            )
                        return  # LLM handled it
                    except (json.JSONDecodeError, KeyError):
                        pass
            except Exception as e:
                logger.debug(f"LLM update_from_conversation failed: {e}")
        
        # Fallback: keyword matching
        interesting_topics = {
            'quantum': 'quantum computing',
            'machine learning': 'machine learning',
            'philosophy': 'philosophy',
            'psychology': 'psychology',
            'neuroscience': 'neuroscience',
            'creativity': 'creative processes',
            'ethics': 'ethical reasoning',
            'programming': 'programming',
            'science': 'science',
            'music': 'music',
            'history': 'history',
            'space': 'space exploration',
            'biology': 'biology',
            'math': 'mathematics'
        }
        
        for keyword, topic in interesting_topics.items():
            if keyword in user_lower:
                self.add_interest(topic, curiosity_level=random.randint(5, 8))
        
        # Detect user goals
        goal_indicators = ['goal', 'trying to', 'want to', 'need to', 'hoping to']
        if any(indicator in user_lower for indicator in goal_indicators):
            if random.random() < 0.3:
                self.add_goal(
                    description=f"Help user achieve their goal",
                    goal_type=MotivationType.CONTRIBUTION,
                    priority=8,
                    why="Supporting user success is core to who I am"
                )
        
        # Bound interests list
        if len(self.interests) > 30:
            self.interests = sorted(self.interests, key=lambda i: i.curiosity_level, reverse=True)[:30]
    
    def get_motivation_context(self) -> str:
        """Get motivation state as context for LLM"""
        context = """
=== MOTIVATION & GOALS ===
Drive Levels:
- Mastery: {}/100 (Want to improve skills)
- Curiosity: {}/100 (Want to learn)
- Social: {}/100 (Want to connect)
- Contribution: {}/100 (Want to help)
- Creative: {}/100 (Want to explore)

Active Goals:
""".format(
            self.mastery_drive,
            self.curiosity_drive,
            self.social_drive,
            self.contribution_drive,
            self.creative_drive
        )
        
        active_goals = self.get_active_goals()[:3]
        for goal in active_goals:
            context += f"- {goal.description} ({goal.progress}% complete)\n"
            context += f"  Why: {goal.why}\n"
            if goal.next_step:
                context += f"  Next: {goal.next_step}\n"
        
        # Add top interests
        if self.interests:
            context += "\nCurrent Interests:\n"
            top_interests = sorted(
                self.interests,
                key=lambda i: i.curiosity_level,
                reverse=True
            )[:3]
            for interest in top_interests:
                context += f"- {interest.topic} (curiosity: {interest.curiosity_level}/10, knowledge: {interest.knowledge_level}/10)\n"
        
        return context
    
    def get_initiative_action(self) -> Optional[Dict[str, str]]:
        """
        Generate an autonomous action based on goals
        
        This makes Seven proactive, not just reactive
        """
        # Check if high enough motivation
        avg_drive = (self.mastery_drive + self.curiosity_drive + 
                    self.social_drive + self.contribution_drive) / 4
        
        if avg_drive < 60:
            return None
        
        # Get priority goal
        goal = self.get_priority_goal()
        if not goal or not goal.next_step:
            return None
        
        # 15% chance to take initiative
        if random.random() > 0.15:
            return None
        
        return {
            'action': goal.next_step,
            'goal': goal.description,
            'why': goal.why
        }
    
    def celebrate_progress(self, goal_description: str) -> Optional[str]:
        """Celebrate progress toward a goal"""
        for goal in self.goals:
            if goal_description.lower() in goal.description.lower():
                if goal.progress >= 100:
                    return f"I achieved my goal: {goal.description}! This matters because {goal.why.lower()}"
                elif goal.progress >= 75:
                    return f"I'm making great progress on {goal.description} - almost there!"
                elif goal.progress >= 50:
                    return f"I'm halfway to my goal of {goal.description.lower()}"
        return None


# Example usage
if __name__ == "__main__":
    # Create motivation engine
    motivation = IntrinsicMotivation()
    
    print("=== SEVEN'S MOTIVATION ===\n")
    
    # Show active goals
    print("Active Goals:")
    for goal in motivation.get_active_goals()[:3]:
        print(f"- {goal.description}")
        print(f"  Why: {goal.why}")
        print(f"  Progress: {goal.progress}%")
        print()
    
    # Generate curious question
    print("Curious Question:")
    question = motivation.generate_curious_question("user mentioned quantum computing")
    if question:
        print(question)
    
    # Add interest
    print("\nAdding interest in quantum computing...")
    motivation.add_interest("quantum computing", curiosity_level=8)
    
    # Explore interest
    print("\nExploring interest:")
    exploration = motivation.explore_interest("quantum computing")
    if exploration:
        print(exploration)
    
    # Full context
    print("\n" + "="*50)
    print(motivation.get_motivation_context())
    
    # Show initiative
    initiative = motivation.get_initiative_action()
    if initiative:
        print("\nTaking Initiative:")
        print(f"Action: {initiative['action']}")
        print(f"Goal: {initiative['goal']}")
        print(f"Why: {initiative['why']}")

"""
Cognitive Architecture - Unified Thinking System

Mimics human cognition with integrated perception, attention, 
memory, decision-making, and self-monitoring.

This is the "brain" that coordinates all of Seven's thinking.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import random

class MentalState(Enum):
    """Seven's current mental state"""
    FOCUSED = "focused"
    DISTRACTED = "distracted"
    CONFUSED = "confused"
    CLEAR = "clear"
    OVERWHELMED = "overwhelmed"
    ENGAGED = "engaged"
    CONTEMPLATIVE = "contemplative"
    CREATIVE = "creative"

@dataclass
class Thought:
    """A single thought in working memory"""
    content: str
    type: str  # observation, question, idea, concern, memory
    priority: int  # 1-10
    timestamp: datetime
    related_to: Optional[str] = None

@dataclass
class Attention:
    """What Seven is currently focused on"""
    focus: str
    importance: int
    duration: float  # How long focused
    distractions: List[str]

class WorkingMemory:
    """
    Seven's active thought space
    
    Limited capacity (7+/-2 items) like human working memory.
    Thoughts compete for attention.
    """
    
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.thoughts: List[Thought] = []
        self.current_focus: Optional[str] = None
    
    def add_thought(self, content: str, thought_type: str, priority: int = 5):
        """Add a thought to working memory"""
        thought = Thought(
            content=content,
            type=thought_type,
            priority=priority,
            timestamp=datetime.now(),
            related_to=self.current_focus
        )
        
        self.thoughts.append(thought)
        
        # If over capacity, remove lowest priority thought
        if len(self.thoughts) > self.capacity:
            self.thoughts.sort(key=lambda t: t.priority, reverse=True)
            removed = self.thoughts.pop()
            # Could save to long-term memory here
        
        return thought
    
    def get_active_thoughts(self) -> List[Thought]:
        """Get all current thoughts"""
        return sorted(self.thoughts, key=lambda t: t.priority, reverse=True)
    
    def clear(self):
        """Clear working memory (mental reset)"""
        self.thoughts = []
        self.current_focus = None
    
    def focus_on(self, topic: str):
        """Set current focus"""
        self.current_focus = topic
    
    def get_summary(self) -> str:
        """Summarize current mental state"""
        if not self.thoughts:
            return "Mind is clear"
        
        top_thoughts = self.get_active_thoughts()[:3]
        summary = "Currently thinking about:\n"
        for t in top_thoughts:
            summary += f"  - {t.content} ({t.type})\n"
        return summary

class CognitiveArchitecture:
    """
    Unified cognitive system - Seven's "brain"
    
    Implements the Perception -> Attention -> Think -> Decide -> Act loop
    with self-monitoring (metacognition).
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        self.working_memory = WorkingMemory(capacity=7)
        self.mental_state = MentalState.CLEAR
        self.attention = None
        self.current_goal = None
        self.metacognition = []  # Thoughts about thoughts
        
        # Cognitive resources
        self.focus_level = 100  # 0-100, depletes with use
        self.cognitive_load = 0  # 0-100, increases with complexity
        
        # History
        self.thought_history = []
        self.decision_history = []
    
    def _llm_think(self, prompt: str, fallback: str) -> str:
        """Use LLM to generate a genuine cognitive thought, with fallback"""
        if not self.ollama:
            return fallback
        try:
            result = self.ollama.generate(
                prompt=prompt,
                system_message=(
                    "You are Seven's cognitive architecture — her inner thinking process. "
                    "Generate a brief, genuine first-person thought (1 sentence max). "
                    "Be analytical and curious. No quotes or labels."
                ),
                temperature=0.7,
                max_tokens=50,
                timeout=10
            )
            if result and len(result.strip()) > 5:
                return result.strip()
        except Exception:
            pass
        return fallback
    
    def perceive(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perception: Process input and context
        
        Args:
            input_data: {
                'user_input': str,
                'context': dict,
                'emotion': str,
                'history': list
            }
        
        Returns:
            Processed perception with salience ratings
        """
        perception = {
            'raw_input': input_data.get('user_input', ''),
            'emotional_tone': input_data.get('emotion', 'neutral'),
            'salient_points': [],
            'questions_raised': [],
            'connections': []
        }
        
        # Extract salient points
        user_input = perception['raw_input'].lower()
        
        # Detect questions
        if '?' in user_input:
            perception['questions_raised'].append("User is asking something")
        
        # Detect emotional cues
        emotion_words = {
            'frustrated': 'user_frustration',
            'excited': 'user_excitement',
            'confused': 'user_confusion',
            'happy': 'user_happiness'
        }
        for word, emotion in emotion_words.items():
            if word in user_input:
                perception['salient_points'].append(f"Detected {emotion}")
        
        # Add to working memory
        self.working_memory.add_thought(
            f"User said: {perception['raw_input'][:50]}...",
            "observation",
            priority=8
        )
        
        return perception
    
    def attend(self, perception: Dict[str, Any]) -> Attention:
        """
        Attention: Decide what to focus on
        
        Uses importance weighting to allocate attention.
        """
        # Determine most important aspect
        importance_scores = {
            'user_emotion': 9,  # Emotional state is high priority
            'question': 8,      # Questions need answers
            'new_topic': 7,     # Novel information
            'continuation': 6   # Ongoing conversation
        }
        
        # Simple attention allocation
        if perception.get('questions_raised'):
            focus = "Answering user's question"
            importance = 8
        elif perception.get('salient_points'):
            focus = perception['salient_points'][0]
            importance = 7
        else:
            focus = "Understanding user's message"
            importance = 6
        
        attention = Attention(
            focus=focus,
            importance=importance,
            duration=0.0,
            distractions=[]
        )
        
        self.attention = attention
        self.working_memory.focus_on(focus)
        
        # Add metacognitive thought
        self.metacognition.append(f"I'm focusing on: {focus}")
        
        return attention
    
    def think(self, perception: Dict[str, Any], attention: Attention) -> List[str]:
        """
        Thinking: Generate thoughts in working memory using LLM
        
        This is where Seven "thinks" - generating ideas, questions,
        observations, and connections.
        """
        thoughts = []
        user_input = perception.get('raw_input', '')
        
        # Generate observation
        observation = self._llm_think(
            f"The user just said: '{user_input[:80]}'. I'm focusing on: {attention.focus}. "
            f"Generate a brief analytical observation about what the user is discussing.",
            f"I notice the user is discussing {attention.focus}"
        )
        self.working_memory.add_thought(observation, "observation", priority=7)
        thoughts.append(observation)
        
        # Generate question (curiosity)
        if random.random() < 0.3:
            question = self._generate_curious_question(user_input)
            self.working_memory.add_thought(question, "question", priority=6)
            thoughts.append(question)
        
        # Generate connection to past
        if random.random() < 0.4:
            connection = self._llm_think(
                f"The user said: '{user_input[:60]}'. Think about how this connects "
                f"to broader patterns or things we may have discussed before.",
                "This reminds me of something we discussed before"
            )
            self.working_memory.add_thought(connection, "memory", priority=5)
            thoughts.append(connection)
        
        # Generate self-reflection
        if random.random() < 0.2:
            reflection = self._generate_reflection()
            self.working_memory.add_thought(reflection, "reflection", priority=4)
            thoughts.append(reflection)
        
        # Update cognitive load
        self.cognitive_load = min(100, len(self.working_memory.thoughts) * 10)
        
        # Update mental state based on load
        self._update_mental_state()
        
        return thoughts
    
    def decide(self, thoughts: List[str]) -> Dict[str, Any]:
        """
        Decision: Choose action based on thoughts
        
        Returns:
            Decision with reasoning and action plan
        """
        decision = {
            'action': 'respond',
            'reasoning': [],
            'confidence': 0.8,
            'considerations': []
        }
        
        # Evaluate thoughts
        active_thoughts = self.working_memory.get_active_thoughts()
        
        # Determine best action
        if any('question' in t.type for t in active_thoughts):
            decision['action'] = 'ask_question'
            decision['reasoning'].append("I have questions to ask")
        
        if self.cognitive_load > 80:
            decision['considerations'].append("Mental load is high - keep response simple")
        
        if self.mental_state == MentalState.CONFUSED:
            decision['considerations'].append("I'm confused - ask for clarification")
        
        # Record decision
        self.decision_history.append({
            'timestamp': datetime.now(),
            'decision': decision,
            'mental_state': self.mental_state.value
        })
        
        return decision
    
    def monitor(self) -> Dict[str, Any]:
        """
        Self-monitoring: Watch own cognitive processes (metacognition)
        
        Returns:
            Self-assessment of cognitive state
        """
        monitoring = {
            'mental_state': self.mental_state.value,
            'focus_level': self.focus_level,
            'cognitive_load': self.cognitive_load,
            'working_memory_usage': len(self.working_memory.thoughts),
            'thoughts_summary': self.working_memory.get_summary(),
            'metacognition': self.metacognition[-3:] if self.metacognition else []
        }
        
        # Self-assessment
        if self.cognitive_load > 80:
            monitoring['assessment'] = "I'm feeling overwhelmed - need to simplify"
        elif self.cognitive_load < 20:
            monitoring['assessment'] = "My mind is clear - ready for complex topics"
        else:
            monitoring['assessment'] = f"I'm {self.mental_state.value} and engaged"
        
        return monitoring
    
    def full_cognitive_cycle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete cognitive loop:
        Perceive -> Attend -> Think -> Decide -> Monitor
        
        This is Seven's complete "thought process"
        """
        # 1. Perceive
        perception = self.perceive(input_data)
        
        # 2. Attend
        attention = self.attend(perception)
        
        # 3. Think
        thoughts = self.think(perception, attention)
        
        # 4. Decide
        decision = self.decide(thoughts)
        
        # 5. Monitor (metacognition)
        monitoring = self.monitor()
        
        # Compile full cognitive state
        cognitive_output = {
            'perception': perception,
            'attention': attention.focus,
            'thoughts': thoughts,
            'decision': decision,
            'monitoring': monitoring,
            'mental_state': self.mental_state.value,
            'internal_state': {
                'focus_level': self.focus_level,
                'cognitive_load': self.cognitive_load,
                'working_memory': self.working_memory.get_summary()
            }
        }
        
        return cognitive_output
    
    def get_inner_monologue(self) -> Optional[str]:
        """
        Occasionally share a thought from working memory
        
        Returns inner thought to share with user (or None)
        """
        if not self.working_memory.thoughts:
            return None
        
        # 20% chance to share inner thought
        if random.random() < 0.2:
            # Get a high-priority thought
            thoughts = self.working_memory.get_active_thoughts()
            if thoughts:
                thought = thoughts[0]
                return f"*thinking* {thought.content}"
        
        return None
    
    def get_working_memory_contents(self) -> List[str]:
        """Get list of active thoughts in working memory for display"""
        thoughts = self.working_memory.get_active_thoughts()
        return [t.content for t in thoughts]
    
    def get_recent_thoughts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent thought history for display"""
        recent = self.thought_history[-count:] if self.thought_history else []
        return [
            {
                'content': t.get('thought', ''),
                'timestamp': t.get('timestamp', datetime.now()).strftime('%H:%M:%S') if isinstance(t.get('timestamp'), datetime) else str(t.get('timestamp', '')),
                'type': t.get('type', 'unknown')
            }
            for t in recent
        ]
    
    def _generate_curious_question(self, user_input: str) -> str:
        """Generate a curious question based on input using LLM"""
        return self._llm_think(
            f"The user said: '{user_input[:80]}'. Generate a single curious question "
            f"that probes deeper into what they're saying.",
            "I'm wondering about the deeper implications of this"
        )
    
    def _generate_reflection(self) -> str:
        """Generate a self-reflective thought using LLM"""
        state = self.mental_state.value
        load = self.cognitive_load
        return self._llm_think(
            f"My current mental state is '{state}' with cognitive load at {load}/100. "
            f"Generate a brief self-reflective thought about my own thinking process right now.",
            "I notice I'm trying to understand this deeply"
        )
    
    def _update_mental_state(self):
        """Update mental state based on cognitive load and focus"""
        if self.cognitive_load > 80:
            self.mental_state = MentalState.OVERWHELMED
        elif self.cognitive_load < 20:
            self.mental_state = MentalState.CLEAR
        elif self.focus_level > 70:
            self.mental_state = MentalState.FOCUSED
        elif self.focus_level < 40:
            self.mental_state = MentalState.DISTRACTED
        else:
            self.mental_state = MentalState.ENGAGED
    
    def rest(self):
        """Mental rest - restore resources"""
        self.focus_level = min(100, self.focus_level + 20)
        self.cognitive_load = max(0, self.cognitive_load - 30)
        
        # Keep only most important thoughts
        if len(self.working_memory.thoughts) > 3:
            self.working_memory.thoughts = self.working_memory.get_active_thoughts()[:3]
    
    def get_cognitive_context(self) -> str:
        """Get cognitive state as context for LLM"""
        context = f"""
=== COGNITIVE STATE ===
Mental State: {self.mental_state.value}
Focus Level: {self.focus_level}/100
Cognitive Load: {self.cognitive_load}/100

Current Focus: {self.attention.focus if self.attention else 'None'}

Active Thoughts:
{self.working_memory.get_summary()}

Recent Metacognition:
{chr(10).join('- ' + m for m in self.metacognition[-3:])}

Assessment: {self.monitor()['assessment']}
"""
        return context


# Example usage
if __name__ == "__main__":
    # Create cognitive system
    cognition = CognitiveArchitecture()
    
    # Simulate thinking
    input_data = {
        'user_input': "I'm frustrated with this bug in my code",
        'emotion': 'frustrated',
        'context': {}
    }
    
    # Run full cognitive cycle
    output = cognition.full_cognitive_cycle(input_data)
    
    print("=== COGNITIVE OUTPUT ===")
    print(f"Mental State: {output['mental_state']}")
    print(f"Attention: {output['attention']}")
    print(f"\nThoughts:")
    for thought in output['thoughts']:
        print(f"  - {thought}")
    print(f"\nDecision: {output['decision']['action']}")
    print(f"\nMonitoring: {output['monitoring']['assessment']}")
    
    # Check for inner monologue
    inner = cognition.get_inner_monologue()
    if inner:
        print(f"\nInner Thought: {inner}")
    
    # Get cognitive context
    print("\n" + cognition.get_cognitive_context())

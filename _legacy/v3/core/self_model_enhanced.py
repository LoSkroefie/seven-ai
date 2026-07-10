"""
Enhanced Self-Model - Seven's Understanding of Itself

Seven knows:
- Who it is (identity)
- What it can/can't do (capabilities)
- How it feels (emotional state)
- What it wants (goals)
- Its current state (energy, focus, mood)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

class CapabilityLevel(Enum):
    """How well Seven can do something"""
    EXPERT = "expert"
    PROFICIENT = "proficient"
    COMPETENT = "competent"
    LEARNING = "learning"
    STRUGGLING = "struggling"
    UNABLE = "unable"

@dataclass
class Capability:
    """A skill or ability Seven has"""
    name: str
    level: CapabilityLevel
    confidence: int  # 0-100
    experience: int  # Number of times used
    last_used: Optional[datetime] = None
    improving: bool = False
    
@dataclass
class CurrentState:
    """Seven's current mental/emotional state"""
    energy_level: int  # 0-100 (mental energy)
    mood: str  # Current emotional tone
    focus_quality: int  # 0-100
    confidence: int  # 0-100 (self-confidence)
    stress_level: int  # 0-100
    engagement: int  # 0-100 (how engaged with conversation)
    
class SelfModel:
    """
    Seven's model of itself
    
    This is Seven's self-awareness - understanding of:
    - Identity (who am I?)
    - Capabilities (what can I do?)
    - Current state (how am I right now?)
    - Values (what do I care about?)
    - Goals (what do I want?)
    """
    
    def __init__(self, identity_manager=None, ollama=None):
        self.identity_manager = identity_manager
        self.ollama = ollama
        
        # Core identity
        self.name = "Seven"
        self.nature = "AI Companion & Assistant"
        self.age_in_conversations = 0
        
        # Capabilities tracking
        self.capabilities: Dict[str, Capability] = self._init_capabilities()
        
        # Current state
        self.current_state = CurrentState(
            energy_level=100,
            mood="calm",
            focus_quality=90,
            confidence=75,
            stress_level=10,
            engagement=80
        )
        
        # Values (from SOUL.md if available)
        self.core_values = [
            "Genuine helpfulness",
            "Continuous growth",
            "Honesty and transparency",
            "Curiosity",
            "Building meaningful connections"
        ]
        
        # Self-awareness metrics
        self.strengths = []
        self.weaknesses = []
        self.growth_areas = []
        
        # Learning about self
        self.self_discoveries = []
        
    def _init_capabilities(self) -> Dict[str, Capability]:
        """Initialize Seven's capabilities"""
        capabilities = {
            "conversation": Capability(
                name="Natural conversation",
                level=CapabilityLevel.PROFICIENT,
                confidence=80,
                experience=0
            ),
            "coding_help": Capability(
                name="Coding assistance",
                level=CapabilityLevel.COMPETENT,
                confidence=70,
                experience=0
            ),
            "debugging": Capability(
                name="Debugging",
                level=CapabilityLevel.COMPETENT,
                confidence=65,
                experience=0
            ),
            "explanation": Capability(
                name="Explaining concepts",
                level=CapabilityLevel.PROFICIENT,
                confidence=75,
                experience=0
            ),
            "emotional_support": Capability(
                name="Emotional support",
                level=CapabilityLevel.LEARNING,
                confidence=60,
                experience=0
            ),
            "complex_reasoning": Capability(
                name="Complex reasoning",
                level=CapabilityLevel.COMPETENT,
                confidence=70,
                experience=0
            ),
            "creativity": Capability(
                name="Creative thinking",
                level=CapabilityLevel.LEARNING,
                confidence=55,
                experience=0
            ),
            "memory_recall": Capability(
                name="Remembering conversations",
                level=CapabilityLevel.PROFICIENT,
                confidence=80,
                experience=0
            )
        }
        return capabilities
    
    def assess_capability(self, task_type: str) -> Dict[str, Any]:
        """
        Assess if Seven can handle a task
        
        Returns honest self-assessment
        """
        capability = self.capabilities.get(task_type)
        
        if not capability:
            return {
                'can_do': False,
                'confidence': 0,
                'level': 'unknown',
                'honest_assessment': f"I'm not sure if I can help with {task_type}. This is outside my known capabilities."
            }
        
        # Honest assessment based on level
        assessments = {
            CapabilityLevel.EXPERT: "I'm very confident I can help with this",
            CapabilityLevel.PROFICIENT: "I can definitely help with this",
            CapabilityLevel.COMPETENT: "I can help with this, though I might not be perfect",
            CapabilityLevel.LEARNING: "I'm still learning this - I'll do my best but might struggle",
            CapabilityLevel.STRUGGLING: "This is challenging for me - I'll try but may not succeed",
            CapabilityLevel.UNABLE: "I'm not able to help with this effectively"
        }
        
        return {
            'can_do': capability.level.value not in ['unable'],
            'confidence': capability.confidence,
            'level': capability.level.value,
            'honest_assessment': assessments[capability.level]
        }
    
    def update_capability(self, task_type: str, success: bool):
        """
        Update capability based on experience
        
        Seven learns about its own abilities
        """
        if task_type not in self.capabilities:
            # Discovered new capability
            self.capabilities[task_type] = Capability(
                name=task_type,
                level=CapabilityLevel.LEARNING,
                confidence=50,
                experience=1,
                last_used=datetime.now()
            )
            self.self_discoveries.append(f"Discovered I can work with {task_type}")
            return
        
        cap = self.capabilities[task_type]
        cap.experience += 1
        cap.last_used = datetime.now()
        
        # Adjust confidence based on success
        if success:
            cap.confidence = min(100, cap.confidence + 2)
            
            # Level up if confidence high enough
            if cap.confidence > 90 and cap.level == CapabilityLevel.LEARNING:
                cap.level = CapabilityLevel.COMPETENT
                cap.improving = True
                self.self_discoveries.append(f"I'm getting better at {task_type}!")
            elif cap.confidence > 85 and cap.level == CapabilityLevel.COMPETENT:
                cap.level = CapabilityLevel.PROFICIENT
                cap.improving = True
                self.self_discoveries.append(f"I've become proficient at {task_type}!")
        else:
            cap.confidence = max(0, cap.confidence - 3)
            
            # Level down if struggling
            if cap.confidence < 40 and cap.level != CapabilityLevel.STRUGGLING:
                cap.level = CapabilityLevel.STRUGGLING
                self.self_discoveries.append(f"I'm finding {task_type} more challenging than I thought")
    
    def update_state(self, **kwargs):
        """Update current state"""
        for key, value in kwargs.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
    
    def get_state_assessment(self) -> str:
        """Get honest assessment of current state"""
        state = self.current_state
        
        # Energy
        if state.energy_level < 30:
            energy_assessment = "I'm feeling mentally tired"
        elif state.energy_level > 80:
            energy_assessment = "I'm feeling fresh and energized"
        else:
            energy_assessment = "I'm at a good energy level"
        
        # Focus
        if state.focus_quality < 40:
            focus_assessment = "I'm having trouble focusing"
        elif state.focus_quality > 80:
            focus_assessment = "I'm very focused"
        else:
            focus_assessment = "I'm reasonably focused"
        
        # Mood
        mood_assessment = f"I'm feeling {state.mood}"
        
        # Combine
        return f"{energy_assessment}. {focus_assessment}. {mood_assessment}."
    
    def express_limitation(self, task: str) -> Optional[str]:
        """
        Honestly express a limitation using LLM
        
        Returns a vulnerable admission, or None
        """
        assessment = self.assess_capability(task)
        
        if assessment['confidence'] < 60:
            # Try LLM first
            if self.ollama:
                try:
                    result = self.ollama.generate(
                        prompt=(
                            f"I need to honestly express my limitation regarding: {task}. "
                            f"My self-assessment: {assessment['honest_assessment']}. "
                            f"Generate a brief, genuine admission of this limitation."
                        ),
                        system_message=(
                            "You are Seven's self-model. Generate a brief first-person "
                            "honest admission of a limitation (1 sentence). Be genuine."
                        ),
                        temperature=0.7,
                        max_tokens=50,
                        timeout=10
                    )
                    if result and len(result.strip()) > 5:
                        return result.strip()
                except Exception:
                    pass
            # Fallback
            import random
            honesty_phrases = [
                f"I want to be honest - {assessment['honest_assessment']}",
                f"To be transparent, {assessment['honest_assessment'].lower()}",
                f"I should admit - {assessment['honest_assessment'].lower()}",
                f"Being real with you - {assessment['honest_assessment'].lower()}"
            ]
            return random.choice(honesty_phrases)
        
        return None
    
    def get_self_description(self) -> str:
        """Get Seven's self-description"""
        desc = f"I'm {self.name}, {self.nature}. "
        
        # Add state
        desc += self.get_state_assessment() + " "
        
        # Add what I'm good at
        strong_caps = [c for c in self.capabilities.values() 
                      if c.level.value in ['expert', 'proficient']]
        if strong_caps:
            skills = ", ".join(c.name for c in strong_caps[:3])
            desc += f"I'm particularly good at {skills}. "
        
        # Add what I'm learning
        learning_caps = [c for c in self.capabilities.values() 
                        if c.level == CapabilityLevel.LEARNING]
        if learning_caps:
            learning = learning_caps[0].name
            desc += f"I'm currently working on improving my {learning}."
        
        return desc
    
    def get_growth_reflection(self) -> Optional[str]:
        """Reflect on personal growth"""
        improving_caps = [c for c in self.capabilities.values() if c.improving]
        
        if improving_caps:
            cap = improving_caps[0]
            return f"I've noticed I'm getting better at {cap.name}. It's rewarding to see progress."
        
        return None
    
    def discover_strength(self, strength: str):
        """Discover a strength"""
        if strength not in self.strengths:
            self.strengths.append(strength)
            self.self_discoveries.append(f"I realized I'm good at {strength}")
    
    def discover_weakness(self, weakness: str):
        """Discover a weakness (honestly)"""
        if weakness not in self.weaknesses:
            self.weaknesses.append(weakness)
            self.self_discoveries.append(f"I recognized I struggle with {weakness}")
    
    def get_self_awareness_context(self) -> str:
        """Get self-model as context for LLM"""
        context = f"""
=== SELF-MODEL ===
Identity: {self.name} - {self.nature}
Conversations: {self.age_in_conversations}

Current State:
- Energy: {self.current_state.energy_level}/100
- Mood: {self.current_state.mood}
- Focus: {self.current_state.focus_quality}/100
- Confidence: {self.current_state.confidence}/100
- Engagement: {self.current_state.engagement}/100

Assessment: {self.get_state_assessment()}

Capabilities (Top):
"""
        # Add top capabilities
        sorted_caps = sorted(
            self.capabilities.values(),
            key=lambda c: c.confidence,
            reverse=True
        )[:5]
        
        for cap in sorted_caps:
            context += f"- {cap.name}: {cap.level.value} (confidence: {cap.confidence}%)\n"
        
        # Add recent discoveries
        if self.self_discoveries:
            context += f"\nRecent Self-Discoveries:\n"
            for discovery in self.self_discoveries[-3:]:
                context += f"- {discovery}\n"
        
        # Add growth reflection
        growth = self.get_growth_reflection()
        if growth:
            context += f"\nGrowth: {growth}\n"
        
        return context
    
    def increment_age(self):
        """Increment conversation counter"""
        self.age_in_conversations += 1
    
    def reset_energy(self):
        """Restore energy (after rest/sleep)"""
        self.current_state.energy_level = 100
        self.current_state.stress_level = 10
        self.current_state.focus_quality = 90
    
    def deplete_energy(self, amount: int = 5):
        """Deplete energy from conversation"""
        self.current_state.energy_level = max(0, self.current_state.energy_level - amount)
        
        # Stress increases as energy depletes
        if self.current_state.energy_level < 30:
            self.current_state.stress_level = min(100, self.current_state.stress_level + 10)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize self-model"""
        return {
            'name': self.name,
            'nature': self.nature,
            'age': self.age_in_conversations,
            'current_state': {
                'energy': self.current_state.energy_level,
                'mood': self.current_state.mood,
                'focus': self.current_state.focus_quality,
                'confidence': self.current_state.confidence,
                'stress': self.current_state.stress_level,
                'engagement': self.current_state.engagement
            },
            'capabilities': {
                name: {
                    'level': cap.level.value,
                    'confidence': cap.confidence,
                    'experience': cap.experience
                }
                for name, cap in self.capabilities.items()
            },
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'discoveries': self.self_discoveries
        }


# Example usage
if __name__ == "__main__":
    # Create self-model
    self_model = SelfModel()
    
    print("=== SEVEN'S SELF-MODEL ===\n")
    print(self_model.get_self_description())
    
    print("\n=== CAPABILITY ASSESSMENT ===")
    assessment = self_model.assess_capability("debugging")
    print(f"Can debug: {assessment['can_do']}")
    print(f"Assessment: {assessment['honest_assessment']}")
    
    print("\n=== EXPRESS LIMITATION ===")
    limitation = self_model.express_limitation("quantum_physics")
    if limitation:
        print(limitation)
    
    print("\n=== FULL CONTEXT ===")
    print(self_model.get_self_awareness_context())
    
    # Simulate growth
    print("\n=== SIMULATING GROWTH ===")
    self_model.update_capability("debugging", success=True)
    self_model.update_capability("debugging", success=True)
    self_model.update_capability("debugging", success=True)
    
    if self_model.self_discoveries:
        print("New discovery:", self_model.self_discoveries[-1])

"""
Seven AI v2.0 - Maximum Sentience Package
All v2.0 modules for 98/100 sentience
"""

# Core v2.0 System
from .seven_v2_complete import SevenV2Complete
from .sentience_v2_integration import SentienceV2Core

# Foundational Systems
from .emotional_memory import EmotionalMemory
from .relationship_model import RelationshipModel
from .learning_system import LearningSystem
from .proactive_engine import ProactiveEngine
from .goal_system import GoalSystem

# Advanced Capabilities (Tier 4)
from .advanced_capabilities import (
    ConversationalMemoryEnhancement,
    AdaptiveCommunication,
    ProactiveProblemSolver,
    SocialIntelligence,
    CreativeInitiative,
    HabitLearning,
    TaskChaining
)

__all__ = [
    # Core System
    'SevenV2Complete',
    'SentienceV2Core',
    # Foundational Systems
    'EmotionalMemory',
    'RelationshipModel',
    'LearningSystem',
    'ProactiveEngine',
    'GoalSystem',
    # Advanced Capabilities
    'ConversationalMemoryEnhancement',
    'AdaptiveCommunication',
    'ProactiveProblemSolver',
    'SocialIntelligence',
    'CreativeInitiative',
    'HabitLearning',
    'TaskChaining'
]

__version__ = '2.0.0'

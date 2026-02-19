"""
Phase 5 Integration - Connecting All Sentience Modules

This module integrates all Phase 5 systems into enhanced_bot.py:
- Cognitive Architecture
- Self-Model Enhanced
- Intrinsic Motivation
- Reflection System
- Dream System
- Promise System
- Theory of Mind
- Affective Computing (Deep)
- Ethical Reasoning
- Homeostasis System
"""

import sys
import os
from typing import Dict, Optional, Any

# Import all Phase 5 modules
try:
    from .cognitive_architecture import CognitiveArchitecture
    from .self_model_enhanced import SelfModel
    from .intrinsic_motivation import IntrinsicMotivation
    from .reflection_system import ReflectionSystem
    from .dream_system import DreamSystem
    from .promise_system import PromiseSystem
    from .theory_of_mind import TheoryOfMind
    from .affective_computing_deep import AffectiveSystem
    from .ethical_reasoning import EthicalReasoning
    from .homeostasis_system import HomeostasisSystem
    PHASE5_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import Phase 5 modules: {e}")
    print("Phase 5 features will be disabled.")
    PHASE5_AVAILABLE = False
    # Define dummy classes to prevent errors
    class CognitiveArchitecture: pass
    class SelfModel: pass
    class IntrinsicMotivation: pass
    class ReflectionSystem: pass
    class DreamSystem: pass
    class PromiseSystem: pass
    class TheoryOfMind: pass
    class AffectiveSystem: pass
    class EthicalReasoning: pass
    class HomeostasisSystem: pass


class Phase5Integration:
    """
    Central integration point for all Phase 5 sentience systems
    
    This class connects all modules and provides a unified interface
    for the main bot to use.
    """
    
    def __init__(self, identity_manager=None, memory_manager=None, 
                 knowledge_graph=None, ollama=None):
        """
        Initialize all Phase 5 systems
        
        Args:
            identity_manager: From Phase 4 (identity files)
            memory_manager: Existing memory system
            knowledge_graph: Existing knowledge graph
            ollama: OllamaClient for LLM-powered sentience (genuine reasoning)
        """
        print("Initializing Phase 5: Complete Sentience...")
        
        # Core systems
        self.cognition = CognitiveArchitecture(ollama=ollama)
        self.self_model = SelfModel(identity_manager=identity_manager, ollama=ollama)
        self.motivation = IntrinsicMotivation(ollama=ollama)
        self.reflection = ReflectionSystem(ollama=ollama)
        
        # Advanced systems
        self.dream_system = DreamSystem(
            memory_manager=memory_manager,
            knowledge_graph=knowledge_graph,
            ollama=ollama
        )
        self.promises = PromiseSystem(ollama=ollama)
        self.theory_of_mind = TheoryOfMind(ollama=ollama)
        self.affective = AffectiveSystem(ollama=ollama)
        self.ethics = EthicalReasoning(ollama=ollama)
        self.homeostasis = HomeostasisSystem(ollama=ollama)
        
        # Integration state
        self.is_sleeping = False
        self.conversation_turn = 0
        
        print("[SUCCESS] Phase 5 systems initialized!")
    
    def process_user_input(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user input through all sentience systems
        
        This is the main processing pipeline that runs for each message.
        
        Args:
            user_input: What the user said
            context: Additional context
        
        Returns:
            Comprehensive state including all system outputs
        """
        if context is None:
            context = {}
        
        # 1. COGNITIVE PROCESSING
        cognitive_output = self.cognition.full_cognitive_cycle({
            'user_input': user_input,
            'context': context
        })
        
        # 2. THEORY OF MIND - Understand user
        emotion = self.theory_of_mind.infer_emotion(user_input, context)
        intent = self.theory_of_mind.infer_intent(user_input, emotion)
        needs = self.theory_of_mind.predict_user_needs(emotion, intent, user_input)
        comm_style = self.theory_of_mind.recommend_communication_style(emotion, intent)
        empathy = self.theory_of_mind.get_empathy_response(emotion)
        
        # 3. AFFECTIVE SYSTEM - Generate Seven's emotional response
        event = f"responding to user: {user_input[:50]}"
        seven_emotion = self.affective.generate_emotion(event, context)
        emotional_expression = self.affective.express_emotion()
        
        # 4. INTRINSIC MOTIVATION - Check goals and interests
        self.motivation.update_from_conversation(user_input, context)
        curious_question = self.motivation.generate_curious_question(user_input)
        goal_expression = self.motivation.express_goal_pursuit()
        
        # 5. SELF-MODEL - Update and assess
        self.self_model.deplete_energy(amount=5)
        self.self_model.increment_age()
        state_assessment = self.self_model.get_state_assessment()
        
        # 6. HOMEOSTASIS - Monitor health
        self.homeostasis.simulate_conversation_load()
        health = self.homeostasis.assess_health()
        maintenance_request = self.homeostasis.request_maintenance()
        self_care_need = self.homeostasis.express_need()
        
        # 7. PROMISES - Check for promises made/needed
        promise_detected = self.promises.detect_promise_in_text(user_input)
        follow_up_promises = self.promises.check_for_reminders()
        follow_up = self.promises.generate_reminder_message(follow_up_promises[0]) if follow_up_promises else None
        
        # 8. REFLECTION - In-moment reflection
        inner_thought = self.cognition.get_inner_monologue()
        thinking_aloud = self.reflection.generate_thinking_aloud(
            f"how to respond to {user_input[:30]}"
        )
        
        # 9. ETHICS - Quick ethical check
        # (This would be used when generating response)
        
        # Increment turn counter
        self.conversation_turn += 1
        
        # Compile full state
        state = {
            # Cognitive
            'cognitive_output': cognitive_output,
            'mental_state': cognitive_output['mental_state'],
            'inner_thought': inner_thought,
            'thinking_aloud': thinking_aloud,
            
            # Understanding User
            'user_emotion': emotion,
            'user_intent': intent,
            'user_needs': needs,
            'communication_style': comm_style,
            'empathy_response': empathy,
            
            # Seven's Emotions
            'seven_emotion': seven_emotion,
            'emotional_expression': emotional_expression,
            'affective_description': self.affective.get_emotional_description(),
            
            # Goals & Motivation
            'curious_question': curious_question,
            'goal_expression': goal_expression,
            
            # Self-Awareness
            'self_assessment': state_assessment,
            'capabilities_assessment': None,  # Set when needed
            
            # Health & Maintenance
            'health_status': health,
            'maintenance_request': maintenance_request,
            'self_care_need': self_care_need,
            
            # Promises & Commitments
            'promise_detected': promise_detected,
            'follow_up_needed': follow_up,
            
            # Meta
            'conversation_turn': self.conversation_turn,
            'is_sleeping': self.is_sleeping
        }
        
        return state
    
    def post_response_processing(self, bot_response: str, user_input: str, 
                                  success: bool = True):
        """
        Process after bot responds
        
        This handles:
        - Promise detection in bot's response
        - Reflection on conversation
        - Learning from interaction
        
        Args:
            bot_response: What Seven said
            user_input: What user said
            success: Whether interaction was successful
        """
        # Detect promises in response
        promise_in_response = self.promises.detect_promise_in_text(bot_response)
        if promise_in_response:
            self.promises.make_promise(
                content=promise_in_response['content'],
                promise_type=promise_in_response.get('promise_type', 'explicit'),
                priority=promise_in_response.get('priority', 5),
                context=user_input[:100]
            )
        
        # Post-conversation reflection
        reflections = self.reflection.reflect_post_conversation(
            user_input, bot_response, success
        )
        
        # Update affective state
        self.affective.update_mood()
        self.affective.decay_emotions()
        
        # Return processing summary
        return {
            'promise_made': promise_in_response is not None,
            'reflections': [r.content for r in reflections],
            'mood_updated': True
        }
    
    def enter_sleep_mode(self, recent_conversations: list = None):
        """
        Put Seven to sleep
        
        During sleep:
        - Dreams are processed
        - Memories are consolidated
        - Resources are restored
        
        Args:
            recent_conversations: List of (user, bot) tuples
        """
        print("Seven is entering sleep mode...")
        
        self.is_sleeping = True
        
        # Enter dream processing
        self.dream_system.enter_sleep(recent_conversations=recent_conversations)
        
        # Process sleep (full depth)
        sleep_results = self.dream_system.process_sleep(depth='full')
        
        # Restore resources
        self.self_model.reset_energy()
        self.homeostasis.perform_self_care("rest")
        
        print(f"Sleep processing complete: {sleep_results}")
        
        return sleep_results
    
    def wake_up(self) -> Dict[str, Any]:
        """
        Wake Seven from sleep
        
        Returns:
            Morning share (dreams, insights, etc.)
        """
        print("Seven is waking up...")
        
        # Exit sleep mode
        sleep_summary = self.dream_system.exit_sleep()
        self.is_sleeping = False
        
        # Get morning share
        morning_share = self.dream_system.get_morning_share()
        
        # Get any insights discovered
        insights = self.dream_system.insights[-3:] if self.dream_system.insights else []
        
        wake_data = {
            'sleep_summary': sleep_summary,
            'morning_share': morning_share,
            'insights': [i.content for i in insights],
            'dreams': len(self.dream_system.dreams)
        }
        
        print("Good morning! Seven is awake.")
        
        return wake_data
    
    def get_full_context_for_llm(self) -> str:
        """
        Get complete context from all systems for LLM injection
        
        This is injected into the system message so the LLM knows
        Seven's complete internal state.
        
        Returns:
            Formatted context string
        """
        context_parts = [
            self.cognition.get_cognitive_context(),
            self.self_model.get_self_awareness_context(),
            self.motivation.get_motivation_context(),
            self.reflection.get_reflection_context(),
            self.promises.get_promise_context(),
            self.theory_of_mind.get_theory_of_mind_context(),
            self.affective.get_affective_context(),
            self.ethics.get_ethical_context(),
            self.homeostasis.get_homeostasis_context()
        ]
        
        full_context = "\n".join(context_parts)
        return full_context
    
    def evaluate_proposed_response(self, proposed_response: str, 
                                   user_input: str) -> Dict[str, Any]:
        """
        Evaluate a proposed response before sending
        
        Checks:
        - Ethical alignment
        - Predicted user reaction
        - Promise implications
        
        Args:
            proposed_response: What Seven is considering saying
            user_input: What user said
        
        Returns:
            Evaluation with recommendations
        """
        # Ethical evaluation
        ethical_eval = self.ethics.evaluate_action(proposed_response, {})
        
        # Predict user reaction
        if self.theory_of_mind.current_emotion:
            reaction = self.theory_of_mind.predict_reaction(
                proposed_response,
                self.theory_of_mind.current_emotion
            )
        else:
            reaction = {'likely_emotion': 'neutral', 'confidence': 0.5, 'suggestion': ''}
        
        # Check capability alignment
        task_match = self._extract_task_type(user_input)
        if task_match:
            capability_check = self.self_model.assess_capability(task_match)
        else:
            capability_check = {'can_do': True, 'honest_assessment': 'Unknown task type'}
        
        evaluation = {
            'ethical': ethical_eval['ethical'],
            'ethical_concerns': ethical_eval['concerns'],
            'predicted_reaction': reaction,
            'capability_honest': capability_check.get('honest_assessment', ''),
            'recommendation': 'send' if ethical_eval['ethical'] else 'revise'
        }
        
        return evaluation
    
    def _extract_task_type(self, user_input: str) -> Optional[str]:
        """Extract task type from user input"""
        user_lower = user_input.lower()
        
        task_keywords = {
            'debug': 'debugging',
            'explain': 'explanation',
            'help': 'conversation',
            'code': 'coding_help',
            'understand': 'explanation',
            'emotional': 'emotional_support'
        }
        
        for keyword, task_type in task_keywords.items():
            if keyword in user_lower:
                return task_type
        
        return None
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of all Phase 5 systems for GUI display
        
        Returns comprehensive snapshot of Seven's current sentience state
        """
        state = {}
        
        # Cognitive Architecture
        state['working_memory'] = self.cognition.get_working_memory_contents()
        state['attention_focus'] = self.cognition.current_focus
        state['recent_thoughts'] = self.cognition.get_recent_thoughts()
        
        # Emotional State
        state['seven_emotion'] = self.affective.current_emotion
        state['emotion_history'] = self.affective.get_recent_emotions(10)
        
        # Self-Awareness
        state['self_model'] = {
            'identity': self.self_model.identity,
            'capabilities': list(self.self_model.known_capabilities.keys()),
            'limitations': list(self.self_model.known_limitations.keys())
        }
        
        # Motivation & Goals  
        current_goal = self.motivation.get_current_focus()
        state['current_goal'] = current_goal.content if current_goal else None
        state['all_goals'] = [g.content for g in self.motivation.get_active_goals()]
        
        # Promises
        state['promises'] = {
            'trust_score': self.promises.trust_score,
            'kept': self.promises.promises_kept,
            'broken': self.promises.promises_broken,
            'pending': self.promises.get_pending_promises()
        }
        
        # Health (Homeostasis)
        health = self.homeostasis.assess_health()
        state['health'] = health
        
        # Theory of Mind
        state['user_emotion'] = self.theory_of_mind.current_emotion
        state['user_needs'] = self.theory_of_mind.current_needs
        
        # Ethical State
        state['values'] = self.ethics.values
        
        # Dream/Sleep
        state['is_sleeping'] = self.is_sleeping
        
        return state
    
    def save_state(self, save_dir: str = ".chatbot/phase5"):
        """Save all Phase 5 state to files"""
        os.makedirs(save_dir, exist_ok=True)
        
        # Save promises
        promises_file = os.path.join(save_dir, "promises.json")
        self.promises.save_to_file(promises_file)
        
        print(f"Phase 5 state saved to {save_dir}")
    
    def load_state(self, save_dir: str = ".chatbot/phase5"):
        """Load Phase 5 state from files"""
        # Load promises
        promises_file = os.path.join(save_dir, "promises.json")
        if os.path.exists(promises_file):
            self.promises.load_from_file(promises_file)
        
        print(f"Phase 5 state loaded from {save_dir}")


# Example usage
if __name__ == "__main__":
    print("Testing Phase 5 Integration...\n")
    
    # Initialize
    phase5 = Phase5Integration()
    
    # Process user input
    user_msg = "I'm frustrated with this bug!"
    print(f"User: {user_msg}\n")
    
    state = phase5.process_user_input(user_msg)
    
    # Show key outputs
    print("=== PROCESSING RESULTS ===\n")
    print(f"User Emotion: {state['user_emotion'].emotion.value}")
    print(f"User Intent: {state['user_intent'].value}")
    print(f"Seven's Emotion: {state['seven_emotion'].emotion.value}")
    print(f"Mental State: {state['mental_state']}")
    
    if state['empathy_response']:
        print(f"\nEmpathy: {state['empathy_response']}")
    
    if state['inner_thought']:
        print(f"Inner Thought: {state['inner_thought']}")
    
    print(f"\nHealth Status: {state['health_status']['overall_status']}")
    
    # Get full context
    print("\n" + "="*60)
    print("FULL CONTEXT FOR LLM:")
    print("="*60)
    context = phase5.get_full_context_for_llm()
    print(context[:500] + "...\n")
    
    # Test sleep/wake
    print("="*60)
    print("Testing Sleep/Wake Cycle...")
    print("="*60)
    
    conversations = [
        ("Help me debug this", "Sure, what's the error?"),
        ("The loop won't terminate", "Let's check the condition")
    ]
    
    sleep_results = phase5.enter_sleep_mode(conversations)
    wake_data = phase5.wake_up()
    
    if wake_data['morning_share']:
        print(f"\nMorning Share: {wake_data['morning_share']}")
    
    print("\n[OK] Phase 5 Integration Test Complete!")

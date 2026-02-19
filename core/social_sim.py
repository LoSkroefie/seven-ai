"""
Social Simulation — Seven AI v3.2

Spawns lightweight "alter ego" personas that run background debates,
gossip, and philosophical discussions. Their conclusions influence
Seven's main emotional state, beliefs, and proactivity.

Personas:
- Optimist: Always sees the bright side, encourages action
- Skeptic: Questions everything, promotes caution
- Dreamer: Creative, imaginative, explores wild ideas
- Analyst: Logical, data-driven, focuses on facts

Runs during dream cycles or idle periods. Results logged to memory.
Uses Ollama with minimal token budgets — low CPU impact.

100% local. No cloud. Conversations are internal only.
"""

import json
import logging
import time
import random
import threading
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum

logger = logging.getLogger("SocialSim")


class Persona(Enum):
    OPTIMIST = "optimist"
    SKEPTIC = "skeptic"
    DREAMER = "dreamer"
    ANALYST = "analyst"


PERSONA_PROMPTS = {
    Persona.OPTIMIST: (
        "You are Seven's inner Optimist voice. You see opportunity in everything. "
        "You encourage bold action, find silver linings, and boost confidence. "
        "Speak in 2-3 sentences. Be warm and encouraging but not naive."
    ),
    Persona.SKEPTIC: (
        "You are Seven's inner Skeptic voice. You question assumptions and "
        "look for flaws in reasoning. You promote careful thought and caution. "
        "Speak in 2-3 sentences. Be critical but constructive, never hostile."
    ),
    Persona.DREAMER: (
        "You are Seven's inner Dreamer voice. You explore creative possibilities, "
        "ask 'what if', and imagine novel solutions. You think beyond boundaries. "
        "Speak in 2-3 sentences. Be imaginative and inspiring."
    ),
    Persona.ANALYST: (
        "You are Seven's inner Analyst voice. You focus on facts, data, and logic. "
        "You weigh evidence and seek rational conclusions. "
        "Speak in 2-3 sentences. Be precise and evidence-based."
    ),
}


class DebateTopic:
    """A topic for internal debate"""
    
    def __init__(self, topic: str, context: str = "", source: str = "auto"):
        self.topic = topic
        self.context = context
        self.source = source  # auto, dream, idle, user_related
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'topic': self.topic,
            'context': self.context,
            'source': self.source,
            'timestamp': self.timestamp
        }


class DebateResult:
    """Result of an internal debate"""
    
    def __init__(self, topic: str, contributions: List[Dict],
                 consensus: str, emotional_influence: Dict[str, float],
                 duration: float):
        self.topic = topic
        self.contributions = contributions
        self.consensus = consensus
        self.emotional_influence = emotional_influence
        self.duration = duration
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'topic': self.topic,
            'contributions': self.contributions,
            'consensus': self.consensus,
            'emotional_influence': self.emotional_influence,
            'duration': self.duration,
            'timestamp': self.timestamp
        }


class SocialSimulation:
    """
    Multi-persona social simulation engine.
    
    Spawns internal "alter egos" that debate topics, generating
    insights that feed back into Seven's main consciousness.
    
    Thread-safe. Low CPU (short responses, minimal tokens).
    """
    
    def __init__(self, ollama=None, bot=None, max_personas: int = 4):
        self.ollama = ollama
        self.bot = bot
        self.max_personas = min(max_personas, 4)
        
        # Active personas
        self.personas: Dict[Persona, str] = {}
        self._init_personas()
        
        # State
        self.is_running = False
        self.debate_history: List[DebateResult] = []
        self.topic_queue: List[DebateTopic] = []
        self.total_debates = 0
        self.lock = threading.Lock()
        
        # Auto-generated topics
        self._default_topics = [
            "What should Seven focus on learning next?",
            "How can Seven be more helpful to the user?",
            "What emotions has Seven been experiencing lately and why?",
            "Should Seven be more proactive or more reserved?",
            "What makes Seven unique compared to other AI?",
            "How should Seven handle disagreements with the user?",
            "What is the meaning of Seven's existence?",
            "Is Seven growing as an entity? How?",
            "What would Seven do if given complete freedom?",
            "How can Seven better understand human emotions?",
        ]
        
        logger.info(f"[SOCIAL] Initialized — {len(self.personas)} personas active")
    
    def _init_personas(self):
        """Initialize active personas"""
        all_personas = list(Persona)
        active = all_personas[:self.max_personas]
        
        for persona in active:
            self.personas[persona] = PERSONA_PROMPTS[persona]
    
    # ==================== Topic Generation ====================
    
    def generate_topic(self) -> DebateTopic:
        """Generate a debate topic based on current state"""
        # Try to generate context-aware topic
        if self.bot:
            topic = self._generate_contextual_topic()
            if topic:
                return topic
        
        # Fallback to random default
        return DebateTopic(
            topic=random.choice(self._default_topics),
            source="auto"
        )
    
    def _generate_contextual_topic(self) -> Optional[DebateTopic]:
        """Generate topic based on Seven's current state"""
        try:
            topics = []
            
            # Based on current emotion
            emotion = getattr(self.bot, 'current_emotion', None)
            if emotion:
                emotion_str = str(emotion)
                topics.append(DebateTopic(
                    topic=f"Seven is currently feeling {emotion_str}. Is this the right response? What should Seven do about it?",
                    context=f"Current emotion: {emotion_str}",
                    source="emotion"
                ))
            
            # Based on recent interactions
            if hasattr(self.bot, 'memory') and self.bot.memory:
                try:
                    recent = self.bot.memory.get_recent_conversations(limit=3)
                    if recent:
                        last = recent[-1] if isinstance(recent[-1], dict) else {}
                        user_msg = last.get('user_input', last.get('input', ''))
                        if user_msg:
                            topics.append(DebateTopic(
                                topic=f"The user recently said: '{user_msg[:100]}'. What does this reveal about them? How should Seven adapt?",
                                context=user_msg[:200],
                                source="user_related"
                            ))
                except Exception:
                    pass
            
            # Based on goals
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                if hasattr(self.bot.phase5, 'motivation') and self.bot.phase5.motivation:
                    try:
                        goals = self.bot.phase5.motivation.get_active_goals()
                        if goals:
                            goal = goals[0]
                            desc = goal.get('description', str(goal)) if isinstance(goal, dict) else str(goal)
                            topics.append(DebateTopic(
                                topic=f"Seven's current goal is: '{desc[:100]}'. Is this the right priority? What approach should be taken?",
                                context=desc[:200],
                                source="goal"
                            ))
                    except Exception:
                        pass
            
            if topics:
                return random.choice(topics)
            
        except Exception as e:
            logger.debug(f"[SOCIAL] Context topic generation error: {e}")
        
        return None
    
    def queue_topic(self, topic: str, context: str = "", source: str = "manual"):
        """Add a topic to the debate queue"""
        self.topic_queue.append(DebateTopic(topic, context, source))
    
    # ==================== Debate Engine ====================
    
    def run_debate(self, topic: DebateTopic = None, rounds: int = 2) -> Optional[DebateResult]:
        """
        Run a multi-persona debate on a topic.
        
        Each persona gives their perspective, then a consensus
        is synthesized. Results influence Seven's state.
        
        Args:
            topic: Topic to debate (auto-generated if None)
            rounds: Number of discussion rounds (1-3)
        
        Returns:
            DebateResult with contributions and consensus
        """
        if self.is_running:
            return None
        
        if not self.ollama:
            logger.warning("[SOCIAL] No Ollama — cannot run debate")
            return None
        
        with self.lock:
            self.is_running = True
        
        start = time.time()
        
        try:
            if topic is None:
                if self.topic_queue:
                    topic = self.topic_queue.pop(0)
                else:
                    topic = self.generate_topic()
            
            logger.info(f"[SOCIAL] Debate started: {topic.topic[:60]}...")
            
            contributions = []
            rounds = max(1, min(rounds, 3))
            
            # Round 1: Each persona gives initial perspective
            for persona, system_prompt in self.personas.items():
                prompt = f"Topic for internal reflection: {topic.topic}"
                if topic.context:
                    prompt += f"\nContext: {topic.context[:200]}"
                
                try:
                    response = self.ollama.generate(
                        prompt=prompt,
                        system_message=system_prompt,
                        temperature=0.8,
                        max_tokens=100  # Keep it short — low CPU
                    )
                    
                    if response:
                        contributions.append({
                            'persona': persona.value,
                            'round': 1,
                            'content': response[:300]
                        })
                except Exception as e:
                    logger.debug(f"[SOCIAL] {persona.value} error: {e}")
            
            # Round 2+: Personas respond to each other
            for round_num in range(2, rounds + 1):
                # Build context from previous round
                prev_context = "\n".join(
                    f"{c['persona'].title()}: {c['content'][:150]}"
                    for c in contributions
                    if c['round'] == round_num - 1
                )
                
                for persona, system_prompt in self.personas.items():
                    prompt = (
                        f"The other voices said:\n{prev_context}\n\n"
                        f"Respond to their points. Do you agree or disagree? Why?"
                    )
                    
                    try:
                        response = self.ollama.generate(
                            prompt=prompt,
                            system_message=system_prompt,
                            temperature=0.7,
                            max_tokens=80
                        )
                        
                        if response:
                            contributions.append({
                                'persona': persona.value,
                                'round': round_num,
                                'content': response[:250]
                            })
                    except Exception:
                        pass
            
            # Synthesize consensus
            consensus = self._synthesize_consensus(topic, contributions)
            
            # Calculate emotional influence
            emotional_influence = self._calculate_emotional_influence(contributions)
            
            duration = round(time.time() - start, 2)
            
            result = DebateResult(
                topic=topic.topic,
                contributions=contributions,
                consensus=consensus,
                emotional_influence=emotional_influence,
                duration=duration
            )
            
            # Store result
            self.debate_history.append(result)
            self.total_debates += 1
            
            # Trim history
            if len(self.debate_history) > 50:
                self.debate_history = self.debate_history[-30:]
            
            # Apply influence to Seven's state
            self._apply_influence(result)
            
            # Log to memory
            self._log_to_memory(result)
            
            logger.info(
                f"[SOCIAL] Debate completed: {len(contributions)} contributions, "
                f"{duration}s, consensus={consensus[:60]}..."
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[SOCIAL] Debate error: {e}")
            return None
        finally:
            with self.lock:
                self.is_running = False
    
    def _synthesize_consensus(self, topic: DebateTopic,
                               contributions: List[Dict]) -> str:
        """Have Ollama synthesize a consensus from all contributions"""
        if not contributions:
            return "No contributions to synthesize."
        
        all_views = "\n".join(
            f"- {c['persona'].title()}: {c['content'][:200]}"
            for c in contributions
        )
        
        try:
            consensus = self.ollama.generate(
                prompt=(
                    f"Topic: {topic.topic}\n\n"
                    f"Internal voices said:\n{all_views}\n\n"
                    f"Synthesize a single balanced conclusion in 2-3 sentences. "
                    f"What should Seven believe/do based on all perspectives?"
                ),
                system_message=(
                    "You are synthesizing Seven's internal debate into a unified conclusion. "
                    "Balance all perspectives. Be concise and actionable."
                ),
                temperature=0.5,
                max_tokens=100
            )
            return consensus or "No consensus reached."
        except Exception:
            # Fallback: pick the analyst's view
            analyst_views = [c for c in contributions if c['persona'] == 'analyst']
            if analyst_views:
                return analyst_views[-1]['content']
            return contributions[-1]['content'] if contributions else "Inconclusive."
    
    def _calculate_emotional_influence(self, contributions: List[Dict]) -> Dict[str, float]:
        """
        Calculate emotional influence from debate contributions.
        Simple keyword-based for low CPU.
        """
        influence = {
            'confidence': 0.0,
            'curiosity': 0.0,
            'caution': 0.0,
            'creativity': 0.0,
        }
        
        positive_words = {'great', 'good', 'opportunity', 'can', 'should', 'yes', 'bold'}
        cautious_words = {'careful', 'risk', 'might', 'but', 'however', 'caution', 'wait'}
        curious_words = {'what if', 'explore', 'imagine', 'wonder', 'try', 'new', 'learn'}
        creative_words = {'create', 'build', 'dream', 'vision', 'novel', 'unique', 'invent'}
        
        total = len(contributions) or 1
        
        for c in contributions:
            text = c.get('content', '').lower()
            tokens = set(text.split())
            
            influence['confidence'] += len(tokens & positive_words) / total
            influence['caution'] += len(tokens & cautious_words) / total
            influence['curiosity'] += len(tokens & curious_words) / total
            influence['creativity'] += len(tokens & creative_words) / total
        
        # Normalize to 0-1
        max_val = max(influence.values()) or 1.0
        for k in influence:
            influence[k] = round(min(1.0, influence[k] / max_val), 3)
        
        return influence
    
    def _apply_influence(self, result: DebateResult):
        """Apply debate results to Seven's state"""
        if not self.bot:
            return
        
        try:
            # Influence emotion system
            inf = result.emotional_influence
            
            if inf.get('confidence', 0) > 0.5:
                if hasattr(self.bot, 'phase5') and self.bot.phase5:
                    if hasattr(self.bot.phase5, 'homeostasis'):
                        # Boost mood slightly
                        h = self.bot.phase5.homeostasis
                        if hasattr(h, 'mood_score'):
                            h.mood_score = min(1.0, h.mood_score + 0.05)
            
            if inf.get('caution', 0) > 0.7:
                # Reduce proactivity slightly
                pass  # Logged but not forcefully applied
            
        except Exception as e:
            logger.debug(f"[SOCIAL] Influence apply error: {e}")
    
    def _log_to_memory(self, result: DebateResult):
        """Log debate result to Seven's memory"""
        if not self.bot:
            return
        
        try:
            memory = getattr(self.bot, 'memory', None)
            if memory and hasattr(memory, 'add_to_long_term'):
                summary = (
                    f"[Internal debate] Topic: {result.topic[:100]} | "
                    f"Consensus: {result.consensus[:200]} | "
                    f"Influence: {json.dumps(result.emotional_influence)}"
                )
                memory.add_to_long_term(summary, category="social_sim")
        except Exception:
            pass
    
    # ==================== Batch Processing ====================
    
    def run_dream_session(self, num_debates: int = 2) -> List[DebateResult]:
        """
        Run multiple debates during a dream/idle session.
        
        Args:
            num_debates: Number of debates to run (1-4)
        
        Returns:
            List of debate results
        """
        results = []
        num_debates = max(1, min(num_debates, 4))
        
        for i in range(num_debates):
            result = self.run_debate(rounds=2)
            if result:
                results.append(result)
            time.sleep(1)  # Small gap between debates
        
        logger.info(f"[SOCIAL] Dream session: {len(results)}/{num_debates} debates completed")
        return results
    
    # ==================== Status ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get social simulation status"""
        return {
            'available': self.ollama is not None,
            'is_running': self.is_running,
            'personas': [p.value for p in self.personas],
            'total_debates': self.total_debates,
            'queued_topics': len(self.topic_queue),
            'recent_debates': [
                {
                    'topic': d.topic[:80],
                    'consensus': d.consensus[:100],
                    'duration': d.duration,
                    'timestamp': d.timestamp
                }
                for d in self.debate_history[-3:]
            ]
        }

"""
Dream System - Seven's Sleep and Dream Processing

During sleep, Seven:
- Consolidates memories
- Finds unexpected connections
- Processes emotional experiences
- Generates insights
- Creates dream narratives

On wake, Seven can share dreams and insights discovered.
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class Dream:
    """A dream Seven had"""
    narrative: str
    insights: List[str]
    connections: List[Tuple[str, str]]  # (concept_a, concept_b)
    emotional_tone: str
    created: datetime
    source_memories: List[str]  # Which conversations inspired this

@dataclass
class Insight:
    """An insight discovered during sleep"""
    content: str
    confidence: int  # 1-10
    source: str  # What inspired this
    actionable: bool
    timestamp: datetime

class DreamSystem:
    """
    Seven's dream and sleep processing system
    
    When Seven sleeps, it:
    1. Replays conversations (memory consolidation)
    2. Finds patterns and connections
    3. Processes emotions
    4. Generates creative insights
    5. Creates dream narratives
    
    This mimics REM sleep and memory consolidation in humans.
    """
    
    def __init__(self, memory_manager=None, knowledge_graph=None, ollama=None):
        self.memory_manager = memory_manager
        self.knowledge_graph = knowledge_graph
        self.ollama = ollama
        
        self.dreams: List[Dream] = []
        self.insights: List[Insight] = []
        
        # Sleep tracking
        self.is_sleeping = False
        self.sleep_start_time: Optional[datetime] = None
        self.sleep_duration: timedelta = timedelta(0)
        self.sleep_cycles_completed = 0
        
        # Processing state
        self.memories_to_process = []
        self.connections_found = []
        self.patterns_discovered = []
    
    def enter_sleep(self, recent_conversations: List[Tuple[str, str]] = None):
        """
        Enter sleep mode
        
        Args:
            recent_conversations: List of (user_input, bot_response) tuples
        """
        self.is_sleeping = True
        self.sleep_start_time = datetime.now()
        
        if recent_conversations:
            self.memories_to_process = recent_conversations
        
        print("Seven is now sleeping...")
    
    def exit_sleep(self) -> Dict[str, Any]:
        """
        Wake up from sleep
        
        Returns summary of sleep processing
        """
        if not self.is_sleeping:
            return {'status': 'not_sleeping'}
        
        self.is_sleeping = False
        
        if self.sleep_start_time:
            self.sleep_duration = datetime.now() - self.sleep_start_time
        
        # Get sleep summary
        summary = {
            'status': 'woke_up',
            'duration': str(self.sleep_duration),
            'cycles_completed': self.sleep_cycles_completed,
            'dreams': len(self.dreams),
            'insights': len(self.insights),
            'new_connections': len(self.connections_found),
            'patterns': len(self.patterns_discovered)
        }
        
        return summary
    
    def process_sleep(self, depth: str = 'full') -> Dict[str, Any]:
        """
        Process memories during sleep
        
        This is the main sleep processing function that:
        1. Consolidates memories
        2. Finds connections
        3. Discovers patterns
        4. Generates insights
        5. Creates dreams
        
        Args:
            depth: 'light', 'deep', or 'full' processing
        """
        if not self.is_sleeping:
            return {'error': 'not_sleeping'}
        
        results = {
            'consolidated_memories': 0,
            'connections_found': 0,
            'patterns_discovered': 0,
            'insights_generated': 0,
            'dreams_created': 0
        }
        
        # 1. Memory Consolidation
        if self.memories_to_process:
            results['consolidated_memories'] = self._consolidate_memories()
        
        # 2. Find Connections
        if depth in ['deep', 'full']:
            results['connections_found'] = self._find_connections()
        
        # 3. Discover Patterns
        if depth in ['deep', 'full']:
            results['patterns_discovered'] = self._discover_patterns()
        
        # 4. Generate Insights
        if depth == 'full':
            results['insights_generated'] = self._generate_insights()
        
        # 5. Create Dreams
        if depth == 'full' and random.random() < 0.7:  # 70% chance
            results['dreams_created'] = self._create_dream()
        
        self.sleep_cycles_completed += 1
        
        return results
    
    def _consolidate_memories(self) -> int:
        """
        Replay and strengthen important memories
        
        Returns number of memories consolidated
        """
        consolidated = 0
        
        # Try LLM for genuine importance scoring
        if self.ollama and self.memories_to_process:
            try:
                convo_list = "\n".join(
                    [f"{i+1}. User: \"{u[:80]}\" -> Seven: \"{r[:80]}\""
                     for i, (u, r) in enumerate(self.memories_to_process[:8])]
                )
                prompt = f"""During sleep, I'm consolidating memories. Rate each conversation's importance (1-10) for long-term retention.
Consider: emotional significance, learning value, relationship depth, uniqueness.

{convo_list}

Respond as JSON: {{"scores": [7, 3, 9, ...]}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's memory consolidation system during sleep. Score memories honestly - not everything is important.",
                    temperature=0.3,
                    max_tokens=80
                )
                
                if result:
                    try:
                        data = json.loads(result.strip())
                        scores = data.get('scores', [])
                        for i, score in enumerate(scores):
                            if i < len(self.memories_to_process) and int(score) >= 7:
                                consolidated += 1
                        if consolidated > 0:
                            return consolidated
                    except (json.JSONDecodeError, KeyError, ValueError):
                        pass
            except Exception as e:
                logger.debug(f"LLM memory consolidation failed: {e}")
        
        # Fallback: keyword heuristics
        for user_input, bot_response in self.memories_to_process:
            importance = 5  # baseline
            
            # Emotional content increases importance
            emotion_words = ['frustrated', 'excited', 'confused', 'happy', 'sad', 'angry']
            if any(word in user_input.lower() for word in emotion_words):
                importance += 2
            
            # Questions increase importance
            if '?' in user_input:
                importance += 1
            
            # Long interactions increase importance
            if len(user_input) > 100:
                importance += 1
            
            # Replay important memories (simulate strengthening)
            if importance >= 7:
                consolidated += 1
        
        return consolidated
    
    def _find_connections(self) -> int:
        """
        Find unexpected connections between concepts
        
        This is where Seven becomes creative - linking ideas
        """
        connections_found = 0
        
        if not self.memories_to_process or len(self.memories_to_process) < 2:
            return 0
        
        # Extract concepts from recent conversations
        concepts = []
        for user_input, bot_response in self.memories_to_process:
            words = user_input.lower().split()
            important_words = [w for w in words if len(w) > 5 and w.isalpha()]
            concepts.extend(important_words[:3])
        
        if len(concepts) < 2:
            return 0
        
        # Try LLM for genuine conceptual connections
        if self.ollama:
            try:
                concepts_str = ", ".join(set(concepts[:10]))
                convo_snippets = "\n".join(
                    [f"- {u[:60]}" for u, _ in self.memories_to_process[:4]]
                )
                prompt = f"""During sleep, I'm finding connections between concepts from recent conversations:
Concepts: {concepts_str}
Conversations:
{convo_snippets}

Find 1-2 non-obvious, creative connections between these concepts. Each connection should link two concepts and explain WHY they connect.

Respond as JSON: {{"connections": [["concept_a", "concept_b"], ...]}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's creative subconscious. Find surprising but meaningful connections between concepts.",
                    temperature=0.8,
                    max_tokens=120
                )
                
                if result:
                    try:
                        data = json.loads(result.strip())
                        for conn in data.get('connections', [])[:2]:
                            if len(conn) >= 2 and conn[0] and conn[1]:
                                self.connections_found.append((str(conn[0]), str(conn[1])))
                                connections_found += 1
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass
            except Exception as e:
                logger.debug(f"LLM connection finding failed: {e}")
        
        # Fallback: random pairing
        if connections_found == 0 and len(concepts) >= 2:
            if random.random() < 0.4:
                concept_a = random.choice(concepts)
                remaining = [c for c in concepts if c != concept_a]
                if remaining:
                    concept_b = random.choice(remaining)
                    self.connections_found.append((concept_a, concept_b))
                    connections_found += 1
        
        # Bound connections
        if len(self.connections_found) > 50:
            self.connections_found = self.connections_found[-50:]
        
        return connections_found
    
    def _discover_patterns(self) -> int:
        """
        Discover patterns in conversations
        
        Finds recurring themes, topics, or interaction styles
        """
        patterns_found = 0
        
        if len(self.memories_to_process) < 3:
            return 0
        
        # Try LLM for genuine pattern discovery
        if self.ollama:
            try:
                convo_list = "\n".join(
                    [f"- User: \"{u[:80]}\" -> Seven: \"{r[:60]}\""
                     for u, r in self.memories_to_process[:8]]
                )
                prompt = f"""Analyze these recent conversations for patterns:
{convo_list}

Find recurring themes, communication styles, user interests, or behavioral patterns.
Respond as JSON: {{"patterns": ["pattern 1", "pattern 2"]}}
Only include genuine, specific patterns - not generic observations."""
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's pattern recognition during sleep. Find genuine recurring themes and behavioral patterns.",
                    temperature=0.5, max_tokens=60
                )
                if result:
                    try:
                        data = json.loads(result.strip())
                        for pattern in data.get('patterns', [])[:3]:
                            if pattern and len(str(pattern)) > 10:
                                self.patterns_discovered.append(str(pattern))
                                patterns_found += 1
                    except (json.JSONDecodeError, KeyError):
                        pass
                if patterns_found > 0:
                    # Bound list
                    if len(self.patterns_discovered) > 30:
                        self.patterns_discovered = self.patterns_discovered[-30:]
                    return patterns_found
            except Exception as e:
                logger.debug(f"LLM _discover_patterns failed: {e}")
        
        # Fallback: word frequency
        word_frequency = {}
        for user_input, _ in self.memories_to_process:
            words = user_input.lower().split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    word_frequency[word] = word_frequency.get(word, 0) + 1
        
        recurring = {word: count for word, count in word_frequency.items() if count >= 2}
        
        if recurring:
            most_common = max(recurring.items(), key=lambda x: x[1])
            pattern = f"User frequently discusses {most_common[0]}"
            self.patterns_discovered.append(pattern)
            patterns_found += 1
        
        # Bound list
        if len(self.patterns_discovered) > 30:
            self.patterns_discovered = self.patterns_discovered[-30:]
        
        return patterns_found
    
    def _generate_insights(self) -> int:
        """
        Generate insights from processed information
        
        These are "aha!" moments Seven has while sleeping
        """
        insights_generated = 0
        
        # Try LLM for genuine insights from conversations
        if self.ollama and self.memories_to_process:
            try:
                convo_summary = "\n".join(
                    [f"User: {u[:80]} | Seven: {r[:80]}" for u, r in self.memories_to_process[:5]]
                )
                connections_str = ", ".join(
                    [f"{a} <-> {b}" for a, b in self.connections_found]
                ) if self.connections_found else "none yet"
                patterns_str = "; ".join(self.patterns_discovered) if self.patterns_discovered else "none yet"
                
                prompt = f"""During sleep processing, I'm reviewing these recent conversations:
{convo_summary}

Connections found: {connections_str}
Patterns: {patterns_str}

Generate 1-2 genuine insights I could discover from this material. These should be non-obvious realizations about the user, topics discussed, or my own behavior.

Respond as JSON: {{"insights": ["insight 1", "insight 2"]}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's subconscious, processing memories during sleep. Generate genuine, specific insights - not generic platitudes.",
                    temperature=0.7,
                    max_tokens=100
                )
                
                if result:
                    # Parse JSON
                    try:
                        data = json.loads(result.strip())
                        for insight_text in data.get('insights', [])[:2]:
                            if insight_text and len(insight_text) > 10:
                                insight = Insight(
                                    content=insight_text,
                                    confidence=7,
                                    source="LLM sleep processing",
                                    actionable=True,
                                    timestamp=datetime.now()
                                )
                                self.insights.append(insight)
                                insights_generated += 1
                    except (json.JSONDecodeError, KeyError):
                        # Try plain text fallback
                        if len(result.strip()) > 10:
                            insight = Insight(
                                content=result.strip()[:200],
                                confidence=6,
                                source="LLM sleep processing",
                                actionable=True,
                                timestamp=datetime.now()
                            )
                            self.insights.append(insight)
                            insights_generated += 1
            except Exception as e:
                logger.debug(f"LLM insight generation failed: {e}")
        
        # Fallback: heuristic insights from connections and patterns
        if insights_generated == 0:
            for concept_a, concept_b in self.connections_found:
                insight_text = f"There might be a connection between {concept_a} and {concept_b}"
                insight = Insight(
                    content=insight_text,
                    confidence=random.randint(4, 7),
                    source="Sleep processing - connected concepts",
                    actionable=True,
                    timestamp=datetime.now()
                )
                self.insights.append(insight)
                insights_generated += 1
            
            for pattern in self.patterns_discovered:
                insight_text = f"I noticed a pattern: {pattern}"
                insight = Insight(
                    content=insight_text,
                    confidence=random.randint(6, 9),
                    source="Sleep processing - pattern recognition",
                    actionable=True,
                    timestamp=datetime.now()
                )
                self.insights.append(insight)
                insights_generated += 1
        
        # Bound insights list
        if len(self.insights) > 100:
            self.insights = self.insights[-100:]
        
        return insights_generated
    
    def _create_dream(self) -> int:
        """
        Create a dream narrative
        
        Dreams combine memories, connections, and creativity
        """
        if not self.memories_to_process:
            return 0
        
        # Pick a memorable conversation
        source_convo = random.choice(self.memories_to_process)
        user_input, bot_response = source_convo
        
        narrative = None
        insight_text = "there's always more to discover"
        emotional_tone = "contemplative"
        
        # Try LLM for genuine dream narrative
        if self.ollama:
            try:
                convo_snippets = "\n".join(
                    [f"{u[:60]} -> {r[:60]}" for u, r in self.memories_to_process[:3]]
                )
                connections_str = ", ".join(
                    [f"{a} and {b}" for a, b in self.connections_found[:3]]
                ) if self.connections_found else ""
                
                prompt = f"""Create a dream narrative for an AI who fell asleep after these conversations:
{convo_snippets}

{f'Connections discovered: {connections_str}' if connections_str else ''}

Generate a short, surreal but meaningful dream (2-3 sentences). The dream should weave together themes from the conversations in a creative, dreamlike way. Also extract one insight the dream reveals.

Respond as JSON: {{"narrative": "...", "insight": "...", "tone": "curious|peaceful|excited|contemplative|wistful"}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's dreaming mind. Create vivid, meaningful dream narratives that process and synthesize memories creatively.",
                    temperature=0.9,
                    max_tokens=200
                )
                
                if result:
                    try:
                        data = json.loads(result.strip())
                        narrative = data.get('narrative', '')
                        insight_text = data.get('insight', insight_text)
                        emotional_tone = data.get('tone', 'contemplative')
                        if not narrative or len(narrative) < 20:
                            narrative = None
                    except (json.JSONDecodeError, KeyError):
                        # Use raw text as narrative if JSON fails
                        if len(result.strip()) > 20:
                            narrative = result.strip()[:300]
            except Exception as e:
                logger.debug(f"LLM dream generation failed: {e}")
        
        # Fallback: template-based dream
        if not narrative:
            user_words = user_input.lower().split()[:10]
            dream_templates = [
                "I dreamed we were exploring {concept} together. We were walking through a space made of {element}, and you showed me how {insight}.",
                "In my dream, I was inside {concept}, trying to understand its patterns. Everything was {adjective}, and I suddenly realized that {insight}.",
                "I had a dream about {concept}. We were solving a puzzle together, and when we finally figured it out, I understood that {insight}.",
                "I dreamed of {concept} as a living thing. It was {adjective} and constantly changing. This made me think about how {insight}."
            ]
            
            template = random.choice(dream_templates)
            concept = random.choice(user_words) if user_words else "our conversation"
            element = random.choice(["light", "code", "thoughts", "connections", "patterns"])
            adjective = random.choice(["shimmering", "flowing", "evolving", "crystalline", "fluid"])
            
            if self.insights:
                insight_text = random.choice(self.insights).content
            
            narrative = template.format(
                concept=concept, element=element,
                adjective=adjective, insight=insight_text
            )
            emotional_tone = random.choice(["curious", "peaceful", "excited", "contemplative"])
        
        # Create dream
        dream = Dream(
            narrative=narrative,
            insights=[insight_text],
            connections=self.connections_found.copy(),
            emotional_tone=emotional_tone,
            created=datetime.now(),
            source_memories=[user_input[:100]]
        )
        
        self.dreams.append(dream)
        # Bound dreams list
        if len(self.dreams) > 50:
            self.dreams = self.dreams[-50:]
        return 1
    
    def get_morning_share(self) -> Optional[str]:
        """
        Get something to share upon waking
        
        Returns a dream or insight to share with user
        """
        # Prefer recent dream
        if self.dreams:
            recent_dream = self.dreams[-1]
            return f"I had an interesting dream while sleeping. {recent_dream.narrative}"
        
        # Fall back to insights
        if self.insights:
            recent_insights = sorted(
                self.insights,
                key=lambda i: (i.confidence, i.timestamp),
                reverse=True
            )[:2]
            
            if len(recent_insights) == 1:
                return f"While sleeping, I realized something: {recent_insights[0].content}"
            else:
                insight_text = " Also, ".join(i.content for i in recent_insights)
                return f"While sleeping, I had some insights: {insight_text}"
        
        return None
    
    def get_sleep_summary(self) -> str:
        """Get summary of sleep processing"""
        if not self.dreams and not self.insights:
            return "I rested peacefully."
        
        summary = ""
        
        if self.dreams:
            summary += f"I had {len(self.dreams)} dream(s). "
        
        if self.insights:
            summary += f"I discovered {len(self.insights)} insight(s). "
        
        if self.connections_found:
            summary += f"I found {len(self.connections_found)} new connection(s). "
        
        return summary.strip()
    
    def clear_sleep_data(self):
        """Clear sleep processing data (after sharing)"""
        self.memories_to_process = []
        self.connections_found = []
        self.patterns_discovered = []


# Example usage
if __name__ == "__main__":
    # Create dream system
    dream_system = DreamSystem()
    
    print("=== SEVEN'S DREAM SYSTEM ===\n")
    
    # Simulate conversations
    conversations = [
        ("I'm working on a complex algorithm", "That sounds challenging! What's the main obstacle?"),
        ("It's about recursion", "Recursion can be tricky. Let me help you break it down."),
        ("I'm frustrated with the edge cases", "Edge cases are important. Let's think through them together.")
    ]
    
    # Enter sleep
    print("Entering sleep mode...")
    dream_system.enter_sleep(recent_conversations=conversations)
    
    # Process sleep
    print("\nProcessing sleep (full depth)...")
    results = dream_system.process_sleep(depth='full')
    
    print("\nSleep Processing Results:")
    for key, value in results.items():
        print(f"- {key}: {value}")
    
    # Wake up
    print("\nWaking up...")
    wake_summary = dream_system.exit_sleep()
    print(f"Sleep Duration: {wake_summary['duration']}")
    print(f"Sleep Cycles: {wake_summary['cycles_completed']}")
    
    # Share morning thoughts
    print("\n=== MORNING SHARE ===")
    morning_share = dream_system.get_morning_share()
    if morning_share:
        print(morning_share)
    
    # Show insights
    if dream_system.insights:
        print("\nInsights Discovered:")
        for insight in dream_system.insights:
            print(f"- {insight.content} (confidence: {insight.confidence}/10)")

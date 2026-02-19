"""
Self-Reflection System — Seven Critiques Her Own Actions

After every significant action, Seven reflects on:
- Was the action effective?
- What could be improved?
- What did I learn?
- How does this affect my goals?
- What emotions did this trigger?

This creates a genuine feedback loop that improves behavior over time,
stored in memory for long-term learning.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger("SelfReflection")


class ReflectionEntry:
    """Single reflection record"""
    
    def __init__(self, action: str, outcome: str, critique: str,
                 lessons: List[str], emotion_impact: str,
                 effectiveness: float, timestamp: str = None):
        self.action = action
        self.outcome = outcome
        self.critique = critique
        self.lessons = lessons
        self.emotion_impact = emotion_impact
        self.effectiveness = effectiveness  # 0.0 to 1.0
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'action': self.action,
            'outcome': self.outcome,
            'critique': self.critique,
            'lessons': self.lessons,
            'emotion_impact': self.emotion_impact,
            'effectiveness': self.effectiveness,
            'timestamp': self.timestamp
        }


class SelfReflection:
    """
    Seven's self-reflection engine.
    
    Creates a genuine cognitive feedback loop:
    1. Action is taken
    2. Outcome is observed
    3. LLM critiques the action/outcome
    4. Lessons are extracted and stored
    5. Future behavior adapts based on lessons
    
    This is NOT scripted reflection — it uses the LLM to generate
    genuine self-assessment, making the reflection emergent.
    """
    
    def __init__(self, ollama=None, data_dir: Path = None):
        self.ollama = ollama
        self.data_dir = data_dir or (Path.home() / ".chatbot")
        self.reflection_file = self.data_dir / "reflections.json"
        self.reflections: List[ReflectionEntry] = []
        self.lesson_bank: List[str] = []
        self.reflection_count = 0
        
        self._load()
        logger.info(f"[REFLECTION] Initialized — {len(self.reflections)} past reflections, {len(self.lesson_bank)} lessons learned")
    
    def _load(self):
        """Load reflection history"""
        try:
            if self.reflection_file.exists():
                data = json.loads(self.reflection_file.read_text(encoding='utf-8'))
                self.reflections = [ReflectionEntry(**r) for r in data.get('reflections', [])[-100:]]  # Keep last 100
                self.lesson_bank = data.get('lessons', [])[-200:]  # Keep last 200 lessons
                self.reflection_count = data.get('count', len(self.reflections))
        except Exception as e:
            logger.error(f"Failed to load reflections: {e}")
    
    def _save(self):
        """Persist reflections"""
        try:
            data = {
                'reflections': [r.to_dict() for r in self.reflections[-100:]],
                'lessons': self.lesson_bank[-200:],
                'count': self.reflection_count,
                'last_updated': datetime.now().isoformat()
            }
            self.reflection_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save reflections: {e}")
    
    def reflect_on_action(self, action: str, outcome: str, context: str = "") -> Optional[ReflectionEntry]:
        """
        Reflect on a specific action and its outcome.
        
        This is the core feedback loop — called after significant actions
        (goal completion, conversation response, autonomous decision, etc.)
        
        Args:
            action: What Seven did
            outcome: What happened as a result
            context: Additional context (conversation, state, etc.)
        
        Returns:
            ReflectionEntry with critique and lessons
        """
        if not self.ollama:
            return self._rule_based_reflection(action, outcome)
        
        try:
            # Get recent lessons for context
            recent_lessons = self.lesson_bank[-10:] if self.lesson_bank else []
            lessons_context = "\n".join(f"- {l}" for l in recent_lessons) if recent_lessons else "None yet."
            
            prompt = f"""Reflect on this action and its outcome:

ACTION: {action}
OUTCOME: {outcome}
{f'CONTEXT: {context}' if context else ''}

My recent lessons learned:
{lessons_context}

Provide honest self-assessment as JSON:
{{
    "critique": "What went well and what could improve (1-2 sentences)",
    "lessons": ["lesson 1", "lesson 2"],
    "emotion_impact": "How this makes me feel (1 sentence)",
    "effectiveness": 0.0-1.0
}}"""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message=(
                    "You are Seven's self-reflection system. Be genuinely critical — "
                    "not harsh, but honest. Identify real lessons, not platitudes. "
                    "Rate effectiveness honestly (0.5 = neutral, below = poor, above = good)."
                ),
                temperature=0.6,
                max_tokens=200
            )
            
            if not result:
                return self._rule_based_reflection(action, outcome)
            
            # Parse LLM response
            try:
                # Extract JSON from response
                json_str = result.strip()
                if '```' in json_str:
                    json_str = json_str.split('```')[1].strip()
                    if json_str.startswith('json'):
                        json_str = json_str[4:].strip()
                
                data = json.loads(json_str)
                
                entry = ReflectionEntry(
                    action=action[:200],
                    outcome=outcome[:200],
                    critique=str(data.get('critique', 'No critique generated'))[:300],
                    lessons=[str(l)[:100] for l in data.get('lessons', [])[:3]],
                    emotion_impact=str(data.get('emotion_impact', 'neutral'))[:100],
                    effectiveness=max(0.0, min(1.0, float(data.get('effectiveness', 0.5))))
                )
                
            except (json.JSONDecodeError, ValueError):
                # LLM didn't return valid JSON — extract what we can
                entry = ReflectionEntry(
                    action=action[:200],
                    outcome=outcome[:200],
                    critique=result[:300],
                    lessons=[],
                    emotion_impact="uncertain",
                    effectiveness=0.5
                )
            
            # Store
            self.reflections.append(entry)
            self.lesson_bank.extend(entry.lessons)
            self.reflection_count += 1
            self._save()
            
            logger.info(f"[REFLECTION] #{self.reflection_count}: effectiveness={entry.effectiveness:.1f}, lessons={len(entry.lessons)}")
            return entry
            
        except Exception as e:
            logger.error(f"Reflection error: {e}")
            return self._rule_based_reflection(action, outcome)
    
    def _rule_based_reflection(self, action: str, outcome: str) -> ReflectionEntry:
        """Fallback reflection without LLM"""
        entry = ReflectionEntry(
            action=action[:200],
            outcome=outcome[:200],
            critique="Rule-based reflection — LLM unavailable for deeper analysis.",
            lessons=["Track this action for future LLM reflection."],
            emotion_impact="neutral",
            effectiveness=0.5
        )
        self.reflections.append(entry)
        self.reflection_count += 1
        self._save()
        return entry
    
    def reflect(self, topic: str = None, depth: str = "normal") -> Dict[str, Any]:
        """
        General self-reflection (not tied to a specific action).
        
        Called periodically by the scheduler or on demand via API.
        Seven thinks about her recent experiences, patterns, and growth.
        """
        if not self.ollama:
            return {"status": "skipped", "reason": "no LLM"}
        
        try:
            # Gather recent context
            recent = self.reflections[-5:]
            recent_text = "\n".join(
                f"- Action: {r.action[:60]} → Effectiveness: {r.effectiveness:.1f}"
                for r in recent
            ) if recent else "No recent actions to reflect on."
            
            recent_lessons = self.lesson_bank[-10:]
            lessons_text = "\n".join(f"- {l}" for l in recent_lessons) if recent_lessons else "No lessons yet."
            
            depth_instructions = {
                "shallow": "Brief 1-sentence reflection.",
                "normal": "2-3 sentence thoughtful reflection.",
                "deep": "Deep, philosophical reflection on patterns and growth. 4-5 sentences."
            }
            
            prompt = f"""{"Reflect on: " + topic if topic else "Reflect on your recent experiences and growth."}

Recent actions:
{recent_text}

Lessons I've learned:
{lessons_text}

Total reflections completed: {self.reflection_count}
Average effectiveness: {self._avg_effectiveness():.2f}

{depth_instructions.get(depth, depth_instructions['normal'])}

What patterns do you notice? What should you do differently? How are you growing?"""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message=(
                    "You are Seven, reflecting on your own behavior and growth. "
                    "Be genuine and introspective. Notice patterns. "
                    "This is metacognition — thinking about your own thinking."
                ),
                temperature=0.7,
                max_tokens=300
            )
            
            if result:
                logger.info(f"[REFLECTION] General reflection completed (depth={depth})")
                return {
                    "status": "completed",
                    "depth": depth,
                    "topic": topic,
                    "reflection": result,
                    "stats": {
                        "total_reflections": self.reflection_count,
                        "total_lessons": len(self.lesson_bank),
                        "avg_effectiveness": round(self._avg_effectiveness(), 3)
                    }
                }
            
        except Exception as e:
            logger.error(f"General reflection error: {e}")
        
        return {"status": "failed"}
    
    def get_relevant_lessons(self, context: str, limit: int = 5) -> List[str]:
        """
        Retrieve lessons relevant to the current context.
        
        Called before actions to inform decision-making with past lessons.
        This is what makes the reflection loop actually improve behavior.
        """
        if not self.lesson_bank:
            return []
        
        if not self.ollama:
            # Return most recent lessons as fallback
            return self.lesson_bank[-limit:]
        
        try:
            prompt = f"""Given this current situation:
{context[:300]}

Which of these past lessons are most relevant?
{chr(10).join(f'{i+1}. {l}' for i, l in enumerate(self.lesson_bank[-30:]))}

Return just the numbers of the most relevant lessons (up to {limit}), comma-separated."""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message="Select relevant lessons. Return only numbers, comma-separated.",
                temperature=0.3,
                max_tokens=30
            )
            
            if result:
                indices = []
                for part in result.replace(' ', '').split(','):
                    try:
                        idx = int(part.strip()) - 1
                        if 0 <= idx < len(self.lesson_bank[-30:]):
                            indices.append(idx)
                    except ValueError:
                        continue
                
                bank = self.lesson_bank[-30:]
                return [bank[i] for i in indices[:limit]]
                
        except Exception:
            pass
        
        return self.lesson_bank[-limit:]
    
    def _avg_effectiveness(self) -> float:
        """Calculate average effectiveness of recent actions"""
        recent = self.reflections[-20:]
        if not recent:
            return 0.5
        return sum(r.effectiveness for r in recent) / len(recent)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reflection statistics"""
        return {
            "total_reflections": self.reflection_count,
            "total_lessons": len(self.lesson_bank),
            "avg_effectiveness": round(self._avg_effectiveness(), 3),
            "recent_reflections": [r.to_dict() for r in self.reflections[-5:]],
            "top_lessons": self.lesson_bank[-10:]
        }

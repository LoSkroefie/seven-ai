"""
Seven AI v2.0 - Advanced Capabilities (Tier 4)
Beyond standard sentience - maximum intelligence features
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class ConversationalMemoryEnhancement:
    """
    Long-term topic tracking and multi-session continuation
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.memory_file = os.path.join(data_dir, "conversational_memory.json")
        self.topics = self._load_topics()
        self.story_threads = self._load_threads()
    
    def _load_topics(self) -> Dict:
        """Load topic memory"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return data.get("topics", {})
            except Exception:
                return {}
        return {}
    
    def _load_threads(self) -> Dict:
        """Load story threads"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    return data.get("threads", {})
            except Exception:
                return {}
        return {}
    
    def track_topic(self, topic: str, context: str, importance: int = 1):
        """Track a conversation topic over time"""
        if topic not in self.topics:
            self.topics[topic] = {
                "first_mentioned": datetime.now().isoformat(),
                "mentions": [],
                "importance_score": 0,
                "related_topics": []
            }
        
        self.topics[topic]["mentions"].append({
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "importance": importance
        })
        self.topics[topic]["importance_score"] += importance
        self._save()
    
    def get_topic_history(self, topic: str) -> Optional[Dict]:
        """Get complete history of a topic"""
        return self.topics.get(topic)
    
    def find_related_topics(self, topic: str) -> List[str]:
        """Find topics related to given topic"""
        if topic not in self.topics:
            return []
        return self.topics[topic].get("related_topics", [])
    
    def create_story_thread(self, thread_id: str, description: str):
        """Create a multi-session story thread"""
        self.story_threads[thread_id] = {
            "created": datetime.now().isoformat(),
            "description": description,
            "updates": [],
            "status": "active"
        }
        self._save()
    
    def update_story_thread(self, thread_id: str, update: str):
        """Add update to story thread"""
        if thread_id in self.story_threads:
            self.story_threads[thread_id]["updates"].append({
                "timestamp": datetime.now().isoformat(),
                "content": update
            })
            self._save()
    
    def get_story_thread(self, thread_id: str) -> Optional[Dict]:
        """Get complete story thread"""
        return self.story_threads.get(thread_id)
    
    def _save(self):
        """Save memory to disk"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump({
                "topics": self.topics,
                "threads": self.story_threads
            }, f, indent=2)


class AdaptiveCommunication:
    """
    Dynamic communication style adjustment
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.style_file = os.path.join(data_dir, "communication_style.json")
        self.style = self._load_style()
    
    def _load_style(self) -> Dict:
        """Load communication style preferences"""
        if os.path.exists(self.style_file):
            try:
                with open(self.style_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return self._default_style()
        return self._default_style()
    
    def _default_style(self) -> Dict:
        """Default communication style"""
        return {
            "formality": 5,  # 1-10 scale
            "humor": 5,
            "verbosity": 5,
            "technical_depth": 5,
            "emoji_use": 2,
            "question_frequency": 5
        }
    
    def adjust_formality(self, delta: int):
        """Adjust formality level"""
        self.style["formality"] = max(1, min(10, self.style["formality"] + delta))
        self._save()
    
    def adjust_humor(self, delta: int):
        """Adjust humor level"""
        self.style["humor"] = max(1, min(10, self.style["humor"] + delta))
        self._save()
    
    def adjust_verbosity(self, delta: int):
        """Adjust verbosity level"""
        self.style["verbosity"] = max(1, min(10, self.style["verbosity"] + delta))
        self._save()
    
    def adjust_technical_depth(self, delta: int):
        """Adjust technical depth"""
        self.style["technical_depth"] = max(1, min(10, self.style["technical_depth"] + delta))
        self._save()
    
    def get_style_instructions(self) -> str:
        """Get style instructions for response generation"""
        instructions = []
        
        if self.style["formality"] < 4:
            instructions.append("Use casual, friendly language")
        elif self.style["formality"] > 7:
            instructions.append("Use formal, professional language")
        
        if self.style["humor"] > 6:
            instructions.append("Include appropriate humor")
        elif self.style["humor"] < 4:
            instructions.append("Maintain serious tone")
        
        if self.style["verbosity"] < 4:
            instructions.append("Be concise and brief")
        elif self.style["verbosity"] > 7:
            instructions.append("Provide detailed explanations")
        
        if self.style["technical_depth"] < 4:
            instructions.append("Use simple, non-technical language")
        elif self.style["technical_depth"] > 7:
            instructions.append("Use technical terminology freely")
        
        return " | ".join(instructions) if instructions else "Natural communication"
    
    def _save(self):
        """Save style preferences"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.style_file, 'w') as f:
            json.dump(self.style, f, indent=2)


class ProactiveProblemSolver:
    """
    Pattern recognition and solution suggestion
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.patterns_file = os.path.join(data_dir, "problem_patterns.json")
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load recognized patterns"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {"patterns": [], "solutions": {}}
        return {"patterns": [], "solutions": {}}
    
    def recognize_pattern(self, issue: str, context: Dict) -> Optional[Dict]:
        """Recognize if issue matches known pattern"""
        for pattern in self.patterns["patterns"]:
            if self._matches_pattern(issue, pattern):
                return {
                    "pattern_id": pattern["id"],
                    "confidence": pattern["confidence"],
                    "solution": self.patterns["solutions"].get(pattern["solution_id"])
                }
        return None
    
    def _matches_pattern(self, issue: str, pattern: Dict) -> bool:
        """Check if issue matches pattern"""
        keywords = pattern.get("keywords", [])
        return any(keyword.lower() in issue.lower() for keyword in keywords)
    
    def suggest_proactive_solution(self, issue: str) -> Optional[str]:
        """Suggest solution before being asked"""
        pattern = self.recognize_pattern(issue, {})
        if pattern and pattern.get("solution"):
            return f"I recognize this pattern - have you tried: {pattern['solution'].get('description')}"
        return None
    
    def learn_pattern(self, issue: str, solution: str, effectiveness: float):
        """Learn new problem-solution pattern"""
        pattern_id = f"pattern_{len(self.patterns['patterns']) + 1}"
        solution_id = f"solution_{len(self.patterns['solutions']) + 1}"
        
        self.patterns["patterns"].append({
            "id": pattern_id,
            "keywords": issue.lower().split()[:5],
            "confidence": effectiveness,
            "solution_id": solution_id,
            "learned": datetime.now().isoformat()
        })
        
        self.patterns["solutions"][solution_id] = {
            "description": solution,
            "effectiveness": effectiveness,
            "uses": 0
        }
        
        self._save()
    
    def _save(self):
        """Save patterns"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)


class SocialIntelligence:
    """
    Tone detection, stress recognition, support timing
    """
    
    def __init__(self, ollama=None):
        self.ollama = ollama
        self.stress_indicators = [
            "stressed", "overwhelmed", "tired", "exhausted", "frustrated",
            "can't handle", "too much", "giving up", "hate", "annoying"
        ]
        self.positive_indicators = [
            "great", "awesome", "excited", "happy", "love", "excellent",
            "perfect", "amazing", "wonderful", "fantastic"
        ]
    
    def detect_tone(self, text: str) -> str:
        """Detect emotional tone of text using LLM or keyword fallback"""
        if self.ollama and len(text) > 5:
            try:
                result = self.ollama.generate(
                    prompt=f'Classify the emotional tone of this text into exactly one of: stressed, positive, seeking_help, neutral\nText: "{text[:150]}"\nRespond with ONLY the single word classification.',
                    system_message="You are an emotion classifier. Respond with exactly one word.",
                    temperature=0.1, max_tokens=10
                )
                if result:
                    tone = result.strip().lower().replace('"', '').replace('.', '')
                    if tone in ('stressed', 'positive', 'seeking_help', 'neutral'):
                        return tone
            except Exception:
                pass
        
        # Fallback: keyword counting
        text_lower = text.lower()
        stress_count = sum(1 for indicator in self.stress_indicators if indicator in text_lower)
        positive_count = sum(1 for indicator in self.positive_indicators if indicator in text_lower)
        
        if stress_count > positive_count:
            return "stressed"
        elif positive_count > stress_count:
            return "positive"
        elif "?" in text and len(text.split()) < 10:
            return "seeking_help"
        else:
            return "neutral"
    
    def should_offer_support(self, tone: str, recent_interactions: int) -> bool:
        """Determine if support should be offered"""
        if tone == "stressed":
            return True
        if tone == "seeking_help" and recent_interactions > 5:
            return True
        return False
    
    def generate_support_message(self, tone: str) -> str:
        """Generate appropriate support message using LLM or template fallback"""
        if self.ollama:
            try:
                result = self.ollama.generate(
                    prompt=f'The user\'s tone is: {tone}. Generate a brief, warm, natural support message (1-2 sentences). Be genuine, not robotic.',
                    system_message="You are Seven, an empathetic AI companion. Generate a natural support message.",
                    temperature=0.7, max_tokens=40
                )
                if result and len(result.strip()) > 5:
                    return result.strip()
            except Exception:
                pass
        
        # Fallback templates
        if tone == "stressed":
            return "I notice you seem stressed. Would it help to take a break or talk through what's bothering you?"
        elif tone == "seeking_help":
            return "I'm here to help! What do you need?"
        elif tone == "positive":
            return "It's great to see you in good spirits!"
        return ""


class CreativeInitiative:
    """
    Unsolicited ideas and suggestions
    """
    
    def __init__(self, data_dir: str = "data", ollama=None):
        self.ollama = ollama
        self.data_dir = data_dir
        self.ideas_file = os.path.join(data_dir, "creative_ideas.json")
        self.ideas = self._load_ideas()
    
    def _load_ideas(self) -> List:
        """Load past ideas"""
        if os.path.exists(self.ideas_file):
            try:
                with open(self.ideas_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def generate_idea(self, context: Dict, user_interests: List[str]) -> Optional[str]:
        """Generate unsolicited creative idea using LLM or template fallback"""
        if not user_interests:
            return None
        
        # Try LLM for genuine creative ideas
        if self.ollama:
            try:
                interests_str = ", ".join(user_interests[:5])
                recent_ideas = "; ".join([p["idea"][:60] for p in self.ideas[-5:]]) if self.ideas else "none"
                result = self.ollama.generate(
                    prompt=f"""User interests: {interests_str}
Recent ideas already shared: {recent_ideas}

Generate ONE creative, specific suggestion or idea related to their interests. Must be different from recent ideas. Keep it to 1-2 sentences.""",
                    system_message="You are Seven, a creative AI companion. Generate a genuinely useful, specific idea - not generic advice.",
                    temperature=0.8, max_tokens=60
                )
                if result and len(result.strip()) > 10:
                    idea = result.strip()
                    self._record_idea(idea)
                    return idea
            except Exception:
                pass
        
        # Fallback: template ideas
        ideas = [
            f"I had a thought - what if we explored {user_interests[0]} from a different angle?",
            f"Here's an idea: combining {user_interests[0]} with automation could save time.",
            "I've been thinking - would you like me to help organize your projects better?",
            "Random suggestion: have you considered creating a knowledge base for your work?"
        ]
        
        for idea in ideas:
            if not any(past["idea"] == idea for past in self.ideas[-10:]):
                self._record_idea(idea)
                return idea
        
        return None
    
    def _record_idea(self, idea: str):
        """Record generated idea"""
        self.ideas.append({
            "idea": idea,
            "generated": datetime.now().isoformat(),
            "accepted": None
        })
        self._save()
    
    def _save(self):
        """Save ideas"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.ideas_file, 'w') as f:
            json.dump(self.ideas, f, indent=2)


class HabitLearning:
    """
    Daily pattern recognition and routine understanding
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.habits_file = os.path.join(data_dir, "habits.json")
        self.habits = self._load_habits()
    
    def _load_habits(self) -> Dict:
        """Load learned habits"""
        if os.path.exists(self.habits_file):
            try:
                with open(self.habits_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {"daily": [], "weekly": [], "patterns": []}
        return {"daily": [], "weekly": [], "patterns": []}
    
    def record_activity(self, activity: str, timestamp: datetime = None):
        """Record user activity"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Detect patterns in activity timing
        hour = timestamp.hour
        day = timestamp.strftime("%A")
        
        # Look for daily patterns
        pattern_key = f"{activity}_{hour}"
        existing = next((p for p in self.habits["patterns"] if p["key"] == pattern_key), None)
        
        if existing:
            existing["count"] += 1
            existing["last_seen"] = timestamp.isoformat()
        else:
            self.habits["patterns"].append({
                "key": pattern_key,
                "activity": activity,
                "hour": hour,
                "day": day,
                "count": 1,
                "first_seen": timestamp.isoformat(),
                "last_seen": timestamp.isoformat()
            })
        
        self._save()
    
    def predict_next_activity(self) -> Optional[str]:
        """Predict what user likely to do next based on time"""
        now = datetime.now()
        hour = now.hour
        
        # Find patterns matching current hour
        matches = [p for p in self.habits["patterns"] if p["hour"] == hour and p["count"] >= 3]
        
        if matches:
            # Return most frequent pattern
            matches.sort(key=lambda x: x["count"], reverse=True)
            return matches[0]["activity"]
        
        return None
    
    def suggest_break(self, work_duration: timedelta) -> bool:
        """Suggest break based on work duration"""
        # Suggest break after 90 minutes of work
        return work_duration.total_seconds() > 5400
    
    def _save(self):
        """Save habits"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.habits_file, 'w') as f:
            json.dump(self.habits, f, indent=2)


class TaskChaining:
    """
    Multi-step autonomous task execution
    """
    
    def __init__(self):
        self.active_chains = {}
        self.chain_results = {}
    
    def create_task_chain(self, chain_id: str, tasks: List[Dict]):
        """Create multi-step task chain"""
        self.active_chains[chain_id] = {
            "tasks": tasks,
            "current_step": 0,
            "status": "pending",
            "results": [],
            "started": datetime.now().isoformat()
        }
    
    def execute_next_step(self, chain_id: str, executor_func) -> Dict:
        """Execute next step in chain"""
        if chain_id not in self.active_chains:
            return {"error": "Chain not found"}
        
        chain = self.active_chains[chain_id]
        if chain["current_step"] >= len(chain["tasks"]):
            chain["status"] = "complete"
            return {"status": "complete", "results": chain["results"]}
        
        current_task = chain["tasks"][chain["current_step"]]
        
        try:
            result = executor_func(current_task)
            chain["results"].append(result)
            chain["current_step"] += 1
            
            if chain["current_step"] >= len(chain["tasks"]):
                chain["status"] = "complete"
            
            return {"status": "success", "result": result, "step": chain["current_step"]}
        except Exception as e:
            chain["status"] = "error"
            return {"status": "error", "error": str(e), "step": chain["current_step"]}
    
    def get_chain_status(self, chain_id: str) -> Optional[Dict]:
        """Get status of task chain"""
        return self.active_chains.get(chain_id)


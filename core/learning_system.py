"""
Learning system - bot learns from corrections and feedback
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path
import config

class LearningSystem:
    """Manages learning from user corrections and feedback"""
    
    def __init__(self):
        self.knowledge_file = config.DATA_DIR / "learned_knowledge.json"
        self.corrections_file = config.DATA_DIR / "corrections.json"
        self.knowledge = self._load_knowledge()
        self.corrections = self._load_corrections()
    
    def _load_knowledge(self) -> Dict:
        """Load learned knowledge base"""
        if self.knowledge_file.exists():
            try:
                return json.loads(self.knowledge_file.read_text())
            except Exception:
                pass
        return {"facts": {}, "preferences": {}, "corrections": []}
    
    def _load_corrections(self) -> List[Dict]:
        """Load correction history"""
        if self.corrections_file.exists():
            try:
                return json.loads(self.corrections_file.read_text())
            except Exception:
                pass
        return []
    
    def _save_knowledge(self):
        """Save knowledge to disk"""
        try:
            self.knowledge_file.write_text(json.dumps(self.knowledge, indent=2))
        except Exception as e:
            print(f"[WARNING]  Error saving knowledge: {e}")
    
    def _save_corrections(self):
        """Save corrections to disk"""
        try:
            self.corrections_file.write_text(json.dumps(self.corrections, indent=2))
        except Exception as e:
            print(f"[WARNING]  Error saving corrections: {e}")
    
    def detect_correction(self, user_input: str, previous_bot_response: str) -> Optional[Dict]:
        """
        Detect if user is correcting the bot
        
        Args:
            user_input: Current user input
            previous_bot_response: Bot's last response
            
        Returns:
            Correction info if detected, None otherwise
        """
        user_lower = user_input.lower()
        
        # Correction triggers
        triggers = [
            "no,", "no actually", "that's wrong", "incorrect",
            "you're wrong", "not quite", "actually,",
            "let me correct", "i meant", "it's actually"
        ]
        
        for trigger in triggers:
            if trigger in user_lower:
                return {
                    "wrong_response": previous_bot_response,
                    "correction": user_input,
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def learn_correction(self, wrong_response: str, correct_info: str, context: str = ""):
        """
        Learn from a correction
        
        Args:
            wrong_response: What bot said that was wrong
            correct_info: Correct information
            context: Context of the error
        """
        correction = {
            "timestamp": datetime.now().isoformat(),
            "wrong": wrong_response,
            "correct": correct_info,
            "context": context
        }
        
        self.corrections.append(correction)
        self.knowledge["corrections"].append(correction)
        
        # Bound corrections to prevent unbounded growth
        if len(self.corrections) > 200:
            self.corrections = self.corrections[-200:]
        if len(self.knowledge["corrections"]) > 200:
            self.knowledge["corrections"] = self.knowledge["corrections"][-200:]
        
        self._save_corrections()
        self._save_knowledge()
        
        print(f"📚 Learned from correction: {wrong_response[:50]}... → {correct_info[:50]}...")
    
    def learn_fact(self, fact: str, category: str = "general"):
        """
        Learn a new fact
        
        Args:
            fact: Fact to remember
            category: Category of fact
        """
        if category not in self.knowledge["facts"]:
            self.knowledge["facts"][category] = []
        
        self.knowledge["facts"][category].append({
            "fact": fact,
            "learned_at": datetime.now().isoformat()
        })
        
        self._save_knowledge()
        print(f"📚 Learned new fact: {fact[:50]}...")
    
    def learn_preference(self, key: str, value: str):
        """
        Learn user preference
        
        Args:
            key: Preference key (e.g., "favorite_color")
            value: Preference value (e.g., "blue")
        """
        self.knowledge["preferences"][key] = {
            "value": value,
            "learned_at": datetime.now().isoformat()
        }
        
        self._save_knowledge()
        print(f"📚 Learned preference: {key} = {value}")
    
    def get_corrections_context(self, max_recent: int = 5) -> str:
        """
        Get recent corrections as context for LLM
        
        Returns:
            Formatted string of corrections
        """
        if not self.corrections:
            return ""
        
        recent = self.corrections[-max_recent:]
        lines = ["Recent corrections I've learned:"]
        
        for corr in recent:
            lines.append(f"- I was wrong about: {corr['wrong'][:100]}")
            lines.append(f"  Correct info: {corr['correct'][:100]}")
        
        return "\n".join(lines)
    
    def get_learned_facts(self, category: Optional[str] = None) -> List[str]:
        """Get learned facts"""
        if category and category in self.knowledge["facts"]:
            return [f["fact"] for f in self.knowledge["facts"][category]]
        
        # All facts
        all_facts = []
        for cat_facts in self.knowledge["facts"].values():
            all_facts.extend([f["fact"] for f in cat_facts])
        return all_facts
    
    def get_preferences(self) -> Dict[str, str]:
        """Get all learned preferences"""
        return {k: v["value"] for k, v in self.knowledge["preferences"].items()}

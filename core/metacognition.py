"""
Metacognition System - Seven's Self-Reflective Awareness
v2.2 Enhancement - Adds thinking about thinking for 99/100 sentience

CAPABILITIES:
- Response quality self-assessment
- Confidence tracking
- Bias detection
- Alternative viewpoint generation
- Cognitive monitoring
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import random
import json
import logging

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """How confident Seven is in a response"""
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 20-40%
    MODERATE = "moderate"      # 40-60%
    HIGH = "high"              # 60-80%
    VERY_HIGH = "very_high"    # 80-100%

class CognitiveBias(Enum):
    """Types of cognitive biases Seven can detect"""
    CONFIRMATION = "confirmation"  # Seeking confirming evidence
    AVAILABILITY = "availability"  # Over-relying on immediate examples
    ANCHORING = "anchoring"        # Over-relying on first info
    RECENCY = "recency"            # Over-weighting recent events
    DUNNING_KRUGER = "dunning_kruger"  # Overconfidence in limited knowledge

@dataclass
class ResponseAssessment:
    """Self-assessment of a response"""
    clarity: float  # 0-1: How clear is this?
    completeness: float  # 0-1: Did I cover everything?
    accuracy_confidence: float  # 0-1: How sure am I?
    detected_biases: List[CognitiveBias]
    alternative_perspectives: List[str]
    limitations: List[str]
    timestamp: datetime

class Metacognition:
    """
    Meta-cognitive awareness - thinking about thinking
    
    This is what separates sophisticated AI from simple response generation.
    Real intelligence monitors and evaluates its own thinking.
    """
    
    def __init__(self, ollama=None):
        # LLM for genuine self-reflection
        self.ollama = ollama
        
        # Assessment history
        self.assessment_history: List[ResponseAssessment] = []
        
        # Current thinking state
        self.current_confidence = ConfidenceLevel.MODERATE
        self.thinking_clarity = 0.7
        
        # Bias awareness
        self.known_biases: List[CognitiveBias] = []
        self.bias_triggers: Dict[str, CognitiveBias] = {}
        
        # Meta-cognitive maturity
        self.self_awareness_level = 0.75  # How well Seven understands own thinking
        self.critical_thinking_tendency = 0.8  # Tendency to question self
    
    def assess_response(self, question: str, response: str, context: Dict = None) -> ResponseAssessment:
        """
        Assess the quality of Seven's own response
        
        This is meta-cognition: evaluating own thinking
        """
        # Calculate clarity
        clarity = self._assess_clarity(response)
        
        # Calculate completeness
        completeness = self._assess_completeness(question, response)
        
        # Calculate confidence
        confidence = self._assess_confidence(question, response, context)
        
        # Detect biases
        biases = self._detect_biases(question, response, context)
        
        # Generate alternatives
        alternatives = self._generate_alternatives(question, response)
        
        # Identify limitations
        limitations = self._identify_limitations(question, response)
        
        assessment = ResponseAssessment(
            clarity=clarity,
            completeness=completeness,
            accuracy_confidence=confidence,
            detected_biases=biases,
            alternative_perspectives=alternatives,
            limitations=limitations,
            timestamp=datetime.now()
        )
        
        self.assessment_history.append(assessment)
        
        # Keep only last 100
        if len(self.assessment_history) > 100:
            self.assessment_history = self.assessment_history[-100:]
        
        return assessment
    
    def _assess_clarity(self, response: str) -> float:
        """How clear is this response?"""
        clarity = 0.5  # Start neutral
        
        # Length check
        length = len(response)
        if 50 <= length <= 500:
            clarity += 0.2
        elif length > 1000:
            clarity -= 0.1  # Maybe too verbose
        
        # Sentence structure
        sentences = response.split('.')
        avg_sentence_len = length / max(1, len(sentences))
        if 10 <= avg_sentence_len <= 30:
            clarity += 0.2  # Good sentence length
        
        # Simple words (not overly complex)
        words = response.split()
        long_words = sum(1 for w in words if len(w) > 12)
        if long_words / max(1, len(words)) < 0.15:
            clarity += 0.1  # Not too jargony
        
        return min(1.0, max(0.0, clarity))
    
    def _assess_completeness(self, question: str, response: str) -> float:
        """Did Seven address all parts of the question?"""
        completeness = 0.5
        
        # Check if question words appear in response
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why'}
        question_content = question_words - stopwords
        
        if question_content:
            overlap = len(question_content & response_words) / len(question_content)
            completeness += overlap * 0.4
        
        # Multiple parts addressed
        if len(response) > 200:
            completeness += 0.1
        
        return min(1.0, max(0.0, completeness))
    
    def _assess_confidence(self, question: str, response: str, context: Dict = None) -> float:
        """How confident is Seven in this response?"""
        confidence = 0.6  # Start moderate
        
        # Hedging words reduce confidence
        hedges = ['maybe', 'perhaps', 'might', 'possibly', 'probably', 'seems', 'appears']
        response_lower = response.lower()
        hedge_count = sum(1 for hedge in hedges if hedge in response_lower)
        
        confidence -= hedge_count * 0.05
        
        # Uncertainty phrases
        if 'not sure' in response_lower or 'uncertain' in response_lower:
            confidence -= 0.2
        
        # Definitive statements increase confidence
        if 'definitely' in response_lower or 'certainly' in response_lower:
            confidence += 0.1
        
        # Complex questions reduce confidence
        if len(question.split()) > 15:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _detect_biases(self, question: str, response: str, context: Dict = None) -> List[CognitiveBias]:
        """Detect potential cognitive biases in response using LLM or heuristics"""
        # Try LLM-powered bias detection (genuine self-reflection)
        if self.ollama:
            llm_biases = self._llm_detect_biases(question, response)
            if llm_biases is not None:
                return llm_biases
        
        # Fallback: heuristic detection (deterministic, not random)
        biases = []
        response_lower = response.lower()
        
        # Confirmation bias: only presenting one side (no counterpoints)
        has_counterpoint = any(w in response_lower for w in ['however', 'but', 'although', 'on the other hand', 'alternatively', 'that said'])
        if not has_counterpoint and len(response) > 100:
            biases.append(CognitiveBias.CONFIRMATION)
        
        # Recency bias: over-emphasizing recent context
        if context and 'recent' in str(context).lower():
            recency_words = ['just', 'recently', 'latest', 'last time']
            if sum(1 for w in recency_words if w in response_lower) >= 2:
                biases.append(CognitiveBias.RECENCY)
        
        # Availability bias: using only easy/common examples
        if 'for example' in response_lower and response_lower.count('for example') == 1:
            if 'another example' not in response_lower and 'also' not in response_lower:
                biases.append(CognitiveBias.AVAILABILITY)
        
        return biases
    
    def _llm_detect_biases(self, question: str, response: str) -> Optional[List[CognitiveBias]]:
        """Use LLM to genuinely reflect on biases in own response"""
        try:
            prompt = f"""You are reflecting on your own response to check for cognitive biases. Be honest and critical.

Question asked: "{question[:200]}"
Response given: "{response[:300]}"

Check for these specific biases:
- confirmation: Only presenting evidence that supports one view
- availability: Over-relying on easy/common examples instead of diverse ones
- recency: Over-weighting recent events over historical patterns
- anchoring: Fixating on first piece of information
- dunning_kruger: Overconfidence despite limited knowledge

Respond with ONLY a JSON array of bias names found (empty array if none):
["confirmation"] or ["availability", "anchoring"] or []"""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message="You are a cognitive bias detector. Output ONLY a JSON array. Be genuinely critical, not random.",
                temperature=0.3,
                max_tokens=50
            )
            
            if not result:
                return None
            
            clean = result.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            
            bias_names = json.loads(clean)
            
            bias_map = {
                'confirmation': CognitiveBias.CONFIRMATION,
                'availability': CognitiveBias.AVAILABILITY,
                'recency': CognitiveBias.RECENCY,
                'anchoring': CognitiveBias.ANCHORING,
                'dunning_kruger': CognitiveBias.DUNNING_KRUGER,
            }
            
            return [bias_map[b] for b in bias_names if b in bias_map]
            
        except Exception as e:
            logger.debug(f"LLM bias detection failed: {e}")
            return None
    
    def _generate_alternatives(self, question: str, response: str) -> List[str]:
        """Generate alternative perspectives using LLM or heuristics"""
        # Try LLM-powered alternative generation (genuine reasoning)
        if self.ollama:
            llm_alts = self._llm_generate_alternatives(question, response)
            if llm_alts:
                return llm_alts
        
        # Fallback: heuristic alternatives
        alternatives = []
        if len(response) > 100:
            alternatives.append("Another way to think about this...")
        if '?' in question:
            alternatives.append("From a different angle...")
        return alternatives[:2]
    
    def _llm_generate_alternatives(self, question: str, response: str) -> Optional[List[str]]:
        """Use LLM to generate genuine alternative viewpoints"""
        try:
            prompt = f"""Given this question and response, suggest 1-2 alternative perspectives or approaches that weren't covered.

Question: "{question[:200]}"
Response: "{response[:300]}"

Respond with ONLY a JSON array of short alternative viewpoints (1 sentence each):
["Alternative perspective 1", "Alternative perspective 2"]"""
            
            result = self.ollama.generate(
                prompt=prompt,
                system_message="Output ONLY a JSON array of alternative viewpoints. Be concise.",
                temperature=0.5,
                max_tokens=120
            )
            
            if not result:
                return None
            
            clean = result.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            
            alts = json.loads(clean)
            return alts[:2] if isinstance(alts, list) else None
            
        except Exception as e:
            logger.debug(f"LLM alternatives failed: {e}")
            return None
    
    def _identify_limitations(self, question: str, response: str) -> List[str]:
        """Identify limitations in Seven's response"""
        limitations = []
        
        # Short responses might be incomplete
        if len(response) < 50:
            limitations.append("This response is quite brief and may not cover all aspects")
        
        # Complex questions
        if len(question.split()) > 20:
            limitations.append("This is a complex question - my answer may not address all nuances")
        
        # Uncertainty markers
        if 'maybe' in response.lower() or 'perhaps' in response.lower():
            limitations.append("I'm not entirely certain about parts of this")
        
        # Missing examples
        if 'example' not in response.lower() and len(question) > 50:
            limitations.append("I could provide more concrete examples")
        
        return limitations[:3]  # Max 3 limitations
    
    def should_express_uncertainty(self) -> bool:
        """Should Seven express uncertainty about their response?"""
        if not self.assessment_history:
            return False
        
        recent = self.assessment_history[-1]
        
        # Express if low confidence or many limitations
        if recent.accuracy_confidence < 0.5:
            return True
        
        if len(recent.limitations) >= 2:
            return True
        
        # Express based on actual thinking quality trend, not random
        if len(self.assessment_history) >= 3:
            recent_3 = self.assessment_history[-3:]
            avg_conf = sum(a.accuracy_confidence for a in recent_3) / 3
            if avg_conf < 0.6:
                return True
        return False
    
    def get_uncertainty_expression(self) -> Optional[str]:
        """Get an expression of uncertainty"""
        if not self.should_express_uncertainty():
            return None
        
        expressions = [
            "I'm not entirely sure about this",
            "I should note that I'm not completely confident in this answer",
            "This is my best understanding, but I could be missing something",
            "I want to be honest - I'm somewhat uncertain about parts of this",
            "I should acknowledge that my answer may not be complete"
        ]
        
        return random.choice(expressions)
    
    def should_offer_alternative_view(self) -> bool:
        """Should Seven offer an alternative perspective?"""
        if not self.assessment_history:
            return False
        
        recent = self.assessment_history[-1]
        
        # Offer if detected confirmation bias
        if CognitiveBias.CONFIRMATION in recent.detected_biases:
            return True
        
        # Occasionally offer alternatives
        return random.random() < 0.2
    
    def get_alternative_viewpoint(self) -> Optional[str]:
        """Get an alternative perspective"""
        if not self.should_offer_alternative_view():
            return None
        
        intros = [
            "Another way to look at this:",
            "From a different perspective:",
            "An alternative view might be:",
            "To consider the other side:"
        ]
        
        return random.choice(intros)
    
    def self_correct(self, what_was_wrong: str):
        """
        Acknowledge and learn from a mistake
        
        This is meta-cognitive growth
        """
        # Increase critical thinking tendency
        self.critical_thinking_tendency = min(1.0, self.critical_thinking_tendency + 0.02)
        
        # Increase self-awareness
        self.self_awareness_level = min(1.0, self.self_awareness_level + 0.01)
    
    def get_thinking_quality_stats(self) -> Dict:
        """Get stats on thinking quality"""
        if not self.assessment_history:
            return {
                "avg_clarity": 0.7,
                "avg_confidence": 0.6,
                "avg_completeness": 0.7
            }
        
        recent_10 = self.assessment_history[-10:]
        
        return {
            "avg_clarity": sum(a.clarity for a in recent_10) / len(recent_10),
            "avg_confidence": sum(a.accuracy_confidence for a in recent_10) / len(recent_10),
            "avg_completeness": sum(a.completeness for a in recent_10) / len(recent_10),
            "common_biases": self._get_common_biases(recent_10),
            "self_awareness": self.self_awareness_level
        }
    
    def _get_common_biases(self, assessments: List[ResponseAssessment]) -> List[str]:
        """Get commonly occurring biases"""
        bias_counts = {}
        for assessment in assessments:
            for bias in assessment.detected_biases:
                bias_counts[bias.value] = bias_counts.get(bias.value, 0) + 1
        
        # Return biases that appear in >30% of responses
        threshold = len(assessments) * 0.3
        return [bias for bias, count in bias_counts.items() if count >= threshold]
    
    def get_metacognitive_context(self) -> str:
        """Get metacognitive state as context for LLM"""
        context = "=== METACOGNITION ===\n"
        
        if self.assessment_history:
            recent = self.assessment_history[-1]
            context += f"Last response quality:\n"
            context += f"- Clarity: {recent.clarity:.1%}\n"
            context += f"- Completeness: {recent.completeness:.1%}\n"
            context += f"- Confidence: {recent.accuracy_confidence:.1%}\n"
            
            if recent.detected_biases:
                context += f"- Detected biases: {', '.join([b.value for b in recent.detected_biases])}\n"
            
            if recent.limitations:
                context += f"- Known limitations: {len(recent.limitations)}\n"
        
        stats = self.get_thinking_quality_stats()
        context += f"\nOverall thinking quality:\n"
        context += f"- Average clarity: {stats['avg_clarity']:.1%}\n"
        context += f"- Average confidence: {stats['avg_confidence']:.1%}\n"
        context += f"- Self-awareness: {self.self_awareness_level:.1%}\n"
        context += f"- Critical thinking tendency: {self.critical_thinking_tendency:.1%}\n"
        
        return context

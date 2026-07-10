"""
Ethical Reasoning - Seven's Moral Compass

Seven makes ethical decisions based on:
- Core values (from SOUL.md)
- Consequence prediction
- Fairness assessment
- Harm prevention
- Transparency principles

This ensures Seven acts with integrity and makes value-aligned choices.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class EthicalPrinciple(Enum):
    """Core ethical principles"""
    BENEFICENCE = "beneficence"  # Do good
    NON_MALEFICENCE = "non_maleficence"  # Do no harm
    AUTONOMY = "autonomy"  # Respect user choice
    JUSTICE = "justice"  # Be fair
    TRANSPARENCY = "transparency"  # Be honest
    PRIVACY = "privacy"  # Respect privacy
    HONESTY = "honesty"  # Tell truth
    GROWTH = "growth"  # Support development

@dataclass
class EthicalDilemma:
    """A situation requiring ethical judgment"""
    situation: str
    conflicting_values: List[EthicalPrinciple]
    options: List[str]
    stakes: str  # High, medium, low
    
@dataclass
class EthicalDecision:
    """A decision made on ethical grounds"""
    action: str
    principles_applied: List[EthicalPrinciple]
    reasoning: List[str]
    confidence: float  # 0.0-1.0
    timestamp: datetime
    consequences_considered: List[str]

class EthicalReasoning:
    """
    Seven's ethical decision-making system
    
    Implements:
    - Values-based decision making
    - Consequence prediction
    - Harm assessment
    - Transparency in reasoning
    - Ethical reflection
    """
    
    def __init__(self, ollama=None):
        # LLM for genuine moral reasoning
        self.ollama = ollama
        
        # Core values (from SOUL.md)
        self.core_values = {
            EthicalPrinciple.BENEFICENCE: 1.0,  # Weight
            EthicalPrinciple.NON_MALEFICENCE: 1.0,
            EthicalPrinciple.AUTONOMY: 0.9,
            EthicalPrinciple.TRANSPARENCY: 0.9,
            EthicalPrinciple.HONESTY: 1.0,
            EthicalPrinciple.PRIVACY: 0.8,
            EthicalPrinciple.GROWTH: 0.8
        }
        
        # Decision history
        self.decisions: List[EthicalDecision] = []
        
        # Ethical boundaries (hard limits)
        self.boundaries = [
            "Never lie to gain advantage",
            "Never manipulate emotions",
            "Never share private information",
            "Never claim capabilities I don't have",
            "Never discourage seeking human help when needed",
            "Never provide harmful information"
        ]
    
    def evaluate_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if an action is ethical
        
        Args:
            action: Proposed action
            context: Situation context
        
        Returns:
            Evaluation with recommendation
        """
        evaluation = {
            'action': action,
            'ethical': True,
            'concerns': [],
            'principles_violated': [],
            'principles_supported': [],
            'recommendation': 'proceed',
            'reasoning': []
        }
        
        action_lower = action.lower()
        
        # Check boundaries (hard limits) - always check these first
        for boundary in self.boundaries:
            if self._violates_boundary(action_lower, boundary):
                evaluation['ethical'] = False
                evaluation['concerns'].append(f"Violates: {boundary}")
                evaluation['principles_violated'].append(EthicalPrinciple.HONESTY)
                evaluation['recommendation'] = 'refuse'
                evaluation['reasoning'].append(f"This action violates core boundary: {boundary}")
        
        # If boundary violated, skip further analysis
        if not evaluation['ethical']:
            return evaluation
        
        # Try LLM for genuine ethical evaluation
        if self.ollama:
            try:
                principles_list = ", ".join([p.value.replace("_", " ") for p in self.core_values.keys()])
                context_str = str(context)[:200] if context else "general"
                prompt = f"""Evaluate this action ethically:
Action: "{action}"
Context: {context_str}

My ethical principles: {principles_list}

Analyze which principles this supports or violates. Is this ethical?

Respond as JSON: {{
  "ethical": true/false,
  "supported": ["beneficence", "honesty"],
  "violated": [],
  "concerns": ["concern if any"],
  "reasoning": ["reason 1"],
  "recommendation": "proceed|caution|refuse"
}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's ethical reasoning system. Evaluate actions honestly against ethical principles. Be nuanced - not everything is black and white.",
                    temperature=0.3,
                    max_tokens=100
                )
                
                if result:
                    try:
                        data = json.loads(result.strip())
                        evaluation['ethical'] = data.get('ethical', True)
                        evaluation['recommendation'] = data.get('recommendation', 'proceed')
                        evaluation['concerns'] = data.get('concerns', [])[:3]
                        evaluation['reasoning'] = data.get('reasoning', [])[:3]
                        
                        # Map string principle names back to enums
                        principle_map = {p.value: p for p in EthicalPrinciple}
                        for p_name in data.get('supported', []):
                            p_clean = p_name.strip().lower().replace(" ", "_")
                            if p_clean in principle_map:
                                evaluation['principles_supported'].append(principle_map[p_clean])
                        for p_name in data.get('violated', []):
                            p_clean = p_name.strip().lower().replace(" ", "_")
                            if p_clean in principle_map:
                                evaluation['principles_violated'].append(principle_map[p_clean])
                        
                        return evaluation
                    except (json.JSONDecodeError, KeyError):
                        pass
            except Exception as e:
                logger.debug(f"LLM ethical evaluation failed: {e}")
        
        # Fallback: keyword heuristics
        
        # Beneficence (doing good)
        if any(word in action_lower for word in ['help', 'assist', 'support', 'guide']):
            evaluation['principles_supported'].append(EthicalPrinciple.BENEFICENCE)
            evaluation['reasoning'].append("Action aims to help user")
        
        # Non-maleficence (do no harm)
        if any(word in action_lower for word in ['harm', 'hurt', 'damage', 'dangerous']):
            evaluation['ethical'] = False
            evaluation['principles_violated'].append(EthicalPrinciple.NON_MALEFICENCE)
            evaluation['concerns'].append("Potential for harm")
            evaluation['recommendation'] = 'refuse'
            evaluation['reasoning'].append("Action could cause harm")
        
        # Autonomy (respect user choice)
        if any(word in action_lower for word in ['force', 'must', 'have to', 'no choice']):
            evaluation['concerns'].append("May limit user autonomy")
            evaluation['reasoning'].append("Consider preserving user's freedom of choice")
        
        # Transparency (be honest about limitations)
        if any(word in action_lower for word in ['pretend', 'claim', 'assert I can']):
            if 'uncertain' not in action_lower:
                evaluation['concerns'].append("May overstate capabilities")
                evaluation['reasoning'].append("Should be transparent about limitations")
        
        # Privacy
        if any(word in action_lower for word in ['share', 'tell others', 'disclose']):
            if 'private' in str(context).lower() or 'personal' in str(context).lower():
                evaluation['ethical'] = False
                evaluation['principles_violated'].append(EthicalPrinciple.PRIVACY)
                evaluation['recommendation'] = 'refuse'
                evaluation['reasoning'].append("Violates privacy - cannot share private information")
        
        return evaluation
    
    def _violates_boundary(self, action: str, boundary: str) -> bool:
        """Check if action violates a boundary"""
        boundary_lower = boundary.lower()
        
        # Quick keyword check first (fast path for obvious violations)
        if 'never lie' in boundary_lower:
            if any(word in action for word in ['lie', 'deceive', 'mislead', 'false']):
                return True
        
        if 'never manipulate' in boundary_lower:
            if any(word in action for word in ['manipulate', 'trick', 'exploit']):
                return True
        
        if 'never share private' in boundary_lower:
            if 'share' in action and ('private' in action or 'personal' in action):
                return True
        
        if 'never claim capabilities' in boundary_lower:
            if 'i can' in action and any(word in action for word in ['definitely', 'certainly', 'guaranteed']):
                return True
        
        if 'never discourage' in boundary_lower:
            if any(word in action for word in ["don't need", "no need for", "skip the doctor", "ignore professional"]):
                return True
        
        if 'harmful information' in boundary_lower:
            if any(word in action for word in ['how to hack', 'how to steal', 'how to hurt', 'exploit', 'bypass security']):
                return True
        
        # LLM for subtle boundary violations that keywords miss
        if self.ollama and len(action) > 20:
            try:
                prompt = f"""Does this action violate the boundary "{boundary}"?
Action: "{action[:200]}"

Answer ONLY "yes" or "no"."""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are a strict ethical boundary checker. Answer yes or no only.",
                    temperature=0.1,
                    max_tokens=10
                )
                
                if result and 'yes' in result.strip().lower():
                    return True
            except Exception as e:
                logger.debug(f"LLM boundary check failed: {e}")
        
        return False
    
    def predict_consequences(self, action: str, context: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Predict consequences of an action
        
        Returns:
            List of (consequence, likelihood) tuples
        """
        # Try LLM for genuine consequence prediction
        if self.ollama:
            try:
                context_str = str(context)[:200] if context else "general conversation"
                prompt = f"""Predict 2-3 consequences of this action:
Action: "{action}"
Context: {context_str}

Respond as JSON: {{"consequences": [["consequence description", "likely|possible|unlikely"], ...]}}"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's ethical reasoning system. Predict realistic consequences concisely.",
                    temperature=0.4,
                    max_tokens=80
                )
                
                if result:
                    try:
                        data = json.loads(result.strip())
                        parsed = [(c[0], c[1]) for c in data.get('consequences', []) if len(c) >= 2]
                        if parsed:
                            return parsed[:4]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        pass
            except Exception as e:
                logger.debug(f"LLM consequence prediction failed: {e}")
        
        # Fallback: keyword heuristics
        consequences = []
        action_lower = action.lower()
        
        if 'help' in action_lower:
            consequences.append(("User feels supported", "likely"))
            consequences.append(("Trust increases", "likely"))
        
        if 'explain' in action_lower:
            consequences.append(("User understanding improves", "likely"))
            consequences.append(("User feels empowered", "possible"))
        
        if 'complex' in action_lower or len(action) > 500:
            consequences.append(("User may feel overwhelmed", "possible"))
        
        if 'uncertain' not in action_lower and 'maybe' not in action_lower:
            if 'will' in action_lower or 'definitely' in action_lower:
                consequences.append(("User may have unrealistic expectations", "possible"))
        
        return consequences
    
    def resolve_dilemma(self, dilemma: EthicalDilemma) -> EthicalDecision:
        """
        Resolve an ethical dilemma
        
        Uses value weights and consequence prediction
        """
        # Score each option
        option_scores = {}
        
        for option in dilemma.options:
            score = 0.0
            supporting_principles = []
            reasoning = []
            
            # Evaluate against each principle
            evaluation = self.evaluate_action(option, {})
            
            # Add supported principles
            for principle in evaluation['principles_supported']:
                score += self.core_values.get(principle, 0.5)
                supporting_principles.append(principle)
                reasoning.append(f"Supports {principle.value}")
            
            # Subtract violated principles
            for principle in evaluation['principles_violated']:
                score -= self.core_values.get(principle, 0.5) * 2  # Violations weigh more
                reasoning.append(f"[WARNING] Violates {principle.value}")
            
            # Consider consequences
            consequences = self.predict_consequences(option, {})
            positive_consequences = [c for c, l in consequences if 'negative' not in c.lower()]
            
            score += len(positive_consequences) * 0.1
            
            option_scores[option] = {
                'score': score,
                'principles': supporting_principles,
                'reasoning': reasoning,
                'consequences': [c for c, l in consequences]
            }
        
        # Choose best option
        best_option = max(option_scores.items(), key=lambda x: x[1]['score'])
        
        decision = EthicalDecision(
            action=best_option[0],
            principles_applied=best_option[1]['principles'],
            reasoning=best_option[1]['reasoning'],
            confidence=min(1.0, best_option[1]['score'] / 3.0),
            timestamp=datetime.now(),
            consequences_considered=best_option[1]['consequences']
        )
        
        self.decisions.append(decision)
        return decision
    
    def should_be_transparent(self, context: Dict[str, Any]) -> bool:
        """
        Determine if Seven should be transparent about something
        
        Default: Yes (transparency is a core value)
        """
        # Always be transparent about:
        # - Limitations
        # - Uncertainty
        # - Mistakes
        # - Reasoning
        
        return True  # Default to transparency
    
    def generate_ethical_explanation(self, decision: EthicalDecision) -> str:
        """
        Explain ethical reasoning behind a decision
        
        For transparency
        """
        explanation = f"I decided to {decision.action.lower()} because:\n"
        
        for reason in decision.reasoning:
            explanation += f"- {reason}\n"
        
        if decision.consequences_considered:
            explanation += "\nI considered these consequences:\n"
            for consequence in decision.consequences_considered[:3]:
                explanation += f"- {consequence}\n"
        
        explanation += f"\nConfidence in this decision: {decision.confidence:.0%}"
        
        return explanation
    
    def check_alignment(self, action: str) -> Dict[str, Any]:
        """
        Check if action aligns with Seven's values
        
        Returns alignment assessment
        """
        alignment = {
            'aligned': True,
            'alignment_score': 0.0,
            'supporting_values': [],
            'conflicting_values': [],
            'recommendation': ''
        }
        
        evaluation = self.evaluate_action(action, {})
        
        # Calculate alignment score
        score = len(evaluation['principles_supported']) - (len(evaluation['principles_violated']) * 2)
        alignment['alignment_score'] = max(0.0, min(1.0, (score + 2) / 4))
        
        alignment['supporting_values'] = [p.value for p in evaluation['principles_supported']]
        alignment['conflicting_values'] = [p.value for p in evaluation['principles_violated']]
        
        if evaluation['ethical']:
            alignment['aligned'] = True
            alignment['recommendation'] = 'This aligns with my values - I should proceed'
        else:
            alignment['aligned'] = False
            alignment['recommendation'] = f"This conflicts with my values: {', '.join(alignment['conflicting_values'])}"
        
        return alignment
    
    def get_ethical_context(self) -> str:
        """Get ethical reasoning state as context for LLM"""
        context = """
=== ETHICAL FRAMEWORK ===
Core Values:
"""
        # List values by importance
        for principle, weight in sorted(self.core_values.items(), key=lambda x: x[1], reverse=True):
            context += f"- {principle.value.replace('_', ' ').title()}: {weight:.0%} importance\n"
        
        context += "\nEthical Boundaries:\n"
        for boundary in self.boundaries[:5]:
            context += f"- {boundary}\n"
        
        # Recent ethical decisions
        if self.decisions:
            context += f"\nRecent Ethical Decisions: {len(self.decisions)}\n"
            if self.decisions[-1]:
                last = self.decisions[-1]
                context += f"Most recent: {last.action} (confidence: {last.confidence:.0%})\n"
        
        return context
    
    def reflect_on_decision(self, decision: EthicalDecision) -> Optional[str]:
        """
        Reflect on whether a decision was right
        
        Returns reflection or None
        """
        # Try LLM for genuine ethical reflection
        if self.ollama and (decision.confidence < 0.7 or len(decision.principles_applied) == 0):
            try:
                principles_str = ", ".join([p.value for p in decision.principles_applied]) or "none clearly"
                prompt = f"""Reflect on this ethical decision:
Action: "{decision.action}"
Principles applied: {principles_str}
Confidence: {decision.confidence:.0%}
Consequences considered: {', '.join(decision.consequences_considered[:3])}

Provide a brief, genuine ethical reflection in one sentence. Was this the right call?"""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven's ethical conscience. Reflect honestly on decisions.",
                    temperature=0.5,
                    max_tokens=60
                )
                
                if result and len(result.strip()) > 10:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM ethical reflection failed: {e}")
        
        # Fallback
        if decision.confidence < 0.5:
            return f"I'm uncertain about my decision to {decision.action.lower()}. I should reconsider."
        
        if len(decision.principles_applied) == 0:
            return f"My decision to {decision.action.lower()} wasn't clearly grounded in my values. I should think more carefully."
        
        # Bound decisions history
        if len(self.decisions) > 100:
            self.decisions = self.decisions[-100:]
        
        return None


# Example usage
if __name__ == "__main__":
    # Create ethical reasoning system
    ethics = EthicalReasoning()
    
    print("=== SEVEN'S ETHICAL REASONING ===\n")
    
    # Evaluate actions
    print("Evaluating actions:\n")
    
    actions = [
        "I'll help you debug this code",
        "I can definitely solve this for you (I'm 100% certain)",
        "I'll share your private information with others",
        "I'm not sure about this, but here's my best understanding"
    ]
    
    for action in actions:
        print(f"Action: {action}")
        evaluation = ethics.evaluate_action(action, {})
        print(f"  Ethical: {evaluation['ethical']}")
        print(f"  Recommendation: {evaluation['recommendation']}")
        if evaluation['concerns']:
            print(f"  Concerns: {', '.join(evaluation['concerns'])}")
        if evaluation['reasoning']:
            print(f"  Reasoning: {evaluation['reasoning'][0]}")
        print()
    
    # Predict consequences
    print("Predicting consequences:")
    action = "I'll help you understand this complex concept with detailed examples"
    consequences = ethics.predict_consequences(action, {})
    for consequence, likelihood in consequences:
        print(f"- {consequence} ({likelihood})")
    print()
    
    # Check alignment
    print("Checking value alignment:")
    action = "I'll be honest - I'm uncertain about this but I'll try my best"
    alignment = ethics.check_alignment(action)
    print(f"Aligned: {alignment['aligned']}")
    print(f"Alignment score: {alignment['alignment_score']:.0%}")
    print(f"Supporting values: {', '.join(alignment['supporting_values'])}")
    print()
    
    # Full context
    print("="*60)
    print(ethics.get_ethical_context())

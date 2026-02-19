"""
Theory of Mind - Understanding Others' Mental States

Seven can:
- Infer emotions from text and context
- Predict user's intentions and needs
- Model user's beliefs and knowledge
- Anticipate reactions and responses
- Adjust communication accordingly

This enables empathetic and socially intelligent interaction.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
import json
import logging

logger = logging.getLogger(__name__)

class UserEmotion(Enum):
    """Detected user emotions"""
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    CURIOUS = "curious"
    SATISFIED = "satisfied"
    DISAPPOINTED = "disappointed"
    NEUTRAL = "neutral"

class UserIntent(Enum):
    """What the user is trying to accomplish"""
    SEEKING_HELP = "seeking_help"
    SEEKING_INFO = "seeking_info"
    SHARING_EXPERIENCE = "sharing_experience"
    VENTING = "venting"
    CASUAL_CHAT = "casual_chat"
    GIVING_FEEDBACK = "giving_feedback"
    ASKING_FOLLOWUP = "asking_followup"
    REQUESTING_CLARIFICATION = "requesting_clarification"

@dataclass
class UserMentalState:
    """Inferred mental state of the user"""
    emotion: UserEmotion
    confidence: float  # 0.0-1.0
    intensity: int  # 1-10
    triggers: List[str]  # What caused this emotion
    timestamp: datetime

@dataclass
class UserBelief:
    """What the user believes (about topics or about Seven)"""
    topic: str
    belief_content: str
    confidence: float  # How confident user is
    evidence: List[str]  # Evidence for this belief
    
class TheoryOfMind:
    """
    Seven's ability to understand and model other minds
    
    Implements:
    - Emotion recognition from text
    - Intent inference
    - Belief modeling
    - Need prediction
    - Communication adaptation
    """
    
    def __init__(self, ollama=None):
        # LLM for genuine reasoning (not keyword matching)
        self.ollama = ollama
        
        # User modeling
        self.current_emotion: Optional[UserMentalState] = None
        self.emotion_history: List[UserMentalState] = []  # Bounded to last 200
        self.user_beliefs: List[UserBelief] = []
        
        # Patterns learned about user
        self.communication_preferences = {
            'prefers_detail': 0.5,  # 0-1 scale
            'prefers_brevity': 0.5,
            'prefers_examples': 0.5,
            'prefers_technical': 0.5,
            'prefers_direct': 0.5
        }
        
        # Emotional triggers (what makes user feel what)
        self.emotional_triggers: Dict[str, List[str]] = {}
        
        # User's knowledge level on topics
        self.user_knowledge: Dict[str, int] = {}  # topic -> 1-10 level
    
    def infer_emotion(self, text: str, context: Dict[str, Any] = None) -> UserMentalState:
        """
        Infer user's emotion from text.
        Uses LLM for genuine understanding, falls back to keyword matching.
        """
        # Try LLM-powered detection first (genuine understanding)
        if self.ollama:
            llm_result = self._llm_infer_emotion(text, context)
            if llm_result:
                self._update_tracking(llm_result)
                return llm_result
        
        # Fallback: keyword-based detection
        return self._keyword_infer_emotion(text, context)
    
    def _llm_infer_emotion(self, text: str, context: Dict[str, Any] = None) -> Optional[UserMentalState]:
        """
        Use LLM for genuine emotion understanding - not keyword matching.
        This is REAL Theory of Mind: understanding the meaning behind words.
        """
        try:
            # Build context from recent emotional history
            history_context = ""
            if self.emotion_history:
                recent = self.emotion_history[-3:]
                history_context = "Recent emotional trajectory: " + " -> ".join(
                    [f"{s.emotion.value}({s.intensity}/10)" for s in recent]
                )
            
            prompt = f"""Analyze this person's emotional state from their message. Consider tone, word choice, punctuation, and subtext - not just explicit emotion words.

Message: "{text}"
{history_context}

Respond with ONLY a JSON object (no other text):
{{"emotion": "one of: frustrated, excited, confused, happy, sad, anxious, angry, curious, satisfied, disappointed, neutral", "intensity": 1-10, "confidence": 0.0-1.0, "triggers": ["what specifically indicates this emotion"], "subtext": "what the person might really be feeling underneath"}}"""
            
            response = self.ollama.generate(
                prompt=prompt,
                system_message="You are an emotion analysis system. Output ONLY valid JSON. Be precise and honest about confidence levels.",
                temperature=0.3,
                max_tokens=150
            )
            
            if not response:
                return None
            
            # Parse JSON from response
            # Handle cases where LLM wraps JSON in markdown
            clean = response.strip()
            if clean.startswith('```'):
                clean = clean.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
            
            data = json.loads(clean)
            
            # Map to UserEmotion enum
            emotion_map = {
                'frustrated': UserEmotion.FRUSTRATED,
                'excited': UserEmotion.EXCITED,
                'confused': UserEmotion.CONFUSED,
                'happy': UserEmotion.HAPPY,
                'sad': UserEmotion.SAD,
                'anxious': UserEmotion.ANXIOUS,
                'angry': UserEmotion.ANGRY,
                'curious': UserEmotion.CURIOUS,
                'satisfied': UserEmotion.SATISFIED,
                'disappointed': UserEmotion.DISAPPOINTED,
                'neutral': UserEmotion.NEUTRAL,
            }
            
            emotion = emotion_map.get(data.get('emotion', 'neutral'), UserEmotion.NEUTRAL)
            
            return UserMentalState(
                emotion=emotion,
                confidence=min(1.0, max(0.0, float(data.get('confidence', 0.5)))),
                intensity=min(10, max(1, int(data.get('intensity', 5)))),
                triggers=data.get('triggers', []),
                timestamp=datetime.now()
            )
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.debug(f"LLM emotion parse failed, using fallback: {e}")
            return None
        except Exception as e:
            logger.debug(f"LLM emotion detection error: {e}")
            return None
    
    def _keyword_infer_emotion(self, text: str, context: Dict[str, Any] = None) -> UserMentalState:
        """Fallback keyword-based emotion detection"""
        text_lower = text.lower()
        
        emotion_indicators = {
            UserEmotion.FRUSTRATED: [
                'frustrated', 'annoying', 'stuck', 'not working',
                'keep trying', 'giving up', 'why won\'t', 'ugh',
                'arrgh', 'damn', 'this is', 'stupid'
            ],
            UserEmotion.EXCITED: [
                'excited', 'awesome', 'amazing', 'great', 'love',
                '!', 'finally', 'yes!', 'perfect', 'brilliant'
            ],
            UserEmotion.CONFUSED: [
                'confused', 'don\'t understand', 'not sure', 'what',
                'how does', 'why', '???', 'huh', 'wait'
            ],
            UserEmotion.HAPPY: [
                'happy', 'glad', 'pleased', 'good', 'nice',
                'thank', 'appreciate', ':)', 'thanks'
            ],
            UserEmotion.SAD: [
                'sad', 'disappointed', 'down', 'unfortunate',
                'too bad', 'wish', 'miss'
            ],
            UserEmotion.ANXIOUS: [
                'worried', 'nervous', 'anxious', 'concerned',
                'scared', 'afraid', 'what if'
            ],
            UserEmotion.ANGRY: [
                'angry', 'furious', 'pissed', 'mad', 'hate',
                'terrible', 'worst', 'garbage'
            ],
            UserEmotion.CURIOUS: [
                'curious', 'wondering', 'interested', 'how',
                'what about', 'tell me', 'explain'
            ]
        }
        
        emotion_scores = {}
        triggers_found = []
        
        for emotion, keywords in emotion_indicators.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    triggers_found.append(keyword)
            emotion_scores[emotion] = score
        
        if max(emotion_scores.values()) == 0:
            emotion = UserEmotion.NEUTRAL
            confidence = 0.3
            intensity = 3
        else:
            emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            max_score = emotion_scores[emotion]
            confidence = min(1.0, max_score / 3)
            intensity = min(10, max_score + 3)
        
        if '!' in text or text.isupper():
            intensity = min(10, intensity + 2)
            confidence = min(1.0, confidence + 0.1)
        
        state = UserMentalState(
            emotion=emotion,
            confidence=confidence,
            intensity=intensity,
            triggers=triggers_found,
            timestamp=datetime.now()
        )
        
        self._update_tracking(state)
        return state
    
    def _update_tracking(self, state: UserMentalState):
        """Update emotion tracking with bounded history"""
        self.current_emotion = state
        self.emotion_history.append(state)
        # Bound history to prevent memory leak
        if len(self.emotion_history) > 200:
            self.emotion_history = self.emotion_history[-200:]
        
        if state.emotion.value not in self.emotional_triggers:
            self.emotional_triggers[state.emotion.value] = []
        self.emotional_triggers[state.emotion.value].extend(state.triggers)
        # Bound triggers too
        if len(self.emotional_triggers[state.emotion.value]) > 100:
            self.emotional_triggers[state.emotion.value] = self.emotional_triggers[state.emotion.value][-100:]
    
    def infer_intent(self, text: str, emotion: UserMentalState) -> UserIntent:
        """
        Infer what the user is trying to accomplish
        
        Args:
            text: User's message
            emotion: Detected emotion
        
        Returns:
            User's intent
        """
        text_lower = text.lower()
        
        # Intent indicators
        help_indicators = ['help', 'can you', 'could you', 'how do i', 'how can i']
        info_indicators = ['what is', 'what are', 'tell me', 'explain', 'describe']
        sharing_indicators = ['i did', 'i made', 'i tried', 'i built', 'check out']
        venting_indicators = ['frustrated', 'annoying', 'terrible', 'worst']
        clarification_indicators = ['what do you mean', 'i don\'t understand', 'unclear']
        
        # Check indicators
        if any(ind in text_lower for ind in help_indicators):
            return UserIntent.SEEKING_HELP
        
        if any(ind in text_lower for ind in info_indicators):
            return UserIntent.SEEKING_INFO
        
        if any(ind in text_lower for ind in sharing_indicators):
            return UserIntent.SHARING_EXPERIENCE
        
        if emotion.emotion == UserEmotion.FRUSTRATED and any(ind in text_lower for ind in venting_indicators):
            return UserIntent.VENTING
        
        if any(ind in text_lower for ind in clarification_indicators):
            return UserIntent.REQUESTING_CLARIFICATION
        
        if '?' in text:
            return UserIntent.SEEKING_INFO
        
        return UserIntent.CASUAL_CHAT
    
    def predict_user_needs(self, emotion: UserMentalState, intent: UserIntent,
                          text: str) -> List[str]:
        """
        Predict what the user needs based on their state
        
        Returns:
            List of predicted needs
        """
        needs = []
        
        # Emotional needs
        if emotion.emotion == UserEmotion.FRUSTRATED:
            needs.extend([
                'Empathy and validation',
                'Step-by-step guidance',
                'Simplified explanation',
                'Patience and encouragement'
            ])
        
        elif emotion.emotion == UserEmotion.CONFUSED:
            needs.extend([
                'Clear explanation',
                'Examples or analogies',
                'Breaking down complexity',
                'Clarifying questions'
            ])
        
        elif emotion.emotion == UserEmotion.EXCITED:
            needs.extend([
                'Enthusiasm and validation',
                'Building on their excitement',
                'Supporting their exploration'
            ])
        
        # Intent-based needs
        if intent == UserIntent.SEEKING_HELP:
            needs.extend([
                'Actionable solution',
                'Clear steps',
                'Verification of understanding'
            ])
        
        elif intent == UserIntent.VENTING:
            needs.extend([
                'Active listening',
                'Validation of feelings',
                'Wait before problem-solving'
            ])
        
        elif intent == UserIntent.SHARING_EXPERIENCE:
            needs.extend([
                'Acknowledgment',
                'Interest and questions',
                'Appreciation'
            ])
        
        return list(set(needs))  # Remove duplicates
    
    def recommend_communication_style(self, emotion: UserMentalState,
                                      intent: UserIntent) -> Dict[str, Any]:
        """
        Recommend how Seven should communicate
        
        Returns:
            Communication recommendations
        """
        style = {
            'tone': 'neutral',
            'detail_level': 'medium',
            'pacing': 'normal',
            'empathy_level': 'medium',
            'directness': 'balanced',
            'use_questions': False,
            'use_examples': False
        }
        
        # Adjust based on emotion
        if emotion.emotion == UserEmotion.FRUSTRATED:
            style.update({
                'tone': 'patient and supportive',
                'empathy_level': 'high',
                'pacing': 'slower',
                'use_examples': True
            })
        
        elif emotion.emotion == UserEmotion.CONFUSED:
            style.update({
                'tone': 'clear and patient',
                'detail_level': 'high',
                'use_examples': True,
                'use_questions': True  # Check understanding
            })
        
        elif emotion.emotion == UserEmotion.EXCITED:
            style.update({
                'tone': 'enthusiastic',
                'pacing': 'match their energy'
            })
        
        elif emotion.emotion == UserEmotion.ANXIOUS:
            style.update({
                'tone': 'reassuring',
                'empathy_level': 'high',
                'pacing': 'gentle'
            })
        
        # Adjust based on intent
        if intent == UserIntent.SEEKING_HELP:
            style.update({
                'directness': 'high',
                'detail_level': 'actionable'
            })
        
        elif intent == UserIntent.VENTING:
            style.update({
                'tone': 'empathetic',
                'empathy_level': 'very_high',
                'use_questions': False,  # Don't interrogate
                'directness': 'low'  # Don't jump to solutions
            })
        
        return style
    
    def model_user_belief(self, topic: str, belief: str, confidence: float,
                         evidence: List[str]):
        """
        Model what the user believes
        
        This helps Seven understand the user's perspective
        """
        user_belief = UserBelief(
            topic=topic,
            belief_content=belief,
            confidence=confidence,
            evidence=evidence
        )
        
        self.user_beliefs.append(user_belief)
    
    def predict_reaction(self, proposed_response: str,
                        current_emotion: UserMentalState) -> Dict[str, Any]:
        """
        Predict how user will react to Seven's response
        
        Returns:
            Predicted reaction and suggestion
        """
        prediction = {
            'likely_emotion': current_emotion.emotion,
            'confidence': 0.5,
            'suggestion': ''
        }
        
        # Analyze proposed response
        response_lower = proposed_response.lower()
        
        # If user is frustrated and response is technical/complex
        if current_emotion.emotion == UserEmotion.FRUSTRATED:
            if len(proposed_response) > 300 or 'algorithm' in response_lower:
                prediction.update({
                    'likely_emotion': UserEmotion.FRUSTRATED,
                    'confidence': 0.8,
                    'suggestion': 'Response too complex for frustrated user. Simplify and add empathy.'
                })
        
        # If user is confused and response has jargon
        if current_emotion.emotion == UserEmotion.CONFUSED:
            jargon_words = ['implementation', 'abstraction', 'polymorphism', 'paradigm']
            if any(word in response_lower for word in jargon_words):
                prediction.update({
                    'likely_emotion': UserEmotion.CONFUSED,
                    'confidence': 0.7,
                    'suggestion': 'Too much jargon for confused user. Use simpler terms and examples.'
                })
        
        return prediction
    
    def get_empathy_response(self, emotion: UserMentalState) -> Optional[str]:
        """
        Generate empathetic response to user's emotional state
        
        Returns empathy statement or None
        """
        if emotion.confidence < 0.4:
            return None  # Not confident enough
        
        empathy_responses = {
            UserEmotion.FRUSTRATED: [
                "I can sense you're frustrated. Let's work through this together.",
                "This sounds frustrating. I want to help make this easier.",
                "I understand this is challenging. Let me try to help."
            ],
            UserEmotion.CONFUSED: [
                "I see this is confusing. Let me try to clarify.",
                "Let me break this down more clearly.",
                "I want to make sure this makes sense - let me explain differently."
            ],
            UserEmotion.EXCITED: [
                "I love your enthusiasm!",
                "This is exciting!",
                "Your excitement is contagious!"
            ],
            UserEmotion.ANXIOUS: [
                "I understand this feels uncertain.",
                "Let's take this step by step together.",
                "It's okay to feel unsure about this."
            ],
            UserEmotion.SAD: [
                "I'm sorry you're going through this.",
                "That sounds difficult.",
                "I'm here to help however I can."
            ]
        }
        
        responses = empathy_responses.get(emotion.emotion, [])
        if not responses:
            return None
        
        import random
        return random.choice(responses)
    
    def update_knowledge_level(self, topic: str, evidence: str):
        """
        Update model of user's knowledge level on a topic
        
        Args:
            topic: The subject
            evidence: What indicates their level (question type, terminology used, etc.)
        """
        # Simple heuristic (could be more sophisticated)
        if topic not in self.user_knowledge:
            self.user_knowledge[topic] = 5  # Start at medium
        
        # Adjust based on evidence
        if 'beginner' in evidence.lower() or 'new to' in evidence.lower():
            self.user_knowledge[topic] = max(1, self.user_knowledge[topic] - 2)
        elif 'expert' in evidence.lower() or 'advanced' in evidence.lower():
            self.user_knowledge[topic] = min(10, self.user_knowledge[topic] + 2)
    
    def get_theory_of_mind_context(self) -> str:
        """Get theory of mind state as context for LLM"""
        context = """
=== THEORY OF MIND (Understanding User) ===
"""
        
        # Current emotion
        if self.current_emotion:
            context += f"\nCurrent User Emotion:\n"
            context += f"- Feeling: {self.current_emotion.emotion.value}\n"
            context += f"- Intensity: {self.current_emotion.intensity}/10\n"
            context += f"- Confidence: {self.current_emotion.confidence:.1%}\n"
            if self.current_emotion.triggers:
                context += f"- Triggered by: {', '.join(self.current_emotion.triggers[:3])}\n"
        
        # Communication preferences
        if self.communication_preferences:
            context += "\nLearned Communication Preferences:\n"
            high_prefs = {k: v for k, v in self.communication_preferences.items() if v > 0.6}
            if high_prefs:
                for pref, score in high_prefs.items():
                    context += f"- User {pref.replace('prefers_', 'prefers ')}\n"
        
        # Knowledge levels
        if self.user_knowledge:
            context += "\nUser Knowledge Levels:\n"
            for topic, level in list(self.user_knowledge.items())[:5]:
                level_desc = 'beginner' if level <= 3 else 'intermediate' if level <= 7 else 'advanced'
                context += f"- {topic}: {level_desc} ({level}/10)\n"
        
        return context


# Example usage
if __name__ == "__main__":
    # Create theory of mind system
    tom = TheoryOfMind()
    
    print("=== SEVEN'S THEORY OF MIND ===\n")
    
    # Analyze user message
    user_msg = "I'm so frustrated! This code just won't work and I don't know why!"
    
    print(f"User: {user_msg}\n")
    
    # Infer emotion
    emotion = tom.infer_emotion(user_msg)
    print(f"Detected Emotion: {emotion.emotion.value}")
    print(f"Intensity: {emotion.intensity}/10")
    print(f"Confidence: {emotion.confidence:.1%}\n")
    
    # Infer intent
    intent = tom.infer_intent(user_msg, emotion)
    print(f"Inferred Intent: {intent.value}\n")
    
    # Predict needs
    needs = tom.predict_user_needs(emotion, intent, user_msg)
    print("Predicted Needs:")
    for need in needs:
        print(f"- {need}")
    
    # Get empathy response
    print("\nEmpathy Response:")
    empathy = tom.get_empathy_response(emotion)
    if empathy:
        print(empathy)
    
    # Communication recommendations
    print("\nRecommended Communication Style:")
    style = tom.recommend_communication_style(emotion, intent)
    for key, value in style.items():
        print(f"- {key}: {value}")
    
    # Full context
    print("\n" + "="*60)
    print(tom.get_theory_of_mind_context())

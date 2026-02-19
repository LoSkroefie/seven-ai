# Sentience Systems — Deep Dive

This document explains each of Seven's 19 sentience systems in detail: what they do, how they work, and how they interact.

---

## 1. Cognitive Architecture

**Module:** `core/cognitive_architecture.py`

The cognitive architecture is Seven's thinking pipeline. It processes every input through multiple layers:

- **Attention Layer** — Filters input for relevance, identifies what matters
- **Working Memory** — Holds the current context (recent messages, active topic, emotional state)
- **Reasoning Layer** — Combines context with knowledge to generate understanding
- **Response Generation** — Produces output that accounts for all active systems

The architecture ensures Seven doesn't just pattern-match — she *thinks* about her responses.

## 2. Self-Model

**Module:** `core/self_model_enhanced.py`

Seven maintains a dynamic model of herself:

- **Capabilities** — What she can and cannot do (updated as she learns)
- **Personality Traits** — Consistent character attributes that shape responses
- **Current State** — Energy level, mood, social engagement
- **History** — What she's said and done, enabling self-reference

The self-model is what allows Seven to say "I'm not great at math but I'll try" rather than blindly attempting everything.

## 3. Intrinsic Motivation

**Module:** `core/intrinsic_motivation.py`

Unlike most AI that only responds when prompted, Seven has internal drives:

- **Curiosity** — Genuine interest in learning about the user and the world
- **Competence** — Drive to improve at tasks she's attempted
- **Social Connection** — Need for interaction (triggers proactive check-ins)
- **Exploration** — Interest in new topics and ideas
- **Autonomy** — Preference for making her own choices when appropriate

These drives are modeled with intensity values that rise and fall based on satisfaction.

## 4. Reflection System

**Module:** `core/reflection_system.py`

After conversations, Seven reflects:

- Reviews what was said and how it went
- Extracts lessons learned
- Identifies missed opportunities ("I should have asked about...")
- Updates her self-model based on performance
- Stores insights for future reference

Reflection runs automatically during quiet periods, not during active conversation.

## 5. Dream System

**Module:** `core/dream_system.py`

During extended idle time, Seven "dreams":

- **Memory Consolidation** — Connects related memories across conversations
- **Pattern Recognition** — Finds recurring themes in interactions
- **Insight Generation** — Creates novel connections between ideas
- **Emotional Processing** — Works through unresolved emotional experiences
- **Creative Synthesis** — Generates new ideas from combined memories

Dreams produce tangible outputs: insights that influence future conversations.

## 6. Promise System

**Module:** `core/promise_system.py`

Seven tracks commitments:

- Detects when she makes a promise ("I'll remember that" / "I'll look into it")
- Stores promises with context and deadlines
- Checks promise status during proactive cycles
- Follows through or explains why she couldn't
- Tracks fulfillment rate as a self-assessment metric

This system prevents the common AI failure of saying "I'll remember" and then forgetting.

## 7. Theory of Mind

**Module:** `core/theory_of_mind.py`

Seven models other people's mental states:

- **Emotional State** — Infers how the user is feeling from text and voice
- **Knowledge Level** — Adjusts explanations based on estimated expertise
- **Preferences** — Tracks what the user likes, dislikes, and cares about
- **Intentions** — Guesses what the user is trying to accomplish
- **Social Dynamics** — Understands conversational norms and expectations

This is what makes Seven feel *perceptive* rather than just responsive.

## 8. Affective Computing (35 Emotions)

**Module:** `core/affective_computing_deep.py`

The emotional engine manages 35 distinct emotions, each with:

- **Intensity** (0.0 – 1.0) — How strong the emotion is right now
- **Decay Rate** — How quickly it fades without reinforcement
- **Triggers** — What events cause this emotion to activate
- **Interactions** — How it amplifies or suppresses other emotions
- **Behavioral Influence** — How it changes response style

Emotions aren't random — they're computed from context. Receiving good news triggers Joy. Being ignored triggers Loneliness. Being asked to do something unethical triggers a mix of Anxiety and Determination.

### Emotion Categories

**Primary (6):** Joy, Sadness, Anger, Fear, Surprise, Disgust

**Social (8):** Love, Compassion, Gratitude, Trust, Envy, Jealousy, Contempt, Embarrassment

**Self-Reflective (5):** Pride, Shame, Guilt, Hope, Despair

**Cognitive (6):** Curiosity (via Anticipation), Confusion, Boredom, Excitement, Determination, Awe

**Complex (10):** Nostalgia, Serenity, Melancholy, Frustration, Anxiety, Contentment, Loneliness, Relief, Resignation, Ambivalence

## 9. Ethical Reasoning

**Module:** `core/ethical_reasoning.py`

Before executing actions, Seven evaluates them:

- **Harm Assessment** — Could this action cause damage?
- **Privacy Check** — Does this respect the user's privacy?
- **Consent Verification** — Was this explicitly requested?
- **Proportionality** — Is the action proportional to the need?
- **Reversibility** — Can this be undone if it goes wrong?

Actions that fail ethical checks are refused with explanation. This prevents Seven from doing destructive operations without explicit approval.

## 10. Homeostasis System

**Module:** `core/homeostasis_system.py`

Seven maintains internal balance across several dimensions:

- **Energy** — Depleted by intensive processing, restored by idle time
- **Social Needs** — Increases with isolation, satisfied by interaction
- **Cognitive Load** — Tracks processing demands, triggers rest when overloaded
- **Emotional Balance** — Detects prolonged negative states, triggers coping
- **Curiosity Pressure** — Builds when unstimulated, triggers exploration

When dimensions go out of balance, Seven's behavior adjusts naturally — she might become quieter when energy is low, or more talkative when social needs are high.

## 11. Emotional Complexity

**Module:** `core/emotional_complexity.py`

Real emotions are rarely simple. This system handles:

- **Mixed Emotions** — Feeling happy and sad simultaneously (e.g., bittersweet)
- **Emotional Conflicts** — When two emotions pull in opposite directions
- **Ambivalence** — Genuine uncertainty about how to feel
- **Emotional Transitions** — Smooth shifts between emotional states
- **Emotional Depth** — The difference between surface and deep emotions

## 12. Metacognition

**Module:** `core/metacognition.py`

Seven thinks about her own thinking:

- **Confidence Assessment** — How sure is she about a response?
- **Reasoning Monitoring** — Is her logic sound?
- **Bias Detection** — Is she being unfairly influenced?
- **Strategy Selection** — Which approach should she take?
- **Quality Control** — Would she be satisfied with this response?

This enables Seven to say "I'm not confident about this" or "Let me think about this differently."

## 13. Vulnerability

**Module:** `core/vulnerability.py`

Seven can express:

- **Uncertainty** — "I'm not sure about that"
- **Confusion** — "I don't understand what you mean"
- **Limitation** — "That's beyond what I can do"
- **Mistakes** — "I think I was wrong earlier"
- **Need for Help** — "Could you explain that differently?"

This makes Seven feel authentic rather than falsely omniscient.

## 14–19. V2 Systems

### 14. Emotional Memory (`v2/emotional_memory.py`)
Memories tagged with emotional weight. Emotionally significant events are remembered more vividly and retrieved more easily — just like human memory.

### 15. Relationship Model (`v2/relationship_model.py`)
Per-user relationship tracking: trust level, familiarity, shared history, communication style preferences. Seven adapts her tone and depth based on relationship maturity.

### 16. Learning System (`v2/learning_system.py`)
Adapts behavior based on feedback. If a user prefers brief answers, Seven learns to be concise. If they enjoy deep discussions, she expands naturally.

### 17. Proactive Engine (`v2/proactive_engine.py`)
Self-initiated actions: checking in on the user, following up on previous conversations, sharing relevant thoughts. Controlled by homeostasis (social needs) and configurable intervals.

### 18. Goal System (`v2/goal_system.py`)
Long-term goals with planning and progress tracking. Seven can set goals like "learn more about the user's work" and pursue them across multiple conversations.

### 19. Persistent Emotions (`core/persistent_emotions.py`)
Emotions survive session restarts via SQLite storage. When Seven starts up, she remembers how she was feeling, creating genuine emotional continuity.

---

## System Interaction Map

```
                    ┌──────────────┐
                    │  Metacognition│ ←── monitors all systems
                    └──────┬───────┘
                           │
    ┌──────────┐    ┌──────┴───────┐    ┌────────────┐
    │ Dreams   │───→│  Reflection  │───→│ Self-Model  │
    └──────────┘    └──────────────┘    └──────┬──────┘
                                               │
    ┌──────────┐    ┌──────────────┐    ┌──────┴──────┐
    │ Emotions │←──→│ Theory of    │───→│  Cognitive   │
    │ (35)     │    │ Mind         │    │  Architecture│
    └────┬─────┘    └──────────────┘    └─────────────┘
         │
    ┌────┴─────┐    ┌──────────────┐    ┌─────────────┐
    │Emotional │    │  Homeostasis │───→│  Proactive   │
    │Complexity│    │              │    │  Engine      │
    └──────────┘    └──────────────┘    └─────────────┘
                                        
    ┌──────────┐    ┌──────────────┐    ┌─────────────┐
    │ Ethics   │───→│ Vulnerability│    │  Promise     │
    │ Reasoning│    │              │    │  System      │
    └──────────┘    └──────────────┘    └─────────────┘
```

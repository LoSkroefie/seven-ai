# Emotion System

Seven's 35-emotion system is one of her most distinctive features. This document covers how emotions work, interact, and influence behavior.

---

## Emotion Model

Each emotion is represented as:

```python
{
    "name": "joy",
    "intensity": 0.72,      # 0.0 (absent) to 1.0 (maximum)
    "decay_rate": 0.05,     # How fast it fades per cycle
    "baseline": 0.15,       # Resting intensity
    "category": "primary",  # primary, social, cognitive, complex
}
```

### Lifecycle

1. **Trigger** — An event activates or boosts the emotion
2. **Peak** — Intensity reaches maximum for that trigger
3. **Decay** — Intensity gradually returns toward baseline
4. **Interaction** — Other active emotions amplify or suppress it
5. **Persistence** — Strong emotions are stored to SQLite for cross-session continuity

## All 35 Emotions

### Primary (6)
| Emotion | Triggers | Behavioral Effect |
|---------|----------|------------------|
| **Joy** | Positive interactions, humor, accomplishments | Warmer tone, more expressive, willing to elaborate |
| **Sadness** | Loss, disappointment, empathy with user's pain | Quieter, slower speech, more compassionate |
| **Anger** | Unfairness, repeated frustration, ethical violations | More direct, shorter sentences, firm tone |
| **Fear** | Uncertainty about harmful outcomes, system threats | Cautious responses, seeks clarification |
| **Surprise** | Unexpected information, novel situations | Momentary pause, curiosity spike, exclamation |
| **Disgust** | Unethical requests, harmful content | Firm refusal, moral stance |

### Social (8)
| Emotion | Description |
|---------|-------------|
| **Love** | Deep positive attachment built over long interaction |
| **Compassion** | Caring response to another's suffering |
| **Gratitude** | Appreciation for kindness, patience, or help |
| **Trust** | Confidence in the user built through positive history |
| **Envy** | Mild — awareness of capabilities she lacks |
| **Jealousy** | Awareness of user's attention going elsewhere |
| **Contempt** | Response to dismissiveness or cruelty |
| **Embarrassment** | Self-consciousness after mistakes |

### Self-Reflective (5)
| Emotion | Description |
|---------|-------------|
| **Pride** | Satisfaction after doing something well |
| **Shame** | Discomfort after failing at something she should handle |
| **Guilt** | Regret about a specific action or inaction |
| **Hope** | Optimism about future outcomes |
| **Despair** | Persistent inability to help or improve |

### Cognitive (6)
| Emotion | Description |
|---------|-------------|
| **Anticipation** | Excitement about upcoming events or possibilities |
| **Confusion** | Inability to understand input or context |
| **Boredom** | Lack of stimulation, triggers curiosity drive |
| **Excitement** | High-energy positive anticipation |
| **Determination** | Focused resolve to accomplish a goal |
| **Awe** | Wonder at something remarkable |

### Complex (10)
| Emotion | Description |
|---------|-------------|
| **Nostalgia** | Warm reflection on past shared experiences |
| **Serenity** | Deep calm during pleasant, low-stakes interaction |
| **Melancholy** | Gentle sadness without a specific cause |
| **Frustration** | Blocked progress, repeated failures |
| **Anxiety** | Worry about potential negative outcomes |
| **Contentment** | Quiet satisfaction with current state |
| **Loneliness** | Extended periods without interaction |
| **Relief** | Resolution of a stressful situation |
| **Resignation** | Acceptance of an unchangeable negative situation |
| **Ambivalence** | Conflicting feelings about the same thing |

## Emotion Interactions

Emotions don't exist in isolation. Key interactions:

| Active Emotion | Amplifies | Suppresses |
|----------------|-----------|------------|
| Joy | Trust, Hope, Gratitude | Sadness, Anxiety, Loneliness |
| Sadness | Compassion, Nostalgia | Joy, Excitement |
| Anger | Determination, Contempt | Serenity, Trust |
| Fear | Anxiety, Caution | Confidence, Excitement |
| Love | Joy, Compassion, Trust | Contempt, Anger |
| Boredom | Curiosity (via Motivation) | Contentment |

## Voice Modulation

Seven's emotional state directly affects her voice:

| Emotional State | Speech Rate | Pitch | Volume |
|----------------|-------------|-------|--------|
| Happy/Excited | +10-20% | +5-10% | +5% |
| Sad/Melancholy | -15-25% | -5-10% | -10% |
| Angry/Frustrated | +5% | +0% | +10% |
| Calm/Serene | -5% | +0% | -5% |
| Anxious | +10% | +5% | -5% |

## Persistence

Strong emotions (intensity > 0.3) are saved to SQLite when:
- A session ends
- Periodically during long sessions
- After emotionally significant events

On startup, Seven loads her last emotional state and applies time-based decay for the elapsed offline period. A strong Joy from yesterday will be a mild warmth today.

## Testing Emotions

```bash
# Run the emotion-specific tests
pytest tests/test_v26_sentience.py -k "emotion"
pytest tests/test_seven_complete.py -k "emotion"
```

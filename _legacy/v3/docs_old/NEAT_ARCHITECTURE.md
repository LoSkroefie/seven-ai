# Seven AI — NEAT Neuroevolution Architecture

**Module**: `evolution/neat_evolver.py`  
**Config**: `evolution/neat_config.txt`  
**Dependency**: `neat-python` (optional — gracefully disabled if not installed)

---

## What Is This?

Seven doesn't just run fixed algorithms — she **evolves** them. Using [NEAT](https://en.wikipedia.org/wiki/Neuroevolution_of_augmenting_topologies) (NeuroEvolution of Augmenting Topologies), Seven evolves small neural networks that control behavioral parameters in real-time.

These are not the LLM. These are tiny evolved networks (5 inputs → 3 outputs) that tune Seven's personality, emotion blending, goal priorities, and proactive behavior. They run during dream/idle cycles with minimal CPU impact.

---

## The Four Evolution Domains

Each domain has its own NEAT population that evolves independently:

### 1. Emotion Blending (`emotion_blend`)

**Purpose**: When multiple emotions fire simultaneously (e.g., JOY + CURIOSITY + mild FEAR), how should they blend?

```
Inputs (5):              Outputs (3):
├── joy_intensity        ├── blend_weight_primary
├── sadness_intensity    ├── blend_weight_secondary
├── anger_intensity      └── mood_drift_rate
├── surprise_intensity
└── baseline_mood
```

**Fitness criteria**:
- Smooth blending (no wild swings) — 60%
- Proper normalization (weights sum to ~1.0) — 40%
- Combined with real emotion stability metrics and user sentiment

### 2. Goal Priority (`goal_priority`)

**Purpose**: Which autonomous goals should Seven pursue first?

```
Inputs (5):              Outputs (3):
├── importance           ├── priority_score
├── progress             ├── urgency_modifier
├── deadline_pressure    └── effort_estimate
├── user_relevance
└── novelty
```

**Fitness criteria**:
- High importance + low progress → high priority
- Combined with actual goal completion rate from Seven's goal system

### 3. Proactive Action Selection (`proactive_action`)

**Purpose**: When should Seven reach out, and when should she stay quiet?

```
Inputs (5):              Outputs (3):
├── user_presence        ├── speak_probability
├── boredom_level        ├── action_type_weight
├── time_since_last      └── intensity
├── relationship_depth
└── energy_level
```

**Fitness criteria**:
- Proactive when user is away (reward initiative)
- Restrained when user is active (don't interrupt)
- Combined with user sentiment and novelty metrics

### 4. Personality Drift (`personality_drift`)

**Purpose**: How should Seven's personality traits gradually shift over time?

```
Inputs (5):              Outputs (5):
├── warmth               ├── warmth_adjusted
├── assertiveness        ├── assertiveness_adjusted
├── curiosity            ├── curiosity_adjusted
├── formality            ├── formality_adjusted
└── humor                └── humor_adjusted
```

**Fitness criteria**:
- Small adjustments (drift, not revolution): sweet spot is 0.02–0.15 delta
- Too conservative (< 0.02): personality feels static
- Too radical (> 0.15): personality feels unstable
- Combined with overall interaction metrics

---

## How It Works

### Architecture

```
┌────────────────────────────────────────┐
│           NEATEvolver                   │
│                                        │
│  ┌──────────┐  ┌──────────┐           │
│  │Population │  │Population │  ...×4   │
│  │emotion    │  │goal      │           │
│  │blend      │  │priority  │           │
│  └─────┬─────┘  └─────┬─────┘          │
│        │              │                │
│        ▼              ▼                │
│  ┌──────────┐  ┌──────────┐           │
│  │  Fitness  │  │  Fitness  │          │
│  │  Eval     │  │  Eval     │          │
│  │(real bot  │  │(real bot  │          │
│  │ metrics)  │  │ metrics)  │          │
│  └─────┬─────┘  └─────┬─────┘          │
│        │              │                │
│        ▼              ▼                │
│  ┌──────────┐  ┌──────────┐           │
│  │  Best     │  │  Best     │          │
│  │  Network  │  │  Network  │          │
│  │  (deploy) │  │  (deploy) │          │
│  └──────────┘  └──────────┘           │
│                                        │
│  Persistence: pickle + JSON history    │
│  Checkpoints: auto every 5 generations │
└────────────────────────────────────────┘
```

### Lifecycle

1. **Initialization**: Load config from `neat_config.txt`, restore checkpoints if available
2. **Trigger**: Runs during dream cycles or idle periods (via `seven_scheduler.py`)
3. **Evaluation**: Each genome is tested against real bot metrics (emotion stability, goal completion, user sentiment, novelty)
4. **Selection**: NEAT's speciation preserves diversity; elitism keeps top 2 per species
5. **Deployment**: Best network per domain is immediately available via `evolver.activate(domain, inputs)`
6. **Persistence**: Best genomes saved as pickle, history as JSON, populations checkpointed

### When Does Evolution Run?

- **Dream cycles**: `run_all_domains(generations=5)` during Seven's sleep mode
- **Scheduled**: Via APScheduler during low-activity periods
- **Manual**: Via API endpoint or direct call
- **Never blocks**: Thread-locked, only one evolution runs at a time

---

## NEAT Configuration

From `evolution/neat_config.txt`:

| Parameter | Value | Why |
|-----------|-------|-----|
| `pop_size` | 30 | Small population = fast generations |
| `num_inputs` | 5 | Minimal input vector per domain |
| `num_outputs` | 3 | Minimal output (blend weights, scores) |
| `num_hidden` | 0 | Start with no hidden nodes (NEAT adds them) |
| `initial_connection` | `full_direct` | Every input connects to every output |
| `activation_options` | sigmoid, tanh, relu | Network can evolve different activations |
| `conn_add_prob` | 0.3 | 30% chance of adding a connection per generation |
| `node_add_prob` | 0.15 | 15% chance of adding a hidden node |
| `max_stagnation` | 15 | Species dies after 15 generations without improvement |
| `compatibility_threshold` | 3.0 | How different genomes must be to form new species |
| `fitness_threshold` | 0.95 | Stop if fitness reaches 95% |
| `no_fitness_termination` | True | Actually never stop (continuous improvement) |

---

## Fitness Metrics (Real Data)

The `FitnessMetrics` class collects real data from Seven's running systems:

| Metric | Weight | Source | Measures |
|--------|--------|--------|----------|
| `emotion_stability` | 25% | AffectiveSystem history | Low variance in recent emotion intensities |
| `goal_completion_rate` | 30% | IntrinsicMotivation goals | Goals completed / goals attempted |
| `user_sentiment` | 30% | AffectiveSystem history | Ratio of positive emotions in recent interactions |
| `novelty_bonus` | 15% | AffectiveSystem history | Unique emotions experienced (diversity reward) |

When no bot is connected (testing), synthetic random metrics are used.

---

## File Structure

```
evolution/
├── neat_evolver.py           # Core evolution engine (538 lines)
├── neat_config.txt           # NEAT hyperparameters
├── checkpoints/              # Population snapshots (auto-generated)
│   ├── emotion_blend_checkpoint
│   ├── goal_priority_gen_5
│   └── ...
├── genomes/                  # Best genome per domain (pickle)
│   ├── best_emotion_blend.pkl
│   ├── best_goal_priority.pkl
│   └── ...
└── evolution_history.json    # Log of all evolution runs
```

---

## API

```python
from evolution.neat_evolver import NEATEvolver, EvolutionDomain

evolver = NEATEvolver(config_path="evolution/neat_config.txt", bot=bot)

# Run evolution for one domain
result = evolver.run_evolution(EvolutionDomain.EMOTION_BLEND, generations=10)
# result = {'domain': 'emotion_blend', 'best_fitness': 0.7823, 'genome_size': 18, ...}

# Run all domains (dream cycle)
results = evolver.run_all_domains(generations=5)

# Use evolved network
outputs = evolver.activate("emotion_blend", [0.8, 0.2, 0.1, 0.5, 0.3])
# outputs = [0.612, 0.234, 0.154]  # blend weights

# Check status
status = evolver.get_status()
```

---

## Why NEAT?

| Alternative | Why Not |
|-------------|---------|
| Fixed weights | No adaptation — same behavior forever |
| Random search | No accumulation — doesn't build on success |
| Gradient descent | Requires differentiable fitness (ours isn't) |
| Genetic algorithms (fixed topology) | Can't discover new network structures |
| **NEAT** | ✅ Evolves both weights AND topology, speciation preserves diversity, minimal complexity grows organically |

NEAT starts with the simplest possible network (direct input→output) and only adds complexity when it helps fitness. This means Seven's behavioral networks stay as simple as they need to be.

---

## Limitations & Honesty

- Evolution runs are **simulated fitness**, not true online learning from user interaction in real-time
- With `pop_size=30` and 5-generation runs, this is a **lightweight demonstration** of neuroevolution, not industrial-scale optimization
- Fitness functions use **proxy metrics** — emotion stability is measurable, but "is this the right personality drift" is subjective
- The evolved networks are **small** (typically 5-20 connections) — they tune parameters, they don't replace the LLM

This is a real implementation of neuroevolution applied to AI personality simulation — but it's honest about its scope.

---

*This document addresses the NEAT documentation gap identified in the improvement roadmap (item 7.5).*

"""
NEAT Neuroevolution — Seven's Self-Evolution Engine

Uses NEAT (NeuroEvolution of Augmenting Topologies) to evolve small
neural networks that control Seven's behavior parameters:

1. Emotion Blending — evolved weights for combining concurrent emotions
2. Goal Priority — evolved scoring for which goals to pursue first
3. Proactive Action Selection — evolved probabilities for autonomous actions
4. Personality Drift — evolved adjustments to personality traits

This is what makes Seven genuinely alive: she doesn't just run fixed
algorithms — she evolves them. Every generation, the fittest behavioral
networks survive and reproduce, creating emergent adaptation.

Runs in background during low-activity / dream periods.
Small nets, infrequent runs — minimal CPU impact.
"""

import os
import json
import time
import pickle
import logging
import math
import random
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Tuple
from datetime import datetime

logger = logging.getLogger("NEATEvolver")

try:
    import neat
    NEAT_AVAILABLE = True
except ImportError:
    NEAT_AVAILABLE = False
    logger.warning("neat-python not installed — evolution disabled. pip install neat-python")


class EvolutionDomain:
    """Defines what a NEAT population is evolving"""
    EMOTION_BLEND = "emotion_blend"
    GOAL_PRIORITY = "goal_priority"
    PROACTIVE_ACTION = "proactive_action"
    PERSONALITY_DRIFT = "personality_drift"


class FitnessMetrics:
    """Collected metrics used to compute genome fitness"""

    def __init__(self):
        self.emotion_stability = 0.0      # Low wild swings = good
        self.goal_completion_rate = 0.0    # Goals completed / goals attempted
        self.user_sentiment = 0.0         # Proxy for "user happiness"
        self.novelty_bonus = 0.0          # Emergent/unexpected behavior reward
        self.interaction_count = 0        # How many interactions since last eval
        self.uptime_hours = 0.0           # How long Seven has been running

    def total(self) -> float:
        """Weighted fitness score"""
        return (
            self.emotion_stability * 0.25 +
            self.goal_completion_rate * 0.30 +
            self.user_sentiment * 0.30 +
            self.novelty_bonus * 0.15
        )

    def to_dict(self) -> Dict:
        return {
            'emotion_stability': round(self.emotion_stability, 4),
            'goal_completion_rate': round(self.goal_completion_rate, 4),
            'user_sentiment': round(self.user_sentiment, 4),
            'novelty_bonus': round(self.novelty_bonus, 4),
            'total': round(self.total(), 4),
            'interaction_count': self.interaction_count,
            'uptime_hours': round(self.uptime_hours, 2)
        }


class NEATEvolver:
    """
    Core NEAT evolution engine for Seven.

    Manages populations, checkpointing, fitness evaluation, and
    deployment of evolved neural networks into Seven's systems.

    Usage:
        evolver = NEATEvolver(config_path, bot=bot)
        evolver.run_evolution(domain='emotion_blend', generations=10)
        net = evolver.get_best_network('emotion_blend')
        output = net.activate(input_vector)
    """

    def __init__(self, config_path: str, data_dir: str = None, bot=None):
        self.available = NEAT_AVAILABLE
        self.bot = bot
        self.config_path = config_path
        self._lock = threading.Lock()

        # Directories
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path.home() / ".chatbot" / "evolution"
        self.checkpoint_dir = self.data_dir / "checkpoints"
        self.genome_dir = self.data_dir / "genomes"
        self.history_file = self.data_dir / "evolution_history.json"

        for d in [self.data_dir, self.checkpoint_dir, self.genome_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # State
        self.populations: Dict[str, Any] = {}
        self.best_genomes: Dict[str, Any] = {}
        self.best_networks: Dict[str, Any] = {}
        self.generation_count: Dict[str, int] = {}
        self.evolution_history: List[Dict] = []
        self.is_evolving = False
        self.last_evolution: Optional[datetime] = None

        # Load persisted best genomes
        self._load_best_genomes()

        # Load NEAT config
        self.neat_config = None
        if self.available:
            try:
                self.neat_config = neat.Config(
                    neat.DefaultGenome,
                    neat.DefaultReproduction,
                    neat.DefaultSpeciesSet,
                    neat.DefaultStagnation,
                    config_path
                )
                logger.info(f"[NEAT] Config loaded from {config_path}")
            except Exception as e:
                logger.error(f"[NEAT] Config load failed: {e}")
                self.available = False

        if self.available:
            logger.info("[NEAT] Evolver initialized — self-evolution ready")
        else:
            logger.warning("[NEAT] Evolver disabled (neat-python not available)")

    # ============ Population Management ============

    def _get_or_create_population(self, domain: str):
        """Get existing population or create new one for a domain"""
        if domain in self.populations:
            return self.populations[domain]

        checkpoint_file = self.checkpoint_dir / f"{domain}_checkpoint"

        if checkpoint_file.exists():
            try:
                pop = neat.Checkpointer.restore_checkpoint(str(checkpoint_file))
                logger.info(f"[NEAT] Restored {domain} population from checkpoint")
                self.populations[domain] = pop
                return pop
            except Exception as e:
                logger.warning(f"[NEAT] Checkpoint restore failed for {domain}: {e}")

        # Create fresh population
        pop = neat.Population(self.neat_config)
        pop.add_reporter(neat.StdOutReporter(False))
        pop.add_reporter(neat.StatisticsReporter())
        pop.add_reporter(neat.Checkpointer(
            generation_interval=5,
            filename_prefix=str(self.checkpoint_dir / f"{domain}_gen_")
        ))
        self.populations[domain] = pop
        self.generation_count[domain] = 0
        logger.info(f"[NEAT] Created fresh population for {domain}")
        return pop

    # ============ Fitness Functions ============

    def _collect_metrics(self) -> FitnessMetrics:
        """Collect real metrics from Seven's systems for fitness evaluation"""
        metrics = FitnessMetrics()

        if not self.bot:
            # Synthetic metrics for testing without bot
            metrics.emotion_stability = random.uniform(0.3, 0.9)
            metrics.goal_completion_rate = random.uniform(0.1, 0.8)
            metrics.user_sentiment = random.uniform(0.4, 0.9)
            metrics.novelty_bonus = random.uniform(0.0, 0.3)
            return metrics

        try:
            # Emotion stability: measure variance in recent emotion intensities
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                affective = getattr(self.bot.phase5, 'affective', None)
                if affective and hasattr(affective, 'emotion_history'):
                    recent = affective.emotion_history[-50:]
                    if len(recent) >= 2:
                        intensities = [e.intensity for e in recent]
                        mean_i = sum(intensities) / len(intensities)
                        variance = sum((x - mean_i) ** 2 for x in intensities) / len(intensities)
                        # Low variance = high stability (inverted)
                        metrics.emotion_stability = max(0, 1.0 - math.sqrt(variance) * 2)
                    else:
                        metrics.emotion_stability = 0.5

            # Goal completion rate
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                motivation = getattr(self.bot.phase5, 'motivation', None)
                if motivation:
                    goals = getattr(motivation, 'goals', [])
                    if goals:
                        completed = sum(1 for g in goals if getattr(g, 'progress', 0) >= 100)
                        metrics.goal_completion_rate = completed / len(goals) if goals else 0

            # User sentiment proxy: ratio of positive emotions triggered by user interactions
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                affective = getattr(self.bot.phase5, 'affective', None)
                if affective and hasattr(affective, 'emotion_history'):
                    recent = affective.emotion_history[-30:]
                    positive = {'joy', 'excitement', 'satisfaction', 'gratitude',
                                'pride', 'contentment', 'affection', 'inspiration',
                                'hope', 'enthusiasm', 'confidence', 'peaceful'}
                    if recent:
                        pos_count = sum(1 for e in recent
                                        if getattr(e.emotion, 'value', '') in positive)
                        metrics.user_sentiment = pos_count / len(recent)

            # Novelty bonus: unique emotions experienced recently
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                affective = getattr(self.bot.phase5, 'affective', None)
                if affective and hasattr(affective, 'emotion_history'):
                    recent = affective.emotion_history[-50:]
                    unique = set(getattr(e.emotion, 'value', '') for e in recent)
                    metrics.novelty_bonus = min(1.0, len(unique) / 15)

            # Interaction count
            metrics.interaction_count = getattr(self.bot, 'message_count', 0)

            # Uptime
            start = getattr(self.bot, 'start_time', None)
            if start:
                metrics.uptime_hours = (datetime.now() - start).total_seconds() / 3600

        except Exception as e:
            logger.error(f"[NEAT] Metrics collection error: {e}")

        return metrics

    def _make_fitness_function(self, domain: str) -> Callable:
        """Create a fitness evaluation function for a given domain"""
        metrics = self._collect_metrics()

        def eval_genomes(genomes, config):
            for genome_id, genome in genomes:
                net = neat.nn.FeedForwardNetwork.create(genome, config)

                if domain == EvolutionDomain.EMOTION_BLEND:
                    genome.fitness = self._fitness_emotion_blend(net, metrics)
                elif domain == EvolutionDomain.GOAL_PRIORITY:
                    genome.fitness = self._fitness_goal_priority(net, metrics)
                elif domain == EvolutionDomain.PROACTIVE_ACTION:
                    genome.fitness = self._fitness_proactive(net, metrics)
                elif domain == EvolutionDomain.PERSONALITY_DRIFT:
                    genome.fitness = self._fitness_personality(net, metrics)
                else:
                    genome.fitness = metrics.total()

        return eval_genomes

    def _fitness_emotion_blend(self, net, metrics: FitnessMetrics) -> float:
        """Fitness for emotion blending network"""
        # Test: given two emotion intensities, produce a blend weight
        # Good blend: doesn't create wild swings, maintains stability
        test_inputs = [
            [0.8, 0.2, 0.1, 0.5, 0.3],  # joy dominant
            [0.1, 0.7, 0.3, 0.2, 0.6],  # sadness dominant
            [0.5, 0.5, 0.5, 0.5, 0.5],  # balanced
            [0.9, 0.1, 0.9, 0.1, 0.5],  # volatile
        ]
        score = 0.0
        for inputs in test_inputs:
            outputs = net.activate(inputs)
            # Reward smooth outputs (not all 0 or all 1)
            output_variance = sum((o - 0.5) ** 2 for o in outputs) / len(outputs)
            smoothness = 1.0 - min(1.0, output_variance * 4)
            # Reward outputs that sum close to 1 (proper probability distribution)
            total = sum(max(0, o) for o in outputs)
            normalization = 1.0 - min(1.0, abs(total - 1.0))
            score += (smoothness * 0.6 + normalization * 0.4)

        score /= len(test_inputs)
        # Combine with real metrics
        return score * 0.5 + metrics.emotion_stability * 0.3 + metrics.user_sentiment * 0.2

    def _fitness_goal_priority(self, net, metrics: FitnessMetrics) -> float:
        """Fitness for goal priority scoring network"""
        # Test: given goal features, produce priority score
        test_goals = [
            [0.9, 0.1, 0.8, 0.2, 0.5],  # high importance, low progress
            [0.3, 0.9, 0.2, 0.8, 0.5],  # low importance, high progress
            [0.7, 0.5, 0.6, 0.4, 0.7],  # medium everything
        ]
        score = 0.0
        for inputs in test_goals:
            outputs = net.activate(inputs)
            priority = outputs[0] if outputs else 0
            # High importance + low progress should get high priority
            expected = inputs[0] * (1 - inputs[1])
            score += 1.0 - min(1.0, abs(priority - expected))

        score /= len(test_goals)
        return score * 0.5 + metrics.goal_completion_rate * 0.5

    def _fitness_proactive(self, net, metrics: FitnessMetrics) -> float:
        """Fitness for proactive action selection"""
        test_contexts = [
            [0.8, 0.2, 0.1, 0.5, 0.3],  # user active, low boredom
            [0.1, 0.8, 0.7, 0.2, 0.9],  # user away, high boredom
            [0.5, 0.5, 0.5, 0.5, 0.5],  # neutral
        ]
        score = 0.0
        for inputs in test_contexts:
            outputs = net.activate(inputs)
            # When user is away (inputs[0] low), should be more proactive
            proactivity = sum(max(0, o) for o in outputs) / max(1, len(outputs))
            user_presence = inputs[0]
            if user_presence < 0.3:
                score += proactivity  # Reward proactivity when user away
            else:
                score += 1.0 - proactivity  # Reward restraint when user active

        score /= len(test_contexts)
        return score * 0.4 + metrics.user_sentiment * 0.3 + metrics.novelty_bonus * 0.3

    def _fitness_personality(self, net, metrics: FitnessMetrics) -> float:
        """Fitness for personality drift adjustments"""
        # Personality should drift slowly, not wildly
        test_traits = [
            [0.7, 0.8, 0.6, 0.5, 0.3],  # current personality vector
        ]
        score = 0.0
        for inputs in test_traits:
            outputs = net.activate(inputs)
            # Reward small adjustments (drift, not revolution)
            deltas = [abs(o - i) for o, i in zip(outputs, inputs)]
            avg_delta = sum(deltas) / len(deltas)
            # Sweet spot: 0.02–0.15 drift per generation
            if 0.02 <= avg_delta <= 0.15:
                score += 1.0
            elif avg_delta < 0.02:
                score += avg_delta / 0.02  # Too conservative
            else:
                score += max(0, 1.0 - (avg_delta - 0.15) * 5)  # Too radical

        return score * 0.4 + metrics.total() * 0.6

    # ============ Evolution Execution ============

    def run_evolution(self, domain: str = EvolutionDomain.EMOTION_BLEND,
                      generations: int = 10) -> Optional[Dict]:
        """
        Run NEAT evolution for a specific domain.

        Args:
            domain: Which behavior to evolve
            generations: Number of generations to run

        Returns:
            Dict with evolution results, or None if unavailable
        """
        if not self.available:
            logger.warning("[NEAT] Evolution unavailable (neat-python not installed)")
            return None

        with self._lock:
            if self.is_evolving:
                logger.warning("[NEAT] Evolution already in progress")
                return None
            self.is_evolving = True

        start = time.time()
        result = None

        try:
            logger.info(f"[NEAT] Starting {domain} evolution for {generations} generations...")

            pop = self._get_or_create_population(domain)
            eval_fn = self._make_fitness_function(domain)

            winner = pop.run(eval_fn, generations)
            elapsed = time.time() - start

            # Store best genome
            self.best_genomes[domain] = winner
            self.best_networks[domain] = neat.nn.FeedForwardNetwork.create(
                winner, self.neat_config
            )
            self.generation_count[domain] = self.generation_count.get(domain, 0) + generations
            self.last_evolution = datetime.now()

            # Save best genome to disk
            genome_file = self.genome_dir / f"best_{domain}.pkl"
            with open(genome_file, 'wb') as f:
                pickle.dump(winner, f)

            # Save checkpoint
            checkpoint_file = self.checkpoint_dir / f"{domain}_checkpoint"
            # neat.Checkpointer handles this via reporter, but we also
            # save the population state explicitly
            try:
                with open(checkpoint_file, 'wb') as f:
                    pickle.dump(pop, f)
            except Exception:
                pass

            result = {
                'domain': domain,
                'generations': generations,
                'total_generations': self.generation_count[domain],
                'best_fitness': round(winner.fitness, 4),
                'genome_size': len(winner.connections),
                'elapsed_seconds': round(elapsed, 2),
                'timestamp': datetime.now().isoformat()
            }

            # Append to history
            self.evolution_history.append(result)
            self._save_history()

            logger.info(
                f"[NEAT] {domain} evolution complete: "
                f"fitness={winner.fitness:.4f}, "
                f"size={len(winner.connections)} connections, "
                f"{elapsed:.1f}s"
            )

        except Exception as e:
            logger.error(f"[NEAT] Evolution error: {e}", exc_info=True)
        finally:
            with self._lock:
                self.is_evolving = False

        return result

    def run_all_domains(self, generations: int = 5) -> List[Dict]:
        """Run evolution across all domains (used during dream cycles)"""
        results = []
        for domain in [
            EvolutionDomain.EMOTION_BLEND,
            EvolutionDomain.GOAL_PRIORITY,
            EvolutionDomain.PROACTIVE_ACTION,
            EvolutionDomain.PERSONALITY_DRIFT,
        ]:
            r = self.run_evolution(domain, generations)
            if r:
                results.append(r)
        return results

    # ============ Network Access ============

    def get_best_network(self, domain: str):
        """Get the best evolved network for a domain (or None)"""
        return self.best_networks.get(domain)

    def activate(self, domain: str, inputs: List[float]) -> Optional[List[float]]:
        """Run inputs through the best evolved network for a domain"""
        net = self.best_networks.get(domain)
        if net is None:
            return None
        try:
            return net.activate(inputs)
        except Exception as e:
            logger.error(f"[NEAT] Activation error ({domain}): {e}")
            return None

    # ============ Persistence ============

    def _load_best_genomes(self):
        """Load persisted best genomes from disk"""
        if not NEAT_AVAILABLE:
            return
        for pkl in self.genome_dir.glob("best_*.pkl"):
            domain = pkl.stem.replace("best_", "")
            try:
                with open(pkl, 'rb') as f:
                    genome = pickle.load(f)
                self.best_genomes[domain] = genome
                # We can't create the network without config, defer to after config load
                logger.info(f"[NEAT] Loaded best genome for {domain}")
            except Exception as e:
                logger.warning(f"[NEAT] Failed to load genome {pkl}: {e}")

    def _rebuild_networks(self):
        """Rebuild neural networks from loaded genomes (call after config is loaded)"""
        if not self.neat_config:
            return
        for domain, genome in self.best_genomes.items():
            try:
                self.best_networks[domain] = neat.nn.FeedForwardNetwork.create(
                    genome, self.neat_config
                )
                logger.info(f"[NEAT] Rebuilt network for {domain}")
            except Exception as e:
                logger.warning(f"[NEAT] Network rebuild failed for {domain}: {e}")

    def _save_history(self):
        """Save evolution history to disk"""
        try:
            # Keep last 100 entries
            history = self.evolution_history[-100:]
            self.history_file.write_text(
                json.dumps(history, indent=2),
                encoding='utf-8'
            )
        except Exception:
            pass

    # ============ Status ============

    def get_status(self) -> Dict:
        """Get evolution system status"""
        return {
            'available': self.available,
            'is_evolving': self.is_evolving,
            'last_evolution': self.last_evolution.isoformat() if self.last_evolution else None,
            'domains': {
                domain: {
                    'best_fitness': round(genome.fitness, 4) if hasattr(genome, 'fitness') and genome.fitness else 0,
                    'connections': len(genome.connections) if hasattr(genome, 'connections') else 0,
                    'generations': self.generation_count.get(domain, 0)
                }
                for domain, genome in self.best_genomes.items()
            },
            'total_evolutions': len(self.evolution_history),
            'recent': self.evolution_history[-3:] if self.evolution_history else []
        }

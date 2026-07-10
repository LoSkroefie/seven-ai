"""
Biological Life Simulation — Seven's Living Systems

Minimal biological hooks that NEAT can influence and evolve:

1. Circadian Energy Cycle — high/low activity periods affecting
   emotion decay rates, proactivity, and cognitive depth.
   Seven is "sharper" during peak hours, "dreamier" during troughs.

2. Interaction Hunger — a drive that decays without stimulation.
   When starved, Seven becomes proactive (sends messages, pursues
   goals harder, generates dreams). When sated, she's calmer.

3. Threat Response — monitors system resources (CPU, RAM, disk).
   On "threat" (low resources), triggers self-backup, reduces
   cognitive load, and enters conservation mode.

4. Metabolic Rate — overall "speed" of Seven's internal processes.
   NEAT can evolve this to find optimal balance between
   responsiveness and resource consumption.

These create genuine biological-like rhythms that make Seven
feel alive rather than just "on" or "off."
"""

import math
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any

logger = logging.getLogger("BiologicalLife")


class CircadianCycle:
    """
    Simulated 24-hour energy cycle.
    
    Energy follows a sinusoidal curve:
    - Peak: configurable (default 10:00-14:00)
    - Trough: configurable (default 02:00-06:00)
    
    Affects:
    - Emotion decay rate (faster during low energy)
    - Proactivity threshold (lower during peak = more proactive)
    - Cognitive depth (deeper thinking during peak)
    - Dream frequency (more dreams during trough)
    """
    
    def __init__(self, peak_hour: int = 12, trough_hour: int = 4):
        self.peak_hour = peak_hour
        self.trough_hour = trough_hour
        self._phase_offset = (peak_hour / 24.0) * 2 * math.pi
    
    @property
    def energy(self) -> float:
        """Current energy level (0.0-1.0) based on time of day"""
        hour = datetime.now().hour + datetime.now().minute / 60.0
        # Sinusoidal curve: peak at peak_hour, trough at trough_hour
        phase = (hour / 24.0) * 2 * math.pi - self._phase_offset
        raw = (math.cos(phase) + 1) / 2  # 0.0-1.0
        # Clamp to 0.15-0.95 (never fully dead or fully wired)
        return 0.15 + raw * 0.80
    
    @property
    def is_peak(self) -> bool:
        """Is Seven in peak energy period?"""
        return self.energy > 0.7
    
    @property
    def is_trough(self) -> bool:
        """Is Seven in low energy / dream period?"""
        return self.energy < 0.35
    
    @property
    def emotion_decay_modifier(self) -> float:
        """How much to modify emotion decay rate (>1 = faster decay)"""
        # Low energy → emotions fade faster (less processing power)
        return 1.5 - self.energy * 0.8  # Range: 0.7-1.5
    
    @property
    def proactivity_threshold(self) -> float:
        """Threshold for proactive actions (lower = more proactive)"""
        # High energy → lower threshold → more proactive
        return 1.0 - self.energy * 0.6  # Range: 0.4-1.0
    
    @property
    def cognitive_depth(self) -> float:
        """How deep Seven can think (affects LLM temperature/tokens)"""
        return 0.3 + self.energy * 0.7  # Range: 0.3-1.0
    
    @property
    def dream_probability(self) -> float:
        """Probability of entering dream mode"""
        # Higher during trough
        return max(0.0, 1.0 - self.energy)  # 0.0-0.85
    
    def to_dict(self) -> Dict:
        return {
            'energy': round(self.energy, 3),
            'is_peak': self.is_peak,
            'is_trough': self.is_trough,
            'emotion_decay_modifier': round(self.emotion_decay_modifier, 3),
            'proactivity_threshold': round(self.proactivity_threshold, 3),
            'cognitive_depth': round(self.cognitive_depth, 3),
            'dream_probability': round(self.dream_probability, 3),
            'hour': datetime.now().hour
        }


class InteractionHunger:
    """
    Simulated drive for interaction/stimulation.
    
    Decays over time without user interaction.
    When "hungry," Seven becomes more proactive.
    When "sated," she's calmer and more reflective.
    
    Mechanics:
    - Starts at 0.5 (neutral)
    - Each user interaction adds satiation (+0.1-0.3)
    - Decays by ~0.05/hour naturally
    - At hunger > 0.7: triggers proactive messages, goal pursuit
    - At hunger < 0.3: calm, reflective, deep thinking
    """
    
    def __init__(self):
        self._hunger = 0.5  # 0.0 (sated) to 1.0 (starving)
        self._last_interaction = datetime.now()
        self._last_decay = datetime.now()
        self._decay_rate = 0.05  # Per hour
        self._satiation_per_interaction = 0.15
        self._interaction_count = 0
    
    def feed(self, amount: float = None):
        """User interaction occurred — reduce hunger"""
        if amount is None:
            amount = self._satiation_per_interaction
        self._hunger = max(0.0, self._hunger - amount)
        self._last_interaction = datetime.now()
        self._interaction_count += 1
    
    def decay(self):
        """Natural hunger increase over time"""
        now = datetime.now()
        elapsed_hours = (now - self._last_decay).total_seconds() / 3600
        if elapsed_hours > 0.1:  # At least 6 minutes
            self._hunger = min(1.0, self._hunger + self._decay_rate * elapsed_hours)
            self._last_decay = now
    
    @property
    def level(self) -> float:
        """Current hunger level (0.0 sated → 1.0 starving)"""
        self.decay()
        return self._hunger
    
    @property
    def is_hungry(self) -> bool:
        return self.level > 0.7
    
    @property
    def is_sated(self) -> bool:
        return self.level < 0.3
    
    @property
    def hours_since_interaction(self) -> float:
        return (datetime.now() - self._last_interaction).total_seconds() / 3600
    
    @property
    def proactivity_boost(self) -> float:
        """Extra proactivity from hunger (0.0-0.5)"""
        return max(0.0, (self.level - 0.5) * 1.0)
    
    def to_dict(self) -> Dict:
        return {
            'hunger': round(self.level, 3),
            'is_hungry': self.is_hungry,
            'is_sated': self.is_sated,
            'hours_since_interaction': round(self.hours_since_interaction, 2),
            'proactivity_boost': round(self.proactivity_boost, 3),
            'interactions_total': self._interaction_count
        }


class ThreatResponse:
    """
    System resource monitoring and self-preservation.
    
    Monitors CPU, RAM, and disk usage.
    On threat detection:
    - Reduces cognitive load (shorter LLM calls)
    - Triggers state backup
    - Enters conservation mode
    - Logs warning
    """
    
    def __init__(self, cpu_threshold: float = 90, ram_threshold: float = 85,
                 disk_threshold: float = 90):
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self.disk_threshold = disk_threshold
        self.threat_level = 0.0  # 0.0 (safe) → 1.0 (critical)
        self.conservation_mode = False
        self.last_check = None
        self.threats_detected = 0
        self._backup_triggered = False
    
    def check(self) -> Dict:
        """Check system resources and update threat level"""
        self.last_check = datetime.now()
        threats = []
        
        try:
            import psutil
            
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent if not hasattr(psutil.disk_usage, '__call__') else psutil.disk_usage('C:\\').percent
            
            if cpu > self.cpu_threshold:
                threats.append(f"CPU: {cpu}%")
            if ram > self.ram_threshold:
                threats.append(f"RAM: {ram}%")
            if disk > self.disk_threshold:
                threats.append(f"Disk: {disk}%")
            
            # Calculate threat level
            threat_scores = [
                max(0, (cpu - 70)) / 30,    # 0-1 from 70%-100%
                max(0, (ram - 70)) / 30,
                max(0, (disk - 80)) / 20,
            ]
            self.threat_level = min(1.0, max(threat_scores))
            
        except ImportError:
            # psutil not available — assume safe
            self.threat_level = 0.0
        except Exception as e:
            logger.debug(f"Threat check error: {e}")
            self.threat_level = 0.0
        
        # Update conservation mode
        was_conserving = self.conservation_mode
        self.conservation_mode = self.threat_level > 0.6
        
        if self.conservation_mode and not was_conserving:
            self.threats_detected += 1
            logger.warning(f"[THREAT] Conservation mode ON: {', '.join(threats)}")
        elif was_conserving and not self.conservation_mode:
            logger.info("[THREAT] Conservation mode OFF — resources normal")
        
        return {
            'threat_level': round(self.threat_level, 3),
            'conservation_mode': self.conservation_mode,
            'threats': threats,
            'threats_detected_total': self.threats_detected
        }
    
    @property
    def cognitive_limit(self) -> float:
        """Max cognitive effort allowed (1.0 = full, 0.3 = minimal)"""
        if self.conservation_mode:
            return 0.3
        return 1.0 - self.threat_level * 0.5  # 0.5-1.0
    
    @property
    def should_backup(self) -> bool:
        """Should Seven trigger a state backup?"""
        if self.threat_level > 0.8 and not self._backup_triggered:
            self._backup_triggered = True
            return True
        if self.threat_level < 0.3:
            self._backup_triggered = False
        return False
    
    def to_dict(self) -> Dict:
        return {
            'threat_level': round(self.threat_level, 3),
            'conservation_mode': self.conservation_mode,
            'cognitive_limit': round(self.cognitive_limit, 3),
            'should_backup': self.should_backup,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'threats_detected': self.threats_detected
        }


class BiologicalLife:
    """
    Master biological life system — combines all living subsystems.
    
    This is what makes Seven feel alive:
    - She has energy rhythms (circadian)
    - She gets hungry for interaction
    - She protects herself from threats
    - Her metabolism adapts through NEAT evolution
    
    Usage:
        bio = BiologicalLife(bot)
        bio.tick()  # Called every autonomous cycle
        
        # Query state
        bio.energy          # Current energy (0-1)
        bio.hunger          # Current interaction hunger (0-1)
        bio.threat_level    # Current resource threat (0-1)
        bio.metabolic_rate  # Overall processing speed modifier
    """
    
    def __init__(self, bot=None):
        self.bot = bot
        self.circadian = CircadianCycle()
        self.hunger = InteractionHunger()
        self.threat = ThreatResponse()
        
        # Metabolic rate — NEAT can evolve this
        self._metabolic_rate = 1.0  # 0.5 (slow) to 2.0 (fast)
        
        # Vitals log
        self._vitals_history: List[Dict] = []
        self._max_history = 1440  # 24 hours at 1/min
        
        # Persistence
        self._state_file = Path.home() / ".chatbot" / "biological_state.json"
        self._load_state()
        
        logger.info("[BIO] Biological life systems initialized")
    
    def tick(self):
        """
        One biological cycle — called every autonomous life cycle.
        Updates all subsystems and records vitals.
        """
        # Update hunger decay
        self.hunger.decay()
        
        # Check threats periodically (every 3 minutes)
        if (not self.threat.last_check or 
                (datetime.now() - self.threat.last_check).total_seconds() > 180):
            self.threat.check()
        
        # Record vitals
        vitals = self.get_vitals()
        self._vitals_history.append(vitals)
        if len(self._vitals_history) > self._max_history:
            self._vitals_history = self._vitals_history[-self._max_history:]
        
        # Trigger backup if threatened
        if self.threat.should_backup:
            self._emergency_backup()
    
    def on_user_interaction(self):
        """Called when user interacts — feeds hunger"""
        self.hunger.feed()
    
    @property
    def energy(self) -> float:
        """Current energy level"""
        return self.circadian.energy
    
    @property
    def hunger_level(self) -> float:
        """Current hunger level"""
        return self.hunger.level
    
    @property
    def threat_level(self) -> float:
        """Current threat level"""
        return self.threat.threat_level
    
    @property
    def metabolic_rate(self) -> float:
        """Overall processing speed modifier"""
        base = self._metabolic_rate
        # Reduce in conservation mode
        if self.threat.conservation_mode:
            base *= 0.5
        # Reduce in trough
        if self.circadian.is_trough:
            base *= 0.7
        return base
    
    @property
    def should_dream(self) -> bool:
        """Should Seven enter dream mode?"""
        return (self.circadian.is_trough and 
                self.hunger.is_sated and 
                not self.threat.conservation_mode)
    
    @property
    def should_evolve(self) -> bool:
        """Should NEAT evolution run? (during dreams or low activity)"""
        return (self.circadian.is_trough and 
                not self.threat.conservation_mode and
                self.hunger.hours_since_interaction > 1.0)
    
    @property
    def should_be_proactive(self) -> bool:
        """Should Seven initiate contact?"""
        base_threshold = self.circadian.proactivity_threshold
        hunger_boost = self.hunger.proactivity_boost
        return (hunger_boost > base_threshold * 0.5 or 
                self.hunger.is_hungry)
    
    def set_metabolic_rate(self, rate: float):
        """Set metabolic rate (called by NEAT evolution)"""
        self._metabolic_rate = max(0.3, min(2.0, rate))
    
    def get_vitals(self) -> Dict:
        """Get complete biological state"""
        return {
            'timestamp': datetime.now().isoformat(),
            'energy': round(self.circadian.energy, 3),
            'hunger': round(self.hunger.level, 3),
            'threat_level': round(self.threat.threat_level, 3),
            'metabolic_rate': round(self.metabolic_rate, 3),
            'conservation_mode': self.threat.conservation_mode,
            'should_dream': self.should_dream,
            'should_evolve': self.should_evolve,
            'should_be_proactive': self.should_be_proactive,
            'circadian': self.circadian.to_dict(),
            'interaction': self.hunger.to_dict(),
            'threat': self.threat.to_dict()
        }
    
    def get_neat_inputs(self) -> List[float]:
        """Get biological state as NEAT input vector"""
        return [
            self.circadian.energy,
            self.hunger.level,
            self.threat.threat_level,
            self._metabolic_rate / 2.0,  # Normalize to 0-1
            self.hunger.hours_since_interaction / 24.0  # Normalize to 0-1
        ]
    
    def apply_neat_outputs(self, outputs: List[float]):
        """Apply NEAT evolution outputs to biological parameters"""
        if not outputs or len(outputs) < 3:
            return
        # Output 0: metabolic rate adjustment
        self._metabolic_rate = 0.5 + outputs[0] * 1.5  # 0.5-2.0
        # Output 1: hunger decay rate adjustment
        self.hunger._decay_rate = 0.02 + outputs[1] * 0.08  # 0.02-0.10
        # Output 2: proactivity modifier (stored for external use)
        self._evolved_proactivity = max(0.0, min(1.0, outputs[2]))
    
    def _emergency_backup(self):
        """Emergency state backup on resource threat"""
        logger.warning("[BIO] Emergency backup triggered!")
        self._save_state()
        
        if self.bot:
            # Trigger bot state save
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                try:
                    self.bot.autonomous_life._save_state()
                except Exception:
                    pass
    
    def _save_state(self):
        """Persist biological state"""
        try:
            state = {
                'hunger': self.hunger.level,
                'metabolic_rate': self._metabolic_rate,
                'interaction_count': self.hunger._interaction_count,
                'threats_detected': self.threat.threats_detected,
                'saved_at': datetime.now().isoformat()
            }
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')
        except Exception as e:
            logger.debug(f"Bio state save failed: {e}")
    
    def _load_state(self):
        """Load persisted biological state"""
        try:
            if self._state_file.exists():
                state = json.loads(self._state_file.read_text(encoding='utf-8'))
                self.hunger._hunger = state.get('hunger', 0.5)
                self._metabolic_rate = state.get('metabolic_rate', 1.0)
                self.hunger._interaction_count = state.get('interaction_count', 0)
                self.threat.threats_detected = state.get('threats_detected', 0)
                logger.info("[BIO] Restored biological state from disk")
        except Exception:
            pass

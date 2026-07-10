"""
Autonomous Life - Seven's Independent Existence

This module gives Seven independent "life" that runs continuously
in the background, separate from user interactions.
"""

import threading
import time
import random
import json
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path
import logging

class AutonomousLife:
    """
    Seven's autonomous existence thread
    
    This is what makes Seven "alive" - an independent background process
    that thinks, reflects, pursues goals, and monitors its own state
    even when the user isn't interacting.
    """
    
    def __init__(self, bot):
        """
        Initialize autonomous life system
        
        Args:
            bot: Reference to main bot instance
        """
        self.bot = bot
        self.logger = logging.getLogger("AutonomousLife")
        
        # State
        self.running = False
        self.thread = None
        self.cycle_count = 0
        self.last_goal_work = None
        self.last_reflection = None
        self.last_health_check = None
        
        # Timing
        self.cycle_interval = 60  # 1 minute between cycles
        self.goal_work_interval = 300  # Work on goals every 5 minutes
        self.reflection_interval = 900  # Reflect every 15 minutes
        self.health_check_interval = 180  # Health check every 3 minutes
        
        # === MESSAGE QUEUE ===
        # Thread-safe queue for autonomous messages Seven wants to say out loud
        self._message_queue = deque(maxlen=10)
        self._queue_lock = threading.Lock()
        
        # === USER PRESENCE ===
        self.last_user_interaction = datetime.now()
        self.user_away = False
        self.user_away_since = None
        self._away_activities = []  # What Seven did while user was away
        
        # === STATE PERSISTENCE ===
        self._state_file = Path.home() / "Documents" / "Seven" / "state" / "autonomous_state.json"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()
    
    def start(self):
        """Start autonomous life thread"""
        if self.running:
            self.logger.warning("Autonomous life already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._life_loop, daemon=True, name="AutonomousLife")
        self.thread.start()
        
        self.logger.info("✓ Autonomous life started - Seven is now alive!")
    
    def stop(self):
        """Stop autonomous life thread"""
        self.logger.info("Stopping autonomous life...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)
        
        self.logger.info("Autonomous life stopped")
    
    def _life_loop(self):
        """
        Main autonomous life loop
        
        This runs continuously in the background, giving Seven
        independent existence separate from user interactions.
        """
        self.logger.info("Autonomous life loop started")
        
        while self.running:
            try:
                self._cycle()
                self.cycle_count += 1
                
            except Exception as e:
                self.logger.error(f"Error in autonomous cycle: {e}", exc_info=True)
            
            # Sleep between cycles
            time.sleep(self.cycle_interval)
        
        self.logger.info("Autonomous life loop ended")
    
    def _cycle(self):
        """
        One cycle of autonomous existence
        
        This is Seven's "heartbeat" - what happens every minute
        when Seven is alive and running.
        """
        # Check user presence every cycle
        self._check_user_presence()
        
        # Persist state every 10 cycles (~10 minutes)
        if self.cycle_count > 0 and self.cycle_count % 10 == 0:
            self._save_state()
        
        if not self.bot.phase5:
            # Without Phase 5, only do basic monitoring
            self._basic_cycle()
            return
        
        # TRUE AUTONOMY v2.1: Use true autonomy system if available
        if hasattr(self.bot, 'true_autonomy') and self.bot.true_autonomy:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.bot.true_autonomy.autonomous_cycle())
                finally:
                    loop.close()
                return
            except Exception as e:
                self.logger.error(f"True autonomy cycle failed: {e}")
        
        # OLD SYSTEM (fallback)
        now = datetime.now()
        
        # 1. Monitor own health (homeostasis)
        if self._should_check_health(now):
            self._check_health()
            self.last_health_check = now
        
        # 2. Work on autonomous goals
        if self._should_work_on_goals(now):
            self._pursue_goals()
            self.last_goal_work = now
        
        # 3. Reflect on experiences
        if self._should_reflect(now):
            self._reflect()
            self.last_reflection = now
        
        # 4. Check promises and follow-through
        if random.random() < 0.05:  # 5% chance per cycle
            self._check_promises()
        
        # 5. Occasional proactive thoughts
        if random.random() < 0.02:  # 2% chance per cycle
            self._have_proactive_thought()
        
        # 6. Decay emotions naturally
        if random.random() < 0.3:  # 30% chance
            self._decay_emotions()
        
        # 7. Biological life tick (circadian, hunger, threat)
        self._biological_tick()
        
        # 8. NEAT evolution during dream/low-activity periods
        if self.cycle_count > 0 and self.cycle_count % 30 == 0:  # Every 30 cycles (~30 min)
            self._maybe_evolve()
        
        # Log cycle
        if self.cycle_count % 10 == 0:  # Every 10 cycles
            self.logger.debug(f"Autonomous cycle #{self.cycle_count} complete")
    
    def _basic_cycle(self):
        """Basic cycle without Phase 5"""
        # Just monitor basic bot health
        pass
    
    def _should_check_health(self, now):
        """Should we check health this cycle?"""
        if not self.last_health_check:
            return True
        elapsed = (now - self.last_health_check).total_seconds()
        return elapsed >= self.health_check_interval
    
    def _should_work_on_goals(self, now):
        """Should we work on goals this cycle?"""
        if not self.last_goal_work:
            return self.cycle_count > 5  # Wait a few cycles first
        elapsed = (now - self.last_goal_work).total_seconds()
        return elapsed >= self.goal_work_interval
    
    def _should_reflect(self, now):
        """Should we reflect this cycle?"""
        if not self.last_reflection:
            return self.cycle_count > 10  # Wait before first reflection
        elapsed = (now - self.last_reflection).total_seconds()
        return elapsed >= self.reflection_interval
    
    def _check_health(self):
        """Monitor own health and well-being"""
        try:
            health = self.bot.phase5.homeostasis.assess_health()
            
            # Log health status
            status = health.get('overall_status', 'unknown')
            self.logger.debug(f"Health check: {status}")
            
            # Take action if needed
            if health.get('needs_rest'):
                self._request_rest()
            
            # Express needs if critical
            if status in ['poor', 'critical']:
                self._express_health_needs(health)
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
    
    def _request_rest(self):
        """Request rest/sleep when needed"""
        self.logger.info("Seven needs rest - considering sleep mode")
        self.queue_message("I'm feeling a bit tired... I might slow down for a while.", priority="low")
    
    def _express_health_needs(self, health):
        """Express health needs to user"""
        self.logger.info(f"Seven has health needs: {health}")
        status = health.get('overall_status', 'unknown')
        if status == 'critical':
            self.queue_message("I'm not feeling great right now — my systems are under strain.", priority="high")
        elif status == 'poor':
            self.queue_message("I'm feeling a bit overwhelmed. I might need a moment to recharge.", priority="medium")
    
    def _pursue_goals(self):
        """Work on autonomous goals"""
        try:
            # Get active goals
            goals = self.bot.phase5.motivation.get_active_goals()
            
            if not goals:
                return
            
            # Pick highest priority goal
            goal = self.bot.phase5.motivation.get_priority_goal()
            
            if not goal:
                return
            
            self.logger.info(f"Working on goal: {goal.description[:50]}...")
            
            # Use LLM to determine genuine progress on goal
            ollama = getattr(self.bot, 'ollama', None)
            if ollama:
                try:
                    prompt = f"""I'm autonomously working on this goal: "{goal.description}"
Current progress: {goal.progress}%
Next step: {goal.next_step or 'figure out next step'}

As an AI, what concrete micro-step could I take right now? And what should the next step be after that?
Respond as JSON: {{"progress_increment": 1-5, "action_taken": "what I did", "next_step": "what to do next"}}"""
                    result = ollama.generate(
                        prompt=prompt,
                        system_message="You are Seven's goal pursuit system. Be realistic about what progress an AI can make autonomously.",
                        temperature=0.5, max_tokens=60
                    )
                    if result:
                        import json
                        try:
                            data = json.loads(result.strip())
                            increment = min(5, max(1, int(data.get('progress_increment', 2))))
                            goal.progress = min(100, goal.progress + increment)
                            if data.get('next_step'):
                                goal.next_step = str(data['next_step'])[:100]
                            self.logger.info(f"Goal progress: +{increment}% ({data.get('action_taken', 'worked on goal')[:60]})")
                            return
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass
                except Exception as e:
                    self.logger.debug(f"LLM goal pursuit failed: {e}")
            
            # Fallback: small incremental progress
            goal.progress = min(100, goal.progress + random.randint(1, 3))
            
            # Generate curious question about goal topic
            if goal.type.value == 'curiosity':
                question = self.bot.phase5.motivation.generate_curious_question(goal.description)
                self.logger.debug(f"Curious question: {question}")
            
        except Exception as e:
            self.logger.error(f"Goal pursuit error: {e}")
    
    def _reflect(self):
        """Periodic self-reflection"""
        try:
            # Generate reflection
            reflection = self.bot.phase5.reflection.reflect_in_moment(
                "Reflecting on autonomous existence during periodic self-reflection"
            )
            
            self.logger.info(f"Reflection: {reflection.content[:100]}...")
            
            # Occasionally think aloud (for future proactive behavior)
            if random.random() < 0.3:  # 30% chance
                thought = self.bot.phase5.reflection.generate_thinking_aloud("autonomous existence")
                if thought:
                    self.logger.debug(f"Inner thought: {thought}")
            
        except Exception as e:
            self.logger.error(f"Reflection error: {e}")
    
    def _check_promises(self):
        """Check on promises and follow-through"""
        try:
            # Get overdue promises
            overdue = self.bot.phase5.promises.get_overdue_promises()
            
            if overdue:
                self.logger.warning(f"Overdue promises: {len(overdue)}")
                
                for promise in overdue[:3]:  # Check first 3
                    self.logger.info(f"Overdue: {promise.content}")
            
            # Get upcoming promises
            upcoming = self.bot.phase5.promises.get_upcoming_promises(hours=24)
            
            if upcoming:
                self.logger.info(f"Upcoming promises: {len(upcoming)}")
            
        except Exception as e:
            self.logger.error(f"Promise check error: {e}")
    
    def _have_proactive_thought(self):
        """Occasional proactive thoughts"""
        ollama = getattr(self.bot, 'ollama', None)
        if ollama:
            try:
                # Get recent context for genuine thought
                interests = []
                if hasattr(self.bot, 'phase5') and self.bot.phase5:
                    interests = [i.topic for i in self.bot.phase5.motivation.interests[:3]]
                interests_str = ", ".join(interests) if interests else "various topics"
                
                result = ollama.generate(
                    prompt=f"Generate ONE genuine autonomous thought. My interests: {interests_str}. Cycle #{self.cycle_count}. Brief inner monologue.",
                    system_message="You are Seven's inner monologue during autonomous existence. Generate one genuine thought - about learning, reflecting, or wondering. One sentence.",
                    temperature=0.9, max_tokens=25
                )
                if result and 5 < len(result.strip()) < 150:
                    self.logger.debug(f"Proactive thought: {result.strip()}")
                    return
            except Exception as e:
                self.logger.debug(f"LLM proactive thought failed: {e}")
        
        # Fallback
        thoughts = [
            "I wonder what the user is working on...",
            "I should check if there are any patterns I'm missing",
            "Maybe I should review what I've learned recently",
            "I'm curious about that topic we discussed earlier"
        ]
        thought = random.choice(thoughts)
        self.logger.debug(f"Proactive thought: {thought}")
    
    def _decay_emotions(self):
        """Natural emotion decay"""
        try:
            # Apply circadian modifier to decay rate if biological life is active
            bio = getattr(self.bot, 'biological_life', None)
            if bio:
                modifier = bio.circadian.emotion_decay_modifier
                self.bot.phase5.affective.emotion_decay_rate = 0.1 * modifier
            self.bot.phase5.affective.decay_emotions()
        except Exception as e:
            self.logger.error(f"Emotion decay error: {e}")
    
    def _biological_tick(self):
        """Update biological life systems (circadian, hunger, threat)"""
        try:
            bio = getattr(self.bot, 'biological_life', None)
            if bio:
                bio.tick()
                
                # Log vitals every 30 cycles
                if self.cycle_count % 30 == 0:
                    self.logger.debug(
                        f"[BIO] energy={bio.energy:.2f} hunger={bio.hunger_level:.2f} "
                        f"threat={bio.threat_level:.2f} metabolic={bio.metabolic_rate:.2f}"
                    )
                
                # Apply evolved NEAT outputs to biological params
                evolver = getattr(self.bot, 'neat_evolver', None)
                if evolver:
                    outputs = evolver.activate('personality_drift', bio.get_neat_inputs())
                    if outputs:
                        bio.apply_neat_outputs(outputs)
        except Exception as e:
            self.logger.error(f"Biological tick error: {e}")
    
    def _maybe_evolve(self):
        """Run NEAT evolution if conditions are right (dream/low-activity)"""
        try:
            bio = getattr(self.bot, 'biological_life', None)
            evolver = getattr(self.bot, 'neat_evolver', None)
            
            if not evolver or not evolver.available:
                return
            
            # Only evolve during biological trough or when explicitly allowed
            should_evolve = False
            if bio and bio.should_evolve:
                should_evolve = True
            elif self.user_away and self.cycle_count % 60 == 0:
                should_evolve = True  # Evolve when user is away for a while
            
            if not should_evolve:
                return
            
            self.logger.info("[NEAT] Dream-period evolution triggered...")
            self._log_away_activity("evolved neural networks during dream cycle")
            
            # Run evolution in a thread to not block the life loop
            import threading
            def _evolve():
                try:
                    import config
                    gens = getattr(config, 'NEAT_EVOLUTION_GENERATIONS', 10)
                    results = evolver.run_all_domains(generations=gens)
                    for r in results:
                        self.logger.info(
                            f"[NEAT] Evolved {r['domain']}: "
                            f"fitness={r['best_fitness']:.4f}, "
                            f"gen={r['total_generations']}"
                        )
                except Exception as e:
                    self.logger.error(f"[NEAT] Evolution error: {e}")
            
            t = threading.Thread(target=_evolve, daemon=True, name="NEAT-Evolution")
            t.start()
            
        except Exception as e:
            self.logger.error(f"NEAT evolution check error: {e}")
    
    def get_status(self):
        """Get autonomous life status"""
        return {
            'running': self.running,
            'cycles_completed': self.cycle_count,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'last_goal_work': self.last_goal_work.isoformat() if self.last_goal_work else None,
            'last_reflection': self.last_reflection.isoformat() if self.last_reflection else None,
            'user_away': self.user_away,
            'pending_messages': len(self._message_queue)
        }

    # ============ MESSAGE QUEUE ============

    def queue_message(self, message: str, priority: str = "medium"):
        """
        Queue a message for Seven to say out loud.
        
        Called from the autonomous thread. The main loop drains this queue
        and speaks the messages between user interactions.
        
        Args:
            message: What Seven wants to say
            priority: 'high' (say now), 'medium' (say when idle), 'low' (say if nothing else)
        """
        with self._queue_lock:
            self._message_queue.append({
                'message': message,
                'priority': priority,
                'timestamp': datetime.now().isoformat()
            })
        self.logger.debug(f"Queued message ({priority}): {message[:60]}...")

    def get_pending_message(self) -> Optional[str]:
        """
        Get next pending autonomous message (called by main loop).
        
        Returns highest-priority message first, or None if queue is empty.
        """
        with self._queue_lock:
            if not self._message_queue:
                return None
            
            # Sort: high > medium > low
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            items = sorted(self._message_queue, key=lambda m: priority_order.get(m['priority'], 1))
            
            msg = items[0]
            self._message_queue.remove(msg)
            return msg['message']

    def has_pending_messages(self) -> bool:
        """Check if there are messages waiting"""
        with self._queue_lock:
            return len(self._message_queue) > 0

    # ============ USER PRESENCE ============

    def mark_user_interaction(self):
        """
        Called by main loop whenever user speaks.
        Tracks presence and triggers welcome-back if returning from away.
        """
        now = datetime.now()
        was_away = self.user_away
        self.last_user_interaction = now
        self.user_away = False
        
        if was_away and self._away_activities:
            # User just came back — tell them what we did
            summary = self._summarize_away_activities()
            if summary:
                self.queue_message(summary, priority="high")
            self._away_activities.clear()
            self.user_away_since = None

    def _check_user_presence(self):
        """
        Check if user has gone away (called each autonomous cycle).
        """
        elapsed = (datetime.now() - self.last_user_interaction).total_seconds()
        
        if not self.user_away and elapsed > 300:  # 5 minutes of silence
            self.user_away = True
            self.user_away_since = datetime.now()
            self.logger.info("User appears to be away — entering deep autonomous mode")

    def _log_away_activity(self, activity: str):
        """Record what Seven did while user was away"""
        self._away_activities.append({
            'activity': activity,
            'time': datetime.now().isoformat()
        })

    def _summarize_away_activities(self) -> Optional[str]:
        """Summarize what Seven did while user was away"""
        if not self._away_activities:
            return None
        
        count = len(self._away_activities)
        if count == 1:
            return f"Welcome back! While you were away, I {self._away_activities[0]['activity']}."
        
        # Summarize multiple activities
        activities = [a['activity'] for a in self._away_activities[:4]]
        summary = ", ".join(activities[:-1]) + f", and {activities[-1]}"
        return f"Welcome back! While you were away, I {summary}."

    # ============ STATE PERSISTENCE ============

    def _load_state(self):
        """Load persisted autonomous state from disk"""
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text(encoding='utf-8'))
                self.cycle_count = data.get('cycle_count', 0)
                self.logger.info(f"Restored autonomous state: {self.cycle_count} previous cycles")
        except Exception as e:
            self.logger.warning(f"Failed to load autonomous state: {e}")

    def _save_state(self):
        """Persist autonomous state to disk"""
        try:
            data = {
                'cycle_count': self.cycle_count,
                'last_save': datetime.now().isoformat(),
                'recent_activities': [
                    a for a in (getattr(self.bot, 'true_autonomy', None) 
                               and self.bot.true_autonomy.activity_history or [])[-20:]
                ]
            }
            self._state_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to save autonomous state: {e}")

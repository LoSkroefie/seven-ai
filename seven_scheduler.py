"""
Seven AI Persistent Scheduler

APScheduler-based task scheduling for autonomous proactive behavior.
Persists jobs to SQLite so they survive restarts.

Features:
    - Cron-style scheduling (e.g., "check email every 30 min")
    - Interval scheduling (e.g., "reflect every 15 min")
    - One-shot delayed tasks (e.g., "remind me in 2 hours")
    - Persistent job store (survives restarts)
    - Built-in proactive tasks (email check, goal review, reflection, health)
    - External trigger registration
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Callable, Any

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.date import DateTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

logger = logging.getLogger("SevenScheduler")

JOB_STORE_PATH = Path.home() / ".chatbot" / "scheduler_jobs.db"
JOB_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


class SevenScheduler:
    """
    Persistent task scheduler for Seven's autonomous behavior.
    
    Uses APScheduler with SQLite backend so scheduled tasks
    survive restarts. This is what makes Seven truly autonomous —
    she can schedule her own future actions.
    """
    
    def __init__(self, bot=None):
        self.bot = bot
        self.available = APSCHEDULER_AVAILABLE
        self.scheduler = None
        self._custom_handlers: Dict[str, Callable] = {}
        
        if not self.available:
            logger.warning("APScheduler not installed. Run: pip install apscheduler sqlalchemy")
            return
        
        # Configure scheduler with persistent SQLite job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{JOB_STORE_PATH}')
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            job_defaults={
                'coalesce': True,       # Combine missed runs into one
                'max_instances': 1,      # Only one instance of each job
                'misfire_grace_time': 300  # 5 min grace for missed jobs
            },
            timezone='UTC'
        )
        
        logger.info(f"[SCHEDULER] Initialized with persistent store: {JOB_STORE_PATH}")
    
    def start(self):
        """Start the scheduler and register built-in proactive tasks"""
        if not self.available or not self.scheduler:
            return
        
        self.scheduler.start()
        self._register_builtin_tasks()
        
        jobs = self.scheduler.get_jobs()
        logger.info(f"[SCHEDULER] Started with {len(jobs)} persisted job(s)")
    
    def stop(self):
        """Stop scheduler gracefully"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("[SCHEDULER] Stopped")
    
    def _register_builtin_tasks(self):
        """Register Seven's built-in proactive tasks"""
        # Only add if not already persisted
        existing = {j.id for j in self.scheduler.get_jobs()}
        
        builtins = [
            {
                'id': 'seven_self_reflection',
                'func': self._task_self_reflection,
                'trigger': IntervalTrigger(minutes=15),
                'name': 'Self-reflection cycle'
            },
            {
                'id': 'seven_goal_review',
                'func': self._task_goal_review,
                'trigger': IntervalTrigger(minutes=10),
                'name': 'Goal progress review'
            },
            {
                'id': 'seven_health_check',
                'func': self._task_health_check,
                'trigger': IntervalTrigger(minutes=5),
                'name': 'Health & homeostasis check'
            },
            {
                'id': 'seven_email_check',
                'func': self._task_email_check,
                'trigger': IntervalTrigger(minutes=30),
                'name': 'Email check'
            },
            {
                'id': 'seven_emotion_decay',
                'func': self._task_emotion_decay,
                'trigger': IntervalTrigger(minutes=3),
                'name': 'Natural emotion decay'
            },
            {
                'id': 'seven_memory_consolidation',
                'func': self._task_memory_consolidation,
                'trigger': IntervalTrigger(hours=1),
                'name': 'Memory consolidation (dream-like)'
            },
            {
                'id': 'seven_neat_evolution',
                'func': self._task_neat_evolution,
                'trigger': IntervalTrigger(hours=8),
                'name': 'NEAT neuroevolution cycle'
            },
            {
                'id': 'seven_biological_vitals',
                'func': self._task_biological_vitals,
                'trigger': IntervalTrigger(minutes=5),
                'name': 'Biological vitals check'
            },
            {
                'id': 'seven_lora_training',
                'func': self._task_lora_training,
                'trigger': IntervalTrigger(hours=24),
                'name': 'LoRA continual fine-tuning check'
            },
            {
                'id': 'seven_social_sim',
                'func': self._task_social_sim,
                'trigger': IntervalTrigger(hours=4),
                'name': 'Social simulation (internal debate)'
            },
            {
                'id': 'seven_user_predictor',
                'func': self._task_user_predictor,
                'trigger': IntervalTrigger(hours=6),
                'name': 'Predictive user modeling'
            },
            {
                'id': 'seven_extensions_run',
                'func': self._task_extensions_run,
                'trigger': IntervalTrigger(minutes=30),
                'name': 'Extension scheduled runner'
            },
        ]
        
        for task in builtins:
            if task['id'] not in existing:
                self.scheduler.add_job(
                    task['func'],
                    trigger=task['trigger'],
                    id=task['id'],
                    name=task['name'],
                    replace_existing=True
                )
                logger.info(f"[SCHEDULER] Registered: {task['name']}")
    
    # ============ Public API ============
    
    def add_interval_job(self, job_id: str, func: Callable, minutes: int, name: str = None):
        """Add an interval-based job"""
        if not self.scheduler:
            return
        self.scheduler.add_job(
            func, IntervalTrigger(minutes=minutes),
            id=job_id, name=name or job_id, replace_existing=True
        )
    
    def add_cron_job(self, job_id: str, func: Callable, cron_expr: str, name: str = None):
        """Add a cron-style job (e.g., '0 9 * * *' for 9am daily)"""
        if not self.scheduler:
            return
        parts = cron_expr.split()
        trigger = CronTrigger(
            minute=parts[0] if len(parts) > 0 else '*',
            hour=parts[1] if len(parts) > 1 else '*',
            day=parts[2] if len(parts) > 2 else '*',
            month=parts[3] if len(parts) > 3 else '*',
            day_of_week=parts[4] if len(parts) > 4 else '*'
        )
        self.scheduler.add_job(
            func, trigger,
            id=job_id, name=name or job_id, replace_existing=True
        )
    
    def add_oneshot_job(self, job_id: str, func: Callable, run_at: datetime, name: str = None):
        """Add a one-time delayed job"""
        if not self.scheduler:
            return
        self.scheduler.add_job(
            func, DateTrigger(run_date=run_at),
            id=job_id, name=name or job_id, replace_existing=True
        )
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job"""
        if not self.scheduler:
            return
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            pass
    
    def list_jobs(self) -> list:
        """List all scheduled jobs"""
        if not self.scheduler:
            return []
        return [
            {
                'id': j.id,
                'name': j.name,
                'next_run': str(j.next_run_time) if j.next_run_time else None,
                'trigger': str(j.trigger)
            }
            for j in self.scheduler.get_jobs()
        ]
    
    # ============ Built-in Proactive Tasks ============
    
    def _task_self_reflection(self):
        """Periodic self-reflection — Seven thinks about her own thinking"""
        if not self.bot:
            return
        try:
            # Use self-reflection module if available
            if hasattr(self.bot, 'self_reflection') and self.bot.self_reflection:
                self.bot.self_reflection.reflect(depth='normal')
                return
            
            # Fallback: Phase 5 reflection
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                if hasattr(self.bot.phase5, 'reflection'):
                    self.bot.phase5.reflection.reflect()
                    
            logger.debug("[TASK] Self-reflection completed")
        except Exception as e:
            logger.error(f"[TASK] Self-reflection error: {e}")
    
    def _task_goal_review(self):
        """Review and pursue autonomous goals"""
        if not self.bot:
            return
        try:
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life._pursue_goals()
            logger.debug("[TASK] Goal review completed")
        except Exception as e:
            logger.error(f"[TASK] Goal review error: {e}")
    
    def _task_health_check(self):
        """Monitor Seven's own health"""
        if not self.bot:
            return
        try:
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                if hasattr(self.bot.phase5, 'homeostasis'):
                    self.bot.phase5.homeostasis.assess_health()
            logger.debug("[TASK] Health check completed")
        except Exception as e:
            logger.error(f"[TASK] Health check error: {e}")
    
    def _task_email_check(self):
        """Check for new emails proactively"""
        if not self.bot:
            return
        try:
            if hasattr(self.bot, 'email_checker') and self.bot.email_checker:
                result = self.bot.email_checker.check_new()
                if result and hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                    self.bot.autonomous_life.queue_message(
                        f"I checked your email — {result}",
                        priority="medium"
                    )
            logger.debug("[TASK] Email check completed")
        except Exception as e:
            logger.error(f"[TASK] Email check error: {e}")
    
    def _task_emotion_decay(self):
        """Natural emotion decay over time"""
        if not self.bot:
            return
        try:
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                if hasattr(self.bot.phase5, 'affective'):
                    self.bot.phase5.affective.decay_emotions()
            logger.debug("[TASK] Emotion decay applied")
        except Exception as e:
            logger.error(f"[TASK] Emotion decay error: {e}")
    
    def _task_neat_evolution(self):
        """Run NEAT neuroevolution cycle (evolve Seven's neural components)"""
        if not self.bot:
            return
        try:
            evolver = getattr(self.bot, 'neat_evolver', None)
            bio = getattr(self.bot, 'biological_life', None)
            
            if not evolver or not evolver.available:
                return
            
            # Only evolve if not in conservation mode
            if bio and bio.threat.conservation_mode:
                logger.debug("[TASK] Skipping evolution — conservation mode")
                return
            
            results = evolver.run_all_domains(generations=5)
            for r in results:
                logger.info(f"[TASK] NEAT evolved {r['domain']}: fitness={r['best_fitness']:.4f}")
        except Exception as e:
            logger.error(f"[TASK] NEAT evolution error: {e}")
    
    def _task_biological_vitals(self):
        """Check biological vitals (circadian, hunger, threat)"""
        if not self.bot:
            return
        try:
            bio = getattr(self.bot, 'biological_life', None)
            if bio:
                bio.tick()
                logger.debug(
                    f"[TASK] Vitals: energy={bio.energy:.2f} "
                    f"hunger={bio.hunger_level:.2f} threat={bio.threat_level:.2f}"
                )
        except Exception as e:
            logger.error(f"[TASK] Biological vitals error: {e}")
    
    def _task_memory_consolidation(self):
        """Consolidate memories (dream-like processing)"""
        if not self.bot:
            return
        try:
            if hasattr(self.bot, 'phase5') and self.bot.phase5:
                if hasattr(self.bot.phase5, 'dream'):
                    self.bot.phase5.dream.process()
            logger.debug("[TASK] Memory consolidation completed")
        except Exception as e:
            logger.error(f"[TASK] Memory consolidation error: {e}")
    
    # ============ v3.2 Tasks ============
    
    def _task_lora_training(self):
        """Check if LoRA fine-tuning should run, and trigger it"""
        if not self.bot:
            return
        try:
            trainer = getattr(self.bot, 'lora_trainer', None)
            if not trainer:
                return
            
            if trainer.should_train():
                logger.info("[TASK] LoRA training threshold reached — starting training")
                report = trainer.train()
                logger.info(f"[TASK] LoRA training: status={report.get('status')}, examples={report.get('examples_used', 0)}")
            else:
                logger.debug("[TASK] LoRA training: not yet needed")
        except Exception as e:
            logger.error(f"[TASK] LoRA training error: {e}")
    
    def _task_social_sim(self):
        """Run social simulation debate during idle/dream periods"""
        if not self.bot:
            return
        try:
            sim = getattr(self.bot, 'social_sim', None)
            if not sim:
                return
            
            # Only run during low activity or dream cycles
            bio = getattr(self.bot, 'biological_life', None)
            if bio and bio.threat.conservation_mode:
                logger.debug("[TASK] Skipping social sim — conservation mode")
                return
            
            result = sim.run_debate(rounds=2)
            if result:
                logger.info(
                    f"[TASK] Social sim: topic='{result.topic[:50]}...', "
                    f"contributions={len(result.contributions)}, "
                    f"duration={result.duration}s"
                )
        except Exception as e:
            logger.error(f"[TASK] Social simulation error: {e}")
    
    def _task_user_predictor(self):
        """Retrain user prediction model"""
        if not self.bot:
            return
        try:
            predictor = getattr(self.bot, 'user_predictor', None)
            if not predictor:
                return
            
            report = predictor.train()
            logger.info(
                f"[TASK] User predictor: status={report.get('status')}, "
                f"records={report.get('records_used', 0)}, "
                f"mood={predictor.predictions.get('mood_trend', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"[TASK] User predictor error: {e}")
    
    def _task_extensions_run(self):
        """Run scheduled extensions"""
        if not self.bot:
            return
        try:
            loader = getattr(self.bot, 'plugin_loader', None)
            if not loader:
                return
            
            scheduled = loader.get_scheduled_extensions()
            for ext_id, interval, cron in scheduled:
                if interval > 0:
                    result = loader.run_extension(ext_id)
                    if result:
                        logger.debug(f"[TASK] Extension {ext_id}: {result}")
        except Exception as e:
            logger.error(f"[TASK] Extension runner error: {e}")

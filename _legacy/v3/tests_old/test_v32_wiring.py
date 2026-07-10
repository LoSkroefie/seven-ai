"""
Integration tests for Seven AI v3.2 wiring chain.

Verifies that all modules import cleanly and the initialization chain
is properly connected:
  Daemon → Scheduler → Multi-Agent → NEAT → LoRA → Robotics → Social Sim → Predictor → Extensions

Run: python -m pytest tests/test_v32_wiring.py -v
  or: python tests/test_v32_wiring.py
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModuleImports(unittest.TestCase):
    """Verify all v3.x modules import without errors"""

    def test_import_social_sim(self):
        from core.social_sim import SocialSimulation, Persona, DebateResult
        self.assertEqual(len(Persona), 4)

    def test_import_lora_trainer(self):
        from learning.lora_trainer import LoRATrainer

    def test_import_user_predictor(self):
        from core.user_predictor import UserPredictor

    def test_import_robotics(self):
        from integrations.robotics import RoboticsController, SerialDevice

    def test_import_plugin_loader(self):
        from utils.plugin_loader import PluginLoader

    def test_import_neat_evolver(self):
        from evolution.neat_evolver import NEATEvolver

    def test_import_biological_life(self):
        from evolution.biological_life import BiologicalLife

    def test_import_self_reflection(self):
        from core.self_reflection import SelfReflection

    def test_import_multi_agent(self):
        from core.multi_agent import MultiAgentOrchestrator

    def test_import_bot_initializers(self):
        from core.bot_initializers import (
            init_integration_modules,
            init_communication_clients,
            init_sentience_v2,
            init_v3_systems,
            init_v32_features,
            init_trackers,
        )

    def test_import_daemon(self):
        from seven_daemon import SevenDaemon

    def test_import_scheduler(self):
        from seven_scheduler import SevenScheduler

    def test_import_api(self):
        from seven_api import create_app


class TestDaemonSetup(unittest.TestCase):
    """Verify daemon uses RotatingFileHandler"""

    def test_rotating_handler(self):
        import logging.handlers
        from seven_daemon import SevenDaemon

        daemon = SevenDaemon()
        handlers = daemon.logger.handlers
        rotating = [h for h in handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
        self.assertTrue(len(rotating) >= 1, "Daemon must use RotatingFileHandler")
        fh = rotating[0]
        self.assertEqual(fh.maxBytes, 1_000_000)
        self.assertEqual(fh.backupCount, 5)
        # Cleanup handlers to avoid leaking file descriptors
        for h in handlers:
            h.close()
        daemon.logger.handlers.clear()


class TestSchedulerTasks(unittest.TestCase):
    """Verify scheduler has all v3.2 task methods"""

    def test_scheduler_has_v32_tasks(self):
        from seven_scheduler import SevenScheduler

        required_tasks = [
            '_task_lora_training',
            '_task_social_sim',
            '_task_user_predictor',
            '_task_extensions_run',
            '_task_neat_evolution',
            '_task_biological_vitals',
        ]

        for task_name in required_tasks:
            self.assertTrue(
                hasattr(SevenScheduler, task_name),
                f"SevenScheduler missing task method: {task_name}"
            )


class TestSocialSimComplete(unittest.TestCase):
    """Verify social simulation is fully implemented (not truncated)"""

    def test_social_sim_has_all_methods(self):
        from core.social_sim import SocialSimulation

        required = [
            'run_debate',
            '_synthesize_consensus',
            '_calculate_emotional_influence',
            '_apply_influence',
            '_log_to_memory',
            'run_dream_session',
            'get_status',
            'generate_topic',
            'queue_topic',
        ]

        for method_name in required:
            self.assertTrue(
                hasattr(SocialSimulation, method_name),
                f"SocialSimulation missing method: {method_name}"
            )

    def test_social_sim_init_without_ollama(self):
        from core.social_sim import SocialSimulation
        sim = SocialSimulation(ollama=None, bot=None)
        self.assertEqual(len(sim.personas), 4)
        self.assertFalse(sim.is_running)

    def test_social_sim_debate_without_ollama_returns_none(self):
        from core.social_sim import SocialSimulation
        sim = SocialSimulation(ollama=None, bot=None)
        result = sim.run_debate()
        self.assertIsNone(result, "Debate without Ollama should return None")

    def test_social_sim_status(self):
        from core.social_sim import SocialSimulation
        sim = SocialSimulation(ollama=None, bot=None)
        status = sim.get_status()
        self.assertIn('available', status)
        self.assertIn('personas', status)
        self.assertEqual(len(status['personas']), 4)


class TestNoDummyFallbacks(unittest.TestCase):
    """Verify Fake* dummy classes are no longer used"""

    def test_no_fake_classes_in_enhanced_bot(self):
        """Scan enhanced_bot.py for inline Fake* class definitions"""
        bot_path = Path(__file__).parent.parent / 'core' / 'enhanced_bot.py'
        content = bot_path.read_text(encoding='utf-8')
        self.assertNotIn('class FakeRelationshipTracker', content,
                         "FakeRelationshipTracker still in enhanced_bot.py")
        self.assertNotIn('class FakeGoalManager', content,
                         "FakeGoalManager still in enhanced_bot.py")
        self.assertNotIn('class FakeLearningTracker', content,
                         "FakeLearningTracker still in enhanced_bot.py")


class TestAPIEndpoints(unittest.TestCase):
    """Verify v3.2 API endpoints are registered"""

    def test_v32_endpoints_exist(self):
        from seven_api import create_app
        app = create_app(bot_instance=None)

        routes = [r.path for r in app.routes]
        self.assertIn('/extensions', routes, "Missing /extensions endpoint")
        self.assertIn('/extensions/reload', routes, "Missing /extensions/reload endpoint")
        self.assertIn('/v32/status', routes, "Missing /v32/status endpoint")


class TestNoHypeLanguage(unittest.TestCase):
    """Verify hype language has been removed"""

    def test_no_unsurpassable_in_config(self):
        config_path = Path(__file__).parent.parent / 'config.py'
        content = config_path.read_text(encoding='utf-8')
        self.assertNotIn('UNSURPASSABLE', content.upper().replace('V3.2 FEATURES', ''),
                         "config.py still contains 'Unsurpassable'")

    def test_no_unsurpassable_in_readme(self):
        readme_path = Path(__file__).parent.parent / 'README.md'
        content = readme_path.read_text(encoding='utf-8')
        self.assertNotIn('Unsurpassable', content,
                         "README.md still contains 'Unsurpassable'")


if __name__ == '__main__':
    unittest.main(verbosity=2)

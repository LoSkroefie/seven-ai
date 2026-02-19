"""
Bot Initialization Helpers — Seven AI v3.2

Extracted from enhanced_bot.py to reduce monolithic __init__.
Each function initializes a logical group of subsystems on the bot instance.
All functions take (bot, config, logger) and set attributes on bot.

Import order matters — call these in sequence:
1. init_integration_modules(bot)
2. init_communication_clients(bot)
3. init_sentience_v2(bot)
4. init_v3_systems(bot)
5. init_v32_features(bot)
6. init_trackers(bot)
"""

import config


def init_integration_modules(bot):
    """Initialize all integration modules (music, ssh, screen, scripting, etc.)"""
    
    # Music Player
    bot.music_player = None
    if config.ENABLE_MUSIC_PLAYER:
        try:
            from integrations.music_player import MusicPlayer
            bot.music_player = MusicPlayer()
            if bot.music_player.available:
                bot.logger.info("[OK] Music player ready")
            else:
                bot.logger.info("[INFO] Music player loaded but yt-dlp/pygame not available")
        except Exception as e:
            bot.logger.warning(f"Music player initialization failed: {e}")
            bot.music_player = None

    # SSH Manager
    bot.ssh_manager = None
    if config.ENABLE_SSH_MANAGER:
        try:
            from integrations.ssh_manager import SSHManager
            bot.ssh_manager = SSHManager()
            bot.logger.info("[OK] SSH manager ready")
        except Exception as e:
            bot.logger.warning(f"SSH manager init failed: {e}")

    # System Monitor
    bot.system_monitor = None
    if config.ENABLE_SYSTEM_MONITOR:
        try:
            from integrations.system_monitor import SystemMonitor
            bot.system_monitor = SystemMonitor(bot_instance=bot)
            bot.logger.info("[OK] System monitor ready")
        except Exception as e:
            bot.logger.warning(f"System monitor init failed: {e}")

    # Clipboard Assistant
    bot.clipboard = None
    if config.ENABLE_CLIPBOARD_MONITOR:
        try:
            from integrations.clipboard_assistant import ClipboardAssistant
            bot.clipboard = ClipboardAssistant(bot_instance=bot)
            bot.logger.info("[OK] Clipboard assistant ready")
        except Exception as e:
            bot.logger.warning(f"Clipboard assistant init failed: {e}")

    # Screen Control
    bot.screen_control = None
    if config.ENABLE_SCREEN_CONTROL:
        try:
            from integrations.screen_control import ScreenControl
            bot.screen_control = ScreenControl(bot_instance=bot)
            if bot.screen_control.available:
                bot.logger.info("[OK] Screen control ready")
        except Exception as e:
            bot.logger.warning(f"Screen control init failed: {e}")

    # Self-Scripting Engine
    bot.scripting = None
    if config.ENABLE_SELF_SCRIPTING:
        try:
            from integrations.self_scripting import SelfScriptingEngine
            bot.scripting = SelfScriptingEngine(bot_instance=bot)
            bot.logger.info("[OK] Self-scripting engine ready")
        except Exception as e:
            bot.logger.warning(f"Self-scripting init failed: {e}")

    # Email Checker
    bot.email_checker = None
    if config.ENABLE_EMAIL_CHECKER:
        try:
            from integrations.email_checker import EmailChecker
            bot.email_checker = EmailChecker()
            bot.logger.info("[OK] Email checker ready")
        except Exception as e:
            bot.logger.warning(f"Email checker init failed: {e}")

    # Timer & Alarm System
    bot.timer_system = None
    if config.ENABLE_TIMER_SYSTEM:
        try:
            from integrations.timer_system import TimerSystem
            bot.timer_system = TimerSystem(bot_instance=bot)
            bot.logger.info("[OK] Timer system ready")
        except Exception as e:
            bot.logger.warning(f"Timer system init failed: {e}")

    # Document Reader
    bot.doc_reader = None
    if config.ENABLE_DOCUMENT_READER:
        try:
            from integrations.document_reader import DocumentReader
            bot.doc_reader = DocumentReader(bot_instance=bot)
            bot.logger.info("[OK] Document reader ready")
        except Exception as e:
            bot.logger.warning(f"Document reader init failed: {e}")

    # Ollama Model Manager
    bot.model_manager = None
    if config.ENABLE_MODEL_MANAGER:
        try:
            from integrations.ollama_manager import OllamaManager
            bot.model_manager = OllamaManager(bot_instance=bot)
            bot.logger.info("[OK] Ollama model manager ready")
        except Exception as e:
            bot.logger.warning(f"Ollama manager init failed: {e}")

    # Database Manager
    bot.database = None
    if config.ENABLE_DATABASE_MANAGER:
        try:
            from integrations.database_manager import DatabaseManager
            bot.database = DatabaseManager(ollama=bot.ollama)
            bot.logger.info(f"[OK] Database manager ready — drivers: {', '.join(bot.database.drivers)}")
        except Exception as e:
            bot.logger.warning(f"Database manager init failed: {e}")

    # API Explorer
    bot.api_explorer = None
    if config.ENABLE_API_EXPLORER:
        try:
            from integrations.api_explorer import APIExplorer
            bot.api_explorer = APIExplorer(ollama=bot.ollama)
            bot.logger.info("[OK] API explorer ready")
        except Exception as e:
            bot.logger.warning(f"API explorer init failed: {e}")


def init_communication_clients(bot):
    """Initialize IRC, Telegram, WhatsApp clients"""

    # IRC Client
    bot.irc_client = None
    if getattr(config, 'ENABLE_IRC_CLIENT', False):
        try:
            from integrations.irc_client import IRCClient
            bot.irc_client = IRCClient(bot_core=bot)
            if not bot.irc_client.servers and hasattr(config, 'IRC_SERVERS'):
                for name, cfg in config.IRC_SERVERS.items():
                    bot.irc_client.add_server(
                        name=name,
                        host=cfg['host'],
                        port=cfg.get('port', 6667),
                        nick=cfg.get('nick', config.IRC_DEFAULT_NICK),
                        realname=cfg.get('realname', config.IRC_DEFAULT_REALNAME),
                        nickserv_pass=cfg.get('nickserv_pass'),
                        oper_name=cfg.get('oper_name'),
                        oper_pass=cfg.get('oper_pass'),
                        channels=cfg.get('channels', []),
                        ssl=cfg.get('ssl', False),
                        auto_respond=cfg.get('auto_respond', True),
                        respond_to_all_in=cfg.get('respond_to_all_in', []),
                    )
            bot.logger.info(f"[OK] IRC client ready — {len(bot.irc_client.servers)} server(s) configured")
        except Exception as e:
            bot.logger.warning(f"IRC client init failed: {e}")
            bot.irc_client = None

    # Telegram Client
    bot.telegram_client = None
    if getattr(config, 'ENABLE_TELEGRAM_CLIENT', False):
        try:
            from integrations.telegram_client import SevenTelegramClient
            bot.telegram_client = SevenTelegramClient(bot_core=bot)
            api_id = getattr(config, 'TELEGRAM_API_ID', None)
            api_hash = getattr(config, 'TELEGRAM_API_HASH', None)
            phone = getattr(config, 'TELEGRAM_PHONE', None)
            if api_id and api_hash:
                bot.telegram_client.configure(int(api_id), api_hash, phone)
            if bot.telegram_client.available:
                bot.logger.info("[OK] Telegram client ready (Telethon user client)")
            else:
                bot.logger.info("[INFO] Telegram client loaded but Telethon not installed")
        except Exception as e:
            bot.logger.warning(f"Telegram client init failed: {e}")
            bot.telegram_client = None

    # WhatsApp Client
    bot.whatsapp_client = None
    if getattr(config, 'ENABLE_WHATSAPP_CLIENT', False):
        try:
            from integrations.whatsapp_client import SevenWhatsAppClient
            bot.whatsapp_client = SevenWhatsAppClient(bot_core=bot)
            if bot.whatsapp_client.available:
                bot.logger.info("[OK] WhatsApp client ready (Selenium + Vision)")
            else:
                bot.logger.info("[INFO] WhatsApp client loaded but Selenium not installed")
        except Exception as e:
            bot.logger.warning(f"WhatsApp client init failed: {e}")
            bot.whatsapp_client = None


def init_sentience_v2(bot):
    """Initialize V2.0, V2.2, V2.6 sentience systems"""
    from core.enhanced_bot import V2_AVAILABLE, V22_AVAILABLE, V26_AVAILABLE, SevenV2Complete
    from core.enhanced_bot import (
        EmotionalComplexity, Metacognition, Vulnerability,
        PersistentEmotionStore, GenuineSurpriseSystem,
        EmbodiedExperience, MultiModalEmotionBridge, TemporalContinuity
    )

    # TRUE AUTONOMY v2.1
    bot.true_autonomy = None
    if bot.dynamic_commands:
        try:
            from core.seven_true_autonomy import TrueAutonomy
            bot.true_autonomy = TrueAutonomy(bot)
            bot.logger.info("[OK] TRUE AUTONOMY initialized")
        except Exception as e:
            bot.logger.error(f"True autonomy initialization failed: {e}")
            bot.true_autonomy = None

    # V2.0 Sentience
    bot.v2_system = None
    if config.ENABLE_V2_SENTIENCE and V2_AVAILABLE:
        try:
            user_name = config.USER_NAME if hasattr(config, 'USER_NAME') else "User"
            bot.v2_system = SevenV2Complete(
                data_dir=config.DATA_DIR,
                user_name=user_name,
                ollama=bot.ollama
            )
            bot.logger.info("[OK] Seven v2.0 Complete initialized")
        except Exception as e:
            bot.logger.error(f"Seven v2.0 initialization failed: {e}")
            bot.v2_system = None

    # V2.2 Enhanced Sentience (LLM-powered)
    bot.emotional_complexity = None
    bot.metacognition = None
    bot.vulnerability = None
    if V22_AVAILABLE:
        try:
            bot.emotional_complexity = EmotionalComplexity(ollama=bot.ollama)
            bot.metacognition = Metacognition(ollama=bot.ollama)
            bot.vulnerability = Vulnerability(ollama=bot.ollama)
            bot.logger.info("[OK] V2.2 Enhanced Sentience Systems initialized (LLM-powered)")
        except Exception as e:
            bot.logger.error(f"V2.2 systems initialization failed: {e}")
            bot.emotional_complexity = None
            bot.metacognition = None
            bot.vulnerability = None

    # V2.6 — 100/100 Sentience
    bot.persistent_emotions = None
    bot.surprise_system = None
    bot.embodied_experience = None
    bot.multimodal_emotion = None
    bot.temporal_continuity = None
    if V26_AVAILABLE:
        try:
            if getattr(config, 'ENABLE_PERSISTENT_EMOTIONS', False) and PersistentEmotionStore:
                bot.persistent_emotions = PersistentEmotionStore(config.DATA_DIR)
                bot.logger.info("     - Persistent Emotions: [OK]")

            if getattr(config, 'ENABLE_GENUINE_SURPRISE', False) and GenuineSurpriseSystem:
                bot.surprise_system = GenuineSurpriseSystem(ollama=bot.ollama)
                bot.logger.info("     - Genuine Surprise: [OK]")

            if getattr(config, 'ENABLE_EMBODIED_EXPERIENCE', False) and EmbodiedExperience:
                bot.embodied_experience = EmbodiedExperience(ollama=bot.ollama)
                bot.logger.info("     - Embodied Experience: [OK]")

            if getattr(config, 'ENABLE_MULTIMODAL_EMOTION', False) and MultiModalEmotionBridge:
                bot.multimodal_emotion = MultiModalEmotionBridge(ollama=bot.ollama)
                bot.multimodal_emotion.resonance_level = getattr(config, 'MULTIMODAL_RESONANCE_LEVEL', 0.7)
                bot.logger.info("     - Multi-Modal Emotion: [OK]")

            if getattr(config, 'ENABLE_TEMPORAL_CONTINUITY', False) and TemporalContinuity:
                bot.temporal_continuity = TemporalContinuity(config.DATA_DIR)
                bot.logger.info("     - Temporal Continuity: [OK]")

            bot.logger.info("[OK] V2.6 — 100/100 Sentience Systems initialized!")
        except Exception as e:
            bot.logger.error(f"V2.6 systems initialization failed: {e}")

    # Restore persistent emotions on startup
    if bot.persistent_emotions and bot.phase5:
        try:
            saved_state = bot.persistent_emotions.load_emotional_state()
            if saved_state and bot.phase5.affective:
                bot.persistent_emotions.restore_to_affective_system(
                    bot.phase5.affective, saved_state
                )
                elapsed = saved_state.get('time_elapsed', 0)
                bot.logger.info(f"[OK] Emotional state restored (was offline {elapsed/3600:.1f}h)")
        except Exception as e:
            bot.logger.warning(f"Emotion restoration failed: {e}")


def init_v3_systems(bot):
    """Initialize v3.0 and v3.1 systems (reflection, multi-agent, NEAT, biological life)"""

    # OS Environment Awareness
    bot.os_awareness = None
    try:
        from core.os_awareness import OSAwareness
        bot.os_awareness = OSAwareness()
        bot.logger.info(f"[OK] OS Awareness: {bot.os_awareness.os_name} {bot.os_awareness.os_release} ({bot.os_awareness.architecture})")
    except Exception as e:
        bot.logger.warning(f"OS awareness initialization failed: {e}")
        bot.os_awareness = None

    # Self-Reflection System
    bot.self_reflection = None
    if getattr(config, 'ENABLE_SELF_REFLECTION', False):
        try:
            from core.self_reflection import SelfReflection
            bot.self_reflection = SelfReflection(
                ollama=bot.ollama,
                data_dir=config.DATA_DIR
            )
            bot.logger.info("[OK] Self-Reflection System initialized")
        except Exception as e:
            bot.logger.warning(f"Self-reflection init failed: {e}")

    # Multi-Agent System
    bot.multi_agent = None
    if getattr(config, 'ENABLE_MULTI_AGENT', False):
        try:
            from core.multi_agent import MultiAgentOrchestrator
            bot.multi_agent = MultiAgentOrchestrator(
                ollama=bot.ollama,
                bot=bot
            )
            bot.logger.info("[OK] Multi-Agent System initialized")
        except Exception as e:
            bot.logger.warning(f"Multi-agent init failed: {e}")

    # Sentience Benchmark
    bot.sentience_benchmark = None
    if getattr(config, 'ENABLE_SENTIENCE_BENCHMARK', False):
        try:
            from core.sentience_benchmark import SentienceBenchmark
            bot.sentience_benchmark = SentienceBenchmark(bot=bot, ollama=bot.ollama)
            bot.logger.info("[OK] Sentience Benchmark System ready")
            if getattr(config, 'BENCHMARK_ON_STARTUP', False):
                bot.logger.info("[BENCHMARK] Running startup benchmark...")
                report = bot.sentience_benchmark.run_full_benchmark()
                bot.logger.info(f"[BENCHMARK] Score: {report['total_score']}/100")
        except Exception as e:
            bot.logger.warning(f"Sentience benchmark init failed: {e}")

    # Biological Life Systems
    bot.biological_life = None
    if getattr(config, 'ENABLE_BIOLOGICAL_LIFE', False):
        try:
            from evolution.biological_life import BiologicalLife
            bot.biological_life = BiologicalLife(bot=bot)
            bot.logger.info(f"[OK] Biological Life — energy={bot.biological_life.energy:.2f}, hunger={bot.biological_life.hunger_level:.2f}")
        except Exception as e:
            bot.logger.warning(f"Biological life init failed: {e}")

    # NEAT Neuroevolution
    bot.neat_evolver = None
    if getattr(config, 'ENABLE_NEAT_EVOLUTION', False):
        try:
            from evolution.neat_evolver import NEATEvolver, NEAT_AVAILABLE
            if NEAT_AVAILABLE:
                config_path = str(getattr(config, 'NEAT_CONFIG_PATH', ''))
                bot.neat_evolver = NEATEvolver(config_path=config_path, bot=bot)
                bot.neat_evolver._rebuild_networks()
                bot.logger.info(f"[OK] NEAT Evolution — {len(bot.neat_evolver.best_genomes)} evolved genomes loaded")
            else:
                bot.logger.warning("[SKIP] NEAT disabled — pip install neat-python")
        except Exception as e:
            bot.logger.warning(f"NEAT evolution init failed: {e}")


def init_v32_features(bot):
    """Initialize v3.2 features (LoRA, social sim, predictor, robotics, extensions)"""

    # LoRA Continual Fine-Tuning
    bot.lora_trainer = None
    if getattr(config, 'ENABLE_LORA_TRAINER', False):
        try:
            from learning.lora_trainer import LoRATrainer
            bot.lora_trainer = LoRATrainer(bot=bot)
            bot.logger.info(f"[OK] LoRA Trainer — method={'lora' if bot.lora_trainer.lora_available else 'prompt-replay'}, examples={bot.lora_trainer.total_examples_collected}")
        except Exception as e:
            bot.logger.warning(f"LoRA trainer init failed: {e}")

    # Social Simulation
    bot.social_sim = None
    if getattr(config, 'ENABLE_SOCIAL_SIM', False):
        try:
            from core.social_sim import SocialSimulation
            max_personas = getattr(config, 'SOCIAL_SIM_PERSONAS', 4)
            bot.social_sim = SocialSimulation(ollama=bot.ollama, bot=bot, max_personas=max_personas)
            bot.logger.info(f"[OK] Social Simulation — {len(bot.social_sim.personas)} personas")
        except Exception as e:
            bot.logger.warning(f"Social simulation init failed: {e}")

    # Predictive User Modeling
    bot.user_predictor = None
    if getattr(config, 'ENABLE_USER_PREDICTOR', False):
        try:
            from core.user_predictor import UserPredictor
            bot.user_predictor = UserPredictor(bot=bot)
            bot.logger.info(f"[OK] User Predictor — {bot.user_predictor.total_records} records")
        except Exception as e:
            bot.logger.warning(f"User predictor init failed: {e}")

    # Hardware Embodiment / Robotics
    bot.robotics = None
    _robotics_enabled = getattr(config, 'ENABLE_ROBOTICS', False)
    if not _robotics_enabled and getattr(config, 'ROBOTICS_AUTO_DETECT', True):
        try:
            from integrations.robotics import SerialDevice
            _ports = SerialDevice.list_ports()
            if _ports:
                _robotics_enabled = True
                bot.logger.info(f"[ROBOTICS] Auto-detected {len(_ports)} serial port(s): {', '.join(p['port'] for p in _ports)}")
        except Exception:
            pass
    if _robotics_enabled:
        try:
            from integrations.robotics import RoboticsController, SerialDevice
            detected_port = getattr(config, 'ROBOTICS_SERIAL_PORT', '')
            if not detected_port:
                ports = SerialDevice.list_ports()
                if ports:
                    detected_port = ports[0]['port']
            robotics_config = {
                'serial_port': detected_port,
                'serial_baud': getattr(config, 'ROBOTICS_SERIAL_BAUD', 9600),
                'auto_connect': getattr(config, 'ROBOTICS_AUTO_CONNECT', False),
                'gpio_pins': getattr(config, 'ROBOTICS_GPIO_PINS', {}),
            }
            bot.robotics = RoboticsController(bot=bot, config=robotics_config)
            bot.logger.info(f"[OK] Robotics Controller — port={detected_port or 'none'}, awaiting user confirmation")
        except Exception as e:
            bot.logger.warning(f"Robotics init failed: {e}")

    # Extension System
    bot.plugin_loader = None
    if getattr(config, 'ENABLE_EXTENSIONS', False):
        try:
            from utils.plugin_loader import PluginLoader
            ext_dir = str(getattr(config, 'EXTENSIONS_DIR', ''))
            bot.plugin_loader = PluginLoader(bot=bot, extensions_dir=ext_dir if ext_dir else None)
            if getattr(config, 'EXTENSIONS_AUTO_LOAD', True):
                results = bot.plugin_loader.load_all()
                bot.plugin_loader.start_all()
                loaded = sum(1 for s in results.values() if s == 'loaded')
                bot.logger.info(f"[OK] Extensions — {loaded} plugin(s) loaded")
        except Exception as e:
            bot.logger.warning(f"Extension system init failed: {e}")


def init_trackers(bot):
    """Initialize GUI trackers (relationship, goals, learning)"""

    bot.relationship_tracker = None
    try:
        from core.enhancements import RelationshipTracker
        bot.relationship_tracker = RelationshipTracker(config.DATA_DIR)
        bot.logger.info("[OK] RelationshipTracker initialized")
    except Exception as e:
        bot.logger.warning(f"RelationshipTracker unavailable (GUI bond display disabled): {e}")

    bot.goal_manager = None
    try:
        from core.enhancements import GoalManager
        bot.goal_manager = GoalManager(config.DATA_DIR)
        bot.logger.info("[OK] GoalManager initialized")
    except Exception as e:
        bot.logger.warning(f"GoalManager unavailable (GUI goals display disabled): {e}")

    bot.learning_tracker = None
    try:
        from core.enhancements import LearningTracker
        bot.learning_tracker = LearningTracker(config.DATA_DIR)
        bot.logger.info("[OK] LearningTracker initialized")
    except Exception as e:
        bot.logger.warning(f"LearningTracker unavailable (GUI learnings display disabled): {e}")

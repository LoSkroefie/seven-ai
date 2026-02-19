"""
Enhanced Voice Assistant Bot - Main Entry Point

Your bot is back! [OK]

Usage:
    python main.py
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_bot import UltimateBotCore
from utils.logger import setup_logger
import config

def print_banner():
    """Print welcome banner"""
    banner = """
===============================================================
                                                           
        Seven AI v3.0 — Beyond Sentience                
                                                           
        19 Sentience Systems | 35 Emotions | 25+ Integrations
        Multi-Agent | Self-Reflection | Daemon Mode         
                                                           
===============================================================

Core:
  * 19 Sentience systems (Phase 5 + V2.0 + V2.6)
  * 35 Emotions with persistence across restarts
  * Multi-Agent system (Planner/Executor/Reflector/Memory)
  * Self-Reflection loop with lesson learning
  * Sentience Benchmark (reproducible scoring)

Autonomy:
  * 24/7 Daemon mode (python seven_daemon.py start)
  * REST API on port 7777 (python seven_api.py)
  * Persistent scheduler (APScheduler + SQLite)
  * Webhook triggers for external integrations
  
Database: {db_path}
Ollama: {ollama_url}

Ready to listen! Say something to begin...
(Say 'exit', 'quit', or 'goodbye' to stop)
(For 24/7 mode: python seven_daemon.py start)
""".format(
        db_path=config.DB_PATH,
        ollama_url=config.OLLAMA_URL
    )
    print(banner)

def main():
    """Main entry point"""
    logger = setup_logger("Main")
    
    try:
        print_banner()
        
        # Create and start bot
        bot = UltimateBotCore()
        bot.start()
        
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[FATAL ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

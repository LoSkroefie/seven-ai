"""
Enhanced Voice Assistant Bot - Main Entry Point WITH GUI
Launches both bot and GUI control panel
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_bot import UltimateBotCore
from gui.bot_gui import launch_gui
from utils.logger import setup_logger
import config

def print_banner():
    """Print welcome banner"""
    banner = """
===============================================================
                                                           
        Enhanced Voice Assistant Bot + GUI                    
                                                           
        Your bot is back and better than ever!            
                                                           
===============================================================

Features:
  * 20+ Emotional states with voice modulation
  * Ollama/Llama 3.2 integration for intelligence
  * SQLite memory (no more exposed credentials!)
  * Speech recognition + Text-to-speech
  * Safe system command execution
  * Google Calendar integration
  * Web search capabilities
  * GUI Control Panel for settings and monitoring
  
Database: {db_path}
Ollama: {ollama_url}

GUI will open in a separate window...
Ready to listen! Say something to begin...
(Say 'exit', 'quit', or 'goodbye' to stop)
""".format(
        db_path=config.DB_PATH,
        ollama_url=config.OLLAMA_URL
    )
    print(banner)

def main():
    """Main entry point with GUI"""
    logger = setup_logger("Main")
    
    try:
        print_banner()
        
        # Create bot
        bot = UltimateBotCore()
        
        # Launch GUI in separate thread
        gui = launch_gui(bot)
        bot.gui = gui  # Wire GUI reference so bot can push conversation updates
        gui.run_async()
        
        logger.info("GUI launched in background")
        gui.add_message('system', text="Bot starting...")
        
        # Start bot (blocking)
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

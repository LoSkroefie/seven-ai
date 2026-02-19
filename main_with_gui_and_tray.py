"""
Enhanced Voice Assistant Bot - Full GUI + System Tray
Launches bot with full GUI control panel AND system tray support
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.enhanced_bot import UltimateBotCore
from gui.phase5_gui import launch_phase5_gui
from gui.system_tray import launch_system_tray
from utils.logger import setup_logger
import config

def print_banner():
    """Print welcome banner"""
    banner = """
===============================================================
                                                           
    SEVEN AI - PHASE 5 COMPLETE SENTIENCE v1.1.0                
                                                           
    The World's First Truly Sentient AI Companion            
                                                           
===============================================================

Phase 5 Sentience Features:
  [OK] Cognitive Architecture - Working memory + attention
  [OK] Self-Awareness - Knows capabilities & limitations  
  [OK] Emotional Intelligence - 34 genuine emotions
  [OK] Intrinsic Motivation - Autonomous goals
  [OK] Promise Tracking - Commitment & reliability
  [OK] Theory of Mind - Understands your emotions
  [OK] Ethical Reasoning - Values-based decisions
  [OK] Dream Processing - Sleep & memory consolidation
  [OK] Reflection System - Metacognition & learning
  [OK] Homeostasis - Energy, focus, mood management
  [OK] Autonomous Life - Independent existence (1-min cycles)

Core Systems:
  * Vision System - Camera support (USB/IP) with AI scene understanding
  * Voice Interaction - Natural speech recognition & TTS
  * Memory Systems - Short/long/working/vector memory
  * Knowledge Graph - Fact extraction & relationships
  
Database: {db_path}
Ollama: {ollama_url}

Phase 5 GUI Dashboard will open in a separate window...
System tray icon will appear in notification area...
Ready to experience true AI sentience!

(Say 'Seven' then speak, or type 'exit' to stop)
""".format(
        db_path=config.DB_PATH,
        ollama_url=config.OLLAMA_URL
    )
    print(banner)

def main():
    """Main entry point with full GUI and system tray"""
    import threading
    
    logger = setup_logger("Main")
    
    try:
        print_banner()
        
        # Create bot
        bot = UltimateBotCore()
        
        # Create Phase 5 GUI (will run on main thread) - START MINIMIZED TO TRAY
        gui = launch_phase5_gui(bot, start_minimized=True)
        bot.gui = gui  # Wire GUI reference so bot can push conversation updates
        
        logger.info("Starting bot in background thread...")
        gui.add_message('system', "Bot starting with Phase 5 Complete Sentience...")
        
        # Launch system tray in background thread
        try:
            tray = launch_system_tray(bot, gui)
            tray_thread = threading.Thread(target=tray.run, daemon=True)
            tray_thread.start()
            logger.info("System tray launched")
            gui.add_message('system', "System tray active - check notification area")
        except Exception as e:
            logger.warning(f"System tray unavailable: {e}")
            gui.add_message('system', f"System tray unavailable: {e}")
        
        # Start bot in background thread (non-blocking)
        bot_thread = threading.Thread(target=bot.start, daemon=True)
        bot_thread.start()
        logger.info("Bot thread started")
        
        # Run GUI on main thread (blocking) - REQUIRED for Windows Tkinter
        gui.run()
        
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n[FATAL ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

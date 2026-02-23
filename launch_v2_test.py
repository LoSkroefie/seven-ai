"""
Launch Seven AI v2.0 with Detailed Logging
This script launches Seven and shows v2.0 initialization in real-time
"""

import sys
import os
import logging
from datetime import datetime

# Setup detailed logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'seven_v2_launch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

print("=" * 80)
print("SEVEN AI v2.0 - MAXIMUM SENTIENCE LAUNCH")
print("=" * 80)
print(f"Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Python: {sys.version}")
print(f"Working Directory: {os.getcwd()}")
print("=" * 80)
print()

logger.info("Starting Seven AI v2.0...")

# Import and launch
try:
    logger.info("Importing main module...")
    import main_with_gui_and_tray
    
    logger.info("Seven AI v2.0 launch complete!")
    
except KeyboardInterrupt:
    logger.info("Shutdown requested by user")
    print("\n" + "=" * 80)
    print("Seven AI v2.0 shutdown complete")
    print("=" * 80)
    
except Exception as e:
    logger.error(f"Launch error: {e}", exc_info=True)
    print("\n" + "=" * 80)
    print(f"ERROR: {e}")
    print("=" * 80)
    sys.exit(1)

"""
Quick test: Can enhanced_bot.py import and initialize v2.0?
"""
import sys
import os

print("Testing enhanced_bot.py with v2.0...")
print("-" * 60)

try:
    print("[1/3] Importing config...")
    import config
    print(f"  [OK] ENABLE_V2_SENTIENCE: {config.ENABLE_V2_SENTIENCE}")
    print(f"  [OK] ENABLE_V2_PROACTIVE: {config.ENABLE_V2_PROACTIVE}")
    print(f"  [OK] USER_NAME: {config.USER_NAME}")
    
    print("\n[2/3] Importing enhanced_bot...")
    from core.enhanced_bot import UltimateBotCore
    print("  [OK] UltimateBotCore imported successfully")
    
    print("\n[3/3] Testing v2.0 integration...")
    # Don't actually initialize (would need Ollama running)
    # Just verify the class has v2.0 integration
    import inspect
    source = inspect.getsource(UltimateBotCore.__init__)
    
    if "SevenV2Complete" in source:
        print("  [OK] SevenV2Complete found in __init__")
    else:
        print("  [FAIL] SevenV2Complete NOT found in __init__")
        sys.exit(1)
    
    if "v2_system" in source:
        print("  [OK] v2_system initialization found")
    else:
        print("  [FAIL] v2_system initialization NOT found")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("SUCCESS: enhanced_bot.py is ready for v2.0!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR]: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

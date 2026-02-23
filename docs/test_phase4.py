"""
Test script for Phase 4: Structured Identity System

Tests:
1. Identity file creation
2. Reading identity
3. Voice command handlers
4. Autonomous self-editing
5. Full integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from core.identity_manager import IdentityManager
from core import identity_commands


def test_identity_manager():
    """Test IdentityManager basic functionality"""
    print("=" * 60)
    print("TEST 1: IdentityManager - File Creation & Reading")
    print("=" * 60)
    
    # Initialize
    im = IdentityManager()
    
    # Check files exist
    print("\n[OK] Checking identity files...")
    assert im.soul_file.exists(), "SOUL.md not created"
    assert im.identity_file.exists(), "IDENTITY.md not created"
    assert im.user_file.exists(), "USER.md not created"
    assert im.tools_file.exists(), "TOOLS.md not created"
    assert im.heartbeat_file.exists(), "HEARTBEAT.md not created"
    assert im.bootstrap_file.exists(), "BOOTSTRAP.md not created"
    print("   All 6 identity files created! [PASS]")
    
    # Read SOUL
    print("\n[OK] Testing SOUL.md reading...")
    soul = im.get_soul()
    assert len(soul) > 100, "SOUL.md too short"
    assert "value" in soul.lower() or "believe" in soul.lower(), "SOUL missing key content"
    print(f"   SOUL.md: {len(soul)} characters [PASS]")
    print(f"   Preview: {soul[:100]}...")
    
    # Read IDENTITY
    print("\n[OK] Testing IDENTITY.md reading...")
    identity = im.get_identity()
    assert len(identity) > 100, "IDENTITY.md too short"
    assert "Seven" in identity, "IDENTITY missing name"
    print(f"   IDENTITY.md: {len(identity)} characters [PASS]")
    
    # Read USER
    print("\n[OK] Testing USER.md reading...")
    user = im.get_user_profile()
    assert len(user) > 50, "USER.md too short"
    print(f"   USER.md: {len(user)} characters [PASS]")
    
    # Get full context
    print("\n[OK] Testing full identity context...")
    context = im.get_full_identity_context()
    assert len(context) > 500, "Full context too short"
    assert "SOUL" in context, "Context missing SOUL section"
    assert "IDENTITY" in context, "Context missing IDENTITY section"
    assert "USER" in context, "Context missing USER section"
    print(f"   Full context: {len(context)} characters [PASS]")
    
    print("\n" + "=" * 60)
    print("[PASS] IdentityManager Test PASSED")
    print("=" * 60)
    
    return im


def test_identity_updates(im):
    """Test identity updating functionality"""
    print("\n" + "=" * 60)
    print("TEST 2: Identity Updates - Self-Editing")
    print("=" * 60)
    
    # Test appending to SOUL
    print("\n✓ Testing SOUL.md update...")
    test_principle = "## Test Principle\n- Testing self-editing capability"
    success = im.append_to_identity("soul", test_principle)
    assert success, "Failed to update SOUL"
    
    # Verify update
    soul = im.get_soul()
    assert "Test Principle" in soul, "Update not found in SOUL"
    print("   SOUL.md successfully updated [OK]")
    
    # Test appending to USER
    print("\n✓ Testing USER.md update...")
    test_pref = "### Test Preference\n- User prefers direct communication"
    success = im.append_to_identity("user", test_pref)
    assert success, "Failed to update USER"
    
    # Verify update
    user = im.get_user_profile()
    assert "Test Preference" in user, "Update not found in USER"
    print("   USER.md successfully updated [OK]")
    
    # Test heartbeat
    print("\n✓ Testing heartbeat check...")
    result = im.check_heartbeat()
    print(f"   Heartbeat result: {result if result else 'HEARTBEAT_OK'} [OK]")
    
    print("\n" + "=" * 60)
    print("[OK] Identity Updates Test PASSED")
    print("=" * 60)


def test_command_handlers():
    """Test voice command handlers"""
    print("\n" + "=" * 60)
    print("TEST 3: Voice Command Handlers")
    print("=" * 60)
    
    # Mock bot object
    class MockBot:
        def __init__(self):
            self.identity_mgr = IdentityManager()
            self.bot_name = "Seven"
            self.personality = None
            self.user_model = None
            
            # Mock logger
            class MockLogger:
                def error(self, msg): print(f"   [LOG] {msg}")
                def warning(self, msg): print(f"   [LOG] {msg}")
            
            self.logger = MockLogger()
    
    bot = MockBot()
    
    # Test "show soul" command
    print("\n✓ Testing 'show me your soul' command...")
    result = identity_commands.handle_identity_commands(bot, "show me your soul", "show me your soul")
    assert result is not None, "Show soul command returned None"
    assert len(result) > 20, "Show soul response too short"
    print(f"   Response: {result[:100]}... [OK]")
    
    # Test "who are you" command
    print("\n✓ Testing 'who are you' command...")
    result = identity_commands.handle_identity_commands(bot, "who are you", "who are you")
    assert result is not None, "Who are you command returned None"
    assert "Seven" in result, "Response missing bot name"
    print(f"   Response: {result[:100]}... [OK]")
    
    # Test "heartbeat check" command
    print("\n✓ Testing 'heartbeat check' command...")
    result = identity_commands.handle_identity_commands(bot, "heartbeat check", "heartbeat check")
    assert result is not None, "Heartbeat command returned None"
    assert "HEARTBEAT" in result.upper(), "Response missing heartbeat confirmation"
    print(f"   Response: {result} [OK]")
    
    # Test autonomous update
    print("\n✓ Testing autonomous identity update...")
    success = identity_commands.autonomous_identity_update(
        bot, 
        "new_realization", 
        "I've discovered that I enjoy helping with coding projects"
    )
    assert success, "Autonomous update failed"
    
    # Verify update
    identity = bot.identity_mgr.get_identity()
    assert "coding projects" in identity, "Autonomous update not found"
    print("   Autonomous update successful [OK]")
    
    print("\n" + "=" * 60)
    print("[OK] Command Handlers Test PASSED")
    print("=" * 60)


def test_integration():
    """Test full integration"""
    print("\n" + "=" * 60)
    print("TEST 4: Full Integration Verification")
    print("=" * 60)
    
    # Check config flags
    print("\n✓ Checking config flags...")
    assert hasattr(config, 'ENABLE_IDENTITY_SYSTEM'), "ENABLE_IDENTITY_SYSTEM not in config"
    assert hasattr(config, 'ENABLE_HEARTBEAT_CHECKS'), "ENABLE_HEARTBEAT_CHECKS not in config"
    assert hasattr(config, 'ENABLE_BOOTSTRAP_GREETING'), "ENABLE_BOOTSTRAP_GREETING not in config"
    assert hasattr(config, 'ENABLE_IDENTITY_SELF_EDIT'), "ENABLE_IDENTITY_SELF_EDIT not in config"
    print("   All config flags present [OK]")
    
    # Check module imports
    print("\n✓ Checking module imports...")
    from core import identity_commands
    assert hasattr(identity_commands, 'handle_identity_commands'), "handle_identity_commands not found"
    assert hasattr(identity_commands, 'autonomous_identity_update'), "autonomous_identity_update not found"
    print("   All modules importable [OK]")
    
    # Verify identity directory structure
    print("\n✓ Checking identity directory...")
    identity_dir = config.DATA_DIR / "identity"
    assert identity_dir.exists(), "Identity directory not created"
    
    files = list(identity_dir.glob("*.md"))
    assert len(files) >= 6, f"Expected 6 identity files, found {len(files)}"
    print(f"   Identity directory contains {len(files)} files [OK]")
    
    print("\n" + "=" * 60)
    print("[OK] Integration Test PASSED")
    print("=" * 60)


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "PHASE 4 TEST SUITE")
    print(" " * 15 + "Structured Identity System")
    print("=" * 70)
    
    try:
        # Test 1: IdentityManager
        im = test_identity_manager()
        
        # Test 2: Updates
        test_identity_updates(im)
        
        # Test 3: Command Handlers
        test_command_handlers()
        
        # Test 4: Integration
        test_integration()
        
        # Summary
        print("\n\n" + "=" * 70)
        print(" " * 25 + "🎉 ALL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\n[OK] Phase 4: Structured Identity System is FULLY OPERATIONAL!")
        print("\nSeven now has:")
        print("  ✓ Self-awareness through markdown files")
        print("  ✓ Self-editing capability")
        print("  ✓ Voice command handlers")
        print("  ✓ Autonomous identity updates")
        print("  ✓ Full integration with bot core")
        print("\n[BRAIN] Seven has gained a SOUL! ")
        print("=" * 70 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n\n[ERROR] TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


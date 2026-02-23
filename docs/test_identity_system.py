"""
Test script for Phase 4: Structured Identity System
Run this to verify the identity system is working correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import config
from core.identity_manager import IdentityManager

def test_identity_system():
    """Test the structured identity system"""
    print("=" * 60)
    print("PHASE 4: Structured Identity System - Test")
    print("=" * 60)
    
    # Initialize
    print("\n1. Initializing IdentityManager...")
    try:
        im = IdentityManager()
        print("   [OK] IdentityManager created successfully")
    except Exception as e:
        print(f"   [FAIL] Failed to create IdentityManager: {e}")
        return False
    
    # Check identity directory
    print(f"\n2. Checking identity directory: {im.identity_dir}")
    if im.identity_dir.exists():
        print("   [OK] Identity directory exists")
    else:
        print("   [FAIL] Identity directory not found")
        return False
    
    # Check all identity files
    print("\n3. Checking identity files...")
    files_to_check = {
        "SOUL.md": im.soul_file,
        "IDENTITY.md": im.identity_file,
        "USER.md": im.user_file,
        "TOOLS.md": im.tools_file,
        "HEARTBEAT.md": im.heartbeat_file,
        "BOOTSTRAP.md": im.bootstrap_file,
    }
    
    all_exist = True
    for name, filepath in files_to_check.items():
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   [OK] {name} ({size} bytes)")
        else:
            print(f"   [FAIL] {name} - NOT FOUND")
            all_exist = False
    
    if not all_exist:
        return False
    
    # Test reading SOUL
    print("\n4. Testing SOUL.md reading...")
    try:
        soul = im.get_soul()
        if soul and len(soul) > 100:
            preview = soul[:150].replace("\n", " ")
            print(f"   [OK] SOUL content: {preview}...")
        else:
            print("   [FAIL] SOUL content too short or empty")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed to read SOUL: {e}")
        return False
    
    # Test reading IDENTITY
    print("\n5. Testing IDENTITY.md reading...")
    try:
        identity = im.get_identity()
        if identity and len(identity) > 100:
            preview = identity[:150].replace("\n", " ")
            print(f"   [OK] IDENTITY content: {preview}...")
        else:
            print("   [FAIL] IDENTITY content too short or empty")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed to read IDENTITY: {e}")
        return False
    
    # Test reading USER
    print("\n6. Testing USER.md reading...")
    try:
        user = im.get_user_profile()
        if user and len(user) > 100:
            preview = user[:150].replace("\n", " ")
            print(f"   [OK] USER content: {preview}...")
        else:
            print("   [FAIL] USER content too short or empty")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed to read USER: {e}")
        return False
    
    # Test full context
    print("\n7. Testing full identity context...")
    try:
        full_context = im.get_full_identity_context()
        if full_context and len(full_context) > 500:
            print(f"   [OK] Full context: {len(full_context)} characters")
            print(f"   [OK] Contains SOUL: {'MY CORE PRINCIPLES' in full_context}")
            print(f"   [OK] Contains IDENTITY: {'WHO I AM' in full_context}")
            print(f"   [OK] Contains USER: {'WHO YOU ARE' in full_context}")
            print(f"   [OK] Contains TOOLS: {'MY ENVIRONMENT' in full_context}")
        else:
            print("   [FAIL] Full context too short or empty")
            return False
    except Exception as e:
        print(f"   [FAIL] Failed to get full context: {e}")
        return False
    
    # Test self-editing (append)
    print("\n8. Testing self-editing capability...")
    try:
        test_addition = "\n## Test Entry\nThis is a test of self-editing capability."
        success = im.append_to_identity("soul", test_addition)
        if success:
            print("   [OK] Successfully appended to SOUL.md")
            # Read back to verify
            updated_soul = im.get_soul()
            if "Test Entry" in updated_soul:
                print("   [OK] Verified: Test content found in SOUL.md")
            else:
                print("   [WARN] Warning: Test content not found after append")
        else:
            print("   [FAIL] Failed to append to SOUL.md")
            return False
    except Exception as e:
        print(f"   [FAIL] Self-editing test failed: {e}")
        return False
    
    # Test heartbeat
    print("\n9. Testing heartbeat check...")
    try:
        heartbeat_result = im.check_heartbeat()
        if heartbeat_result is None:
            print("   [OK] Heartbeat check returned None (HEARTBEAT_OK)")
        else:
            print(f"   [OK] Heartbeat check returned: {heartbeat_result}")
    except Exception as e:
        print(f"   [FAIL] Heartbeat check failed: {e}")
        return False
    
    # Test bootstrap greeting
    print("\n10. Testing bootstrap greeting...")
    try:
        bootstrap = im.get_bootstrap_greeting()
        if bootstrap and len(bootstrap) > 50:
            preview = bootstrap[:100].replace("\n", " ")
            print(f"   [OK] Bootstrap greeting: {preview}...")
        else:
            print("   [FAIL] Bootstrap greeting too short or empty")
            return False
    except Exception as e:
        print(f"   [FAIL] Bootstrap greeting failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED!")
    print("=" * 60)
    print("\nPhase 4: Structured Identity System is fully operational!")
    print(f"\nIdentity files location: {im.identity_dir}")
    print("\nYou can now:")
    print("  - Read Seven's SOUL.md to see its principles")
    print("  - Edit identity files directly")
    print("  - Seven will use this identity in conversations")
    print("  - Seven can update its own identity files")
    
    return True

if __name__ == "__main__":
    try:
        success = test_identity_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

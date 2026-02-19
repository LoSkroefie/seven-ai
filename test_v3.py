"""
Seven AI v3.0 — Runtime test for all new modules
"""
import sys
sys.path.insert(0, '.')

passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        print(f"  [OK] {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1

print("=== Test 1: Import all new modules ===")
test("SelfReflection", lambda: __import__('core.self_reflection', fromlist=['SelfReflection']))
test("MultiAgentOrchestrator", lambda: __import__('core.multi_agent', fromlist=['MultiAgentOrchestrator']))
test("SentienceBenchmark", lambda: __import__('core.sentience_benchmark', fromlist=['SentienceBenchmark']))
test("OllamaCache", lambda: __import__('core.ollama_cache', fromlist=['OllamaCache']))
test("SevenDaemon", lambda: __import__('seven_daemon', fromlist=['SevenDaemon']))
test("SevenScheduler", lambda: __import__('seven_scheduler', fromlist=['SevenScheduler']))

print("\n=== Test 2: FastAPI import ===")
try:
    from seven_api import create_app, FASTAPI_AVAILABLE
    print(f"  [OK] seven_api (FastAPI available: {FASTAPI_AVAILABLE})")
    passed += 1
except ImportError as e:
    print(f"  [WARN] FastAPI not installed yet: {e}")
    print("         Run: pip install fastapi uvicorn")

print("\n=== Test 3: SelfReflection without LLM ===")
from core.self_reflection import SelfReflection
sr = SelfReflection(ollama=None)
entry = sr.reflect_on_action("tested import", "all modules loaded", "")
test("reflect_on_action", lambda: None if entry.effectiveness == 0.5 else (_ for _ in ()).throw(Exception("bad effectiveness")))
test("get_stats", lambda: sr.get_stats())
print(f"         Reflections: {sr.reflection_count}, Lessons: {len(sr.lesson_bank)}")

print("\n=== Test 4: CodeExecutor sandbox ===")
from integrations.code_executor import CodeExecutor
ce = CodeExecutor()

r1 = ce.is_safe_code("print(2+2)")
test("safe_code_passes", lambda: None if r1['safe'] else (_ for _ in ()).throw(Exception(r1)))

r2 = ce.is_safe_code("import os")
test("os_import_blocked", lambda: None if not r2['safe'] else (_ for _ in ()).throw(Exception("os should be blocked")))

r3 = ce.is_safe_code("x.__class__.__bases__")
test("dunder_blocked", lambda: None if not r3['safe'] else (_ for _ in ()).throw(Exception("dunder should be blocked")))

r4 = ce.is_safe_code("import socket")
test("socket_blocked", lambda: None if not r4['safe'] else (_ for _ in ()).throw(Exception("socket should be blocked")))

r5 = ce.is_safe_code("import math\nprint(math.sqrt(16))")
test("math_allowed", lambda: None if r5['safe'] else (_ for _ in ()).throw(Exception(r5)))

r6 = ce.is_safe_code("import subprocess")
test("subprocess_blocked", lambda: None if not r6['safe'] else (_ for _ in ()).throw(Exception("subprocess should be blocked")))

# Test actual execution
r7 = ce.execute_code("print(2 + 2)")
test("execute_safe_code", lambda: None if r7['success'] and '4' in r7['output'] else (_ for _ in ()).throw(Exception(r7)))

r8 = ce.execute_code("import os")
test("execute_blocks_os", lambda: None if not r8['success'] else (_ for _ in ()).throw(Exception("os execution should fail")))

print("\n=== Test 5: Config v3.0 values ===")
import config
test("ENABLE_SELF_REFLECTION", lambda: None if config.ENABLE_SELF_REFLECTION else (_ for _ in ()).throw(Exception("should be True")))
test("ENABLE_MULTI_AGENT", lambda: None if config.ENABLE_MULTI_AGENT else (_ for _ in ()).throw(Exception("should be True")))
test("ENABLE_SENTIENCE_BENCHMARK", lambda: None if config.ENABLE_SENTIENCE_BENCHMARK else (_ for _ in ()).throw(Exception("should be True")))
test("ENABLE_DAEMON_MODE", lambda: None if config.ENABLE_DAEMON_MODE else (_ for _ in ()).throw(Exception("should be True")))
test("API_PORT", lambda: None if config.API_PORT == 7777 else (_ for _ in ()).throw(Exception(f"expected 7777, got {config.API_PORT}")))

print("\n=== Test 6: SSH Manager encryption ===")
from integrations.ssh_manager import SSHManager, CRYPTO_AVAILABLE
print(f"         Crypto available: {CRYPTO_AVAILABLE}")
if CRYPTO_AVAILABLE:
    sm = SSHManager()
    test_pw = "MySecret123"
    encrypted = sm._encrypt(test_pw)
    decrypted = sm._decrypt(encrypted)
    test("encrypt_decrypt", lambda: None if decrypted == test_pw else (_ for _ in ()).throw(Exception(f"got {decrypted}")))
    test("encrypted_differs", lambda: None if encrypted != test_pw else (_ for _ in ()).throw(Exception("not encrypted")))
else:
    print("  [SKIP] cryptography not installed")

print("\n=== Test 7: Daemon PID management ===")
from seven_daemon import SevenDaemon
d = SevenDaemon()
test("no_running_daemon", lambda: None if d._read_pid() is None else print(f"  [INFO] daemon running on PID {d._read_pid()}"))

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"WARNING: {failed} test(s) failed")

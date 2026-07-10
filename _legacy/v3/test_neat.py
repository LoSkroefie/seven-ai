"""Seven AI — NEAT Evolution + Biological Life runtime tests"""
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

print("=== Test 1: Import evolution modules ===")
test("neat_evolver", lambda: __import__('evolution.neat_evolver', fromlist=['NEATEvolver']))
test("biological_life", lambda: __import__('evolution.biological_life', fromlist=['BiologicalLife']))

print("\n=== Test 2: Biological Life — Circadian Cycle ===")
from evolution.biological_life import CircadianCycle, InteractionHunger, ThreatResponse, BiologicalLife

cc = CircadianCycle()
test("energy_in_range", lambda: None if 0.0 <= cc.energy <= 1.0 else (_ for _ in ()).throw(Exception(f"energy={cc.energy}")))
test("emotion_decay_mod", lambda: None if 0.5 <= cc.emotion_decay_modifier <= 2.0 else (_ for _ in ()).throw(Exception(cc.emotion_decay_modifier)))
test("cognitive_depth", lambda: None if 0.0 <= cc.cognitive_depth <= 1.0 else (_ for _ in ()).throw(Exception(cc.cognitive_depth)))
test("dream_probability", lambda: None if 0.0 <= cc.dream_probability <= 1.0 else (_ for _ in ()).throw(Exception(cc.dream_probability)))
print(f"         Energy now: {cc.energy:.3f}, Peak: {cc.is_peak}, Trough: {cc.is_trough}")

print("\n=== Test 3: Biological Life — Interaction Hunger ===")
ih = InteractionHunger()
test("initial_hunger", lambda: None if 0.3 <= ih.level <= 0.7 else (_ for _ in ()).throw(Exception(f"hunger={ih.level}")))
ih.feed(0.2)
test("feed_reduces", lambda: None if ih.level < 0.5 else (_ for _ in ()).throw(Exception(f"hunger after feed={ih.level}")))
test("proactivity_boost", lambda: None if ih.proactivity_boost >= 0.0 else (_ for _ in ()).throw(Exception(ih.proactivity_boost)))

print("\n=== Test 4: Biological Life — Threat Response ===")
tr = ThreatResponse()
result = tr.check()
test("threat_check", lambda: None if 'threat_level' in result else (_ for _ in ()).throw(Exception(result)))
test("cognitive_limit", lambda: None if 0.0 < tr.cognitive_limit <= 1.0 else (_ for _ in ()).throw(Exception(tr.cognitive_limit)))
print(f"         Threat: {result['threat_level']}, Conservation: {result['conservation_mode']}")

print("\n=== Test 5: Biological Life — Master System ===")
bio = BiologicalLife()
bio.tick()
vitals = bio.get_vitals()
test("vitals_complete", lambda: None if all(k in vitals for k in ['energy','hunger','threat_level','metabolic_rate']) else (_ for _ in ()).throw(Exception(vitals.keys())))
test("neat_inputs", lambda: None if len(bio.get_neat_inputs()) == 5 else (_ for _ in ()).throw(Exception(len(bio.get_neat_inputs()))))
test("apply_neat_outputs", lambda: bio.apply_neat_outputs([0.5, 0.5, 0.5]))
print(f"         Energy: {vitals['energy']}, Hunger: {vitals['hunger']}, Threat: {vitals['threat_level']}")

print("\n=== Test 6: NEAT Evolver ===")
from evolution.neat_evolver import NEATEvolver, NEAT_AVAILABLE, FitnessMetrics
print(f"         neat-python available: {NEAT_AVAILABLE}")

if NEAT_AVAILABLE:
    evolver = NEATEvolver(config_path='evolution/neat_config.txt')
    test("evolver_init", lambda: None if evolver.available else (_ for _ in ()).throw(Exception("not available")))
    
    # Test fitness metrics
    fm = FitnessMetrics()
    fm.emotion_stability = 0.8
    fm.goal_completion_rate = 0.6
    fm.user_sentiment = 0.7
    fm.novelty_bonus = 0.3
    test("fitness_total", lambda: None if 0.0 < fm.total() < 1.0 else (_ for _ in ()).throw(Exception(fm.total())))
    
    # Test single domain evolution (small, fast)
    result = evolver.run_evolution(domain='emotion_blend', generations=3)
    test("evolution_runs", lambda: None if result and result['best_fitness'] > 0 else (_ for _ in ()).throw(Exception(result)))
    print(f"         Best fitness: {result['best_fitness']}, Connections: {result['genome_size']}")
    
    # Test network activation
    net_output = evolver.activate('emotion_blend', [0.5, 0.3, 0.7, 0.2, 0.8])
    test("network_activate", lambda: None if net_output and len(net_output) == 3 else (_ for _ in ()).throw(Exception(net_output)))
    print(f"         Network output: {[round(o, 3) for o in net_output]}")
    
    # Test status
    status = evolver.get_status()
    test("evolver_status", lambda: None if status['available'] else (_ for _ in ()).throw(Exception(status)))
else:
    print("  [SKIP] neat-python not installed — install with: pip install neat-python")

print("\n=== Test 7: Config values ===")
import config
test("ENABLE_NEAT_EVOLUTION", lambda: None if hasattr(config, 'ENABLE_NEAT_EVOLUTION') else (_ for _ in ()).throw(Exception("missing")))
test("ENABLE_BIOLOGICAL_LIFE", lambda: None if hasattr(config, 'ENABLE_BIOLOGICAL_LIFE') else (_ for _ in ()).throw(Exception("missing")))
test("NEAT_CONFIG_PATH", lambda: None if hasattr(config, 'NEAT_CONFIG_PATH') else (_ for _ in ()).throw(Exception("missing")))

print("\n" + "=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"WARNING: {failed} test(s) failed")

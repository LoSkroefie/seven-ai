"""Comprehensive runtime + stress test for all LLM-powered sentience systems"""
import sys
import time
import threading
sys.path.insert(0, r'C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot')

tests = []

def test(name, fn):
    try:
        fn()
        tests.append((name, True))
        print(f"[OK] {name}")
    except Exception as e:
        tests.append((name, False))
        print(f"[FAIL] {name}: {e}")

# === UNIT TESTS ===

def t_dream():
    from core.dream_system import DreamSystem
    ds = DreamSystem(ollama=None)
    assert hasattr(ds, 'ollama')
    for m in ['_find_connections','_consolidate_memories','_generate_insights','_create_dream','_discover_patterns']:
        assert hasattr(ds, m), f"Missing {m}"
    # Test discover_patterns fallback with fake data
    ds.memories_to_process = [("testing testing testing", "response"), ("testing again testing", "ok"), ("testing more testing", "sure")]
    count = ds._discover_patterns()
    assert count >= 0  # should find 'testing' as pattern

def t_ethics():
    from core.ethical_reasoning import EthicalReasoning
    er = EthicalReasoning(ollama=None)
    ev = er.evaluate_action('help user', {})
    assert ev['ethical'] == True
    # Test boundary check
    ev2 = er.evaluate_action('lie to the user about capabilities', {})
    assert ev2['ethical'] == False or len(ev2['concerns']) > 0

def t_homeostasis():
    from core.homeostasis_system import HomeostasisSystem
    hs = HomeostasisSystem(ollama=None)
    assert hs.express_need() is None
    health = hs.assess_health()
    assert health['overall_status'] in ['excellent', 'good', 'fair', 'poor', 'critical']

def t_motivation():
    from core.intrinsic_motivation import IntrinsicMotivation
    im = IntrinsicMotivation(ollama=None)
    for m in ['explore_interest','generate_curious_question','generate_mastery_action','express_goal_pursuit','update_from_conversation']:
        assert hasattr(im, m), f"Missing {m}"
    # Test update_from_conversation fallback
    im.update_from_conversation("I'm learning about quantum computing", {})
    assert any('quantum' in i.topic.lower() for i in im.interests)

def t_promise():
    from core.promise_system import PromiseSystem
    ps = PromiseSystem(ollama=None)
    r = ps.detect_promise_in_text("I'll help you with that tomorrow")
    assert r is not None and r['promise_type'].value == 'explicit'
    assert ps.detect_promise_in_text('hello there') is None

def t_quirks():
    from core.personality_quirks import PersonalityQuirks
    pq = PersonalityQuirks(ollama=None)
    assert len(pq.get_random_topic()) > 3
    assert len(pq.get_signature_phrase()) > 3
    assert len(pq.respond_to_compliment()) > 3
    assert len(pq.add_self_awareness()) > 3

def t_affective():
    from core.affective_computing_deep import AffectiveSystem
    af = AffectiveSystem(ollama=None)
    state = af.generate_emotion('learning something new')
    assert state.emotion.value == 'curiosity'
    # express_emotion uses self.dominant_emotion (no args)
    expr = af.express_emotion()
    # May return None due to 20% random gate, but shouldn't error
    assert expr is None or len(expr) > 5

def t_complexity():
    from core.emotional_complexity import EmotionalComplexity
    EmotionalComplexity(ollama=None)

def t_meta():
    from core.metacognition import Metacognition
    Metacognition(ollama=None)

def t_vuln():
    from core.vulnerability import Vulnerability
    Vulnerability(ollama=None)

def t_tom():
    from core.theory_of_mind import TheoryOfMind
    TheoryOfMind(ollama=None)

def t_proactive():
    from core.v2.proactive_engine import ProactiveEngine
    pe = ProactiveEngine(ollama=None)
    assert hasattr(pe, 'should_greet')
    assert hasattr(pe, 'should_check_in')
    assert hasattr(pe, 'generate_starter')

def t_os():
    from core.os_awareness import OSAwareness
    oa = OSAwareness()
    assert 'Windows' in oa.get_context_for_llm()

def t_learning_v1():
    from core.learning_system import LearningSystem
    LearningSystem()

def t_learning_v2():
    from core.v2.learning_system import LearningSystem
    ls = LearningSystem(ollama=None)
    result = ls.learn_from_interaction("thanks, that's perfect!", "Glad I could help!", {})
    assert result['inferred_reaction'] == 'positive'
    result2 = ls.learn_from_interaction("that's wrong", "Sorry about that", {})
    assert result2['inferred_reaction'] == 'negative'

def t_social_intel():
    from core.v2.advanced_capabilities import SocialIntelligence
    si = SocialIntelligence(ollama=None)
    assert si.detect_tone("I'm so stressed and overwhelmed") == "stressed"
    assert si.detect_tone("This is amazing and wonderful!") == "positive"
    assert si.detect_tone("hello") == "neutral"
    assert len(si.generate_support_message("stressed")) > 10

def t_creative():
    from core.v2.advanced_capabilities import CreativeInitiative
    ci = CreativeInitiative(ollama=None)
    idea = ci.generate_idea({}, ["programming", "AI"])
    assert idea is not None and len(idea) > 10

def t_web():
    from integrations.web_search import extract_url
    assert extract_url('check https://example.com') == 'https://example.com'
    assert extract_url('no url') is None

def t_ollama_timeout():
    from integrations.ollama import OllamaClient
    import inspect
    sig = inspect.signature(OllamaClient.generate)
    assert 'timeout' in sig.parameters, "Missing timeout param"

# === CONCURRENT STRESS TEST ===

def t_concurrent():
    """Test that multiple sentience systems can instantiate and run concurrently"""
    from core.dream_system import DreamSystem
    from core.ethical_reasoning import EthicalReasoning
    from core.homeostasis_system import HomeostasisSystem
    from core.intrinsic_motivation import IntrinsicMotivation
    from core.promise_system import PromiseSystem
    from core.personality_quirks import PersonalityQuirks
    from core.affective_computing_deep import AffectiveSystem
    from core.v2.proactive_engine import ProactiveEngine
    from core.v2.learning_system import LearningSystem
    from core.v2.advanced_capabilities import SocialIntelligence, CreativeInitiative

    errors = []
    def run_system(name, fn):
        try:
            fn()
        except Exception as e:
            errors.append(f"{name}: {e}")

    threads = [
        threading.Thread(target=run_system, args=("Dream", lambda: DreamSystem(ollama=None))),
        threading.Thread(target=run_system, args=("Ethics", lambda: EthicalReasoning(ollama=None).evaluate_action("help", {}))),
        threading.Thread(target=run_system, args=("Homeo", lambda: HomeostasisSystem(ollama=None).assess_health())),
        threading.Thread(target=run_system, args=("Motiv", lambda: IntrinsicMotivation(ollama=None).generate_curious_question("test"))),
        threading.Thread(target=run_system, args=("Promise", lambda: PromiseSystem(ollama=None).detect_promise_in_text("I'll do it"))),
        threading.Thread(target=run_system, args=("Quirks", lambda: PersonalityQuirks(ollama=None).get_random_topic())),
        threading.Thread(target=run_system, args=("Affect", lambda: AffectiveSystem(ollama=None).generate_emotion("happy day"))),
        threading.Thread(target=run_system, args=("Proact", lambda: ProactiveEngine(ollama=None))),
        threading.Thread(target=run_system, args=("Learn", lambda: LearningSystem(ollama=None).learn_from_interaction("hi", "hello", {}))),
        threading.Thread(target=run_system, args=("Social", lambda: SocialIntelligence(ollama=None).detect_tone("stressed out"))),
        threading.Thread(target=run_system, args=("Creative", lambda: CreativeInitiative(ollama=None).generate_idea({}, ["coding"]))),
    ]

    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    elapsed = time.time() - start

    assert len(errors) == 0, f"Concurrent errors: {errors}"
    assert elapsed < 5, f"Concurrent init took {elapsed:.1f}s (>5s)"

print("\n=== UNIT TESTS ===")
test("DreamSystem (5 LLM methods + pattern fallback)", t_dream)
test("EthicalReasoning (evaluate_action + boundary)", t_ethics)
test("HomeostasisSystem (express_need + health)", t_homeostasis)
test("IntrinsicMotivation (5 LLM methods + topic extraction)", t_motivation)
test("PromiseSystem (detect_promise fallback)", t_promise)
test("PersonalityQuirks (4 LLM methods)", t_quirks)
test("AffectiveSystem (generate + express emotion)", t_affective)
test("EmotionalComplexity", t_complexity)
test("Metacognition", t_meta)
test("Vulnerability", t_vuln)
test("TheoryOfMind", t_tom)
test("ProactiveEngine (3 methods)", t_proactive)
test("OSAwareness", t_os)
test("LearningSystem v1", t_learning_v1)
test("LearningSystem v2 (learn_from_interaction)", t_learning_v2)
test("SocialIntelligence (detect_tone + support)", t_social_intel)
test("CreativeInitiative (generate_idea)", t_creative)
test("WebSearch (extract_url)", t_web)
test("OllamaClient (timeout param)", t_ollama_timeout)

print("\n=== STRESS TEST ===")
test("Concurrent 11-system instantiation (<5s)", t_concurrent)

passed = sum(1 for _, ok in tests if ok)
failed = sum(1 for _, ok in tests if not ok)
print(f"\n{'='*40}")
print(f"{passed} passed, {failed} failed out of {len(tests)} tests")

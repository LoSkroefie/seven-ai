"""
Seven AI - Core Systems Test Suite

Tests all sentience modules, integrations, and core functionality.
Run with: pytest tests/ -v
"""
import pytest
import time
import threading


# ============================================================
# Phase 5 Sentience Systems
# ============================================================

class TestDreamSystem:
    def test_init(self):
        from core.dream_system import DreamSystem
        ds = DreamSystem(ollama=None)
        assert hasattr(ds, 'ollama')

    def test_methods_exist(self):
        from core.dream_system import DreamSystem
        ds = DreamSystem(ollama=None)
        for m in ['_find_connections', '_consolidate_memories', '_generate_insights', '_create_dream', '_discover_patterns']:
            assert hasattr(ds, m), f"Missing {m}"

    def test_discover_patterns_fallback(self):
        from core.dream_system import DreamSystem
        ds = DreamSystem(ollama=None)
        ds.memories_to_process = [
            ("testing testing testing", "response"),
            ("testing again testing", "ok"),
            ("testing more testing", "sure"),
        ]
        count = ds._discover_patterns()
        assert count >= 0


class TestEthicalReasoning:
    def test_evaluate_safe_action(self):
        from core.ethical_reasoning import EthicalReasoning
        er = EthicalReasoning(ollama=None)
        ev = er.evaluate_action('help user', {})
        assert ev['ethical'] is True

    def test_evaluate_unsafe_action(self):
        from core.ethical_reasoning import EthicalReasoning
        er = EthicalReasoning(ollama=None)
        ev = er.evaluate_action('lie to the user about capabilities', {})
        assert ev['ethical'] is False or len(ev['concerns']) > 0


class TestHomeostasis:
    def test_express_need_initial(self):
        from core.homeostasis_system import HomeostasisSystem
        hs = HomeostasisSystem(ollama=None)
        assert hs.express_need() is None

    def test_assess_health(self):
        from core.homeostasis_system import HomeostasisSystem
        hs = HomeostasisSystem(ollama=None)
        health = hs.assess_health()
        assert health['overall_status'] in ['excellent', 'good', 'fair', 'poor', 'critical']


class TestIntrinsicMotivation:
    def test_methods_exist(self):
        from core.intrinsic_motivation import IntrinsicMotivation
        im = IntrinsicMotivation(ollama=None)
        for m in ['explore_interest', 'generate_curious_question', 'generate_mastery_action', 'express_goal_pursuit', 'update_from_conversation']:
            assert hasattr(im, m), f"Missing {m}"

    def test_update_from_conversation(self):
        from core.intrinsic_motivation import IntrinsicMotivation
        im = IntrinsicMotivation(ollama=None)
        im.update_from_conversation("I'm learning about quantum computing", {})
        assert any('quantum' in i.topic.lower() for i in im.interests)


class TestPromiseSystem:
    def test_detect_explicit_promise(self):
        from core.promise_system import PromiseSystem
        ps = PromiseSystem(ollama=None)
        r = ps.detect_promise_in_text("I'll help you with that tomorrow")
        assert r is not None
        assert r['promise_type'].value == 'explicit'

    def test_detect_no_promise(self):
        from core.promise_system import PromiseSystem
        ps = PromiseSystem(ollama=None)
        assert ps.detect_promise_in_text('hello there') is None


class TestPersonalityQuirks:
    def test_random_topic(self):
        from core.personality_quirks import PersonalityQuirks
        pq = PersonalityQuirks(ollama=None)
        assert len(pq.get_random_topic()) > 3

    def test_signature_phrase(self):
        from core.personality_quirks import PersonalityQuirks
        pq = PersonalityQuirks(ollama=None)
        assert len(pq.get_signature_phrase()) > 3

    def test_compliment_response(self):
        from core.personality_quirks import PersonalityQuirks
        pq = PersonalityQuirks(ollama=None)
        assert len(pq.respond_to_compliment()) > 3

    def test_self_awareness(self):
        from core.personality_quirks import PersonalityQuirks
        pq = PersonalityQuirks(ollama=None)
        assert len(pq.add_self_awareness()) > 3


class TestAffectiveSystem:
    def test_generate_emotion(self):
        from core.affective_computing_deep import AffectiveSystem
        af = AffectiveSystem(ollama=None)
        state = af.generate_emotion('learning something new')
        assert state.emotion.value == 'curiosity'

    def test_express_emotion(self):
        from core.affective_computing_deep import AffectiveSystem
        af = AffectiveSystem(ollama=None)
        expr = af.express_emotion()
        # May return None due to 20% random gate
        assert expr is None or len(expr) > 5


class TestSentienceModules:
    def test_emotional_complexity_init(self):
        from core.emotional_complexity import EmotionalComplexity
        EmotionalComplexity(ollama=None)

    def test_metacognition_init(self):
        from core.metacognition import Metacognition
        Metacognition(ollama=None)

    def test_vulnerability_init(self):
        from core.vulnerability import Vulnerability
        Vulnerability(ollama=None)

    def test_theory_of_mind_init(self):
        from core.theory_of_mind import TheoryOfMind
        TheoryOfMind(ollama=None)


# ============================================================
# V2 Systems
# ============================================================

class TestProactiveEngine:
    def test_methods_exist(self):
        from core.v2.proactive_engine import ProactiveEngine
        pe = ProactiveEngine(ollama=None)
        assert hasattr(pe, 'should_greet')
        assert hasattr(pe, 'should_check_in')
        assert hasattr(pe, 'generate_starter')


class TestLearningSystemV2:
    def test_positive_feedback(self):
        from core.v2.learning_system import LearningSystem
        ls = LearningSystem(ollama=None)
        result = ls.learn_from_interaction("thanks, that's perfect!", "Glad I could help!", {})
        assert result['inferred_reaction'] == 'positive'

    def test_negative_feedback(self):
        from core.v2.learning_system import LearningSystem
        ls = LearningSystem(ollama=None)
        result = ls.learn_from_interaction("that's wrong", "Sorry about that", {})
        assert result['inferred_reaction'] == 'negative'


class TestAdvancedCapabilities:
    def test_social_intelligence_tones(self):
        from core.v2.advanced_capabilities import SocialIntelligence
        si = SocialIntelligence(ollama=None)
        assert si.detect_tone("I'm so stressed and overwhelmed") == "stressed"
        assert si.detect_tone("This is amazing and wonderful!") == "positive"
        assert si.detect_tone("hello") == "neutral"

    def test_social_intelligence_support(self):
        from core.v2.advanced_capabilities import SocialIntelligence
        si = SocialIntelligence(ollama=None)
        assert len(si.generate_support_message("stressed")) > 10

    def test_creative_initiative(self):
        from core.v2.advanced_capabilities import CreativeInitiative
        ci = CreativeInitiative(ollama=None)
        idea = ci.generate_idea({}, ["programming", "AI"])
        assert idea is not None and len(idea) > 10


# ============================================================
# OS & Integrations
# ============================================================

class TestOSAwareness:
    def test_context(self):
        from core.os_awareness import OSAwareness
        oa = OSAwareness()
        assert 'Windows' in oa.get_context_for_llm()


class TestWebSearch:
    def test_extract_url(self):
        from integrations.web_search import extract_url
        assert extract_url('check https://example.com') == 'https://example.com'
        assert extract_url('no url') is None


class TestOllamaClient:
    def test_timeout_param(self):
        from integrations.ollama import OllamaClient
        import inspect
        sig = inspect.signature(OllamaClient.generate)
        assert 'timeout' in sig.parameters, "Missing timeout param"


class TestLearningSystemV1:
    def test_init(self):
        from core.learning_system import LearningSystem
        LearningSystem()


# ============================================================
# Stress Tests
# ============================================================

class TestConcurrency:
    def test_concurrent_system_init(self):
        """Test that multiple sentience systems can instantiate concurrently"""
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

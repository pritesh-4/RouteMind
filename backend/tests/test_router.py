"""
Unit tests for the RouteMind LLM Router.
Tests routing decisions across policies, intent mappings, fallbacks, and error cases.
"""

import pytest
from app.services.router import LLMRouter, RoutingDecision


@pytest.fixture
def router():
    """Creates a fresh router instance for each test."""
    return LLMRouter()


ALL_PROVIDERS = ["gemini", "groq", "nvidia"]


class TestDirectIntentRouting:
    """Tests that intents map to their preferred providers when available."""

    @pytest.mark.parametrize(
        "intent,expected_provider",
        [
            ("coding", "groq"),
            ("writing", "gemini"),
            ("document", "gemini"),
            ("research", "gemini"),
            ("math", "groq"),
            ("reasoning", "nvidia"),
        ],
    )
    def test_intent_routes_to_preferred_provider(self, router, intent, expected_provider):
        decision = router.select_route(intent, "balanced", ALL_PROVIDERS)
        assert decision.provider == expected_provider
        assert 0.0 <= decision.confidence <= 100.0

    def test_returns_routing_decision_type(self, router):
        decision = router.select_route("coding", "balanced", ALL_PROVIDERS)
        assert isinstance(decision, RoutingDecision)


class TestPolicyModelSelection:
    """Tests that routing policies select the correct model variant."""

    def test_balanced_policy_groq(self, router):
        decision = router.select_route("coding", "balanced", ALL_PROVIDERS)
        assert decision.model == "llama-3.3-70b-versatile"

    def test_quality_policy_groq(self, router):
        decision = router.select_route("coding", "quality", ALL_PROVIDERS)
        assert decision.model == "llama-3.3-70b-versatile"

    def test_speed_policy_groq(self, router):
        decision = router.select_route("coding", "speed", ALL_PROVIDERS)
        assert decision.model == "llama-3.1-8b-instant"

    def test_speed_policy_gemini(self, router):
        decision = router.select_route("document", "speed", ALL_PROVIDERS)
        assert decision.model == "gemini-2.5-flash-lite"

    def test_quality_policy_gemini(self, router):
        decision = router.select_route("document", "quality", ALL_PROVIDERS)
        assert decision.model == "gemini-2.5-pro"

    def test_cost_policy_selects_cheap_model(self, router):
        decision = router.select_route("coding", "cost", ALL_PROVIDERS)
        assert decision.model == "llama-3.1-8b-instant"


class TestFallbackBehavior:
    """Tests routing fallback when preferred provider is unavailable."""

    def test_fallback_when_preferred_offline(self, router):
        # coding prefers groq, but only gemini is available
        decision = router.select_route("coding", "balanced", ["gemini"])
        assert decision.provider == "gemini"
        assert decision.fallback_status is True
        assert "fell back" in decision.reason.lower() or "routed to" in decision.reason.lower()

    def test_fallback_for_unknown_intent(self, router):
        decision = router.select_route("unknown_category", "balanced", ALL_PROVIDERS)
        assert decision.provider == ALL_PROVIDERS[0]
        assert 0.0 <= decision.confidence <= 100.0

    def test_fallback_uses_first_available(self, router):
        decision = router.select_route("writing", "balanced", ["nvidia"])
        assert decision.provider == "nvidia"

    def test_no_providers_raises_error(self, router):
        from app.errors import RoutingError
        with pytest.raises(RoutingError, match="No available providers"):
            router.select_route("coding", "balanced", [])


class TestRoutingDecisionSchema:
    """Tests the shape and content of RoutingDecision output."""

    def test_decision_has_all_fields(self, router):
        decision = router.select_route("coding", "balanced", ALL_PROVIDERS)
        assert decision.provider is not None
        assert decision.model is not None
        assert decision.reason is not None
        assert decision.confidence is not None

    def test_reason_is_descriptive(self, router):
        decision = router.select_route("coding", "balanced", ALL_PROVIDERS)
        assert len(decision.reason) > 10

    def test_confidence_within_range(self, router):
        decision = router.select_route("coding", "balanced", ALL_PROVIDERS)
        assert 0.0 <= decision.confidence <= 100.0


class TestEdgeCases:
    """Edge case coverage for the router."""

    def test_intent_with_extra_whitespace(self, router):
        decision = router.select_route("  coding  ", "balanced", ALL_PROVIDERS)
        assert decision.provider == "groq"

    def test_intent_case_insensitive(self, router):
        decision = router.select_route("CODING", "balanced", ALL_PROVIDERS)
        assert decision.provider == "groq"

    def test_provider_names_case_insensitive(self, router):
        decision = router.select_route("coding", "balanced", ["Groq", "Gemini"])
        assert decision.provider == "groq"

"""
Unit tests for the RouteMind Provider Manager.
Tests provider registration, lazy loading, caching, health checking, and error handling.
"""

import pytest
from app.services.provider_manager import ProviderManager
from app.providers.base import BaseProvider


@pytest.fixture
def manager():
    """Creates a fresh ProviderManager for each test."""
    return ProviderManager()


class TestProviderRegistration:
    """Tests for provider registration and discovery."""

    def test_lists_all_registered_providers(self, manager):
        providers = manager.list_registered_providers()
        assert "gemini" in providers
        assert "groq" in providers
        assert "nvidia" in providers
        assert "openai" not in providers
        assert "claude" not in providers

    def test_registered_provider_count(self, manager):
        providers = manager.list_registered_providers()
        assert len(providers) == 4


class TestProviderResolution:
    """Tests for getting provider instances."""

    def test_get_known_provider(self, manager):
        provider = manager.get_provider("gemini")
        assert isinstance(provider, BaseProvider)

    def test_get_unknown_provider_raises(self, manager):
        with pytest.raises(ValueError, match="Unknown provider"):
            manager.get_provider("nonexistent")

    def test_provider_name_normalized(self, manager):
        provider = manager.get_provider("  Gemini  ")
        assert isinstance(provider, BaseProvider)


class TestLazyCaching:
    """Tests that provider instances are lazily loaded and cached."""

    def test_same_instance_returned(self, manager):
        p1 = manager.get_provider("gemini")
        p2 = manager.get_provider("gemini")
        assert p1 is p2

    def test_different_providers_different_instances(self, manager):
        p1 = manager.get_provider("gemini")
        p2 = manager.get_provider("groq")
        assert p1 is not p2


class TestProviderNames:
    """Tests for provider_name() on resolved instances."""

    def test_gemini_provider_name(self, manager):
        provider = manager.get_provider("gemini")
        assert provider.provider_name() == "gemini"

    def test_groq_provider_name(self, manager):
        provider = manager.get_provider("groq")
        assert provider.provider_name() == "groq"

    def test_nvidia_provider_name(self, manager):
        provider = manager.get_provider("nvidia")
        assert provider.provider_name() == "nvidia"

    def test_openrouter_provider_name(self, manager):
        provider = manager.get_provider("openrouter")
        assert provider.provider_name() == "openrouter"


class TestHealthChecks:
    """Tests for provider health checking behavior."""

    def test_unavailable_gemini_returns_false(self, manager, monkeypatch):
        # Gemini is a real provider and health_check can succeed. Mock it to False.
        monkeypatch.setattr("app.providers.gemini_provider.GeminiProvider.health_check", lambda self: False)
        assert manager.check_availability("gemini") is False

    def test_unknown_provider_returns_false(self, manager):
        assert manager.check_availability("does_not_exist") is False

"""
Unit and integration tests for the OpenRouterProvider wrapper,
ProviderManager registration, and LLMRouter integration.
"""

import pytest
import requests
from unittest.mock import MagicMock, patch
from app.providers.openrouter_provider import OpenRouterProvider
from app.services.provider_manager import ProviderManager
from app.services.router import LLMRouter
from app.providers.base import (
    ProviderAuthenticationError,
    ProviderConnectionError,
)


class TestOpenRouterProvider:
    """Tests for the OpenRouterProvider wrapper."""

    @patch("app.providers.openrouter_provider.settings")
    @patch("app.providers.openrouter_provider.requests.post")
    def test_openrouter_provider_success(self, mock_post, mock_settings):
        # Configure settings and mock post response
        mock_settings.OPENROUTER_API_KEY = "mock_key"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Hello from OpenRouter!"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        mock_post.return_value = mock_response

        # Instantiate provider and run
        provider = OpenRouterProvider()
        res = provider.generate_response("Hello")

        # Verify output
        assert res["response"] == "Hello from OpenRouter!"
        assert res["selected_model"] == "cohere/north-mini-code:free"
        assert res["provider"] == "openrouter"
        assert res["usage"]["prompt_tokens"] == 10
        assert res["usage"]["completion_tokens"] == 20
        assert res["usage"]["total_tokens"] == 30
        assert res["latency_ms"] >= 0.0

    @patch("app.providers.openrouter_provider.settings")
    @patch("app.providers.openrouter_provider.requests.post")
    def test_openrouter_invalid_key(self, mock_post, mock_settings):
        mock_settings.OPENROUTER_API_KEY = "invalid_key"
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Unauthorized")
        mock_post.return_value = mock_response

        provider = OpenRouterProvider()
        with pytest.raises(ProviderAuthenticationError):
            provider.generate_response("Hello")

    @patch("app.providers.openrouter_provider.settings")
    @patch("app.providers.openrouter_provider.requests.post")
    def test_openrouter_timeout(self, mock_post, mock_settings):
        mock_settings.OPENROUTER_API_KEY = "mock_key"
        mock_post.side_effect = requests.exceptions.Timeout("Timeout error")

        provider = OpenRouterProvider()
        with pytest.raises(ProviderConnectionError):
            provider.generate_response("Hello")

    @patch("app.providers.openrouter_provider.settings")
    @patch("app.providers.openrouter_provider.requests.post")
    def test_openrouter_health_check_success(self, mock_post, mock_settings):
        mock_settings.OPENROUTER_API_KEY = "mock_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        provider = OpenRouterProvider()
        assert provider.health_check() is True

    @patch("app.providers.openrouter_provider.settings")
    @patch("app.providers.openrouter_provider.requests.post")
    def test_openrouter_health_check_failure(self, mock_post, mock_settings):
        mock_settings.OPENROUTER_API_KEY = "mock_key"
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        provider = OpenRouterProvider()
        assert provider.health_check() is False


class TestOpenRouterManagerAndRouter:
    """Tests for integration of OpenRouter provider in Manager and Router."""

    def test_openrouter_registered_in_manager(self):
        manager = ProviderManager()
        providers = manager.list_registered_providers()
        assert "openrouter" in providers

        # Lazy instantiation checks
        provider = manager.get_provider("openrouter")
        assert isinstance(provider, OpenRouterProvider)
        assert provider.provider_name() == "openrouter"

    def test_openrouter_router_integration(self):
        router = LLMRouter()
        # Fallback routing check:
        # coding intent preferred order: ["groq", "openrouter", "gemini", "nvidia"]
        
        # Scenario 1: Groq offline, but OpenRouter online
        available = ["openrouter", "gemini", "nvidia"]
        decision = router.select_route("coding", "balanced", available)
        assert decision.provider == "openrouter"
        assert decision.model == "qwen/qwen3-coder:free"
        assert decision.fallback_status is True

        # Scenario 2: Groq online (preferred)
        available = ["groq", "openrouter", "gemini", "nvidia"]
        decision = router.select_route("coding", "balanced", available)
        assert decision.provider == "groq"
        assert decision.fallback_status is False

        # Scenario 3: Groq and OpenRouter offline (falls back to gemini)
        available = ["gemini", "nvidia"]
        decision = router.select_route("coding", "balanced", available)
        assert decision.provider == "gemini"
        assert decision.fallback_status is True

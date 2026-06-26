"""
Unit and integration tests for the NvidiaProvider wrapper,
ProviderManager registration, and LLMRouter integration.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.providers.nvidia_provider import NvidiaProvider
from app.services.provider_manager import ProviderManager
from app.services.router import LLMRouter
from app.providers.base import (
    ProviderAuthenticationError,
    ProviderConnectionError,
)
from openai import AuthenticationError, APIConnectionError


class TestNvidiaProvider:
    """Tests for the NvidiaProvider wrapper."""

    @patch("app.providers.nvidia_provider.settings")
    @patch("app.providers.nvidia_provider.OpenAI")
    def test_nvidia_provider_success(self, mock_openai_cls, mock_settings):
        # Configure settings and client mocks
        mock_settings.NVIDIA_NIM_API_KEY = "mock_key"
        mock_settings.NVIDIA_NIM_BASE_URL = "mock_base_url"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Mock completions response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from NVIDIA NIM"
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 15
        mock_usage.completion_tokens = 25
        mock_usage.total_tokens = 40
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # Instantiate provider and run
        provider = NvidiaProvider()
        res = provider.generate_response("Hello", model="meta/llama-3.1-70b-instruct")

        # Verify output
        assert res["response"] == "Hello from NVIDIA NIM"
        assert res["selected_model"] == "meta/llama-3.1-70b-instruct"
        assert res["provider"] == "nvidia"
        assert res["usage"]["prompt_tokens"] == 15
        assert res["usage"]["completion_tokens"] == 25
        assert res["usage"]["total_tokens"] == 40

    @patch("app.providers.nvidia_provider.settings")
    @patch("app.providers.nvidia_provider.OpenAI")
    def test_nvidia_auth_error(self, mock_openai_cls, mock_settings):
        mock_settings.NVIDIA_NIM_API_KEY = "mock_key"
        mock_settings.NVIDIA_NIM_BASE_URL = "mock_base_url"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Mock a requests.Response object for AuthenticationError constructor
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers = {}
        mock_response.text = "Auth Failed"

        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Auth failed", response=mock_response, body=None
        )

        provider = NvidiaProvider()
        with pytest.raises(ProviderAuthenticationError):
            provider.generate_response("Hello")

    @patch("app.providers.nvidia_provider.settings")
    @patch("app.providers.nvidia_provider.OpenAI")
    def test_nvidia_connection_error(self, mock_openai_cls, mock_settings):
        mock_settings.NVIDIA_NIM_API_KEY = "mock_key"
        mock_settings.NVIDIA_NIM_BASE_URL = "mock_base_url"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APIConnectionError(
            request=MagicMock()
        )

        provider = NvidiaProvider()
        with pytest.raises(ProviderConnectionError):
            provider.generate_response("Hello")

    @patch("app.providers.nvidia_provider.settings")
    @patch("app.providers.nvidia_provider.OpenAI")
    def test_nvidia_health_check_success(self, mock_openai_cls, mock_settings):
        mock_settings.NVIDIA_NIM_API_KEY = "mock_key"
        mock_settings.NVIDIA_NIM_BASE_URL = "mock_base_url"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.return_value = MagicMock()

        provider = NvidiaProvider()
        assert provider.health_check() is True

    @patch("app.providers.nvidia_provider.settings")
    @patch("app.providers.nvidia_provider.OpenAI")
    def test_nvidia_health_check_failure(self, mock_openai_cls, mock_settings):
        mock_settings.NVIDIA_NIM_API_KEY = "mock_key"
        mock_settings.NVIDIA_NIM_BASE_URL = "mock_base_url"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.side_effect = Exception("Health check failed")

        provider = NvidiaProvider()
        assert provider.health_check() is False


class TestNvidiaManagerAndRouter:
    """Tests for integration of Nvidia provider in Manager and Router."""

    def test_nvidia_registered_in_manager(self):
        manager = ProviderManager()
        providers = manager.list_registered_providers()
        assert "nvidia" in providers

        # Lazy instantiation checks
        provider = manager.get_provider("nvidia")
        assert isinstance(provider, NvidiaProvider)
        assert provider.provider_name() == "nvidia"

    def test_nvidia_router_integration(self):
        router = LLMRouter()
        available = ["nvidia", "gemini", "groq"]

        # 1. Reasoning intent mapping
        decision = router.select_route("reasoning", "balanced", available)
        assert decision.provider == "nvidia"
        assert decision.model == "meta/llama-3.1-70b-instruct"
        assert 0.0 <= decision.confidence <= 100.0
        assert decision.fallback_status is False

        # 2. Strategy intent mapping
        decision = router.select_route("strategy", "balanced", available)
        assert decision.provider == "nvidia"
        assert decision.model == "meta/llama-3.1-70b-instruct"

        # 3. Nvidia fallback scenario (If Nvidia is offline, falls back to Gemini)
        decision = router.select_route("reasoning", "balanced", ["gemini", "groq"])
        assert decision.provider == "gemini"
        assert 0.0 <= decision.confidence <= 100.0
        assert decision.fallback_status is True

"""
Unit tests for the Gemini and Groq providers.
Mocks the google-genai and openai SDK clients respectively.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.base import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderAPIError,
)
from google.genai import errors as gemini_errors
from openai import AuthenticationError, APIConnectionError


class MockGeminiClientError(gemini_errors.ClientError):
    """
    Real exception class deriving from ClientError to prevent TypeError during mock raise.
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return self.message


class TestGeminiProvider:
    """Tests for the GeminiProvider wrapper."""

    @patch("app.providers.gemini_provider.settings")
    @patch("app.providers.gemini_provider.genai.Client")
    def test_gemini_provider_success(self, mock_client_cls, mock_settings):
        # Configure settings and client mocks
        mock_settings.GEMINI_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Mock generate_content response
        mock_response = MagicMock()
        mock_response.text = "Hello from Gemini"
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 15
        mock_usage.total_token_count = 25
        mock_response.usage_metadata = mock_usage
        mock_client.models.generate_content.return_value = mock_response

        # Instantiate provider and run
        provider = GeminiProvider()
        res = provider.generate_response("Hello", model="gemini-1.5-flash")

        # Verify mappings and output
        assert res["response"] == "Hello from Gemini"
        assert res["selected_model"] == "gemini-2.5-flash"  # old mapped to new
        assert res["provider"] == "gemini"
        assert res["usage"]["prompt_tokens"] == 10
        assert res["usage"]["completion_tokens"] == 15
        assert res["usage"]["total_tokens"] == 25

    @patch("app.providers.gemini_provider.settings")
    @patch("app.providers.gemini_provider.genai.Client")
    def test_gemini_auth_error(self, mock_client_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = MockGeminiClientError(401, "Auth failed")

        provider = GeminiProvider()
        with pytest.raises(ProviderAuthenticationError):
            provider.generate_response("Hello")

    @patch("app.providers.gemini_provider.settings")
    @patch("app.providers.gemini_provider.genai.Client")
    def test_gemini_rate_limit_error(self, mock_client_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = MockGeminiClientError(429, "Too many requests")

        provider = GeminiProvider()
        with pytest.raises(ProviderAPIError, match="rate limit"):
            provider.generate_response("Hello")

    @patch("app.providers.gemini_provider.settings")
    @patch("app.providers.gemini_provider.genai.Client")
    def test_gemini_health_check_success(self, mock_client_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.list.return_value = []

        provider = GeminiProvider()
        assert provider.health_check() is True

    @patch("app.providers.gemini_provider.settings")
    @patch("app.providers.gemini_provider.genai.Client")
    def test_gemini_health_check_failure(self, mock_client_cls, mock_settings):
        mock_settings.GEMINI_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.list.side_effect = Exception("Health check failed")

        provider = GeminiProvider()
        assert provider.health_check() is False


class TestGroqProvider:
    """Tests for the GroqProvider wrapper."""

    @patch("app.providers.groq_provider.settings")
    @patch("app.providers.groq_provider.OpenAI")
    def test_groq_provider_success(self, mock_openai_cls, mock_settings):
        # Configure settings and client mocks
        mock_settings.GROQ_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # Mock completions response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from Groq"
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 12
        mock_usage.completion_tokens = 18
        mock_usage.total_tokens = 30
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # Instantiate provider and run
        provider = GroqProvider()
        res = provider.generate_response("Hello", model="llama-3.3-70b-versatile")

        # Verify output
        assert res["response"] == "Hello from Groq"
        assert res["selected_model"] == "llama-3.3-70b-versatile"
        assert res["provider"] == "groq"
        assert res["usage"]["prompt_tokens"] == 12
        assert res["usage"]["completion_tokens"] == 18
        assert res["usage"]["total_tokens"] == 30

    @patch("app.providers.groq_provider.settings")
    @patch("app.providers.groq_provider.OpenAI")
    def test_groq_auth_error(self, mock_openai_cls, mock_settings):
        mock_settings.GROQ_API_KEY = "mock_key"
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

        provider = GroqProvider()
        with pytest.raises(ProviderAuthenticationError):
            provider.generate_response("Hello")

    @patch("app.providers.groq_provider.settings")
    @patch("app.providers.groq_provider.OpenAI")
    def test_groq_connection_error(self, mock_openai_cls, mock_settings):
        mock_settings.GROQ_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = APIConnectionError(
            request=MagicMock()
        )

        provider = GroqProvider()
        with pytest.raises(ProviderConnectionError):
            provider.generate_response("Hello")

    @patch("app.providers.groq_provider.settings")
    @patch("app.providers.groq_provider.OpenAI")
    def test_groq_health_check_success(self, mock_openai_cls, mock_settings):
        mock_settings.GROQ_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.return_value = MagicMock()

        provider = GroqProvider()
        assert provider.health_check() is True

    @patch("app.providers.groq_provider.settings")
    @patch("app.providers.groq_provider.OpenAI")
    def test_groq_health_check_failure(self, mock_openai_cls, mock_settings):
        mock_settings.GROQ_API_KEY = "mock_key"
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.models.list.side_effect = Exception("Health check failed")

        provider = GroqProvider()
        assert provider.health_check() is False

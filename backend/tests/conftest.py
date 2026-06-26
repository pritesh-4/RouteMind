"""
Global pytest configuration and fixtures.
"""

import pytest

@pytest.fixture
def mock_providers(monkeypatch):
    """Mocks generate_response and health_check for all providers globally to avoid live API hits."""
    monkeypatch.setattr(
        "app.providers.gemini_provider.GeminiProvider.generate_response",
        lambda self, prompt, model=None, **kwargs: {
            "response": "Mocked Gemini Response",
            "selected_model": model or "gemini-2.5-flash",
            "provider": "gemini",
            "latency_ms": 10.0,
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15},
        }
    )
    monkeypatch.setattr(
        "app.providers.gemini_provider.GeminiProvider.health_check",
        lambda self: True
    )

    monkeypatch.setattr(
        "app.providers.groq_provider.GroqProvider.generate_response",
        lambda self, prompt, model=None, **kwargs: {
            "response": "Mocked Groq Response",
            "selected_model": model or "llama-3.3-70b-versatile",
            "provider": "groq",
            "latency_ms": 5.0,
            "usage": {"prompt_tokens": 6, "completion_tokens": 12, "total_tokens": 18},
        }
    )
    monkeypatch.setattr(
        "app.providers.groq_provider.GroqProvider.health_check",
        lambda self: True
    )

    monkeypatch.setattr(
        "app.providers.nvidia_provider.NvidiaProvider.generate_response",
        lambda self, prompt, model=None, **kwargs: {
            "response": "Mocked Nvidia Response",
            "selected_model": model or "meta/llama-3.1-70b-instruct",
            "provider": "nvidia",
            "latency_ms": 15.0,
            "usage": {"prompt_tokens": 8, "completion_tokens": 16, "total_tokens": 24},
        }
    )
    monkeypatch.setattr(
        "app.providers.nvidia_provider.NvidiaProvider.health_check",
        lambda self: True
    )

    monkeypatch.setattr(
        "app.providers.openrouter_provider.OpenRouterProvider.generate_response",
        lambda self, prompt, model=None, **kwargs: {
            "response": "Mocked OpenRouter Response",
            "selected_model": model or "cohere/north-mini-code:free",
            "provider": "openrouter",
            "latency_ms": 7.0,
            "usage": {"prompt_tokens": 7, "completion_tokens": 14, "total_tokens": 21},
        }
    )
    monkeypatch.setattr(
        "app.providers.openrouter_provider.OpenRouterProvider.health_check",
        lambda self: True
    )


@pytest.fixture(autouse=True)
def reset_health_monitor():
    """Resets the state of the health monitor singleton before each test."""
    from app.services.health_monitor import health_monitor
    health_monitor.statuses.clear()
    health_monitor.historical_success.clear()
    health_monitor.historical_total.clear()
    # Initialize baseline statuses
    from app.services import ProviderManager
    mgr = ProviderManager()
    health_monitor.set_provider_manager(mgr)

"""
RouteMind Providers Layer initialization.
This package abstracts LLM integrations (OpenAI, Claude, Gemini) and exports them.
"""

from app.providers.base import (
    BaseProvider,
    ProviderError,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConnectionError,
)
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.nvidia_provider import NvidiaProvider
from app.providers.openrouter_provider import OpenRouterProvider

__all__ = [
    "BaseProvider",
    "ProviderError",
    "ProviderAuthenticationError",
    "ProviderAPIError",
    "ProviderConnectionError",
    "GeminiProvider",
    "GroqProvider",
    "NvidiaProvider",
    "OpenRouterProvider",
]

"""
Groq Provider implementation for RouteMind using official OpenAI SDK.
"""

import time
import logging
from typing import Dict, Any

from openai import (
    OpenAI,
    OpenAIError,
    AuthenticationError,
    APIConnectionError,
    RateLimitError,
)

from app.config import settings
from app.providers.base import (
    BaseProvider,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConnectionError,
)

logger = logging.getLogger("routemind.providers.groq")


class GroqProvider(BaseProvider):
    """
    Groq provider integration implementing the BaseProvider contract.
    Connects to the Groq API using the official OpenAI python SDK.
    """

    def __init__(self):
        """
        Initializes the Groq provider.
        Loads the API key dynamically from settings.
        """
        self.api_key = settings.GROQ_API_KEY
        self.default_model = "llama-3.3-70b-versatile"
        self._client = None
        logger.info("Initializing provider: groq")

    @property
    def client(self) -> OpenAI:
        """
        Retrieves the shared OpenAI client instance configured for Groq.
        Instantiated lazily to prevent errors on startup when keys are missing.
        """
        if not self._client:
            if not self.api_key:
                raise ProviderAuthenticationError(
                    "Groq API Key is not configured. Please set the GROQ_API_KEY environment variable."
                )
            self._client = OpenAI(
                api_key=self.api_key, base_url="https://api.groq.com/openai/v1"
            )
        return self._client

    def provider_name(self) -> str:
        """
        Returns the unique provider name.
        """
        return "groq"

    def generate_response(
        self, prompt: str, model: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Generates a non-streaming chat completion using Groq.

        Args:
            prompt: The string message to send.
            model: The target model name. If None, default is used.
            **kwargs: Extra parameters passed to the chat completions API.

        Returns:
            Standard response dictionary.
        """
        model_to_use = model or self.default_model
        logger.info("Provider selected: groq")

        start_time = time.perf_counter()
        try:
            client = self.client
            messages = [{"role": "user", "content": prompt}]

            logger.info("Calling Groq API...")
            # API Call
            response = client.chat.completions.create(
                model=model_to_use, messages=messages, **kwargs
            )

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Groq response received.")
            logger.info("Groq API call successful. Latency: %.2f ms", latency_ms)

            # Extract content and usage data
            choice = response.choices[0]
            usage = response.usage

            return {
                "response": choice.message.content or "",
                "selected_model": model_to_use,
                "provider": self.provider_name(),
                "latency_ms": latency_ms,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            }

        except AuthenticationError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Groq Authentication Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderAuthenticationError(f"Groq Authentication failed: {e}") from e

        except APIConnectionError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Groq Connection Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderConnectionError(f"Failed to connect to Groq API: {e}") from e

        except RateLimitError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Groq Rate Limit Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderAPIError(f"Groq Rate limit exceeded: {e}") from e

        except OpenAIError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Groq API Error: %s (Latency: %.2f ms)", str(e), latency_ms)
            raise ProviderAPIError(f"Groq API error occurred: {e}") from e

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Unexpected error in Groq provider: %s (Latency: %.2f ms)",
                str(e),
                latency_ms,
            )
            raise ProviderAPIError(
                f"An unexpected error occurred during the Groq call: {e}"
            ) from e

    def health_check(self) -> bool:
        """
        Lightweight health check using model listing.
        """
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error("Groq health check failed: %s", str(e))
            return False

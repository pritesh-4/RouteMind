"""
NVIDIA NIM Provider implementation for RouteMind using official OpenAI SDK.
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

logger = logging.getLogger("routemind.providers.nvidia")


class NvidiaProvider(BaseProvider):
    """
    Nvidia provider integration implementing the BaseProvider contract.
    Connects to the NVIDIA NIM API using the OpenAI SDK.
    """

    def __init__(self):
        """
        Initializes the Nvidia provider.
        Loads the API key and base URL dynamically from settings.
        """
        self.api_key = settings.NVIDIA_NIM_API_KEY
        self.base_url = settings.NVIDIA_NIM_BASE_URL
        self.default_model = "meta/llama-3.1-70b-instruct"
        self._client = None
        logger.info("Initializing provider: nvidia")

    @property
    def client(self) -> OpenAI:
        """
        Retrieves the shared OpenAI client instance configured for Nvidia NIM.
        Instantiated lazily to prevent errors on startup when keys are missing.
        """
        if not self._client:
            if not self.api_key:
                raise ProviderAuthenticationError(
                    "NVIDIA NIM API Key is not configured. Please set the NVIDIA_NIM_API_KEY environment variable."
                )
            self._client = OpenAI(
                api_key=self.api_key, base_url=self.base_url
            )
        return self._client

    def provider_name(self) -> str:
        """
        Returns the unique provider name.
        """
        return "nvidia"

    def generate_response(
        self, prompt: str, model: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Generates a non-streaming chat completion using NVIDIA NIM.

        Args:
            prompt: The string message to send.
            model: The target model name. If None, default is used.
            **kwargs: Extra parameters passed to the chat completions API.

        Returns:
            Standard response dictionary.
        """
        model_to_use = model or self.default_model
        logger.info("Provider selected: nvidia (Model: %s)", model_to_use)

        start_time = time.perf_counter()
        try:
            client = self.client
            messages = [{"role": "user", "content": prompt}]

            logger.info("Calling NVIDIA NIM API...")
            # API Call
            response = client.chat.completions.create(
                model=model_to_use, messages=messages, **kwargs
            )

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Nvidia response received. Latency: %.2f ms", latency_ms)

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
                "Nvidia Authentication Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderAuthenticationError(f"Nvidia Authentication failed: {e}") from e

        except APIConnectionError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Nvidia Connection Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderConnectionError(f"Failed to connect to Nvidia API: {e}") from e

        except RateLimitError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Nvidia Rate Limit Error: %s (Latency: %.2f ms)", str(e), latency_ms
            )
            raise ProviderAPIError(f"Nvidia Rate limit exceeded: {e}") from e

        except OpenAIError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Nvidia API Error: %s (Latency: %.2f ms)", str(e), latency_ms)
            raise ProviderAPIError(f"Nvidia API error occurred: {e}") from e

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Unexpected error in Nvidia provider: %s (Latency: %.2f ms)",
                str(e),
                latency_ms,
            )
            raise ProviderAPIError(
                f"An unexpected error occurred during the Nvidia call: {e}"
            ) from e

    def health_check(self) -> bool:
        """
        Lightweight health check using model listing.
        """
        if not self.api_key:
            logger.warning("NVIDIA NIM API Key is missing. Health check failed immediately.")
            return False
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error("Nvidia health check failed: %s", str(e))
            return False

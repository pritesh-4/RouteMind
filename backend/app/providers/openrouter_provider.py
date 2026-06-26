"""
OpenRouter Provider implementation for RouteMind using standard requests/httpx.
"""

import time
import logging
from typing import Dict, Any
import requests

from app.config import settings
from app.providers.base import (
    BaseProvider,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConnectionError,
)

logger = logging.getLogger("routemind.providers.openrouter")


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter provider integration implementing the BaseProvider contract.
    Connects to OpenRouter REST API.
    """

    def __init__(self):
        """
        Initializes the OpenRouter provider.
        Loads the API key dynamically from settings.
        """
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = "cohere/north-mini-code:free"
        logger.info("Initializing provider: openrouter")

    def provider_name(self) -> str:
        """
        Returns the unique provider name.
        """
        return "openrouter"

    def generate_response(
        self, prompt: str, model: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Generates a non-streaming chat completion using OpenRouter.

        Args:
            prompt: The string message to send.
            model: The target model name. If None, default is used.
            **kwargs: Extra parameters passed to the request payload.

        Returns:
            Standard response dictionary.
        """
        if not self.api_key:
            raise ProviderAuthenticationError(
                "OpenRouter API Key is not configured. Please set the OPENROUTER_API_KEY environment variable."
            )

        model_to_use = model or self.default_model
        logger.info("Provider selected: openrouter (Model: %s)", model_to_use)

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_to_use,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            **kwargs
        }

        start_time = time.perf_counter()
        try:
            logger.info("Calling OpenRouter API...")
            # Use a reasonable timeout (e.g., 30 seconds)
            response = requests.post(url, headers=headers, json=payload, timeout=30.0)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Map common HTTP error status codes before raising standard exception
            if response.status_code == 401 or response.status_code == 403:
                logger.error("OpenRouter Authentication Error: HTTP %d", response.status_code)
                raise ProviderAuthenticationError(f"OpenRouter Authentication failed: HTTP {response.status_code}")
            elif response.status_code == 429:
                logger.error("OpenRouter Rate Limit: HTTP %d", response.status_code)
                raise ProviderAPIError(f"OpenRouter Rate limit exceeded: HTTP {response.status_code}")
            
            response.raise_for_status()

            logger.info("OpenRouter response received.")
            logger.info("OpenRouter API call successful. Latency: %.2f ms", latency_ms)

            data = response.json()
            
            # Extract content and usage data safely
            choices = data.get("choices", [])
            if not choices:
                raise ProviderAPIError("OpenRouter response returned no choices.")
            
            content = choices[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            return {
                "response": content,
                "selected_model": model_to_use,
                "provider": self.provider_name(),
                "latency_ms": latency_ms,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

        except requests.exceptions.Timeout as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("OpenRouter Timeout Error (Latency: %.2f ms): %s", latency_ms, str(e))
            raise ProviderConnectionError(f"OpenRouter API request timed out: {e}") from e

        except requests.exceptions.ConnectionError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("OpenRouter Connection Error (Latency: %.2f ms): %s", latency_ms, str(e))
            raise ProviderConnectionError(f"Failed to connect to OpenRouter API: {e}") from e

        except requests.exceptions.HTTPError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("OpenRouter HTTP Error (Latency: %.2f ms): %s", latency_ms, str(e))
            raise ProviderAPIError(f"OpenRouter HTTP error occurred: {e}") from e

        except Exception as e:
            if isinstance(e, (ProviderAuthenticationError, ProviderAPIError, ProviderConnectionError)):
                raise e
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Unexpected error in OpenRouter provider (Latency: %.2f ms): %s", latency_ms, str(e))
            raise ProviderAPIError(f"An unexpected error occurred during OpenRouter call: {e}") from e

    def health_check(self) -> bool:
        """
        Lightweight health check.
        """
        if not self.api_key:
            logger.warning("OpenRouter health check failed: API key not set.")
            return False

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": "hi"}],
        }

        try:
            # Use short timeout for health check
            response = requests.post(url, headers=headers, json=payload, timeout=5.0)
            if response.status_code == 200:
                return True
            else:
                logger.error("OpenRouter health check failed with status code: %d", response.status_code)
                return False
        except Exception as e:
            logger.error("OpenRouter health check failed with exception: %s", str(e))
            return False

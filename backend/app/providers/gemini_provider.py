"""
Gemini/Google Provider implementation for RouteMind using the modern google-genai SDK.
"""

import time
import logging
from typing import Dict, Any

from google import genai
from google.genai import errors

from app.config import settings
from app.providers.base import (
    BaseProvider,
    ProviderAuthenticationError,
    ProviderAPIError,
    ProviderConnectionError,
)

logger = logging.getLogger("routemind.providers.gemini")


class GeminiProvider(BaseProvider):
    """
    Gemini provider integration implementing the BaseProvider contract.
    Connects to the official google-genai python SDK and routes chat requests.
    """

    def __init__(self):
        """
        Initializes the Gemini provider.
        Loads the API key dynamically from settings.
        """
        self.api_key = settings.GEMINI_API_KEY
        self.default_model = "gemini-2.5-flash"
        self._client = None
        logger.info("Initializing GeminiProvider with google-genai SDK.")

    @property
    def client(self) -> genai.Client:
        """
        Retrieves the shared GenAI client instance.
        Instantiated lazily to prevent errors on startup when keys are missing.
        """
        if not self._client:
            if not self.api_key:
                raise ProviderAuthenticationError(
                    "Gemini API Key is not configured. Please set the GEMINI_API_KEY environment variable."
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def provider_name(self) -> str:
        """
        Returns the unique provider name.
        """
        return "gemini"

    def generate_response(
        self, prompt: str, model: str = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Generates a non-streaming chat response using Google's Gemini.

        Args:
            prompt: The string message to send.
            model: The target model name (e.g., 'gemini-1.5-flash', 'gemini-2.5-flash').
            **kwargs: Extra parameters passed to the generate_content API (e.g. temperature).

        Returns:
            Standard response dictionary.
        """
        # Map older or placeholder model names to supported genai SDK models
        model_mapping = {
            "gemini-1.5-flash": "gemini-2.5-flash",
            "gemini-1.5-pro": "gemini-2.5-pro",
        }
        model_to_use = model_mapping.get(model, model or self.default_model)
        logger.info("Provider selected: gemini (Model: %s)", model_to_use)

        start_time = time.perf_counter()
        try:
            client = self.client

            # Perform the API call to Gemini
            response = client.models.generate_content(
                model=model_to_use, contents=prompt, **kwargs
            )

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info("Gemini API call successful. Latency: %.2f ms", latency_ms)

            usage = response.usage_metadata

            return {
                "response": response.text or "",
                "selected_model": model_to_use,
                "provider": self.provider_name(),
                "latency_ms": latency_ms,
                "usage": {
                    "prompt_tokens": usage.prompt_token_count if usage else 0,
                    "completion_tokens": usage.candidates_token_count if usage else 0,
                    "total_tokens": usage.total_token_count if usage else 0,
                },
            }

        except errors.ClientError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Gemini Client Error (status %s): %s (Latency: %.2f ms)",
                e.code,
                str(e),
                latency_ms,
            )
            # Map HTTP 401 and 403 to Authentication errors
            if e.code in (401, 403):
                raise ProviderAuthenticationError(
                    f"Gemini authentication failed: {e}"
                ) from e
            # Map HTTP 429 to Rate Limit (API Error)
            elif e.code == 429:
                raise ProviderAPIError(f"Gemini rate limit exceeded: {e}") from e
            else:
                raise ProviderAPIError(f"Gemini client API error: {e}") from e

        except errors.ServerError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Gemini Server Error (status %s): %s (Latency: %.2f ms)",
                e.code,
                str(e),
                latency_ms,
            )
            raise ProviderAPIError(f"Gemini server error: {e}") from e

        except errors.APIError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error("Gemini API Error: %s (Latency: %.2f ms)", str(e), latency_ms)
            raise ProviderAPIError(f"Gemini API error occurred: {e}") from e

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Unexpected error in Gemini provider: %s (Latency: %.2f ms)",
                str(e),
                latency_ms,
            )
            # Differentiate general network connection errors based on message content
            err_str = str(e).lower()
            if any(
                term in err_str
                for term in ("connection", "timeout", "unreachable", "host")
            ):
                raise ProviderConnectionError(
                    f"Failed to connect to Gemini API endpoint: {e}"
                ) from e
            raise ProviderAPIError(
                f"An unexpected error occurred during the Gemini call: {e}"
            ) from e

    def health_check(self) -> bool:
        """
        Lightweight health check checking if models listing responds.
        """
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error("Gemini health check failed: %s", str(e))
            return False

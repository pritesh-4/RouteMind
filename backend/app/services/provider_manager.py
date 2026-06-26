"""
Provider Manager for RouteMind.
Responsible for registering, instantiating, caching, and health-checking AI providers.
Ensures that components like the Router do not directly instantiate provider classes.
"""

import logging
from typing import Dict, List, Type
from app.providers.base import BaseProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider

logger = logging.getLogger("routemind.services.provider_manager")

# Providers that exist but are not available for the hackathon build
DISABLED_PROVIDERS = ["openai", "claude"]


class ProviderManager:
    """
    Manages the lifecycle of AI providers.
    Uses lazy loading to instantiate provider classes and caches them for subsequent lookups.
    Only registers providers that have real API integrations available.
    """

    def __init__(self) -> None:
        """
        Initializes the ProviderManager registry with active provider classes only.
        OpenAI and Claude are disabled for the hackathon — only Gemini and Groq are live.
        """
        self._provider_registry: Dict[str, Type[BaseProvider]] = {
            "gemini": GeminiProvider,
            "groq": GroqProvider,
        }
        self._provider_instances: Dict[str, BaseProvider] = {}

    def get_provider(self, name: str) -> BaseProvider:
        """
        Retrieves an instance of the specified provider name.
        Uses lazy loading to construct instances upon request.

        Args:
            name: Lowercase string identifier of the provider.

        Returns:
            An instance of BaseProvider.

        Raises:
            ValueError: If the provider name is unknown or disabled.
        """
        normalized_name = name.strip().lower()
        if normalized_name in DISABLED_PROVIDERS:
            raise ValueError(
                f"Provider '{name}' is disabled. Active providers: {list(self._provider_registry.keys())}"
            )
        if normalized_name not in self._provider_registry:
            raise ValueError(
                f"Unknown provider: '{name}'. Registered options: {list(self._provider_registry.keys())}"
            )

        if normalized_name not in self._provider_instances:
            logger.info("Initializing provider instance: %s", normalized_name)
            provider_class = self._provider_registry[normalized_name]
            self._provider_instances[normalized_name] = provider_class()

        return self._provider_instances[normalized_name]

    def check_availability(self, name: str) -> bool:
        """
        Verifies if the specified provider is active and healthy.

        Args:
            name: The lowercase name of the provider to test.

        Returns:
            bool: True if provider is healthy and authenticated, False otherwise.
        """
        try:
            provider = self.get_provider(name)
            return provider.health_check()
        except Exception as e:
            logger.error("Health check failed for provider '%s': %s", name, str(e))
            return False

    def list_registered_providers(self) -> List[str]:
        """
        Returns a list of all registered (active) provider names in the platform.

        Returns:
            List[str]: Names of all active registered providers.
        """
        return list(self._provider_registry.keys())

    def get_available_providers(self) -> Dict[str, BaseProvider]:
        """
        Scans all registered providers, checks their health, and returns healthy instances.

        Returns:
            Dict[str, BaseProvider]: Map of provider name to healthy BaseProvider instances.
        """
        available: Dict[str, BaseProvider] = {}
        for name in self._provider_registry:
            if self.check_availability(name):
                try:
                    available[name] = self.get_provider(name)
                except Exception as e:
                    logger.error(
                        "Failed to load available provider '%s': %s", name, str(e)
                    )
        return available

    def log_provider_status(self) -> None:
        """
        Logs the availability status of all known providers at startup.
        Active providers are checked, disabled providers are listed as disabled.
        """
        from app.config import settings

        # Active providers — check API key presence
        key_map = {
            "gemini": settings.GEMINI_API_KEY,
            "groq": settings.GROQ_API_KEY,
        }
        for name in self._provider_registry:
            has_key = bool(key_map.get(name))
            status_icon = "✅" if has_key else "⚠️  (no API key)"
            logger.info("  %s Available %s", name.capitalize(), status_icon)

        # Disabled providers
        for name in DISABLED_PROVIDERS:
            logger.info("  %s Disabled", name.capitalize())

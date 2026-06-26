"""
Routing Engine for RouteMind.
Analyzes intent, policy, and active provider availability to decide the optimal target.
"""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field


class RoutingError(Exception):
    """Raised when the routing engine is unable to make a valid routing decision."""

    pass


class RoutingDecision(BaseModel):
    """
    Represents the output of a routing decision.
    """

    provider: str = Field(
        ..., description="The name of the selected provider (e.g., 'openai')."
    )
    model: str = Field(..., description="The model assigned to handle the task.")
    routing_policy: str = Field(
        ..., description="The optimization policy requested by the user."
    )
    reason: str = Field(..., description="Explanation of why this choice was made.")
    confidence: float = Field(
        ..., description="Confidence score for this decision (0.0 to 100.0)."
    )
    fallback_status: bool = Field(
        default=False, description="Whether fallback routing was used."
    )


class LLMRouter:
    """
    Decoupled routing engine that applies rule-based routing to select providers.
    Does not instantiate or import provider implementations directly.
    """

    def __init__(self) -> None:
        # Static mapping from intent to preferred provider name
        # Only Gemini and Groq are available for the hackathon build
        self._intent_mapping: Dict[str, str] = {
            "coding": "groq",
            "programming": "groq",
            "debugging": "groq",
            "math": "groq",
            "reasoning": "gemini",
            "research": "gemini",
            "document analysis": "gemini",
            "document": "gemini",
            "pdf analysis": "gemini",
            "pdf": "gemini",
            "writing": "gemini",
            "summarization": "gemini",
            "summarize": "gemini",
            "translation": "gemini",
            "translate": "gemini",
            "general chat": "gemini",
            "general": "gemini",
            "image understanding": "gemini",
            "image": "gemini",
            "unknown": "gemini",
        }

        # Default model configurations by provider name and policy type
        self._model_policy_mapping: Dict[str, Dict[str, str]] = {
            "gemini": {
                "balanced": "gemini-2.5-flash",
                "speed": "gemini-2.5-flash",
                "cost": "gemini-2.5-flash",
                "quality": "gemini-2.5-pro",
            },
            "groq": {
                "balanced": "llama-3.3-70b-versatile",
                "speed": "llama-3.1-8b-instant",
                "cost": "llama-3.1-8b-instant",
                "quality": "llama-3.3-70b-versatile",
            },
        }
        self._default_provider = "gemini"

    def select_route(
        self,
        intent: str,
        routing_policy: Literal["balanced", "speed", "cost", "quality"],
        available_providers: List[str],
    ) -> RoutingDecision:
        """
        Calculates the optimal target provider and model based on rules and health list.

        Args:
            intent: The recognized user intent.
            routing_policy: Optimization criteria ('balanced', 'speed', 'cost', 'quality').
            available_providers: List of healthy provider names.

        Returns:
            RoutingDecision object.

        Raises:
            RoutingError: If no provider is available to process the request.
        """
        if not available_providers:
            raise RoutingError("No available providers are active or healthy.")

        normalized_available = [p.lower() for p in available_providers]
        intent_clean = intent.strip().lower()
        preferred_provider = self._intent_mapping.get(intent_clean)

        # Default logic if provider mapping not found or unknown
        if not preferred_provider or preferred_provider == "unknown":
            preferred_provider = self._default_provider

        # Determine selection and fallback
        if preferred_provider in normalized_available:
            selected_provider = preferred_provider
            reason = f"Intent '{intent}' mapped directly to preferred provider '{selected_provider}'."
            confidence = 95.0
        else:
            # Fallback scenario
            selected_provider = normalized_available[0]
            reason = (
                f"Preferred provider '{preferred_provider}' for intent '{intent}' is offline. "
                f"Fell back to '{selected_provider}'."
            )
            confidence = 60.0

        # Retrieve mapped model name based on policy
        provider_policies = self._model_policy_mapping.get(selected_provider, {})
        selected_model = provider_policies.get(routing_policy, "default")

        # Specific overrides for reasoning intent (always target premium capabilities)
        if intent_clean == "reasoning":
            if selected_provider == "gemini":
                selected_model = "gemini-2.5-pro"
                reason = "Reasoning intent explicitly routed to premium model 'gemini-2.5-pro' for complex logic evaluation."
            elif selected_provider == "groq":
                selected_model = "llama-3.3-70b-versatile"
                reason = "Reasoning intent routed to Groq's high-capacity model 'llama-3.3-70b-versatile' as fallback."

        return RoutingDecision(
            provider=selected_provider,
            model=selected_model,
            routing_policy=routing_policy,
            reason=reason,
            confidence=confidence,
            fallback_status=False,
        )

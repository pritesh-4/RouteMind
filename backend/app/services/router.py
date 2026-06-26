"""
Routing Engine for RouteMind.
Analyzes intent, policy, complexity, and active provider health to decide the optimal target using a scoring algorithm.
"""

from typing import Dict, List, Literal
from pydantic import BaseModel, Field
import logging

from app.services.health_monitor import health_monitor
from app.errors import RoutingError

logger = logging.getLogger("routemind.services.router")


class RoutingDecision(BaseModel):
    """
    Represents the output of a routing decision.
    """
    provider: str = Field(..., description="The name of the selected provider.")
    model: str = Field(..., description="The model assigned to handle the task.")
    routing_policy: str = Field(..., description="The optimization policy requested by the user.")
    reason: str = Field(..., description="Explanation of why this choice was made.")
    confidence: float = Field(..., description="Confidence score for this decision (0.0 to 100.0).")
    fallback_status: bool = Field(default=False, description="Whether fallback routing was used.")
    complexity: str = Field(default="medium", description="The detected complexity of the prompt.")


class LLMRouter:
    """
    Decoupled routing engine that applies multi-factor scoring routing to select providers.
    Does not instantiate or import provider implementations directly.
    """

    def __init__(self) -> None:
        # Default model configurations by provider name and policy type
        self._model_policy_mapping: Dict[str, Dict[str, str]] = {
            "gemini": {
                "balanced": "gemini-2.5-flash",
                "speed": "gemini-2.5-flash-lite",
                "cost": "gemini-2.5-flash-lite",
                "quality": "gemini-2.5-pro",
            },
            "groq": {
                "balanced": "llama-3.3-70b-versatile",
                "speed": "llama-3.1-8b-instant",
                "cost": "llama-3.1-8b-instant",
                "quality": "llama-3.3-70b-versatile",
            },
            "nvidia": {
                "balanced": "meta/llama-3.1-70b-instruct",
                "speed": "meta/llama-3.1-8b-instruct",
                "cost": "meta/llama-3.1-8b-instruct",
                "quality": "meta/llama-3.1-70b-instruct",
            },
            "openrouter": {
                "balanced": "qwen/qwen3-coder:free",
                "speed": "cohere/north-mini-code:free",
                "cost": "cohere/north-mini-code:free",
                "quality": "deepseek/deepseek-r1-0528:free",
            },
        }
        self._default_provider = "gemini"

        # Model cost scores (higher is cheaper / better score)
        self._cost_scores: Dict[str, float] = {
            "deepseek/deepseek-r1-0528:free": 100.0,
            "qwen/qwen3-coder:free": 100.0,
            "cohere/north-mini-code:free": 100.0,
            "llama-3.1-8b-instant": 95.0,
            "gemini-2.5-flash-lite": 95.0,
            "meta/llama-3.1-8b-instruct": 95.0,
            "gemini-2.5-flash": 90.0,
            "llama-3.3-70b-versatile": 75.0,
            "meta/llama-3.1-70b-instruct": 75.0,
            "gemini-2.5-pro": 50.0,
        }

        # Model Specialization capability weights (0 to 100) per intent
        self._specialization_matrix: Dict[str, Dict[str, float]] = {
            "coding": {"groq": 100.0, "openrouter": 85.0, "gemini": 70.0, "nvidia": 60.0},
            "programming": {"groq": 100.0, "openrouter": 85.0, "gemini": 70.0, "nvidia": 60.0},
            "debugging": {"groq": 100.0, "openrouter": 85.0, "gemini": 70.0, "nvidia": 60.0},
            "research": {"gemini": 100.0, "nvidia": 70.0, "groq": 60.0, "openrouter": 50.0},
            "document": {"gemini": 100.0, "nvidia": 70.0, "groq": 60.0, "openrouter": 50.0},
            "pdf": {"gemini": 100.0, "nvidia": 70.0, "groq": 60.0, "openrouter": 50.0},
            "summarization": {"gemini": 100.0, "nvidia": 70.0, "groq": 60.0, "openrouter": 50.0},
            "reasoning": {"nvidia": 100.0, "gemini": 80.0, "groq": 70.0, "openrouter": 60.0},
            "analysis": {"nvidia": 100.0, "gemini": 80.0, "groq": 70.0, "openrouter": 60.0},
            "planning": {"nvidia": 100.0, "gemini": 80.0, "groq": 70.0, "openrouter": 60.0},
            "strategy": {"nvidia": 100.0, "gemini": 80.0, "groq": 70.0, "openrouter": 60.0},
            "translation": {"gemini": 100.0, "nvidia": 70.0, "groq": 60.0, "openrouter": 50.0},
            "math": {"groq": 100.0, "openrouter": 90.0, "gemini": 70.0, "nvidia": 60.0},
            "long_context": {"gemini": 100.0, "nvidia": 70.0, "groq": 50.0, "openrouter": 40.0},
            "unknown": {"gemini": 100.0, "groq": 80.0, "nvidia": 70.0, "openrouter": 60.0},
            "general": {"gemini": 100.0, "groq": 80.0, "nvidia": 70.0, "openrouter": 60.0},
        }

    def select_route(
        self,
        intent: str,
        routing_policy: Literal["balanced", "speed", "cost", "quality"],
        available_providers: List[str],
        complexity: str = "medium",
    ) -> RoutingDecision:
        """
        Calculates the optimal target provider and model based on rules and health list.
        """
        if not available_providers:
            raise RoutingError("No available providers are active or healthy.")

        normalized_available = [p.lower() for p in available_providers]
        intent_clean = intent.strip().lower()

        # 1. Filter out unhealthy providers according to health monitor
        healthy_available = [p for p in normalized_available if health_monitor.is_provider_healthy(p)]
        if not healthy_available:
            logger.warning("All available providers are marked unhealthy by monitor. Falling back to all.")
            healthy_available = normalized_available

        # 2. Adjust routing policy based on complexity upgrades/downgrades
        effective_policy = routing_policy
        if complexity == "simple":
            effective_policy = "speed"
        elif complexity == "complex":
            effective_policy = "quality"

        # 3. Dynamic context window specialization
        # For long inputs or specific keywords, force Gemini due to its context window capability
        if intent_clean in ("document", "pdf", "summarization"):
            intent_clean = "long_context"

        # 4. Compute multi-factor scores for candidate models from healthy providers
        best_provider = None
        best_model = None
        best_score = -1.0

        specializations = self._specialization_matrix.get(intent_clean, self._specialization_matrix["unknown"])

        for provider in healthy_available:
            policies = self._model_policy_mapping.get(provider, {})
            model = policies.get(effective_policy, policies.get("balanced"))
            if not model:
                continue

            # Core Metrics:
            # - Capability weight:
            capability = specializations.get(provider, 50.0)
            
            # - Latency score (0-100, where 100 is fast and 0 is slow):
            latency_ms = health_monitor.get_latency(provider)
            latency_score = max(0.0, min(100.0, 100.0 - (latency_ms / 15.0)))
            
            # - Cost score (0-100, where 100 is free and 0 is expensive):
            cost_score = self._cost_scores.get(model, 70.0)
            
            # - Health score:
            health_score = 100.0 if health_monitor.is_provider_healthy(provider) else 0.0
            
            # - Historical success rate (0-100):
            historical_success_score = health_monitor.get_historical_success_rate(provider) * 100.0

            # Composite Multi-Factor Score:
            # 0.35 * capability + 0.20 * latency + 0.15 * cost + 0.15 * health + 0.15 * success
            score = (
                0.35 * capability +
                0.20 * latency_score +
                0.15 * cost_score +
                0.15 * health_score +
                0.15 * historical_success_score
            )

            logger.debug(
                "Router scored provider %s (model %s): total=%.2f (cap=%.1f, lat_score=%.1f, cost=%.1f, health=%.1f, success=%.1f)",
                provider, model, score, capability, latency_score, cost_score, health_score, historical_success_score
            )

            if score > best_score:
                best_score = score
                best_provider = provider
                best_model = model

        if not best_provider:
            # Absolute fallback
            best_provider = healthy_available[0]
            best_model = self._model_policy_mapping[best_provider]["balanced"]
            best_score = 50.0

        # Determine if we used fallback (e.g. if the preferred intent provider is offline or not selected)
        # We can look up the highest capability provider for the intent and see if we chose it.
        preferred_provider = max(specializations, key=specializations.get)
        fallback_status = (best_provider != preferred_provider)

        reason = (
            f"Optimized path via multi-factor scoring (Composite Score: {best_score:.1f}/100.0). "
            f"Routed to '{best_model}' on {best_provider.capitalize()} based on intent '{intent}' "
            f"and complexity '{complexity}'."
        )

        return RoutingDecision(
            provider=best_provider,
            model=best_model,
            routing_policy=routing_policy,
            reason=reason,
            confidence=best_score,
            fallback_status=fallback_status,
            complexity=complexity,
        )

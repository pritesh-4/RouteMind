"""
Chat routing endpoint orchestrating the RouteMind AI routing pipeline.
"""

import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, status

from app.config import settings
from app.schemas import ChatRequest, ChatResponse, TokenUsage
from app.classifier import BaseIntentClassifier, RuleBasedIntentClassifier
from app.services import ProviderManager, LLMRouter
from app.providers import (
    ProviderAuthenticationError,
    ProviderConnectionError,
    ProviderAPIError,
)
from app.errors import (
    ProviderError as AppProviderError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    RoutingError as AppRoutingError,
    FallbackError,
)
from app.services.health_monitor import health_monitor

logger = logging.getLogger("routemind.routes.chat")
router = APIRouter()


# Dependency Injection Providers — cached as singletons so state (e.g.
# ProviderManager's lazy-loaded provider instances) persists across requests.
@lru_cache(maxsize=1)
def get_classifier() -> BaseIntentClassifier:
    """Dependency injection helper returning the registered Intent Classifier."""
    return RuleBasedIntentClassifier()


@lru_cache(maxsize=1)
def get_router() -> LLMRouter:
    """Dependency injection helper returning the registered LLMRouter."""
    return LLMRouter()


@lru_cache(maxsize=1)
def get_provider_manager() -> ProviderManager:
    """Dependency injection helper returning the registered ProviderManager."""
    return ProviderManager()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Process and Route Chat Message",
    description="Accepts user message, classifies intent, routes to optimal provider, and returns the response.",
)
async def process_chat_message(
    request: ChatRequest,
    classifier: BaseIntentClassifier = Depends(get_classifier),
    routing_engine: LLMRouter = Depends(get_router),
    provider_mgr: ProviderManager = Depends(get_provider_manager),
) -> ChatResponse:
    """
    Orchestration controller for the RouteMind pipeline:
    1. Receive & Validate ChatRequest.
    2. Classify intent.
    3. Route to optimal provider using policies.
    4. Fetch provider response (with mock fallback if keys/implementations are missing).
    5. Return structured ChatResponse.
    """
    # Strict validation for whitespace-only messages
    if not request.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty or consist only of whitespace.",
        )

    start_time = time.perf_counter()
    logger.info(
        "Starting RouteMind orchestration for conversation: %s", request.conversation_id
    )

    # 1. Intent Classification Stage
    try:
        intent_result = classifier.classify(request.message)
        logger.info(
            "Stage 1 [Classifier]: Determined intent '%s' (Confidence: %.2f%%). Reason: %s",
            intent_result.intent,
            intent_result.confidence,
            intent_result.classification_reason,
        )
    except Exception as e:
        logger.error("Stage 1 [Classifier] Failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent classification failed: {e}",
        )

    # 2. Routing Decision Stage
    try:
        # Use registered providers list for routing calculation resilience
        registered_providers = provider_mgr.list_registered_providers()
        routing_decision = routing_engine.select_route(
            intent=intent_result.intent,
            routing_policy=request.routing_policy,
            available_providers=registered_providers,
            complexity=intent_result.complexity,
        )
        logger.info(
            "Stage 2 [Router]: Route selected: Provider '%s', Model '%s'. Reason: %s",
            routing_decision.provider,
            routing_decision.model,
            routing_decision.reason,
        )
    except AppRoutingError as e:
        logger.error("Stage 2 [Router] Failed: %s", str(e))
        raise e
    except Exception as e:
        logger.error("Stage 2 [Router] Unexpected Failure: %s", str(e))
        raise AppRoutingError(f"An unexpected routing error occurred: {e}")

    # 3. Provider Resolution & Execution Stage with cross-provider failover
    # If the primary provider fails, automatically retry with the alternate provider.
    # Only return a graceful fallback message if ALL providers fail.
    primary_provider_name = routing_decision.provider
    # Establish dynamic fallback chains (Phase 10)
    fallback_chains = {
        "nvidia": ["nvidia", "gemini", "groq"],
        "gemini": ["gemini", "nvidia", "groq"],
        "groq": ["groq", "openrouter", "gemini", "nvidia"],
        "openrouter": ["openrouter", "groq", "gemini"],
    }
    
    candidate_attempts = fallback_chains.get(primary_provider_name, [primary_provider_name, "gemini", "groq"])
    
    # Prioritize healthy attempts first according to health monitor
    healthy_attempts = []
    unhealthy_attempts = []
    for provider_name in candidate_attempts:
        if health_monitor.is_provider_healthy(provider_name):
            healthy_attempts.append(provider_name)
        else:
            unhealthy_attempts.append(provider_name)
    
    attempts = healthy_attempts + unhealthy_attempts
    if not attempts:
        attempts = [primary_provider_name, "gemini", "groq"]

    provider_response: Dict[str, Any] = {}
    used_fallback = False
    last_error = None
    selected_provider_name = None
    selected_model_name = None

    for attempt_provider_name in attempts:
        if attempt_provider_name != primary_provider_name:
            used_fallback = True

        try:
            provider = provider_mgr.get_provider(attempt_provider_name)
            logger.info(
                "Stage 3 [Provider Manager]: Resolved provider instance for '%s'",
                attempt_provider_name,
            )
        except Exception as e:
            logger.error(
                "Stage 3 [Provider Manager] Failed to resolve provider '%s': %s",
                attempt_provider_name,
                str(e),
            )
            last_error = AppProviderError(str(e), provider=attempt_provider_name)
            continue

        # Determine model for this provider
        model_for_attempt = routing_decision.model
        if attempt_provider_name != primary_provider_name:
            # Use fallback policy mapping
            model_policies = routing_engine._model_policy_mapping.get(attempt_provider_name, {})
            effective_policy = request.routing_policy
            if intent_result.complexity == "simple":
                effective_policy = "speed"
            elif intent_result.complexity == "complex":
                effective_policy = "quality"
            model_for_attempt = model_policies.get(effective_policy, "balanced")

        # Retry loop for connection/timeout issues (up to 3 times)
        max_retries = 3
        success = False
        for retry in range(1, max_retries + 1):
            try:
                logger.info(
                    "Stage 4 [Provider Call]: Calling %s API... (Model: %s) (Attempt %d/%d)",
                    attempt_provider_name.capitalize(),
                    model_for_attempt,
                    retry,
                    max_retries
                )
                start_call_time = time.perf_counter()
                provider_response = provider.generate_response(
                    prompt=request.message, model=model_for_attempt
                )
                latency = (time.perf_counter() - start_call_time) * 1000.0
                
                logger.info(
                    "Stage 4 [Provider Call]: %s response received. Latency: %.2f ms, "
                    "Tokens: %d prompt / %d completion / %d total",
                    attempt_provider_name.capitalize(),
                    provider_response.get("latency_ms", 0),
                    provider_response.get("usage", {}).get("prompt_tokens", 0),
                    provider_response.get("usage", {}).get("completion_tokens", 0),
                    provider_response.get("usage", {}).get("total_tokens", 0),
                )
                
                # Update health outcomes
                await health_monitor.record_call_success(attempt_provider_name, latency)
                selected_provider_name = attempt_provider_name
                selected_model_name = model_for_attempt
                
                # Update routing decision details dynamically for final packaging
                routing_decision.provider = attempt_provider_name
                routing_decision.model = model_for_attempt
                routing_decision.fallback_status = used_fallback
                if used_fallback:
                    routing_decision.reason = (
                        f"Primary provider '{primary_provider_name}' failed. "
                        f"Automatically fell back to '{attempt_provider_name}'."
                    )
                    routing_decision.confidence = 70.0
                
                last_error = None
                success = True
                break
            except ProviderAuthenticationError as e:
                logger.error("Authentication error for provider %s: %s", attempt_provider_name, str(e))
                last_error = AuthenticationError(str(e), provider=attempt_provider_name)
                # Disable temporarily for 5 minutes
                await health_monitor.disable_provider_temporarily(attempt_provider_name, 300)
                break  # Switch provider immediately
            except ProviderConnectionError as e:
                logger.warning(
                    "Connection/Timeout on try %d for provider %s: %s",
                    retry, attempt_provider_name, str(e)
                )
                last_error = TimeoutError(str(e), provider=attempt_provider_name)
                if retry == max_retries:
                    await health_monitor.record_call_failure(attempt_provider_name)
            except ProviderAPIError as e:
                logger.error("API error for provider %s: %s", attempt_provider_name, str(e))
                if "rate limit" in str(e).lower() or "429" in str(e).lower():
                    last_error = RateLimitError(str(e), provider=attempt_provider_name)
                else:
                    last_error = AppProviderError(str(e), provider=attempt_provider_name)
                await health_monitor.record_call_failure(attempt_provider_name)
                break  # Switch provider immediately
            except Exception as e:
                logger.error("Unexpected error for provider %s: %s", attempt_provider_name, str(e))
                last_error = AppProviderError(str(e), provider=attempt_provider_name)
                await health_monitor.record_call_failure(attempt_provider_name)
                break  # Switch provider immediately

        if success:
            break

    # If all provider attempts failed, raise FallbackError
    if provider_response is None or not selected_provider_name:
        logger.error("ALL providers failed. Raising FallbackError.")
        raise FallbackError(
            f"All provider attempts failed. Last error: {last_error}",
            provider=primary_provider_name
        )

    # 5. Response Packaging
    total_processing_time = int((time.perf_counter() - start_time) * 1000)

    # Calculate cost using centralized pricing table and extract token usage
    usage_data = provider_response.get("usage") or {}
    prompt_tokens = usage_data.get("prompt_tokens", 0)
    completion_tokens = usage_data.get("completion_tokens", 0)
    total_tokens = usage_data.get("total_tokens", 0)

    selected_model_name = provider_response.get(
        "selected_model", routing_decision.model
    )
    latency_ms = provider_response.get("latency_ms", float(total_processing_time))

    from app.config.pricing import calculate_cost_usd

    estimated_cost_usd = calculate_cost_usd(selected_model_name, total_tokens)

    # Dynamic metrics calculation
    latency_index = max(0, min(100, int(100 - (latency_ms / 50.0))))

    if latency_ms < 500:
        response_speed = "Extremely Fast"
    elif latency_ms < 1000:
        response_speed = "Very Fast"
    elif latency_ms < 2500:
        response_speed = "Fast"
    else:
        response_speed = "Normal"

    cost_efficiency_mapping = {
        "gemini-1.5-flash": 98,
        "gemini-2.5-flash": 98,
        "gemini-1.5-pro": 85,
        "gemini-2.5-pro": 85,
        "llama-3.3": 92,
        "llama-3.1": 97,
        "cohere": 100,
        "north-mini-code": 100,
    }
    cost_efficiency = 80  # Default fallback
    model_lower = selected_model_name.lower()
    for key, score in cost_efficiency_mapping.items():
        if key in model_lower:
            cost_efficiency = score
            break

    intent_match = int(intent_result.confidence)

    # Calculate response quality based on model capability
    response_quality = 90  # Default fallback
    model_lower = selected_model_name.lower()
    if "llama" in model_lower:
        if "3.3" in model_lower or "70b" in model_lower:
            response_quality = 94
        else:
            response_quality = 88  # Llama 3.1 8b
    elif "gemini" in model_lower:
        if "pro" in model_lower:
            response_quality = 96
        else:
            response_quality = 91
    elif "cohere" in model_lower or "north-mini-code" in model_lower:
        response_quality = 89

    composite_score = int(
        (intent_match + latency_index + cost_efficiency + response_quality) / 4
    )

    provider_entity_mapping = {
        "gemini": "Gemini",
        "groq": "Groq",
        "nvidia": "NVIDIA NIM",
        "openrouter": "OpenRouter",
    }
    provider_key = provider_response.get("provider", routing_decision.provider).lower()
    provider_entity = provider_entity_mapping.get(
        provider_key, provider_key.capitalize()
    )

    fallbacks_evaluated = [
        provider_entity_mapping.get(p.lower(), p.capitalize())
        for p in registered_providers
        if p.lower() != provider_key
    ]

    logger.info(
        "Stage 5 [Pipeline Finished]: Successfully routed and processed. Total Latency: %d ms",
        total_processing_time,
    )

    # Output highly visible terminal telemetry block for hackathon demo
    logger.info(
        "\n"
        "=================== ROUTEMIND TELEMETRY ===================\n"
        f"  Detected Intent:     {intent_result.intent.upper()}\n"
        f"  Routing Policy:      {request.routing_policy.upper()}\n"
        f"  Chosen Provider:     {provider_entity}\n"
        f"  Chosen Model:        {selected_model_name}\n"
        f"  Fallback Used:       {'YES' if routing_decision.fallback_status else 'NO'}\n"
        f"  Latency:             {latency_ms:.2f} ms\n"
        f"  Token Usage:         Prompt: {prompt_tokens} | Completion: {completion_tokens} | Total: {total_tokens}\n"
        f"  API Cost Estimate:   ${estimated_cost_usd:.8f}\n"
        f"  Response Success:    {last_error is None}\n"
        "==========================================================="
    )

    return ChatResponse(
        # Response content
        content=provider_response.get("response", ""),
        conversation_id=request.conversation_id or "conv_routed_default",
        attachments=request.attachments,
        # Routing decision
        intent=intent_result.intent,
        provider=provider_key,
        selected_model=selected_model_name,
        routing_policy=request.routing_policy,
        confidence=intent_result.confidence,
        reason=routing_decision.reason,
        routing_reason=routing_decision.reason,
        fallback_used=used_fallback,
        complexity=intent_result.complexity,
        # Performance metrics
        latency_ms=latency_ms,
        processing_time_ms=total_processing_time,
        estimated_cost_usd=estimated_cost_usd,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        # Evaluation scores
        intent_match=intent_match,
        response_quality=response_quality,
        latency_index=latency_index,
        cost_efficiency=cost_efficiency,
        composite_score=composite_score,
        response_speed=response_speed,
        context_length=total_tokens,
        # Provider display
        provider_entity=provider_entity,
        model_version=selected_model_name,
        fallbacks_evaluated=fallbacks_evaluated,
        # Metadata
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        status="success",
        api_version=settings.VERSION,
        # Compatibility fields
        success=True,
        response=provider_response.get("response", ""),
        estimated_cost=estimated_cost_usd,
        usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
        routing_metadata={
            "response_quality": response_quality,
            "composite_score": composite_score,
            "response_speed": response_speed,
            "fallbacks_evaluated": fallbacks_evaluated,
        },
    )


# ----------------------------------------------------------------------
# DATA FLOW EXPLANATION
# ----------------------------------------------------------------------
# The RouteMind data flows through the backend pipeline as follows:
#
# 1. Input Ingestion & Validation:
#    FastAPI receives the client HTTP POST payload and validates it against the `ChatRequest` schema.
#
# 2. Intent Classification:
#    The raw prompt message string is passed to `RuleBasedIntentClassifier.classify()`.
#    Heuristic rules analyze keywords and return an `IntentResult` (intent type, confidence, matches).
#
# 3. Provider Routing:
#    The `LLMRouter` consumes the classified intent, the client's routing policy, and the active
#    provider names. It determines the target provider and model, returning a `RoutingDecision`.
#
# 4. Provider Selection:
#    The `ProviderManager` matches the selected provider name to its adapter class and returns
#    a cached instance (lazy-loading it if necessary).
#
# 5. Model Execution:
#    The controller calls `provider.generate_response()`. If external APIs are unavailable or
#    unimplemented, the controller gracefully falls back to a structured mock text generator.
#
# 6. Response Serialization:
#    The controller wraps the response, selected model, routing metrics, and calculated costs
#    into a `ChatResponse` schema which FastAPI automatically parses and returns as standard JSON.
# ----------------------------------------------------------------------

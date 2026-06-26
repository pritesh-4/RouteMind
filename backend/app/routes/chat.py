"""
Chat routing endpoint orchestrating the RouteMind AI routing pipeline.
"""

import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.config import settings
from app.schemas import ChatRequest, ChatResponse
from app.schemas.chat import (
    ResponseDetail,
    RoutingDetail,
    MetadataDetail,
    RoutingMetrics,
)
from app.classifier import BaseIntentClassifier, RuleBasedIntentClassifier
from app.services import ProviderManager, LLMRouter, RoutingError
from app.providers import ProviderError

logger = logging.getLogger("routemind.routes.chat")
router = APIRouter()


# Dependency Injection Providers
def get_classifier() -> BaseIntentClassifier:
    """Dependency injection helper returning the registered Intent Classifier."""
    return RuleBasedIntentClassifier()


def get_router() -> LLMRouter:
    """Dependency injection helper returning the registered LLMRouter."""
    return LLMRouter()


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
        )
        logger.info(
            "Stage 2 [Router]: Route selected: Provider '%s', Model '%s'. Reason: %s",
            routing_decision.provider,
            routing_decision.model,
            routing_decision.reason,
        )
    except RoutingError as e:
        logger.error("Stage 2 [Router] Failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Routing decision failed: {e}",
        )
    except Exception as e:
        logger.error("Stage 2 [Router] Unexpected Failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected routing error occurred: {e}",
        )

    # 3. Provider Resolution & Execution Stage with cross-provider failover
    # If the primary provider fails, automatically retry with the alternate provider.
    # Only return a graceful fallback message if BOTH providers fail.
    primary_provider_name = routing_decision.provider
    alternate_provider_name = "gemini" if primary_provider_name == "groq" else "groq"

    provider_response: Dict[str, Any] = {}
    used_fallback = False
    last_error = None

    for attempt_provider_name in [primary_provider_name, alternate_provider_name]:
        try:
            provider = provider_mgr.get_provider(attempt_provider_name)
            logger.info(
                "Stage 3 [Provider Manager]: Resolved provider instance for '%s'",
                attempt_provider_name,
            )
        except ValueError as e:
            logger.error(
                "Stage 3 [Provider Manager] Failed to resolve provider '%s': %s",
                attempt_provider_name,
                str(e),
            )
            last_error = e
            continue

        try:
            # Determine model for this provider
            model_for_attempt = routing_decision.model
            if attempt_provider_name != primary_provider_name:
                # Use the fallback provider's default model
                model_policies = routing_engine._model_policy_mapping.get(
                    attempt_provider_name, {}
                )
                model_for_attempt = model_policies.get(
                    request.routing_policy, "default"
                )
                used_fallback = True

            logger.info(
                "Stage 4 [Provider Call]: Calling %s API... (Model: %s)",
                attempt_provider_name.capitalize(),
                model_for_attempt,
            )
            provider_response = provider.generate_response(
                prompt=request.message, model=model_for_attempt
            )
            logger.info(
                "Stage 4 [Provider Call]: %s response received. Latency: %.2f ms, "
                "Tokens: %d prompt / %d completion / %d total",
                attempt_provider_name.capitalize(),
                provider_response.get("latency_ms", 0),
                provider_response.get("usage", {}).get("prompt_tokens", 0),
                provider_response.get("usage", {}).get("completion_tokens", 0),
                provider_response.get("usage", {}).get("total_tokens", 0),
            )

            # Update routing decision if we fell back
            if used_fallback:
                routing_decision = routing_engine.select_route(
                    intent=intent_result.intent,
                    routing_policy=request.routing_policy,
                    available_providers=[attempt_provider_name],
                )
                routing_decision.reason = (
                    f"Primary provider '{primary_provider_name}' failed. "
                    f"Automatically fell back to '{attempt_provider_name}'."
                )
                routing_decision.confidence = 70.0
                routing_decision.fallback_status = True

            last_error = None
            break  # Success — exit the retry loop

        except (ProviderError, NotImplementedError) as e:
            logger.warning(
                "Stage 4 [Provider Call]: %s call failed (%s). Trying fallback...",
                attempt_provider_name.capitalize(),
                str(e),
            )
            last_error = e
            continue

        except Exception as e:
            logger.error(
                "Stage 4 [Provider Call]: Unexpected error from %s: %s",
                attempt_provider_name.capitalize(),
                str(e),
            )
            last_error = e
            continue

    # If BOTH providers failed, return graceful fallback (never crash)
    if last_error is not None:
        logger.error(
            "Stage 4 [Provider Call]: ALL providers failed. Returning graceful fallback. Last error: %s",
            str(last_error),
        )
        fallback_latency = (time.perf_counter() - start_time) * 1000
        routing_decision.fallback_status = True
        provider_response = {
            "response": (
                "I'm sorry, both AI providers (Gemini and Groq) are temporarily unavailable. "
                "Please check your API keys and try again shortly.\n\n"
                f"Your prompt was classified as **{intent_result.intent}** "
                f"(confidence: {intent_result.confidence}%) "
                f"and would have been routed to **{primary_provider_name}**."
            ),
            "selected_model": routing_decision.model,
            "provider": routing_decision.provider,
            "latency_ms": fallback_latency,
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }

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
        "gpt-4o-mini": 96,
        "gpt-4o": 75,
        "claude-3-5-sonnet": 70,
        "claude-3-5-haiku": 90,
        "gemini-1.5-flash": 98,
        "gemini-2.5-flash": 98,
        "gemini-1.5-pro": 85,
        "gemini-2.5-pro": 85,
        "llama-3.3": 92,
        "llama-3.1": 97,
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

    composite_score = int(
        (intent_match + latency_index + cost_efficiency + response_quality) / 4
    )

    provider_entity_mapping = {
        "gemini": "Gemini",
        "openai": "OpenAI",
        "claude": "Claude",
        "groq": "Groq",
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

    metrics_detail = RoutingMetrics(
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        intent_match=intent_match,
        response_quality=response_quality,
        latency_index=latency_index,
        cost_efficiency=cost_efficiency,
        composite_score=composite_score,
        response_speed=response_speed,
        context_length=total_tokens,
        fallbacks_evaluated=fallbacks_evaluated,
        provider_entity=provider_entity,
        model_version=selected_model_name,
    )

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

    response_detail = ResponseDetail(
        content=provider_response.get("response", ""),
        conversation_id=request.conversation_id or "conv_routed_default",
        attachments=request.attachments,
    )

    routing_detail = RoutingDetail(
        intent=intent_result.intent,
        provider=provider_key,
        selected_model=selected_model_name,
        routing_policy=request.routing_policy,
        confidence=intent_result.confidence,
        reason=routing_decision.reason,
        fallback_status=routing_decision.fallback_status,
        estimated_cost=estimated_cost_usd,
        processing_time_ms=total_processing_time,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        routing_reason=routing_decision.reason,
        metrics=metrics_detail,
    )

    metadata_detail = MetadataDetail(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).isoformat(),
        status="success",
        api_version=settings.VERSION,
    )

    return ChatResponse(
        response=response_detail, routing=routing_detail, metadata=metadata_detail
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

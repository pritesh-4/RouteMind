"""
Pydantic schemas for Chat requests and responses.
Defines production-ready validation, descriptions, and examples.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


class ChatRequest(BaseModel):
    """
    Schema for incoming chat routing requests.
    Validates input parameters and supports customizable routing policy preferences.
    """

    message: str = Field(
        ...,
        min_length=1,
        description="The chat message to analyze and route.",
        examples=["What is the runtime complexity of bubble sort?"],
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the chat conversation thread.",
        examples=["conv_8f3a9e2d"],
    )
    routing_policy: Literal["balanced", "speed", "cost", "quality"] = Field(
        default="balanced",
        description="The routing policy preference to optimize AI model selection.",
        examples=["quality"],
    )
    attachments: Optional[List[str]] = Field(
        default=None,
        description="Optional list of attachment URLs or base64 resource identifiers associated with the message.",
        examples=[["https://example.com/image.png"]],
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the user initiating the request.",
        examples=["usr_9x12bc8f"],
    )
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 formatted UTC timestamp of when the request was initiated.",
        examples=["2026-06-25T15:41:00Z"],
    )

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, value: str) -> str:
        """
        Validate that the message is not just whitespaces.
        """
        if not value.strip():
            raise ValueError("Message cannot be empty or consist only of whitespace.")
        return value


class TokenUsage(BaseModel):
    """
    Schema for token utilization metrics.
    """
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)


class ChatResponse(BaseModel):
    """
    Flat schema for the response returned by RouteMind.
    All fields are top-level for simple, direct frontend consumption.
    No nested sub-objects — every metric is immediately accessible.
    """

    # --- Response Content ---
    content: str = Field(
        ...,
        description="The generated textual response from the selected AI model.",
        examples=["Bubble sort has a worst-case runtime complexity of O(n^2)."],
    )
    conversation_id: str = Field(
        ...,
        description="The conversation identifier associated with this response.",
        examples=["conv_8f3a9e2d"],
    )
    attachments: Optional[List[str]] = Field(
        default=None,
        description="Optional list of attachments associated with this response.",
    )

    # --- Routing Decision ---
    intent: str = Field(
        ...,
        description="The classified intent/category of the message.",
        examples=["coding"],
    )
    provider: str = Field(
        ...,
        description="The AI provider hosting the selected model.",
        examples=["groq"],
    )
    selected_model: str = Field(
        ...,
        description="The specific AI model that processed the request.",
        examples=["llama-3.3-70b-versatile"],
    )
    routing_policy: str = Field(
        ...,
        description="The optimization policy requested by the user.",
        examples=["balanced"],
    )
    confidence: float = Field(
        ...,
        description="The confidence score (0.0 to 100.0) of the routing decision.",
        examples=[95.0],
        ge=0.0,
        le=100.0,
    )
    reason: str = Field(
        ...,
        description="Explaining rationale for why this model and provider were selected.",
        examples=["Selected Llama-3.3-70b-versatile on Groq for high-quality reasoning."],
    )
    routing_reason: str = Field(
        ...,
        description="Explainability logic for routing (alias for reason).",
        examples=["Selected due to optimal intent match and cost efficiency."],
    )
    fallback_used: bool = Field(
        default=False,
        description="Whether a fallback provider was used due to primary provider failure.",
    )
    complexity: str = Field(
        default="medium",
        description="The estimated complexity of the user request.",
        examples=["medium"],
    )

    # --- Performance Metrics ---
    latency_ms: float = Field(
        ...,
        description="The provider API call latency in milliseconds.",
        examples=[342.1],
        ge=0.0,
    )
    processing_time_ms: int = Field(
        ...,
        description="The total end-to-end processing time in milliseconds.",
        examples=[500],
        ge=0,
    )
    estimated_cost_usd: float = Field(
        ...,
        description="Estimated cost in USD calculated using pricing table.",
        examples=[0.00009],
        ge=0.0,
    )
    prompt_tokens: int = Field(
        ...,
        description="Tokens used in the prompt.",
        examples=[158],
        ge=0,
    )
    completion_tokens: int = Field(
        ...,
        description="Tokens used in the completion.",
        examples=[311],
        ge=0,
    )
    total_tokens: int = Field(
        ...,
        description="Total tokens used.",
        examples=[469],
        ge=0,
    )

    # --- Evaluation Scores ---
    intent_match: int = Field(
        ...,
        description="Intent match confidence (0 to 100).",
        examples=[95],
        ge=0,
        le=100,
    )
    response_quality: Optional[int] = Field(
        default=None,
        description="Objective response quality score (0 to 100).",
        examples=[90],
        ge=0,
        le=100,
    )
    latency_index: int = Field(
        ...,
        description="Latency converted to a 0-100 score.",
        examples=[92],
        ge=0,
        le=100,
    )
    cost_efficiency: int = Field(
        ...,
        description="Cost efficiency score (0 to 100) based on pricing.",
        examples=[98],
        ge=0,
        le=100,
    )
    composite_score: int = Field(
        ...,
        description="Composite score computed from available metrics.",
        examples=[94],
        ge=0,
        le=100,
    )
    response_speed: str = Field(
        ...,
        description="Speed description string.",
        examples=["Very Fast"],
    )
    context_length: int = Field(
        ...,
        description="Context length (total tokens).",
        examples=[469],
        ge=0,
    )

    # --- Provider Display ---
    provider_entity: str = Field(
        ...,
        description="User-friendly name of the provider.",
        examples=["Gemini"],
    )
    model_version: str = Field(
        ...,
        description="The actual model version selected.",
        examples=["gemini-2.5-flash"],
    )
    fallbacks_evaluated: List[str] = Field(
        ...,
        description="List of other providers evaluated by the router.",
        examples=[["Groq", "NVIDIA NIM"]],
    )

    # --- Metadata ---
    request_id: str = Field(
        ...,
        description="Unique identifier for this request execution.",
        examples=["req_d3f28a9b7"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of when the response was generated.",
        examples=["2026-06-25T15:41:00Z"],
    )
    status: str = Field(
        default="success",
        description="Status string indicating success or partial failure.",
        examples=["success"],
    )
    api_version: str = Field(
        ...,
        description="The version of the RouteMind API processing the request.",
        examples=["1.0.0"],
    )

    # --- Alias/Extra Flat Fields for Compatibility ---
    success: bool = Field(
        default=True,
        description="Indicates if the request was processed successfully.",
    )
    response: str = Field(
        default="",
        description="The generated textual response from the selected AI model (alias for content).",
    )
    estimated_cost: float = Field(
        default=0.0,
        description="Estimated cost in USD (alias for estimated_cost_usd).",
    )
    usage: Optional[TokenUsage] = Field(
        default=None,
        description="Detailed token usage details.",
    )
    routing_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata dictionary for additional routing parameters.",
    )

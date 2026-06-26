"""
Pricing configuration and calculation for RouteMind.
"""

# Price per token (USD) for each model based on standard rates
PRICING_TABLE = {
    "gpt-4o-mini": 0.00000015,
    "gpt-4o": 0.0000025,
    "claude-3-5-sonnet": 0.000003,
    "claude-3-5-haiku": 0.0000008,
    "gemini-1.5-flash": 0.000000075,
    "gemini-2.5-flash": 0.000000075,
    "gemini-1.5-pro": 0.00000125,
    "gemini-2.5-pro": 0.00000125,
    "llama-3.3-70b-versatile": 0.0000007,
    "llama-3.1-8b-instant": 0.00000005,
}

DEFAULT_PRICE_PER_TOKEN = 0.000015  # Fallback price per token in USD


def calculate_cost_usd(model: str, total_tokens: int) -> float:
    """
    Calculate the estimated cost in USD based on total tokens and model pricing.
    """
    if not model:
        return round(total_tokens * DEFAULT_PRICE_PER_TOKEN, 8)

    model_lower = model.lower()
    price_per_token = DEFAULT_PRICE_PER_TOKEN

    for key, price in PRICING_TABLE.items():
        if key in model_lower:
            price_per_token = price
            break

    return round(total_tokens * price_per_token, 8)

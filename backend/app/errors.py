"""
Custom exceptions module for RouteMind.
Defines a unified exception hierarchy to manage provider errors, routing errors, and validation errors.
"""

class BaseRouteMindError(Exception):
    """Base class for all exceptions originating in RouteMind."""
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", provider: str = "system"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.provider = provider


class ProviderError(BaseRouteMindError):
    """Base exception class for all errors originating in the provider layer."""
    def __init__(self, message: str, error_code: str = "PROVIDER_ERROR", provider: str = "unknown"):
        super().__init__(message, error_code, provider)


class AuthenticationError(ProviderError):
    """Raised when authentication credentials (e.g., API keys) are invalid or missing."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message, "AUTHENTICATION_ERROR", provider)


class RateLimitError(ProviderError):
    """Raised when an API request returns a rate limit exceeded status code."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message, "RATE_LIMIT_ERROR", provider)


class TimeoutError(ProviderError):
    """Raised when request times out or is blocked by network connectivity issues."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message, "TIMEOUT_ERROR", provider)


class ValidationError(BaseRouteMindError):
    """Raised when request payload validation fails validation checks."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", "system")


class RoutingError(BaseRouteMindError):
    """Raised when the routing engine is unable to make a valid routing decision."""
    def __init__(self, message: str):
        super().__init__(message, "ROUTING_ERROR", "system")


class FallbackError(BaseRouteMindError):
    """Raised when both primary and secondary fallback providers fail to fulfill the request."""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(message, "FALLBACK_ERROR", provider)

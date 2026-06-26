"""
Unit and integration tests for RouteMind's production readiness architecture.
Tests retries, timeouts, rate limits, health monitoring, and unified exception formats.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.errors import (
    RoutingError,
)
from app.services.health_monitor import health_monitor


@pytest.fixture
def client():
    return TestClient(app)


class TestUnifiedExceptions:
    """Tests that custom exceptions are mapped correctly and standard structures are returned."""

    def test_routemind_custom_error_formatting(self, client):
        # We trigger a routing error during execution using dependency overrides
        from app.routes.chat import get_router
        
        mock_router = MagicMock()
        mock_router.select_route.side_effect = RoutingError("Routing failure mock")
        
        app.dependency_overrides[get_router] = lambda: mock_router
        try:
            response = client.post("/chat", json={"message": "hello"})
            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert data["error_code"] == "ROUTING_ERROR"
            assert "message" in data
            assert data["fallback_used"] is True
            assert "request_id" in data
        finally:
            app.dependency_overrides.pop(get_router, None)

    def test_validation_error_formatting(self, client):
        # Standard input validation error
        response = client.post("/chat", json={})
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "request_id" in data


class TestRetryAndFallbackOrchestration:
    """Tests the retry loops and transient error mappings."""

    @patch("app.routes.chat.ProviderManager.get_provider")
    def test_transient_connection_error_retries(self, mock_get_provider):
        # Mock provider to raise ProviderConnectionError twice, and succeed on the third attempt.
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider
        
        from app.providers import ProviderConnectionError
        mock_provider.generate_response.side_effect = [
            ProviderConnectionError("Connection timeout transient"),
            ProviderConnectionError("Connection timeout transient 2"),
            {"response": "Success response", "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}}
        ]
        
        client_test = TestClient(app)
        response = client_test.post("/chat", json={"message": "debug my python function"})
        
        assert response.status_code == 200
        assert response.json()["content"] == "Success response"

    @patch("app.routes.chat.ProviderManager.get_provider")
    def test_rate_limit_switches_provider(self, mock_get_provider):
        # Mock primary provider (Groq) to raise ProviderAPIError (Rate limit)
        # Should switch to fallback (OpenRouter or Gemini)
        mock_groq = MagicMock()
        from app.providers import ProviderAPIError
        mock_groq.generate_response.side_effect = ProviderAPIError("Rate Limit 429 exceeded")
        
        mock_gemini = MagicMock()
        mock_gemini.generate_response.return_value = {
            "response": "Fallback gemini answer",
            "usage": {"prompt_tokens": 2, "completion_tokens": 4, "total_tokens": 6}
        }
        
        def get_provider_side_effect(name):
            if name == "groq":
                return mock_groq
            return mock_gemini
            
        mock_get_provider.side_effect = get_provider_side_effect
        
        client_test = TestClient(app)
        response = client_test.post("/chat", json={"message": "debug python"})
        assert response.status_code == 200
        assert response.json()["content"] == "Fallback gemini answer"


class TestHealthMonitorService:
    """Tests for the Background HealthMonitor."""

    def test_health_monitor_basic_tracking(self):
        import asyncio

        async def run_test():
            # Verify status updates and transitions
            await health_monitor.record_health_outcome("gemini", True, 45.0)
            assert health_monitor.is_provider_healthy("gemini") is True
            assert health_monitor.get_latency("gemini") == 83.5
            
            # Record failure
            await health_monitor.record_call_failure("gemini")
            await health_monitor.record_call_failure("gemini")
            await health_monitor.record_call_failure("gemini")
            # consecutive_failures >= 3 makes it unhealthy
            assert health_monitor.is_provider_healthy("gemini") is False
            
            # Reset health
            await health_monitor.record_call_success("gemini", 30.0)
            assert health_monitor.is_provider_healthy("gemini") is True

        asyncio.run(run_test())

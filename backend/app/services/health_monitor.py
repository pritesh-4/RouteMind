"""
Background health tracking service for RouteMind.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("routemind.services.health_monitor")


class ProviderStatus(BaseModel):
    """
    Status of an LLM provider tracked by the HealthMonitor.
    """
    provider: str
    is_healthy: bool
    latency_ms: float
    last_checked: datetime
    error_count: int
    consecutive_failures: int = 0
    temp_disabled_until: Optional[datetime] = None


class HealthMonitor:
    """
    Service that monitors provider status, calculates error counts, latencies,
    and runs a background task to refresh statuses every 60 seconds.
    """
    _instance: Optional["HealthMonitor"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, provider_manager=None) -> None:
        if self._initialized:
            return
        self.provider_manager = provider_manager
        self.statuses: Dict[str, ProviderStatus] = {}
        self.historical_success: Dict[str, int] = {}
        self.historical_total: Dict[str, int] = {}
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._initialized = True

    def set_provider_manager(self, provider_manager):
        """Sets the provider manager dependency dynamically to prevent circular imports."""
        self.provider_manager = provider_manager
        # Initialize status for registered providers
        for p in provider_manager.list_registered_providers():
            if p not in self.statuses:
                self.statuses[p] = ProviderStatus(
                    provider=p,
                    is_healthy=True,  # assume healthy initially
                    latency_ms=100.0,  # baseline estimate
                    last_checked=datetime.now(timezone.utc),
                    error_count=0,
                )
                self.historical_success[p] = 1
                self.historical_total[p] = 1

    async def start(self):
        """Starts the background tracking loop."""
        if self._task is None:
            self._task = asyncio.create_task(self._monitoring_loop())
            logger.info("Background HealthMonitor loop started.")

    async def stop(self):
        """Stops the background tracking loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Background HealthMonitor loop stopped.")

    async def _monitoring_loop(self):
        while True:
            try:
                await self.check_all_providers()
            except Exception as e:
                logger.error("Error checking provider health in loop: %s", str(e))
            await asyncio.sleep(60.0)

    async def check_all_providers(self):
        """Runs check_availability for all registered providers and updates status."""
        if not self.provider_manager:
            return

        providers = self.provider_manager.list_registered_providers()
        for p in providers:
            await self.check_provider_health_async(p)

    async def check_provider_health_async(self, provider_name: str):
        """Runs health_check in executor and updates local stats."""
        p_name = provider_name.strip().lower()
        if not self.provider_manager:
            return

        try:
            loop = asyncio.get_running_loop()
            # check health in background thread
            start_time = asyncio.get_event_loop().time()
            
            # Resolve provider instance
            provider_inst = self.provider_manager.get_provider(p_name)
            is_healthy = await loop.run_in_executor(None, provider_inst.health_check)
            
            end_time = asyncio.get_event_loop().time()
            latency = (end_time - start_time) * 1000.0
            
            await self.record_health_outcome(p_name, is_healthy, latency)
        except Exception as e:
            logger.error("Failed health check for provider %s: %s", p_name, str(e))
            await self.record_health_outcome(p_name, False, 1000.0)

    async def record_health_outcome(self, provider_name: str, is_healthy: bool, latency: float):
        """Updates internal status atomically."""
        p_name = provider_name.strip().lower()
        async with self._lock:
            status = self.statuses.get(p_name)
            now = datetime.now(timezone.utc)
            if not status:
                status = ProviderStatus(
                    provider=p_name,
                    is_healthy=is_healthy,
                    latency_ms=latency,
                    last_checked=now,
                    error_count=0 if is_healthy else 1,
                    consecutive_failures=0 if is_healthy else 1,
                )
                self.statuses[p_name] = status
            else:
                status.is_healthy = is_healthy
                status.latency_ms = (status.latency_ms * 0.7) + (latency * 0.3)  # EMA latency
                status.last_checked = now
                if is_healthy:
                    status.consecutive_failures = 0
                else:
                    status.consecutive_failures += 1
                    status.error_count += 1
                    
            logger.debug(
                "HealthMonitor updated for %s: is_healthy=%s, latency=%.2f ms, consecutive_failures=%d",
                p_name, status.is_healthy, status.latency_ms, status.consecutive_failures
            )

    async def record_call_success(self, provider_name: str, latency: float):
        """Records a successful LLM call outcome."""
        p_name = provider_name.strip().lower()
        async with self._lock:
            self.historical_total[p_name] = self.historical_total.get(p_name, 0) + 1
            self.historical_success[p_name] = self.historical_success.get(p_name, 0) + 1
            
            status = self.statuses.get(p_name)
            if status:
                status.is_healthy = True
                status.consecutive_failures = 0
                status.latency_ms = (status.latency_ms * 0.8) + (latency * 0.2)  # EMA latency
                status.last_checked = datetime.now(timezone.utc)

    async def record_call_failure(self, provider_name: str):
        """Records a failed LLM call outcome."""
        p_name = provider_name.strip().lower()
        async with self._lock:
            self.historical_total[p_name] = self.historical_total.get(p_name, 0) + 1
            
            status = self.statuses.get(p_name)
            if status:
                status.consecutive_failures += 1
                status.error_count += 1
                status.last_checked = datetime.now(timezone.utc)
                if status.consecutive_failures >= 3:
                    status.is_healthy = False

    async def disable_provider_temporarily(self, provider_name: str, duration_seconds: int = 300):
        """Disables a provider temporarily (e.g. for authentication/severe errors)."""
        p_name = provider_name.strip().lower()
        async with self._lock:
            status = self.statuses.get(p_name)
            if status:
                now = datetime.now(timezone.utc)
                status.temp_disabled_until = now + timedelta(seconds=duration_seconds)
                status.is_healthy = False
                logger.warning("Provider %s disabled temporarily for %d seconds.", p_name, duration_seconds)

    def is_provider_healthy(self, provider_name: str) -> bool:
        """Returns whether a provider is healthy and not temporarily disabled."""
        p_name = provider_name.strip().lower()
        status = self.statuses.get(p_name)
        if not status:
            return True  # default to true if untracked
        
        # Check temp disable
        if status.temp_disabled_until:
            now = datetime.now(timezone.utc)
            if now < status.temp_disabled_until:
                return False
            else:
                # Disable period has expired, reset it
                status.temp_disabled_until = None
                status.is_healthy = True
                status.consecutive_failures = 0

        return status.is_healthy

    def get_latency(self, provider_name: str) -> float:
        """Gets last tracked or estimated latency for provider."""
        status = self.statuses.get(provider_name.strip().lower())
        return status.latency_ms if status else 150.0

    def get_historical_success_rate(self, provider_name: str) -> float:
        """Gets the historical success rate between 0.0 and 1.0."""
        p_name = provider_name.strip().lower()
        total = self.historical_total.get(p_name, 1)
        success = self.historical_success.get(p_name, 1)
        return float(success) / float(total) if total > 0 else 1.0

    def get_healthy_providers(self) -> List[str]:
        """Gets a list of all registered provider names that are currently healthy."""
        healthy = []
        for name, status in self.statuses.items():
            if self.is_provider_healthy(name):
                healthy.append(name)
        return healthy


# Global health monitor singleton instance
health_monitor = HealthMonitor()

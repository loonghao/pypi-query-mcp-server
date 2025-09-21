"""Rate limiting implementation for external API calls."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager

import httpx

from .rate_limit_config import get_service_rate_limit, is_rate_limiting_enabled, ServiceRateLimit

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration for a service."""
    requests_per_second: float = 10.0
    burst_capacity: int = 50
    max_retries: int = 3
    backoff_factor: float = 2.0


class TokenBucket:
    """Token bucket algorithm for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket."""
        async with self._lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_time(self) -> float:
        """Calculate how long to wait before tokens are available."""
        async with self._lock:
            if self.tokens >= 1:
                return 0.0
            return (1 - self.tokens) / self.refill_rate


class RateLimiter:
    """Rate limiter with per-service token buckets."""

    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        # Service limits are now loaded from configuration
        self._load_service_limits()

    def _load_service_limits(self):
        """Load service limits from configuration."""
        self.service_limits = {}
        # Convert ServiceRateLimit to RateLimit for backwards compatibility
        for service in ["pypi", "github", "pypistats", "default", "security"]:
            config = get_service_rate_limit(service)
            self.service_limits[service] = RateLimit(
                requests_per_second=config.requests_per_second,
                burst_capacity=config.burst_capacity,
                max_retries=config.max_retries,
                backoff_factor=config.backoff_factor
            )

    def _get_bucket(self, service: str) -> TokenBucket:
        """Get or create a token bucket for a service."""
        if service not in self.buckets:
            limits = self.service_limits.get(service, self.service_limits["default"])
            self.buckets[service] = TokenBucket(
                capacity=limits.burst_capacity,
                refill_rate=limits.requests_per_second
            )
        return self.buckets[service]

    async def acquire(self, service: str) -> None:
        """Acquire permission to make a request to a service."""
        # Skip rate limiting if disabled globally
        if not is_rate_limiting_enabled():
            return

        bucket = self._get_bucket(service)

        while not await bucket.consume():
            wait_time = await bucket.wait_time()
            logger.debug(f"Rate limit hit for {service}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

    def configure_service(self, service: str, rate_limit: RateLimit) -> None:
        """Configure rate limits for a specific service."""
        self.service_limits[service] = rate_limit
        # Reset bucket to apply new limits
        if service in self.buckets:
            del self.buckets[service]


class RateLimitedClient:
    """HTTP client with built-in rate limiting."""

    def __init__(self, service: str = "default", rate_limiter: Optional[RateLimiter] = None):
        self.service = service
        self.rate_limiter = rate_limiter or RateLimiter()
        self._client: Optional[httpx.AsyncClient] = None

    @asynccontextmanager
    async def _get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        try:
            yield self._client
        finally:
            pass  # Keep client alive for reuse

    async def request(
        self,
        method: str,
        url: str,
        *,
        params=None,
        data=None,
        json=None,
        headers=None,
        **kwargs
    ) -> httpx.Response:
        """Make a rate-limited HTTP request."""
        await self.rate_limiter.acquire(self.service)

        limits = self.rate_limiter.service_limits.get(self.service, self.rate_limiter.service_limits["default"])

        for attempt in range(limits.max_retries + 1):
            try:
                async with self._get_client() as client:
                    logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        json=json,
                        headers=headers,
                        **kwargs
                    )

                    # Handle rate limit responses
                    if response.status_code == 429:
                        retry_after = self._parse_retry_after(response)
                        if attempt < limits.max_retries:
                            logger.warning(f"Rate limited by {self.service}, waiting {retry_after}s before retry")
                            await asyncio.sleep(retry_after)
                            continue

                    return response

            except (httpx.RequestError, httpx.TimeoutException) as e:
                if attempt < limits.max_retries:
                    backoff_time = limits.backoff_factor ** attempt
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {backoff_time}s: {e}")
                    await asyncio.sleep(backoff_time)
                    continue
                raise

        raise httpx.RequestError(f"Max retries ({limits.max_retries}) exceeded for {url}")

    def _parse_retry_after(self, response: httpx.Response) -> float:
        """Parse Retry-After header or use default backoff."""
        retry_after_header = response.headers.get("Retry-After")
        if retry_after_header:
            try:
                return float(retry_after_header)
            except ValueError:
                pass
        return 60.0  # Default 1 minute backoff

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def get_rate_limited_client(service: str = "default") -> RateLimitedClient:
    """Get a rate-limited HTTP client for a specific service."""
    return RateLimitedClient(service=service, rate_limiter=_global_rate_limiter)


def configure_service_limits(service: str, rate_limit: RateLimit) -> None:
    """Configure rate limits for a specific service globally."""
    _global_rate_limiter.configure_service(service, rate_limit)


def configure_service_from_config(service: str, config: ServiceRateLimit) -> None:
    """Configure rate limits for a service using ServiceRateLimit config."""
    rate_limit = RateLimit(
        requests_per_second=config.requests_per_second,
        burst_capacity=config.burst_capacity,
        max_retries=config.max_retries,
        backoff_factor=config.backoff_factor
    )
    configure_service_limits(service, rate_limit)
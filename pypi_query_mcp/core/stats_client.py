"""PyPI download statistics client using pypistats.org API."""

import asyncio
import logging
from typing import Any

import httpx

from .exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIServerError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class PyPIStatsClient:
    """Async client for PyPI download statistics API."""

    def __init__(
        self,
        base_url: str = "https://pypistats.org/api",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize PyPI stats client.

        Args:
            base_url: Base URL for pypistats API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Simple in-memory cache
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour (data updates daily)

        # HTTP client configuration
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": "pypi-query-mcp-server/0.1.0",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _validate_package_name(self, package_name: str) -> str:
        """Validate and normalize package name.

        Args:
            package_name: Package name to validate

        Returns:
            Normalized package name

        Raises:
            InvalidPackageNameError: If package name is invalid
        """
        if not package_name or not package_name.strip():
            raise InvalidPackageNameError(package_name)

        # Basic validation
        normalized = package_name.strip().lower()
        return normalized

    def _get_cache_key(self, endpoint: str, package_name: str = "", **params) -> str:
        """Generate cache key for API data."""
        param_str = "&".join(
            f"{k}={v}" for k, v in sorted(params.items()) if v is not None
        )
        return f"{endpoint}:{package_name}:{param_str}"

    def _is_cache_valid(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        import time

        return time.time() - cache_entry.get("timestamp", 0) < self._cache_ttl

    async def _make_request(self, url: str) -> dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            url: URL to request

        Returns:
            JSON response data

        Raises:
            NetworkError: For network-related errors
            PackageNotFoundError: When package is not found
            RateLimitError: When rate limit is exceeded
            PyPIServerError: For server errors
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1})")

                response = await self._client.get(url)

                # Handle different HTTP status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Extract package name from URL for better error message
                    package_name = url.split("/")[-2] if "/" in url else "unknown"
                    raise PackageNotFoundError(package_name)
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after_int = int(retry_after) if retry_after else None
                    raise RateLimitError(retry_after_int)
                elif response.status_code >= 500:
                    raise PyPIServerError(response.status_code)
                else:
                    raise PyPIServerError(
                        response.status_code,
                        f"Unexpected status code: {response.status_code}",
                    )

            except httpx.TimeoutException as e:
                last_exception = NetworkError(f"Request timeout: {e}", e)
            except httpx.NetworkError as e:
                last_exception = NetworkError(f"Network error: {e}", e)
            except (PackageNotFoundError, RateLimitError, PyPIServerError):
                # Don't retry these errors
                raise
            except Exception as e:
                last_exception = NetworkError(f"Unexpected error: {e}", e)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        # If we get here, all retries failed
        raise last_exception

    async def get_recent_downloads(
        self, package_name: str, period: str = "month", use_cache: bool = True
    ) -> dict[str, Any]:
        """Get recent download statistics for a package.

        Args:
            package_name: Name of the package to query
            period: Time period ('day', 'week', 'month')
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary containing recent download statistics

        Raises:
            InvalidPackageNameError: If package name is invalid
            PackageNotFoundError: If package is not found
            NetworkError: For network-related errors
        """
        normalized_name = self._validate_package_name(package_name)
        cache_key = self._get_cache_key("recent", normalized_name, period=period)

        # Check cache first
        if use_cache and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Using cached recent downloads for: {normalized_name}")
                return cache_entry["data"]

        # Make API request
        url = f"{self.base_url}/packages/{normalized_name}/recent"
        if period and period != "all":
            url += f"?period={period}"

        logger.info(
            f"Fetching recent downloads for: {normalized_name} (period: {period})"
        )

        try:
            data = await self._make_request(url)

            # Cache the result
            import time

            self._cache[cache_key] = {"data": data, "timestamp": time.time()}

            return data

        except Exception as e:
            logger.error(f"Failed to fetch recent downloads for {normalized_name}: {e}")
            raise

    async def get_overall_downloads(
        self, package_name: str, mirrors: bool = False, use_cache: bool = True
    ) -> dict[str, Any]:
        """Get overall download time series for a package.

        Args:
            package_name: Name of the package to query
            mirrors: Whether to include mirror downloads
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary containing overall download time series

        Raises:
            InvalidPackageNameError: If package name is invalid
            PackageNotFoundError: If package is not found
            NetworkError: For network-related errors
        """
        normalized_name = self._validate_package_name(package_name)
        cache_key = self._get_cache_key("overall", normalized_name, mirrors=mirrors)

        # Check cache first
        if use_cache and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Using cached overall downloads for: {normalized_name}")
                return cache_entry["data"]

        # Make API request
        url = f"{self.base_url}/packages/{normalized_name}/overall"
        if mirrors is not None:
            url += f"?mirrors={'true' if mirrors else 'false'}"

        logger.info(
            f"Fetching overall downloads for: {normalized_name} (mirrors: {mirrors})"
        )

        try:
            data = await self._make_request(url)

            # Cache the result
            import time

            self._cache[cache_key] = {"data": data, "timestamp": time.time()}

            return data

        except Exception as e:
            logger.error(
                f"Failed to fetch overall downloads for {normalized_name}: {e}"
            )
            raise

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        logger.debug("Stats cache cleared")

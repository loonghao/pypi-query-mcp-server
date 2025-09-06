"""GitHub API client for fetching repository statistics and popularity metrics."""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Async client for GitHub API to fetch repository statistics."""

    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        github_token: str | None = None,
    ):
        """Initialize GitHub API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            github_token: Optional GitHub API token for higher rate limits
        """
        self.base_url = "https://api.github.com"
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Simple in-memory cache for repository data
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 hour cache

        # HTTP client configuration
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "pypi-query-mcp-server/0.1.0",
        }

        if github_token:
            headers["Authorization"] = f"token {github_token}"

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=headers,
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

    def _get_cache_key(self, repo: str) -> str:
        """Generate cache key for repository data."""
        return f"repo:{repo}"

    def _is_cache_valid(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        import time

        return time.time() - cache_entry.get("timestamp", 0) < self._cache_ttl

    async def _make_request(self, url: str) -> dict[str, Any] | None:
        """Make HTTP request with retry logic and error handling.

        Args:
            url: URL to request

        Returns:
            JSON response data or None if failed
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Making GitHub API request to {url} (attempt {attempt + 1})"
                )

                response = await self._client.get(url)

                # Handle different HTTP status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"GitHub repository not found: {url}")
                    return None
                elif response.status_code == 403:
                    # Rate limit or permission issue
                    logger.warning(f"GitHub API rate limit or permission denied: {url}")
                    return None
                elif response.status_code >= 500:
                    logger.warning(
                        f"GitHub API server error {response.status_code}: {url}"
                    )
                    if attempt < self.max_retries:
                        continue
                    return None
                else:
                    logger.warning(
                        f"Unexpected GitHub API status {response.status_code}: {url}"
                    )
                    return None

            except httpx.TimeoutException:
                last_exception = f"Request timeout for {url}"
                logger.warning(last_exception)
            except httpx.NetworkError as e:
                last_exception = f"Network error for {url}: {e}"
                logger.warning(last_exception)
            except Exception as e:
                last_exception = f"Unexpected error for {url}: {e}"
                logger.warning(last_exception)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        # If we get here, all retries failed
        logger.error(
            f"Failed to fetch GitHub data after {self.max_retries + 1} attempts: {last_exception}"
        )
        return None

    async def get_repository_stats(
        self, repo_path: str, use_cache: bool = True
    ) -> dict[str, Any] | None:
        """Get repository statistics from GitHub API.

        Args:
            repo_path: Repository path in format "owner/repo"
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary containing repository statistics or None if failed
        """
        cache_key = self._get_cache_key(repo_path)

        # Check cache first
        if use_cache and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Using cached GitHub data for: {repo_path}")
                return cache_entry["data"]

        # Make API request
        url = f"{self.base_url}/repos/{repo_path}"

        try:
            data = await self._make_request(url)

            if data:
                # Extract relevant statistics
                stats = {
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "watchers": data.get("watchers_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "size": data.get("size", 0),
                    "language": data.get("language"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "pushed_at": data.get("pushed_at"),
                    "description": data.get("description"),
                    "topics": data.get("topics", []),
                    "homepage": data.get("homepage"),
                    "has_issues": data.get("has_issues", False),
                    "has_projects": data.get("has_projects", False),
                    "has_wiki": data.get("has_wiki", False),
                    "archived": data.get("archived", False),
                    "disabled": data.get("disabled", False),
                    "license": data.get("license", {}).get("name")
                    if data.get("license")
                    else None,
                }

                # Cache the result
                import time

                self._cache[cache_key] = {"data": stats, "timestamp": time.time()}

                logger.debug(
                    f"Fetched GitHub stats for {repo_path}: {stats['stars']} stars"
                )
                return stats
            else:
                return None

        except Exception as e:
            logger.error(f"Error fetching GitHub stats for {repo_path}: {e}")
            return None

    async def get_multiple_repo_stats(
        self, repo_paths: list[str], use_cache: bool = True, max_concurrent: int = 5
    ) -> dict[str, dict[str, Any] | None]:
        """Get statistics for multiple repositories concurrently.

        Args:
            repo_paths: List of repository paths in format "owner/repo"
            use_cache: Whether to use cached data if available
            max_concurrent: Maximum number of concurrent requests

        Returns:
            Dictionary mapping repo paths to their statistics
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_repo_stats(repo_path: str) -> tuple[str, dict[str, Any] | None]:
            async with semaphore:
                stats = await self.get_repository_stats(repo_path, use_cache)
                return repo_path, stats

        # Fetch all repositories concurrently
        tasks = [fetch_repo_stats(repo) for repo in repo_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        repo_stats = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error in concurrent GitHub fetch: {result}")
                continue

            repo_path, stats = result
            repo_stats[repo_path] = stats

        return repo_stats

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        logger.debug("GitHub cache cleared")

    async def get_rate_limit(self) -> dict[str, Any] | None:
        """Get current GitHub API rate limit status.

        Returns:
            Dictionary containing rate limit information
        """
        url = f"{self.base_url}/rate_limit"

        try:
            data = await self._make_request(url)
            if data:
                return data.get("rate", {})
            return None
        except Exception as e:
            logger.error(f"Error fetching GitHub rate limit: {e}")
            return None

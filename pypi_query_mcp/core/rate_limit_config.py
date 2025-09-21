"""Rate limiting configuration for different external services."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ServiceRateLimit:
    """Rate limit configuration for a specific service."""
    requests_per_second: float = 5.0
    burst_capacity: int = 15
    max_retries: int = 3
    backoff_factor: float = 2.0


@dataclass
class RateLimitConfig:
    """Global rate limiting configuration for all external services."""

    # Service-specific configurations
    service_limits: Dict[str, ServiceRateLimit] = field(default_factory=lambda: {
        # PyPI services - generous limits since PyPI doesn't enforce strict rate limiting
        "pypi": ServiceRateLimit(
            requests_per_second=10.0,
            burst_capacity=20,
            max_retries=3,
            backoff_factor=2.0
        ),

        # GitHub API - strict limits as GitHub enforces rate limiting
        "github": ServiceRateLimit(
            requests_per_second=5.0,
            burst_capacity=10,
            max_retries=3,
            backoff_factor=2.0
        ),

        # PyPI Stats API - moderate limits
        "pypistats": ServiceRateLimit(
            requests_per_second=8.0,
            burst_capacity=15,
            max_retries=3,
            backoff_factor=2.0
        ),

        # Generic fallback for other services
        "default": ServiceRateLimit(
            requests_per_second=5.0,
            burst_capacity=15,
            max_retries=3,
            backoff_factor=2.0
        ),

        # Security scanning services (if any external ones are added)
        "security": ServiceRateLimit(
            requests_per_second=3.0,
            burst_capacity=8,
            max_retries=5,
            backoff_factor=3.0
        )
    })

    # Global settings
    enable_rate_limiting: bool = True
    enable_backoff: bool = True
    log_rate_limits: bool = True
    cache_rate_limit_state: bool = True


# Global configuration instance
DEFAULT_RATE_LIMIT_CONFIG = RateLimitConfig()


def get_service_rate_limit(service_name: str) -> ServiceRateLimit:
    """Get rate limit configuration for a service."""
    config = DEFAULT_RATE_LIMIT_CONFIG
    return config.service_limits.get(service_name, config.service_limits["default"])


def update_service_rate_limit(service_name: str, rate_limit: ServiceRateLimit) -> None:
    """Update rate limit configuration for a service."""
    DEFAULT_RATE_LIMIT_CONFIG.service_limits[service_name] = rate_limit


def is_rate_limiting_enabled() -> bool:
    """Check if rate limiting is globally enabled."""
    return DEFAULT_RATE_LIMIT_CONFIG.enable_rate_limiting


def disable_rate_limiting() -> None:
    """Disable rate limiting globally (for testing)."""
    DEFAULT_RATE_LIMIT_CONFIG.enable_rate_limiting = False


def enable_rate_limiting() -> None:
    """Enable rate limiting globally."""
    DEFAULT_RATE_LIMIT_CONFIG.enable_rate_limiting = True
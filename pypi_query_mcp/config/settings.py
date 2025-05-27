"""Configuration settings for PyPI Query MCP Server."""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Server configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="PYPI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Basic server settings
    log_level: str = Field(default="INFO", description="Logging level")
    cache_ttl: int = Field(default=3600, description="Cache time-to-live in seconds")
    request_timeout: float = Field(
        default=30.0, description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    # PyPI settings
    index_url: str = Field(
        default="https://pypi.org/pypi", description="Primary PyPI index URL"
    )
    index_urls: str | None = Field(
        default=None, description="Additional PyPI index URLs (comma-separated)"
    )
    extra_index_urls: str | None = Field(
        default=None, description="Extra PyPI index URLs for fallback (comma-separated)"
    )

    # Private repository settings
    private_pypi_url: str | None = Field(
        default=None, description="Private PyPI repository URL"
    )
    private_pypi_username: str | None = Field(
        default=None, description="Private PyPI username"
    )
    private_pypi_password: str | None = Field(
        default=None, description="Private PyPI password"
    )

    # Advanced dependency analysis settings
    dependency_max_depth: int = Field(
        default=5, description="Maximum depth for recursive dependency analysis"
    )
    dependency_max_concurrent: int = Field(
        default=10, description="Maximum concurrent dependency queries"
    )
    enable_security_analysis: bool = Field(
        default=False, description="Enable security vulnerability analysis"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @field_validator("cache_ttl")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL."""
        if v < 0:
            raise ValueError("Cache TTL must be non-negative")
        return v

    @field_validator("dependency_max_depth")
    @classmethod
    def validate_dependency_max_depth(cls, v: int) -> int:
        """Validate dependency analysis max depth."""
        if v < 1 or v > 10:
            raise ValueError("Dependency max depth must be between 1 and 10")
        return v

    @field_validator("dependency_max_concurrent")
    @classmethod
    def validate_dependency_max_concurrent(cls, v: int) -> int:
        """Validate max concurrent dependency queries."""
        if v < 1 or v > 50:
            raise ValueError("Max concurrent queries must be between 1 and 50")
        return v

    def has_private_repo(self) -> bool:
        """Check if private repository is configured."""
        return bool(self.private_pypi_url)

    def has_private_auth(self) -> bool:
        """Check if private repository authentication is configured."""
        return bool(
            self.private_pypi_url
            and self.private_pypi_username
            and self.private_pypi_password
        )

    def get_all_index_urls(self) -> list[str]:
        """Get all configured index URLs in priority order."""
        urls = [self.index_url]

        # Add additional index URLs
        if self.index_urls:
            additional_urls = [
                url.strip() for url in self.index_urls.split(",") if url.strip()
            ]
            urls.extend(additional_urls)

        # Add extra index URLs (lower priority)
        if self.extra_index_urls:
            extra_urls = [
                url.strip() for url in self.extra_index_urls.split(",") if url.strip()
            ]
            urls.extend(extra_urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def get_primary_index_urls(self) -> list[str]:
        """Get primary index URLs (excluding extra fallback URLs)."""
        urls = [self.index_url]

        if self.index_urls:
            additional_urls = [
                url.strip() for url in self.index_urls.split(",") if url.strip()
            ]
            urls.extend(additional_urls)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def get_fallback_index_urls(self) -> list[str]:
        """Get fallback index URLs."""
        if not self.extra_index_urls:
            return []

        return [url.strip() for url in self.extra_index_urls.split(",") if url.strip()]

    def get_safe_dict(self) -> dict[str, Any]:
        """Get configuration as dictionary with sensitive data masked."""
        data = self.model_dump()
        # Mask sensitive information
        if data.get("private_pypi_password"):
            data["private_pypi_password"] = "***"
        return data


# Global settings instance
_settings: ServerSettings | None = None


def get_settings() -> ServerSettings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = ServerSettings()
    return _settings


def reload_settings() -> ServerSettings:
    """Reload settings from environment variables."""
    global _settings
    _settings = ServerSettings()
    return _settings


def update_settings(**kwargs: Any) -> ServerSettings:
    """Update settings with new values."""
    global _settings
    current_data = _settings.model_dump() if _settings else {}
    current_data.update(kwargs)
    _settings = ServerSettings(**current_data)
    return _settings

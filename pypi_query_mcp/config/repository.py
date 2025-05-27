"""Repository configuration for PyPI Query MCP Server."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RepositoryType(str, Enum):
    """Repository type enumeration."""

    PUBLIC = "public"
    PRIVATE = "private"


class AuthType(str, Enum):
    """Authentication type enumeration."""

    NONE = "none"
    BASIC = "basic"
    TOKEN = "token"


class RepositoryConfig(BaseModel):
    """Configuration for a PyPI repository."""

    name: str = Field(description="Repository name")
    url: str = Field(description="Repository URL")
    type: RepositoryType = Field(description="Repository type")
    priority: int = Field(
        default=100, description="Repository priority (lower = higher priority)"
    )

    # Authentication settings
    auth_type: AuthType = Field(
        default=AuthType.NONE, description="Authentication type"
    )
    username: str | None = Field(
        default=None, description="Username for authentication"
    )
    password: str | None = Field(
        default=None, description="Password for authentication"
    )
    token: str | None = Field(default=None, description="Token for authentication")

    # Connection settings
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    # Feature flags
    enabled: bool = Field(default=True, description="Whether repository is enabled")
    use_cache: bool = Field(default=True, description="Whether to cache responses")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Validate repository priority."""
        if v < 1 or v > 1000:
            raise ValueError("Priority must be between 1 and 1000")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        """Validate timeout."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries."""
        if v < 0 or v > 10:
            raise ValueError("Max retries must be between 0 and 10")
        return v

    def requires_auth(self) -> bool:
        """Check if repository requires authentication."""
        return self.auth_type != AuthType.NONE

    def has_credentials(self) -> bool:
        """Check if repository has valid credentials."""
        if self.auth_type == AuthType.BASIC:
            return bool(self.username and self.password)
        elif self.auth_type == AuthType.TOKEN:
            return bool(self.token)
        return True  # No auth required

    def get_safe_dict(self) -> dict[str, Any]:
        """Get repository config as dictionary with sensitive data masked."""
        data = self.model_dump()
        # Mask sensitive information
        if data.get("password"):
            data["password"] = "***"
        if data.get("token"):
            data["token"] = "***"
        return data


class RepositoryManager:
    """Manager for repository configurations."""

    def __init__(self):
        """Initialize repository manager."""
        self._repositories: dict[str, RepositoryConfig] = {}
        self._load_default_repositories()

    def _load_default_repositories(self) -> None:
        """Load default repository configurations."""
        # Add default public PyPI repository
        public_repo = RepositoryConfig(
            name="pypi",
            url="https://pypi.org/pypi",
            type=RepositoryType.PUBLIC,
            priority=100,
            auth_type=AuthType.NONE,
        )
        self._repositories["pypi"] = public_repo

    def load_repositories_from_settings(self, settings) -> None:
        """Load repositories from settings configuration."""
        # Clear existing repositories except default PyPI
        repos_to_keep = {
            name: repo
            for name, repo in self._repositories.items()
            if repo.type == RepositoryType.PUBLIC and name == "pypi"
        }
        self._repositories = repos_to_keep

        # Add repositories from index URLs
        all_urls = settings.get_all_index_urls()
        primary_urls = settings.get_primary_index_urls()
        fallback_urls = settings.get_fallback_index_urls()

        # Update primary PyPI URL if different from default
        if all_urls and all_urls[0] != "https://pypi.org/pypi":
            self._repositories["pypi"].url = all_urls[0]

        # Add additional primary index URLs
        for i, url in enumerate(
            primary_urls[1:], 1
        ):  # Skip first URL (already set as primary)
            repo_name = f"index_{i}"
            repo = RepositoryConfig(
                name=repo_name,
                url=url,
                type=RepositoryType.PUBLIC,
                priority=100 + i,  # Slightly lower priority than primary
                auth_type=AuthType.NONE,
            )
            self._repositories[repo_name] = repo

        # Add fallback index URLs
        for i, url in enumerate(fallback_urls):
            repo_name = f"fallback_{i}"
            repo = RepositoryConfig(
                name=repo_name,
                url=url,
                type=RepositoryType.PUBLIC,
                priority=200 + i,  # Lower priority for fallbacks
                auth_type=AuthType.NONE,
            )
            self._repositories[repo_name] = repo

        # Add private repository if configured
        if settings.has_private_repo():
            self.add_private_repository_from_settings(
                settings.private_pypi_url,
                settings.private_pypi_username,
                settings.private_pypi_password,
            )

    def add_repository(self, repo: RepositoryConfig) -> None:
        """Add a repository configuration."""
        if not repo.has_credentials() and repo.requires_auth():
            raise ValueError(
                f"Repository {repo.name} requires authentication but has no credentials"
            )
        self._repositories[repo.name] = repo

    def remove_repository(self, name: str) -> None:
        """Remove a repository configuration."""
        if name == "pypi":
            raise ValueError("Cannot remove default PyPI repository")
        self._repositories.pop(name, None)

    def get_repository(self, name: str) -> RepositoryConfig | None:
        """Get repository configuration by name."""
        return self._repositories.get(name)

    def list_repositories(self) -> list[RepositoryConfig]:
        """List all repository configurations."""
        return list(self._repositories.values())

    def get_enabled_repositories(self) -> list[RepositoryConfig]:
        """Get all enabled repositories sorted by priority."""
        enabled = [repo for repo in self._repositories.values() if repo.enabled]
        return sorted(enabled, key=lambda x: x.priority)

    def get_private_repositories(self) -> list[RepositoryConfig]:
        """Get all private repositories."""
        return [
            repo
            for repo in self._repositories.values()
            if repo.type == RepositoryType.PRIVATE and repo.enabled
        ]

    def has_private_repositories(self) -> bool:
        """Check if any private repositories are configured."""
        return len(self.get_private_repositories()) > 0

    def add_private_repository_from_settings(
        self, url: str, username: str | None = None, password: str | None = None
    ) -> None:
        """Add private repository from settings."""
        if not url:
            return

        auth_type = AuthType.BASIC if username and password else AuthType.NONE

        private_repo = RepositoryConfig(
            name="private",
            url=url,
            type=RepositoryType.PRIVATE,
            priority=1,  # Higher priority than public
            auth_type=auth_type,
            username=username,
            password=password,
        )

        self.add_repository(private_repo)


# Global repository manager instance
_repository_manager: RepositoryManager | None = None


def get_repository_manager() -> RepositoryManager:
    """Get global repository manager instance."""
    global _repository_manager
    if _repository_manager is None:
        _repository_manager = RepositoryManager()
    return _repository_manager


def reload_repository_manager() -> RepositoryManager:
    """Reload repository manager."""
    global _repository_manager
    _repository_manager = RepositoryManager()
    return _repository_manager

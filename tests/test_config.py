"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from pypi_query_mcp.config import (
    AuthType,
    RepositoryConfig,
    RepositoryManager,
    RepositoryType,
    ServerSettings,
    get_repository_manager,
    get_settings,
    reload_settings,
)


class TestServerSettings:
    """Test ServerSettings class."""

    def test_default_settings(self):
        """Test default settings values."""
        settings = ServerSettings()

        assert settings.log_level == "INFO"
        assert settings.cache_ttl == 3600
        assert settings.request_timeout == 30.0
        assert settings.max_retries == 3
        assert settings.retry_delay == 1.0
        assert settings.index_url == "https://pypi.org/pypi"
        assert settings.private_pypi_url is None
        assert settings.dependency_max_depth == 5
        assert settings.dependency_max_concurrent == 10
        assert settings.enable_security_analysis is False

    def test_environment_variables(self):
        """Test loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PYPI_LOG_LEVEL": "DEBUG",
                "PYPI_CACHE_TTL": "7200",
                "PYPI_PRIVATE_PYPI_URL": "https://private.pypi.com",
                "PYPI_PRIVATE_PYPI_USERNAME": "testuser",
                "PYPI_PRIVATE_PYPI_PASSWORD": "testpass",
            },
        ):
            settings = ServerSettings()

            assert settings.log_level == "DEBUG"
            assert settings.cache_ttl == 7200
            assert settings.private_pypi_url == "https://private.pypi.com"
            assert settings.private_pypi_username == "testuser"
            assert settings.private_pypi_password == "testpass"

    def test_validation(self):
        """Test settings validation."""
        # Test invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            ServerSettings(log_level="INVALID")

        # Test negative cache TTL
        with pytest.raises(ValueError, match="Cache TTL must be non-negative"):
            ServerSettings(cache_ttl=-1)

        # Test invalid dependency max depth
        with pytest.raises(
            ValueError, match="Dependency max depth must be between 1 and 10"
        ):
            ServerSettings(dependency_max_depth=0)

        with pytest.raises(
            ValueError, match="Dependency max depth must be between 1 and 10"
        ):
            ServerSettings(dependency_max_depth=11)

    def test_has_private_repo(self):
        """Test private repository detection."""
        settings = ServerSettings()
        assert not settings.has_private_repo()

        settings = ServerSettings(private_pypi_url="https://private.pypi.com")
        assert settings.has_private_repo()

    def test_has_private_auth(self):
        """Test private authentication detection."""
        settings = ServerSettings()
        assert not settings.has_private_auth()

        settings = ServerSettings(
            private_pypi_url="https://private.pypi.com",
            private_pypi_username="user",
            private_pypi_password="pass",
        )
        assert settings.has_private_auth()

    def test_get_safe_dict(self):
        """Test safe dictionary representation."""
        settings = ServerSettings(private_pypi_password="secret123")
        safe_dict = settings.get_safe_dict()
        assert safe_dict["private_pypi_password"] == "***"

    def test_multiple_index_urls(self):
        """Test multiple index URLs configuration."""
        settings = ServerSettings(
            index_url="https://pypi.org/pypi",
            index_urls="https://mirrors.aliyun.com/pypi/simple/,https://pypi.tuna.tsinghua.edu.cn/simple/",
            extra_index_urls="https://test.pypi.org/simple/",
        )

        all_urls = settings.get_all_index_urls()
        assert len(all_urls) == 4
        assert all_urls[0] == "https://pypi.org/pypi"
        assert "https://mirrors.aliyun.com/pypi/simple/" in all_urls
        assert "https://pypi.tuna.tsinghua.edu.cn/simple/" in all_urls
        assert "https://test.pypi.org/simple/" in all_urls

        primary_urls = settings.get_primary_index_urls()
        assert len(primary_urls) == 3
        assert "https://test.pypi.org/simple/" not in primary_urls

        fallback_urls = settings.get_fallback_index_urls()
        assert len(fallback_urls) == 1
        assert fallback_urls[0] == "https://test.pypi.org/simple/"

    def test_duplicate_urls_removal(self):
        """Test duplicate URL removal while preserving order."""
        settings = ServerSettings(
            index_url="https://pypi.org/pypi",
            index_urls="https://pypi.org/pypi,https://mirrors.aliyun.com/pypi/simple/",
            extra_index_urls="https://mirrors.aliyun.com/pypi/simple/",
        )

        all_urls = settings.get_all_index_urls()
        assert len(all_urls) == 2  # Duplicates removed
        assert all_urls[0] == "https://pypi.org/pypi"
        assert all_urls[1] == "https://mirrors.aliyun.com/pypi/simple/"

    def test_empty_index_urls(self):
        """Test handling of empty index URLs."""
        settings = ServerSettings(
            index_url="https://pypi.org/pypi", index_urls="", extra_index_urls=None
        )

        all_urls = settings.get_all_index_urls()
        assert len(all_urls) == 1
        assert all_urls[0] == "https://pypi.org/pypi"

        fallback_urls = settings.get_fallback_index_urls()
        assert len(fallback_urls) == 0


class TestRepositoryConfig:
    """Test RepositoryConfig class."""

    def test_basic_repository(self):
        """Test basic repository configuration."""
        repo = RepositoryConfig(
            name="test", url="https://test.pypi.com", type=RepositoryType.PRIVATE
        )

        assert repo.name == "test"
        assert repo.url == "https://test.pypi.com"
        assert repo.type == RepositoryType.PRIVATE
        assert repo.priority == 100
        assert repo.auth_type == AuthType.NONE
        assert repo.enabled is True

    def test_repository_with_auth(self):
        """Test repository with authentication."""
        repo = RepositoryConfig(
            name="private",
            url="https://private.pypi.com",
            type=RepositoryType.PRIVATE,
            auth_type=AuthType.BASIC,
            username="user",
            password="pass",
        )

        assert repo.requires_auth()
        assert repo.has_credentials()

    def test_repository_validation(self):
        """Test repository validation."""
        # Test invalid priority
        with pytest.raises(ValueError, match="Priority must be between 1 and 1000"):
            RepositoryConfig(
                name="test",
                url="https://test.com",
                type=RepositoryType.PUBLIC,
                priority=0,
            )

        # Test invalid timeout
        with pytest.raises(ValueError, match="Timeout must be positive"):
            RepositoryConfig(
                name="test",
                url="https://test.com",
                type=RepositoryType.PUBLIC,
                timeout=0,
            )

    def test_get_safe_dict(self):
        """Test safe dictionary representation."""
        repo = RepositoryConfig(
            name="test",
            url="https://test.com",
            type=RepositoryType.PRIVATE,
            auth_type=AuthType.BASIC,
            username="user",
            password="secret123",
        )
        safe_dict = repo.get_safe_dict()
        assert safe_dict["password"] == "***"


class TestRepositoryManager:
    """Test RepositoryManager class."""

    def test_default_repositories(self):
        """Test default repository loading."""
        manager = RepositoryManager()
        repos = manager.list_repositories()

        assert len(repos) == 1
        assert repos[0].name == "pypi"
        assert repos[0].type == RepositoryType.PUBLIC

    def test_add_repository(self):
        """Test adding repository."""
        manager = RepositoryManager()

        repo = RepositoryConfig(
            name="private",
            url="https://private.pypi.com",
            type=RepositoryType.PRIVATE,
            priority=1,
        )

        manager.add_repository(repo)
        assert len(manager.list_repositories()) == 2
        assert manager.get_repository("private") == repo

    def test_remove_repository(self):
        """Test removing repository."""
        manager = RepositoryManager()

        # Cannot remove default PyPI
        with pytest.raises(ValueError, match="Cannot remove default PyPI repository"):
            manager.remove_repository("pypi")

        # Add and remove custom repository
        repo = RepositoryConfig(
            name="test", url="https://test.com", type=RepositoryType.PRIVATE
        )
        manager.add_repository(repo)
        assert manager.get_repository("test") is not None

        manager.remove_repository("test")
        assert manager.get_repository("test") is None

    def test_get_enabled_repositories(self):
        """Test getting enabled repositories sorted by priority."""
        manager = RepositoryManager()

        # Add repositories with different priorities
        repo1 = RepositoryConfig(
            name="high_priority",
            url="https://high.com",
            type=RepositoryType.PRIVATE,
            priority=1,
        )
        repo2 = RepositoryConfig(
            name="low_priority",
            url="https://low.com",
            type=RepositoryType.PRIVATE,
            priority=200,
        )

        manager.add_repository(repo1)
        manager.add_repository(repo2)

        enabled = manager.get_enabled_repositories()
        assert len(enabled) == 3  # Including default PyPI
        assert enabled[0].name == "high_priority"  # Highest priority first
        assert enabled[1].name == "pypi"
        assert enabled[2].name == "low_priority"

    def test_private_repositories(self):
        """Test private repository management."""
        manager = RepositoryManager()

        assert not manager.has_private_repositories()
        assert len(manager.get_private_repositories()) == 0

        # Add private repository
        repo = RepositoryConfig(
            name="private", url="https://private.com", type=RepositoryType.PRIVATE
        )
        manager.add_repository(repo)

        assert manager.has_private_repositories()
        assert len(manager.get_private_repositories()) == 1

    def test_add_private_repository_from_settings(self):
        """Test adding private repository from settings."""
        manager = RepositoryManager()

        # Add without auth
        manager.add_private_repository_from_settings("https://private.com")
        private_repos = manager.get_private_repositories()
        assert len(private_repos) == 1
        assert private_repos[0].auth_type == AuthType.NONE

        # Add with auth
        manager = RepositoryManager()
        manager.add_private_repository_from_settings(
            "https://private.com", "user", "pass"
        )
        private_repos = manager.get_private_repositories()
        assert len(private_repos) == 1
        assert private_repos[0].auth_type == AuthType.BASIC
        assert private_repos[0].username == "user"

    def test_load_repositories_from_settings(self):
        """Test loading repositories from settings."""
        manager = RepositoryManager()

        # Create settings with multiple index URLs
        settings = ServerSettings(
            index_url="https://custom.pypi.org/pypi",
            index_urls="https://mirrors.aliyun.com/pypi/simple/",
            extra_index_urls="https://test.pypi.org/simple/",
            private_pypi_url="https://private.pypi.com",
            private_pypi_username="user",
            private_pypi_password="pass",
        )

        manager.load_repositories_from_settings(settings)

        # Check all repositories are loaded
        all_repos = manager.list_repositories()
        repo_names = [repo.name for repo in all_repos]

        assert "pypi" in repo_names  # Primary
        assert "index_1" in repo_names  # Additional index
        assert "fallback_0" in repo_names  # Fallback
        assert "private" in repo_names  # Private repo

        # Check primary PyPI URL is updated
        pypi_repo = manager.get_repository("pypi")
        assert pypi_repo.url == "https://custom.pypi.org/pypi"

        # Check priorities are correct
        enabled_repos = manager.get_enabled_repositories()
        priorities = [repo.priority for repo in enabled_repos]
        assert priorities == sorted(priorities)  # Should be sorted by priority

        # Check private repository has auth
        private_repo = manager.get_repository("private")
        assert private_repo.auth_type == AuthType.BASIC
        assert private_repo.username == "user"


class TestGlobalInstances:
    """Test global configuration instances."""

    def test_get_settings(self):
        """Test global settings instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Same instance

    def test_reload_settings(self):
        """Test settings reload."""
        settings1 = get_settings()
        settings2 = reload_settings()
        assert settings1 is not settings2  # Different instance

    def test_get_repository_manager(self):
        """Test global repository manager instance."""
        manager1 = get_repository_manager()
        manager2 = get_repository_manager()
        assert manager1 is manager2  # Same instance

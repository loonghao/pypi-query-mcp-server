"""Configuration management for PyPI Query MCP Server.

This package handles configuration loading, validation, and management
for the MCP server, including private registry settings.
"""

from .repository import (
    AuthType,
    RepositoryConfig,
    RepositoryManager,
    RepositoryType,
    get_repository_manager,
    reload_repository_manager,
)
from .settings import (
    ServerSettings,
    get_settings,
    reload_settings,
    update_settings,
)

__all__ = [
    # Settings
    "ServerSettings",
    "get_settings",
    "reload_settings",
    "update_settings",
    # Repository
    "RepositoryConfig",
    "RepositoryManager",
    "RepositoryType",
    "AuthType",
    "get_repository_manager",
    "reload_repository_manager",
]

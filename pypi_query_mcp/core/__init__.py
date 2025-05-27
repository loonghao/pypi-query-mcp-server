"""Core modules for PyPI Query MCP Server.

This package contains the core business logic for PyPI package queries,
including API clients, data processing, and utility functions.
"""

from .exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIError,
    PyPIServerError,
    RateLimitError,
)
from .pypi_client import PyPIClient
from .version_utils import VersionCompatibility

__all__ = [
    "PyPIClient",
    "VersionCompatibility",
    "PyPIError",
    "PackageNotFoundError",
    "NetworkError",
    "RateLimitError",
    "InvalidPackageNameError",
    "PyPIServerError",
]

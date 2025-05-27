"""MCP tools for PyPI package queries.

This package contains the FastMCP tool implementations that provide
the user-facing interface for PyPI package operations.
"""

from .compatibility_check import (
    check_python_compatibility,
    get_compatible_python_versions,
    suggest_python_version_for_packages,
)
from .package_query import (
    query_package_dependencies,
    query_package_info,
    query_package_versions,
)

__all__ = [
    "query_package_info",
    "query_package_versions",
    "query_package_dependencies",
    "check_python_compatibility",
    "get_compatible_python_versions",
    "suggest_python_version_for_packages",
]

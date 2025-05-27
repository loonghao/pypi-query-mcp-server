"""MCP tools for PyPI package queries.

This package contains the FastMCP tool implementations that provide
the user-facing interface for PyPI package operations.
"""

from .compatibility_check import (
    check_python_compatibility,
    get_compatible_python_versions,
    suggest_python_version_for_packages,
)
from .dependency_resolver import resolve_package_dependencies
from .download_stats import (
    get_package_download_stats,
    get_package_download_trends,
    get_top_packages_by_downloads,
)
from .package_downloader import download_package_with_dependencies
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
    "resolve_package_dependencies",
    "download_package_with_dependencies",
    "get_package_download_stats",
    "get_package_download_trends",
    "get_top_packages_by_downloads",
]

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
from .metadata import (
    manage_package_keywords,
    manage_package_urls,
    set_package_visibility,
    update_package_metadata,
)
from .publishing import (
    check_pypi_credentials,
    delete_pypi_release,
    get_pypi_account_info,
    get_pypi_upload_history,
    manage_pypi_maintainers,
    upload_package_to_pypi,
)
from .search import (
    find_alternatives,
    get_trending_packages,
    search_by_category,
    search_packages,
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
    "search_packages",
    "search_by_category",
    "find_alternatives",
    "get_trending_packages",
    "upload_package_to_pypi",
    "check_pypi_credentials",
    "get_pypi_upload_history",
    "delete_pypi_release",
    "manage_pypi_maintainers",
    "get_pypi_account_info",
    "update_package_metadata",
    "manage_package_urls",
    "set_package_visibility",
    "manage_package_keywords",
]

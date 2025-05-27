"""Package query tools for PyPI MCP server."""

import logging
from typing import Any

from ..core import InvalidPackageNameError, NetworkError, PyPIClient, PyPIError

logger = logging.getLogger(__name__)


def format_package_info(package_data: dict[str, Any]) -> dict[str, Any]:
    """Format package information for MCP response.

    Args:
        package_data: Raw package data from PyPI API

    Returns:
        Formatted package information
    """
    info = package_data.get("info", {})

    # Extract basic information
    formatted = {
        "name": info.get("name", ""),
        "version": info.get("version", ""),
        "summary": info.get("summary", ""),
        "description": info.get("description", "")[:500] + "..."
        if len(info.get("description", "")) > 500
        else info.get("description", ""),
        "author": info.get("author", ""),
        "author_email": info.get("author_email", ""),
        "maintainer": info.get("maintainer", ""),
        "maintainer_email": info.get("maintainer_email", ""),
        "license": info.get("license", ""),
        "home_page": info.get("home_page", ""),
        "project_url": info.get("project_url", ""),
        "download_url": info.get("download_url", ""),
        "requires_python": info.get("requires_python", ""),
        "platform": info.get("platform", ""),
        "keywords": info.get("keywords", ""),
        "classifiers": info.get("classifiers", []),
        "requires_dist": info.get("requires_dist", []),
        "project_urls": info.get("project_urls", {}),
    }

    # Add release information
    releases = package_data.get("releases", {})
    formatted["total_versions"] = len(releases)
    formatted["available_versions"] = list(releases.keys())[-10:]  # Last 10 versions

    # Add download statistics if available
    if "urls" in package_data:
        urls = package_data["urls"]
        if urls:
            formatted["download_info"] = {
                "files_count": len(urls),
                "file_types": list({url.get("packagetype", "") for url in urls}),
                "python_versions": list(
                    {
                        url.get("python_version", "")
                        for url in urls
                        if url.get("python_version")
                    }
                ),
            }

    return formatted


def format_version_info(package_data: dict[str, Any]) -> dict[str, Any]:
    """Format version information for MCP response.

    Args:
        package_data: Raw package data from PyPI API

    Returns:
        Formatted version information
    """
    info = package_data.get("info", {})
    releases = package_data.get("releases", {})

    # Sort versions (basic sorting, could be improved with proper version parsing)
    sorted_versions = sorted(releases.keys(), reverse=True)

    return {
        "package_name": info.get("name", ""),
        "latest_version": info.get("version", ""),
        "total_versions": len(releases),
        "versions": sorted_versions,
        "recent_versions": sorted_versions[:20],  # Last 20 versions
        "version_details": {
            version: {
                "release_count": len(releases[version]),
                "has_wheel": any(
                    file.get("packagetype") == "bdist_wheel"
                    for file in releases[version]
                ),
                "has_source": any(
                    file.get("packagetype") == "sdist" for file in releases[version]
                ),
            }
            for version in sorted_versions[:10]  # Details for last 10 versions
        },
    }


def format_dependency_info(package_data: dict[str, Any]) -> dict[str, Any]:
    """Format dependency information for MCP response.

    Args:
        package_data: Raw package data from PyPI API

    Returns:
        Formatted dependency information
    """
    info = package_data.get("info", {})
    requires_dist = info.get("requires_dist", []) or []

    # Parse dependencies
    runtime_deps = []
    dev_deps = []
    optional_deps = {}

    for dep in requires_dist:
        if not dep:
            continue

        # Basic parsing - could be improved with proper dependency parsing
        if "extra ==" in dep:
            # Optional dependency
            parts = dep.split(";")
            dep_name = parts[0].strip()
            extra_part = parts[1] if len(parts) > 1 else ""

            if "extra ==" in extra_part:
                extra_name = extra_part.split("extra ==")[1].strip().strip("\"'")
                if extra_name not in optional_deps:
                    optional_deps[extra_name] = []
                optional_deps[extra_name].append(dep_name)
        elif "dev" in dep.lower() or "test" in dep.lower():
            dev_deps.append(dep)
        else:
            runtime_deps.append(dep)

    return {
        "package_name": info.get("name", ""),
        "version": info.get("version", ""),
        "requires_python": info.get("requires_python", ""),
        "runtime_dependencies": runtime_deps,
        "development_dependencies": dev_deps,
        "optional_dependencies": optional_deps,
        "total_dependencies": len(requires_dist),
        "dependency_summary": {
            "runtime_count": len(runtime_deps),
            "dev_count": len(dev_deps),
            "optional_groups": len(optional_deps),
            "total_optional": sum(len(deps) for deps in optional_deps.values()),
        },
    }


async def query_package_info(package_name: str) -> dict[str, Any]:
    """Query comprehensive package information from PyPI.

    Args:
        package_name: Name of the package to query

    Returns:
        Formatted package information

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    logger.info(f"Querying package info for: {package_name}")

    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            return format_package_info(package_data)
    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying package {package_name}: {e}")
        raise NetworkError(f"Failed to query package information: {e}", e) from e


async def query_package_versions(package_name: str) -> dict[str, Any]:
    """Query package version information from PyPI.

    Args:
        package_name: Name of the package to query

    Returns:
        Formatted version information

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    logger.info(f"Querying versions for package: {package_name}")

    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            return format_version_info(package_data)
    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying versions for {package_name}: {e}")
        raise NetworkError(f"Failed to query package versions: {e}", e) from e


async def query_package_dependencies(
    package_name: str, version: str | None = None
) -> dict[str, Any]:
    """Query package dependency information from PyPI.

    Args:
        package_name: Name of the package to query
        version: Specific version to query (optional, defaults to latest)

    Returns:
        Formatted dependency information

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    logger.info(
        f"Querying dependencies for package: {package_name}"
        + (f" version {version}" if version else " (latest)")
    )

    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)

            # TODO: In future, support querying specific version dependencies
            # For now, we return dependencies for the latest version
            if version and version != package_data.get("info", {}).get("version"):
                logger.warning(
                    f"Specific version {version} requested but not implemented yet. "
                    f"Returning dependencies for latest version."
                )

            return format_dependency_info(package_data)
    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying dependencies for {package_name}: {e}")
        raise NetworkError(f"Failed to query package dependencies: {e}", e) from e

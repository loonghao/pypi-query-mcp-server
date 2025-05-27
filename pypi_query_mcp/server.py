"""FastMCP server for PyPI package queries."""

import logging
from typing import Any

import click
from fastmcp import FastMCP

from .core.exceptions import InvalidPackageNameError, NetworkError, PackageNotFoundError
from .tools import (
    check_python_compatibility,
    get_compatible_python_versions,
    query_package_dependencies,
    query_package_info,
    query_package_versions,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastMCP application
mcp = FastMCP("PyPI Query MCP Server")


@mcp.tool()
async def get_package_info(package_name: str) -> dict[str, Any]:
    """Query comprehensive information about a PyPI package.

    This tool retrieves detailed information about a Python package from PyPI,
    including metadata, description, author information, dependencies, and more.

    Args:
        package_name: The name of the PyPI package to query (e.g., 'requests', 'django')

    Returns:
        Dictionary containing comprehensive package information including:
        - Basic metadata (name, version, summary, description)
        - Author and maintainer information
        - License and project URLs
        - Python version requirements
        - Dependencies and classifiers
        - Version history summary

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(f"MCP tool: Querying package info for {package_name}")
        result = await query_package_info(package_name)
        logger.info(f"Successfully retrieved info for package: {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error querying package {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name
        }
    except Exception as e:
        logger.error(f"Unexpected error querying package {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name
        }


@mcp.tool()
async def get_package_versions(package_name: str) -> dict[str, Any]:
    """Get version information for a PyPI package.

    This tool retrieves comprehensive version information for a Python package,
    including all available versions, release details, and distribution formats.

    Args:
        package_name: The name of the PyPI package to query (e.g., 'requests', 'numpy')

    Returns:
        Dictionary containing version information including:
        - Latest version and total version count
        - List of all available versions (sorted)
        - Recent versions with release details
        - Distribution format information (wheel, source)

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(f"MCP tool: Querying versions for {package_name}")
        result = await query_package_versions(package_name)
        logger.info(f"Successfully retrieved versions for package: {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error querying versions for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name
        }
    except Exception as e:
        logger.error(f"Unexpected error querying versions for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name
        }


@mcp.tool()
async def get_package_dependencies(package_name: str, version: str | None = None) -> dict[str, Any]:
    """Get dependency information for a PyPI package.

    This tool retrieves comprehensive dependency information for a Python package,
    including runtime dependencies, development dependencies, and optional dependencies.

    Args:
        package_name: The name of the PyPI package to query (e.g., 'django', 'flask')
        version: Specific version to query (optional, defaults to latest version)

    Returns:
        Dictionary containing dependency information including:
        - Runtime dependencies and development dependencies
        - Optional dependency groups
        - Python version requirements
        - Dependency counts and summary statistics

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(f"MCP tool: Querying dependencies for {package_name}" +
                   (f" version {version}" if version else " (latest)"))
        result = await query_package_dependencies(package_name, version)
        logger.info(f"Successfully retrieved dependencies for package: {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error querying dependencies for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "version": version
        }
    except Exception as e:
        logger.error(f"Unexpected error querying dependencies for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "version": version
        }


@mcp.tool()
async def check_package_python_compatibility(
    package_name: str,
    target_python_version: str,
    use_cache: bool = True
) -> dict[str, Any]:
    """Check if a package is compatible with a specific Python version.

    This tool analyzes a package's Python version requirements and determines
    if it's compatible with your target Python version.

    Args:
        package_name: The name of the PyPI package to check (e.g., 'django', 'requests')
        target_python_version: Target Python version to check (e.g., '3.9', '3.10.5', '3.11')
        use_cache: Whether to use cached package data (default: True)

    Returns:
        Dictionary containing detailed compatibility information including:
        - Compatibility status (True/False)
        - Source of compatibility information (requires_python or classifiers)
        - Detailed analysis and suggestions
        - Package version requirements

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(f"MCP tool: Checking Python {target_python_version} compatibility for {package_name}")
        result = await check_python_compatibility(package_name, target_python_version, use_cache)
        logger.info(f"Compatibility check completed for {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error checking compatibility for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "target_python_version": target_python_version
        }
    except Exception as e:
        logger.error(f"Unexpected error checking compatibility for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "target_python_version": target_python_version
        }


@mcp.tool()
async def get_package_compatible_python_versions(
    package_name: str,
    python_versions: list[str] | None = None,
    use_cache: bool = True
) -> dict[str, Any]:
    """Get all Python versions compatible with a package.

    This tool analyzes a package and returns which Python versions are
    compatible with it, along with recommendations.

    Args:
        package_name: The name of the PyPI package to analyze (e.g., 'numpy', 'pandas')
        python_versions: List of Python versions to check (optional, defaults to common versions)
        use_cache: Whether to use cached package data (default: True)

    Returns:
        Dictionary containing compatibility information including:
        - List of compatible Python versions
        - List of incompatible versions with reasons
        - Compatibility rate and recommendations
        - Package version requirements

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(f"MCP tool: Getting compatible Python versions for {package_name}")
        result = await get_compatible_python_versions(package_name, python_versions, use_cache)
        logger.info(f"Compatible versions analysis completed for {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error getting compatible versions for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name
        }
    except Exception as e:
        logger.error(f"Unexpected error getting compatible versions for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name
        }


@click.command()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Logging level"
)
def main(log_level: str) -> None:
    """Start the PyPI Query MCP Server."""
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level))

    logger.info("Starting PyPI Query MCP Server")
    logger.info(f"Log level set to: {log_level}")

    # Run the FastMCP server (uses STDIO transport by default)
    mcp.run()


if __name__ == "__main__":
    main()

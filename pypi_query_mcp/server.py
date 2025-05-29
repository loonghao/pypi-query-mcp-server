"""FastMCP server for PyPI package queries."""

import logging
from typing import Any

import click
from fastmcp import FastMCP

from .core.exceptions import InvalidPackageNameError, NetworkError, PackageNotFoundError
from .prompts import (
    analyze_daily_trends,
    analyze_environment_dependencies,
    analyze_package_quality,
    audit_security_risks,
    check_outdated_packages,
    compare_packages,
    find_trending_packages,
    generate_migration_checklist,
    generate_update_plan,
    plan_package_migration,
    plan_version_upgrade,
    resolve_dependency_conflicts,
    suggest_alternatives,
    track_package_updates,
)
from .tools import (
    check_python_compatibility,
    download_package_with_dependencies,
    get_compatible_python_versions,
    get_package_download_stats,
    get_package_download_trends,
    get_top_packages_by_downloads,
    query_package_dependencies,
    query_package_info,
    query_package_versions,
    resolve_package_dependencies,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            "package_name": package_name,
        }
    except Exception as e:
        logger.error(f"Unexpected error querying package {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
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
            "package_name": package_name,
        }
    except Exception as e:
        logger.error(f"Unexpected error querying versions for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


@mcp.tool()
async def get_package_dependencies(
    package_name: str, version: str | None = None
) -> dict[str, Any]:
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
        logger.info(
            f"MCP tool: Querying dependencies for {package_name}"
            + (f" version {version}" if version else " (latest)")
        )
        result = await query_package_dependencies(package_name, version)
        logger.info(f"Successfully retrieved dependencies for package: {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error querying dependencies for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "version": version,
        }
    except Exception as e:
        logger.error(f"Unexpected error querying dependencies for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "version": version,
        }


@mcp.tool()
async def check_package_python_compatibility(
    package_name: str, target_python_version: str, use_cache: bool = True
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
        logger.info(
            f"MCP tool: Checking Python {target_python_version} compatibility for {package_name}"
        )
        result = await check_python_compatibility(
            package_name, target_python_version, use_cache
        )
        logger.info(f"Compatibility check completed for {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error checking compatibility for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "target_python_version": target_python_version,
        }
    except Exception as e:
        logger.error(f"Unexpected error checking compatibility for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "target_python_version": target_python_version,
        }


@mcp.tool()
async def get_package_compatible_python_versions(
    package_name: str, python_versions: list[str] | None = None, use_cache: bool = True
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
        result = await get_compatible_python_versions(
            package_name, python_versions, use_cache
        )
        logger.info(f"Compatible versions analysis completed for {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error getting compatible versions for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
        }
    except Exception as e:
        logger.error(
            f"Unexpected error getting compatible versions for {package_name}: {e}"
        )
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
        }


@mcp.tool()
async def resolve_dependencies(
    package_name: str,
    python_version: str | None = None,
    include_extras: list[str] | None = None,
    include_dev: bool = False,
    max_depth: int = 5,
) -> dict[str, Any]:
    """Resolve all dependencies for a PyPI package recursively.

    This tool performs comprehensive dependency resolution for a Python package,
    analyzing the complete dependency tree including transitive dependencies.

    Args:
        package_name: The name of the PyPI package to analyze (e.g., 'pyside2', 'django')
        python_version: Target Python version for dependency filtering (e.g., '3.10', '3.11')
        include_extras: List of extra dependency groups to include (e.g., ['dev', 'test'])
        include_dev: Whether to include development dependencies (default: False)
        max_depth: Maximum recursion depth for dependency resolution (default: 5)

    Returns:
        Dictionary containing comprehensive dependency analysis including:
        - Complete dependency tree with all transitive dependencies
        - Dependency categorization (runtime, development, extras)
        - Package metadata for each dependency
        - Summary statistics and analysis

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(
            f"MCP tool: Resolving dependencies for {package_name} "
            f"(Python {python_version}, extras: {include_extras})"
        )
        result = await resolve_package_dependencies(
            package_name=package_name,
            python_version=python_version,
            include_extras=include_extras,
            include_dev=include_dev,
            max_depth=max_depth,
        )
        logger.info(f"Successfully resolved dependencies for package: {package_name}")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error resolving dependencies for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "python_version": python_version,
        }
    except Exception as e:
        logger.error(f"Unexpected error resolving dependencies for {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "python_version": python_version,
        }


@mcp.tool()
async def download_package(
    package_name: str,
    download_dir: str = "./downloads",
    python_version: str | None = None,
    include_extras: list[str] | None = None,
    include_dev: bool = False,
    prefer_wheel: bool = True,
    verify_checksums: bool = True,
    max_depth: int = 5,
) -> dict[str, Any]:
    """Download a PyPI package and all its dependencies to local directory.

    This tool downloads a Python package and all its dependencies, providing
    comprehensive package collection for offline installation or analysis.

    Args:
        package_name: The name of the PyPI package to download (e.g., 'pyside2', 'requests')
        download_dir: Local directory to download packages to (default: './downloads')
        python_version: Target Python version for compatibility (e.g., '3.10', '3.11')
        include_extras: List of extra dependency groups to include (e.g., ['dev', 'test'])
        include_dev: Whether to include development dependencies (default: False)
        prefer_wheel: Whether to prefer wheel files over source distributions (default: True)
        verify_checksums: Whether to verify downloaded file checksums (default: True)
        max_depth: Maximum dependency resolution depth (default: 5)

    Returns:
        Dictionary containing download results including:
        - Download statistics and file information
        - Dependency resolution results
        - File verification results
        - Success/failure summary for each package

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(
            f"MCP tool: Downloading {package_name} and dependencies to {download_dir} "
            f"(Python {python_version})"
        )
        result = await download_package_with_dependencies(
            package_name=package_name,
            download_dir=download_dir,
            python_version=python_version,
            include_extras=include_extras,
            include_dev=include_dev,
            prefer_wheel=prefer_wheel,
            verify_checksums=verify_checksums,
            max_depth=max_depth,
        )
        logger.info(f"Successfully downloaded {package_name} and dependencies")
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error downloading {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "download_dir": download_dir,
        }
    except Exception as e:
        logger.error(f"Unexpected error downloading {package_name}: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "download_dir": download_dir,
        }


@mcp.tool()
async def get_download_statistics(
    package_name: str, period: str = "month", use_cache: bool = True
) -> dict[str, Any]:
    """Get download statistics for a PyPI package.

    This tool retrieves comprehensive download statistics for a Python package,
    including recent download counts, trends, and analysis.

    Args:
        package_name: The name of the PyPI package to analyze (e.g., 'requests', 'numpy')
        period: Time period for recent downloads ('day', 'week', 'month', default: 'month')
        use_cache: Whether to use cached data for faster responses (default: True)

    Returns:
        Dictionary containing download statistics including:
        - Recent download counts (last day/week/month)
        - Package metadata and repository information
        - Download trends and growth analysis
        - Data source and timestamp information

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(
            f"MCP tool: Getting download statistics for {package_name} (period: {period})"
        )
        result = await get_package_download_stats(package_name, period, use_cache)
        logger.info(
            f"Successfully retrieved download statistics for package: {package_name}"
        )
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error getting download statistics for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "period": period,
        }
    except Exception as e:
        logger.error(
            f"Unexpected error getting download statistics for {package_name}: {e}"
        )
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "period": period,
        }


@mcp.tool()
async def get_download_trends(
    package_name: str, include_mirrors: bool = False, use_cache: bool = True
) -> dict[str, Any]:
    """Get download trends and time series for a PyPI package.

    This tool retrieves detailed download trends and time series data for a Python package,
    providing insights into download patterns over the last 180 days.

    Args:
        package_name: The name of the PyPI package to analyze (e.g., 'django', 'flask')
        include_mirrors: Whether to include mirror downloads in analysis (default: False)
        use_cache: Whether to use cached data for faster responses (default: True)

    Returns:
        Dictionary containing download trends including:
        - Time series data for the last 180 days
        - Trend analysis (increasing/decreasing/stable)
        - Peak download periods and statistics
        - Average daily downloads and growth indicators

    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
    """
    try:
        logger.info(
            f"MCP tool: Getting download trends for {package_name} "
            f"(include_mirrors: {include_mirrors})"
        )
        result = await get_package_download_trends(
            package_name, include_mirrors, use_cache
        )
        logger.info(
            f"Successfully retrieved download trends for package: {package_name}"
        )
        return result
    except (InvalidPackageNameError, PackageNotFoundError, NetworkError) as e:
        logger.error(f"Error getting download trends for {package_name}: {e}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "package_name": package_name,
            "include_mirrors": include_mirrors,
        }
    except Exception as e:
        logger.error(
            f"Unexpected error getting download trends for {package_name}: {e}"
        )
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "package_name": package_name,
            "include_mirrors": include_mirrors,
        }


@mcp.tool()
async def get_top_downloaded_packages(
    period: str = "month", limit: int = 20
) -> dict[str, Any]:
    """Get the most downloaded PyPI packages.

    This tool retrieves a list of the most popular Python packages by download count,
    helping you discover trending and widely-used packages in the Python ecosystem.

    Args:
        period: Time period for download ranking ('day', 'week', 'month', default: 'month')
        limit: Maximum number of packages to return (default: 20, max: 50)

    Returns:
        Dictionary containing top packages information including:
        - Ranked list of packages with download counts
        - Package metadata and repository links
        - Period and ranking information
        - Data source and limitations

    Note:
        Due to API limitations, this tool provides results based on known popular packages.
        For comprehensive data analysis, consider using Google BigQuery with PyPI datasets.
    """
    try:
        # Limit the maximum number of packages to prevent excessive API calls
        actual_limit = min(limit, 50)

        logger.info(
            f"MCP tool: Getting top {actual_limit} packages for period: {period}"
        )
        result = await get_top_packages_by_downloads(period, actual_limit)
        logger.info("Successfully retrieved top packages list")
        return result
    except Exception as e:
        logger.error(f"Error getting top packages: {e}")
        return {
            "error": f"Unexpected error: {e}",
            "error_type": "UnexpectedError",
            "period": period,
            "limit": limit,
        }


# Register prompt templates following standard MCP workflow:
# 1. User calls tool → MCP client sends request
# 2. Tool function executes → Collects necessary data and parameters
# 3. Call Prompt generator → Pass parameters to corresponding generator
# 4. Load template → Get template with {{parameter}} placeholders
# 5. Parameter replacement → Replace {{parameter_name}} with actual values
# 6. Environment variable customization → Apply user's custom prompt words
# 7. Return final prompt → As tool's response back to AI


@mcp.prompt()
async def analyze_package_quality_prompt(
    package_name: str, version: str | None = None
) -> str:
    """Generate a comprehensive quality analysis prompt for a PyPI package."""
    # Step 3: Call Prompt generator
    template = await analyze_package_quality(package_name, version)

    # Step 5: Parameter replacement - replace {{parameter_name}} with actual values
    result = template.replace("{{package_name}}", package_name)

    # Handle version parameter
    if version:
        version_text = f"version {version}"
    else:
        version_text = ""
    result = result.replace("{{version_text}}", version_text)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def compare_packages_prompt(
    packages: list[str], use_case: str, criteria: list[str] | None = None
) -> str:
    """Generate a detailed comparison prompt for multiple PyPI packages."""
    # Step 3: Call Prompt generator
    template = await compare_packages(packages, use_case, criteria)

    # Step 5: Parameter replacement
    packages_text = ", ".join(f"'{pkg}'" for pkg in packages)
    result = template.replace("{{packages_text}}", packages_text)
    result = result.replace("{{use_case}}", use_case)

    # Handle criteria parameter
    if criteria:
        criteria_text = (
            f"\n\nFocus particularly on these criteria: {', '.join(criteria)}"
        )
    else:
        criteria_text = ""
    result = result.replace("{{criteria_text}}", criteria_text)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def suggest_alternatives_prompt(
    package_name: str, reason: str, requirements: str | None = None
) -> str:
    """Generate a prompt for finding package alternatives."""
    # Step 3: Call Prompt generator
    template = await suggest_alternatives(package_name, reason, requirements)

    # Step 5: Parameter replacement
    result = template.replace("{{package_name}}", package_name)

    # Handle reason parameter with context mapping
    reason_context = {
        "deprecated": "the package is deprecated or no longer maintained",
        "security": "security vulnerabilities or concerns",
        "performance": "performance issues or requirements",
        "licensing": "licensing conflicts or restrictions",
        "maintenance": "poor maintenance or lack of updates",
        "features": "missing features or functionality gaps",
    }
    reason_text = reason_context.get(reason, reason)
    result = result.replace("{{reason_text}}", reason_text)

    # Handle requirements parameter
    if requirements:
        requirements_text = f"\n\nSpecific requirements: {requirements}"
    else:
        requirements_text = ""
    result = result.replace("{{requirements_text}}", requirements_text)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def resolve_dependency_conflicts_prompt(
    conflicts: list[str],
    python_version: str | None = None,
    project_context: str | None = None,
) -> str:
    """Generate a prompt for resolving dependency conflicts."""
    messages = await resolve_dependency_conflicts(
        conflicts, python_version, project_context
    )
    return messages[0].text


@mcp.prompt()
async def plan_version_upgrade_prompt(
    package_name: str,
    current_version: str,
    target_version: str | None = None,
    project_size: str | None = None,
) -> str:
    """Generate a prompt for planning package version upgrades."""
    messages = await plan_version_upgrade(
        package_name, current_version, target_version, project_size
    )
    return messages[0].text


@mcp.prompt()
async def audit_security_risks_prompt(
    packages: list[str],
    environment: str | None = None,
    compliance_requirements: str | None = None,
) -> str:
    """Generate a prompt for security risk auditing of packages."""
    messages = await audit_security_risks(
        packages, environment, compliance_requirements
    )
    return messages[0].text


@mcp.prompt()
async def plan_package_migration_prompt(
    from_package: str,
    to_package: str,
    codebase_size: str = "medium",
    timeline: str | None = None,
    team_size: int | None = None,
) -> str:
    """Generate a comprehensive package migration plan prompt."""
    messages = await plan_package_migration(
        from_package, to_package, codebase_size, timeline, team_size
    )
    return messages[0].text


@mcp.prompt()
async def generate_migration_checklist_prompt(
    migration_type: str, packages_involved: list[str], environment: str = "all"
) -> str:
    """Generate a detailed migration checklist prompt."""
    messages = await generate_migration_checklist(
        migration_type, packages_involved, environment
    )
    return messages[0].text


# Environment Analysis Prompts
@mcp.prompt()
async def analyze_environment_dependencies_prompt(
    environment_type: str = "local",
    python_version: str | None = None,
    project_path: str | None = None,
) -> str:
    """Generate a prompt for analyzing environment dependencies."""
    # Step 3: Call Prompt generator
    template = await analyze_environment_dependencies(
        environment_type, python_version, project_path
    )

    # Step 5: Parameter replacement
    result = template.replace("{{environment_type}}", environment_type)

    # Handle environment info
    env_info = f"({environment_type} environment)"
    if python_version:
        env_info += f" with Python {python_version}"
    if project_path:
        env_info += f" at {project_path}"
    result = result.replace("{{environment_info}}", env_info)

    # Handle command prefix based on environment
    command_prefix = "uvx " if environment_type in ["virtual", "uv"] else ""
    result = result.replace("{{command_prefix}}", command_prefix)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def check_outdated_packages_prompt(
    package_filter: str | None = None,
    severity_level: str = "all",
    include_dev_dependencies: bool = True,
) -> str:
    """Generate a prompt for checking outdated packages."""
    # Step 3: Call Prompt generator
    template = await check_outdated_packages(
        package_filter, severity_level, include_dev_dependencies
    )

    # Step 5: Parameter replacement
    result = template.replace("{{severity_level}}", severity_level)

    # Handle filter info
    if package_filter:
        filter_info = f" (filtering by: {package_filter})"
    else:
        filter_info = ""
    result = result.replace("{{filter_info}}", filter_info)

    # Handle dev dependencies
    if include_dev_dependencies:
        dev_deps_text = " including development dependencies"
    else:
        dev_deps_text = " excluding development dependencies"
    result = result.replace("{{dev_deps_text}}", dev_deps_text)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def generate_update_plan_prompt(
    update_strategy: str = "balanced",
    environment_constraints: str | None = None,
    testing_requirements: str | None = None,
) -> str:
    """Generate a prompt for creating package update plans."""
    # Step 3: Call Prompt generator
    template = await generate_update_plan(
        update_strategy, environment_constraints, testing_requirements
    )

    # Step 5: Parameter replacement
    result = template.replace("{{strategy}}", update_strategy)

    # Handle constraints
    if environment_constraints:
        constraints_text = f"\n\nEnvironment constraints: {environment_constraints}"
    else:
        constraints_text = ""
    result = result.replace("{{constraints_text}}", constraints_text)

    # Handle testing requirements
    if testing_requirements:
        testing_text = f"\n\nTesting requirements: {testing_requirements}"
    else:
        testing_text = ""
    result = result.replace("{{testing_text}}", testing_text)

    # Step 7: Return final prompt
    return result


# Trending Analysis Prompts
@mcp.prompt()
async def analyze_daily_trends_prompt(
    date: str = "today", category: str | None = None, limit: int = 20
) -> str:
    """Generate a prompt for analyzing daily PyPI trends."""
    # Step 3: Call Prompt generator
    template = await analyze_daily_trends(date, category, limit)

    # Step 5: Parameter replacement
    result = template.replace("{{date}}", date)
    result = result.replace("{{limit}}", str(limit))

    # Handle category filter
    if category:
        category_filter = f" focusing on {category} packages"
    else:
        category_filter = ""
    result = result.replace("{{category_filter}}", category_filter)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def find_trending_packages_prompt(
    time_period: str = "weekly", trend_type: str = "rising", domain: str | None = None
) -> str:
    """Generate a prompt for finding trending packages."""
    # Step 3: Call Prompt generator
    template = await find_trending_packages(time_period, trend_type, domain)

    # Step 5: Parameter replacement
    result = template.replace("{{time_period}}", time_period)
    result = result.replace("{{trend_type}}", trend_type)

    # Handle domain filter
    if domain:
        domain_filter = f" in the {domain} domain"
    else:
        domain_filter = ""
    result = result.replace("{{domain_filter}}", domain_filter)

    # Step 7: Return final prompt
    return result


@mcp.prompt()
async def track_package_updates_prompt(
    time_range: str = "today", update_type: str = "all", popular_only: bool = False
) -> str:
    """Generate a prompt for tracking recent package updates."""
    # Step 3: Call Prompt generator
    template = await track_package_updates(time_range, update_type, popular_only)

    # Step 5: Parameter replacement
    result = template.replace("{{time_range}}", time_range)
    result = result.replace("{{update_type}}", update_type)

    # Handle popularity filter
    if popular_only:
        popularity_filter = " (popular packages only)"
        popularity_description = "Popular packages with >1M downloads"
    else:
        popularity_filter = ""
        popularity_description = "All packages in the ecosystem"
    result = result.replace("{{popularity_filter}}", popularity_filter)
    result = result.replace("{{popularity_description}}", popularity_description)

    # Step 7: Return final prompt
    return result


@click.command()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Logging level",
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

"""Package query tools for PyPI MCP server."""

import logging
import re
from typing import Any

from ..core import InvalidPackageNameError, NetworkError, PyPIClient, PyPIError
from ..core.version_utils import sort_versions_semantically

logger = logging.getLogger(__name__)


def validate_version_format(version: str | None) -> bool:
    """Validate that a version string follows a reasonable format.

    Args:
        version: Version string to validate

    Returns:
        True if version format is valid or None, False otherwise
    """
    if version is None:
        return True

    # Basic validation for common version patterns
    # Supports: 1.0.0, 1.0, 1.0.0a1, 1.0.0b2, 1.0.0rc1, 1.0.0.dev1, 2.0.0-dev, etc.
    version_pattern = r"^[0-9]+(?:\.[0-9]+)*(?:[\.\-]?(?:a|b|rc|alpha|beta|dev|pre|post|final)[0-9]*)*$"
    return bool(re.match(version_pattern, version.strip(), re.IGNORECASE))


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
    # Sort versions semantically and get the most recent 10
    if releases:
        sorted_versions = sort_versions_semantically(list(releases.keys()), reverse=True)
        formatted["available_versions"] = sorted_versions[:10]  # Most recent 10 versions
    else:
        formatted["available_versions"] = []

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

    # Sort versions using semantic version ordering
    sorted_versions = sort_versions_semantically(list(releases.keys()), reverse=True)

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
    from ..core.dependency_parser import DependencyParser
    
    info = package_data.get("info", {})
    requires_dist = info.get("requires_dist", []) or []
    provides_extra = info.get("provides_extra", []) or []

    # Use the improved dependency parser
    parser = DependencyParser()
    requirements = parser.parse_requirements(requires_dist)
    categories = parser.categorize_dependencies(requirements, provides_extra)

    # Convert Requirements back to strings for JSON serialization
    runtime_deps = [str(req) for req in categories["runtime"]]
    dev_deps = [str(req) for req in categories["development"]]
    
    # Convert optional dependencies (extras) to string format
    optional_deps = {}
    for extra_name, reqs in categories["extras"].items():
        optional_deps[extra_name] = [str(req) for req in reqs]

    # Separate development and non-development optional dependencies
    dev_optional_deps = {}
    non_dev_optional_deps = {}
    
    # Define development-related extra names (same as in DependencyParser)
    dev_extra_names = {
        'dev', 'development', 'test', 'testing', 'tests', 'lint', 'linting',
        'doc', 'docs', 'documentation', 'build', 'check', 'cover', 'coverage',
        'type', 'typing', 'mypy', 'style', 'format', 'quality'
    }
    
    for extra_name, deps in optional_deps.items():
        if extra_name.lower() in dev_extra_names:
            dev_optional_deps[extra_name] = deps
        else:
            non_dev_optional_deps[extra_name] = deps

    return {
        "package_name": info.get("name", ""),
        "version": info.get("version", ""),
        "requires_python": info.get("requires_python", ""),
        "runtime_dependencies": runtime_deps,
        "development_dependencies": dev_deps,
        "optional_dependencies": non_dev_optional_deps,
        "development_optional_dependencies": dev_optional_deps,
        "provides_extra": provides_extra,
        "total_dependencies": len(requires_dist),
        "dependency_summary": {
            "runtime_count": len(runtime_deps),
            "dev_count": len(dev_deps),
            "optional_groups": len(non_dev_optional_deps),
            "dev_optional_groups": len(dev_optional_deps),
            "total_optional": sum(len(deps) for deps in non_dev_optional_deps.values()),
            "total_dev_optional": sum(len(deps) for deps in dev_optional_deps.values()),
            "provides_extra_count": len(provides_extra),
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
            package_data = await client.get_package_info(package_name, version=None)
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
            package_data = await client.get_package_info(package_name, version=None)
            return format_version_info(package_data)
    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying versions for {package_name}: {e}")
        raise NetworkError(f"Failed to query package versions: {e}", e) from e


async def query_package_dependencies(
    package_name: str, 
    version: str | None = None, 
    include_transitive: bool = False,
    max_depth: int = 5,
    python_version: str | None = None
) -> dict[str, Any]:
    """Query package dependency information from PyPI.

    Args:
        package_name: Name of the package to query
        version: Specific version to query (optional, defaults to latest)
        include_transitive: Whether to include transitive dependencies (default: False)
        max_depth: Maximum recursion depth for transitive dependencies (default: 5)
        python_version: Target Python version for dependency filtering (optional)

    Returns:
        Formatted dependency information with optional transitive dependencies

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found or version doesn't exist
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    # Validate version format if provided
    if version and not validate_version_format(version):
        raise InvalidPackageNameError(f"Invalid version format: {version}")

    logger.info(
        f"Querying dependencies for package: {package_name}"
        + (f" version {version}" if version else " (latest)")
        + (f" with transitive dependencies (max depth: {max_depth})" if include_transitive else " (direct only)")
    )

    try:
        if include_transitive:
            # Use the comprehensive dependency resolver for transitive dependencies
            from .dependency_resolver import resolve_package_dependencies
            
            result = await resolve_package_dependencies(
                package_name=package_name,
                python_version=python_version,
                include_extras=[],
                include_dev=False,
                max_depth=max_depth
            )
            
            # Format the transitive dependency result to match expected structure
            return format_transitive_dependency_info(result, package_name, version)
        else:
            # Use direct dependency logic with version support
            async with PyPIClient() as client:
                # Pass the version parameter to get_package_info
                package_data = await client.get_package_info(package_name, version=version)
                return format_dependency_info(package_data)
    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error querying dependencies for {package_name}: {e}")
        raise NetworkError(f"Failed to query package dependencies: {e}", e) from e


def format_transitive_dependency_info(
    resolver_result: dict[str, Any], package_name: str, version: str | None = None
) -> dict[str, Any]:
    """Format transitive dependency information for MCP response.

    Args:
        resolver_result: Result from dependency resolver
        package_name: Original package name
        version: Specific version (if any)

    Returns:
        Formatted transitive dependency information
    """
    # Get the main package from dependency tree
    normalized_name = package_name.lower().replace("_", "-")
    dependency_tree = resolver_result.get("dependency_tree", {})
    summary = resolver_result.get("summary", {})
    
    main_package = dependency_tree.get(normalized_name, {})
    
    # Build the response in the same format as direct dependencies but with tree structure
    result = {
        "package_name": package_name,
        "version": main_package.get("version", "unknown"),
        "requires_python": main_package.get("requires_python", ""),
        "include_transitive": True,
        "max_depth": summary.get("max_depth", 0),
        "python_version": resolver_result.get("python_version"),
        
        # Direct dependencies (same as before)
        "runtime_dependencies": main_package.get("dependencies", {}).get("runtime", []),
        "development_dependencies": main_package.get("dependencies", {}).get("development", []),
        "optional_dependencies": main_package.get("dependencies", {}).get("extras", {}),
        
        # Transitive dependency information
        "transitive_dependencies": {
            "dependency_tree": _build_dependency_tree_structure(dependency_tree, normalized_name),
            "all_packages": _extract_all_packages_info(dependency_tree),
            "circular_dependencies": _detect_circular_dependencies(dependency_tree),
            "depth_analysis": _analyze_dependency_depths(dependency_tree),
        },
        
        # Enhanced summary statistics
        "dependency_summary": {
            "direct_runtime_count": len(main_package.get("dependencies", {}).get("runtime", [])),
            "direct_dev_count": len(main_package.get("dependencies", {}).get("development", [])),
            "direct_optional_groups": len(main_package.get("dependencies", {}).get("extras", {})),
            "total_transitive_packages": summary.get("total_packages", 0) - 1,  # Exclude main package
            "total_runtime_dependencies": summary.get("total_runtime_dependencies", 0),
            "total_development_dependencies": summary.get("total_development_dependencies", 0),
            "total_extra_dependencies": summary.get("total_extra_dependencies", 0),
            "max_dependency_depth": summary.get("max_depth", 0),
            "complexity_score": _calculate_complexity_score(summary),
        },
        
        # Performance and health metrics
        "analysis": {
            "resolution_stats": summary,
            "potential_conflicts": _analyze_potential_conflicts(dependency_tree),
            "maintenance_concerns": _analyze_maintenance_concerns(dependency_tree),
            "performance_impact": _assess_performance_impact(summary),
        }
    }
    
    return result


def _build_dependency_tree_structure(
    dependency_tree: dict[str, Any], root_package: str, visited: set[str] | None = None
) -> dict[str, Any]:
    """Build a hierarchical dependency tree structure."""
    if visited is None:
        visited = set()
        
    if root_package in visited:
        return {"circular_reference": True, "package_name": root_package}
        
    visited.add(root_package)
    
    if root_package not in dependency_tree:
        return {}
        
    package_info = dependency_tree[root_package]
    children = package_info.get("children", {})
    
    tree_node = {
        "package_name": package_info.get("name", root_package),
        "version": package_info.get("version", "unknown"),
        "depth": package_info.get("depth", 0),
        "requires_python": package_info.get("requires_python", ""),
        "dependencies": package_info.get("dependencies", {}),
        "children": {}
    }
    
    # Recursively build children (with visited tracking to prevent infinite loops)
    for child_name in children:
        if child_name not in visited:
            tree_node["children"][child_name] = _build_dependency_tree_structure(
                dependency_tree, child_name, visited.copy()
            )
        else:
            tree_node["children"][child_name] = {
                "circular_reference": True, 
                "package_name": child_name
            }
    
    return tree_node


def _extract_all_packages_info(dependency_tree: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract comprehensive information about all packages in the dependency tree."""
    all_packages = {}
    
    for package_name, package_info in dependency_tree.items():
        all_packages[package_name] = {
            "name": package_info.get("name", package_name),
            "version": package_info.get("version", "unknown"),
            "depth": package_info.get("depth", 0),
            "requires_python": package_info.get("requires_python", ""),
            "direct_dependencies": {
                "runtime": package_info.get("dependencies", {}).get("runtime", []),
                "development": package_info.get("dependencies", {}).get("development", []),
                "extras": package_info.get("dependencies", {}).get("extras", {}),
            },
            "dependency_count": {
                "runtime": len(package_info.get("dependencies", {}).get("runtime", [])),
                "development": len(package_info.get("dependencies", {}).get("development", [])),
                "total_extras": sum(len(deps) for deps in package_info.get("dependencies", {}).get("extras", {}).values()),
            }
        }
    
    return all_packages


def _detect_circular_dependencies(dependency_tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect circular dependencies in the dependency tree."""
    circular_deps = []
    
    def dfs(package_name: str, path: list[str], visited: set[str]) -> None:
        if package_name in path:
            # Found a circular dependency
            cycle_start = path.index(package_name)
            cycle = path[cycle_start:] + [package_name]
            circular_deps.append({
                "cycle": cycle,
                "length": len(cycle) - 1,
                "packages_involved": list(set(cycle))
            })
            return
            
        if package_name in visited or package_name not in dependency_tree:
            return
            
        visited.add(package_name)
        path.append(package_name)
        
        # Check children
        children = dependency_tree[package_name].get("children", {})
        for child_name in children:
            dfs(child_name, path.copy(), visited)
    
    # Start DFS from each package
    for package_name in dependency_tree:
        dfs(package_name, [], set())
    
    # Remove duplicates
    unique_cycles = []
    seen_cycles = set()
    
    for cycle_info in circular_deps:
        cycle_set = frozenset(cycle_info["packages_involved"])
        if cycle_set not in seen_cycles:
            seen_cycles.add(cycle_set)
            unique_cycles.append(cycle_info)
    
    return unique_cycles


def _analyze_dependency_depths(dependency_tree: dict[str, Any]) -> dict[str, Any]:
    """Analyze the depth distribution of dependencies."""
    depth_counts = {}
    depth_packages = {}
    
    for package_name, package_info in dependency_tree.items():
        depth = package_info.get("depth", 0)
        
        if depth not in depth_counts:
            depth_counts[depth] = 0
            depth_packages[depth] = []
            
        depth_counts[depth] += 1
        depth_packages[depth].append(package_name)
    
    max_depth = max(depth_counts.keys()) if depth_counts else 0
    
    return {
        "max_depth": max_depth,
        "depth_distribution": depth_counts,
        "packages_by_depth": depth_packages,
        "average_depth": sum(d * c for d, c in depth_counts.items()) / sum(depth_counts.values()) if depth_counts else 0,
        "depth_analysis": {
            "shallow_deps": depth_counts.get(1, 0),  # Direct dependencies
            "deep_deps": sum(count for depth, count in depth_counts.items() if depth > 2),
            "leaf_packages": [pkg for pkg, info in dependency_tree.items() if not info.get("children")]
        }
    }


def _calculate_complexity_score(summary: dict[str, Any]) -> dict[str, Any]:
    """Calculate a complexity score for the dependency tree."""
    total_packages = summary.get("total_packages", 0)
    max_depth = summary.get("max_depth", 0)
    total_deps = summary.get("total_runtime_dependencies", 0)
    
    # Simple complexity scoring (can be enhanced)
    base_score = total_packages * 0.3
    depth_penalty = max_depth * 1.5
    dependency_penalty = total_deps * 0.1
    
    complexity_score = base_score + depth_penalty + dependency_penalty
    
    # Classify complexity
    if complexity_score < 10:
        complexity_level = "low"
        recommendation = "Simple dependency structure, low maintenance overhead"
    elif complexity_score < 30:
        complexity_level = "moderate"
        recommendation = "Moderate complexity, manageable with proper tooling"
    elif complexity_score < 60:
        complexity_level = "high"
        recommendation = "High complexity, consider dependency management strategies"
    else:
        complexity_level = "very_high"
        recommendation = "Very high complexity, significant maintenance overhead expected"
    
    return {
        "score": round(complexity_score, 2),
        "level": complexity_level,
        "recommendation": recommendation,
        "factors": {
            "total_packages": total_packages,
            "max_depth": max_depth,
            "total_dependencies": total_deps,
        }
    }


def _analyze_potential_conflicts(dependency_tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze potential version conflicts in dependencies."""
    # This is a simplified analysis - in a real implementation, 
    # you'd parse version constraints and check for conflicts
    package_versions = {}
    potential_conflicts = []
    
    for package_name, package_info in dependency_tree.items():
        runtime_deps = package_info.get("dependencies", {}).get("runtime", [])
        
        for dep_str in runtime_deps:
            # Basic parsing of "package>=version" format
            if ">=" in dep_str or "==" in dep_str or "<" in dep_str or ">" in dep_str:
                parts = dep_str.replace(">=", "@").replace("==", "@").replace("<", "@").replace(">", "@")
                dep_name = parts.split("@")[0].strip()
                
                if dep_name not in package_versions:
                    package_versions[dep_name] = []
                package_versions[dep_name].append({
                    "constraint": dep_str,
                    "required_by": package_name
                })
    
    # Look for packages with multiple version constraints
    for dep_name, constraints in package_versions.items():
        if len(constraints) > 1:
            potential_conflicts.append({
                "package": dep_name,
                "conflicting_constraints": constraints,
                "severity": "potential" if len(constraints) == 2 else "high"
            })
    
    return potential_conflicts


def _analyze_maintenance_concerns(dependency_tree: dict[str, Any]) -> dict[str, Any]:
    """Analyze maintenance concerns in the dependency tree."""
    total_packages = len(dependency_tree)
    packages_without_version = sum(
        1 for info in dependency_tree.values() 
        if info.get("version") in ["unknown", "", None]
    )
    
    packages_without_python_req = sum(
        1 for info in dependency_tree.values()
        if not info.get("requires_python")
    )
    
    # Calculate dependency concentration (packages with many dependencies)
    high_dep_packages = [
        {
            "name": name,
            "dependency_count": len(info.get("dependencies", {}).get("runtime", []))
        }
        for name, info in dependency_tree.items()
        if len(info.get("dependencies", {}).get("runtime", [])) > 5
    ]
    
    return {
        "total_packages": total_packages,
        "packages_without_version_info": packages_without_version,
        "packages_without_python_requirements": packages_without_python_req,
        "high_dependency_packages": high_dep_packages,
        "maintenance_risk_score": {
            "score": round(
                (packages_without_version / total_packages * 100) +
                (len(high_dep_packages) / total_packages * 50), 2
            ) if total_packages > 0 else 0,
            "level": "low" if total_packages < 10 else "moderate" if total_packages < 30 else "high"
        }
    }


def _assess_performance_impact(summary: dict[str, Any]) -> dict[str, Any]:
    """Assess the performance impact of the dependency tree."""
    total_packages = summary.get("total_packages", 0)
    max_depth = summary.get("max_depth", 0)
    
    # Estimate installation time (rough approximation)
    estimated_install_time = total_packages * 2 + max_depth * 5  # seconds
    
    # Estimate memory footprint (very rough)
    estimated_memory_mb = total_packages * 10 + max_depth * 5
    
    # Performance recommendations
    recommendations = []
    if total_packages > 50:
        recommendations.append("Consider using virtual environments to isolate dependencies")
    if max_depth > 5:
        recommendations.append("Deep dependency chains may slow resolution and installation")
    if total_packages > 100:
        recommendations.append("Consider dependency analysis tools for large projects")
    
    return {
        "estimated_install_time_seconds": estimated_install_time,
        "estimated_memory_footprint_mb": estimated_memory_mb,
        "performance_level": (
            "good" if total_packages < 20
            else "moderate" if total_packages < 50
            else "concerning"
        ),
        "recommendations": recommendations,
        "metrics": {
            "package_count_impact": "low" if total_packages < 20 else "high",
            "depth_impact": "low" if max_depth < 4 else "high",
            "resolution_complexity": "simple" if total_packages < 10 else "complex"
        }
    }

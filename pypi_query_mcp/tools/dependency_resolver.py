"""Dependency resolution tools for PyPI packages."""

import logging
from typing import Any

from ..core import PyPIClient, PyPIError
from ..core.dependency_parser import DependencyParser
from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
)

logger = logging.getLogger(__name__)


class DependencyResolver:
    """Resolves package dependencies recursively."""

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.parser = DependencyParser()
        self.resolved_cache: dict[str, dict[str, Any]] = {}

    async def resolve_dependencies(
        self,
        package_name: str,
        python_version: str | None = None,
        include_extras: list[str] | None = None,
        include_dev: bool = False,
        max_depth: int | None = None,
    ) -> dict[str, Any]:
        """Resolve all dependencies for a package recursively.

        Args:
            package_name: Name of the package to resolve
            python_version: Target Python version (e.g., "3.10")
            include_extras: List of extra dependencies to include
            include_dev: Whether to include development dependencies
            max_depth: Maximum recursion depth (overrides instance default)

        Returns:
            Dictionary containing resolved dependency tree
        """
        if not package_name or not package_name.strip():
            raise InvalidPackageNameError(package_name)

        max_depth = max_depth or self.max_depth
        include_extras = include_extras or []

        logger.info(
            f"Resolving dependencies for {package_name} (Python {python_version})"
        )

        # Track visited packages to avoid circular dependencies
        visited: set[str] = set()
        dependency_tree = {}

        try:
            await self._resolve_recursive(
                package_name=package_name,
                python_version=python_version,
                include_extras=include_extras,
                include_dev=include_dev,
                visited=visited,
                dependency_tree=dependency_tree,
                current_depth=0,
                max_depth=max_depth,
            )

            # Check if main package was resolved
            normalized_name = package_name.lower().replace("_", "-")
            if normalized_name not in dependency_tree:
                raise PackageNotFoundError(
                    f"Package '{package_name}' not found on PyPI"
                )

            # Generate summary
            summary = self._generate_dependency_summary(dependency_tree)

            return {
                "package_name": package_name,
                "python_version": python_version,
                "include_extras": include_extras,
                "include_dev": include_dev,
                "dependency_tree": dependency_tree,
                "summary": summary,
            }

        except PyPIError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error resolving dependencies for {package_name}: {e}"
            )
            raise NetworkError(f"Failed to resolve dependencies: {e}", e) from e

    async def _resolve_recursive(
        self,
        package_name: str,
        python_version: str | None,
        include_extras: list[str],
        include_dev: bool,
        visited: set[str],
        dependency_tree: dict[str, Any],
        current_depth: int,
        max_depth: int,
    ) -> None:
        """Recursively resolve dependencies."""

        # Normalize package name
        normalized_name = package_name.lower().replace("_", "-")

        # Check if already visited or max depth reached
        if normalized_name in visited or current_depth >= max_depth:
            return

        visited.add(normalized_name)

        try:
            # Get package information
            async with PyPIClient() as client:
                package_data = await client.get_package_info(package_name)

            info = package_data.get("info", {})
            requires_dist = info.get("requires_dist", []) or []

            # Parse requirements
            requirements = self.parser.parse_requirements(requires_dist)

            # Filter by Python version if specified
            if python_version:
                requirements = self.parser.filter_requirements_by_python_version(
                    requirements, python_version
                )

            # Categorize dependencies
            categorized = self.parser.categorize_dependencies(requirements)

            # Build dependency info for this package
            package_info = {
                "name": info.get("name", package_name),
                "version": info.get("version", "unknown"),
                "requires_python": info.get("requires_python", ""),
                "dependencies": {
                    "runtime": [str(req) for req in categorized["runtime"]],
                    "development": [str(req) for req in categorized["development"]]
                    if include_dev
                    else [],
                    "extras": {},
                },
                "depth": current_depth,
                "children": {},
            }

            # Add requested extras
            for extra in include_extras:
                if extra in categorized["extras"]:
                    package_info["dependencies"]["extras"][extra] = [
                        str(req) for req in categorized["extras"][extra]
                    ]

            dependency_tree[normalized_name] = package_info

            # Collect all dependencies to resolve
            deps_to_resolve = []
            deps_to_resolve.extend(categorized["runtime"])

            if include_dev:
                deps_to_resolve.extend(categorized["development"])

            for extra in include_extras:
                if extra in categorized["extras"]:
                    deps_to_resolve.extend(categorized["extras"][extra])

            # Resolve child dependencies
            for dep_req in deps_to_resolve:
                dep_name = dep_req.name
                if dep_name.lower() not in visited:
                    await self._resolve_recursive(
                        package_name=dep_name,
                        python_version=python_version,
                        include_extras=[],  # Don't propagate extras to children
                        include_dev=False,  # Don't propagate dev deps to children
                        visited=visited,
                        dependency_tree=dependency_tree,
                        current_depth=current_depth + 1,
                        max_depth=max_depth,
                    )

                    # Add to children if resolved
                    if dep_name.lower() in dependency_tree:
                        package_info["children"][dep_name.lower()] = dependency_tree[
                            dep_name.lower()
                        ]

        except PackageNotFoundError:
            logger.warning(f"Package {package_name} not found, skipping")
        except Exception as e:
            logger.error(f"Error resolving {package_name}: {e}")
            # Continue with other dependencies

    def _generate_dependency_summary(
        self, dependency_tree: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate summary statistics for the dependency tree."""

        total_packages = len(dependency_tree)
        total_runtime_deps = 0
        total_dev_deps = 0
        total_extra_deps = 0
        max_depth = 0

        for package_info in dependency_tree.values():
            total_runtime_deps += len(package_info["dependencies"]["runtime"])
            total_dev_deps += len(package_info["dependencies"]["development"])

            for extra_deps in package_info["dependencies"]["extras"].values():
                total_extra_deps += len(extra_deps)

            max_depth = max(max_depth, package_info["depth"])

        return {
            "total_packages": total_packages,
            "total_runtime_dependencies": total_runtime_deps,
            "total_development_dependencies": total_dev_deps,
            "total_extra_dependencies": total_extra_deps,
            "max_depth": max_depth,
            "package_list": list(dependency_tree.keys()),
        }


async def resolve_package_dependencies(
    package_name: str,
    python_version: str | None = None,
    include_extras: list[str] | None = None,
    include_dev: bool = False,
    max_depth: int = 5,
) -> dict[str, Any]:
    """Resolve package dependencies with comprehensive analysis.

    Args:
        package_name: Name of the package to resolve
        python_version: Target Python version (e.g., "3.10")
        include_extras: List of extra dependencies to include
        include_dev: Whether to include development dependencies
        max_depth: Maximum recursion depth

    Returns:
        Comprehensive dependency resolution results
    """
    resolver = DependencyResolver(max_depth=max_depth)
    return await resolver.resolve_dependencies(
        package_name=package_name,
        python_version=python_version,
        include_extras=include_extras,
        include_dev=include_dev,
    )

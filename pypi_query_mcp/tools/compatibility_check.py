"""Python version compatibility checking tools for PyPI MCP server."""

import logging
from typing import Any

from ..core import InvalidPackageNameError, NetworkError, PyPIClient, PyPIError
from ..core.version_utils import VersionCompatibility

logger = logging.getLogger(__name__)


async def check_python_compatibility(
    package_name: str, target_python_version: str, use_cache: bool = True
) -> dict[str, Any]:
    """Check if a package is compatible with a specific Python version.

    Args:
        package_name: Name of the package to check
        target_python_version: Target Python version (e.g., "3.9", "3.10.5")
        use_cache: Whether to use cached package data

    Returns:
        Dictionary containing compatibility information

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    if not target_python_version or not target_python_version.strip():
        raise ValueError("Target Python version cannot be empty")

    logger.info(
        f"Checking Python {target_python_version} compatibility for package: {package_name}"
    )

    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name, use_cache)

            info = package_data.get("info", {})
            requires_python = info.get("requires_python")
            classifiers = info.get("classifiers", [])

            # Perform compatibility check
            compat_checker = VersionCompatibility()
            result = compat_checker.check_version_compatibility(
                target_python_version, requires_python, classifiers
            )

            # Add package information to result
            result.update(
                {
                    "package_name": info.get("name", package_name),
                    "package_version": info.get("version", ""),
                    "requires_python": requires_python,
                    "supported_implementations": compat_checker.extract_python_implementations(
                        classifiers
                    ),
                    "classifier_versions": sorted(
                        compat_checker.extract_python_versions_from_classifiers(
                            classifiers
                        )
                    ),
                }
            )

            return result

    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking compatibility for {package_name}: {e}")
        raise NetworkError(f"Failed to check Python compatibility: {e}", e) from e


async def get_compatible_python_versions(
    package_name: str, python_versions: list[str] | None = None, use_cache: bool = True
) -> dict[str, Any]:
    """Get list of Python versions compatible with a package.

    Args:
        package_name: Name of the package to check
        python_versions: List of Python versions to check (optional)
        use_cache: Whether to use cached package data

    Returns:
        Dictionary containing compatibility information for multiple versions

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)

    logger.info(f"Getting compatible Python versions for package: {package_name}")

    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name, use_cache)

            info = package_data.get("info", {})
            requires_python = info.get("requires_python")
            classifiers = info.get("classifiers", [])

            # Get compatibility information
            compat_checker = VersionCompatibility()
            result = compat_checker.get_compatible_versions(
                requires_python, classifiers, python_versions
            )

            # Add package information to result
            result.update(
                {
                    "package_name": info.get("name", package_name),
                    "package_version": info.get("version", ""),
                    "requires_python": requires_python,
                    "supported_implementations": sorted(
                        compat_checker.extract_python_implementations(classifiers)
                    ),
                    "classifier_versions": sorted(
                        compat_checker.extract_python_versions_from_classifiers(
                            classifiers
                        )
                    ),
                }
            )

            return result

    except PyPIError:
        # Re-raise PyPI-specific errors
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error getting compatible versions for {package_name}: {e}"
        )
        raise NetworkError(f"Failed to get compatible Python versions: {e}", e) from e


async def suggest_python_version_for_packages(
    package_names: list[str], use_cache: bool = True
) -> dict[str, Any]:
    """Suggest optimal Python version for a list of packages.

    Args:
        package_names: List of package names to analyze
        use_cache: Whether to use cached package data

    Returns:
        Dictionary containing version suggestions and compatibility matrix

    Raises:
        ValueError: If package_names is empty
        NetworkError: For network-related errors
    """
    if not package_names:
        raise ValueError("Package names list cannot be empty")

    logger.info(
        f"Analyzing Python version compatibility for {len(package_names)} packages"
    )

    # Default Python versions to analyze
    python_versions = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12"]

    compatibility_matrix = {}
    package_details = {}
    errors = {}

    async with PyPIClient() as client:
        for package_name in package_names:
            try:
                package_data = await client.get_package_info(package_name, use_cache)
                info = package_data.get("info", {})

                requires_python = info.get("requires_python")
                classifiers = info.get("classifiers", [])

                compat_checker = VersionCompatibility()
                compat_result = compat_checker.get_compatible_versions(
                    requires_python, classifiers, python_versions
                )

                # Store compatibility for this package
                compatible_versions = [
                    v["version"] for v in compat_result["compatible_versions"]
                ]
                compatibility_matrix[package_name] = compatible_versions

                package_details[package_name] = {
                    "version": info.get("version", ""),
                    "requires_python": requires_python,
                    "compatible_versions": compatible_versions,
                    "compatibility_rate": compat_result["compatibility_rate"],
                }

            except Exception as e:
                logger.warning(f"Failed to analyze package {package_name}: {e}")
                errors[package_name] = str(e)
                compatibility_matrix[package_name] = []

    # Find common compatible versions
    if compatibility_matrix:
        all_versions = set(python_versions)
        common_versions = all_versions.copy()

        for _package_name, compatible in compatibility_matrix.items():
            if compatible:  # Only consider packages with known compatibility
                common_versions &= set(compatible)
    else:
        common_versions = set()

    # Generate recommendations
    recommendations = []
    if common_versions:
        latest_common = max(
            common_versions, key=lambda x: tuple(map(int, x.split(".")))
        )
        recommendations.append(
            f"✅ Recommended Python version: {latest_common} "
            f"(compatible with all {len([p for p in compatibility_matrix if compatibility_matrix[p]])} packages)"
        )

        if len(common_versions) > 1:
            all_common = sorted(
                common_versions, key=lambda x: tuple(map(int, x.split(".")))
            )
            recommendations.append(
                f"📋 All compatible versions: {', '.join(all_common)}"
            )
    else:
        recommendations.append(
            "⚠️  No Python version is compatible with all packages. "
            "Consider updating packages or using different versions."
        )

        # Find the version compatible with most packages
        version_scores = {}
        for version in python_versions:
            score = sum(
                1
                for compatible in compatibility_matrix.values()
                if version in compatible
            )
            version_scores[version] = score

        if version_scores:
            best_version = max(version_scores, key=version_scores.get)
            best_score = version_scores[best_version]
            total_packages = len(
                [p for p in compatibility_matrix if compatibility_matrix[p]]
            )

            if best_score > 0:
                recommendations.append(
                    f"📊 Best compromise: Python {best_version} "
                    f"(compatible with {best_score}/{total_packages} packages)"
                )

    return {
        "analyzed_packages": len(package_names),
        "successful_analyses": len(package_details),
        "failed_analyses": len(errors),
        "common_compatible_versions": sorted(common_versions),
        "recommended_version": max(
            common_versions, key=lambda x: tuple(map(int, x.split(".")))
        )
        if common_versions
        else None,
        "compatibility_matrix": compatibility_matrix,
        "package_details": package_details,
        "errors": errors,
        "recommendations": recommendations,
        "python_versions_analyzed": python_versions,
    }

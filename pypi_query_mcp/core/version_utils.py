"""Version parsing and compatibility checking utilities."""

import logging
import re
from typing import Any

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

logger = logging.getLogger(__name__)


class VersionCompatibility:
    """Utility class for Python version compatibility checking."""

    def __init__(self):
        """Initialize version compatibility checker."""
        # Common Python version patterns in classifiers
        self.python_classifier_pattern = re.compile(
            r"Programming Language :: Python :: (\d+(?:\.\d+)*)"
        )

        # Implementation-specific classifiers
        self.implementation_pattern = re.compile(
            r"Programming Language :: Python :: Implementation :: (\w+)"
        )

    def parse_requires_python(self, requires_python: str) -> SpecifierSet | None:
        """Parse requires_python field into a SpecifierSet.

        Args:
            requires_python: The requires_python string from package metadata

        Returns:
            SpecifierSet object or None if parsing fails
        """
        if not requires_python or not requires_python.strip():
            return None

        try:
            # Clean up the version specification
            cleaned = requires_python.strip()
            return SpecifierSet(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse requires_python '{requires_python}': {e}")
            return None

    def extract_python_versions_from_classifiers(
        self, classifiers: list[str]
    ) -> set[str]:
        """Extract Python version information from classifiers.

        Args:
            classifiers: List of classifier strings

        Returns:
            Set of Python version strings
        """
        versions = set()

        for classifier in classifiers:
            match = self.python_classifier_pattern.search(classifier)
            if match:
                version = match.group(1)
                versions.add(version)

        return versions

    def extract_python_implementations(self, classifiers: list[str]) -> set[str]:
        """Extract Python implementation information from classifiers.

        Args:
            classifiers: List of classifier strings

        Returns:
            Set of Python implementation names (CPython, PyPy, etc.)
        """
        implementations = set()

        for classifier in classifiers:
            match = self.implementation_pattern.search(classifier)
            if match:
                implementation = match.group(1)
                implementations.add(implementation)

        return implementations

    def check_version_compatibility(
        self,
        target_version: str,
        requires_python: str | None = None,
        classifiers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Check if a target Python version is compatible with package requirements.

        Args:
            target_version: Target Python version (e.g., "3.9", "3.10.5")
            requires_python: The requires_python specification
            classifiers: List of package classifiers

        Returns:
            Dictionary containing compatibility information
        """
        result = {
            "target_version": target_version,
            "is_compatible": False,
            "compatibility_source": None,
            "details": {},
            "warnings": [],
            "suggestions": [],
        }

        try:
            target_ver = Version(target_version)
        except InvalidVersion as e:
            result["warnings"].append(f"Invalid target version format: {e}")
            return result

        # Check requires_python first (more authoritative)
        if requires_python:
            spec_set = self.parse_requires_python(requires_python)
            if spec_set:
                is_compatible = target_ver in spec_set
                result.update(
                    {
                        "is_compatible": is_compatible,
                        "compatibility_source": "requires_python",
                        "details": {
                            "requires_python": requires_python,
                            "parsed_spec": str(spec_set),
                            "check_result": is_compatible,
                        },
                    }
                )

                if not is_compatible:
                    result["suggestions"].append(
                        f"Package requires Python {requires_python}, "
                        f"but target is {target_version}"
                    )

                return result

        # Fall back to classifiers if no requires_python
        if classifiers:
            supported_versions = self.extract_python_versions_from_classifiers(
                classifiers
            )
            implementations = self.extract_python_implementations(classifiers)

            if supported_versions:
                # Check if target version matches any supported version
                target_major_minor = f"{target_ver.major}.{target_ver.minor}"
                target_major = str(target_ver.major)

                is_compatible = (
                    target_version in supported_versions
                    or target_major_minor in supported_versions
                    or target_major in supported_versions
                )

                result.update(
                    {
                        "is_compatible": is_compatible,
                        "compatibility_source": "classifiers",
                        "details": {
                            "supported_versions": sorted(supported_versions),
                            "implementations": sorted(implementations),
                            "target_major_minor": target_major_minor,
                            "check_result": is_compatible,
                        },
                    }
                )

                if not is_compatible:
                    result["suggestions"].append(
                        f"Package supports Python versions: {', '.join(sorted(supported_versions))}, "
                        f"but target is {target_version}"
                    )

                return result

        # No version information available
        result["warnings"].append(
            "No Python version requirements found in package metadata"
        )
        result["suggestions"].append(
            "Consider checking package documentation for Python version compatibility"
        )

        return result

    def get_compatible_versions(
        self,
        requires_python: str | None = None,
        classifiers: list[str] | None = None,
        available_pythons: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get list of compatible Python versions for a package.

        Args:
            requires_python: The requires_python specification
            classifiers: List of package classifiers
            available_pythons: List of Python versions to check against

        Returns:
            Dictionary containing compatible versions and recommendations
        """
        if available_pythons is None:
            # Default Python versions to check
            available_pythons = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

        compatible = []
        incompatible = []

        for python_version in available_pythons:
            result = self.check_version_compatibility(
                python_version, requires_python, classifiers
            )

            if result["is_compatible"]:
                compatible.append(
                    {
                        "version": python_version,
                        "source": result["compatibility_source"],
                    }
                )
            else:
                incompatible.append(
                    {
                        "version": python_version,
                        "reason": result["suggestions"][0]
                        if result["suggestions"]
                        else "Unknown",
                    }
                )

        return {
            "compatible_versions": compatible,
            "incompatible_versions": incompatible,
            "total_checked": len(available_pythons),
            "compatibility_rate": len(compatible) / len(available_pythons)
            if available_pythons
            else 0,
            "recommendations": self._generate_recommendations(compatible, incompatible),
        }

    def _generate_recommendations(
        self, compatible: list[dict[str, Any]], incompatible: list[dict[str, Any]]
    ) -> list[str]:
        """Generate recommendations based on compatibility results.

        Args:
            compatible: List of compatible versions
            incompatible: List of incompatible versions

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if not compatible:
            recommendations.append(
                "⚠️  No compatible Python versions found. "
                "Check package documentation for requirements."
            )
        elif len(compatible) == 1:
            version = compatible[0]["version"]
            recommendations.append(
                f"📌 Only Python {version} is compatible with this package."
            )
        else:
            versions = [v["version"] for v in compatible]
            latest = max(versions, key=lambda x: tuple(map(int, x.split("."))))
            recommendations.append(
                f"✅ Compatible with Python {', '.join(versions)}. "
                f"Recommended: Python {latest}"
            )

        if len(incompatible) > len(compatible):
            recommendations.append(
                "⚠️  This package has limited Python version support. "
                "Consider using a more recent version of the package if available."
            )

        return recommendations

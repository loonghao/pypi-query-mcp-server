"""Dependency parsing utilities for PyPI packages."""

import logging
import re
from typing import Any

from packaging.requirements import Requirement
from packaging.version import Version

logger = logging.getLogger(__name__)


class DependencyParser:
    """Parser for Python package dependencies."""

    def __init__(self):
        self.parsed_cache: dict[str, list[Requirement]] = {}

    def parse_requirements(self, requires_dist: list[str]) -> list[Requirement]:
        """Parse requirements from requires_dist list.

        Args:
            requires_dist: List of requirement strings from PyPI metadata

        Returns:
            List of parsed Requirement objects
        """
        requirements = []

        for req_str in requires_dist or []:
            if not req_str or not req_str.strip():
                continue

            try:
                req = Requirement(req_str)
                requirements.append(req)
            except Exception as e:
                logger.warning(f"Failed to parse requirement '{req_str}': {e}")
                continue

        return requirements

    def filter_requirements_by_python_version(
        self, requirements: list[Requirement], python_version: str
    ) -> list[Requirement]:
        """Filter requirements based on Python version.

        Args:
            requirements: List of Requirement objects
            python_version: Target Python version (e.g., "3.10")

        Returns:
            Filtered list of requirements applicable to the Python version
        """
        filtered = []

        try:
            target_version = Version(python_version)
        except Exception as e:
            logger.warning(f"Invalid Python version '{python_version}': {e}")
            return requirements

        for req in requirements:
            if self._is_requirement_applicable(req, target_version):
                filtered.append(req)

        return filtered

    def _is_requirement_applicable(
        self, req: Requirement, python_version: Version
    ) -> bool:
        """Check if a requirement is applicable for the given Python version.

        Args:
            req: Requirement object
            python_version: Target Python version

        Returns:
            True if requirement applies to the Python version
        """
        if not req.marker:
            return True

        # Create environment for marker evaluation
        env = {
            "python_version": str(python_version),
            "python_full_version": str(python_version),
            "platform_system": "Linux",  # Default assumption
            "platform_machine": "x86_64",  # Default assumption
            "implementation_name": "cpython",
            "implementation_version": str(python_version),
        }

        try:
            return req.marker.evaluate(env)
        except Exception as e:
            logger.warning(f"Failed to evaluate marker for {req}: {e}")
            return True  # Include by default if evaluation fails

    def categorize_dependencies(
        self, requirements: list[Requirement]
    ) -> dict[str, list[Requirement]]:
        """Categorize dependencies into runtime, development, and optional groups.

        Args:
            requirements: List of Requirement objects

        Returns:
            Dictionary with categorized dependencies
        """
        categories = {"runtime": [], "development": [], "optional": {}, "extras": {}}

        for req in requirements:
            if not req.marker:
                # No marker means it's a runtime dependency
                categories["runtime"].append(req)
                continue

            marker_str = str(req.marker)

            # Check for extra dependencies
            if "extra ==" in marker_str:
                extra_match = re.search(r'extra\s*==\s*["\']([^"\']+)["\']', marker_str)
                if extra_match:
                    extra_name = extra_match.group(1)
                    if extra_name not in categories["extras"]:
                        categories["extras"][extra_name] = []
                    categories["extras"][extra_name].append(req)
                    continue

            # Check for development dependencies
            if any(
                keyword in marker_str.lower()
                for keyword in ["dev", "test", "lint", "doc"]
            ):
                categories["development"].append(req)
            else:
                categories["runtime"].append(req)

        return categories

    def extract_package_names(self, requirements: list[Requirement]) -> set[str]:
        """Extract package names from requirements.

        Args:
            requirements: List of Requirement objects

        Returns:
            Set of package names
        """
        return {req.name.lower() for req in requirements}

    def get_version_constraints(self, req: Requirement) -> dict[str, Any]:
        """Get version constraints from a requirement.

        Args:
            req: Requirement object

        Returns:
            Dictionary with version constraint information
        """
        if not req.specifier:
            return {"constraints": [], "allows_any": True}

        constraints = []
        for spec in req.specifier:
            constraints.append(
                {"operator": spec.operator, "version": str(spec.version)}
            )

        return {
            "constraints": constraints,
            "allows_any": len(constraints) == 0,
            "specifier_str": str(req.specifier),
        }

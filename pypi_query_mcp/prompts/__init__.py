"""MCP prompt templates for PyPI package queries.

This package contains FastMCP prompt implementations that provide
reusable templates for common PyPI package analysis and decision-making scenarios.
"""

from .dependency_management import (
    audit_security_risks,
    plan_version_upgrade,
    resolve_dependency_conflicts,
)
from .environment_analysis import (
    analyze_environment_dependencies,
    check_outdated_packages,
    generate_update_plan,
)
from .migration_guidance import (
    generate_migration_checklist,
    plan_package_migration,
)
from .package_analysis import (
    analyze_package_quality,
    compare_packages,
    suggest_alternatives,
)
from .trending_analysis import (
    analyze_daily_trends,
    find_trending_packages,
    track_package_updates,
)

__all__ = [
    # Package Analysis
    "analyze_package_quality",
    "compare_packages",
    "suggest_alternatives",
    # Dependency Management
    "resolve_dependency_conflicts",
    "plan_version_upgrade",
    "audit_security_risks",
    # Environment Analysis
    "analyze_environment_dependencies",
    "check_outdated_packages",
    "generate_update_plan",
    # Migration Guidance
    "plan_package_migration",
    "generate_migration_checklist",
    # Trending Analysis
    "analyze_daily_trends",
    "find_trending_packages",
    "track_package_updates",
]

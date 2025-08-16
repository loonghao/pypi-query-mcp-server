#!/usr/bin/env python3
"""
Example usage of the enhanced get_package_dependencies tool with transitive analysis.

This demonstrates how to use the new transitive dependency functionality.
"""

# Example MCP Tool Calls with the enhanced functionality

# Basic usage (backward compatible)
example_1 = {
    "tool": "get_package_dependencies",
    "parameters": {"package_name": "requests"},
}
# Returns: Direct dependencies only (existing behavior)

# Enable transitive dependencies
example_2 = {
    "tool": "get_package_dependencies",
    "parameters": {"package_name": "requests", "include_transitive": True},
}
# Returns: Complete dependency tree with analysis

# Advanced transitive analysis
example_3 = {
    "tool": "get_package_dependencies",
    "parameters": {
        "package_name": "django",
        "include_transitive": True,
        "max_depth": 3,
        "python_version": "3.11",
    },
}
# Returns: Filtered dependency tree for Python 3.11, max 3 levels deep

# Example expected response format for transitive dependencies:
example_response = {
    "package_name": "requests",
    "version": "2.31.0",
    "requires_python": ">=3.7",
    "include_transitive": True,
    "max_depth": 5,
    "python_version": "3.10",
    # Direct dependencies (same as before)
    "runtime_dependencies": [
        "urllib3>=1.21.1,<3",
        "certifi>=2017.4.17",
        "charset-normalizer>=2,<4",
        "idna>=2.5,<4",
    ],
    "development_dependencies": [],
    "optional_dependencies": {
        "security": ["pyOpenSSL>=0.14", "cryptography>=1.3.4"],
        "socks": ["PySocks>=1.5.6,!=1.5.7"],
    },
    # NEW: Transitive dependency information
    "transitive_dependencies": {
        "dependency_tree": {
            "package_name": "requests",
            "version": "2.31.0",
            "depth": 0,
            "children": {
                "urllib3": {
                    "package_name": "urllib3",
                    "version": "2.0.4",
                    "depth": 1,
                    "children": {},
                },
                "certifi": {
                    "package_name": "certifi",
                    "version": "2023.7.22",
                    "depth": 1,
                    "children": {},
                },
                "charset-normalizer": {
                    "package_name": "charset-normalizer",
                    "version": "3.2.0",
                    "depth": 1,
                    "children": {},
                },
                "idna": {
                    "package_name": "idna",
                    "version": "3.4",
                    "depth": 1,
                    "children": {},
                },
            },
        },
        "all_packages": {
            "requests": {
                "name": "requests",
                "version": "2.31.0",
                "depth": 0,
                "dependency_count": {"runtime": 4, "development": 0, "total_extras": 0},
            },
            "urllib3": {
                "name": "urllib3",
                "version": "2.0.4",
                "depth": 1,
                "dependency_count": {"runtime": 0, "development": 0, "total_extras": 0},
            },
            # ... other packages
        },
        "circular_dependencies": [],
        "depth_analysis": {
            "max_depth": 1,
            "depth_distribution": {"0": 1, "1": 4},
            "average_depth": 0.8,
            "shallow_deps": 4,
            "deep_deps": 0,
            "leaf_packages": ["urllib3", "certifi", "charset-normalizer", "idna"],
        },
    },
    # Enhanced summary statistics
    "dependency_summary": {
        "direct_runtime_count": 4,
        "direct_dev_count": 0,
        "direct_optional_groups": 2,
        "total_transitive_packages": 4,  # All dependencies
        "total_runtime_dependencies": 4,
        "total_development_dependencies": 0,
        "total_extra_dependencies": 0,
        "max_dependency_depth": 1,
        "complexity_score": {
            "score": 8.2,
            "level": "low",
            "recommendation": "Simple dependency structure, low maintenance overhead",
            "factors": {"total_packages": 5, "max_depth": 1, "total_dependencies": 4},
        },
    },
    # Performance and health analysis
    "analysis": {
        "resolution_stats": {
            "total_packages": 5,
            "total_runtime_dependencies": 4,
            "max_depth": 1,
        },
        "potential_conflicts": [],
        "maintenance_concerns": {
            "total_packages": 5,
            "packages_without_version_info": 0,
            "high_dependency_packages": [],
            "maintenance_risk_score": {"score": 0.0, "level": "low"},
        },
        "performance_impact": {
            "estimated_install_time_seconds": 15,
            "estimated_memory_footprint_mb": 65,
            "performance_level": "good",
            "recommendations": [],
            "metrics": {
                "package_count_impact": "low",
                "depth_impact": "low",
                "resolution_complexity": "simple",
            },
        },
    },
}

# Usage examples for different complexity levels
complexity_examples = {
    "simple_package": {
        "package": "six",
        "expected_packages": 1,  # No dependencies
        "complexity": "low",
    },
    "moderate_package": {
        "package": "requests",
        "expected_packages": 5,  # Few dependencies
        "complexity": "low",
    },
    "complex_package": {
        "package": "django",
        "expected_packages": 15,  # Moderate dependencies
        "complexity": "moderate",
    },
    "very_complex_package": {
        "package": "tensorflow",
        "expected_packages": 50,  # Many dependencies
        "complexity": "high",
    },
}

# Test cases for edge cases
edge_case_examples = {
    "circular_dependencies": {
        "description": "Package with circular dependency references",
        "expected_behavior": "Detected and reported in circular_dependencies array",
    },
    "deep_nesting": {
        "description": "Package with very deep dependency chains",
        "max_depth": 2,
        "expected_behavior": "Truncated at max_depth with depth tracking",
    },
    "version_conflicts": {
        "description": "Dependencies with conflicting version requirements",
        "expected_behavior": "Reported in potential_conflicts array",
    },
    "missing_packages": {
        "description": "Dependencies that don't exist on PyPI",
        "expected_behavior": "Graceful handling with warnings in logs",
    },
}

print("Enhanced get_package_dependencies Tool")
print("=====================================")
print()
print("New Parameters:")
print("- include_transitive: bool = False  # Enable transitive analysis")
print("- max_depth: int = 5                # Limit recursion depth")
print("- python_version: str | None = None # Filter by Python version")
print()
print("Key Features:")
print("✓ Backward compatible (include_transitive=False by default)")
print("✓ Circular dependency detection and prevention")
print("✓ Performance safeguards (max depth, caching)")
print("✓ Comprehensive analysis (complexity, performance, maintenance)")
print("✓ Detailed dependency tree structure")
print("✓ Version conflict detection")
print("✓ Python version filtering")
print()
print("See TRANSITIVE_DEPS_DOCUMENTATION.md for full details.")

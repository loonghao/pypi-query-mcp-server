#!/usr/bin/env python3
"""Simple test for the transitive dependency formatting functions."""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))


def test_formatting_functions():
    """Test the formatting functions directly."""
    print("Testing transitive dependency formatting functions...")

    # Sample data that mimics what the dependency resolver would return
    sample_resolver_result = {
        "package_name": "requests",
        "python_version": "3.10",
        "dependency_tree": {
            "requests": {
                "name": "requests",
                "version": "2.31.0",
                "requires_python": ">=3.7",
                "dependencies": {
                    "runtime": [
                        "urllib3>=1.21.1",
                        "certifi>=2017.4.17",
                        "charset-normalizer>=2.0",
                    ],
                    "development": [],
                    "extras": {},
                },
                "depth": 0,
                "children": {
                    "urllib3": {
                        "name": "urllib3",
                        "version": "2.0.4",
                        "requires_python": ">=3.7",
                        "dependencies": {
                            "runtime": [],
                            "development": [],
                            "extras": {},
                        },
                        "depth": 1,
                        "children": {},
                    },
                    "certifi": {
                        "name": "certifi",
                        "version": "2023.7.22",
                        "requires_python": ">=3.6",
                        "dependencies": {
                            "runtime": [],
                            "development": [],
                            "extras": {},
                        },
                        "depth": 1,
                        "children": {},
                    },
                },
            },
            "urllib3": {
                "name": "urllib3",
                "version": "2.0.4",
                "requires_python": ">=3.7",
                "dependencies": {"runtime": [], "development": [], "extras": {}},
                "depth": 1,
                "children": {},
            },
            "certifi": {
                "name": "certifi",
                "version": "2023.7.22",
                "requires_python": ">=3.6",
                "dependencies": {"runtime": [], "development": [], "extras": {}},
                "depth": 1,
                "children": {},
            },
        },
        "summary": {
            "total_packages": 3,
            "total_runtime_dependencies": 3,
            "total_development_dependencies": 0,
            "total_extra_dependencies": 0,
            "max_depth": 1,
            "package_list": ["requests", "urllib3", "certifi"],
        },
    }

    # Import the formatting function
    try:
        from pypi_query_mcp.tools.package_query import (
            _analyze_dependency_depths,
            _build_dependency_tree_structure,
            _calculate_complexity_score,
            _detect_circular_dependencies,
            _extract_all_packages_info,
            format_transitive_dependency_info,
        )

        # Test format_transitive_dependency_info
        print("✓ Successfully imported formatting functions")

        result = format_transitive_dependency_info(sample_resolver_result, "requests")

        print(f"✓ Formatted result for package: {result.get('package_name')}")
        print(f"  Include transitive: {result.get('include_transitive')}")
        print(f"  Version: {result.get('version')}")
        print(f"  Max depth: {result.get('max_depth')}")

        # Test transitive dependencies section
        transitive = result.get("transitive_dependencies", {})
        print(f"  All packages count: {len(transitive.get('all_packages', {}))}")
        print(
            f"  Circular dependencies: {len(transitive.get('circular_dependencies', []))}"
        )

        # Test dependency summary
        summary = result.get("dependency_summary", {})
        print(f"  Direct runtime count: {summary.get('direct_runtime_count')}")
        print(
            f"  Total transitive packages: {summary.get('total_transitive_packages')}"
        )
        print(f"  Complexity level: {summary.get('complexity_score', {}).get('level')}")

        # Test analysis section
        analysis = result.get("analysis", {})
        print(
            f"  Performance level: {analysis.get('performance_impact', {}).get('performance_level')}"
        )

        print("✓ All formatting functions working correctly")
        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing formatting functions: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_helper_functions():
    """Test individual helper functions."""
    print("\nTesting helper functions...")

    sample_tree = {
        "pkg-a": {
            "name": "pkg-a",
            "version": "1.0.0",
            "depth": 0,
            "children": {"pkg-b": {}, "pkg-c": {}},
        },
        "pkg-b": {"name": "pkg-b", "version": "2.0.0", "depth": 1, "children": {}},
        "pkg-c": {
            "name": "pkg-c",
            "version": "3.0.0",
            "depth": 1,
            "children": {"pkg-b": {}},  # Creates potential circular reference
        },
    }

    try:
        from pypi_query_mcp.tools.package_query import (
            _analyze_dependency_depths,
            _calculate_complexity_score,
            _extract_all_packages_info,
        )

        # Test _extract_all_packages_info
        all_packages = _extract_all_packages_info(sample_tree)
        print(f"✓ Extracted {len(all_packages)} packages")

        # Test _analyze_dependency_depths
        depth_analysis = _analyze_dependency_depths(sample_tree)
        print(f"✓ Depth analysis - max depth: {depth_analysis.get('max_depth')}")

        # Test _calculate_complexity_score
        sample_summary = {
            "total_packages": 3,
            "max_depth": 1,
            "total_runtime_dependencies": 2,
        }
        complexity = _calculate_complexity_score(sample_summary)
        print(
            f"✓ Complexity score: {complexity.get('score')} ({complexity.get('level')})"
        )

        return True

    except Exception as e:
        print(f"✗ Error testing helper functions: {e}")
        return False


def main():
    """Run tests."""
    print("Simple Test for Transitive Dependencies")
    print("=" * 50)

    results = []
    results.append(test_formatting_functions())
    results.append(test_helper_functions())

    print("\n" + "=" * 50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✓ All formatting tests passed!")
        return 0
    else:
        print("✗ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

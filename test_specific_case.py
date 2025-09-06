#!/usr/bin/env python3
"""Test the specific case mentioned in the task: 5.2rc1 vs 5.2.5"""

from pypi_query_mcp.core.version_utils import sort_versions_semantically


def test_specific_case():
    """Test the exact case mentioned in the task requirements."""
    print("=" * 60)
    print("Testing Specific Task Requirement")
    print("=" * 60)

    # The exact problem mentioned in the task
    versions = ["5.2rc1", "5.2.5"]

    # Old way (string sorting)
    old_sorted = sorted(versions, reverse=True)

    # New way (semantic sorting)
    new_sorted = sort_versions_semantically(versions, reverse=True)

    print(f"Original versions: {versions}")
    print(f"Old string sorting: {old_sorted}")
    print(f"New semantic sorting: {new_sorted}")
    print()

    print("Analysis:")
    print("  Problem: '5.2rc1' was appearing before '5.2.5' in string sorting")
    print(f"  String sorting result: {old_sorted[0]} comes first")
    print(f"  Semantic sorting result: {new_sorted[0]} comes first")
    print()

    if new_sorted == ["5.2.5", "5.2rc1"]:
        print("  ✅ SUCCESS: Semantic sorting correctly places 5.2.5 before 5.2rc1")
        print("  ✅ This fixes the issue described in the task!")
    else:
        print("  ❌ FAILED: The issue is not resolved")

    print()

    # Test a more comprehensive example
    comprehensive_test = [
        "5.2.5",
        "5.2rc1",
        "5.2.0",
        "5.2a1",
        "5.2b1",
        "5.1.0",
        "5.3.0",
        "5.2.1",
    ]

    old_comprehensive = sorted(comprehensive_test, reverse=True)
    new_comprehensive = sort_versions_semantically(comprehensive_test, reverse=True)

    print("Comprehensive version sorting test:")
    print(f"  Input: {comprehensive_test}")
    print(f"  String sorted: {old_comprehensive}")
    print(f"  Semantic sorted: {new_comprehensive}")
    print()

    print("Expected semantic order (newest to oldest):")
    print("  5.3.0 > 5.2.5 > 5.2.1 > 5.2.0 > 5.2rc1 > 5.2b1 > 5.2a1 > 5.1.0")


if __name__ == "__main__":
    test_specific_case()

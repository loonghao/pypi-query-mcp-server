#!/usr/bin/env python3
"""Test script to verify semantic version sorting functionality."""

import asyncio
import logging
from pypi_query_mcp.core.version_utils import sort_versions_semantically
from pypi_query_mcp.tools.package_query import query_package_versions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_semantic_version_sorting():
    """Test the semantic version sorting function with various edge cases."""
    print("=" * 60)
    print("Testing Semantic Version Sorting Function")
    print("=" * 60)
    
    # Test case 1: Basic pre-release ordering
    test1_versions = ["5.2rc1", "5.2.5", "5.2.0", "5.2a1", "5.2b1"]
    sorted1 = sort_versions_semantically(test1_versions)
    print(f"Test 1 - Pre-release ordering:")
    print(f"  Input:  {test1_versions}")
    print(f"  Output: {sorted1}")
    print(f"  Expected: ['5.2.5', '5.2.0', '5.2rc1', '5.2b1', '5.2a1']")
    print()
    
    # Test case 2: Complex Django-like versions
    test2_versions = [
        "4.2.0", "4.2a1", "4.2b1", "4.2rc1", "4.1.0", "4.1.7", 
        "4.0.0", "3.2.18", "4.2.1", "4.2.2"
    ]
    sorted2 = sort_versions_semantically(test2_versions)
    print(f"Test 2 - Django-like versions:")
    print(f"  Input:  {test2_versions}")
    print(f"  Output: {sorted2}")
    print()
    
    # Test case 3: TensorFlow-like versions with dev builds
    test3_versions = [
        "2.13.0", "2.13.0rc1", "2.13.0rc0", "2.12.0", "2.12.1",
        "2.14.0dev20230517", "2.13.0rc2"  # This might not parse correctly
    ]
    sorted3 = sort_versions_semantically(test3_versions)
    print(f"Test 3 - TensorFlow-like versions:")
    print(f"  Input:  {test3_versions}")
    print(f"  Output: {sorted3}")
    print()
    
    # Test case 4: Edge cases and malformed versions
    test4_versions = [
        "1.0.0", "1.0.0.post1", "1.0.0.dev0", "1.0.0a1", "1.0.0b1", 
        "1.0.0rc1", "1.0.1", "invalid-version", "1.0"
    ]
    sorted4 = sort_versions_semantically(test4_versions)
    print(f"Test 4 - Edge cases and malformed versions:")
    print(f"  Input:  {test4_versions}")
    print(f"  Output: {sorted4}")
    print()
    
    # Test case 5: Empty and single item lists
    test5_empty = []
    test5_single = ["1.0.0"]
    sorted5_empty = sort_versions_semantically(test5_empty)
    sorted5_single = sort_versions_semantically(test5_single)
    print(f"Test 5 - Edge cases:")
    print(f"  Empty list: {sorted5_empty}")
    print(f"  Single item: {sorted5_single}")
    print()


async def test_real_package_versions():
    """Test with real PyPI packages that have complex version histories."""
    print("=" * 60)
    print("Testing Real Package Version Sorting")
    print("=" * 60)
    
    # Test packages known to have complex version histories
    test_packages = [
        "django",      # Known for alpha, beta, rc versions
        "tensorflow",  # Complex versioning with dev builds
        "numpy",       # Long history with various formats
        "requests"     # Simple but well-known package
    ]
    
    for package_name in test_packages:
        try:
            print(f"\nTesting {package_name}:")
            result = await query_package_versions(package_name)
            
            recent_versions = result.get("recent_versions", [])[:10]
            print(f"  Recent versions (first 10): {recent_versions}")
            
            # Check if versions seem to be properly sorted
            if len(recent_versions) >= 3:
                print(f"  First three versions: {recent_versions[:3]}")
                
        except Exception as e:
            print(f"  Error querying {package_name}: {e}")
    
    print()


def validate_sorting_correctness():
    """Validate that our sorting meets the requirements."""
    print("=" * 60)
    print("Validation Tests")
    print("=" * 60)
    
    # The specific example from the task: "5.2rc1" should come after "5.2.5"
    task_example = ["5.2rc1", "5.2.5"]
    sorted_task = sort_versions_semantically(task_example)
    
    print("Task requirement validation:")
    print(f"  Input: {task_example}")
    print(f"  Output: {sorted_task}")
    print(f"  Requirement: '5.2rc1' should come after '5.2.5'")
    
    if sorted_task == ["5.2.5", "5.2rc1"]:
        print("  ✅ PASS: Requirement met!")
    else:
        print("  ❌ FAIL: Requirement not met!")
    
    print()
    
    # Test pre-release ordering: alpha < beta < rc < stable
    pre_release_test = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
    sorted_pre = sort_versions_semantically(pre_release_test)
    
    print("Pre-release ordering validation:")
    print(f"  Input: {pre_release_test}")
    print(f"  Output: {sorted_pre}")
    print(f"  Expected order: stable > rc > beta > alpha")
    
    expected_order = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
    if sorted_pre == expected_order:
        print("  ✅ PASS: Pre-release ordering correct!")
    else:
        print("  ❌ FAIL: Pre-release ordering incorrect!")
    
    print()


async def main():
    """Main test function."""
    print("Semantic Version Sorting Test Suite")
    print("="*60)
    
    # Run unit tests
    test_semantic_version_sorting()
    
    # Validate specific requirements
    validate_sorting_correctness()
    
    # Test with real packages
    await test_real_package_versions()
    
    print("=" * 60)
    print("Test suite completed!")


if __name__ == "__main__":
    asyncio.run(main())
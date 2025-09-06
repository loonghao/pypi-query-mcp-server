#!/usr/bin/env python3
"""Standalone test script to verify semantic version sorting functionality."""

import logging

from packaging.version import InvalidVersion, Version

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sort_versions_semantically(versions: list[str], reverse: bool = True) -> list[str]:
    """Sort package versions using semantic version ordering.

    This function properly sorts versions by parsing them as semantic versions,
    ensuring that pre-release versions (alpha, beta, rc) are ordered correctly
    relative to stable releases.

    Args:
        versions: List of version strings to sort
        reverse: If True, sort in descending order (newest first). Default True.

    Returns:
        List of version strings sorted semantically

    Examples:
        >>> sort_versions_semantically(['1.0.0', '2.0.0a1', '1.5.0', '2.0.0'])
        ['2.0.0', '2.0.0a1', '1.5.0', '1.0.0']

        >>> sort_versions_semantically(['5.2rc1', '5.2.5', '5.2.0'])
        ['5.2.5', '5.2.0', '5.2rc1']
    """
    if not versions:
        return []

    def parse_version_safe(version_str: str) -> tuple[Version | None, str]:
        """Safely parse a version string, returning (parsed_version, original_string).

        Returns (None, original_string) if parsing fails.
        """
        try:
            return (Version(version_str), version_str)
        except InvalidVersion:
            logger.debug(f"Failed to parse version '{version_str}' as semantic version")
            return (None, version_str)

    # Parse all versions, keeping track of originals
    parsed_versions = [parse_version_safe(v) for v in versions]

    # Separate valid and invalid versions
    valid_versions = [(v, orig) for v, orig in parsed_versions if v is not None]
    invalid_versions = [orig for v, orig in parsed_versions if v is None]

    # Sort valid versions semantically
    valid_versions.sort(key=lambda x: x[0], reverse=reverse)

    # Sort invalid versions lexicographically as fallback
    invalid_versions.sort(reverse=reverse)

    # Combine results: valid versions first, then invalid ones
    result = [orig for _, orig in valid_versions] + invalid_versions

    logger.debug(
        f"Sorted {len(versions)} versions: {len(valid_versions)} valid, "
        f"{len(invalid_versions)} invalid"
    )

    return result


def test_semantic_version_sorting():
    """Test the semantic version sorting function with various edge cases."""
    print("=" * 60)
    print("Testing Semantic Version Sorting Function")
    print("=" * 60)

    # Test case 1: Basic pre-release ordering
    test1_versions = ["5.2rc1", "5.2.5", "5.2.0", "5.2a1", "5.2b1"]
    sorted1 = sort_versions_semantically(test1_versions)
    print("Test 1 - Pre-release ordering:")
    print(f"  Input:  {test1_versions}")
    print(f"  Output: {sorted1}")
    print("  Expected: ['5.2.5', '5.2.0', '5.2rc1', '5.2b1', '5.2a1']")
    print()

    # Test case 2: Complex Django-like versions
    test2_versions = [
        "4.2.0",
        "4.2a1",
        "4.2b1",
        "4.2rc1",
        "4.1.0",
        "4.1.7",
        "4.0.0",
        "3.2.18",
        "4.2.1",
        "4.2.2",
    ]
    sorted2 = sort_versions_semantically(test2_versions)
    print("Test 2 - Django-like versions:")
    print(f"  Input:  {test2_versions}")
    print(f"  Output: {sorted2}")
    print()

    # Test case 3: TensorFlow-like versions with dev builds
    test3_versions = [
        "2.13.0",
        "2.13.0rc1",
        "2.13.0rc0",
        "2.12.0",
        "2.12.1",
        "2.14.0dev20230517",
        "2.13.0rc2",  # This might not parse correctly
    ]
    sorted3 = sort_versions_semantically(test3_versions)
    print("Test 3 - TensorFlow-like versions:")
    print(f"  Input:  {test3_versions}")
    print(f"  Output: {sorted3}")
    print()

    # Test case 4: Edge cases and malformed versions
    test4_versions = [
        "1.0.0",
        "1.0.0.post1",
        "1.0.0.dev0",
        "1.0.0a1",
        "1.0.0b1",
        "1.0.0rc1",
        "1.0.1",
        "invalid-version",
        "1.0",
    ]
    sorted4 = sort_versions_semantically(test4_versions)
    print("Test 4 - Edge cases and malformed versions:")
    print(f"  Input:  {test4_versions}")
    print(f"  Output: {sorted4}")
    print()

    # Test case 5: Empty and single item lists
    test5_empty = []
    test5_single = ["1.0.0"]
    sorted5_empty = sort_versions_semantically(test5_empty)
    sorted5_single = sort_versions_semantically(test5_single)
    print("Test 5 - Edge cases:")
    print(f"  Empty list: {sorted5_empty}")
    print(f"  Single item: {sorted5_single}")
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
    print("  Requirement: '5.2rc1' should come after '5.2.5'")

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
    print("  Expected order: stable > rc > beta > alpha")

    expected_order = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
    if sorted_pre == expected_order:
        print("  ✅ PASS: Pre-release ordering correct!")
    else:
        print("  ❌ FAIL: Pre-release ordering incorrect!")

    print()


def test_version_comparison_details():
    """Test detailed version comparison to understand packaging behavior."""
    print("=" * 60)
    print("Version Comparison Details")
    print("=" * 60)

    test_versions = [
        ("1.0.0", "1.0.0a1"),
        ("1.0.0", "1.0.0b1"),
        ("1.0.0", "1.0.0rc1"),
        ("1.0.0rc1", "1.0.0b1"),
        ("1.0.0b1", "1.0.0a1"),
        ("5.2.5", "5.2rc1"),
        ("5.2.0", "5.2rc1"),
        ("1.0.0.post1", "1.0.0"),
        ("1.0.0.dev0", "1.0.0"),
    ]

    for v1, v2 in test_versions:
        try:
            ver1 = Version(v1)
            ver2 = Version(v2)
            comparison = ">" if ver1 > ver2 else "<" if ver1 < ver2 else "="
            print(f"  {v1} {comparison} {v2}")
        except Exception as e:
            print(f"  Error comparing {v1} and {v2}: {e}")

    print()


def main():
    """Main test function."""
    print("Semantic Version Sorting Test Suite")
    print("=" * 60)

    # Run unit tests
    test_semantic_version_sorting()

    # Validate specific requirements
    validate_sorting_correctness()

    # Show detailed version comparisons
    test_version_comparison_details()

    print("=" * 60)
    print("Test suite completed!")


if __name__ == "__main__":
    main()

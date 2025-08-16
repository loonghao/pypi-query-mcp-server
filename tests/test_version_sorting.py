"""Tests for semantic version sorting functionality."""

from pypi_query_mcp.core.version_utils import sort_versions_semantically


class TestSemanticVersionSorting:
    """Test semantic version sorting function."""

    def test_basic_version_sorting(self):
        """Test basic version sorting with stable versions."""
        versions = ["1.0.0", "2.0.0", "1.5.0", "1.0.1"]
        expected = ["2.0.0", "1.5.0", "1.0.1", "1.0.0"]
        result = sort_versions_semantically(versions, reverse=True)
        assert result == expected

    def test_pre_release_ordering(self):
        """Test that pre-release versions are ordered correctly."""
        versions = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
        expected = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
        result = sort_versions_semantically(versions, reverse=True)
        assert result == expected

    def test_task_requirement(self):
        """Test the specific requirement from the task: 5.2rc1 vs 5.2.5."""
        versions = ["5.2rc1", "5.2.5"]
        expected = ["5.2.5", "5.2rc1"]
        result = sort_versions_semantically(versions, reverse=True)
        assert result == expected

    def test_complex_pre_release_scenario(self):
        """Test complex pre-release scenario with multiple types."""
        versions = ["5.2rc1", "5.2.5", "5.2.0", "5.2a1", "5.2b1"]
        expected = ["5.2.5", "5.2.0", "5.2rc1", "5.2b1", "5.2a1"]
        result = sort_versions_semantically(versions, reverse=True)
        assert result == expected

    def test_dev_and_post_versions(self):
        """Test development and post-release versions."""
        versions = ["1.0.0", "1.0.0.post1", "1.0.0.dev0", "1.0.1"]
        result = sort_versions_semantically(versions, reverse=True)

        # 1.0.1 should be first, then 1.0.0.post1, then 1.0.0, then 1.0.0.dev0
        assert result[0] == "1.0.1"
        assert result[1] == "1.0.0.post1"
        assert result[2] == "1.0.0"
        assert result[3] == "1.0.0.dev0"

    def test_invalid_versions_fallback(self):
        """Test that invalid versions fall back to string sorting."""
        versions = ["1.0.0", "invalid-version", "another-invalid", "2.0.0"]
        result = sort_versions_semantically(versions, reverse=True)

        # Valid versions should come first
        assert result[0] == "2.0.0"
        assert result[1] == "1.0.0"
        # Invalid versions should be at the end, string-sorted
        assert "invalid-version" in result[2:]
        assert "another-invalid" in result[2:]

    def test_empty_list(self):
        """Test that empty list returns empty list."""
        result = sort_versions_semantically([])
        assert result == []

    def test_single_version(self):
        """Test that single version returns single version."""
        result = sort_versions_semantically(["1.0.0"])
        assert result == ["1.0.0"]

    def test_ascending_order(self):
        """Test sorting in ascending order."""
        versions = ["2.0.0", "1.0.0", "1.5.0"]
        expected = ["1.0.0", "1.5.0", "2.0.0"]
        result = sort_versions_semantically(versions, reverse=False)
        assert result == expected

    def test_mixed_version_formats(self):
        """Test sorting with mixed version formats."""
        versions = ["1.0", "1.0.0", "1.0.1", "v1.0.2"]  # v1.0.2 might be invalid
        result = sort_versions_semantically(versions, reverse=True)

        # Should handle mixed formats gracefully
        assert len(result) == 4
        assert "1.0.1" in result
        assert "1.0.0" in result
        assert "1.0" in result

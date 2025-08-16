"""Tests for PyPI Development Workflow Tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pypi_query_mcp.core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
)
from pypi_query_mcp.tools.workflow import (
    PyPIWorkflowError,
    _analyze_build_quality,
    _analyze_wheel_filename,
    _calculate_completeness_score,
    _calculate_discoverability_score,
    _generate_html_preview,
    _generate_next_steps,
    _validate_package_name_format,
    check_pypi_upload_requirements,
    get_pypi_build_logs,
    preview_pypi_package_page,
    validate_pypi_package_name,
)


class TestValidatePackageNameFormat:
    """Test package name format validation."""

    def test_valid_package_names(self):
        """Test that valid package names pass validation."""
        valid_names = [
            "mypackage",
            "my-package",
            "my_package",
            "my.package",
            "package123",
            "a",
            "package-name-123",
        ]
        
        for name in valid_names:
            result = _validate_package_name_format(name)
            assert result["valid"] is True, f"'{name}' should be valid"
            assert len(result["issues"]) == 0

    def test_invalid_package_names(self):
        """Test that invalid package names fail validation."""
        invalid_names = [
            "",  # Empty
            "-package",  # Starts with hyphen
            "package-",  # Ends with hyphen
            ".package",  # Starts with dot
            "package.",  # Ends with dot
            "pack--age",  # Double hyphen
            "pack..age",  # Double dot
            "pack@age",  # Invalid character
            "PACKAGE",  # Uppercase (should get recommendation)
        ]
        
        for name in invalid_names:
            result = _validate_package_name_format(name)
            if name == "PACKAGE":
                # This should be valid but get recommendations
                assert result["valid"] is True
                assert len(result["recommendations"]) > 0
            else:
                assert result["valid"] is False or len(result["issues"]) > 0, f"'{name}' should be invalid"

    def test_reserved_names(self):
        """Test that reserved names are flagged."""
        reserved_names = ["pip", "setuptools", "wheel", "python"]
        
        for name in reserved_names:
            result = _validate_package_name_format(name)
            assert result["valid"] is False
            assert any("reserved" in issue.lower() for issue in result["issues"])

    def test_normalization(self):
        """Test package name normalization."""
        test_cases = [
            ("My_Package", "my-package"),
            ("my__package", "my-package"),
            ("my.-_package", "my-package"),
            ("PACKAGE", "package"),
        ]
        
        for input_name, expected in test_cases:
            result = _validate_package_name_format(input_name)
            assert result["normalized_name"] == expected


class TestValidatePyPIPackageName:
    """Test the main package name validation function."""

    @pytest.mark.asyncio
    async def test_validate_available_package(self):
        """Test validation of an available package name."""
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            # Mock package not found (available)
            mock_client.return_value.__aenter__.return_value.get_package_info.side_effect = PackageNotFoundError("test-package")
            
            result = await validate_pypi_package_name("test-package")
            
            assert result["package_name"] == "test-package"
            assert result["availability"]["status"] == "available"
            assert result["ready_for_upload"] is True

    @pytest.mark.asyncio
    async def test_validate_taken_package(self):
        """Test validation of a taken package name."""
        mock_package_data = {
            "info": {
                "name": "requests",
                "version": "2.28.0",
                "summary": "Python HTTP for Humans.",
                "author": "Kenneth Reitz",
            }
        }
        
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.return_value = mock_package_data
            
            result = await validate_pypi_package_name("requests")
            
            assert result["package_name"] == "requests"
            assert result["availability"]["status"] == "taken"
            assert result["availability"]["existing_package"]["name"] == "requests"
            assert result["ready_for_upload"] is False

    @pytest.mark.asyncio
    async def test_validate_invalid_format(self):
        """Test validation of invalid package name format."""
        with pytest.raises(InvalidPackageNameError):
            await validate_pypi_package_name("-invalid-")

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors during validation."""
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.side_effect = NetworkError("Connection failed")
            
            result = await validate_pypi_package_name("test-package")
            
            assert result["availability"]["status"] == "unknown"


class TestPreviewPyPIPackagePage:
    """Test package page preview generation."""

    @pytest.mark.asyncio
    async def test_basic_preview_generation(self):
        """Test basic preview generation with minimal metadata."""
        result = await preview_pypi_package_page(
            package_name="my-package",
            version="1.0.0",
            summary="A test package",
            author="Test Author"
        )
        
        assert result["package_name"] == "my-package"
        assert result["version"] == "1.0.0"
        assert result["preview"]["sections"]["header"]["summary"] == "A test package"
        assert result["preview"]["sections"]["header"]["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_comprehensive_preview(self):
        """Test preview generation with comprehensive metadata."""
        keywords = ["testing", "python", "package"]
        classifiers = [
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: MIT License",
        ]
        
        result = await preview_pypi_package_page(
            package_name="comprehensive-package",
            version="2.1.0",
            summary="A comprehensive test package with full metadata",
            description="This is a detailed description of the package functionality...",
            author="Test Author",
            license_name="MIT",
            home_page="https://github.com/test/package",
            keywords=keywords,
            classifiers=classifiers,
        )
        
        assert result["ready_for_upload"] is True
        assert result["validation"]["completeness_score"]["level"] in ["good", "complete"]
        assert result["seo_analysis"]["discoverability_score"]["level"] in ["good", "excellent"]

    @pytest.mark.asyncio
    async def test_preview_warnings(self):
        """Test that preview generates appropriate warnings."""
        result = await preview_pypi_package_page(
            package_name="minimal-package",
            # Minimal metadata to trigger warnings
        )
        
        assert len(result["warnings"]) > 0
        assert any("Summary is missing" in warning for warning in result["warnings"])
        assert any("description" in warning.lower() for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_invalid_package_name_preview(self):
        """Test preview with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await preview_pypi_package_page("-invalid-package-")


class TestCalculateScores:
    """Test scoring calculation functions."""

    def test_discoverability_score_calculation(self):
        """Test discoverability score calculation."""
        # High quality metadata
        result = _calculate_discoverability_score(
            summary="A comprehensive package for testing",
            description="This is a very detailed description with lots of useful information about the package functionality and use cases.",
            keywords=["testing", "python", "package", "quality", "automation"],
            classifiers=["Development Status :: 4 - Beta", "Programming Language :: Python :: 3.8"]
        )
        
        assert result["score"] >= 70
        assert result["level"] in ["good", "excellent"]
        
        # Poor quality metadata
        result = _calculate_discoverability_score("", "", [], [])
        assert result["score"] == 0
        assert result["level"] == "poor"

    def test_completeness_score_calculation(self):
        """Test completeness score calculation."""
        # Complete metadata
        sections = {
            "header": {
                "summary": "A test package",
                "author": "Test Author",
            },
            "metadata": {
                "license": "MIT",
                "home_page": "https://github.com/test/package",
                "keywords": ["test", "package"],
                "classifiers": ["Development Status :: 4 - Beta"],
            },
            "description": {
                "content": "A detailed description with more than 200 characters to ensure it gets a good score.",
                "length": 80,
            }
        }
        
        result = _calculate_completeness_score(sections)
        assert result["score"] >= 60
        assert result["level"] in ["good", "complete"]


class TestCheckPyPIUploadRequirements:
    """Test PyPI upload requirements checking."""

    @pytest.mark.asyncio
    async def test_minimal_requirements_met(self):
        """Test with minimal required fields."""
        result = await check_pypi_upload_requirements(
            package_name="test-package",
            version="1.0.0",
            author="Test Author",
            description="A test package"
        )
        
        assert result["upload_readiness"]["can_upload"] is True
        assert result["validation"]["compliance"]["required_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test with missing required fields."""
        result = await check_pypi_upload_requirements(
            package_name="test-package",
            # Missing required fields
        )
        
        assert result["upload_readiness"]["can_upload"] is False
        assert len(result["issues"]["errors"]) > 0

    @pytest.mark.asyncio
    async def test_comprehensive_metadata(self):
        """Test with comprehensive metadata."""
        classifiers = [
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: MIT License",
        ]
        
        result = await check_pypi_upload_requirements(
            package_name="comprehensive-package",
            version="1.0.0",
            author="Test Author",
            author_email="test@example.com",
            description="A comprehensive test package",
            long_description="This is a detailed description...",
            license_name="MIT",
            home_page="https://github.com/test/package",
            classifiers=classifiers,
            requires_python=">=3.8"
        )
        
        assert result["upload_readiness"]["should_upload"] is True
        assert result["validation"]["compliance"]["recommended_percentage"] >= 80.0

    @pytest.mark.asyncio
    async def test_invalid_package_name_requirements(self):
        """Test requirements check with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await check_pypi_upload_requirements("-invalid-")


class TestGetPyPIBuildLogs:
    """Test PyPI build logs analysis."""

    @pytest.mark.asyncio
    async def test_analyze_package_with_wheels(self):
        """Test analysis of package with wheel distributions."""
        mock_package_data = {
            "info": {"name": "test-package", "version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {
                        "filename": "test_package-1.0.0-py3-none-any.whl",
                        "packagetype": "bdist_wheel",
                        "size": 10000,
                        "upload_time_iso_8601": "2023-01-01T00:00:00Z",
                        "python_version": "py3",
                        "url": "https://files.pythonhosted.org/...",
                        "md5_digest": "abc123",
                        "digests": {"sha256": "def456"},
                    },
                    {
                        "filename": "test-package-1.0.0.tar.gz",
                        "packagetype": "sdist",
                        "size": 15000,
                        "upload_time_iso_8601": "2023-01-01T00:00:00Z",
                        "python_version": "source",
                        "url": "https://files.pythonhosted.org/...",
                        "md5_digest": "ghi789",
                        "digests": {"sha256": "jkl012"},
                    }
                ]
            },
            "urls": []  # Empty for this test
        }
        
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.return_value = mock_package_data
            
            result = await get_pypi_build_logs("test-package")
            
            assert result["package_name"] == "test-package"
            assert result["build_summary"]["wheel_count"] == 1
            assert result["build_summary"]["source_count"] == 1
            assert result["build_status"]["has_wheels"] is True
            assert result["build_status"]["has_source"] is True

    @pytest.mark.asyncio
    async def test_analyze_source_only_package(self):
        """Test analysis of package with only source distribution."""
        mock_package_data = {
            "info": {"name": "source-only", "version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {
                        "filename": "source-only-1.0.0.tar.gz",
                        "packagetype": "sdist",
                        "size": 20000,
                        "upload_time_iso_8601": "2023-01-01T00:00:00Z",
                        "python_version": "source",
                    }
                ]
            },
            "urls": []
        }
        
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.return_value = mock_package_data
            
            result = await get_pypi_build_logs("source-only")
            
            assert result["build_status"]["has_wheels"] is False
            assert result["build_status"]["has_source"] is True
            assert any("No wheel distributions" in warning for warning in result["issues"]["warnings"])

    @pytest.mark.asyncio
    async def test_package_not_found_build_logs(self):
        """Test build logs for non-existent package."""
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.side_effect = PackageNotFoundError("nonexistent")
            
            with pytest.raises(PackageNotFoundError):
                await get_pypi_build_logs("nonexistent")

    @pytest.mark.asyncio
    async def test_platform_filtering(self):
        """Test platform-specific filtering of build logs."""
        mock_package_data = {
            "info": {"name": "multi-platform", "version": "1.0.0"},
            "releases": {
                "1.0.0": [
                    {
                        "filename": "multi_platform-1.0.0-py3-none-win_amd64.whl",
                        "packagetype": "bdist_wheel",
                        "size": 10000,
                        "python_version": "py3",
                    },
                    {
                        "filename": "multi_platform-1.0.0-py3-none-linux_x86_64.whl",
                        "packagetype": "bdist_wheel", 
                        "size": 10000,
                        "python_version": "py3",
                    }
                ]
            },
            "urls": []
        }
        
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.return_value = mock_package_data
            
            # Test Windows filtering
            result = await get_pypi_build_logs("multi-platform", platform="windows")
            
            # Should only include Windows wheels
            windows_wheels = [w for w in result["distributions"]["wheels"] if "win" in w.get("platform", "")]
            assert len(windows_wheels) > 0


class TestWheelFilenameAnalysis:
    """Test wheel filename analysis."""

    def test_universal_wheel_analysis(self):
        """Test analysis of universal wheel filename."""
        result = _analyze_wheel_filename("mypackage-1.0.0-py2.py3-none-any.whl")
        
        assert result["wheel_type"] == "universal"
        assert result["platform"] == "any"
        assert result["python_implementation"] == "universal"

    def test_platform_specific_wheel_analysis(self):
        """Test analysis of platform-specific wheel filename."""
        result = _analyze_wheel_filename("mypackage-1.0.0-cp38-cp38-win_amd64.whl")
        
        assert result["wheel_type"] == "platform_specific"
        assert result["platform"] == "windows"
        assert result["python_implementation"] == "cpython"
        assert result["architecture"] == "x86_64"

    def test_linux_wheel_analysis(self):
        """Test analysis of Linux wheel filename."""
        result = _analyze_wheel_filename("mypackage-1.0.0-cp39-cp39-linux_x86_64.whl")
        
        assert result["platform"] == "linux"
        assert result["architecture"] == "x86_64"

    def test_macos_wheel_analysis(self):
        """Test analysis of macOS wheel filename."""
        result = _analyze_wheel_filename("mypackage-1.0.0-cp310-cp310-macosx_10_9_x86_64.whl")
        
        assert result["platform"] == "macos"
        assert result["architecture"] == "x86_64"


class TestBuildQualityAnalysis:
    """Test build quality analysis."""

    def test_high_quality_build_analysis(self):
        """Test analysis of high-quality builds."""
        distributions = {
            "wheels": [
                {"platform": "windows", "size_bytes": 1000000, "python_version": "py3"},
                {"platform": "linux", "size_bytes": 1000000, "python_version": "py3"},
                {"platform": "macos", "size_bytes": 1000000, "python_version": "py3"},
            ],
            "source": [{"size_bytes": 500000}],
        }
        
        result = _analyze_build_quality(distributions, {})
        
        assert result["health_status"] in ["good", "excellent"]
        assert result["platform_coverage"] == 3
        assert len(result["health_issues"]) == 0

    def test_poor_quality_build_analysis(self):
        """Test analysis of poor-quality builds."""
        distributions = {
            "wheels": [],  # No wheels
            "source": [],  # No source
        }
        
        result = _analyze_build_quality(distributions, {})
        
        assert result["health_status"] == "poor"
        assert len(result["health_issues"]) > 0


class TestUtilityFunctions:
    """Test utility functions."""

    def test_generate_html_preview(self):
        """Test HTML preview generation."""
        sections = {
            "header": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "A test package",
                "author": "Test Author",
            },
            "metadata": {
                "license": "MIT",
                "home_page": "https://github.com/test/package",
                "keywords": ["test"],
                "classifiers": ["Development Status :: 4 - Beta"],
            },
            "description": {
                "content": "Test description",
            }
        }
        
        html = _generate_html_preview(sections)
        
        assert "test-package" in html
        assert "1.0.0" in html
        assert "A test package" in html
        assert "Test Author" in html
        assert "MIT" in html

    def test_generate_next_steps(self):
        """Test next steps generation."""
        errors = ["Missing required field: name"]
        warnings = ["Author email is recommended"]
        suggestions = ["Consider adding keywords"]
        
        steps = _generate_next_steps(errors, warnings, suggestions, False)
        
        assert len(steps) > 0
        assert any("Fix critical errors" in step for step in steps)
        
        # Test with upload ready
        steps_ready = _generate_next_steps([], warnings, suggestions, True)
        assert any("Ready for upload" in step for step in steps_ready)


class TestErrorHandling:
    """Test error handling in workflow functions."""

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test custom workflow error handling."""
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.side_effect = Exception("Unexpected error")
            
            with pytest.raises(PyPIWorkflowError) as exc_info:
                await validate_pypi_package_name("test-package")
            
            assert "validate_name" in str(exc_info.value.operation)

    @pytest.mark.asyncio
    async def test_network_error_propagation(self):
        """Test that network errors are properly propagated."""
        with patch("pypi_query_mcp.tools.workflow.PyPIClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get_package_info.side_effect = NetworkError("Network down")
            
            with pytest.raises(PyPIWorkflowError):
                await get_pypi_build_logs("test-package")


if __name__ == "__main__":
    pytest.main([__file__])
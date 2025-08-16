"""Tests for PyPI metadata management tools."""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import httpx
import pytest

from pypi_query_mcp.core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIAuthenticationError,
    PyPIPermissionError,
    PyPIServerError,
)
from pypi_query_mcp.tools.metadata import (
    PyPIMetadataClient,
    manage_package_keywords,
    manage_package_urls,
    set_package_visibility,
    update_package_metadata,
)


class TestPyPIMetadataClient:
    """Test cases for PyPIMetadataClient."""

    def test_init_default(self):
        """Test client initialization with default values."""
        client = PyPIMetadataClient()
        
        assert client.api_token is None
        assert client.test_pypi is False
        assert client.timeout == 60.0
        assert client.max_retries == 3
        assert client.retry_delay == 2.0
        assert "pypi.org" in client.api_url
        assert "pypi.org" in client.manage_url

    def test_init_test_pypi(self):
        """Test client initialization for TestPyPI."""
        client = PyPIMetadataClient(test_pypi=True)
        
        assert client.test_pypi is True
        assert "test.pypi.org" in client.api_url
        assert "test.pypi.org" in client.manage_url

    def test_init_with_token(self):
        """Test client initialization with API token."""
        token = "pypi-test-token"
        client = PyPIMetadataClient(api_token=token)
        
        assert client.api_token == token
        assert "Authorization" in client._client.headers
        assert client._client.headers["Authorization"] == f"token {token}"

    def test_validate_package_name_valid(self):
        """Test package name validation with valid names."""
        client = PyPIMetadataClient()
        
        valid_names = [
            "requests",
            "django-rest-framework",
            "numpy",
            "package_name",
            "package.name",
            "a",
            "a1",
            "package-1.0",
        ]
        
        for name in valid_names:
            result = client._validate_package_name(name)
            assert result == name.strip()

    def test_validate_package_name_invalid(self):
        """Test package name validation with invalid names."""
        client = PyPIMetadataClient()
        
        invalid_names = [
            "",
            "   ",
            "-invalid",
            "invalid-",
            ".invalid",
            "invalid.",
            "in..valid",
            "in--valid",
        ]
        
        for name in invalid_names:
            with pytest.raises(InvalidPackageNameError):
                client._validate_package_name(name)

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request."""
        with patch.object(httpx.AsyncClient, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            client = PyPIMetadataClient()
            response = await client._make_request("GET", "https://example.com")
            
            assert response == mock_response
            mock_request.assert_called_once_with("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_make_request_authentication_error(self):
        """Test HTTP request with authentication error."""
        with patch.object(httpx.AsyncClient, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_request.return_value = mock_response
            
            client = PyPIMetadataClient()
            
            with pytest.raises(PyPIAuthenticationError):
                await client._make_request("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_verify_package_ownership_no_token(self):
        """Test package ownership verification without token."""
        client = PyPIMetadataClient()
        result = await client._verify_package_ownership("test-package")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_package_ownership_with_token(self):
        """Test package ownership verification with token."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            client = PyPIMetadataClient(api_token="test-token")
            result = await client._verify_package_ownership("test-package")
            assert result is True


class TestUpdatePackageMetadata:
    """Test cases for update_package_metadata function."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data from PyPI API."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "Test package description",
                "keywords": "test,python,package",
                "classifiers": [
                    "Development Status :: 4 - Beta",
                    "Programming Language :: Python :: 3",
                    "License :: OSI Approved :: MIT License",
                ],
                "author": "Test Author",
                "license": "MIT",
            }
        }

    @pytest.mark.asyncio
    async def test_update_metadata_dry_run_success(self, mock_package_data):
        """Test metadata update in dry run mode."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await update_package_metadata(
                package_name="test-package",
                description="New description",
                keywords=["test", "python", "new"],
                dry_run=True,
            )
            
            assert result["dry_run"] is True
            assert result["package_name"] == "test-package"
            assert "metadata_updates" in result
            assert result["metadata_updates"]["description"] == "New description"
            assert "test" in result["metadata_updates"]["keywords"]

    @pytest.mark.asyncio
    async def test_update_metadata_invalid_package(self):
        """Test metadata update with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await update_package_metadata(
                package_name="",
                description="Test description",
            )

    @pytest.mark.asyncio
    async def test_update_metadata_package_not_found(self):
        """Test metadata update with non-existent package."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            with pytest.raises(PackageNotFoundError):
                await update_package_metadata(
                    package_name="non-existent-package",
                    description="Test description",
                )

    @pytest.mark.asyncio
    async def test_update_metadata_validation_errors(self, mock_package_data):
        """Test metadata update with validation errors."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            # Test description too long
            long_description = "x" * 3000
            result = await update_package_metadata(
                package_name="test-package",
                description=long_description,
                dry_run=True,
            )
            
            assert len(result["validation_errors"]) > 0
            assert any("Description exceeds" in error for error in result["validation_errors"])

    @pytest.mark.asyncio
    async def test_update_metadata_invalid_keywords(self, mock_package_data):
        """Test metadata update with invalid keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            # Test invalid keyword type
            result = await update_package_metadata(
                package_name="test-package",
                keywords="not-a-list",  # Should be a list
                dry_run=True,
            )
            
            assert len(result["validation_errors"]) > 0
            assert any("must be a list" in error for error in result["validation_errors"])


class TestManagePackageUrls:
    """Test cases for manage_package_urls function."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data from PyPI API."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "home_page": "https://example.com",
                "download_url": "",
                "project_urls": {
                    "Documentation": "https://docs.example.com",
                    "Repository": "https://github.com/user/repo",
                },
            }
        }

    @pytest.mark.asyncio
    async def test_manage_urls_dry_run_success(self, mock_package_data):
        """Test URL management in dry run mode."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_package_urls(
                package_name="test-package",
                homepage="https://new-homepage.com",
                documentation="https://new-docs.com",
                validate_urls=False,  # Skip URL validation for test
                dry_run=True,
            )
            
            assert result["dry_run"] is True
            assert result["package_name"] == "test-package"
            assert "url_updates" in result
            assert result["url_updates"]["homepage"] == "https://new-homepage.com"

    @pytest.mark.asyncio
    async def test_manage_urls_invalid_format(self, mock_package_data):
        """Test URL management with invalid URL formats."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_package_urls(
                package_name="test-package",
                homepage="not-a-url",
                dry_run=True,
            )
            
            assert len(result["validation_errors"]) > 0
            assert any("Invalid" in error and "URL format" in error for error in result["validation_errors"])

    @pytest.mark.asyncio
    async def test_manage_urls_with_validation(self, mock_package_data):
        """Test URL management with URL validation."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            # Mock package data request
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            
            # Mock URL validation request
            mock_head_response = Mock()
            mock_head_response.status_code = 200
            
            mock_request.side_effect = [mock_response, mock_head_response]
            
            with patch.object(httpx.AsyncClient, 'head', return_value=mock_head_response):
                result = await manage_package_urls(
                    package_name="test-package",
                    homepage="https://valid-url.com",
                    validate_urls=True,
                    dry_run=True,
                )
            
            assert "validation_results" in result
            assert "homepage" in result["validation_results"]
            assert result["validation_results"]["homepage"]["accessible"] is True

    @pytest.mark.asyncio
    async def test_manage_urls_quality_score(self, mock_package_data):
        """Test URL quality score calculation."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_package_urls(
                package_name="test-package",
                homepage="https://secure-url.com",  # HTTPS URL
                documentation="http://insecure-url.com",  # HTTP URL
                validate_urls=False,
                dry_run=True,
            )
            
            assert "url_quality_score" in result
            assert isinstance(result["url_quality_score"], (int, float))


class TestSetPackageVisibility:
    """Test cases for set_package_visibility function."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data from PyPI API."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "author": "TestOrg",
                "home_page": "https://github.com/testorg/test-package",
            }
        }

    @pytest.mark.asyncio
    async def test_set_visibility_public_success(self, mock_package_data):
        """Test setting package visibility to public."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await set_package_visibility(
                    package_name="test-package",
                    visibility="public",
                    api_token="test-token",
                )
            
            assert result["package_name"] == "test-package"
            assert result["requested_visibility"] == "public"
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_set_visibility_private_no_confirmation(self, mock_package_data):
        """Test setting package visibility to private without confirmation."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await set_package_visibility(
                package_name="test-package",
                visibility="private",
                confirm_action=False,
            )
            
            assert result["success"] is False
            assert result["confirmation_required"] is True

    @pytest.mark.asyncio
    async def test_set_visibility_invalid_visibility(self):
        """Test setting package visibility with invalid value."""
        with pytest.raises(ValueError):
            await set_package_visibility(
                package_name="test-package",
                visibility="invalid",
            )

    @pytest.mark.asyncio
    async def test_set_visibility_organization_indicators(self, mock_package_data):
        """Test detection of organization indicators."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await set_package_visibility(
                    package_name="test-package",
                    visibility="public",
                    api_token="test-token",
                )
            
            assert "organization_indicators" in result
            # Should detect GitHub organization from home_page URL
            assert len(result["organization_indicators"]) > 0


class TestManagePackageKeywords:
    """Test cases for manage_package_keywords function."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data from PyPI API."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "keywords": "python,test,package",
                "classifiers": [
                    "Topic :: Software Development :: Libraries",
                    "Topic :: Internet :: WWW/HTTP",
                ],
                "summary": "A test package for Python development and web applications",
            }
        }

    @pytest.mark.asyncio
    async def test_manage_keywords_list_action(self, mock_package_data):
        """Test listing package keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_package_keywords(
                package_name="test-package",
                action="list",
            )
            
            assert result["action"] == "list"
            assert result["current_keywords"] == ["python", "test", "package"]
            assert "keyword_analysis" in result
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_manage_keywords_add_action(self, mock_package_data):
        """Test adding keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await manage_package_keywords(
                    package_name="test-package",
                    action="add",
                    keywords=["automation", "cli"],
                    api_token="test-token",
                    dry_run=True,
                )
            
            assert result["action"] == "add"
            assert "automation" in result["keywords_after"]
            assert "cli" in result["keywords_after"]
            assert result["changes_detected"] is True

    @pytest.mark.asyncio
    async def test_manage_keywords_remove_action(self, mock_package_data):
        """Test removing keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await manage_package_keywords(
                    package_name="test-package",
                    action="remove",
                    keywords=["test"],
                    api_token="test-token",
                    dry_run=True,
                )
            
            assert result["action"] == "remove"
            assert "test" not in result["keywords_after"]
            assert result["changes_detected"] is True

    @pytest.mark.asyncio
    async def test_manage_keywords_replace_action(self, mock_package_data):
        """Test replacing all keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await manage_package_keywords(
                    package_name="test-package",
                    action="replace",
                    keywords=["new", "keywords", "only"],
                    api_token="test-token",
                    dry_run=True,
                )
            
            assert result["action"] == "replace"
            assert result["keywords_after"] == ["new", "keywords", "only"]
            assert result["changes_detected"] is True

    @pytest.mark.asyncio
    async def test_manage_keywords_invalid_action(self):
        """Test managing keywords with invalid action."""
        with pytest.raises(ValueError):
            await manage_package_keywords(
                package_name="test-package",
                action="invalid",
            )

    @pytest.mark.asyncio
    async def test_manage_keywords_validation_errors(self, mock_package_data):
        """Test keyword validation errors."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                result = await manage_package_keywords(
                    package_name="test-package",
                    action="add",
                    keywords=["valid", "x" * 60, "invalid@keyword"],  # One too long, one with invalid chars
                    api_token="test-token",
                    dry_run=True,
                )
            
            assert len(result["validation_errors"]) > 0
            assert any("too long" in error.lower() for error in result["validation_errors"])
            assert any("invalid" in error.lower() for error in result["validation_errors"])

    @pytest.mark.asyncio
    async def test_manage_keywords_quality_analysis(self, mock_package_data):
        """Test keyword quality analysis."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_package_keywords(
                package_name="test-package",
                action="list",
            )
            
            assert "keyword_analysis" in result
            assert "keyword_quality" in result["keyword_analysis"]
            
            # Check that each keyword has quality metrics
            for keyword in result["current_keywords"]:
                assert keyword in result["keyword_analysis"]["keyword_quality"]
                quality_data = result["keyword_analysis"]["keyword_quality"][keyword]
                assert "score" in quality_data
                assert "quality" in quality_data
                assert quality_data["quality"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_manage_keywords_no_keywords_for_modify_action(self):
        """Test modify actions without providing keywords."""
        with pytest.raises(ValueError):
            await manage_package_keywords(
                package_name="test-package",
                action="add",
                keywords=None,  # Should provide keywords for add action
            )

    @pytest.mark.asyncio
    async def test_manage_keywords_too_many_keywords(self, mock_package_data):
        """Test adding too many keywords."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                # Generate 25 keywords (more than the 20 limit)
                too_many_keywords = [f"keyword{i}" for i in range(25)]
                
                result = await manage_package_keywords(
                    package_name="test-package",
                    action="replace",
                    keywords=too_many_keywords,
                    api_token="test-token",
                    dry_run=True,
                )
            
            assert len(result["validation_errors"]) > 0
            assert any("Too many keywords" in error for error in result["validation_errors"])
            # Should be truncated to 20
            assert len(result["keywords_after"]) <= 20

    @pytest.mark.asyncio
    async def test_manage_keywords_permission_error(self, mock_package_data):
        """Test keyword management without proper permissions."""
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=False):
                with pytest.raises(PyPIPermissionError):
                    await manage_package_keywords(
                        package_name="test-package",
                        action="add",
                        keywords=["new-keyword"],
                        api_token="test-token",
                        dry_run=False,  # Not dry run, so permission check applies
                    )


# Integration-style tests
class TestMetadataIntegration:
    """Integration tests for metadata tools."""

    @pytest.mark.asyncio
    async def test_complete_metadata_workflow(self):
        """Test a complete metadata management workflow."""
        package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "Old description",
                "keywords": "old,keywords",
                "classifiers": ["Development Status :: 3 - Alpha"],
                "home_page": "https://old-site.com",
                "project_urls": {},
            }
        }
        
        with patch.object(PyPIMetadataClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = package_data
            mock_request.return_value = mock_response
            
            with patch.object(PyPIMetadataClient, '_verify_package_ownership', return_value=True):
                # Test metadata update
                metadata_result = await update_package_metadata(
                    package_name="test-package",
                    description="New improved description",
                    keywords=["python", "testing", "automation"],
                    classifiers=["Development Status :: 4 - Beta"],
                    api_token="test-token",
                    dry_run=True,
                )
                
                # Test URL management
                url_result = await manage_package_urls(
                    package_name="test-package",
                    homepage="https://new-homepage.com",
                    documentation="https://docs.new-site.com",
                    repository="https://github.com/user/test-package",
                    validate_urls=False,
                    dry_run=True,
                )
                
                # Test keyword management
                keyword_result = await manage_package_keywords(
                    package_name="test-package",
                    action="add",
                    keywords=["cli", "tool"],
                    api_token="test-token",
                    dry_run=True,
                )
                
                # Verify all operations completed successfully
                assert metadata_result["dry_run"] is True
                assert url_result["dry_run"] is True  
                assert keyword_result["dry_run"] is True
                
                assert metadata_result["changes_detected"]["description"]["changed"] is True
                assert url_result["changes_detected"]["homepage"]["changed"] is True
                assert keyword_result["changes_detected"] is True
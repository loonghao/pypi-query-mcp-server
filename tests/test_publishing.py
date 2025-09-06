"""Tests for PyPI publishing and account management tools."""

import asyncio
import json
import os
import tempfile
from pathlib import Path
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
    PyPIUploadError,
    RateLimitError,
)
from pypi_query_mcp.tools.publishing import (
    PyPIPublishingClient,
    check_pypi_credentials,
    delete_pypi_release,
    get_pypi_account_info,
    get_pypi_upload_history,
    manage_pypi_maintainers,
    upload_package_to_pypi,
)


class TestPyPIPublishingClient:
    """Test cases for PyPIPublishingClient."""

    def test_init_default(self):
        """Test client initialization with default values."""
        client = PyPIPublishingClient()
        
        assert client.api_token is None
        assert client.test_pypi is False
        assert client.timeout == 60.0
        assert client.max_retries == 3
        assert client.retry_delay == 2.0
        assert "upload.pypi.org" in client.upload_url
        assert "pypi.org" in client.api_url

    def test_init_test_pypi(self):
        """Test client initialization for TestPyPI."""
        client = PyPIPublishingClient(test_pypi=True)
        
        assert client.test_pypi is True
        assert "test.pypi.org" in client.upload_url
        assert "test.pypi.org" in client.api_url

    def test_init_with_token(self):
        """Test client initialization with API token."""
        token = "pypi-test-token"
        client = PyPIPublishingClient(api_token=token)
        
        assert client.api_token == token
        assert "Authorization" in client._client.headers
        assert client._client.headers["Authorization"] == f"token {token}"

    def test_validate_package_name_valid(self):
        """Test package name validation with valid names."""
        client = PyPIPublishingClient()
        
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
        client = PyPIPublishingClient()
        
        invalid_names = [
            "",
            "   ",
            "-invalid",
            "invalid-",
            ".invalid",
            "invalid.",
            "in..valid",
            "in--valid",
            "in valid",
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
            
            client = PyPIPublishingClient()
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
            
            client = PyPIPublishingClient()
            
            with pytest.raises(PyPIAuthenticationError):
                await client._make_request("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_make_request_permission_error(self):
        """Test HTTP request with permission error."""
        with patch.object(httpx.AsyncClient, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.return_value = mock_response
            
            client = PyPIPublishingClient()
            
            with pytest.raises(PyPIPermissionError):
                await client._make_request("GET", "https://example.com")

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self):
        """Test HTTP request with rate limit error."""
        with patch.object(httpx.AsyncClient, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_request.return_value = mock_response
            
            client = PyPIPublishingClient()
            
            with pytest.raises(RateLimitError) as exc_info:
                await client._make_request("GET", "https://example.com")
            
            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_make_request_network_error_with_retry(self):
        """Test HTTP request with network error and retry logic."""
        with patch.object(httpx.AsyncClient, 'request') as mock_request:
            mock_request.side_effect = httpx.NetworkError("Connection failed")
            
            client = PyPIPublishingClient(max_retries=1, retry_delay=0.01)
            
            with pytest.raises(NetworkError):
                await client._make_request("GET", "https://example.com")
            
            # Should retry once (initial + 1 retry = 2 calls)
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as async context manager."""
        with patch.object(PyPIPublishingClient, 'close') as mock_close:
            async with PyPIPublishingClient() as client:
                assert client is not None
            
            mock_close.assert_called_once()


class TestUploadPackageToPyPI:
    """Test cases for upload_package_to_pypi function."""

    @pytest.fixture
    def temp_dist_files(self):
        """Create temporary distribution files for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create fake distribution files
            wheel_file = temp_path / "test_package-1.0.0-py3-none-any.whl"
            sdist_file = temp_path / "test_package-1.0.0.tar.gz"
            
            wheel_file.write_bytes(b"fake wheel content")
            sdist_file.write_bytes(b"fake sdist content")
            
            yield [str(wheel_file), str(sdist_file)]

    @pytest.mark.asyncio
    async def test_upload_no_distribution_paths(self):
        """Test upload with no distribution paths."""
        with pytest.raises(ValueError, match="No distribution paths provided"):
            await upload_package_to_pypi([])

    @pytest.mark.asyncio
    async def test_upload_missing_files(self):
        """Test upload with missing distribution files."""
        missing_files = ["/nonexistent/file1.whl", "/nonexistent/file2.tar.gz"]
        
        with pytest.raises(FileNotFoundError):
            await upload_package_to_pypi(missing_files)

    @pytest.mark.asyncio
    async def test_upload_invalid_files(self, temp_dist_files):
        """Test upload with invalid file types."""
        temp_dir = Path(temp_dist_files[0]).parent
        invalid_file = temp_dir / "invalid.txt"
        invalid_file.write_text("not a distribution file")
        
        # Should skip invalid files and proceed with valid ones
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_request.return_value = mock_response
                
                result = await upload_package_to_pypi(
                    temp_dist_files + [str(invalid_file)],
                    test_pypi=True
                )
                
                # Should only process the 2 valid distribution files
                assert result["total_files"] == 2

    @pytest.mark.asyncio
    async def test_upload_authentication_failure(self, temp_dist_files):
        """Test upload with authentication failure."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": False}
            
            with pytest.raises(PyPIAuthenticationError):
                await upload_package_to_pypi(temp_dist_files, api_token="invalid-token")

    @pytest.mark.asyncio
    async def test_upload_successful(self, temp_dist_files):
        """Test successful upload."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_request.return_value = mock_response
                
                result = await upload_package_to_pypi(
                    temp_dist_files,
                    api_token="valid-token",
                    test_pypi=True
                )
                
                assert result["successful_uploads"] == 2
                assert result["failed_uploads"] == 0
                assert result["target_repository"] == "TestPyPI"
                assert len(result["upload_results"]) == 2
                
                for upload_result in result["upload_results"]:
                    assert upload_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_upload_file_exists_skip(self, temp_dist_files):
        """Test upload with existing file and skip_existing=True."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 409  # Conflict - file exists
                mock_request.return_value = mock_response
                
                result = await upload_package_to_pypi(
                    temp_dist_files,
                    skip_existing=True,
                    test_pypi=True
                )
                
                assert result["successful_uploads"] == 0
                assert result["skipped_uploads"] == 2
                
                for upload_result in result["upload_results"]:
                    assert upload_result["status"] == "skipped"
                    assert "already exists" in upload_result["error"]

    @pytest.mark.asyncio
    async def test_upload_with_verification(self, temp_dist_files):
        """Test upload with verification enabled."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
                # Mock upload response
                upload_response = Mock()
                upload_response.status_code = 200
                
                # Mock verification response
                verify_response = Mock()
                verify_response.status_code = 200
                
                mock_request.side_effect = [upload_response, upload_response, verify_response, verify_response]
                
                result = await upload_package_to_pypi(
                    temp_dist_files,
                    verify_uploads=True,
                    test_pypi=True
                )
                
                assert result["successful_uploads"] == 2
                assert "verification_results" in result
                assert len(result["verification_results"]) == 2


class TestCheckPyPICredentials:
    """Test cases for check_pypi_credentials function."""

    @pytest.mark.asyncio
    async def test_no_token_provided(self):
        """Test credential check with no token provided."""
        with patch.dict(os.environ, {}, clear=True):
            result = await check_pypi_credentials()
            
            assert result["valid"] is False
            assert "No API token provided" in result["error"]

    @pytest.mark.asyncio
    async def test_invalid_token_format(self):
        """Test credential check with invalid token format."""
        result = await check_pypi_credentials(api_token="invalid-format")
        
        assert result["valid"] is False
        assert "Invalid token format" in result["error"]

    @pytest.mark.asyncio
    async def test_valid_credentials(self):
        """Test credential check with valid credentials."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            result = await check_pypi_credentials(
                api_token="pypi-valid-token",
                test_pypi=True
            )
            
            assert result["valid"] is True
            assert result["repository"] == "TestPyPI"

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test credential check with invalid credentials."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_request.side_effect = PyPIAuthenticationError("Invalid token", 401)
            
            result = await check_pypi_credentials(api_token="pypi-invalid-token")
            
            assert result["valid"] is False
            assert result["status_code"] == 401

    @pytest.mark.asyncio
    async def test_permission_denied(self):
        """Test credential check with permission denied."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_request.return_value = mock_response
            
            result = await check_pypi_credentials(api_token="pypi-limited-token")
            
            assert result["valid"] is False
            assert result["status_code"] == 403
            assert "permissions" in result["error"]


class TestGetPyPIUploadHistory:
    """Test cases for get_pypi_upload_history function."""

    @pytest.mark.asyncio
    async def test_invalid_package_name(self):
        """Test upload history with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_upload_history("")

    @pytest.mark.asyncio
    async def test_package_not_found(self):
        """Test upload history for non-existent package."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            with pytest.raises(PackageNotFoundError):
                await get_pypi_upload_history("nonexistent-package")

    @pytest.mark.asyncio
    async def test_successful_history_retrieval(self):
        """Test successful upload history retrieval."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "author": "Test Author",
                "summary": "A test package",
                "license": "MIT",
            },
            "releases": {
                "1.0.0": [
                    {
                        "filename": "test_package-1.0.0-py3-none-any.whl",
                        "upload_time": "2024-01-01T12:00:00",
                        "upload_time_iso_8601": "2024-01-01T12:00:00Z",
                        "size": 12345,
                        "python_version": "py3",
                        "packagetype": "bdist_wheel",
                        "md5_digest": "abcd1234",
                        "digests": {"sha256": "efgh5678"},
                        "url": "https://pypi.org/...",
                        "yanked": False,
                    }
                ],
                "0.9.0": [
                    {
                        "filename": "test_package-0.9.0.tar.gz",
                        "upload_time": "2023-12-01T12:00:00",
                        "upload_time_iso_8601": "2023-12-01T12:00:00Z",
                        "size": 9876,
                        "python_version": "source",
                        "packagetype": "sdist",
                        "md5_digest": "wxyz9999",
                        "digests": {"sha256": "ijkl0000"},
                        "url": "https://pypi.org/...",
                        "yanked": True,
                        "yanked_reason": "Critical bug",
                    }
                ],
            },
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await get_pypi_upload_history("test-package", limit=10)
            
            assert result["package_name"] == "test-package"
            assert len(result["upload_history"]) == 2
            assert result["statistics"]["total_uploads"] == 2
            assert result["statistics"]["total_versions"] == 2
            assert result["statistics"]["yanked_uploads"] == 1
            assert result["statistics"]["package_types"]["bdist_wheel"] == 1
            assert result["statistics"]["package_types"]["sdist"] == 1
            
            # Check that uploads are sorted by time (newest first)
            assert result["upload_history"][0]["version"] == "1.0.0"
            assert result["upload_history"][1]["version"] == "0.9.0"

    @pytest.mark.asyncio
    async def test_upload_history_with_limit(self):
        """Test upload history retrieval with limit."""
        mock_package_data = {
            "info": {"name": "test-package", "version": "3.0.0"},
            "releases": {
                f"{i}.0.0": [
                    {
                        "filename": f"test_package-{i}.0.0.tar.gz",
                        "upload_time_iso_8601": f"2024-01-{i:02d}T12:00:00Z",
                        "size": 1000 + i,
                        "packagetype": "sdist",
                        "yanked": False,
                    }
                ]
                for i in range(1, 11)  # 10 versions
            },
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await get_pypi_upload_history("test-package", limit=5)
            
            # Should only return 5 uploads due to limit
            assert len(result["upload_history"]) == 5
            assert result["limit_applied"] == 5


class TestDeletePyPIRelease:
    """Test cases for delete_pypi_release function."""

    @pytest.mark.asyncio
    async def test_invalid_package_name(self):
        """Test deletion with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await delete_pypi_release("", "1.0.0")

    @pytest.mark.asyncio
    async def test_empty_version(self):
        """Test deletion with empty version."""
        with pytest.raises(ValueError, match="Version cannot be empty"):
            await delete_pypi_release("test-package", "")

    @pytest.mark.asyncio
    async def test_deletion_not_confirmed(self):
        """Test deletion without confirmation."""
        result = await delete_pypi_release(
            "test-package",
            "1.0.0",
            confirm_deletion=False,
            dry_run=False
        )
        
        assert result["success"] is False
        assert "not confirmed" in result["error"]
        assert "PRODUCTION PyPI deletion" in result["safety_warnings"]

    @pytest.mark.asyncio
    async def test_dry_run_successful(self):
        """Test successful dry run deletion."""
        mock_release_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "upload_time": "2024-01-01T12:00:00Z",
                "author": "Test Author",
                "summary": "Test package",
            },
            "urls": [
                {"filename": "test_package-1.0.0.tar.gz", "packagetype": "sdist"},
                {"filename": "test_package-1.0.0-py3-none-any.whl", "packagetype": "bdist_wheel"},
            ],
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_release_data
            mock_request.return_value = mock_response
            
            result = await delete_pypi_release(
                "test-package",
                "1.0.0",
                dry_run=True,
                test_pypi=True
            )
            
            assert result["success"] is True
            assert result["dry_run"] is True
            assert result["action"] == "dry_run_completed"
            assert result["release_info"]["file_count"] == 2

    @pytest.mark.asyncio
    async def test_package_not_found(self):
        """Test deletion of non-existent package/version."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            with pytest.raises(PackageNotFoundError):
                await delete_pypi_release("nonexistent-package", "1.0.0")

    @pytest.mark.asyncio
    async def test_deletion_permission_denied(self):
        """Test deletion with permission denied."""
        mock_release_data = {
            "info": {"name": "test-package", "version": "1.0.0"},
            "urls": [{"filename": "test_package-1.0.0.tar.gz"}],
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            # First call for verification, second for deletion
            verify_response = Mock()
            verify_response.status_code = 200
            verify_response.json.return_value = mock_release_data
            
            delete_response = Mock()
            delete_response.status_code = 403
            
            mock_request.side_effect = [verify_response, delete_response]
            
            result = await delete_pypi_release(
                "test-package",
                "1.0.0",
                confirm_deletion=True,
                dry_run=False,
                test_pypi=True
            )
            
            assert result["success"] is False
            assert result["action"] == "permission_denied"

    @pytest.mark.asyncio
    async def test_successful_deletion(self):
        """Test successful deletion."""
        mock_release_data = {
            "info": {"name": "test-package", "version": "1.0.0"},
            "urls": [{"filename": "test_package-1.0.0.tar.gz"}],
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            # First call for verification, second for deletion
            verify_response = Mock()
            verify_response.status_code = 200
            verify_response.json.return_value = mock_release_data
            
            delete_response = Mock()
            delete_response.status_code = 204
            
            mock_request.side_effect = [verify_response, delete_response]
            
            result = await delete_pypi_release(
                "test-package",
                "1.0.0",
                confirm_deletion=True,
                dry_run=False,
                test_pypi=True
            )
            
            assert result["success"] is True
            assert result["action"] == "deleted"


class TestManagePyPIMaintainers:
    """Test cases for manage_pypi_maintainers function."""

    @pytest.mark.asyncio
    async def test_invalid_package_name(self):
        """Test maintainer management with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await manage_pypi_maintainers("", "list")

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test maintainer management with invalid action."""
        with pytest.raises(ValueError, match="Invalid action"):
            await manage_pypi_maintainers("test-package", "invalid")

    @pytest.mark.asyncio
    async def test_missing_username_for_add(self):
        """Test add action without username."""
        with pytest.raises(ValueError, match="Username required"):
            await manage_pypi_maintainers("test-package", "add")

    @pytest.mark.asyncio
    async def test_list_maintainers_successful(self):
        """Test successful maintainer listing."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "author": "John Doe",
                "author_email": "john@example.com",
                "maintainer": "Jane Smith",
                "maintainer_email": "jane@example.com",
                "summary": "Test package",
                "license": "MIT",
            },
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_pypi_maintainers("test-package", "list")
            
            assert result["success"] is True
            assert result["action"] == "list"
            assert result["maintainer_count"] == 2
            assert len(result["current_maintainers"]) == 2
            
            # Check author information
            author_info = next(m for m in result["current_maintainers"] if m["type"] == "author")
            assert author_info["name"] == "John Doe"
            assert author_info["email"] == "john@example.com"
            
            # Check maintainer information
            maintainer_info = next(m for m in result["current_maintainers"] if m["type"] == "maintainer")
            assert maintainer_info["name"] == "Jane Smith"
            assert maintainer_info["email"] == "jane@example.com"

    @pytest.mark.asyncio
    async def test_add_maintainer_not_supported(self):
        """Test add maintainer operation (not supported via API)."""
        mock_package_data = {
            "info": {"name": "test-package", "author": "John Doe"},
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            result = await manage_pypi_maintainers(
                "test-package", 
                "add", 
                username="newuser"
            )
            
            assert result["success"] is False
            assert "not supported via API" in result["error"]
            assert "alternative_method" in result
            assert "web interface" in result["alternative_method"]["description"]

    @pytest.mark.asyncio
    async def test_package_not_found(self):
        """Test maintainer management for non-existent package."""
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response
            
            with pytest.raises(PackageNotFoundError):
                await manage_pypi_maintainers("nonexistent-package", "list")


class TestGetPyPIAccountInfo:
    """Test cases for get_pypi_account_info function."""

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test account info with invalid credentials."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": False}
            
            with pytest.raises(PyPIAuthenticationError):
                await get_pypi_account_info(api_token="invalid-token")

    @pytest.mark.asyncio
    async def test_successful_account_info(self):
        """Test successful account info retrieval."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True, "repository": "PyPI"}
            
            result = await get_pypi_account_info(api_token="valid-token")
            
            assert result["repository"] == "PyPI"
            assert result["credentials"]["valid"] is True
            assert "account_info" in result
            assert "recommendations" in result
            assert "useful_links" in result
            
            # Check account info structure
            account_info = result["account_info"]
            assert account_info["api_token_valid"] is True
            assert "account_limitations" in account_info
            assert "features" in account_info
            assert "user_projects" in account_info
            
            # Check recommendations
            assert len(result["recommendations"]) > 0
            assert any("two-factor" in rec for rec in result["recommendations"])
            
            # Check useful links
            links = result["useful_links"]
            assert "account_settings" in links
            assert "api_tokens" in links
            assert "projects" in links

    @pytest.mark.asyncio
    async def test_test_pypi_account_info(self):
        """Test account info for TestPyPI."""
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True, "repository": "TestPyPI"}
            
            result = await get_pypi_account_info(test_pypi=True)
            
            assert result["repository"] == "TestPyPI"
            assert result["test_pypi"] is True
            assert "test.pypi.org" in result["useful_links"]["account_settings"]


class TestIntegration:
    """Integration tests for publishing tools."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_simulation(self):
        """Test simulated end-to-end workflow."""
        # This test simulates a complete workflow without making real API calls
        
        # 1. Check credentials
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            cred_result = await check_pypi_credentials(api_token="pypi-test-token")
            assert cred_result["valid"] is True
        
        # 2. Get account info
        with patch('pypi_query_mcp.tools.publishing.check_pypi_credentials') as mock_cred:
            mock_cred.return_value = {"valid": True}
            
            account_result = await get_pypi_account_info(api_token="pypi-test-token")
            assert "account_info" in account_result
        
        # 3. Check upload history
        mock_package_data = {
            "info": {"name": "test-package"},
            "releases": {"1.0.0": [{"filename": "test-1.0.0.tar.gz"}]},
        }
        
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_package_data
            mock_request.return_value = mock_response
            
            history_result = await get_pypi_upload_history("test-package")
            assert len(history_result["upload_history"]) == 1
        
        # 4. Test dry run deletion
        with patch.object(PyPIPublishingClient, '_make_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "info": {"name": "test-package", "version": "1.0.0"},
                "urls": [{"filename": "test-1.0.0.tar.gz"}],
            }
            mock_request.return_value = mock_response
            
            delete_result = await delete_pypi_release(
                "test-package", "1.0.0", dry_run=True
            )
            assert delete_result["dry_run"] is True
            assert delete_result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__])
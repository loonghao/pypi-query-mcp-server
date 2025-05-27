"""Tests for package downloader functionality."""

import shutil
import tempfile
from unittest.mock import AsyncMock, mock_open, patch

import pytest

from pypi_query_mcp.core.exceptions import InvalidPackageNameError
from pypi_query_mcp.tools.package_downloader import (
    PackageDownloader,
    download_package_with_dependencies,
)


class TestPackageDownloader:
    """Test cases for PackageDownloader class."""

    @pytest.fixture
    def temp_download_dir(self):
        """Create a temporary download directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def downloader(self, temp_download_dir):
        """Create a PackageDownloader instance for testing."""
        return PackageDownloader(download_dir=temp_download_dir)

    @pytest.mark.asyncio
    async def test_download_package_invalid_name(self, downloader):
        """Test that invalid package names raise appropriate errors."""
        with pytest.raises(InvalidPackageNameError):
            await downloader.download_package_with_dependencies("")

        with pytest.raises(InvalidPackageNameError):
            await downloader.download_package_with_dependencies("   ")

    @pytest.mark.asyncio
    async def test_download_package_basic(self, downloader):
        """Test basic package download functionality."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": []
            },
            "releases": {
                "1.0.0": [
                    {
                        "filename": "test_package-1.0.0-py3-none-any.whl",
                        "url": "https://files.pythonhosted.org/packages/test_package-1.0.0-py3-none-any.whl",
                        "packagetype": "bdist_wheel",
                        "md5_digest": "abc123",
                        "size": 1024
                    }
                ]
            }
        }

        mock_resolution_result = {
            "package_name": "test-package",
            "dependency_tree": {
                "test-package": {
                    "name": "test-package",
                    "version": "1.0.0",
                    "dependencies": {"runtime": [], "development": [], "extras": {}},
                    "depth": 0,
                    "children": {}
                }
            },
            "summary": {"total_packages": 1}
        }

        with patch.object(downloader.resolver, 'resolve_dependencies') as mock_resolve:
            mock_resolve.return_value = mock_resolution_result

            # Mock the _download_single_package method directly
            with patch.object(downloader, '_download_single_package') as mock_download_single:
                mock_download_single.return_value = {
                    "package_name": "test-package",
                    "version": "1.0.0",
                    "file_info": mock_package_data["releases"]["1.0.0"][0],
                    "download_result": {
                        "filename": "test_package-1.0.0-py3-none-any.whl",
                        "file_path": "/tmp/test_package-1.0.0-py3-none-any.whl",
                        "downloaded_size": 1024,
                        "verification": {},
                        "success": True
                    }
                }

                result = await downloader.download_package_with_dependencies("test-package")

                assert result["package_name"] == "test-package"
                assert "download_results" in result
                assert "summary" in result
                mock_download_single.assert_called()

    @pytest.mark.asyncio
    async def test_select_best_file_prefer_wheel(self, downloader):
        """Test file selection with wheel preference."""
        release_files = [
            {
                "filename": "test_package-1.0.0.tar.gz",
                "packagetype": "sdist",
                "url": "https://example.com/test_package-1.0.0.tar.gz"
            },
            {
                "filename": "test_package-1.0.0-py3-none-any.whl",
                "packagetype": "bdist_wheel",
                "url": "https://example.com/test_package-1.0.0-py3-none-any.whl"
            }
        ]

        selected = downloader._select_best_file(release_files, prefer_wheel=True)
        assert selected["packagetype"] == "bdist_wheel"

    @pytest.mark.asyncio
    async def test_select_best_file_prefer_source(self, downloader):
        """Test file selection with source preference."""
        release_files = [
            {
                "filename": "test_package-1.0.0.tar.gz",
                "packagetype": "sdist",
                "url": "https://example.com/test_package-1.0.0.tar.gz"
            },
            {
                "filename": "test_package-1.0.0-py3-none-any.whl",
                "packagetype": "bdist_wheel",
                "url": "https://example.com/test_package-1.0.0-py3-none-any.whl"
            }
        ]

        selected = downloader._select_best_file(release_files, prefer_wheel=False)
        assert selected["packagetype"] == "sdist"

    @pytest.mark.asyncio
    async def test_filter_compatible_wheels(self, downloader):
        """Test filtering wheels by Python version compatibility."""
        wheels = [
            {"filename": "test_package-1.0.0-py38-none-any.whl"},
            {"filename": "test_package-1.0.0-py310-none-any.whl"},
            {"filename": "test_package-1.0.0-py3-none-any.whl"},
            {"filename": "test_package-1.0.0-cp39-cp39-linux_x86_64.whl"}
        ]

        compatible = downloader._filter_compatible_wheels(wheels, "3.10")

        # Should include py310 and py3 wheels
        assert len(compatible) >= 2
        filenames = [w["filename"] for w in compatible]
        assert any("py310" in f for f in filenames)
        assert any("py3" in f for f in filenames)

    @pytest.mark.asyncio
    async def test_download_with_python_version(self, downloader):
        """Test download with specific Python version."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": []
            },
            "releases": {
                "1.0.0": [
                    {
                        "filename": "test_package-1.0.0-py310-none-any.whl",
                        "url": "https://files.pythonhosted.org/packages/test_package-1.0.0-py310-none-any.whl",
                        "packagetype": "bdist_wheel",
                        "md5_digest": "abc123",
                        "size": 1024
                    }
                ]
            }
        }

        mock_resolution_result = {
            "package_name": "test-package",
            "dependency_tree": {
                "test-package": {
                    "name": "test-package",
                    "version": "1.0.0",
                    "dependencies": {"runtime": [], "development": [], "extras": {}},
                    "depth": 0,
                    "children": {}
                }
            },
            "summary": {"total_packages": 1}
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class, \
             patch('httpx.AsyncClient') as mock_httpx_class, \
             patch.object(downloader.resolver, 'resolve_dependencies') as mock_resolve:

            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            mock_resolve.return_value = mock_resolution_result

            mock_httpx_client = AsyncMock()
            mock_httpx_class.return_value.__aenter__.return_value = mock_httpx_client

            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.aiter_bytes.return_value = [b"test content"]
            mock_httpx_client.stream.return_value.__aenter__.return_value = mock_response

            with patch("builtins.open", mock_open()):
                result = await downloader.download_package_with_dependencies(
                    "test-package",
                    python_version="3.10"
                )

                assert result["python_version"] == "3.10"

    @pytest.mark.asyncio
    async def test_download_package_with_dependencies_function(self, temp_download_dir):
        """Test the standalone download_package_with_dependencies function."""

        with patch('pypi_query_mcp.tools.package_downloader.PackageDownloader') as mock_downloader_class:
            # Setup downloader mock
            mock_downloader = AsyncMock()
            mock_downloader_class.return_value = mock_downloader
            mock_downloader.download_package_with_dependencies.return_value = {
                "package_name": "test-package",
                "python_version": None,
                "download_directory": temp_download_dir,
                "resolution_result": {
                    "package_name": "test-package",
                    "dependency_tree": {
                        "test-package": {
                            "name": "test-package",
                            "version": "1.0.0",
                            "dependencies": {"runtime": [], "development": [], "extras": {}},
                            "depth": 0,
                            "children": {}
                        }
                    },
                    "summary": {"total_packages": 1}
                },
                "download_results": {},
                "failed_downloads": [],
                "summary": {
                    "total_packages": 1,
                    "successful_downloads": 1,
                    "failed_downloads": 0,
                    "total_downloaded_size": 1024,
                    "download_directory": temp_download_dir,
                    "success_rate": 100.0
                }
            }

            result = await download_package_with_dependencies(
                "test-package",
                download_dir=temp_download_dir
            )

            assert result["package_name"] == "test-package"
            assert result["download_directory"] == temp_download_dir

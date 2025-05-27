"""Tests for dependency resolver functionality."""

from unittest.mock import AsyncMock, patch

import pytest

from pypi_query_mcp.core.exceptions import InvalidPackageNameError, PackageNotFoundError
from pypi_query_mcp.tools.dependency_resolver import (
    DependencyResolver,
    resolve_package_dependencies,
)


class TestDependencyResolver:
    """Test cases for DependencyResolver class."""

    @pytest.fixture
    def resolver(self):
        """Create a DependencyResolver instance for testing."""
        return DependencyResolver(max_depth=3)

    @pytest.mark.asyncio
    async def test_resolve_dependencies_invalid_package_name(self, resolver):
        """Test that invalid package names raise appropriate errors."""
        with pytest.raises(InvalidPackageNameError):
            await resolver.resolve_dependencies("")

        with pytest.raises(InvalidPackageNameError):
            await resolver.resolve_dependencies("   ")

    @pytest.mark.asyncio
    async def test_resolve_dependencies_basic(self, resolver):
        """Test basic dependency resolution."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": [
                    "requests>=2.25.0",
                    "click>=8.0.0"
                ]
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies("test-package")

            assert result["package_name"] == "test-package"
            assert "dependency_tree" in result
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_resolve_dependencies_with_python_version(self, resolver):
        """Test dependency resolution with Python version filtering."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": [
                    "requests>=2.25.0",
                    "typing-extensions>=4.0.0; python_version<'3.10'"
                ]
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies(
                "test-package",
                python_version="3.11"
            )

            assert result["python_version"] == "3.11"
            assert "dependency_tree" in result

    @pytest.mark.asyncio
    async def test_resolve_dependencies_with_extras(self, resolver):
        """Test dependency resolution with extra dependencies."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": [
                    "requests>=2.25.0",
                    "pytest>=6.0.0; extra=='test'"
                ]
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies(
                "test-package",
                include_extras=["test"]
            )

            assert result["include_extras"] == ["test"]
            assert "dependency_tree" in result

    @pytest.mark.asyncio
    async def test_resolve_dependencies_max_depth(self, resolver):
        """Test that max depth is respected."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0"]
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies(
                "test-package",
                max_depth=1
            )

            assert result["summary"]["max_depth"] <= 1

    @pytest.mark.asyncio
    async def test_resolve_package_dependencies_function(self):
        """Test the standalone resolve_package_dependencies function."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0"]
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolve_package_dependencies("test-package")

            assert result["package_name"] == "test-package"
            assert "dependency_tree" in result
            assert "summary" in result

    @pytest.mark.asyncio
    async def test_circular_dependency_handling(self, resolver):
        """Test that circular dependencies are handled properly."""
        # This is a simplified test - in reality, circular dependencies
        # are prevented by the visited set
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["test-package>=1.0.0"]  # Self-dependency
            }
        }

        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            # Should not hang or crash
            result = await resolver.resolve_dependencies("test-package")
            assert "dependency_tree" in result

    @pytest.mark.asyncio
    async def test_package_not_found_handling(self, resolver):
        """Test handling of packages that are not found."""
        with patch('pypi_query_mcp.core.PyPIClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.side_effect = PackageNotFoundError("Package not found")

            with pytest.raises(PackageNotFoundError):
                await resolver.resolve_dependencies("nonexistent-package")

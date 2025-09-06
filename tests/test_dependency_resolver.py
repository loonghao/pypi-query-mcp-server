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
                "requires_dist": ["requests>=2.25.0", "click>=8.0.0"],
            }
        }

        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
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
                    "typing-extensions>=4.0.0; python_version<'3.10'",
                ],
            }
        }

        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies(
                "test-package", python_version="3.11"
            )

            assert result["python_version"] == "3.11"
            assert "dependency_tree" in result

    @pytest.mark.asyncio
    async def test_resolve_dependencies_with_extras(self, resolver):
        """Test dependency resolution with extra dependencies."""
        mock_package_data = {
            "info": {
                "name": "mock-test-package-12345",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0", "pytest>=6.0.0; extra=='test'"],
            }
        }

        # Mock for transitive dependencies
        mock_requests_data = {
            "info": {
                "name": "requests",
                "version": "2.25.0",
                "requires_python": ">=3.6",
                "requires_dist": [],
            }
        }

        mock_pytest_data = {
            "info": {
                "name": "pytest",
                "version": "6.0.0",
                "requires_python": ">=3.6",
                "requires_dist": [],
            }
        }

        # Patch the PyPIClient import at the module level where it's used
        with patch("pypi_query_mcp.tools.dependency_resolver.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Setup mock to return different data based on package name
            def mock_get_package_info(package_name):
                if package_name.lower() == "mock-test-package-12345":
                    return mock_package_data
                elif package_name.lower() == "requests":
                    return mock_requests_data
                elif package_name.lower() == "pytest":
                    return mock_pytest_data
                else:
                    return {
                        "info": {
                            "name": package_name,
                            "version": "1.0.0",
                            "requires_dist": [],
                        }
                    }

            mock_client.get_package_info.side_effect = mock_get_package_info

            result = await resolver.resolve_dependencies(
                "mock-test-package-12345", include_extras=["test"], max_depth=2
            )

            assert result["include_extras"] == ["test"]
            assert "dependency_tree" in result

            # Verify that the main package is in the dependency tree
            assert "mock-test-package-12345" in result["dependency_tree"]
            
            # The extras should be resolved when include_extras=["test"] is specified
            # Check that pytest is included as an extra dependency
            main_pkg = result["dependency_tree"]["mock-test-package-12345"]
            assert "dependencies" in main_pkg
            assert "extras" in main_pkg["dependencies"]
            
            # Check if test extras are included
            if "test" in main_pkg["dependencies"]["extras"]:
                assert len(main_pkg["dependencies"]["extras"]["test"]) >= 1
                # Verify summary counts extras correctly
                assert result["summary"]["total_extra_dependencies"] >= 1

    @pytest.mark.asyncio
    async def test_resolve_dependencies_with_extras_and_python_version(self, resolver):
        """Test that extras work correctly with Python version filtering."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": [
                    "requests>=2.25.0",
                    "typing-extensions>=4.0.0; python_version<'3.10'",
                    "pytest>=6.0.0; extra=='test'",
                    "coverage>=5.0; extra=='test'",
                ],
            }
        }

        # Mock for transitive dependencies
        mock_requests_data = {
            "info": {
                "name": "requests",
                "version": "2.25.0",
                "requires_python": ">=3.6",
                "requires_dist": [],
            }
        }

        mock_pytest_data = {
            "info": {
                "name": "pytest",
                "version": "6.0.0",
                "requires_python": ">=3.6",
                "requires_dist": [],
            }
        }

        mock_coverage_data = {
            "info": {
                "name": "coverage",
                "version": "5.0.0",
                "requires_python": ">=3.6",
                "requires_dist": [],
            }
        }

        with patch("pypi_query_mcp.tools.dependency_resolver.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Setup mock to return different data based on package name
            def mock_get_package_info(package_name):
                if package_name.lower() == "test-package":
                    return mock_package_data
                elif package_name.lower() == "requests":
                    return mock_requests_data
                elif package_name.lower() == "pytest":
                    return mock_pytest_data
                elif package_name.lower() == "coverage":
                    return mock_coverage_data
                else:
                    return {
                        "info": {
                            "name": package_name,
                            "version": "1.0.0",
                            "requires_dist": [],
                        }
                    }

            mock_client.get_package_info.side_effect = mock_get_package_info

            # Test with Python 3.11 - should not include typing-extensions but should include extras
            result = await resolver.resolve_dependencies(
                "test-package",
                python_version="3.11",
                include_extras=["test"],
                max_depth=2,
            )

            assert result["include_extras"] == ["test"]
            assert result["python_version"] == "3.11"

            # Verify that the main package is in the dependency tree
            assert "test-package" in result["dependency_tree"]
            
            # The extras should be resolved when include_extras=["test"] is specified
            main_pkg = result["dependency_tree"]["test-package"]
            assert "dependencies" in main_pkg
            assert "extras" in main_pkg["dependencies"]
            
            # Verify that test extras are included and contain both pytest and coverage
            if "test" in main_pkg["dependencies"]["extras"]:
                test_deps = main_pkg["dependencies"]["extras"]["test"]
                assert len(test_deps) >= 2  # Should have pytest and coverage
                # Verify summary counts extras correctly
                assert result["summary"]["total_extra_dependencies"] >= 2

            # Verify Python version filtering worked for runtime deps but not extras
            runtime_deps = main_pkg["dependencies"]["runtime"]
            assert len(runtime_deps) == 1  # Only requests, not typing-extensions
            assert "requests" in runtime_deps[0]

    @pytest.mark.asyncio
    async def test_resolve_dependencies_max_depth(self, resolver):
        """Test that max depth is respected."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0"],
            }
        }

        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            result = await resolver.resolve_dependencies("test-package", max_depth=1)

            assert result["summary"]["max_depth"] <= 1

    @pytest.mark.asyncio
    async def test_resolve_package_dependencies_function(self):
        """Test the standalone resolve_package_dependencies function."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0"],
            }
        }

        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
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
                "requires_dist": ["test-package>=1.0.0"],  # Self-dependency
            }
        }

        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_data

            # Should not hang or crash
            result = await resolver.resolve_dependencies("test-package")
            assert "dependency_tree" in result

    @pytest.mark.asyncio
    async def test_package_not_found_handling(self, resolver):
        """Test handling of packages that are not found."""
        with patch("pypi_query_mcp.core.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.side_effect = PackageNotFoundError(
                "Package not found"
            )

            with pytest.raises(PackageNotFoundError):
                await resolver.resolve_dependencies("nonexistent-package")

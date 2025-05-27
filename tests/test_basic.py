"""Basic tests for PyPI Query MCP Server."""

import pytest

from pypi_query_mcp import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_import():
    """Test that main modules can be imported."""
    from pypi_query_mcp.core import PyPIClient, VersionCompatibility
    from pypi_query_mcp.server import mcp

    assert PyPIClient is not None
    assert VersionCompatibility is not None
    assert mcp is not None


@pytest.mark.asyncio
async def test_pypi_client_basic():
    """Test basic PyPI client functionality."""
    from pypi_query_mcp.core import PyPIClient

    async with PyPIClient() as client:
        # Test that client can be created and closed
        assert client is not None

        # Test cache clearing
        client.clear_cache()


def test_version_compatibility():
    """Test version compatibility utility."""
    from pypi_query_mcp.core import VersionCompatibility

    compat = VersionCompatibility()

    # Test requires_python parsing
    spec = compat.parse_requires_python(">=3.8")
    assert spec is not None

    # Test classifier extraction
    classifiers = [
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython"
    ]

    versions = compat.extract_python_versions_from_classifiers(classifiers)
    assert "3.8" in versions
    assert "3.9" in versions

    implementations = compat.extract_python_implementations(classifiers)
    assert "CPython" in implementations


def test_mcp_tools_import():
    """Test that MCP tools can be imported."""
    from pypi_query_mcp.tools import (
        check_python_compatibility,
        get_compatible_python_versions,
        query_package_dependencies,
        query_package_info,
        query_package_versions,
        suggest_python_version_for_packages,
    )

    # Test that all tools are callable
    assert callable(query_package_info)
    assert callable(query_package_versions)
    assert callable(query_package_dependencies)
    assert callable(check_python_compatibility)
    assert callable(get_compatible_python_versions)
    assert callable(suggest_python_version_for_packages)

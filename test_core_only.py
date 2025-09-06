#!/usr/bin/env python3
"""Test script to verify the version parameter fix - core functionality only."""

import asyncio
import logging
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_pypi_client():
    """Test the PyPIClient with version-specific queries."""
    # Import only the core modules we need
    from pypi_query_mcp.core.exceptions import PackageNotFoundError
    from pypi_query_mcp.core.pypi_client import PyPIClient

    async with PyPIClient() as client:
        # Test 1: Django 4.2.0 (specific version)
        logger.info("Testing Django 4.2.0...")
        try:
            data = await client.get_package_info("django", version="4.2.0")
            actual_version = data.get("info", {}).get("version", "")
            if actual_version in ["4.2", "4.2.0"]:  # PyPI may normalize version numbers
                logger.info(
                    f"✅ Django 4.2.0 test passed (got version: {actual_version})"
                )
            else:
                logger.error(f"❌ Expected version 4.2.0, got {actual_version}")
                return False

            # Check dependencies
            deps = data.get("info", {}).get("requires_dist", [])
            logger.info(f"   Dependencies found: {len(deps) if deps else 0}")

        except Exception as e:
            logger.error(f"❌ Django 4.2.0 test failed: {e}")
            return False

        # Test 2: Latest Django (no version)
        logger.info("Testing Django latest...")
        try:
            data = await client.get_package_info("django", version=None)
            actual_version = data.get("info", {}).get("version", "")
            logger.info(f"✅ Django latest test passed - version: {actual_version}")
        except Exception as e:
            logger.error(f"❌ Django latest test failed: {e}")
            return False

        # Test 3: Non-existent version (should fail)
        logger.info("Testing Django 999.999.999 (should fail)...")
        try:
            data = await client.get_package_info("django", version="999.999.999")
            logger.error("❌ Expected error for non-existent version but got result")
            return False
        except PackageNotFoundError:
            logger.info("✅ Non-existent version test passed (correctly failed)")
        except Exception as e:
            logger.error(f"❌ Unexpected error type: {e}")
            return False

        # Test 4: FastAPI 0.100.0
        logger.info("Testing FastAPI 0.100.0...")
        try:
            data = await client.get_package_info("fastapi", version="0.100.0")
            actual_version = data.get("info", {}).get("version", "")
            if actual_version == "0.100.0":
                logger.info("✅ FastAPI 0.100.0 test passed")
            else:
                logger.error(f"❌ Expected version 0.100.0, got {actual_version}")
                return False
        except Exception as e:
            logger.error(f"❌ FastAPI 0.100.0 test failed: {e}")
            return False

        # Test 5: NumPy 1.20.0
        logger.info("Testing NumPy 1.20.0...")
        try:
            data = await client.get_package_info("numpy", version="1.20.0")
            actual_version = data.get("info", {}).get("version", "")
            if actual_version == "1.20.0":
                logger.info("✅ NumPy 1.20.0 test passed")
            else:
                logger.error(f"❌ Expected version 1.20.0, got {actual_version}")
                return False
        except Exception as e:
            logger.error(f"❌ NumPy 1.20.0 test failed: {e}")
            return False

    return True


async def test_dependency_formatting():
    """Test the dependency formatting functions."""
    from pypi_query_mcp.tools.package_query import (
        format_dependency_info,
        validate_version_format,
    )

    # Test version validation
    logger.info("Testing version validation...")
    test_versions = [
        ("1.0.0", True),
        ("2.1", True),
        ("1.0.0a1", True),
        ("1.0.0b2", True),
        ("1.0.0rc1", True),
        ("2.0.0.dev1", True),
        ("invalid.version!", False),
        ("", False),
        (None, True),
    ]

    for version, expected in test_versions:
        result = validate_version_format(version)
        if result == expected:
            logger.info(f"✅ Version validation for '{version}': {result}")
        else:
            logger.error(
                f"❌ Version validation for '{version}': expected {expected}, got {result}"
            )
            return False

    # Test dependency formatting with mock data
    logger.info("Testing dependency formatting...")
    mock_data = {
        "info": {
            "name": "test-package",
            "version": "1.0.0",
            "requires_python": ">=3.8",
            "requires_dist": [
                "requests>=2.25.0",
                "click>=8.0.0",
                "pytest>=6.0.0; extra=='test'",
                "black>=21.0.0; extra=='dev'",
            ],
        }
    }

    result = format_dependency_info(mock_data)
    expected_fields = [
        "package_name",
        "version",
        "runtime_dependencies",
        "dependency_summary",
    ]
    for field in expected_fields:
        if field not in result:
            logger.error(f"❌ Missing field '{field}' in dependency formatting result")
            return False

    if len(result["runtime_dependencies"]) >= 2:  # Should have requests and click
        logger.info("✅ Dependency formatting test passed")
    else:
        logger.error(
            f"❌ Expected at least 2 runtime dependencies, got {len(result['runtime_dependencies'])}"
        )
        return False

    return True


async def test_comparison():
    """Test that version-specific queries return different results than latest."""
    from pypi_query_mcp.core.pypi_client import PyPIClient

    logger.info("Testing that version-specific queries work differently than latest...")

    async with PyPIClient() as client:
        # Get Django latest
        latest_data = await client.get_package_info("django", version=None)
        latest_version = latest_data.get("info", {}).get("version", "")

        # Get Django 4.2.0 specifically
        specific_data = await client.get_package_info("django", version="4.2.0")
        specific_version = specific_data.get("info", {}).get("version", "")

        logger.info(f"Latest Django version: {latest_version}")
        logger.info(f"Specific Django version: {specific_version}")

        # They should be different (unless 4.2.0 happens to be latest, which is unlikely)
        if specific_version in ["4.2", "4.2.0"] and latest_version != specific_version:
            logger.info(
                "✅ Version-specific query returns different version than latest"
            )
            return True
        elif specific_version in ["4.2", "4.2.0"]:
            logger.info(
                "⚠️  Specific version matches latest (this is fine, but less conclusive)"
            )
            return True
        else:
            logger.error(
                f"❌ Specific version query failed: expected 4.2.0, got {specific_version}"
            )
            return False


async def main():
    """Run all tests."""
    logger.info("Starting PyPI client and dependency query tests...")

    success = True

    # Test PyPI client
    if await test_pypi_client():
        logger.info("✅ PyPI client tests passed")
    else:
        logger.error("❌ PyPI client tests failed")
        success = False

    # Test dependency formatting
    if await test_dependency_formatting():
        logger.info("✅ Dependency formatting tests passed")
    else:
        logger.error("❌ Dependency formatting tests failed")
        success = False

    # Test comparison
    if await test_comparison():
        logger.info("✅ Version comparison test passed")
    else:
        logger.error("❌ Version comparison test failed")
        success = False

    if success:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

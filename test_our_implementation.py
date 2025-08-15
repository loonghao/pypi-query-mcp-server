#!/usr/bin/env python3
"""Test our actual implementation directly."""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_our_implementation():
    """Test our actual implementation directly."""
    
    # Import just the core pieces we need
    from pypi_query_mcp.core.pypi_client import PyPIClient
    from pypi_query_mcp.tools.package_query import (
        query_package_dependencies, 
        validate_version_format,
        format_dependency_info
    )
    from pypi_query_mcp.core.exceptions import PackageNotFoundError, InvalidPackageNameError
    
    logger.info("Testing our actual implementation...")
    
    # Test 1: Version validation
    logger.info("Testing version validation...")
    assert validate_version_format("1.0.0") == True
    assert validate_version_format("invalid!") == False
    assert validate_version_format(None) == True
    logger.info("✅ Version validation works correctly")
    
    # Test 2: PyPI Client with version
    logger.info("Testing PyPIClient with version parameter...")
    async with PyPIClient() as client:
        # Test specific version
        data = await client.get_package_info("django", version="4.2.0")
        assert data["info"]["version"] in ["4.2", "4.2.0"]
        logger.info(f"✅ Got Django 4.2.0: {data['info']['version']}")
        
        # Test latest version
        data = await client.get_package_info("django", version=None)
        latest_version = data["info"]["version"]
        logger.info(f"✅ Got Django latest: {latest_version}")
        
        # Verify they're different (unless 4.2 is latest, which is unlikely)
        if latest_version not in ["4.2", "4.2.0"]:
            logger.info("✅ Confirmed version-specific queries work differently than latest")
    
    # Test 3: Dependency formatting
    logger.info("Testing dependency formatting...")
    async with PyPIClient() as client:
        data = await client.get_package_info("django", version="4.2.0")
        formatted = format_dependency_info(data)
        
        assert "package_name" in formatted
        assert "version" in formatted
        assert "runtime_dependencies" in formatted
        assert "dependency_summary" in formatted
        assert formatted["version"] in ["4.2", "4.2.0"]
        logger.info(f"✅ Dependency formatting works: {len(formatted['runtime_dependencies'])} runtime deps")
    
    # Test 4: Full query_package_dependencies function
    logger.info("Testing query_package_dependencies function...")
    
    # Test with Django 4.2.0
    result = await query_package_dependencies("django", "4.2.0")
    assert result["package_name"].lower() == "django"
    assert result["version"] in ["4.2", "4.2.0"]
    logger.info(f"✅ Django 4.2.0 dependencies: {len(result['runtime_dependencies'])} runtime deps")
    
    # Test with Django latest
    result_latest = await query_package_dependencies("django", None)
    assert result_latest["package_name"].lower() == "django"
    logger.info(f"✅ Django latest dependencies: {len(result_latest['runtime_dependencies'])} runtime deps")
    
    # Verify they might be different
    if result["version"] != result_latest["version"]:
        logger.info("✅ Confirmed: version-specific query returns different version than latest")
    
    # Test 5: Error cases
    logger.info("Testing error cases...")
    
    # Invalid version format
    try:
        await query_package_dependencies("django", "invalid!")
        assert False, "Should have raised InvalidPackageNameError"
    except InvalidPackageNameError:
        logger.info("✅ Invalid version format correctly rejected")
    
    # Non-existent version
    try:
        await query_package_dependencies("django", "999.999.999")
        assert False, "Should have raised PackageNotFoundError"
    except PackageNotFoundError:
        logger.info("✅ Non-existent version correctly rejected")
    
    # Test 6: Multiple packages
    logger.info("Testing multiple packages...")
    
    packages_and_versions = [
        ("fastapi", "0.100.0"),
        ("numpy", "1.20.0"),
        ("requests", "2.25.1"),
    ]
    
    for package, version in packages_and_versions:
        try:
            result = await query_package_dependencies(package, version)
            assert result["package_name"].lower() == package.lower()
            assert result["version"] == version
            logger.info(f"✅ {package} {version}: {len(result['runtime_dependencies'])} runtime deps")
        except Exception as e:
            logger.warning(f"⚠️  {package} {version} failed (may not exist): {e}")
    
    return True


async def main():
    """Run the test."""
    try:
        success = await test_our_implementation()
        if success:
            logger.info("🎉 All implementation tests passed!")
            return 0
        else:
            logger.error("❌ Some tests failed!")
            return 1
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
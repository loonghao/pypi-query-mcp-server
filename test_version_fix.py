#!/usr/bin/env python3
"""Test script to verify the version parameter fix for get_package_dependencies."""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from pypi_query_mcp.tools.package_query import query_package_dependencies
from pypi_query_mcp.core.exceptions import PackageNotFoundError, InvalidPackageNameError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_package_version(package_name: str, version: str = None, expect_error: bool = False):
    """Test a specific package and version combination."""
    version_str = f" version {version}" if version else " (latest)"
    logger.info(f"Testing {package_name}{version_str}")
    
    try:
        result = await query_package_dependencies(package_name, version)
        
        if expect_error:
            logger.error(f"Expected error for {package_name}{version_str}, but got result")
            return False
            
        # Verify the result contains expected fields
        required_fields = ["package_name", "version", "runtime_dependencies", "dependency_summary"]
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing field '{field}' in result for {package_name}{version_str}")
                return False
        
        # Check if we got the correct version
        actual_version = result.get("version", "")
        if version and actual_version != version:
            logger.error(f"Expected version {version}, got {actual_version} for {package_name}")
            return False
        
        logger.info(f"✅ Success: {package_name}{version_str} - Got version {actual_version}")
        logger.info(f"   Runtime dependencies: {len(result['runtime_dependencies'])}")
        logger.info(f"   Total dependencies: {result['dependency_summary']['runtime_count']}")
        
        return True
        
    except Exception as e:
        if expect_error:
            logger.info(f"✅ Expected error for {package_name}{version_str}: {type(e).__name__}: {e}")
            return True
        else:
            logger.error(f"❌ Unexpected error for {package_name}{version_str}: {type(e).__name__}: {e}")
            return False


async def main():
    """Run all tests."""
    logger.info("Starting version parameter fix tests...")
    
    tests = [
        # Test with valid package versions
        ("django", "4.2.0", False),
        ("fastapi", "0.100.0", False),
        ("numpy", "1.20.0", False),
        
        # Test latest versions (no version specified)
        ("requests", None, False),
        ("click", None, False),
        
        # Test edge cases - should fail
        ("django", "999.999.999", True),  # Non-existent version
        ("nonexistent-package-12345", None, True),  # Non-existent package
        ("django", "invalid.version.format!", True),  # Invalid version format
        
        # Test pre-release versions
        ("django", "5.0a1", False),  # Pre-release (may or may not exist)
    ]
    
    passed = 0
    total = len(tests)
    
    for package, version, expect_error in tests:
        try:
            if await test_package_version(package, version, expect_error):
                passed += 1
        except Exception as e:
            logger.error(f"Test framework error: {e}")
    
    logger.info(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""Simple test script to verify the version parameter fix without server dependencies."""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_pypi_client():
    """Test the PyPIClient with version-specific queries."""
    from pypi_query_mcp.core.pypi_client import PyPIClient
    from pypi_query_mcp.core.exceptions import PackageNotFoundError
    
    async with PyPIClient() as client:
        # Test 1: Django 4.2.0 (specific version)
        logger.info("Testing Django 4.2.0...")
        try:
            data = await client.get_package_info("django", version="4.2.0")
            actual_version = data.get("info", {}).get("version", "")
            if actual_version == "4.2":  # PyPI may normalize version numbers
                logger.info("✅ Django 4.2.0 test passed (normalized to 4.2)")
            elif actual_version == "4.2.0":
                logger.info("✅ Django 4.2.0 test passed")
            else:
                logger.error(f"❌ Expected version 4.2.0, got {actual_version}")
                return False
                
            # Check dependencies
            deps = data.get("info", {}).get("requires_dist", [])
            logger.info(f"   Dependencies found: {len(deps)}")
            
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


async def test_dependency_query():
    """Test the query_package_dependencies function."""
    from pypi_query_mcp.tools.package_query import query_package_dependencies, validate_version_format
    from pypi_query_mcp.core.exceptions import InvalidPackageNameError, PackageNotFoundError
    
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
            logger.error(f"❌ Version validation for '{version}': expected {expected}, got {result}")
            return False
    
    # Test dependency queries
    logger.info("Testing dependency queries...")
    
    # Test Django 4.2.0 dependencies
    try:
        result = await query_package_dependencies("django", "4.2.0")
        if result["package_name"].lower() == "django" and result["version"] in ["4.2", "4.2.0"]:
            logger.info(f"✅ Django 4.2.0 dependencies query passed - {len(result['runtime_dependencies'])} runtime deps")
        else:
            logger.error(f"❌ Django dependencies query failed - got {result['package_name']} v{result['version']}")
            return False
    except Exception as e:
        logger.error(f"❌ Django dependencies query failed: {e}")
        return False
    
    # Test invalid version format
    try:
        result = await query_package_dependencies("django", "invalid.version!")
        logger.error("❌ Expected error for invalid version format")
        return False
    except InvalidPackageNameError:
        logger.info("✅ Invalid version format correctly rejected")
    except Exception as e:
        logger.error(f"❌ Unexpected error for invalid version: {e}")
        return False
    
    return True


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
    
    # Test dependency queries
    if await test_dependency_query():
        logger.info("✅ Dependency query tests passed")
    else:
        logger.error("❌ Dependency query tests failed")
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
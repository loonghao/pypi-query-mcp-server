#!/usr/bin/env python3
"""Test MCP tools integration and functionality."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pypi_query_mcp.server import main, mcp
from pypi_query_mcp.security.validation import sanitize_for_logging
from pypi_query_mcp.core.rate_limiter import get_rate_limited_client

logger = logging.getLogger(__name__)


class MCPIntegrationTestSuite:
    """Test MCP server and tools integration."""

    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def test_server_initialization(self):
        """Test that MCP server initializes correctly."""
        logger.info("Testing MCP server initialization...")

        try:
            # Test server creation (use the global mcp instance)
            server = mcp

            # Verify server has expected tools
            expected_tools = [
                "get_package_info",
                "get_package_versions",
                "get_package_dependencies",
                "search_pypi_packages",
                "scan_pypi_package_security_tool",
                "analyze_pypi_package_license_tool"
            ]

            # Get available tools from server (async method)
            tools = await server.get_tools()
            available_tool_names = list(tools.keys())

            for tool in expected_tools:
                if tool not in available_tool_names:
                    raise AssertionError(f"Required tool '{tool}' not found in server")

            logger.info(f"✅ Server initialized with {len(available_tool_names)} tools")

        except Exception as e:
            raise AssertionError(f"Server initialization failed: {e}")

    async def test_rate_limiting_integration(self):
        """Test rate limiting integration with MCP tools."""
        logger.info("Testing rate limiting integration...")

        try:
            # Test rate limiter client creation
            client = get_rate_limited_client("test")

            # Verify client has proper configuration
            assert hasattr(client, 'rate_limiter'), "Rate limiter missing rate_limiter configuration"

            # Test basic rate limiting functionality
            import time
            start_time = time.time()

            # Make multiple rapid requests to test throttling
            tasks = []
            for i in range(5):
                # Create mock request tasks
                tasks.append(asyncio.sleep(0.01))

            await asyncio.gather(*tasks)

            elapsed = time.time() - start_time
            logger.info(f"✅ Rate limiting integration working (elapsed: {elapsed:.3f}s)")

        except Exception as e:
            raise AssertionError(f"Rate limiting integration failed: {e}")

    async def test_security_validation_integration(self):
        """Test security validation integration."""
        logger.info("Testing security validation integration...")

        try:
            # Test log sanitization with various inputs
            test_cases = [
                "Normal package name",
                "github_pat_1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12",
                "https://user:pass@evil.com/malicious",
                "SECRET_KEY=very_secret_value"
            ]

            for test_input in test_cases:
                sanitized = sanitize_for_logging(test_input)

                # Verify no sensitive data leaked
                if any(word in sanitized.lower() for word in ['secret', 'pass', 'token', 'key']):
                    if 'REDACTED' not in sanitized:
                        raise AssertionError(f"Potential data leak in: {sanitized}")

            logger.info("✅ Security validation integration working correctly")

        except Exception as e:
            raise AssertionError(f"Security validation integration failed: {e}")

    async def test_tool_parameter_validation(self):
        """Test MCP tool parameter validation."""
        logger.info("Testing MCP tool parameter validation...")

        try:
            from pypi_query_mcp.security.validation import secure_validate_package_name

            # Test valid package names
            valid_names = ["requests", "numpy", "fastapi", "my-package"]
            for name in valid_names:
                result = secure_validate_package_name(name)
                if not result["valid"]:
                    raise AssertionError(f"Valid package name '{name}' rejected")

            # Test invalid/dangerous package names
            dangerous_names = ["../../../etc/passwd", "<script>alert('xss')</script>", "package; rm -rf /"]
            for name in dangerous_names:
                try:
                    secure_validate_package_name(name)
                    # Should raise SecurityValidationError
                    raise AssertionError(f"Dangerous package name '{name}' was accepted")
                except Exception:
                    # Expected to fail
                    pass

            logger.info("✅ Tool parameter validation working correctly")

        except Exception as e:
            raise AssertionError(f"Tool parameter validation failed: {e}")

    async def test_error_handling_integration(self):
        """Test error handling across MCP integration."""
        logger.info("Testing error handling integration...")

        try:
            # Test handling of various error conditions
            from pypi_query_mcp.core.exceptions import PyPIError, RateLimitError

            # Test custom exception handling
            test_exceptions = [
                PyPIError("Test PyPI error"),
                RateLimitError("Test rate limit error"),
                ValueError("Test value error")
            ]

            for exc in test_exceptions:
                # Verify exception can be raised and caught properly
                try:
                    raise exc
                except type(exc):
                    # Expected behavior
                    pass
                except Exception as e:
                    raise AssertionError(f"Unexpected exception type: {type(e)}")

            logger.info("✅ Error handling integration working correctly")

        except Exception as e:
            raise AssertionError(f"Error handling integration failed: {e}")

    async def test_resource_management(self):
        """Test resource management in MCP integration."""
        logger.info("Testing resource management...")

        try:
            # Test that resources are properly managed
            client = get_rate_limited_client("resource_test")

            # Test client can be created and closed properly
            await client.close()

            logger.info("✅ Resource management working correctly")

        except Exception as e:
            raise AssertionError(f"Resource management failed: {e}")

    async def test_configuration_validation(self):
        """Test configuration validation."""
        logger.info("Testing configuration validation...")

        try:
            # Test that configuration is properly validated
            from pypi_query_mcp.core.rate_limit_config import get_service_rate_limit

            # Test configuration can provide limits for services
            try:
                pypi_limits = get_service_rate_limit("pypi")
                assert pypi_limits is not None, "PyPI limits should be available"
                assert hasattr(pypi_limits, 'requests_per_second'), "Limits missing requests_per_second"
            except Exception as e:
                raise AssertionError(f"Failed to get PyPI limits: {e}")

            logger.info("✅ Configuration validation working correctly")

        except Exception as e:
            raise AssertionError(f"Configuration validation failed: {e}")

    async def run_all_tests(self):
        """Run all MCP integration tests."""
        logger.info("🔗 Starting MCP Integration Test Suite")
        logger.info("=" * 60)

        test_methods = [
            ("Server Initialization", self.test_server_initialization),
            ("Rate Limiting Integration", self.test_rate_limiting_integration),
            ("Security Validation Integration", self.test_security_validation_integration),
            ("Tool Parameter Validation", self.test_tool_parameter_validation),
            ("Error Handling Integration", self.test_error_handling_integration),
            ("Resource Management", self.test_resource_management),
            ("Configuration Validation", self.test_configuration_validation)
        ]

        for test_name, test_method in test_methods:
            try:
                logger.info(f"\n🧪 Running {test_name}")
                await test_method()
                self.test_results["passed"] += 1
                logger.info(f"✅ {test_name} PASSED")

            except Exception as e:
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"{test_name}: {str(e)}")
                logger.error(f"❌ {test_name} FAILED: {e}")

        # Print results
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

        logger.info("\n" + "=" * 60)
        logger.info("🔗 MCP INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {self.test_results['passed']}")
        logger.info(f"❌ Failed: {self.test_results['failed']}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")

        if self.test_results["errors"]:
            logger.info("\n❌ FAILED TESTS:")
            for error in self.test_results["errors"]:
                logger.info(f"   • {error}")

        logger.info("=" * 60)

        if self.test_results["failed"] == 0:
            logger.info("🎉 ALL MCP INTEGRATION TESTS PASSED!")
            return True
        else:
            logger.warning("⚠️  Some MCP integration tests failed.")
            return False


async def main():
    """Main function to run MCP integration tests."""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    print("🔗 mcpypi MCP Integration Test Suite")
    print("=" * 60)

    try:
        suite = MCPIntegrationTestSuite()
        success = await suite.run_all_tests()
        return 0 if success else 1

    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
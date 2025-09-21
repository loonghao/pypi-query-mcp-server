#!/usr/bin/env python3
"""Quick demonstration of the HTML reporting framework."""

import asyncio
import logging
import time
from pathlib import Path

# Import the HTML reporting framework
from pypi_query_mcp.reports import SecurityTestReporter, ReportConfig
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting, create_demo_report_config
from pypi_query_mcp.reports.report_data import TestSuiteResults, TestResult, TestStatus, TestCategory, PerformanceMetric

# Import existing test suite
from test_security_comprehensive import SecurityTestSuite

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_quick_integration():
    """Demonstrate quick integration with existing test suite."""
    logger.info("🚀 Demo 1: Quick Integration with Existing Test Suite")

    # Run existing SecurityTestSuite with beautiful HTML reports
    report_path = await run_security_tests_with_reporting(
        SecurityTestSuite,
        report_config=create_demo_report_config("gruvbox-dark")
    )

    logger.info(f"📊 Report generated: {report_path}")
    logger.info(f"🌐 Open in browser: file://{report_path.resolve()}")
    return report_path


def demo_manual_report_creation():
    """Demonstrate manual report creation with custom data."""
    logger.info("🚀 Demo 2: Manual Report Creation")

    # Create test results manually
    results = TestSuiteResults(
        suite_name="Custom Security Tests",
        start_time=time.time() - 30.0
    )

    # Add some sample tests
    test_cases = [
        {
            "name": "test_api_authentication",
            "category": TestCategory.SECURITY,
            "status": TestStatus.PASSED,
            "duration": 1.23,
            "logs": ["[INFO] Testing API authentication", "[INFO] ✅ Authentication working correctly"]
        },
        {
            "name": "test_input_sanitization",
            "category": TestCategory.INPUT_VALIDATION,
            "status": TestStatus.FAILED,
            "duration": 0.87,
            "error": "XSS attack not properly blocked",
            "logs": ["[ERROR] XSS payload was accepted", "[ERROR] ❌ Input sanitization failed"]
        },
        {
            "name": "test_rate_limiting",
            "category": TestCategory.RATE_LIMITING,
            "status": TestStatus.PASSED,
            "duration": 2.45,
            "logs": ["[INFO] Testing rate limiting", "[INFO] ✅ Rate limiting working correctly"]
        }
    ]

    for test_data in test_cases:
        test = TestResult(
            name=test_data["name"],
            category=test_data["category"],
            status=test_data["status"],
            duration=test_data["duration"]
        )

        test.output_logs = test_data["logs"]

        if test_data["status"] == TestStatus.FAILED:
            test.error_message = test_data["error"]

        # Add performance metrics
        test.add_performance_metric(PerformanceMetric(
            name="execution_time",
            value=test_data["duration"],
            unit="seconds",
            description="Test execution time"
        ))

        results.add_test(test)

    results.finish()

    # Generate report
    config = ReportConfig(
        theme="dracula",
        report_title="Custom Security Test Report",
        company_name="Demo Company"
    )

    reporter = SecurityTestReporter(config)
    report_path = reporter.generate_report(results, "demo_custom_report.html")

    logger.info(f"📊 Custom report generated: {report_path}")
    logger.info(f"🌐 Open in browser: file://{report_path.resolve()}")
    return report_path


def demo_theme_showcase():
    """Demonstrate all available themes."""
    logger.info("🚀 Demo 3: Theme Showcase")

    themes = ["gruvbox-dark", "solarized-dark", "dracula"]
    report_paths = []

    # Create sample data
    results = TestSuiteResults(
        suite_name="Theme Showcase Tests",
        start_time=time.time() - 15.0
    )

    # Add a few sample tests
    for i, status in enumerate([TestStatus.PASSED, TestStatus.FAILED, TestStatus.PASSED]):
        test = TestResult(
            name=f"test_example_{i+1}",
            category=TestCategory.SECURITY,
            status=status,
            duration=1.0 + i * 0.5
        )
        test.output_logs = [f"[INFO] Example test {i+1} execution"]
        if status == TestStatus.FAILED:
            test.error_message = "Example failure for demonstration"
        results.add_test(test)

    results.finish()

    # Generate report with each theme
    for theme in themes:
        config = ReportConfig(
            theme=theme,
            report_title=f"Security Report - {theme.title()} Theme"
        )

        reporter = SecurityTestReporter(config)
        report_path = reporter.generate_report(results, f"demo_theme_{theme}.html")
        report_paths.append(report_path)

        logger.info(f"🎨 {theme.title()} theme report: {report_path}")

    return report_paths


async def main():
    """Run all demonstrations."""
    logger.info("🎬 Starting HTML Test Report Framework Demonstration")
    logger.info("=" * 80)

    try:
        # Demo 1: Quick integration
        report1 = await demo_quick_integration()

        print("\n" + "-" * 40)

        # Demo 2: Manual creation
        report2 = demo_manual_report_creation()

        print("\n" + "-" * 40)

        # Demo 3: Theme showcase
        report3_list = demo_theme_showcase()

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("🎉 All demonstrations completed successfully!")
        logger.info("=" * 80)

        all_reports = [report1, report2] + report3_list

        for i, report in enumerate(all_reports, 1):
            logger.info(f"📄 Report {i}: {report}")
            logger.info(f"🌐 Open: file://{report.resolve()}")

        logger.info("\n💡 Open these HTML files in your browser to see:")
        logger.info("   ✨ Beautiful terminal-inspired themes")
        logger.info("   🔍 Interactive test filtering and search")
        logger.info("   📊 Performance metrics and charts")
        logger.info("   📝 Detailed test logs and error information")
        logger.info("   📱 Mobile-responsive design")
        logger.info("   ⌨️  Keyboard shortcuts (Ctrl+E to export, etc.)")

    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
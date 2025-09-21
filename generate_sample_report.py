#!/usr/bin/env python3
"""Generate a sample HTML security test report for demonstration."""

import json
import time
from datetime import datetime
from pathlib import Path

from pypi_query_mcp.reports import SecurityTestReporter, ReportConfig
from pypi_query_mcp.reports.report_data import (
    TestSuiteResults, TestResult, TestStatus, TestCategory, PerformanceMetric
)


def create_sample_test_data() -> TestSuiteResults:
    """Create sample test data for demonstration."""

    # Create test suite results
    results = TestSuiteResults(
        suite_name="MCPyPI Security Test Suite",
        start_time=time.time() - 45.0,  # Started 45 seconds ago
        environment_info={
            "python_version": "3.12.0",
            "platform": "Linux-6.16.7-arch1-1-x86_64",
            "hostname": "dev-machine",
            "working_directory": "/home/rpm/claude/pypi-query-mcp"
        },
        configuration={
            "theme": "gruvbox-dark",
            "auto_refresh": False,
            "performance_monitoring": True
        }
    )

    # Sample test cases with different outcomes
    test_cases = [
        {
            "name": "test_input_validation_attacks",
            "category": TestCategory.INPUT_VALIDATION,
            "status": TestStatus.PASSED,
            "duration": 2.34,
            "logs": [
                "[12:34:56.123] INFO: Testing input validation against attack vectors...",
                "[12:34:56.150] DEBUG: ✓ Correctly rejected: ../../../etc/passwd",
                "[12:34:56.175] DEBUG: ✓ Correctly rejected: <script>alert('xss')</script>",
                "[12:34:58.456] INFO: ✅ Input validation successfully blocked all attack vectors"
            ],
            "metrics": [
                PerformanceMetric("validation_calls", 25, "count", "Number of validation calls"),
                PerformanceMetric("avg_response_time", 0.045, "ms", "Average validation response time")
            ]
        },
        {
            "name": "test_log_sanitization_comprehensive",
            "category": TestCategory.SECURITY,
            "status": TestStatus.PASSED,
            "duration": 1.87,
            "logs": [
                "[12:34:58.500] INFO: Testing comprehensive log sanitization...",
                "[12:34:58.520] DEBUG: ✓ Sanitized: token=pypi-secret → token=***REDACTED***",
                "[12:34:58.540] DEBUG: ✓ Sanitized: user@example.com → ***REDACTED_EMAIL***",
                "[12:35:00.370] INFO: ✅ Log sanitization working correctly for all patterns"
            ],
            "metrics": [
                PerformanceMetric("sanitization_speed", 1200, "ops/sec", "Sanitization operations per second")
            ]
        },
        {
            "name": "test_path_traversal_protection",
            "category": TestCategory.SECURITY,
            "status": TestStatus.FAILED,
            "duration": 0.95,
            "error": "Path traversal attack not properly blocked: ....//....//....//etc/passwd",
            "logs": [
                "[12:35:00.400] INFO: Testing path traversal protection...",
                "[12:35:00.450] DEBUG: ✓ Correctly rejected: ../../../etc/passwd",
                "[12:35:00.475] DEBUG: ✓ Correctly rejected: /etc/passwd",
                "[12:35:01.350] ERROR: ❌ test_path_traversal_protection FAILED: Path traversal attack not properly blocked"
            ]
        },
        {
            "name": "test_rate_limiting_functionality",
            "category": TestCategory.RATE_LIMITING,
            "status": TestStatus.PASSED,
            "duration": 3.21,
            "logs": [
                "[12:35:01.400] INFO: Testing rate limiting functionality...",
                "[12:35:01.450] INFO: Testing token bucket refill mechanism...",
                "[12:35:02.500] INFO: ✓ Token bucket rate limiting working correctly",
                "[12:35:04.610] INFO: ✅ Rate limiting tests completed successfully"
            ],
            "metrics": [
                PerformanceMetric("token_bucket_capacity", 5, "tokens", "Token bucket capacity"),
                PerformanceMetric("refill_rate", 2.0, "tokens/sec", "Token refill rate"),
                PerformanceMetric("rate_limit_effectiveness", 98.5, "%", "Rate limiting effectiveness", status="ok")
            ]
        },
        {
            "name": "test_malicious_package_names",
            "category": TestCategory.INPUT_VALIDATION,
            "status": TestStatus.PASSED,
            "duration": 0.78,
            "logs": [
                "[12:35:04.650] INFO: Testing advanced malicious package name detection...",
                "[12:35:04.680] DEBUG: ✓ Correctly rejected Unicode attack: 'package\\u0000hidden'",
                "[12:35:04.705] DEBUG: ✓ Correctly accepted: requests",
                "[12:35:05.430] INFO: ✅ Advanced package name validation working correctly"
            ]
        },
        {
            "name": "test_performance_under_load",
            "category": TestCategory.PERFORMANCE,
            "status": TestStatus.PASSED,
            "duration": 5.67,
            "logs": [
                "[12:35:05.470] INFO: Testing performance under load...",
                "[12:35:08.123] INFO: ✓ Log sanitization performance good: 0.456s for 1000 ops",
                "[12:35:10.789] INFO: ✓ Input validation performance good: 1.234s for 1000 ops",
                "[12:35:11.140] INFO: ✅ Performance testing completed"
            ],
            "metrics": [
                PerformanceMetric("log_sanitization_throughput", 2193, "ops/sec", "Log sanitization throughput"),
                PerformanceMetric("input_validation_throughput", 810, "ops/sec", "Input validation throughput"),
                PerformanceMetric("memory_usage_peak", 45.7, "MB", "Peak memory usage during load test"),
                PerformanceMetric("cpu_usage_avg", 23.4, "%", "Average CPU usage during test")
            ]
        },
        {
            "name": "test_concurrent_rate_limiting",
            "category": TestCategory.INTEGRATION,
            "status": TestStatus.ERROR,
            "duration": 2.1,
            "error": "ConnectionError: Failed to establish mock HTTP connection",
            "traceback": """Traceback (most recent call last):
  File "test_security_comprehensive.py", line 489, mock_client.request.side_effect = ConnectionError("Mock connection failed")
  ConnectionError: Failed to establish mock HTTP connection""",
            "logs": [
                "[12:35:11.180] INFO: Testing concurrent rate limiting...",
                "[12:35:12.890] ERROR: Mock HTTP client setup failed",
                "[12:35:13.280] ERROR: ❌ test_concurrent_rate_limiting ERROR: ConnectionError"
            ]
        },
        {
            "name": "test_edge_cases_and_corner_cases",
            "category": TestCategory.EDGE_CASES,
            "status": TestStatus.PASSED,
            "duration": 1.45,
            "logs": [
                "[12:35:13.320] INFO: Testing edge cases and corner cases...",
                "[12:35:13.350] DEBUG: ✓ Sanitization handled None input: 4 chars",
                "[12:35:13.375] DEBUG: ✓ Sanitization handled Unicode emoji: 12 chars",
                "[12:35:14.770] INFO: ✅ Edge case testing completed"
            ]
        }
    ]

    # Create test result objects
    for i, test_case in enumerate(test_cases):
        test = TestResult(
            name=test_case["name"],
            category=test_case["category"],
            status=test_case["status"],
            start_time=results.start_time + i * 3.0,
            duration=test_case["duration"]
        )

        if test.start_time and test.duration:
            test.end_time = test.start_time + test.duration

        # Add logs
        test.output_logs = test_case.get("logs", [])

        # Add error info if failed/error
        if test_case["status"] in [TestStatus.FAILED, TestStatus.ERROR]:
            test.error_message = test_case.get("error", "Unknown error")
            test.error_traceback = test_case.get("traceback")

        # Add performance metrics
        for metric_data in test_case.get("metrics", []):
            test.add_performance_metric(metric_data)

        # Set assertion counts
        test.assertions_total = 15 + i * 3
        test.assertions_passed = test.assertions_total if test.status == TestStatus.PASSED else max(0, test.assertions_total - 2)

        results.add_test(test)

    # Finalize results
    results.finish()

    # Add global performance metrics
    results.global_performance_metrics = [
        PerformanceMetric("total_execution_time", results.duration, "seconds", "Total test suite execution time"),
        PerformanceMetric("tests_per_second", results.total_tests / results.duration, "tests/sec", "Test execution rate"),
        PerformanceMetric("memory_efficiency", 92.3, "%", "Memory efficiency score", status="ok"),
        PerformanceMetric("security_coverage", 87.5, "%", "Security test coverage", status="warning")
    ]

    return results


def generate_sample_reports():
    """Generate sample reports with different themes."""

    # Create sample data
    test_data = create_sample_test_data()

    # Create output directory
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    # Generate reports with different themes
    themes = ["gruvbox-dark", "solarized-dark", "dracula"]
    report_paths = []

    for theme in themes:
        print(f"🎨 Generating sample report with {theme} theme...")

        config = ReportConfig(
            output_dir=output_dir,
            theme=theme,
            include_performance_charts=True,
            include_detailed_logs=True,
            include_environment_info=True,
            company_name="MCPyPI Security Framework",
            report_title=f"Security Test Report - {theme.title()} Theme"
        )

        reporter = SecurityTestReporter(config)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sample_security_report_{theme}_{timestamp}.html"

        report_path = reporter.generate_report(test_data, filename)
        report_paths.append(report_path)

        print(f"✅ Sample report generated: {report_path}")
        print(f"🌐 Open in browser: file://{report_path.resolve()}")

    print(f"\n🎉 Generated {len(report_paths)} sample reports!")
    print("💡 Open these HTML files in your browser to see the beautiful, interactive reports!")

    return report_paths


if __name__ == "__main__":
    generate_sample_reports()
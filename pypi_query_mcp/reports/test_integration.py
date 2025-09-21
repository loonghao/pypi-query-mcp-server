"""Integration layer for SecurityTestSuite with HTML reporting."""

import asyncio
import inspect
import logging
import platform
import sys
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from .html_reporter import SecurityTestReporter, ReportConfig
from .report_data import (
    TestSuiteResults, TestResult, TestStatus, TestCategory,
    PerformanceMetric
)


class SecurityTestRunner:
    """Enhanced test runner with HTML reporting integration."""

    def __init__(self, report_config: Optional[ReportConfig] = None):
        self.report_config = report_config or ReportConfig()
        self.reporter = SecurityTestReporter(self.report_config)
        self.results: Optional[TestSuiteResults] = None
        self.current_test: Optional[TestResult] = None

        # Set up logging capture
        self.log_handler = ReportLogHandler()
        self.logger = logging.getLogger(__name__)

    async def run_enhanced_suite(self, test_suite_instance) -> Path:
        """Run a test suite with enhanced reporting."""
        suite_name = test_suite_instance.__class__.__name__

        # Initialize results
        self.results = TestSuiteResults(
            suite_name=suite_name,
            start_time=time.time(),
            environment_info=self._collect_environment_info(),
            configuration=self._collect_configuration_info()
        )

        # Get all test methods
        test_methods = self._discover_test_methods(test_suite_instance)

        self.logger.info(f"🚀 Starting Enhanced {suite_name} with {len(test_methods)} tests")

        # Run each test with reporting
        for test_method in test_methods:
            await self._run_single_test(test_suite_instance, test_method)

        # Finalize results
        self.results.finish()

        # Generate HTML report
        report_path = self.reporter.generate_report(self.results)

        self.logger.info(f"📊 HTML report generated: {report_path}")
        return report_path

    async def _run_single_test(self, test_instance, test_method: Callable):
        """Run a single test with detailed tracking."""
        test_name = test_method.__name__
        category = self._categorize_test(test_name)

        # Create test result
        test_result = TestResult(
            name=test_name,
            category=category
        )

        self.current_test = test_result
        self.results.add_test(test_result)

        # Start logging capture
        self.log_handler.start_capture()

        test_result.start()
        test_result.add_log(f"Starting test: {test_name}")

        try:
            # Performance monitoring
            start_memory = self._get_memory_usage()
            start_time = time.time()

            # Run the test
            if inspect.iscoroutinefunction(test_method):
                await test_method()
            else:
                test_method()

            # Record performance metrics
            end_time = time.time()
            end_memory = self._get_memory_usage()

            test_result.add_performance_metric(PerformanceMetric(
                name="execution_time",
                value=end_time - start_time,
                unit="seconds",
                description="Test execution time"
            ))

            if start_memory and end_memory:
                memory_delta = end_memory - start_memory
                test_result.add_performance_metric(PerformanceMetric(
                    name="memory_delta",
                    value=memory_delta,
                    unit="MB",
                    description="Memory usage change during test",
                    status="warning" if memory_delta > 10 else "ok"
                ))

            test_result.finish_success()
            test_result.add_log(f"Test completed successfully")

        except AssertionError as e:
            test_result.finish_failure(
                error_message=str(e),
                traceback=traceback.format_exc()
            )
            test_result.add_log(f"Test failed: {str(e)}")

        except Exception as e:
            test_result.finish_error(
                error_message=str(e),
                traceback=traceback.format_exc()
            )
            test_result.add_log(f"Test error: {str(e)}")

        finally:
            # Capture logs
            captured_logs = self.log_handler.stop_capture()
            test_result.output_logs.extend(captured_logs)

            self.current_test = None

    def _discover_test_methods(self, test_instance) -> List[Callable]:
        """Discover test methods in the test instance."""
        test_methods = []

        for attr_name in dir(test_instance):
            if attr_name.startswith('test_'):
                attr = getattr(test_instance, attr_name)
                if callable(attr):
                    test_methods.append(attr)

        return test_methods

    def _categorize_test(self, test_name: str) -> TestCategory:
        """Categorize test based on its name."""
        name_lower = test_name.lower()

        if 'input' in name_lower or 'validation' in name_lower:
            return TestCategory.INPUT_VALIDATION
        elif 'rate' in name_lower or 'limit' in name_lower:
            return TestCategory.RATE_LIMITING
        elif 'performance' in name_lower or 'load' in name_lower:
            return TestCategory.PERFORMANCE
        elif 'concurrent' in name_lower or 'integration' in name_lower:
            return TestCategory.INTEGRATION
        elif 'edge' in name_lower or 'corner' in name_lower:
            return TestCategory.EDGE_CASES
        else:
            return TestCategory.SECURITY

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information."""
        return {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor() or platform.machine(),
            "hostname": platform.node(),
            "working_directory": str(Path.cwd()),
            "script_path": str(Path(__file__).parent)
        }

    def _collect_configuration_info(self) -> Dict[str, Any]:
        """Collect configuration information."""
        return {
            "report_theme": self.report_config.theme,
            "output_directory": str(self.report_config.output_dir),
            "auto_refresh": self.report_config.auto_refresh,
            "include_performance_charts": self.report_config.include_performance_charts,
            "include_detailed_logs": self.report_config.include_detailed_logs
        }

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None

    @asynccontextmanager
    async def live_reporting(self, update_interval: float = 2.0):
        """Context manager for live report updates during test execution."""
        if not self.report_config.auto_refresh:
            yield
            return

        update_task = None
        try:
            async def update_report():
                while True:
                    if self.results:
                        # Generate intermediate report
                        temp_results = TestSuiteResults(
                            suite_name=f"{self.results.suite_name} (Live)",
                            start_time=self.results.start_time,
                            tests=self.results.tests.copy()
                        )

                        # Mark running test
                        if self.current_test and self.current_test.status == TestStatus.RUNNING:
                            temp_results.tests[-1] = self.current_test

                        self.reporter.generate_report(temp_results, "live_report.html")

                    await asyncio.sleep(update_interval)

            update_task = asyncio.create_task(update_report())
            yield

        finally:
            if update_task:
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass


class ReportLogHandler(logging.Handler):
    """Custom log handler for capturing test logs."""

    def __init__(self):
        super().__init__()
        self.captured_logs = []
        self.capturing = False

    def start_capture(self):
        """Start capturing logs."""
        self.captured_logs = []
        self.capturing = True
        logging.getLogger().addHandler(self)

    def stop_capture(self) -> List[str]:
        """Stop capturing logs and return captured messages."""
        self.capturing = False
        logging.getLogger().removeHandler(self)
        return self.captured_logs.copy()

    def emit(self, record):
        """Emit a log record."""
        if not self.capturing:
            return

        try:
            msg = self.format(record)
            timestamp = time.strftime("%H:%M:%S", time.localtime(record.created))
            self.captured_logs.append(f"[{timestamp}] {record.levelname}: {msg}")
        except Exception:
            pass  # Ignore logging errors


# Convenience functions for easy integration
async def run_security_tests_with_reporting(
    test_suite_class,
    report_config: Optional[ReportConfig] = None,
    output_file: Optional[str] = None
) -> Path:
    """Convenience function to run security tests with HTML reporting."""

    # Create test runner
    runner = SecurityTestRunner(report_config)

    # Create test suite instance
    test_suite = test_suite_class()

    # Run tests with live reporting if enabled
    if runner.report_config.auto_refresh:
        async with runner.live_reporting():
            return await runner.run_enhanced_suite(test_suite)
    else:
        return await runner.run_enhanced_suite(test_suite)


def create_demo_report_config(theme: str = "gruvbox-dark") -> ReportConfig:
    """Create a demonstration report configuration."""
    return ReportConfig(
        output_dir=Path("reports"),
        theme=theme,
        include_performance_charts=True,
        include_detailed_logs=True,
        include_environment_info=True,
        auto_refresh=False,
        company_name="MCPyPI Security Framework",
        report_title="Comprehensive Security Test Report"
    )
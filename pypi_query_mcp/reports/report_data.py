"""Data models for test reporting."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class TestCategory(Enum):
    """Test categories for organization."""
    INPUT_VALIDATION = "input_validation"
    SECURITY = "security"
    RATE_LIMITING = "rate_limiting"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    EDGE_CASES = "edge_cases"


@dataclass
class PerformanceMetric:
    """Performance measurement data."""
    name: str
    value: float
    unit: str
    description: str = ""
    threshold: Optional[float] = None
    status: str = "ok"  # ok, warning, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "threshold": self.threshold,
            "status": self.status
        }


@dataclass
class TestResult:
    """Individual test result data."""
    name: str
    category: TestCategory
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    output_logs: List[str] = field(default_factory=list)
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    assertions_passed: int = 0
    assertions_total: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self):
        """Mark test as started."""
        self.status = TestStatus.RUNNING
        self.start_time = time.time()

    def finish_success(self):
        """Mark test as successfully completed."""
        self.status = TestStatus.PASSED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time

    def finish_failure(self, error_message: str, traceback: Optional[str] = None):
        """Mark test as failed."""
        self.status = TestStatus.FAILED
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error_message = error_message
        self.error_traceback = traceback

    def finish_error(self, error_message: str, traceback: Optional[str] = None):
        """Mark test as errored."""
        self.status = TestStatus.ERROR
        self.end_time = time.time()
        if self.start_time:
            self.duration = self.end_time - self.start_time
        self.error_message = error_message
        self.error_traceback = traceback

    def add_log(self, message: str):
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.output_logs.append(f"[{timestamp}] {message}")

    def add_performance_metric(self, metric: PerformanceMetric):
        """Add a performance metric."""
        self.performance_metrics.append(metric)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "output_logs": self.output_logs,
            "performance_metrics": [m.to_dict() for m in self.performance_metrics],
            "assertions_passed": self.assertions_passed,
            "assertions_total": self.assertions_total,
            "metadata": self.metadata
        }


@dataclass
class TestSuiteResults:
    """Complete test suite results."""
    suite_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tests: List[TestResult] = field(default_factory=list)
    global_performance_metrics: List[PerformanceMetric] = field(default_factory=list)
    environment_info: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)

    def add_test(self, test: TestResult):
        """Add a test result."""
        self.tests.append(test)

    def finish(self):
        """Mark suite as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    @property
    def total_tests(self) -> int:
        return len(self.tests)

    @property
    def passed_tests(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.PASSED])

    @property
    def failed_tests(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.FAILED])

    @property
    def error_tests(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.ERROR])

    @property
    def skipped_tests(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.SKIPPED])

    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

    def get_tests_by_category(self, category: TestCategory) -> List[TestResult]:
        """Get tests filtered by category."""
        return [t for t in self.tests if t.category == category]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "suite_name": self.suite_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tests": [t.to_dict() for t in self.tests],
            "global_performance_metrics": [m.to_dict() for m in self.global_performance_metrics],
            "environment_info": self.environment_info,
            "configuration": self.configuration,
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "error_tests": self.error_tests,
                "skipped_tests": self.skipped_tests,
                "success_rate": self.success_rate
            }
        }
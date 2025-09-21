# HTML Test Report Framework - Usage Examples

This document provides practical examples for integrating the HTML test report framework into your security testing workflow.

## 🚀 Quick Start Examples

### Example 1: Basic Integration

```python
#!/usr/bin/env python3
"""Basic example of integrating HTML reporting with existing tests."""

import asyncio
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting
from test_security_comprehensive import SecurityTestSuite

async def main():
    # Run existing test suite with beautiful HTML reports
    report_path = await run_security_tests_with_reporting(SecurityTestSuite)
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Custom Configuration

```python
#!/usr/bin/env python3
"""Example with custom report configuration."""

import asyncio
from pathlib import Path
from pypi_query_mcp.reports import ReportConfig
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting
from test_security_comprehensive import SecurityTestSuite

async def main():
    # Custom configuration
    config = ReportConfig(
        output_dir=Path("security_reports"),
        theme="dracula",
        include_performance_charts=True,
        include_detailed_logs=True,
        company_name="Your Security Team",
        report_title="Daily Security Test Report"
    )

    # Generate timestamped filename
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"daily_security_report_{timestamp}.html"

    # Run tests with custom config
    report_path = await run_security_tests_with_reporting(
        SecurityTestSuite,
        report_config=config,
        output_file=filename
    )

    print(f"Daily report generated: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 3: CI/CD Integration

```python
#!/usr/bin/env python3
"""Example for CI/CD pipeline integration."""

import asyncio
import os
import sys
from pathlib import Path
from pypi_query_mcp.reports import ReportConfig
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting
from test_security_comprehensive import SecurityTestSuite

async def run_ci_security_tests():
    """Run security tests optimized for CI/CD pipeline."""

    # Get CI environment variables
    ci_build_number = os.getenv("BUILD_NUMBER", "local")
    ci_branch = os.getenv("BRANCH_NAME", "main")
    ci_commit = os.getenv("COMMIT_SHA", "unknown")[:8]

    # Configure report for CI
    config = ReportConfig(
        output_dir=Path("ci_reports"),
        theme="gruvbox-dark",
        include_performance_charts=True,
        include_detailed_logs=True,
        include_environment_info=True,
        company_name="CI Security Pipeline",
        report_title=f"Security Tests - Build #{ci_build_number}"
    )

    try:
        # Run tests
        report_path = await run_security_tests_with_reporting(
            SecurityTestSuite,
            report_config=config,
            output_file=f"security_report_build_{ci_build_number}_{ci_commit}.html"
        )

        # Success - output for CI
        print(f"✅ Security tests passed!")
        print(f"📊 Report: {report_path}")
        print(f"🌐 Artifact URL: {report_path.resolve()}")

        # Set CI environment variables for artifact upload
        print(f"::set-output name=report_path::{report_path}")
        print(f"::set-output name=test_status::passed")

        return 0

    except Exception as e:
        print(f"❌ Security tests failed: {e}")
        print(f"::set-output name=test_status::failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_ci_security_tests())
    sys.exit(exit_code)
```

### Example 4: GitHub Actions Workflow

```yaml
# .github/workflows/security-tests.yml
name: Security Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  security-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.12
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run security tests with HTML reporting
      id: security_tests
      run: |
        python ci_security_tests.py
        echo "REPORT_PATH=$(ls ci_reports/*.html | head -1)" >> $GITHUB_OUTPUT

    - name: Upload security test report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-test-report
        path: ci_reports/*.html
        retention-days: 30

    - name: Comment PR with report link
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request' && always()
      with:
        script: |
          const reportUrl = `https://github.com/${{github.repository}}/actions/runs/${{github.run_id}}/artifacts`;
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `📊 Security test report generated! View the [HTML report](${reportUrl}) for detailed results.`
          });
```

### Example 5: Custom Test Suite with Enhanced Reporting

```python
#!/usr/bin/env python3
"""Example of creating a custom test suite with enhanced reporting."""

import asyncio
import time
from pypi_query_mcp.reports.test_integration import SecurityTestRunner
from pypi_query_mcp.reports import ReportConfig
from pypi_query_mcp.reports.report_data import TestCategory, PerformanceMetric

class MyCustomSecurityTests:
    """Custom security test suite with enhanced reporting."""

    def __init__(self):
        self.assertion_count = 0

    def assert_secure(self, condition: bool, message: str = ""):
        """Enhanced assertion for security tests."""
        self.assertion_count += 1
        if not condition:
            raise AssertionError(message or f"Security assertion {self.assertion_count} failed")

    async def test_api_security(self):
        """Test API security measures."""
        print("Testing API security...")

        # Simulate API security testing
        await asyncio.sleep(0.1)  # Simulate test work

        # Example assertions
        self.assert_secure(True, "API authentication working")
        self.assert_secure(True, "Rate limiting enabled")
        self.assert_secure(True, "Input validation active")

        print("✅ API security tests passed")

    async def test_data_encryption(self):
        """Test data encryption mechanisms."""
        print("Testing data encryption...")

        start_time = time.time()
        await asyncio.sleep(0.2)  # Simulate encryption testing
        duration = time.time() - start_time

        # Add custom performance metric
        metric = PerformanceMetric(
            name="encryption_speed",
            value=1000 / duration,  # operations per second
            unit="ops/sec",
            description="Encryption operations per second"
        )

        self.assert_secure(True, "Data encrypted at rest")
        self.assert_secure(True, "Data encrypted in transit")

        print("✅ Data encryption tests passed")

    async def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities."""
        print("Testing authentication bypass...")

        await asyncio.sleep(0.05)  # Simulate testing

        # Simulate a failure for demonstration
        self.assert_secure(False, "Authentication bypass detected in admin panel")

async def run_custom_tests():
    """Run custom tests with beautiful HTML reporting."""

    # Configure reporting
    config = ReportConfig(
        theme="solarized-dark",
        include_performance_charts=True,
        company_name="My Security Team",
        report_title="Custom Security Assessment"
    )

    # Create test runner
    runner = SecurityTestRunner(config)

    # Run custom test suite
    try:
        report_path = await runner.run_enhanced_suite(MyCustomSecurityTests())
        print(f"📊 Custom test report: {report_path}")
        return report_path
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_custom_tests())
```

### Example 6: Integration with pytest

```python
#!/usr/bin/env python3
"""Example of integrating with pytest framework."""

import pytest
import asyncio
from pathlib import Path
from pypi_query_mcp.reports import SecurityTestReporter, ReportConfig
from pypi_query_mcp.reports.report_data import TestSuiteResults, TestResult, TestStatus, TestCategory

class PytestSecurityReporter:
    """Pytest plugin for security test HTML reporting."""

    def __init__(self):
        self.results = TestSuiteResults(
            suite_name="Pytest Security Tests",
            start_time=time.time()
        )
        self.current_test = None

    @pytest.fixture(autouse=True)
    def setup_test_reporting(self, request):
        """Setup test reporting for each test."""
        test_name = request.node.name
        category = self._categorize_test(test_name)

        self.current_test = TestResult(name=test_name, category=category)
        self.current_test.start()

        yield

        # Finalize test result
        if hasattr(request.node, 'rep_call'):
            if request.node.rep_call.passed:
                self.current_test.finish_success()
            else:
                self.current_test.finish_failure(str(request.node.rep_call.longrepr))

        self.results.add_test(self.current_test)

    def _categorize_test(self, test_name: str) -> TestCategory:
        """Categorize test based on name."""
        if 'input' in test_name or 'validation' in test_name:
            return TestCategory.INPUT_VALIDATION
        elif 'auth' in test_name or 'security' in test_name:
            return TestCategory.SECURITY
        elif 'rate' in test_name or 'limit' in test_name:
            return TestCategory.RATE_LIMITING
        else:
            return TestCategory.SECURITY

    def generate_report(self) -> Path:
        """Generate final HTML report."""
        self.results.finish()

        config = ReportConfig(
            theme="gruvbox-dark",
            report_title="Pytest Security Test Report"
        )

        reporter = SecurityTestReporter(config)
        return reporter.generate_report(self.results, "pytest_security_report.html")

# Global reporter instance
security_reporter = PytestSecurityReporter()

def pytest_runtest_makereport(item, call):
    """Hook to capture test results."""
    if call.when == "call":
        item.rep_call = call

def pytest_sessionfinish(session, exitstatus):
    """Generate HTML report at end of session."""
    report_path = security_reporter.generate_report()
    print(f"\n📊 Security test report generated: {report_path}")

# Example security tests
def test_input_validation():
    """Test input validation security."""
    # Your test code here
    assert True

def test_authentication_security():
    """Test authentication mechanisms."""
    # Your test code here
    assert True

def test_rate_limiting_security():
    """Test rate limiting protection."""
    # Your test code here
    assert True
```

### Example 7: Docker Integration

```dockerfile
# Dockerfile for running security tests with HTML reporting
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create reports directory
RUN mkdir -p /app/reports

# Run security tests and generate HTML report
CMD ["python", "docker_security_tests.py"]
```

```python
# docker_security_tests.py
#!/usr/bin/env python3
"""Docker-optimized security test runner."""

import asyncio
import os
from pathlib import Path
from pypi_query_mcp.reports import ReportConfig
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting
from test_security_comprehensive import SecurityTestSuite

async def run_docker_tests():
    """Run security tests optimized for Docker environment."""

    # Docker-specific configuration
    config = ReportConfig(
        output_dir=Path("/app/reports"),
        theme="gruvbox-dark",
        include_performance_charts=True,
        include_environment_info=True,
        company_name="Docker Security Pipeline",
        report_title="Containerized Security Tests"
    )

    # Get container info
    container_id = os.getenv("HOSTNAME", "unknown")[:12]

    # Run tests
    report_path = await run_security_tests_with_reporting(
        SecurityTestSuite,
        report_config=config,
        output_file=f"docker_security_report_{container_id}.html"
    )

    print(f"🐳 Docker security test completed")
    print(f"📊 Report: {report_path}")
    print(f"💡 Mount /app/reports to access the HTML report")

if __name__ == "__main__":
    asyncio.run(run_docker_tests())
```

## 🔧 Advanced Customization Examples

### Custom Theme Creation

```python
# custom_theme_example.py
"""Example of creating a custom theme."""

from pypi_query_mcp.reports import SecurityTestReporter

class CustomThemeReporter(SecurityTestReporter):
    """Reporter with custom theme."""

    def _generate_css(self) -> str:
        """Generate CSS with custom theme."""
        base_css = super()._generate_css()

        custom_theme = """
        /* Custom Dark Blue Theme */
        .theme-custom-blue {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #f0f6fc;
            --text-secondary: #c9d1d9;
            --text-muted: #7d8590;
            --accent-success: #2ea043;
            --accent-error: #da3633;
            --accent-warning: #fb8500;
            --accent-info: #1f6feb;
            --accent-primary: #8b5cf6;
        }
        """

        return base_css + custom_theme
```

### Live Reporting Example

```python
# live_reporting_example.py
"""Example of live test reporting."""

import asyncio
from pypi_query_mcp.reports.test_integration import SecurityTestRunner
from pypi_query_mcp.reports import ReportConfig

async def run_live_tests():
    """Run tests with live report updates."""

    config = ReportConfig(
        auto_refresh=True,
        refresh_interval=2,  # Update every 2 seconds
        theme="gruvbox-dark"
    )

    runner = SecurityTestRunner(config)

    # Use live reporting context manager
    async with runner.live_reporting(update_interval=1.0):
        report_path = await runner.run_enhanced_suite(YourTestSuite())

    print(f"Live reporting completed: {report_path}")

if __name__ == "__main__":
    asyncio.run(run_live_tests())
```

### Performance Monitoring Example

```python
# performance_monitoring_example.py
"""Example with detailed performance monitoring."""

from pypi_query_mcp.reports.report_data import PerformanceMetric
from pypi_query_mcp.reports.test_integration import SecurityTestRunner

class PerformanceMonitoredTests:
    """Test suite with detailed performance monitoring."""

    async def test_with_performance_metrics(self):
        """Example test with performance monitoring."""
        import time
        import psutil

        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Your test code here
        await asyncio.sleep(0.1)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # Add custom metrics (this would be done by the framework automatically)
        duration = end_time - start_time
        memory_delta = end_memory - start_memory

        print(f"Test completed in {duration:.3f}s with {memory_delta:.2f}MB memory change")
```

## 📋 Best Practices

### 1. Naming Conventions
- Use descriptive test method names starting with `test_`
- Include the security domain in the name (e.g., `test_input_validation_xss`)
- Use consistent naming patterns for easy categorization

### 2. Error Handling
- Provide clear, actionable error messages
- Include context about what was being tested
- Use structured logging for better report integration

### 3. Performance Considerations
- Add performance thresholds for critical tests
- Monitor memory usage during load tests
- Use async/await for I/O-bound operations

### 4. CI/CD Integration
- Generate timestamped report filenames
- Set appropriate artifact retention policies
- Include report links in PR comments
- Fail builds on security test failures

### 5. Report Organization
- Use meaningful report titles and company names
- Include environment information for debugging
- Export JSON data for further analysis
- Organize reports by date/build for easy tracking

---

**For more examples and advanced usage, see the complete documentation in the `pypi_query_mcp/reports/` directory.**
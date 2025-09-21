# MCPyPI HTML Test Report Framework

A comprehensive, beautiful HTML test report generation framework designed specifically for security testing suites. This framework creates stunning, interactive reports with terminal-inspired aesthetics and modern web technologies.

## 🌟 Features

### Visual Excellence
- **Terminal-Inspired Themes**: Gruvbox Dark, Solarized Dark, Dracula
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Interactive Components**: Collapsible sections, live filtering, modal dialogs
- **Professional Styling**: Clean, modern design with accessibility features

### Technical Capabilities
- **Zero Dependencies**: Self-contained HTML files with embedded CSS/JS
- **Universal Compatibility**: Works with `file://` and `https://` protocols
- **Real-time Updates**: Optional live reporting during test execution
- **Performance Monitoring**: Detailed metrics and performance charts
- **Export Functions**: JSON export, print-friendly layouts

### Security Focus
- **Comprehensive Logging**: Captured test logs with syntax highlighting
- **Error Tracking**: Detailed error messages and stack traces
- **Performance Metrics**: Load testing results and bottleneck identification
- **Test Categorization**: Organized by security domains

## 🚀 Quick Start

### Basic Usage

```python
import asyncio
from pypi_query_mcp.reports import SecurityTestReporter, ReportConfig
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting

# Run your existing test suite with beautiful HTML reports
async def main():
    report_path = await run_security_tests_with_reporting(
        YourTestSuiteClass,
        report_config=ReportConfig(theme="gruvbox-dark")
    )
    print(f"Report generated: {report_path}")

asyncio.run(main())
```

### Advanced Configuration

```python
from pathlib import Path
from pypi_query_mcp.reports import ReportConfig

config = ReportConfig(
    output_dir=Path("custom_reports"),
    theme="solarized-dark",
    include_performance_charts=True,
    include_detailed_logs=True,
    auto_refresh=True,
    refresh_interval=5,
    company_name="Your Company",
    report_title="Custom Security Report"
)
```

## 🎨 Available Themes

### Gruvbox Dark (Default)
```python
ReportConfig(theme="gruvbox-dark")
```
- Warm, retro terminal colors
- High contrast for readability
- Perfect for dark mode lovers

### Solarized Dark
```python
ReportConfig(theme="solarized-dark")
```
- Precision colors designed for long-term viewing
- Scientifically crafted color palette
- Easy on the eyes

### Dracula
```python
ReportConfig(theme="dracula")
```
- Popular dark theme with vibrant accents
- Purple and pink highlights
- Modern and stylish

## 📊 Report Structure

### Dashboard Overview
- **Test Statistics**: Pass/fail counts, success rates
- **Performance Metrics**: Execution times, memory usage
- **Visual Progress Bars**: Color-coded status indicators
- **Environment Information**: System and configuration details

### Test Categories
- **Input Validation**: XSS, injection, sanitization tests
- **Security**: Authentication, authorization, encryption tests
- **Rate Limiting**: Throttling, burst capacity, concurrent tests
- **Performance**: Load testing, benchmarking, optimization
- **Integration**: End-to-end, API integration tests
- **Edge Cases**: Boundary conditions, error handling

### Detailed Results
- **Interactive Test Cards**: Expandable sections for each test
- **Real-time Filtering**: Search by name, filter by status
- **Comprehensive Logs**: Timestamped execution logs
- **Error Analysis**: Stack traces and debugging information
- **Performance Data**: Execution metrics and charts

## 🔧 Integration with Existing Tests

### Method 1: Extend Your Test Class

```python
from pypi_query_mcp.reports.test_integration import SecurityTestRunner

class YourTestSuite:
    async def test_security_feature(self):
        # Your existing test code
        pass

# Run with reporting
runner = SecurityTestRunner()
report_path = await runner.run_enhanced_suite(YourTestSuite())
```

### Method 2: Use the Enhanced Base Class

```python
from test_security_with_html_reporting import EnhancedSecurityTestSuite

class YourTestSuite(EnhancedSecurityTestSuite):
    async def test_your_feature(self):
        # Use enhanced assertion methods
        self.assert_true(condition, "Custom error message")
        self.assert_raises(SecurityError, dangerous_function)
```

### Method 3: Direct Integration

```python
from pypi_query_mcp.reports import SecurityTestReporter
from pypi_query_mcp.reports.report_data import TestSuiteResults, TestResult

# Create results manually
results = TestSuiteResults(suite_name="Your Tests", start_time=time.time())

# Add test results
test = TestResult(name="test_example", category=TestCategory.SECURITY)
test.start()
# ... run your test ...
test.finish_success()
results.add_test(test)

# Generate report
reporter = SecurityTestReporter()
report_path = reporter.generate_report(results)
```

## 🎯 Interactive Features

### Keyboard Shortcuts
- **Ctrl+E**: Export test results as JSON
- **Ctrl+R**: Toggle auto-refresh (in server mode)
- **Ctrl+F**: Focus search filter
- **Escape**: Clear filters

### Mouse Interactions
- **Double-click code blocks**: Copy to clipboard
- **Click category headers**: Expand/collapse sections
- **Hover test cards**: Highlight and preview
- **Click test details**: View comprehensive information

### Live Features
- **Auto-refresh**: Real-time updates during test execution
- **Progress tracking**: Live status updates
- **Performance monitoring**: Real-time metrics
- **Log streaming**: Live log capture and display

## 📈 Performance Metrics

The framework automatically collects:

### Execution Metrics
- Test duration (individual and total)
- Memory usage (peak and average)
- CPU utilization during tests
- I/O operations and network calls

### Quality Metrics
- Assertion pass/fail ratios
- Error rates and types
- Security coverage percentages
- Performance thresholds

### Custom Metrics
```python
from pypi_query_mcp.reports.report_data import PerformanceMetric

# Add custom performance metric
metric = PerformanceMetric(
    name="api_response_time",
    value=0.125,
    unit="seconds",
    description="Average API response time",
    threshold=0.200,
    status="ok"  # ok, warning, error
)

test_result.add_performance_metric(metric)
```

## 🌐 Browser Compatibility

### Supported Browsers
- **Chrome/Chromium**: Full feature support
- **Firefox**: Full feature support
- **Safari**: Full feature support
- **Edge**: Full feature support

### File Protocol Support
The reports work perfectly when opened directly as files (`file://`) without requiring a web server:

- ✅ All interactive features work
- ✅ JavaScript functionality preserved
- ✅ CSS styling fully applied
- ✅ Export and copy features available
- ⚠️ Auto-refresh disabled (requires server)

### Mobile Support
- **Responsive Design**: Adapts to all screen sizes
- **Touch Interactions**: Optimized for touch devices
- **Performance**: Lightweight and fast loading
- **Accessibility**: Screen reader compatible

## 🎨 Customization

### Custom Themes

Create your own theme by defining CSS custom properties:

```css
.theme-custom {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --text-primary: #ffffff;
    --accent-success: #00ff00;
    --accent-error: #ff0000;
    /* ... more variables ... */
}
```

### Custom Components

Extend the reporter with custom sections:

```python
class CustomReporter(SecurityTestReporter):
    def _generate_custom_section(self) -> str:
        return '''<div class="card">
            <div class="card-header">Custom Analysis</div>
            <div class="card-body">
                <!-- Your custom content -->
            </div>
        </div>'''

    def _generate_html(self) -> str:
        html = super()._generate_html()
        # Insert custom section
        return html.replace(
            '</div>\n</body>',
            f'{self._generate_custom_section()}</div>\n</body>'
        )
```

## 🛠️ Development

### Running Tests

```bash
# Generate sample reports
python generate_sample_report.py

# Run enhanced security tests
python test_security_with_html_reporting.py

# Run original tests with new reporting
python -c "
import asyncio
from test_security_comprehensive import SecurityTestSuite
from pypi_query_mcp.reports.test_integration import run_security_tests_with_reporting

asyncio.run(run_security_tests_with_reporting(SecurityTestSuite))
"
```

### File Structure

```
pypi_query_mcp/reports/
├── __init__.py              # Package exports
├── html_reporter.py         # Main HTML generator
├── report_data.py          # Data models and structures
├── test_integration.py     # Test runner integration
└── README.md               # This documentation
```

### Dependencies

The reporting framework has minimal dependencies:
- **Python 3.8+**: Core runtime
- **asyncio**: For async test execution
- **json**: For data serialization (built-in)
- **pathlib**: For file operations (built-in)
- **typing**: For type hints (built-in)

Optional dependencies:
- **psutil**: For memory monitoring
- **logging**: For enhanced log capture (built-in)

## 🔒 Security Considerations

### Safe HTML Generation
- All user input is properly escaped
- No eval() or dangerous JavaScript functions
- Content Security Policy compatible
- XSS protection built-in

### Data Privacy
- No external requests or analytics
- All data stays local
- No cookies or tracking
- Complete offline functionality

### File Safety
- No file system access from browser
- Safe file:// protocol handling
- No server requirements for basic features
- Isolated execution environment

## 📚 Examples

### Complete Integration Example

See `test_security_with_html_reporting.py` for a complete example of integrating the reporting framework with an existing security test suite.

### Sample Report Generation

Run `generate_sample_report.py` to see example reports with different themes and sample data.

### Custom Test Runner

```python
import asyncio
from pypi_query_mcp.reports.test_integration import SecurityTestRunner, ReportConfig

async def run_custom_tests():
    # Configure reporting
    config = ReportConfig(
        theme="gruvbox-dark",
        include_performance_charts=True,
        company_name="Your Security Team"
    )

    # Create runner
    runner = SecurityTestRunner(config)

    # Run your test suite
    report_path = await runner.run_enhanced_suite(YourTestSuite())

    print(f"🎉 Report generated: {report_path}")
    print(f"🌐 Open: file://{report_path.resolve()}")

if __name__ == "__main__":
    asyncio.run(run_custom_tests())
```

## 🎯 Best Practices

### Test Organization
- Use descriptive test method names starting with `test_`
- Group related tests into categories
- Include comprehensive assertions and logging
- Add performance metrics for critical paths

### Report Generation
- Generate reports after test completion
- Use meaningful report titles and filenames
- Include environment information for debugging
- Export JSON for CI/CD integration

### Performance Optimization
- Enable performance monitoring for slow tests
- Set reasonable thresholds for metrics
- Monitor memory usage during load tests
- Use async/await for I/O-bound operations

### Accessibility
- Test reports with screen readers
- Ensure keyboard navigation works
- Use high contrast themes when needed
- Include descriptive text for charts

---

**Created by the MCPyPI Security Framework Team**
**For questions and support, see the main project documentation**
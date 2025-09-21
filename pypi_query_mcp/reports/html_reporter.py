"""Beautiful HTML test report generator with modern design and interactivity."""

import html
import json
import os
import sys
import platform
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .report_data import TestSuiteResults, TestResult, TestStatus, TestCategory, PerformanceMetric


@dataclass
class ReportConfig:
    """Configuration for HTML report generation."""
    output_dir: Path = Path("reports")
    theme: str = "gruvbox-dark"  # gruvbox-dark, gruvbox-light, solarized-dark, dracula
    include_performance_charts: bool = True
    include_detailed_logs: bool = True
    include_environment_info: bool = True
    auto_refresh: bool = False
    refresh_interval: int = 5  # seconds
    company_name: str = "MCPyPI Security Suite"
    report_title: str = "Security Test Report"


class SecurityTestReporter:
    """Advanced HTML test report generator with beautiful styling and interactivity."""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.results: Optional[TestSuiteResults] = None

    def generate_report(self, results: TestSuiteResults, filename: Optional[str] = None) -> Path:
        """Generate a comprehensive HTML report."""
        self.results = results

        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_test_report_{timestamp}.html"

        output_path = self.config.output_dir / filename

        # Generate complete HTML
        html_content = self._generate_html()

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _generate_html(self) -> str:
        """Generate the complete HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{self.config.report_title}">
    <title>{self.config.report_title} - {self.results.suite_name}</title>

    {self._generate_css()}
</head>
<body class="theme-{self.config.theme}">
    <div class="terminal-window">
        {self._generate_header()}

        <div class="terminal-body">
            {self._generate_status_line()}
            {self._generate_summary_dashboard()}
            {self._generate_test_categories()}
            {self._generate_detailed_results()}
            {self._generate_performance_section()}
            {self._generate_environment_section()}
        </div>
    </div>

    <script type="application/json" id="test-data">
    {json.dumps(self.results.to_dict(), indent=2, default=str)}
    </script>

    {self._generate_javascript()}
</body>
</html>"""

    def _generate_css(self) -> str:
        """Generate embedded CSS with beautiful terminal-inspired styling."""
        return f"""<style>
/* CSS Reset and Base Styles */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

/* Theme Variables - Gruvbox Dark */
:root {{
    --gruvbox-dark0: #282828;
    --gruvbox-dark1: #3c3836;
    --gruvbox-dark2: #504945;
    --gruvbox-dark3: #665c54;
    --gruvbox-light0: #ebdbb2;
    --gruvbox-light1: #d5c4a1;
    --gruvbox-light2: #bdae93;
    --gruvbox-light4: #928374;
    --gruvbox-red: #fb4934;
    --gruvbox-green: #b8bb26;
    --gruvbox-yellow: #fabd2f;
    --gruvbox-blue: #83a598;
    --gruvbox-purple: #d3869b;
    --gruvbox-aqua: #8ec07c;
    --gruvbox-orange: #fe8019;
    --gruvbox-red-dim: #cc241d;
    --gruvbox-green-dim: #98971a;
    --gruvbox-yellow-dim: #d79921;
    --gruvbox-blue-dim: #458588;
    --gruvbox-purple-dim: #b16286;
    --gruvbox-aqua-dim: #689d6a;
    --gruvbox-orange-dim: #d65d0e;
}}

/* Theme Application */
.theme-gruvbox-dark {{
    --bg-primary: var(--gruvbox-dark0);
    --bg-secondary: var(--gruvbox-dark1);
    --bg-tertiary: var(--gruvbox-dark2);
    --bg-quaternary: var(--gruvbox-dark3);
    --text-primary: var(--gruvbox-light0);
    --text-secondary: var(--gruvbox-light1);
    --text-muted: var(--gruvbox-light4);
    --border-color: var(--gruvbox-dark3);
    --accent-success: var(--gruvbox-green);
    --accent-warning: var(--gruvbox-yellow);
    --accent-error: var(--gruvbox-red);
    --accent-info: var(--gruvbox-blue);
    --accent-primary: var(--gruvbox-orange);
    --accent-secondary: var(--gruvbox-purple);
    --accent-tertiary: var(--gruvbox-aqua);
}}

/* Solarized Dark Theme */
.theme-solarized-dark {{
    --bg-primary: #002b36;
    --bg-secondary: #073642;
    --bg-tertiary: #586e75;
    --bg-quaternary: #657b83;
    --text-primary: #839496;
    --text-secondary: #93a1a1;
    --text-muted: #586e75;
    --border-color: #073642;
    --accent-success: #859900;
    --accent-warning: #b58900;
    --accent-error: #dc322f;
    --accent-info: #268bd2;
    --accent-primary: #cb4b16;
    --accent-secondary: #d33682;
    --accent-tertiary: #2aa198;
}}

/* Dracula Theme */
.theme-dracula {{
    --bg-primary: #282a36;
    --bg-secondary: #44475a;
    --bg-tertiary: #6272a4;
    --bg-quaternary: #8be9fd;
    --text-primary: #f8f8f2;
    --text-secondary: #6272a4;
    --text-muted: #6272a4;
    --border-color: #44475a;
    --accent-success: #50fa7b;
    --accent-warning: #f1fa8c;
    --accent-error: #ff5555;
    --accent-info: #8be9fd;
    --accent-primary: #bd93f9;
    --accent-secondary: #ff79c6;
    --accent-tertiary: #ffb86c;
}}

/* Base Styles */
body {{
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', 'Source Code Pro', monospace;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    font-size: 14px;
    overflow-x: auto;
}}

/* Terminal Window */
.terminal-window {{
    background: var(--bg-primary);
    min-height: 100vh;
    position: relative;
}}

/* Header */
.terminal-header {{
    background: var(--bg-secondary);
    padding: 1rem 2rem;
    border-bottom: 2px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}}

.terminal-title {{
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--accent-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.terminal-title::before {{
    content: "🔒";
    font-size: 1.2em;
}}

.terminal-meta {{
    color: var(--text-muted);
    font-size: 0.9rem;
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}}

/* Status Line */
.status-line {{
    background: var(--accent-info);
    color: var(--bg-primary);
    padding: 0.5rem 2rem;
    font-weight: bold;
    font-size: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}}

.status-indicator {{
    display: flex;
    align-items: center;
    gap: 0.25rem;
}}

/* Terminal Body */
.terminal-body {{
    padding: 2rem;
    background: var(--bg-primary);
}}

/* Cards and Sections */
.card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    margin: 1rem 0;
    overflow: hidden;
}}

.card-header {{
    background: var(--bg-tertiary);
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    font-weight: bold;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.card-body {{
    padding: 1.5rem;
}}

/* Grid Layouts */
.grid {{
    display: grid;
    gap: 1rem;
}}

.grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
.grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }}
.grid-4 {{ grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }}

/* Summary Dashboard */
.summary-stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}}

.stat-card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    padding: 1.5rem 1rem;
    text-align: center;
    border-radius: 4px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}

.stat-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}}

.stat-value {{
    font-size: 2rem;
    font-weight: bold;
    line-height: 1;
    margin-bottom: 0.5rem;
}}

.stat-label {{
    color: var(--text-muted);
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.stat-success {{ color: var(--accent-success); }}
.stat-error {{ color: var(--accent-error); }}
.stat-warning {{ color: var(--accent-warning); }}
.stat-info {{ color: var(--accent-info); }}

/* Progress Bars */
.progress-bar {{
    background: var(--bg-tertiary);
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 0.5rem 0;
}}

.progress-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}}

.progress-success {{ background: var(--accent-success); }}
.progress-error {{ background: var(--accent-error); }}

/* Tables */
.table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
}}

.table th,
.table td {{
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    vertical-align: top;
}}

.table th {{
    background: var(--bg-tertiary);
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 10;
}}

.table tr:hover {{
    background: var(--bg-tertiary);
}}

/* Status Badges */
.status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.status-passed {{
    background: var(--accent-success);
    color: var(--bg-primary);
}}

.status-failed {{
    background: var(--accent-error);
    color: var(--bg-primary);
}}

.status-error {{
    background: var(--accent-warning);
    color: var(--bg-primary);
}}

.status-running {{
    background: var(--accent-info);
    color: var(--bg-primary);
    animation: pulse 2s infinite;
}}

/* Collapsible Sections */
.collapsible {{
    cursor: pointer;
    user-select: none;
}}

.collapsible-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
}}

.collapsible-content {{
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}}

.collapsible.expanded .collapsible-content {{
    max-height: 1000px;
}}

.collapse-icon {{
    transition: transform 0.3s ease;
    font-family: monospace;
    font-size: 1.2rem;
}}

.collapsible.expanded .collapse-icon {{
    transform: rotate(90deg);
}}

/* Code and Logs */
.code-block {{
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    font-family: inherit;
    white-space: pre-wrap;
    max-height: 300px;
    overflow-y: auto;
}}

.log-entry {{
    padding: 0.25rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-family: inherit;
}}

.log-timestamp {{
    color: var(--text-muted);
    margin-right: 0.5rem;
}}

/* Performance Charts */
.chart-container {{
    height: 300px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
}}

/* Interactive Elements */
.btn {{
    background: var(--accent-primary);
    color: var(--bg-primary);
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-family: inherit;
    font-weight: bold;
    transition: all 0.2s ease;
}}

.btn:hover {{
    background: var(--accent-secondary);
    transform: translateY(-1px);
}}

.btn-secondary {{
    background: var(--bg-tertiary);
    color: var(--text-primary);
}}

.btn-small {{
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
}}

/* Filters and Controls */
.controls {{
    display: flex;
    gap: 1rem;
    margin: 1rem 0;
    flex-wrap: wrap;
    align-items: center;
}}

.filter-group {{
    display: flex;
    gap: 0.5rem;
    align-items: center;
}}

.filter-label {{
    color: var(--text-muted);
    font-size: 0.9rem;
}}

select, input[type="text"] {{
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    padding: 0.5rem;
    border-radius: 4px;
    font-family: inherit;
}}

/* Animations */
@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
}}

@keyframes slideIn {{
    from {{ transform: translateY(-10px); opacity: 0; }}
    to {{ transform: translateY(0); opacity: 1; }}
}}

.slide-in {{
    animation: slideIn 0.3s ease-out;
}}

/* Responsive Design */
@media (max-width: 768px) {{
    .terminal-header,
    .status-line,
    .terminal-body {{
        padding: 1rem;
    }}

    .summary-stats {{
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }}

    .controls {{
        flex-direction: column;
        align-items: stretch;
    }}

    .table {{
        font-size: 0.8rem;
    }}

    .table th,
    .table td {{
        padding: 0.5rem;
    }}
}}

/* Print Styles */
@media print {{
    body {{
        background: white !important;
        color: black !important;
        font-size: 12pt;
    }}

    .terminal-window {{
        background: white !important;
    }}

    .card,
    .stat-card {{
        border: 1px solid #ccc !important;
        background: white !important;
    }}

    .btn,
    .controls {{
        display: none !important;
    }}

    .collapsible-content {{
        max-height: none !important;
    }}
}}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {{
    * {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }}
}}

.sr-only {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}}
</style>"""

    def _generate_header(self) -> str:
        """Generate the terminal header section."""
        timestamp = datetime.fromtimestamp(self.results.start_time).strftime("%Y-%m-%d %H:%M:%S")
        duration = f"{self.results.duration:.2f}s" if self.results.duration else "Running..."

        return f"""<div class="terminal-header">
    <div class="terminal-title">
        {self.config.report_title}
        <span style="color: var(--text-muted); font-size: 0.8em;">v1.0</span>
    </div>
    <div class="terminal-meta">
        <div>Suite: {self.results.suite_name}</div>
        <div>Started: {timestamp}</div>
        <div>Duration: {duration}</div>
    </div>
</div>"""

    def _generate_status_line(self) -> str:
        """Generate the vim-style status line."""
        mode = "NORMAL" if self.results.end_time else "INSERT"
        file_info = f"{self.results.suite_name}.py"
        line_col = f"{self.results.total_tests}L, {self.results.passed_tests}P"

        return f"""<div class="status-line">
    <div class="status-indicator">
        <span>{mode}</span>
        <span>|</span>
        <span>{file_info}</span>
        <span>|</span>
        <span>{line_col}</span>
    </div>
    <div class="status-indicator">
        <span>Success Rate: {self.results.success_rate:.1f}%</span>
        <span>|</span>
        <span>Tests: {self.results.total_tests}</span>
    </div>
</div>"""

    def _generate_summary_dashboard(self) -> str:
        """Generate the summary dashboard with statistics."""
        return f"""<div class="card">
    <div class="card-header">
        <span>📊 Test Summary Dashboard</span>
        <div class="controls">
            <button class="btn btn-small" onclick="toggleAutoRefresh()">Auto Refresh: OFF</button>
            <button class="btn btn-small" onclick="exportResults()">Export JSON</button>
        </div>
    </div>
    <div class="card-body">
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-value stat-info">{self.results.total_tests}</div>
                <div class="stat-label">Total Tests</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-success" style="width: 100%"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-success">{self.results.passed_tests}</div>
                <div class="stat-label">Passed</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-success" style="width: {(self.results.passed_tests/self.results.total_tests*100) if self.results.total_tests > 0 else 0}%"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-error">{self.results.failed_tests}</div>
                <div class="stat-label">Failed</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-error" style="width: {(self.results.failed_tests/self.results.total_tests*100) if self.results.total_tests > 0 else 0}%"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-warning">{self.results.error_tests}</div>
                <div class="stat-label">Errors</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-error" style="width: {(self.results.error_tests/self.results.total_tests*100) if self.results.total_tests > 0 else 0}%"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-info">{self.results.success_rate:.1f}%</div>
                <div class="stat-label">Success Rate</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-success" style="width: {self.results.success_rate}%"></div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-value stat-info">{self.results.duration:.2f}s</div>
                <div class="stat-label">Duration</div>
            </div>
        </div>
    </div>
</div>"""

    def _generate_test_categories(self) -> str:
        """Generate test results organized by category."""
        categories_html = []

        for category in TestCategory:
            tests = self.results.get_tests_by_category(category)
            if not tests:
                continue

            passed = len([t for t in tests if t.status == TestStatus.PASSED])
            failed = len([t for t in tests if t.status == TestStatus.FAILED])
            errors = len([t for t in tests if t.status == TestStatus.ERROR])

            category_html = f"""<div class="card collapsible" data-category="{category.value}">
    <div class="collapsible-header">
        <div>
            <span>🧪 {category.value.replace('_', ' ').title()}</span>
            <span style="color: var(--text-muted); margin-left: 1rem;">
                {len(tests)} tests | {passed} passed | {failed} failed | {errors} errors
            </span>
        </div>
        <span class="collapse-icon">▶</span>
    </div>
    <div class="collapsible-content">
        <div class="card-body">
            <table class="table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Status</th>
                        <th>Duration</th>
                        <th>Assertions</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>"""

            for test in tests:
                duration_str = f"{test.duration:.3f}s" if test.duration else "N/A"
                assertions_str = f"{test.assertions_passed}/{test.assertions_total}"
                status_class = f"status-{test.status.value}"

                category_html += f"""<tr class="test-row" data-test="{test.name}">
                        <td>{test.name}</td>
                        <td><span class="status-badge {status_class}">{test.status.value}</span></td>
                        <td>{duration_str}</td>
                        <td>{assertions_str}</td>
                        <td>
                            <button class="btn btn-small" onclick="showTestDetails('{test.name}')">Details</button>
                        </td>
                    </tr>"""

            category_html += """</tbody>
            </table>
        </div>
    </div>
</div>"""

            categories_html.append(category_html)

        return "\n".join(categories_html)

    def _generate_detailed_results(self) -> str:
        """Generate detailed test results section."""
        return f"""<div class="card">
    <div class="card-header">
        <span>🔍 Detailed Test Results</span>
        <div class="controls">
            <div class="filter-group">
                <span class="filter-label">Filter:</span>
                <select id="statusFilter" onchange="filterTests()">
                    <option value="">All Status</option>
                    <option value="passed">Passed</option>
                    <option value="failed">Failed</option>
                    <option value="error">Error</option>
                </select>
            </div>
            <div class="filter-group">
                <span class="filter-label">Search:</span>
                <input type="text" id="searchFilter" placeholder="Search tests..." oninput="filterTests()">
            </div>
        </div>
    </div>
    <div class="card-body">
        <div id="detailed-tests">
            {self._generate_test_details()}
        </div>
    </div>
</div>"""

    def _generate_test_details(self) -> str:
        """Generate individual test detail cards."""
        details_html = []

        for test in self.results.tests:
            status_class = f"status-{test.status.value}"
            duration_str = f"{test.duration:.3f}s" if test.duration else "N/A"

            # Generate logs section
            logs_html = ""
            if test.output_logs:
                logs_html = f"""<div class="collapsible">
                    <div class="collapsible-header">
                        <span>📝 Logs ({len(test.output_logs)} entries)</span>
                        <span class="collapse-icon">▶</span>
                    </div>
                    <div class="collapsible-content">
                        <div class="code-block">
{''.join(f'<div class="log-entry">{html.escape(log)}</div>' for log in test.output_logs)}
                        </div>
                    </div>
                </div>"""

            # Generate error section
            error_html = ""
            if test.error_message:
                error_html = f"""<div class="collapsible">
                    <div class="collapsible-header" style="background: var(--accent-error); color: var(--bg-primary);">
                        <span>❌ Error Details</span>
                        <span class="collapse-icon">▶</span>
                    </div>
                    <div class="collapsible-content">
                        <div class="code-block" style="background: rgba(251, 73, 52, 0.1);">
                            <strong>Message:</strong> {html.escape(test.error_message)}
                            {f'<br><br><strong>Traceback:</strong><br>{html.escape(test.error_traceback)}' if test.error_traceback else ''}
                        </div>
                    </div>
                </div>"""

            # Generate performance metrics section
            metrics_html = ""
            if test.performance_metrics:
                metrics_table = '<table class="table"><thead><tr><th>Metric</th><th>Value</th><th>Unit</th><th>Status</th></tr></thead><tbody>'
                for metric in test.performance_metrics:
                    status_color = {
                        'ok': 'var(--accent-success)',
                        'warning': 'var(--accent-warning)',
                        'error': 'var(--accent-error)'
                    }.get(metric.status, 'var(--text-primary)')

                    metrics_table += f"""<tr>
                        <td>{metric.name}</td>
                        <td>{metric.value}</td>
                        <td>{metric.unit}</td>
                        <td style="color: {status_color};">{metric.status}</td>
                    </tr>"""
                metrics_table += '</tbody></table>'

                metrics_html = f"""<div class="collapsible">
                    <div class="collapsible-header">
                        <span>📈 Performance Metrics</span>
                        <span class="collapse-icon">▶</span>
                    </div>
                    <div class="collapsible-content">
                        {metrics_table}
                    </div>
                </div>"""

            test_html = f"""<div class="card test-detail" data-test="{test.name}" data-status="{test.status.value}" data-category="{test.category.value}">
                <div class="card-header">
                    <div>
                        <span>{test.name}</span>
                        <span class="status-badge {status_class}" style="margin-left: 1rem;">{test.status.value}</span>
                    </div>
                    <div style="color: var(--text-muted);">
                        Category: {test.category.value} | Duration: {duration_str}
                    </div>
                </div>
                <div class="card-body">
                    {error_html}
                    {logs_html}
                    {metrics_html}
                </div>
            </div>"""

            details_html.append(test_html)

        return "\n".join(details_html)

    def _generate_performance_section(self) -> str:
        """Generate performance metrics section."""
        if not self.config.include_performance_charts:
            return ""

        return """<div class="card">
    <div class="card-header">
        <span>📈 Performance Analysis</span>
    </div>
    <div class="card-body">
        <div class="grid grid-2">
            <div class="chart-container">
                <div>Test Duration Distribution Chart<br><small style="color: var(--text-muted);">(Chart rendering requires JavaScript)</small></div>
            </div>
            <div class="chart-container">
                <div>Performance Metrics Trend<br><small style="color: var(--text-muted);">(Chart rendering requires JavaScript)</small></div>
            </div>
        </div>
    </div>
</div>"""

    def _generate_environment_section(self) -> str:
        """Generate environment information section."""
        if not self.config.include_environment_info:
            return ""

        env_info = {
            "Python Version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "Platform": platform.platform(),
            "Architecture": platform.architecture()[0],
            "Processor": platform.processor() or platform.machine(),
            "Host": platform.node(),
            "Generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        env_info.update(self.results.environment_info)

        env_rows = "".join(f"""<tr><td>{key}</td><td>{value}</td></tr>"""
                          for key, value in env_info.items())

        return f"""<div class="card">
    <div class="card-header">
        <span>🖥️ Environment Information</span>
    </div>
    <div class="card-body">
        <table class="table">
            <thead>
                <tr>
                    <th>Property</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                {env_rows}
            </tbody>
        </table>
    </div>
</div>"""

    def _generate_javascript(self) -> str:
        """Generate embedded JavaScript for interactivity."""
        return f"""<script>
// Enhanced Test Report JavaScript with Modern Features
(function() {{
    'use strict';

    // Global state
    let autoRefreshEnabled = false;
    let autoRefreshInterval = null;
    let testData = null;

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {{
        initializeReport();
        loadTestData();
        setupEventListeners();
        setupCollapsibleSections();
        setupKeyboardShortcuts();
        detectFileProtocol();
    }});

    function initializeReport() {{
        console.log('🚀 Initializing Security Test Report');

        // Add loading animation for charts
        const chartContainers = document.querySelectorAll('.chart-container');
        chartContainers.forEach(container => {{
            container.innerHTML = '<div style="text-align: center;"><div style="animation: pulse 2s infinite;">📊 Loading Chart...</div></div>';
        }});

        // Animate test rows on load
        const testRows = document.querySelectorAll('.test-detail');
        testRows.forEach((row, index) => {{
            setTimeout(() => {{
                row.classList.add('slide-in');
            }}, index * 50);
        }});
    }}

    function loadTestData() {{
        const dataElement = document.getElementById('test-data');
        if (dataElement) {{
            try {{
                testData = JSON.parse(dataElement.textContent);
                console.log('✅ Test data loaded:', testData.summary);
                renderCharts();
            }} catch (e) {{
                console.error('❌ Failed to parse test data:', e);
            }}
        }}
    }}

    function setupEventListeners() {{
        // Filter functionality
        const statusFilter = document.getElementById('statusFilter');
        const searchFilter = document.getElementById('searchFilter');

        if (statusFilter) statusFilter.addEventListener('change', filterTests);
        if (searchFilter) searchFilter.addEventListener('input', filterTests);

        // Copy functionality for code blocks
        document.querySelectorAll('.code-block').forEach(block => {{
            block.addEventListener('dblclick', function() {{
                copyToClipboard(block.textContent);
                showToast('Copied to clipboard!', 'success');
            }});

            // Add copy hint
            block.title = 'Double-click to copy';
            block.style.cursor = 'copy';
        }});
    }}

    function setupCollapsibleSections() {{
        document.querySelectorAll('.collapsible').forEach(element => {{
            const header = element.querySelector('.collapsible-header');
            const content = element.querySelector('.collapsible-content');
            const icon = element.querySelector('.collapse-icon');

            if (header && content && icon) {{
                header.addEventListener('click', function() {{
                    const isExpanded = element.classList.contains('expanded');

                    element.classList.toggle('expanded');
                    icon.textContent = isExpanded ? '▶' : '▼';

                    // Smooth height animation
                    if (!isExpanded) {{
                        content.style.maxHeight = content.scrollHeight + 'px';
                    }} else {{
                        content.style.maxHeight = '0px';
                    }}
                }});

                // Set initial state based on content importance
                if (element.dataset.category ||
                    header.textContent.includes('Error') ||
                    header.textContent.includes('Failed')) {{
                    header.click(); // Auto-expand important sections
                }}
            }}
        }});
    }}

    function setupKeyboardShortcuts() {{
        document.addEventListener('keydown', function(e) {{
            // Only trigger if not in input field
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

            switch(e.key) {{
                case 'e':
                    if (e.ctrlKey || e.metaKey) {{
                        e.preventDefault();
                        exportResults();
                    }}
                    break;
                case 'r':
                    if (e.ctrlKey || e.metaKey) {{
                        e.preventDefault();
                        toggleAutoRefresh();
                    }}
                    break;
                case 'f':
                    if (e.ctrlKey || e.metaKey) {{
                        e.preventDefault();
                        const searchFilter = document.getElementById('searchFilter');
                        if (searchFilter) searchFilter.focus();
                    }}
                    break;
                case 'Escape':
                    // Close any open modals or reset filters
                    resetFilters();
                    break;
            }}
        }});
    }}

    function detectFileProtocol() {{
        if (window.location.protocol === 'file:') {{
            console.info('📁 File protocol detected - some features may be limited');

            // Disable features that don't work with file://
            const autoRefreshBtn = document.querySelector('[onclick="toggleAutoRefresh()"]');
            if (autoRefreshBtn) {{
                autoRefreshBtn.style.opacity = '0.5';
                autoRefreshBtn.title = 'Auto-refresh not available in file:// mode';
            }}
        }}
    }}

    // Global functions for HTML onclick handlers
    window.toggleAutoRefresh = function() {{
        if (window.location.protocol === 'file:') {{
            showToast('Auto-refresh not available in file:// mode', 'warning');
            return;
        }}

        autoRefreshEnabled = !autoRefreshEnabled;
        const btn = document.querySelector('[onclick="toggleAutoRefresh()"]');

        if (autoRefreshEnabled) {{
            btn.textContent = 'Auto Refresh: ON';
            autoRefreshInterval = setInterval(() => {{
                window.location.reload();
            }}, {self.config.refresh_interval * 1000});
            showToast('Auto-refresh enabled', 'success');
        }} else {{
            btn.textContent = 'Auto Refresh: OFF';
            if (autoRefreshInterval) {{
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }}
            showToast('Auto-refresh disabled', 'info');
        }}
    }};

    window.exportResults = function() {{
        if (!testData) {{
            showToast('No test data available for export', 'error');
            return;
        }}

        try {{
            const jsonData = JSON.stringify(testData, null, 2);
            const blob = new Blob([jsonData], {{ type: 'application/json' }});
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `test_results_${{new Date().toISOString().slice(0, 19).replace(/:/g, '-')}}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('Test results exported successfully', 'success');
        }} catch (e) {{
            console.error('Export failed:', e);
            showToast('Failed to export test results', 'error');
        }}
    }};

    window.showTestDetails = function(testName) {{
        const testElement = document.querySelector(`[data-test="${{testName}}"]`);
        if (testElement) {{
            testElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            testElement.style.transform = 'scale(1.02)';
            testElement.style.boxShadow = '0 8px 25px rgba(254, 128, 25, 0.3)';

            setTimeout(() => {{
                testElement.style.transform = '';
                testElement.style.boxShadow = '';
            }}, 1000);
        }}
    }};

    window.filterTests = function() {{
        const statusFilter = document.getElementById('statusFilter');
        const searchFilter = document.getElementById('searchFilter');

        const statusValue = statusFilter ? statusFilter.value.toLowerCase() : '';
        const searchValue = searchFilter ? searchFilter.value.toLowerCase() : '';

        document.querySelectorAll('.test-detail').forEach(test => {{
            const testStatus = test.dataset.status || '';
            const testName = test.dataset.test || '';

            const statusMatch = !statusValue || testStatus === statusValue;
            const searchMatch = !searchValue || testName.toLowerCase().includes(searchValue);

            test.style.display = (statusMatch && searchMatch) ? 'block' : 'none';
        }});

        // Update category counters
        updateCategoryCounters();
    }};

    function resetFilters() {{
        const statusFilter = document.getElementById('statusFilter');
        const searchFilter = document.getElementById('searchFilter');

        if (statusFilter) statusFilter.value = '';
        if (searchFilter) searchFilter.value = '';

        filterTests();
    }}

    function updateCategoryCounters() {{
        document.querySelectorAll('[data-category]').forEach(category => {{
            const categoryValue = category.dataset.category;
            const visibleTests = document.querySelectorAll(`.test-detail[data-category="${{categoryValue}}"]:not([style*="display: none"])`);
            const totalTests = document.querySelectorAll(`.test-detail[data-category="${{categoryValue}}"]`);

            const headerText = category.querySelector('.collapsible-header span:first-child');
            if (headerText) {{
                const originalText = headerText.textContent.split('(')[0].trim();
                headerText.textContent = `${{originalText}} (${{visibleTests.length}}/${{totalTests.length}} visible)`;
            }}
        }});
    }}

    function renderCharts() {{
        if (!testData || !testData.tests) return;

        // Simple ASCII-style charts for universal compatibility
        const chartContainers = document.querySelectorAll('.chart-container');

        if (chartContainers.length >= 1) {{
            renderDurationChart(chartContainers[0]);
        }}

        if (chartContainers.length >= 2) {{
            renderMetricsChart(chartContainers[1]);
        }}
    }}

    function renderDurationChart(container) {{
        const tests = testData.tests.filter(t => t.duration);
        if (tests.length === 0) {{
            container.innerHTML = '<div>No duration data available</div>';
            return;
        }}

        tests.sort((a, b) => b.duration - a.duration);
        const maxDuration = tests[0].duration;

        let chartHtml = '<div style="font-family: monospace; font-size: 12px; text-align: left;">';
        chartHtml += '<div style="margin-bottom: 10px; font-weight: bold;">Test Duration (seconds)</div>';

        tests.slice(0, 10).forEach(test => {{
            const barWidth = Math.max(1, (test.duration / maxDuration) * 40);
            const bar = '█'.repeat(Math.floor(barWidth)) + '░'.repeat(40 - Math.floor(barWidth));
            const statusColor = test.status === 'passed' ? 'var(--accent-success)' :
                               test.status === 'failed' ? 'var(--accent-error)' : 'var(--accent-warning)';

            chartHtml += `<div style="margin: 2px 0; color: ${{statusColor}};">`;
            chartHtml += `<span style="width: 200px; display: inline-block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{test.name.slice(0, 25)}}</span> `;
            chartHtml += `<span style="font-family: monospace;">${{bar}}</span> `;
            chartHtml += `<span>${{test.duration.toFixed(3)}}s</span>`;
            chartHtml += `</div>`;
        }});

        chartHtml += '</div>';
        container.innerHTML = chartHtml;
    }}

    function renderMetricsChart(container) {{
        const allMetrics = testData.tests.flatMap(t => t.performance_metrics || []);

        if (allMetrics.length === 0) {{
            container.innerHTML = '<div>No performance metrics available</div>';
            return;
        }}

        // Group metrics by name
        const metricGroups = {{}};
        allMetrics.forEach(metric => {{
            if (!metricGroups[metric.name]) {{
                metricGroups[metric.name] = [];
            }}
            metricGroups[metric.name].push(metric.value);
        }});

        let chartHtml = '<div style="font-family: monospace; font-size: 12px; text-align: left;">';
        chartHtml += '<div style="margin-bottom: 10px; font-weight: bold;">Performance Metrics Summary</div>';

        Object.entries(metricGroups).forEach(([name, values]) => {{
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const min = Math.min(...values);
            const max = Math.max(...values);

            chartHtml += `<div style="margin: 5px 0; padding: 5px; background: var(--bg-secondary); border-radius: 3px;">`;
            chartHtml += `<div style="font-weight: bold;">${{name}}</div>`;
            chartHtml += `<div style="color: var(--text-muted);">Avg: ${{avg.toFixed(3)}} | Min: ${{min.toFixed(3)}} | Max: ${{max.toFixed(3)}}</div>`;
            chartHtml += `</div>`;
        }});

        chartHtml += '</div>';
        container.innerHTML = chartHtml;
    }}

    function copyToClipboard(text) {{
        if (navigator.clipboard) {{
            navigator.clipboard.writeText(text).catch(e => {{
                console.error('Clipboard write failed:', e);
                fallbackCopy(text);
            }});
        }} else {{
            fallbackCopy(text);
        }}
    }}

    function fallbackCopy(text) {{
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }}

    function showToast(message, type = 'info') {{
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--accent-${{type}});
            color: var(--bg-primary);
            padding: 12px 20px;
            border-radius: 4px;
            font-weight: bold;
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        `;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {{
            toast.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }}, 3000);
    }}

    // Add some custom CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOut {{
            to {{ transform: translateX(100%); opacity: 0; }}
        }}
    `;
    document.head.appendChild(style);

    console.log('🎉 Security Test Report initialized successfully!');
}})();
</script>"""
# PyPI Query MCP Server

[![PyPI version](https://img.shields.io/pypi/v/mcpypi.svg)](https://pypi.org/project/mcpypi/)

A Model Context Protocol (MCP) server for querying PyPI package information, dependencies, and compatibility checking.

## Features

- 📦 Query PyPI package information (name, version, description, dependencies)
- 🐍 Python version compatibility checking
- 🔍 **Advanced dependency analysis and recursive resolution**
- 📥 **Package download with dependency collection**
- 📊 **Download statistics and popularity analysis**
- 🏆 **Top packages ranking and trends**
- 🎯 **MCP prompt templates for guided analysis and decision-making**
- 🏢 Private PyPI repository support
- ⚡ Fast async operations with caching
- 🛠️ Easy integration with MCP clients

## Installation

### Using uvx (recommended)

```bash
# Run directly with uvx
uvx mcpypi

# Or install and run with specific script
uvx --from mcpypi mcpypi
```

### Using pip

```bash
# Install from PyPI
pip install mcpypi

# Run the server
python -m pypi_query_mcp.server
```

### From source

```bash
git clone https://github.com/loonghao/pypi-query-mcp-server.git
cd pypi-query-mcp-server
uv sync
uv run pypi-query-mcp
```

## Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pypi-query": {
      "command": "uvx",
      "args": ["--from", "mcpypi", "mcpypi"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/pypi",
        "PYPI_INDEX_URLS": "https://mirrors.aliyun.com/pypi/simple/,https://pypi.tuna.tsinghua.edu.cn/simple/",
        "PYPI_CACHE_TTL": "3600",
        "PYPI_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### With Private Repository
```json
{
  "mcpServers": {
    "pypi-query": {
      "command": "uvx",
      "args": ["--from", "mcpypi", "mcpypi"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/pypi",
        "PYPI_PRIVATE_PYPI_URL": "https://private.pypi.company.com",
        "PYPI_PRIVATE_PYPI_USERNAME": "your_username",
        "PYPI_PRIVATE_PYPI_PASSWORD": "your_password",
        "PYPI_CACHE_TTL": "3600"
      }
    }
  }
}
```

### Cline

Add to your Cline MCP settings (`cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "pypi-query": {
      "command": "uvx",
      "args": ["--from", "mcpypi", "mcpypi"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/simple/",
        "CACHE_TTL": "3600"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP configuration (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "pypi-query": {
      "command": "uvx",
      "args": ["--from", "mcpypi", "mcpypi"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/simple/",
        "CACHE_TTL": "3600"
      }
    }
  }
}
```

### Windsurf

Add to your Windsurf MCP configuration (`~/.codeium/windsurf/mcp_config.json`):

```json
{
  "mcpServers": {
    "pypi-query": {
      "command": "uvx",
      "args": ["--from", "mcpypi", "mcpypi"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/simple/",
        "CACHE_TTL": "3600"
      }
    }
  }
}
```

### Claude Code

If you're using [Claude Code](https://claude.ai/code), you can connect to this MCP server using the `claude mcp` command:

```bash
# Connect to the PyPI Query MCP server
claude mcp add mcpypi -- uvx mcpypi

# Or with custom environment variables
claude mcp add mcpypi -- uvx mcpypi \
  --env PYPI_INDEX_URL=https://pypi.org/pypi \
  --env PYPI_CACHE_TTL=3600 \
  --env PYPI_LOG_LEVEL=INFO

# List connected MCP servers
claude mcp list

# Remove the server if needed
claude mcp remove mcpypi
```

Once connected, you can use all the MCP tools directly in Claude Code sessions by asking questions like:
- "What are the dependencies of Django?"
- "Check if numpy is compatible with Python 3.11"
- "Show me the top downloaded packages this month"
- "Analyze the security vulnerabilities in my requirements.txt file"

### Environment Variables

#### Basic Configuration
- `PYPI_INDEX_URL`: Primary PyPI index URL (default: https://pypi.org/pypi)
- `PYPI_CACHE_TTL`: Cache time-to-live in seconds (default: 3600)
- `PYPI_LOG_LEVEL`: Logging level (default: INFO)
- `PYPI_REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 30.0)

#### Multiple Mirror Sources Support
- `PYPI_INDEX_URLS`: Additional PyPI index URLs (comma-separated, optional)
- `PYPI_EXTRA_INDEX_URLS`: Extra PyPI index URLs for fallback (comma-separated, optional)

#### Private Repository Support
- `PYPI_PRIVATE_PYPI_URL`: Private PyPI repository URL (optional)
- `PYPI_PRIVATE_PYPI_USERNAME`: Private PyPI username (optional)
- `PYPI_PRIVATE_PYPI_PASSWORD`: Private PyPI password (optional)

#### Advanced Dependency Analysis
- `PYPI_DEPENDENCY_MAX_DEPTH`: Maximum depth for recursive dependency analysis (default: 5)
- `PYPI_DEPENDENCY_MAX_CONCURRENT`: Maximum concurrent dependency queries (default: 10)
- `PYPI_ENABLE_SECURITY_ANALYSIS`: Enable security vulnerability analysis (default: false)

#### Example Configuration
```bash
# Use multiple mirror sources for better availability
export PYPI_INDEX_URL="https://pypi.org/pypi"
export PYPI_INDEX_URLS="https://mirrors.aliyun.com/pypi/simple/,https://pypi.tuna.tsinghua.edu.cn/simple/"
export PYPI_EXTRA_INDEX_URLS="https://test.pypi.org/simple/"

# Private repository configuration
export PYPI_PRIVATE_PYPI_URL="https://private.pypi.company.com"
export PYPI_PRIVATE_PYPI_USERNAME="your_username"
export PYPI_PRIVATE_PYPI_PASSWORD="your_password"
```

## Available MCP Tools

The server provides **37 comprehensive MCP tools** across **8 categories**:

### Core Package Information (11 tools)
1. **get_package_info** - Get comprehensive package information
2. **get_package_versions** - List all available versions for a package
3. **get_package_dependencies** - Analyze package dependencies
4. **check_package_python_compatibility** - Check Python version compatibility
5. **get_package_compatible_python_versions** - Get all compatible Python versions
6. **resolve_dependencies** - Recursively resolve all package dependencies with detailed analysis
7. **download_package** - Download package and all dependencies to local directory
8. **get_download_statistics** - Get comprehensive download statistics for any package
9. **get_download_trends** - Analyze download trends and time series data (last 180 days)
10. **get_top_downloaded_packages** - Get the most popular packages by download count
11. **search_pypi_packages** - Advanced PyPI package search with intelligent fallbacks

### PyPI Publishing & Account Management (6 tools)
12. **upload_package_to_pypi** - Upload packages to PyPI with comprehensive validation
13. **check_pypi_credentials** - Validate PyPI authentication credentials
14. **get_pypi_upload_history** - Get detailed upload history and statistics
15. **delete_pypi_release** - Delete specific package releases from PyPI
16. **manage_pypi_maintainers** - Add/remove package maintainers
17. **get_pypi_account_info** - Get comprehensive PyPI account information

### Package Metadata & Management (4 tools)
18. **update_package_metadata** - Update package descriptions, keywords, and metadata
19. **manage_package_urls** - Update project URLs and documentation links
20. **set_package_visibility** - Control package visibility and access
21. **manage_package_keywords** - Add/remove package keywords and tags

### Analytics & Insights (4 tools)
22. **get_pypi_package_analytics** - Comprehensive package analytics and metrics
23. **get_pypi_security_alerts** - Security vulnerability alerts and advisories
24. **get_pypi_package_rankings** - Package popularity rankings and comparisons
25. **analyze_pypi_competition** - Competitive analysis with similar packages

### Discovery & Monitoring (4 tools)
26. **monitor_pypi_new_releases** - Monitor new package releases and updates
27. **get_pypi_trending_today** - Get trending packages with growth metrics
28. **search_pypi_by_maintainer** - Find packages by maintainer or organization
29. **get_pypi_package_recommendations** - Get intelligent package recommendations

### Development Workflow (4 tools)
30. **validate_pypi_package_name** - Validate package names and availability
31. **preview_pypi_package_page** - Preview package page before publishing
32. **check_pypi_upload_requirements** - Validate package before upload
33. **get_pypi_build_logs** - Retrieve build logs and debugging information

### 🔒 Security Analysis (2 tools)
34. **scan_pypi_package_security** - Comprehensive security vulnerability scanning with OSV database and GitHub advisories
35. **bulk_scan_package_security** - Bulk security scanning for multiple packages with consolidated reporting

### 📄 License & Compliance (2 tools)
36. **analyze_pypi_package_license** - License compatibility analysis with SPDX normalization and risk assessment
37. **check_bulk_license_compliance** - Bulk license compliance checking with comprehensive compatibility matrix

### 🏥 Package Health Assessment (2 tools)
- **assess_package_health_score** - Package health scoring across 7 categories (maintenance, popularity, documentation, testing, security, compatibility, metadata)
- **compare_packages_health_scores** - Comparative health analysis between multiple packages with GitHub metrics integration

### 📋 Requirements Analysis (2 tools)
- **analyze_requirements_file_tool** - Requirements file analysis supporting multiple formats (requirements.txt, pyproject.toml, setup.py, Pipfile, conda.yml)
- **compare_multiple_requirements_files** - Multi-file comparison for requirements analysis across different environments

### MCP Prompt Templates (12 tools)
- **analyze_package_quality** - Generate comprehensive package quality analysis prompts
- **compare_packages** - Generate detailed package comparison prompts
- **suggest_alternatives** - Generate prompts for finding package alternatives
- **resolve_dependency_conflicts** - Generate prompts for resolving dependency conflicts
- **plan_version_upgrade** - Generate prompts for planning package version upgrades
- **audit_security_risks** - Generate prompts for security risk auditing
- **plan_package_migration** - Generate comprehensive package migration plan prompts
- **generate_migration_checklist** - Generate detailed migration checklist prompts
- **analyze_environment_dependencies** - Generate prompts for analyzing current environment dependencies
- **check_outdated_packages** - Generate prompts for checking outdated packages with update priorities
- **generate_update_plan** - Generate prompts for creating comprehensive package update plans
- **analyze_daily_trends** - Generate prompts for analyzing daily PyPI download trends

> 📖 **Learn more about prompt templates**: See [PROMPT_TEMPLATES.md](PROMPT_TEMPLATES.md) for detailed documentation and examples.

## Usage Examples

Once configured in your MCP client (Claude Desktop, Cline, Cursor, Windsurf), you can ask questions like:

### Basic Package Queries
- "What are the dependencies of Django 4.2?"
- "Is FastAPI compatible with Python 3.9?"
- "Show me all versions of requests package"
- "What Python versions does numpy support?"
- "Get detailed information about the pandas package"

### Advanced Dependency Analysis
- "Please help me analyze the complete dependency tree for PySide2 with Python 3.10"
- "Resolve all dependencies for Django including development dependencies"
- "What are all the transitive dependencies of FastAPI?"

### Package Download
- "Please help me download PySide2 and all its dependencies for Python 3.10 to my local machine"
- "Download the requests package with all dependencies to ./downloads folder"
- "Collect all packages needed for Django development"

### Download Statistics & Popularity Analysis
- "What are the download statistics for the requests package this month?"
- "Show me the download trends for numpy over the last 180 days"
- "What are the top 10 most downloaded Python packages today?"
- "Compare the popularity of Django vs Flask vs FastAPI"
- "Which web framework has the highest download count this week?"

### MCP Prompt Templates
- "Use the analyze_package_quality prompt to evaluate the requests package"
- "Generate a comparison prompt for Django vs FastAPI vs Flask for building APIs"
- "Create a migration plan prompt for moving from Flask to FastAPI"
- "Help me resolve dependency conflicts with a structured prompt"
- "Generate a security audit prompt for my production packages"

### Environment Analysis
- "Analyze my current Python environment dependencies and check for outdated packages"
- "Check which packages in my environment have security updates available"
- "Generate an update plan for my production environment with conservative strategy"
- "Help me identify packages that need immediate updates vs. planned updates"

### Trending Analysis
- "What are the most downloaded Python packages today?"
- "Show me trending packages in the machine learning domain this week"
- "Track recent security updates and new package releases"
- "Find rising packages in web development that I should consider"

### Security Analysis
- "Scan Django for security vulnerabilities using OSV database"
- "Check my requirements.txt file for packages with known security issues"
- "Bulk scan all packages in my project for security vulnerabilities"
- "What security advisories exist for numpy version 1.21.0?"

### License Analysis & Compliance
- "Analyze the license compatibility of MIT, Apache-2.0, and GPL-3.0 licenses"
- "Check if all packages in my requirements.txt are compatible with my MIT license"
- "What are the licensing risks of using this package in a commercial project?"
- "Bulk check license compliance for my entire dependency tree"

### Package Health Assessment
- "Assess the overall health score of the requests package"
- "Compare the health scores of Django vs FastAPI vs Flask for a new project"
- "Which package has better maintenance: numpy or pandas?"
- "Score this package across maintenance, popularity, and security metrics"

### Requirements File Analysis
- "Analyze my requirements.txt file for outdated packages and security issues"
- "Compare my development and production requirements files"
- "Parse my pyproject.toml file and suggest package updates"
- "What dependencies in my Pipfile need security updates?"

### Example Conversations

**User**: "Check if Django 4.2 is compatible with Python 3.9"

**AI Assistant**: I'll check Django 4.2's compatibility with Python 3.9 for you.

*[Uses get_package_info and check_package_python_compatibility tools]*

**User**: "What are the main dependencies of FastAPI?"

**AI Assistant**: Let me get the dependency information for FastAPI.

*[Uses get_package_dependencies tool]*

**User**: "Show me the download statistics for the requests package and tell me which is more popular: requests or urllib3?"

**AI Assistant**: I'll get the download statistics for both packages and compare their popularity.

*[Uses get_download_statistics tool for both packages]*

### Programmatic Usage

```python
# Example: Check if Django is compatible with Python 3.9
result = await mcp_client.call_tool("check_package_python_compatibility", {
    "package_name": "django",
    "target_python_version": "3.9"
})

# Example: Get package information
info = await mcp_client.call_tool("get_package_info", {
    "package_name": "requests"
})

# Example: Get download statistics
stats = await mcp_client.call_tool("get_download_statistics", {
    "package_name": "numpy",
    "period": "month"
})

# Example: Get top downloaded packages
top_packages = await mcp_client.call_tool("get_top_downloaded_packages", {
    "period": "week",
    "limit": 10
})
```

## Development Status

🎉 **Core functionality implemented and ready for use!**

Current implementation status:
- ✅ Basic project structure
- ✅ PyPI API client with caching
- ✅ MCP tools implementation (package info, versions, dependencies)
- ✅ Python version compatibility checking
- ✅ Advanced dependency analysis and recursive resolution
- ✅ Package download with dependency collection
- ✅ **Download statistics and popularity analysis**
- ✅ **Top packages ranking and trends**
- ✅ CI/CD pipeline with multi-platform testing
- ⏳ Private repository support (planned)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

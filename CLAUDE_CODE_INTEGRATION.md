# Claude Code Integration Guide

This guide covers how to integrate the PyPI Query MCP Server with [Claude Code](https://claude.ai/code), Anthropic's official CLI tool for Claude.

## Prerequisites

- Claude Code installed and configured
- Python 3.9+ with `uvx` available

## Installation Methods

### Method 1: Using Claude Code MCP Command (Recommended)

The simplest way to add the PyPI Query MCP Server to Claude Code is using the built-in MCP management:

#### From PyPI (Production Use)
```bash
# Add with local scope (project-specific)
claude mcp add pypi uvx pypi-query-mcp-server -s local

# Add with user scope (available across all projects)
claude mcp add pypi uvx pypi-query-mcp-server -s user
```

#### From Local Directory (Development)
For development or testing with a locally checked out repository:

```bash
# Clone the repository first (if not already done)
git clone https://github.com/loonghao/pypi-query-mcp-server.git
cd pypi-query-mcp-server

# Install in development mode from local directory
claude mcp add pypi-dev uv run pypi-query-mcp -s local

# Alternative: Install from local path with pip
claude mcp add pypi-local python -m pip install -e . && python -m pypi_query_mcp.server -s local
```

#### From Git Repository
You can also install directly from the git repository:

```bash
# Install from main branch
claude mcp add pypi-git uvx --from git+https://github.com/loonghao/pypi-query-mcp-server.git pypi-query-mcp -s local

# Install from specific branch or commit
claude mcp add pypi-git uvx --from git+https://github.com/loonghao/pypi-query-mcp-server.git@feature-branch pypi-query-mcp -s local
```

This will automatically configure the MCP server with sensible defaults.

### Method 2: Manual Configuration

If you prefer manual configuration or need custom settings, you can directly edit the Claude Code configuration files.

#### Local Scope Configuration

Create or edit `.claude/mcp.json` in your project directory:

```json
{
  "mcpServers": {
    "pypi": {
      "command": "uvx",
      "args": ["pypi-query-mcp-server"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/pypi",
        "PYPI_CACHE_TTL": "3600",
        "PYPI_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### User Scope Configuration

Edit `~/.claude/mcp.json` for user-wide availability:

```json
{
  "mcpServers": {
    "pypi": {
      "command": "uvx",
      "args": ["pypi-query-mcp-server"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/pypi",
        "PYPI_CACHE_TTL": "3600",
        "PYPI_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Advanced Configuration

### Multiple PyPI Sources

Configure multiple PyPI mirrors for better availability:

```json
{
  "mcpServers": {
    "pypi": {
      "command": "uvx",
      "args": ["pypi-query-mcp-server"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/pypi",
        "PYPI_INDEX_URLS": "https://mirrors.aliyun.com/pypi/simple/,https://pypi.tuna.tsinghua.edu.cn/simple/",
        "PYPI_CACHE_TTL": "3600"
      }
    }
  }
}
```

### Private Repository Support

For corporate environments with private PyPI repositories:

```json
{
  "mcpServers": {
    "pypi": {
      "command": "uvx",
      "args": ["pypi-query-mcp-server"],
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

## Usage with Claude Code

Once configured, you can use the PyPI Query MCP Server directly in your Claude Code conversations:

### Basic Package Information

```
What are the dependencies of Django 4.2?
```

```
Is FastAPI compatible with Python 3.11?
```

```
Show me information about the requests package
```

### Dependency Analysis

```
Help me analyze the complete dependency tree for PySide2 with Python 3.10
```

```
What are all the transitive dependencies of FastAPI?
```

### Download Statistics

```
What are the download statistics for numpy this month?
```

```
Show me the top 10 most downloaded Python packages
```

### Package Comparison

```
Compare the popularity and features of Django vs FastAPI vs Flask
```

### Environment Analysis

```
Analyze the dependencies in my current project and check for outdated packages
```

## Verification

To verify the MCP server is working correctly with Claude Code:

1. Start a new Claude Code session
2. Ask a simple question: "What is the latest version of requests?"
3. The response should include current PyPI information

You can also check the MCP server status:

```bash
claude mcp list
```

This should show the `pypi` server in the list of active MCP servers.

## Troubleshooting

### Common Issues

#### Server Not Found
```
Error: MCP server 'pypi' not found
```

**Solution**: Ensure uvx is installed and the package can be found:
```bash
uvx pypi-query-mcp-server --help
```

#### Connection Timeout
```
Error: Connection to MCP server timed out
```

**Solution**: Check network connectivity and try increasing timeout:
```json
{
  "env": {
    "PYPI_REQUEST_TIMEOUT": "60.0"
  }
}
```

#### Permission Errors
```
Error: Permission denied accessing PyPI
```

**Solution**: Check credentials for private repositories and ensure environment variables are set correctly.

### Debug Mode

Enable debug logging for troubleshooting:

```json
{
  "env": {
    "PYPI_LOG_LEVEL": "DEBUG"
  }
}
```

### Getting Help

- Check Claude Code documentation: `claude help mcp`
- View MCP server logs: `claude mcp logs pypi`
- Report issues: [GitHub Issues](https://github.com/loonghao/pypi-query-mcp-server/issues)

## Integration Examples

### Project Setup Workflow

When starting a new Python project with Claude Code:

1. Ask about package recommendations:
   ```
   I'm building a web API. What are the most popular Python web frameworks and their recent download trends?
   ```

2. Check compatibility:
   ```
   Is FastAPI compatible with Python 3.11? What are its main dependencies?
   ```

3. Analyze dependencies before installation:
   ```
   What would be the complete dependency tree if I install FastAPI, SQLAlchemy, and pytest?
   ```

### Maintenance Workflow

For existing projects:

1. Check for updates:
   ```
   Analyze my requirements.txt and check which packages have newer versions available
   ```

2. Security analysis:
   ```
   Check if any of my dependencies have known security issues or recent security updates
   ```

3. Migration planning:
   ```
   I want to migrate from Flask to FastAPI. Generate a detailed migration plan with dependency analysis
   ```

## Best Practices

1. **Scope Selection**: Use local scope (`-s local`) for project-specific configurations, user scope (`-s user`) for general development work.

2. **Caching**: Set appropriate cache TTL based on your workflow. Higher values (3600s+) for stable environments, lower values (300s) for active development.

3. **Private Repositories**: Store credentials securely and avoid committing them to version control.

4. **Network Configuration**: Configure multiple mirrors in environments with connectivity issues.

5. **Logging**: Use INFO level for normal operation, DEBUG for troubleshooting.
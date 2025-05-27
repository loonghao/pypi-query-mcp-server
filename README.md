# PyPI Query MCP Server

[![PyPI version](https://img.shields.io/pypi/v/pypi-query-mcp-server.svg)](https://pypi.org/project/pypi-query-mcp-server/)

A Model Context Protocol (MCP) server for querying PyPI package information, dependencies, and compatibility checking.

## Features

- 📦 Query PyPI package information (name, version, description, dependencies)
- 🐍 Python version compatibility checking
- 🔍 Dependency analysis and resolution
- 🏢 Private PyPI repository support
- ⚡ Fast async operations with caching
- 🛠️ Easy integration with MCP clients

## Installation

### Using uvx (recommended)

```bash
# Run directly with uvx
uvx pypi-query-mcp-server

# Or install and run with specific script
uvx --from pypi-query-mcp-server pypi-query-mcp
```

### Using pip

```bash
# Install from PyPI
pip install pypi-query-mcp-server

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
      "args": ["--from", "pypi-query-mcp-server", "pypi-query-mcp"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/simple/",
        "CACHE_TTL": "3600"
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
      "args": ["--from", "pypi-query-mcp-server", "pypi-query-mcp"],
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
      "args": ["--from", "pypi-query-mcp-server", "pypi-query-mcp"],
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
      "args": ["--from", "pypi-query-mcp-server", "pypi-query-mcp"],
      "env": {
        "PYPI_INDEX_URL": "https://pypi.org/simple/",
        "CACHE_TTL": "3600"
      }
    }
  }
}
```

### Environment Variables

- `PYPI_INDEX_URL`: PyPI index URL (default: https://pypi.org/simple/)
- `CACHE_TTL`: Cache time-to-live in seconds (default: 3600)
- `PRIVATE_PYPI_URL`: Private PyPI repository URL (optional)
- `PRIVATE_PYPI_USERNAME`: Private PyPI username (optional)
- `PRIVATE_PYPI_PASSWORD`: Private PyPI password (optional)

## Available MCP Tools

The server provides the following MCP tools:

1. **get_package_info** - Get comprehensive package information
2. **get_package_versions** - List all available versions for a package
3. **get_package_dependencies** - Analyze package dependencies
4. **check_package_python_compatibility** - Check Python version compatibility
5. **get_package_compatible_python_versions** - Get all compatible Python versions

## Usage Examples

Once configured in your MCP client (Claude Desktop, Cline, Cursor, Windsurf), you can ask questions like:

- "What are the dependencies of Django 4.2?"
- "Is FastAPI compatible with Python 3.9?"
- "Show me all versions of requests package"
- "What Python versions does numpy support?"
- "Get detailed information about the pandas package"

### Example Conversations

**User**: "Check if Django 4.2 is compatible with Python 3.9"

**AI Assistant**: I'll check Django 4.2's compatibility with Python 3.9 for you.

*[Uses get_package_info and check_package_python_compatibility tools]*

**User**: "What are the main dependencies of FastAPI?"

**AI Assistant**: Let me get the dependency information for FastAPI.

*[Uses get_package_dependencies tool]*

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
```

## Development Status

🎉 **Core functionality implemented and ready for use!**

Current implementation status:
- ✅ Basic project structure
- ✅ PyPI API client with caching
- ✅ MCP tools implementation (package info, versions, dependencies)
- ✅ Python version compatibility checking
- ✅ CI/CD pipeline with multi-platform testing
- ⏳ Private repository support (planned)
- ⏳ Advanced dependency analysis (planned)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

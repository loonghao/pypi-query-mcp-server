# PyPI Query MCP Server

A Model Context Protocol (MCP) server for querying PyPI package information, dependencies, and compatibility checking.

## Features

- 📦 Query PyPI package information (name, version, description, dependencies)
- 🐍 Python version compatibility checking
- 🔍 Dependency analysis and resolution
- 🏢 Private PyPI repository support
- ⚡ Fast async operations with caching
- 🛠️ Easy integration with MCP clients

## Quick Start

### Installation

```bash
# Install from PyPI (coming soon)
pip install pypi-query-mcp-server

# Or install from source
git clone https://github.com/loonghao/pypi-query-mcp-server.git
cd pypi-query-mcp-server
poetry install
```

### Usage

```bash
# Start the MCP server
pypi-query-mcp

# Or run directly with Python
python -m pypi_query_mcp.server
```

### Available MCP Tools

The server provides the following MCP tools:

1. **get_package_info** - Get comprehensive package information
2. **get_package_versions** - List all available versions for a package
3. **get_package_dependencies** - Analyze package dependencies
4. **check_package_python_compatibility** - Check Python version compatibility
5. **get_package_compatible_python_versions** - Get all compatible Python versions

### Example Usage with MCP Client

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

"""PyPI Query MCP Server.

A Model Context Protocol (MCP) server for querying PyPI package information,
dependencies, and compatibility checking.
"""

__version__ = "0.1.0"
__author__ = "Hal"
__email__ = "hal.long@outlook.com"

try:
    from pypi_query_mcp.server import mcp
    __all__ = ["mcp", "__version__"]
except ImportError:
    # Server dependencies not available (fastmcp, etc.)
    # Tools can still be imported individually
    __all__ = ["__version__"]

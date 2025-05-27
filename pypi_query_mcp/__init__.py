"""PyPI Query MCP Server.

A Model Context Protocol (MCP) server for querying PyPI package information,
dependencies, and compatibility checking.
"""

__version__ = "0.1.0"
__author__ = "Hal"
__email__ = "hal.long@outlook.com"

from pypi_query_mcp.server import mcp

__all__ = ["mcp", "__version__"]

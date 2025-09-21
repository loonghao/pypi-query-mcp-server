"""
Security module for mcpypi.

This module provides security utilities including input validation,
sanitization, and protection against common attack vectors.
"""

from .validation import (
    FilePathValidator,
    InputSanitizer,
    PackageNameValidator,
    SecurityValidationError,
    URLValidator,
    sanitize_for_logging,
    secure_validate_file_path,
    secure_validate_package_name,
    secure_validate_url,
)

from .input_validator import (
    MCPInputValidator,
    validate_package_name,
    validate_search_query,
    validate_tool_params,
)

# Credential management has been migrated to standard .pypirc/twine approach
# from .credentials import (...) - removed in favor of standard PyPI tooling

__all__ = [
    "secure_validate_package_name",
    "secure_validate_url",
    "secure_validate_file_path",
    "sanitize_for_logging",
    "SecurityValidationError",
    "PackageNameValidator",
    "URLValidator",
    "FilePathValidator",
    "InputSanitizer",
    "MCPInputValidator",
    "validate_package_name",
    "validate_search_query",
    "validate_tool_params",
]

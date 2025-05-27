"""Custom exceptions for PyPI Query MCP Server."""


class PyPIError(Exception):
    """Base exception for PyPI-related errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PackageNotFoundError(PyPIError):
    """Raised when a package is not found on PyPI."""

    def __init__(self, package_name: str):
        message = f"Package '{package_name}' not found on PyPI"
        super().__init__(message, status_code=404)
        self.package_name = package_name


class NetworkError(PyPIError):
    """Raised when network-related errors occur."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class RateLimitError(PyPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None):
        message = "PyPI API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class InvalidPackageNameError(PyPIError):
    """Raised when package name is invalid."""

    def __init__(self, package_name: str):
        message = f"Invalid package name: '{package_name}'"
        super().__init__(message, status_code=400)
        self.package_name = package_name


class PyPIServerError(PyPIError):
    """Raised when PyPI server returns a server error."""

    def __init__(self, status_code: int, message: str | None = None):
        if not message:
            message = f"PyPI server error (HTTP {status_code})"
        super().__init__(message, status_code=status_code)

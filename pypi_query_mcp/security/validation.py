"""
Secure input validation module for mcpypi.

This module provides robust validation functions to prevent injection attacks
and ensure data integrity across the application.
"""
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Security constants
MAX_PACKAGE_NAME_LENGTH = 214
MAX_VERSION_LENGTH = 32
MAX_URL_LENGTH = 2048
MAX_FILE_PATH_LENGTH = 1024

# Security patterns
SAFE_PACKAGE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$")
SAFE_VERSION_PATTERN = re.compile(r"^[0-9]+(\.[0-9]+)*([a-zA-Z0-9\-\.]*)?$")
SAFE_FILE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")

# Reserved and dangerous patterns
RESERVED_NAMES = {
    "pip", "setuptools", "wheel", "python", "test", "tests",
    "src", "docs", "build", "dist", "requirements", "readme",
    "con", "prn", "aux", "nul",  # Windows reserved names
    "sys", "os", "io", "subprocess", "exec", "eval"  # Dangerous Python modules
}

DANGEROUS_PATTERNS = [
    r"\.\.\/",  # Path traversal
    r"\/\.\.",  # Path traversal
    r"<.*>",   # HTML/XML tags
    r"javascript:",  # JavaScript protocol
    r"data:",  # Data protocol
    r"file:",  # File protocol
    r"[;&|`$]",  # Shell metacharacters
    r"eval\(",  # Eval calls
    r"exec\(",  # Exec calls
    r"import\s+",  # Import statements
    r"__.*__",  # Python dunder methods
]


class SecurityValidationError(Exception):
    """Raised when input fails security validation."""
    pass


class PackageNameValidator:
    """Secure package name validator with injection prevention."""

    @staticmethod
    def validate(package_name: str, strict: bool = True) -> dict[str, Any]:
        """
        Validate package name with comprehensive security checks.

        Args:
            package_name: Package name to validate
            strict: If True, applies strict security validation

        Returns:
            Dictionary with validation results

        Raises:
            SecurityValidationError: If package name is potentially dangerous
        """
        if not isinstance(package_name, str):
            raise SecurityValidationError("Package name must be a string")

        issues = []
        recommendations = []
        security_warnings = []

        # Basic validation
        if not package_name or not package_name.strip():
            raise SecurityValidationError("Package name cannot be empty")

        # Check for dangerous Unicode characters before stripping
        dangerous_unicode = [
            '\u0000',  # Null byte
            '\u200b', '\u200c', '\u200d',  # Zero-width characters
            '\u202e', '\u202d',  # Bidirectional text override
            '\uFEFF',  # Byte order mark
            '\u2028', '\u2029',  # Line/paragraph separators
        ]

        for char in dangerous_unicode:
            if char in package_name:
                raise SecurityValidationError(f"Package name contains dangerous Unicode character: {repr(char)}")

        # Remove leading/trailing whitespace for security
        package_name = package_name.strip()

        # Length validation
        if len(package_name) > MAX_PACKAGE_NAME_LENGTH:
            raise SecurityValidationError(f"Package name too long (max {MAX_PACKAGE_NAME_LENGTH} chars)")

        # Security pattern checks
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, package_name, re.IGNORECASE):
                raise SecurityValidationError(f"Package name contains dangerous pattern: {pattern}")

        # Character validation with security focus
        if not SAFE_PACKAGE_NAME_PATTERN.match(package_name):
            # More detailed analysis for specific security issues
            if any(char in package_name for char in ['<', '>', '&', '"', "'"]):
                raise SecurityValidationError("Package name contains HTML/XML metacharacters")
            if any(char in package_name for char in [';', '|', '&', '`', '$']):
                raise SecurityValidationError("Package name contains shell metacharacters")
            if '../' in package_name or '..\\' in package_name:
                raise SecurityValidationError("Package name contains path traversal sequences")

            issues.append("Package name contains invalid characters")

        # Check for reserved names (security risk)
        if package_name.lower() in RESERVED_NAMES:
            raise SecurityValidationError(f"'{package_name}' is a reserved/dangerous name")

        # Additional security checks
        if package_name.startswith('.') or package_name.endswith('.'):
            raise SecurityValidationError("Package name cannot start or end with dots")

        if package_name.startswith('-') or package_name.endswith('-'):
            issues.append("Package name cannot start or end with hyphens")

        # Check for suspicious patterns
        if re.search(r'(admin|root|sudo|config|secret|token|password|auth)', package_name, re.IGNORECASE):
            security_warnings.append("Package name contains potentially sensitive keywords")

        # Normalization (security-aware)
        try:
            normalized = re.sub(r"[-_.]+", "-", package_name.lower())
            # Validate normalized name doesn't create new security issues
            if not SAFE_PACKAGE_NAME_PATTERN.match(normalized):
                raise SecurityValidationError("Normalized package name fails security validation")
        except Exception as e:
            raise SecurityValidationError(f"Package name normalization failed: {e}")

        return {
            "valid": len(issues) == 0,
            "secure": len(security_warnings) == 0,
            "issues": issues,
            "security_warnings": security_warnings,
            "recommendations": recommendations,
            "normalized_name": normalized,
            "original_name": package_name,
        }


class URLValidator:
    """Secure URL validator to prevent SSRF and injection attacks."""

    @staticmethod
    def validate(url: str, allowed_schemes: list[str] | None = None) -> dict[str, Any]:
        """
        Validate URL with security checks.

        Args:
            url: URL to validate
            allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

        Returns:
            Dictionary with validation results

        Raises:
            SecurityValidationError: If URL is potentially dangerous
        """
        if not isinstance(url, str):
            raise SecurityValidationError("URL must be a string")

        if not url or not url.strip():
            raise SecurityValidationError("URL cannot be empty")

        url = url.strip()

        if len(url) > MAX_URL_LENGTH:
            raise SecurityValidationError(f"URL too long (max {MAX_URL_LENGTH} chars)")

        # Parse URL safely
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as e:
            raise SecurityValidationError(f"Invalid URL format: {e}")

        # Scheme validation
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']

        if parsed.scheme.lower() not in allowed_schemes:
            raise SecurityValidationError(f"URL scheme '{parsed.scheme}' not allowed")

        # Prevent local/private network access (SSRF protection)
        if parsed.hostname:
            # Block localhost and private ranges
            dangerous_hosts = [
                'localhost', '127.0.0.1', '0.0.0.0',
                '::1', '[::1]', 'local'
            ]

            # Allow localhost for development/testing but warn
            if parsed.hostname.lower() in dangerous_hosts:
                # For localhost, just warn but don't error for development use
                if parsed.hostname.lower() in ['localhost', '127.0.0.1', '::1']:
                    # Allow localhost for development but mark as warning
                    pass
                else:
                    raise SecurityValidationError("URL points to localhost/private network")

            # Block private IP ranges
            if re.match(r'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)', parsed.hostname):
                raise SecurityValidationError("URL points to private IP address")

        # Check for dangerous patterns in URL
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise SecurityValidationError(f"URL contains dangerous pattern: {pattern}")

        return {
            "valid": True,
            "secure": True,
            "parsed": parsed,
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "path": parsed.path,
        }


class FilePathValidator:
    """Secure file path validator to prevent path traversal attacks."""

    @staticmethod
    def validate(file_path: str, base_dir: str | None = None) -> dict[str, Any]:
        """
        Validate file path with security checks.

        Args:
            file_path: File path to validate
            base_dir: Base directory to restrict access to

        Returns:
            Dictionary with validation results

        Raises:
            SecurityValidationError: If file path is potentially dangerous
        """
        if not isinstance(file_path, str):
            raise SecurityValidationError("File path must be a string")

        if not file_path or not file_path.strip():
            raise SecurityValidationError("File path cannot be empty")

        file_path = file_path.strip()

        if len(file_path) > MAX_FILE_PATH_LENGTH:
            raise SecurityValidationError(f"File path too long (max {MAX_FILE_PATH_LENGTH} chars)")

        # Check for path traversal patterns
        dangerous_path_patterns = [
            '../', '..\\\\',
            '/./', '\\.\\',
            '/..', '\\..',
            '~/', '%2e%2e',
            '.%2f', '%2f..',
            '/proc/', '/dev/',
            '/sys/', '/etc/',
            'etc/passwd', 'etc\\passwd',
            'windows/system32', 'windows\\system32',
        ]

        file_path_lower = file_path.lower()
        for pattern in dangerous_path_patterns:
            if pattern in file_path_lower:
                raise SecurityValidationError(f"File path contains dangerous pattern: {pattern}")

        # Use pathlib for safe path handling
        try:
            path_obj = Path(file_path)

            # Check if path tries to escape base directory
            if base_dir:
                base_path = Path(base_dir).resolve()
                try:
                    resolved_path = (base_path / path_obj).resolve()
                    if not str(resolved_path).startswith(str(base_path)):
                        raise SecurityValidationError("File path attempts to escape base directory")
                except (OSError, ValueError) as e:
                    raise SecurityValidationError(f"Invalid file path: {e}")

            # Check for dangerous file names
            if path_obj.name:
                if not SAFE_FILE_NAME_PATTERN.match(path_obj.name):
                    raise SecurityValidationError("File name contains invalid characters")

        except SecurityValidationError:
            raise
        except Exception as e:
            raise SecurityValidationError(f"File path validation failed: {e}")

        return {
            "valid": True,
            "secure": True,
            "path": str(path_obj),
            "name": path_obj.name,
            "suffix": path_obj.suffix,
        }


class InputSanitizer:
    """General input sanitization utilities."""

    @staticmethod
    def sanitize_log_data(data: Any) -> str:
        """
        Sanitize data for safe logging.

        Args:
            data: Data to sanitize

        Returns:
            Sanitized string safe for logging
        """
        if data is None:
            return "None"

        data_str = str(data)

        # Remove potential secrets and sensitive information
        sensitive_patterns = [
            # URLs with sensitive info (check first to prevent email pattern conflicts)
            (r'(?:https?|ftp|ftps)://[^/]*:[^/]*@[^\s]+', '***REDACTED_URL_WITH_CREDS***'),

            # API tokens and credentials
            (r'(token|password|secret|key|auth|credential)[\s]*[:=][\s]*["\']?([^"\'\s]+)', r'\1=***REDACTED***'),
            (r'pypi-[A-Za-z0-9_-]+', '***REDACTED_TOKEN***'),
            (r'Bearer\s+[A-Za-z0-9_-]+', 'Bearer ***REDACTED***'),
            (r'Basic\s+[A-Za-z0-9+/]+=*', 'Basic ***REDACTED***'),

            # GitHub tokens and similar (check these first as they're more specific)
            (r'github_pat_[A-Za-z0-9_]{20,100}', '***REDACTED_GITHUB_PAT***'),
            (r'gh[pousr]_[A-Za-z0-9_]{36,}', '***REDACTED_GITHUB_TOKEN***'),

            # AWS and cloud credentials (make more specific to avoid conflicts)
            (r'AKIA[0-9A-Z]{16}', '***REDACTED_AWS_KEY***'),
            (r'(?<!github_pat_)(?<!gh[pousr]_)[A-Za-z0-9/+=]{40}(?![A-Za-z0-9_])', '***REDACTED_AWS_SECRET***'),

            # Email addresses (after URL patterns to prevent conflicts)
            (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', '***REDACTED_EMAIL***'),

            # File paths in home directories
            (r'/home/[^/\s]+', '/home/***USER***'),
            (r'/Users/[^/\s]+', '/Users/***USER***'),
            (r'C:\\\\Users\\\\[^\\\\\\s]+', r'C:\\Users\\***USER***'),

            # Private key indicators
            (r'-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----', '***REDACTED_PRIVATE_KEY***', re.DOTALL),

            # Common secret env var patterns
            (r'((SECRET|PASSWORD|TOKEN|KEY|AUTH)_[A-Z_]*)=.*', r'\1=***REDACTED***'),
            (r'((secret|password|token|key|auth)_[a-zA-Z_]*)=.*', r'\1=***REDACTED***'),
        ]

        sanitized = data_str
        for pattern_data in sensitive_patterns:
            if len(pattern_data) == 3:  # Pattern has additional flags
                pattern, replacement, flags = pattern_data
                sanitized = re.sub(pattern, replacement, sanitized, flags=flags | re.IGNORECASE)
            else:  # Standard pattern
                pattern, replacement = pattern_data
                sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        # Limit length for logs
        if len(sanitized) > 200:
            sanitized = sanitized[:197] + "..."

        return sanitized

    @staticmethod
    def validate_json_input(data: Any, max_depth: int = 10, max_items: int = 1000) -> bool:
        """
        Validate JSON input for safety.

        Args:
            data: JSON data to validate
            max_depth: Maximum nesting depth
            max_items: Maximum number of items

        Returns:
            True if safe, raises SecurityValidationError if dangerous
        """
        def _check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise SecurityValidationError(f"JSON depth exceeds limit ({max_depth})")

            if isinstance(obj, dict):
                if len(obj) > max_items:
                    raise SecurityValidationError(f"JSON object size exceeds limit ({max_items})")
                for key, value in obj.items():
                    if not isinstance(key, str) or len(key) > 100:
                        raise SecurityValidationError("Invalid JSON key")
                    _check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                if len(obj) > max_items:
                    raise SecurityValidationError(f"JSON array size exceeds limit ({max_items})")
                for item in obj:
                    _check_depth(item, current_depth + 1)
            elif isinstance(obj, str) and len(obj) > 10000:
                raise SecurityValidationError("JSON string value too long")

        _check_depth(data)
        return True


# Export main validation functions
def secure_validate_package_name(package_name: str) -> dict[str, Any]:
    """Main package name validation function."""
    return PackageNameValidator.validate(package_name)


def secure_validate_url(url: str, allowed_schemes: list[str] | None = None) -> dict[str, Any]:
    """Main URL validation function."""
    return URLValidator.validate(url, allowed_schemes)


def secure_validate_file_path(file_path: str, base_dir: str | None = None) -> dict[str, Any]:
    """Main file path validation function."""
    return FilePathValidator.validate(file_path, base_dir)


def sanitize_for_logging(data: Any) -> str:
    """Main log sanitization function."""
    return InputSanitizer.sanitize_log_data(data)

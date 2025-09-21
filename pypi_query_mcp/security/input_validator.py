"""Comprehensive input validation for MCP tool parameters."""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from .validation import SecurityValidationError, sanitize_for_logging

logger = logging.getLogger(__name__)


class MCPInputValidator:
    """Comprehensive input validator for MCP tool parameters."""

    # Common security patterns to block
    DANGEROUS_PATTERNS = [
        r'<script',
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'onload=',
        r'onerror=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess\.',
        r'os\.',
        r'sys\.',
        r'open\s*\(',
        r'file\s*\(',
    ]

    # Valid values for common parameters
    VALID_SORT_OPTIONS = ["relevance", "popularity", "recency", "quality", "name", "downloads"]
    VALID_PERIODS = ["day", "week", "month", "year"]
    VALID_MAINTENANCE_STATUS = ["active", "maintained", "stale", "abandoned"]
    VALID_PYTHON_VERSIONS = ["2.7", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"]

    @classmethod
    def validate_package_name(cls, package_name: str, field_name: str = "package_name") -> str:
        """Validate and sanitize package name."""
        if not package_name or not isinstance(package_name, str):
            raise SecurityValidationError(f"{field_name} must be a non-empty string")

        package_name = package_name.strip()

        if len(package_name) > 214:  # PyPI limit
            raise SecurityValidationError(f"{field_name} too long (max 214 characters)")

        if len(package_name) < 1:
            raise SecurityValidationError(f"{field_name} cannot be empty")

        # Basic PyPI package name format validation
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$', package_name):
            raise SecurityValidationError(f"{field_name} contains invalid characters")

        cls._check_dangerous_patterns(package_name, field_name)
        return package_name

    @classmethod
    def validate_search_query(cls, query: str, field_name: str = "query") -> str:
        """Validate and sanitize search query."""
        if not query or not isinstance(query, str):
            raise SecurityValidationError(f"{field_name} must be a non-empty string")

        query = query.strip()

        if len(query) > 1000:
            raise SecurityValidationError(f"{field_name} too long (max 1000 characters)")

        if len(query) < 1:
            raise SecurityValidationError(f"{field_name} cannot be empty")

        cls._check_dangerous_patterns(query, field_name)
        return query

    @classmethod
    def validate_version_string(cls, version: Optional[str], field_name: str = "version") -> Optional[str]:
        """Validate version string."""
        if version is None:
            return None

        if not isinstance(version, str):
            raise SecurityValidationError(f"{field_name} must be a string")

        version = version.strip()
        if not version:
            return None

        if len(version) > 100:
            raise SecurityValidationError(f"{field_name} too long (max 100 characters)")

        # Basic version format validation
        if not re.match(r'^[a-zA-Z0-9._+-]+$', version):
            raise SecurityValidationError(f"{field_name} contains invalid characters")

        cls._check_dangerous_patterns(version, field_name)
        return version

    @classmethod
    def validate_limit(cls, limit: int, max_limit: int = 100, field_name: str = "limit") -> int:
        """Validate limit parameter."""
        if not isinstance(limit, int):
            raise SecurityValidationError(f"{field_name} must be an integer")

        if limit <= 0:
            return 20  # Default

        if limit > max_limit:
            logger.warning(f"{field_name} {limit} exceeds maximum {max_limit}, capping")
            return max_limit

        return limit

    @classmethod
    def validate_sort_option(cls, sort_by: str, field_name: str = "sort_by") -> str:
        """Validate sort option."""
        if not isinstance(sort_by, str):
            raise SecurityValidationError(f"{field_name} must be a string")

        sort_by = sort_by.strip().lower()

        if sort_by not in cls.VALID_SORT_OPTIONS:
            logger.warning(f"Invalid {field_name} '{sort_by}', defaulting to 'relevance'")
            return "relevance"

        return sort_by

    @classmethod
    def validate_period(cls, period: str, field_name: str = "period") -> str:
        """Validate time period."""
        if not isinstance(period, str):
            raise SecurityValidationError(f"{field_name} must be a string")

        period = period.strip().lower()

        if period not in cls.VALID_PERIODS:
            logger.warning(f"Invalid {field_name} '{period}', defaulting to 'month'")
            return "month"

        return period

    @classmethod
    def validate_python_version(cls, python_version: Optional[str], field_name: str = "python_version") -> Optional[str]:
        """Validate Python version string."""
        if python_version is None:
            return None

        if not isinstance(python_version, str):
            raise SecurityValidationError(f"{field_name} must be a string")

        python_version = python_version.strip()
        if not python_version:
            return None

        # Allow common Python version patterns
        if not re.match(r'^[0-9]+\.[0-9]+(\.[0-9]+)?$', python_version):
            raise SecurityValidationError(f"{field_name} must be in format 'X.Y' or 'X.Y.Z'")

        return python_version

    @classmethod
    def validate_python_versions_list(cls, python_versions: Optional[List[str]], field_name: str = "python_versions") -> Optional[List[str]]:
        """Validate list of Python versions."""
        if python_versions is None:
            return None

        if not isinstance(python_versions, list):
            raise SecurityValidationError(f"{field_name} must be a list")

        if len(python_versions) > 20:  # Reasonable limit
            raise SecurityValidationError(f"{field_name} list too long (max 20 items)")

        validated_versions = []
        for version in python_versions:
            validated_version = cls.validate_python_version(version, f"{field_name} item")
            if validated_version:
                validated_versions.append(validated_version)

        return validated_versions if validated_versions else None

    @classmethod
    def validate_string_list(cls, string_list: Optional[List[str]], max_items: int = 50, max_length: int = 100, field_name: str = "string_list") -> Optional[List[str]]:
        """Validate list of strings."""
        if string_list is None:
            return None

        if not isinstance(string_list, list):
            raise SecurityValidationError(f"{field_name} must be a list")

        if len(string_list) > max_items:
            raise SecurityValidationError(f"{field_name} list too long (max {max_items} items)")

        validated_strings = []
        for item in string_list:
            if not isinstance(item, str):
                raise SecurityValidationError(f"{field_name} items must be strings")

            item = item.strip()
            if not item:
                continue

            if len(item) > max_length:
                raise SecurityValidationError(f"{field_name} item too long (max {max_length} characters)")

            cls._check_dangerous_patterns(item, f"{field_name} item")
            validated_strings.append(item)

        return validated_strings if validated_strings else None

    @classmethod
    def validate_boolean(cls, value: Any, default: bool = False, field_name: str = "boolean_field") -> bool:
        """Validate boolean value."""
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value_lower = value.strip().lower()
            if value_lower in ("true", "1", "yes", "on"):
                return True
            elif value_lower in ("false", "0", "no", "off"):
                return False

        logger.warning(f"Invalid {field_name} value '{value}', defaulting to {default}")
        return default

    @classmethod
    def validate_maintenance_status(cls, status: Optional[str], field_name: str = "maintenance_status") -> Optional[str]:
        """Validate maintenance status."""
        if status is None:
            return None

        if not isinstance(status, str):
            raise SecurityValidationError(f"{field_name} must be a string")

        status = status.strip().lower()

        if status not in cls.VALID_MAINTENANCE_STATUS:
            logger.warning(f"Invalid {field_name} '{status}', ignoring")
            return None

        return status

    @classmethod
    def _check_dangerous_patterns(cls, value: str, field_name: str) -> None:
        """Check for dangerous patterns in input."""
        value_lower = value.lower()

        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, value_lower):
                safe_value = sanitize_for_logging(value)
                logger.warning(f"Potentially dangerous pattern detected in {field_name}: {safe_value}")
                raise SecurityValidationError(f"{field_name} contains potentially dangerous content")

    @classmethod
    def validate_tool_parameters(cls, tool_name: str, **params) -> Dict[str, Any]:
        """Validate all parameters for a specific tool."""
        validated_params = {}

        # Common parameter validations
        if "package_name" in params:
            validated_params["package_name"] = cls.validate_package_name(params["package_name"])

        if "query" in params:
            validated_params["query"] = cls.validate_search_query(params["query"])

        if "version" in params:
            validated_params["version"] = cls.validate_version_string(params["version"])

        if "limit" in params:
            validated_params["limit"] = cls.validate_limit(params["limit"])

        if "sort_by" in params:
            validated_params["sort_by"] = cls.validate_sort_option(params["sort_by"])

        if "period" in params:
            validated_params["period"] = cls.validate_period(params["period"])

        if "python_version" in params:
            validated_params["python_version"] = cls.validate_python_version(params["python_version"])

        if "python_versions" in params:
            validated_params["python_versions"] = cls.validate_python_versions_list(params["python_versions"])

        if "target_python_version" in params:
            validated_params["target_python_version"] = cls.validate_python_version(params["target_python_version"], "target_python_version")

        # Boolean parameters
        boolean_fields = ["use_cache", "include_mirrors", "test_pypi", "include_dependencies", "security_scan", "compatibility_check"]
        for field in boolean_fields:
            if field in params:
                validated_params[field] = cls.validate_boolean(params[field], field_name=field)

        # String list parameters
        string_list_fields = ["licenses", "categories", "keywords"]
        for field in string_list_fields:
            if field in params:
                validated_params[field] = cls.validate_string_list(params[field], field_name=field)

        # Copy through other validated parameters
        for key, value in params.items():
            if key not in validated_params:
                # Log unvalidated parameters for monitoring
                safe_value = sanitize_for_logging(str(value)) if isinstance(value, str) else str(type(value))
                logger.debug(f"Unvalidated parameter {key} in {tool_name}: {safe_value}")
                validated_params[key] = value

        return validated_params


# Convenience functions for common validations
def validate_package_name(package_name: str) -> str:
    """Convenience function for package name validation."""
    return MCPInputValidator.validate_package_name(package_name)


def validate_search_query(query: str) -> str:
    """Convenience function for search query validation."""
    return MCPInputValidator.validate_search_query(query)


def validate_tool_params(tool_name: str, **params) -> Dict[str, Any]:
    """Convenience function for tool parameter validation."""
    return MCPInputValidator.validate_tool_parameters(tool_name, **params)
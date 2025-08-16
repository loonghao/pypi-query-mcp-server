"""PyPI metadata management tools for package configuration and visibility."""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIAuthenticationError,
    PyPIPermissionError,
    PyPIServerError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class PyPIMetadataClient:
    """Async client for PyPI metadata management operations."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        test_pypi: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize PyPI metadata client.

        Args:
            api_token: PyPI API token for authentication
            test_pypi: Whether to use TestPyPI instead of production PyPI
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_token = api_token
        self.test_pypi = test_pypi
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Configure base URLs
        if test_pypi:
            self.api_url = "https://test.pypi.org/pypi"
            self.manage_url = "https://test.pypi.org/manage"
            self.warehouse_api = "https://test.pypi.org/api/v1"
        else:
            self.api_url = "https://pypi.org/pypi"
            self.manage_url = "https://pypi.org/manage"
            self.warehouse_api = "https://pypi.org/api/v1"

        # HTTP client configuration
        headers = {
            "User-Agent": "pypi-query-mcp-server/0.1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.api_token:
            headers["Authorization"] = f"token {self.api_token}"

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=headers,
            follow_redirects=True,
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    def _validate_package_name(self, package_name: str) -> str:
        """Validate and normalize package name."""
        if not package_name or not package_name.strip():
            raise InvalidPackageNameError(package_name)

        # Basic validation
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$", package_name):
            raise InvalidPackageNameError(package_name)

        return package_name.strip()

    async def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                response = await self._client.request(method, url, **kwargs)
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise PyPIAuthenticationError(
                        "Authentication failed. Check your API token.",
                        status_code=401
                    )
                elif response.status_code == 403:
                    raise PyPIPermissionError(
                        "Permission denied. Check your account permissions.",
                        status_code=403
                    )
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    retry_after_int = int(retry_after) if retry_after else None
                    raise RateLimitError(retry_after_int)
                
                return response

            except httpx.TimeoutException as e:
                last_exception = NetworkError(f"Request timeout: {e}", e)
            except httpx.NetworkError as e:
                last_exception = NetworkError(f"Network error: {e}", e)
            except (PyPIAuthenticationError, PyPIPermissionError, RateLimitError):
                # Don't retry these errors
                raise
            except Exception as e:
                last_exception = NetworkError(f"Unexpected error: {e}", e)

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay * (2**attempt))

        # If we get here, all retries failed
        raise last_exception

    async def _verify_package_ownership(self, package_name: str) -> bool:
        """Verify that the authenticated user has permission to modify the package."""
        try:
            # Try to get package info first
            api_url = f"{self.api_url}/{package_name}/json"
            response = await self._make_request("GET", api_url)
            
            if response.status_code == 404:
                return False  # Package doesn't exist
            elif response.status_code != 200:
                return False  # Other error
            
            # For now, we assume if we have a valid token, we have permission
            # In a real implementation, we would check the package maintainers
            return self.api_token is not None
            
        except Exception:
            return False


async def update_package_metadata(
    package_name: str,
    description: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    classifiers: Optional[List[str]] = None,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Update package metadata including description, keywords, and classifiers.
    
    Note: PyPI metadata updates are typically done during package upload.
    This function provides guidance and validation for metadata changes.
    
    Args:
        package_name: Name of the package to update
        description: New package description
        keywords: List of keywords for the package
        classifiers: List of PyPI classifiers (e.g., programming language, license)
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        dry_run: If True, only validate changes without applying them
        
    Returns:
        Dictionary containing metadata update results and recommendations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        PyPIPermissionError: If user lacks permission to modify package
        NetworkError: For network-related errors
    """
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Updating metadata for {package_name}")
    
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    async with PyPIMetadataClient(api_token=api_token, test_pypi=test_pypi) as client:
        package_name = client._validate_package_name(package_name)
        
        try:
            # Get current package information
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to fetch package data")
            
            package_data = response.json()
            current_info = package_data.get("info", {})
            
            # Verify ownership if not dry run
            if not dry_run:
                has_permission = await client._verify_package_ownership(package_name)
                if not has_permission:
                    raise PyPIPermissionError(
                        "Insufficient permissions to modify package metadata"
                    )
            
            # Validate and prepare metadata updates
            metadata_updates = {}
            validation_errors = []
            recommendations = []
            
            # Process description
            if description is not None:
                description = description.strip()
                if len(description) > 2048:
                    validation_errors.append("Description exceeds 2048 characters")
                else:
                    metadata_updates["description"] = description
                    if len(description) < 50:
                        recommendations.append("Consider expanding the description for better discoverability")
            
            # Process keywords
            if keywords is not None:
                if not isinstance(keywords, list):
                    validation_errors.append("Keywords must be a list of strings")
                else:
                    # Validate keywords
                    valid_keywords = []
                    for keyword in keywords:
                        if isinstance(keyword, str) and keyword.strip():
                            clean_keyword = keyword.strip().lower()
                            if len(clean_keyword) <= 50 and re.match(r'^[a-zA-Z0-9\s\-_]+$', clean_keyword):
                                valid_keywords.append(clean_keyword)
                            else:
                                validation_errors.append(f"Invalid keyword: '{keyword}'")
                    
                    if len(valid_keywords) > 20:
                        validation_errors.append("Too many keywords (max 20)")
                        valid_keywords = valid_keywords[:20]
                    
                    metadata_updates["keywords"] = valid_keywords
                    if len(valid_keywords) < 3:
                        recommendations.append("Consider adding more keywords for better discoverability")
            
            # Process classifiers
            if classifiers is not None:
                if not isinstance(classifiers, list):
                    validation_errors.append("Classifiers must be a list of strings")
                else:
                    # Common PyPI classifiers for validation
                    common_classifier_prefixes = [
                        "Development Status",
                        "Intended Audience",
                        "License",
                        "Operating System",
                        "Programming Language",
                        "Topic",
                        "Framework",
                        "Environment",
                        "Natural Language",
                        "Typing",
                    ]
                    
                    valid_classifiers = []
                    for classifier in classifiers:
                        if isinstance(classifier, str) and classifier.strip():
                            clean_classifier = classifier.strip()
                            # Basic validation - check if it matches common patterns
                            if any(clean_classifier.startswith(prefix) for prefix in common_classifier_prefixes):
                                valid_classifiers.append(clean_classifier)
                            else:
                                # Still include it but add a warning
                                valid_classifiers.append(clean_classifier)
                                recommendations.append(f"Verify classifier format: '{clean_classifier}'")
                    
                    metadata_updates["classifiers"] = valid_classifiers
            
            # Compare with current metadata
            current_metadata = {
                "description": current_info.get("summary", ""),
                "keywords": current_info.get("keywords", "").split(",") if current_info.get("keywords") else [],
                "classifiers": current_info.get("classifiers", []),
            }
            
            # Calculate changes
            changes_detected = {}
            for key, new_value in metadata_updates.items():
                current_value = current_metadata.get(key)
                if new_value != current_value:
                    changes_detected[key] = {
                        "current": current_value,
                        "new": new_value,
                        "changed": True,
                    }
                else:
                    changes_detected[key] = {
                        "current": current_value,
                        "new": new_value,
                        "changed": False,
                    }
            
            result = {
                "package_name": package_name,
                "dry_run": dry_run,
                "validation_errors": validation_errors,
                "metadata_updates": metadata_updates,
                "changes_detected": changes_detected,
                "current_metadata": current_metadata,
                "recommendations": recommendations,
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Add implementation guidance
            if not dry_run and not validation_errors:
                result["implementation_note"] = {
                    "method": "package_upload",
                    "description": "PyPI metadata is updated during package upload, not via direct API",
                    "steps": [
                        "1. Update your package's setup.py, pyproject.toml, or setup.cfg with new metadata",
                        "2. Increment the package version",
                        "3. Build new distribution files (wheel and/or sdist)",
                        "4. Upload the new version to PyPI using twine or similar tool",
                    ],
                    "files_to_update": [
                        "setup.py (if using setuptools)",
                        "pyproject.toml (if using modern Python packaging)",
                        "setup.cfg (if using declarative setup.cfg)",
                    ],
                }
            elif dry_run:
                result["success"] = len(validation_errors) == 0
                result["message"] = "Dry run completed successfully" if not validation_errors else "Validation errors found"
            
            logger.info(f"Metadata update analysis completed for {package_name}")
            return result
            
        except (PackageNotFoundError, PyPIServerError, PyPIPermissionError):
            raise
        except Exception as e:
            logger.error(f"Error updating metadata for {package_name}: {e}")
            raise NetworkError(f"Failed to update metadata: {e}", e)


async def manage_package_urls(
    package_name: str,
    homepage: Optional[str] = None,
    documentation: Optional[str] = None,
    repository: Optional[str] = None,
    download_url: Optional[str] = None,
    bug_tracker: Optional[str] = None,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    validate_urls: bool = True,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Manage package URLs including homepage, documentation, and repository links.
    
    Args:
        package_name: Name of the package to update
        homepage: Package homepage URL
        documentation: Documentation URL
        repository: Source code repository URL
        download_url: Package download URL
        bug_tracker: Bug tracker URL
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        validate_urls: Whether to validate URL accessibility
        dry_run: If True, only validate changes without applying them
        
    Returns:
        Dictionary containing URL management results and validation
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        PyPIPermissionError: If user lacks permission to modify package
        NetworkError: For network-related errors
    """
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Managing URLs for {package_name}")
    
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    async with PyPIMetadataClient(api_token=api_token, test_pypi=test_pypi) as client:
        package_name = client._validate_package_name(package_name)
        
        try:
            # Get current package information
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to fetch package data")
            
            package_data = response.json()
            current_info = package_data.get("info", {})
            current_urls = current_info.get("project_urls", {}) or {}
            
            # Verify ownership if not dry run
            if not dry_run:
                has_permission = await client._verify_package_ownership(package_name)
                if not has_permission:
                    raise PyPIPermissionError(
                        "Insufficient permissions to modify package URLs"
                    )
            
            # Validate and prepare URL updates
            url_updates = {}
            validation_errors = []
            validation_results = {}
            recommendations = []
            
            # URL validation regex
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            urls_to_process = {
                "homepage": homepage,
                "documentation": documentation,
                "repository": repository,
                "download_url": download_url,
                "bug_tracker": bug_tracker,
            }
            
            # Process each URL
            for url_type, url_value in urls_to_process.items():
                if url_value is not None:
                    url_value = url_value.strip()
                    
                    if not url_value:
                        # Empty string means remove the URL
                        url_updates[url_type] = None
                        continue
                    
                    # Validate URL format
                    if not url_pattern.match(url_value):
                        validation_errors.append(f"Invalid {url_type} URL format: {url_value}")
                        continue
                    
                    # Check for HTTPS
                    if not url_value.startswith('https://'):
                        recommendations.append(f"Consider using HTTPS for {url_type}: {url_value}")
                    
                    url_updates[url_type] = url_value
                    
                    # Validate URL accessibility if requested
                    if validate_urls:
                        try:
                            # Quick HEAD request to check if URL is accessible
                            head_response = await client._client.head(url_value, timeout=10)
                            validation_results[url_type] = {
                                "url": url_value,
                                "accessible": head_response.status_code < 400,
                                "status_code": head_response.status_code,
                                "error": None,
                            }
                            
                            if head_response.status_code >= 400:
                                recommendations.append(f"{url_type} URL returned status {head_response.status_code}: {url_value}")
                                
                        except Exception as e:
                            validation_results[url_type] = {
                                "url": url_value,
                                "accessible": False,
                                "status_code": None,
                                "error": str(e),
                            }
                            recommendations.append(f"Could not validate {url_type} URL: {url_value}")
            
            # Compare with current URLs
            current_url_mapping = {
                "homepage": current_info.get("home_page", ""),
                "documentation": current_urls.get("Documentation", ""),
                "repository": current_urls.get("Repository", "") or current_urls.get("Source", ""),
                "download_url": current_info.get("download_url", ""),
                "bug_tracker": current_urls.get("Bug Tracker", "") or current_urls.get("Issues", ""),
            }
            
            # Calculate changes
            changes_detected = {}
            for url_type, new_url in url_updates.items():
                current_url = current_url_mapping.get(url_type, "")
                changes_detected[url_type] = {
                    "current": current_url,
                    "new": new_url,
                    "changed": new_url != current_url,
                }
            
            # Generate URL quality score
            total_urls = len([url for url in url_updates.values() if url])
            https_urls = len([url for url in url_updates.values() if url and url.startswith('https://')])
            accessible_urls = len([r for r in validation_results.values() if r.get('accessible', False)])
            
            url_quality_score = 0
            if total_urls > 0:
                url_quality_score = (https_urls * 0.3 + accessible_urls * 0.7) / total_urls * 100
            
            result = {
                "package_name": package_name,
                "dry_run": dry_run,
                "validation_errors": validation_errors,
                "url_updates": url_updates,
                "changes_detected": changes_detected,
                "current_urls": current_url_mapping,
                "validation_results": validation_results if validate_urls else {},
                "url_quality_score": round(url_quality_score, 1),
                "recommendations": recommendations,
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Add implementation guidance
            if not dry_run and not validation_errors:
                result["implementation_note"] = {
                    "method": "package_upload",
                    "description": "PyPI URLs are updated during package upload via project metadata",
                    "setup_py_example": {
                        "project_urls": {
                            "Homepage": url_updates.get("homepage", ""),
                            "Documentation": url_updates.get("documentation", ""),
                            "Repository": url_updates.get("repository", ""),
                            "Bug Tracker": url_updates.get("bug_tracker", ""),
                        }
                    },
                    "pyproject_toml_example": {
                        "[project.urls]": {
                            "Homepage": url_updates.get("homepage", ""),
                            "Documentation": url_updates.get("documentation", ""),
                            "Repository": url_updates.get("repository", ""),
                            "Bug-Tracker": url_updates.get("bug_tracker", ""),
                        }
                    },
                }
            elif dry_run:
                result["success"] = len(validation_errors) == 0
                result["message"] = "URL validation completed successfully" if not validation_errors else "URL validation errors found"
            
            logger.info(f"URL management analysis completed for {package_name}")
            return result
            
        except (PackageNotFoundError, PyPIServerError, PyPIPermissionError):
            raise
        except Exception as e:
            logger.error(f"Error managing URLs for {package_name}: {e}")
            raise NetworkError(f"Failed to manage URLs: {e}", e)


async def set_package_visibility(
    package_name: str,
    visibility: str,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    confirm_action: bool = False,
) -> Dict[str, Any]:
    """
    Set package visibility (private/public) for organization packages.
    
    Note: Package visibility management is primarily available for PyPI organizations
    and requires special permissions. Individual packages are public by default.
    
    Args:
        package_name: Name of the package to modify
        visibility: Visibility setting ("public" or "private")
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        confirm_action: Explicit confirmation required for visibility changes
        
    Returns:
        Dictionary containing visibility management results and limitations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        PyPIPermissionError: If user lacks permission to modify package
        NetworkError: For network-related errors
    """
    logger.info(f"Setting visibility for {package_name} to {visibility}")
    
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    visibility = visibility.lower().strip()
    if visibility not in ["public", "private"]:
        raise ValueError("Visibility must be 'public' or 'private'")
    
    async with PyPIMetadataClient(api_token=api_token, test_pypi=test_pypi) as client:
        package_name = client._validate_package_name(package_name)
        
        try:
            # Get current package information
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to fetch package data")
            
            package_data = response.json()
            current_info = package_data.get("info", {})
            
            # Check if confirmation is provided for private visibility changes
            if visibility == "private" and not confirm_action:
                return {
                    "package_name": package_name,
                    "success": False,
                    "error": "Explicit confirmation required for making packages private",
                    "current_visibility": "public",  # PyPI packages are public by default
                    "requested_visibility": visibility,
                    "confirmation_required": True,
                    "repository": "TestPyPI" if test_pypi else "PyPI",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            
            # Verify ownership
            has_permission = await client._verify_package_ownership(package_name)
            if not has_permission:
                raise PyPIPermissionError(
                    "Insufficient permissions to modify package visibility"
                )
            
            # Analyze current visibility status
            # PyPI packages are public by default, private packages require special setup
            current_visibility = "public"  # Default assumption
            
            # Check if package shows signs of being part of an organization
            author = current_info.get("author", "")
            maintainer = current_info.get("maintainer", "")
            home_page = current_info.get("home_page", "")
            
            organization_indicators = []
            if "@" not in author and len(author.split()) == 1:
                organization_indicators.append("Single-word author (possible organization)")
            if "github.com" in home_page and "/" in home_page:
                org_match = re.search(r'github\.com/([^/]+)/', home_page)
                if org_match:
                    organization_indicators.append(f"GitHub organization: {org_match.group(1)}")
            
            # Implementation limitations
            limitations = [
                "PyPI does not provide a direct API for visibility management",
                "Private packages are typically managed through PyPI organizations",
                "Individual user packages are public by default",
                "Visibility changes require organization-level permissions",
            ]
            
            result = {
                "package_name": package_name,
                "current_visibility": current_visibility,
                "requested_visibility": visibility,
                "organization_indicators": organization_indicators,
                "limitations": limitations,
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Provide guidance based on requested visibility
            if visibility == "private":
                result.update({
                    "success": False,
                    "implementation_note": {
                        "description": "Private packages require PyPI organization setup",
                        "requirements": [
                            "Package must be part of a PyPI organization",
                            "Organization must have private package features enabled",
                            "User must have organization admin permissions",
                        ],
                        "alternative_solutions": [
                            "Use private package repositories (e.g., Azure Artifacts, JFrog)",
                            "Deploy internal PyPI server (e.g., devpi, pypiserver)",
                            "Use git-based dependencies for private code",
                            "Consider GitHub Packages for private Python packages",
                        ],
                        "organization_setup": {
                            "steps": [
                                "1. Create or join a PyPI organization",
                                "2. Transfer package ownership to organization",
                                "3. Configure organization privacy settings",
                                "4. Manage access through organization members",
                            ],
                            "url": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/organizations/",
                        },
                    },
                })
            else:  # public
                result.update({
                    "success": True,
                    "message": "Package is already public (PyPI default)",
                    "note": "No action needed - PyPI packages are public by default",
                })
            
            # Add package information for context
            result["package_info"] = {
                "version": current_info.get("version", ""),
                "author": author,
                "maintainer": maintainer,
                "license": current_info.get("license", ""),
                "upload_time": current_info.get("upload_time", ""),
            }
            
            logger.info(f"Visibility analysis completed for {package_name}")
            return result
            
        except (PackageNotFoundError, PyPIServerError, PyPIPermissionError):
            raise
        except Exception as e:
            logger.error(f"Error setting visibility for {package_name}: {e}")
            raise NetworkError(f"Failed to set visibility: {e}", e)


async def manage_package_keywords(
    package_name: str,
    action: str,
    keywords: Optional[List[str]] = None,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Manage package keywords and search tags.
    
    Args:
        package_name: Name of the package to modify
        action: Action to perform ("add", "remove", "replace", "list")
        keywords: List of keywords to add/remove/replace
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        dry_run: If True, only simulate changes without applying them
        
    Returns:
        Dictionary containing keyword management results and recommendations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        PyPIPermissionError: If user lacks permission to modify package
        NetworkError: For network-related errors
    """
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Managing keywords for {package_name}: {action}")
    
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    action = action.lower().strip()
    if action not in ["add", "remove", "replace", "list"]:
        raise ValueError("Action must be 'add', 'remove', 'replace', or 'list'")
    
    if action in ["add", "remove", "replace"] and not keywords:
        raise ValueError(f"Keywords required for '{action}' action")
    
    async with PyPIMetadataClient(api_token=api_token, test_pypi=test_pypi) as client:
        package_name = client._validate_package_name(package_name)
        
        try:
            # Get current package information
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to fetch package data")
            
            package_data = response.json()
            current_info = package_data.get("info", {})
            
            # Verify ownership if not dry run and not just listing
            if not dry_run and action != "list":
                has_permission = await client._verify_package_ownership(package_name)
                if not has_permission:
                    raise PyPIPermissionError(
                        "Insufficient permissions to modify package keywords"
                    )
            
            # Extract current keywords
            current_keywords_str = current_info.get("keywords", "") or ""
            current_keywords = [kw.strip() for kw in current_keywords_str.split(",") if kw.strip()]
            
            # Also check classifiers for topic-related keywords
            classifiers = current_info.get("classifiers", [])
            topic_keywords = []
            for classifier in classifiers:
                if classifier.startswith("Topic ::"):
                    # Extract topic keywords from classifiers
                    topic = classifier.replace("Topic ::", "").strip()
                    topic_parts = [part.strip().lower().replace(" ", "-") for part in topic.split("::")]
                    topic_keywords.extend(topic_parts)
            
            result = {
                "package_name": package_name,
                "action": action,
                "dry_run": dry_run,
                "current_keywords": current_keywords,
                "topic_keywords": topic_keywords,
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            if action == "list":
                # Analyze keyword effectiveness
                keyword_analysis = {
                    "total_keywords": len(current_keywords),
                    "topic_derived_keywords": len(topic_keywords),
                    "keyword_quality": {},
                    "recommendations": [],
                }
                
                # Analyze each keyword
                for keyword in current_keywords:
                    quality_score = 0
                    issues = []
                    
                    # Length check
                    if len(keyword) < 3:
                        issues.append("Too short")
                    elif len(keyword) > 20:
                        issues.append("Too long")
                    else:
                        quality_score += 20
                    
                    # Character check
                    if re.match(r'^[a-zA-Z0-9\s\-_]+$', keyword):
                        quality_score += 20
                    else:
                        issues.append("Contains special characters")
                    
                    # Common programming terms
                    programming_terms = [
                        "python", "web", "api", "cli", "gui", "framework", "library",
                        "tool", "utility", "development", "testing", "data", "machine",
                        "learning", "ai", "automation", "database", "security"
                    ]
                    if any(term in keyword.lower() for term in programming_terms):
                        quality_score += 30
                    
                    # Uniqueness (not in topic keywords)
                    if keyword.lower() not in [tk.lower() for tk in topic_keywords]:
                        quality_score += 30
                    
                    keyword_analysis["keyword_quality"][keyword] = {
                        "score": quality_score,
                        "issues": issues,
                        "quality": "high" if quality_score >= 70 else "medium" if quality_score >= 40 else "low"
                    }
                
                # Generate recommendations
                if len(current_keywords) < 3:
                    keyword_analysis["recommendations"].append("Add more keywords for better discoverability")
                elif len(current_keywords) > 15:
                    keyword_analysis["recommendations"].append("Consider reducing keywords to focus on most relevant ones")
                
                low_quality_keywords = [kw for kw, data in keyword_analysis["keyword_quality"].items() if data["quality"] == "low"]
                if low_quality_keywords:
                    keyword_analysis["recommendations"].append(f"Improve or replace low-quality keywords: {', '.join(low_quality_keywords)}")
                
                result["keyword_analysis"] = keyword_analysis
                result["success"] = True
                
                logger.info(f"Listed {len(current_keywords)} keywords for {package_name}")
                return result
            
            # Process keyword modifications
            validation_errors = []
            new_keywords = current_keywords.copy()
            
            # Validate input keywords
            if keywords:
                processed_keywords = []
                for keyword in keywords:
                    if not isinstance(keyword, str):
                        validation_errors.append(f"Invalid keyword type: {type(keyword)}")
                        continue
                    
                    clean_keyword = keyword.strip().lower()
                    if not clean_keyword:
                        continue
                    
                    if len(clean_keyword) > 50:
                        validation_errors.append(f"Keyword too long: '{keyword}'")
                        continue
                    
                    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', clean_keyword):
                        validation_errors.append(f"Invalid keyword characters: '{keyword}'")
                        continue
                    
                    processed_keywords.append(clean_keyword)
                
                keywords = processed_keywords
            
            # Apply keyword actions
            changes_made = []
            
            if action == "add":
                for keyword in keywords:
                    if keyword not in [kw.lower() for kw in new_keywords]:
                        new_keywords.append(keyword)
                        changes_made.append(f"Added: {keyword}")
                    else:
                        changes_made.append(f"Already exists: {keyword}")
            
            elif action == "remove":
                for keyword in keywords:
                    # Case-insensitive removal
                    original_keywords = new_keywords.copy()
                    new_keywords = [kw for kw in new_keywords if kw.lower() != keyword.lower()]
                    if len(new_keywords) < len(original_keywords):
                        changes_made.append(f"Removed: {keyword}")
                    else:
                        changes_made.append(f"Not found: {keyword}")
            
            elif action == "replace":
                new_keywords = keywords
                changes_made.append(f"Replaced all keywords with {len(keywords)} new keywords")
            
            # Validate final keyword list
            if len(new_keywords) > 20:
                validation_errors.append("Too many keywords (max 20)")
                new_keywords = new_keywords[:20]
            
            # Calculate keyword quality score
            keyword_quality_score = 0
            if new_keywords:
                valid_keywords = len([kw for kw in new_keywords if len(kw) >= 3 and len(kw) <= 20])
                unique_keywords = len(set(kw.lower() for kw in new_keywords))
                keyword_quality_score = (valid_keywords * 0.5 + unique_keywords * 0.5) / len(new_keywords) * 100
            
            result.update({
                "validation_errors": validation_errors,
                "keywords_before": current_keywords,
                "keywords_after": new_keywords,
                "changes_made": changes_made,
                "keyword_quality_score": round(keyword_quality_score, 1),
                "changes_detected": new_keywords != current_keywords,
            })
            
            # Add implementation guidance
            if not dry_run and not validation_errors and new_keywords != current_keywords:
                result["implementation_note"] = {
                    "method": "package_upload",
                    "description": "Keywords are updated during package upload via metadata",
                    "setup_py_example": f"keywords='{', '.join(new_keywords)}'",
                    "pyproject_toml_example": f"keywords = {json.dumps(new_keywords)}",
                    "setup_cfg_example": f"keywords = {', '.join(new_keywords)}",
                }
            elif dry_run:
                result["success"] = len(validation_errors) == 0
                result["message"] = "Keyword changes validated successfully" if not validation_errors else "Keyword validation errors found"
            
            # Generate recommendations
            recommendations = []
            if len(new_keywords) < 3:
                recommendations.append("Consider adding more keywords for better discoverability")
            
            # Check for redundancy with topic keywords
            redundant_keywords = [kw for kw in new_keywords if kw.lower() in [tk.lower() for tk in topic_keywords]]
            if redundant_keywords:
                recommendations.append(f"Keywords already covered by classifiers: {', '.join(redundant_keywords)}")
            
            # Suggest related keywords based on package description
            description = current_info.get("summary", "") or current_info.get("description", "")
            if description:
                description_words = re.findall(r'\b[a-zA-Z]{4,}\b', description.lower())
                common_tech_words = [
                    "python", "web", "api", "cli", "framework", "library", "tool",
                    "data", "analysis", "machine", "learning", "automation", "testing"
                ]
                suggested = [word for word in description_words if word in common_tech_words and word not in [kw.lower() for kw in new_keywords]]
                if suggested:
                    recommendations.append(f"Consider adding keywords from description: {', '.join(set(suggested[:5]))}")
            
            result["recommendations"] = recommendations
            
            logger.info(f"Keyword management completed for {package_name}")
            return result
            
        except (PackageNotFoundError, PyPIServerError, PyPIPermissionError):
            raise
        except Exception as e:
            logger.error(f"Error managing keywords for {package_name}: {e}")
            raise NetworkError(f"Failed to manage keywords: {e}", e)
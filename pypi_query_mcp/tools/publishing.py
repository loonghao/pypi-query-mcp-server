"""PyPI account and publishing tools for package management and distribution."""

import asyncio
import base64
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx

from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIAuthenticationError,
    PyPIPermissionError,
    PyPIServerError,
    PyPIUploadError,
    RateLimitError,
)


class PyPIPublishingClient:
    """Async client for PyPI publishing and account management operations."""

    def __init__(
        self,
        api_token: Optional[str] = None,
        test_pypi: bool = False,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        """Initialize PyPI publishing client.

        Args:
            api_token: PyPI API token for authentication
            test_pypi: Whether to use TestPyPI instead of production PyPI
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.api_token = api_token or os.getenv("PYPI_API_TOKEN")
        self.test_pypi = test_pypi
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Configure base URLs
        if test_pypi:
            self.upload_url = "https://test.pypi.org/legacy/"
            self.api_url = "https://test.pypi.org/pypi"
            self.account_url = "https://test.pypi.org"
        else:
            self.upload_url = "https://upload.pypi.org/legacy/"
            self.api_url = "https://pypi.org/pypi"
            self.account_url = "https://pypi.org"

        # HTTP client configuration
        headers = {
            "User-Agent": "pypi-query-mcp-server/0.1.0",
            "Accept": "application/json",
        }
        
        if self.api_token:
            # Use token authentication
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


async def upload_package_to_pypi(
    distribution_paths: List[str],
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    skip_existing: bool = True,
    verify_uploads: bool = True,
) -> Dict[str, Any]:
    """
    Upload package distributions to PyPI or TestPyPI.
    
    Args:
        distribution_paths: List of paths to distribution files (.whl, .tar.gz)
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to upload to TestPyPI instead of production PyPI
        skip_existing: Skip files that already exist on PyPI
        verify_uploads: Verify uploads after completion
        
    Returns:
        Dictionary containing upload results and metadata
        
    Raises:
        PyPIAuthenticationError: If authentication fails
        PyPIUploadError: If upload operations fail
        NetworkError: For network-related errors
    """
    logger.info(f"Starting upload of {len(distribution_paths)} distributions to {'TestPyPI' if test_pypi else 'PyPI'}")
    
    if not distribution_paths:
        raise ValueError("No distribution paths provided")
    
    # Validate all distribution files exist
    missing_files = []
    valid_files = []
    
    for path_str in distribution_paths:
        path = Path(path_str)
        if not path.exists():
            missing_files.append(str(path))
        elif not path.suffix.lower() in ['.whl', '.tar.gz']:
            logger.warning(f"Skipping non-distribution file: {path}")
        else:
            valid_files.append(path)
    
    if missing_files:
        raise FileNotFoundError(f"Distribution files not found: {missing_files}")
    
    if not valid_files:
        raise ValueError("No valid distribution files found")
    
    results = {
        "upload_results": [],
        "total_files": len(valid_files),
        "successful_uploads": 0,
        "failed_uploads": 0,
        "skipped_uploads": 0,
        "target_repository": "TestPyPI" if test_pypi else "PyPI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    async with PyPIPublishingClient(
        api_token=api_token, 
        test_pypi=test_pypi
    ) as client:
        
        # Verify authentication
        try:
            auth_result = await check_pypi_credentials(api_token, test_pypi)
            if not auth_result.get("valid", False):
                raise PyPIAuthenticationError("Invalid API token")
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            raise PyPIAuthenticationError(f"Authentication failed: {e}")
        
        # Upload each distribution file
        for dist_file in valid_files:
            file_result = {
                "filename": dist_file.name,
                "filepath": str(dist_file),
                "size_bytes": dist_file.stat().st_size,
                "status": "pending",
                "error": None,
                "upload_time": None,
            }
            
            try:
                logger.info(f"Uploading {dist_file.name}...")
                
                # Prepare upload data
                with open(dist_file, 'rb') as f:
                    file_content = f.read()
                
                # Create multipart form data for upload
                files = {
                    'content': (dist_file.name, file_content, 'application/octet-stream')
                }
                
                data = {
                    ':action': 'file_upload',
                    'protocol_version': '1',
                }
                
                # Make upload request
                upload_url = urljoin(client.upload_url, "")
                response = await client._make_request(
                    "POST",
                    upload_url,
                    files=files,
                    data=data,
                )
                
                if response.status_code == 200:
                    file_result["status"] = "success"
                    file_result["upload_time"] = datetime.now(timezone.utc).isoformat()
                    results["successful_uploads"] += 1
                    logger.info(f"Successfully uploaded {dist_file.name}")
                    
                elif response.status_code == 409 and skip_existing:
                    file_result["status"] = "skipped"
                    file_result["error"] = "File already exists"
                    results["skipped_uploads"] += 1
                    logger.info(f"Skipped {dist_file.name} (already exists)")
                    
                else:
                    error_msg = f"Upload failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        error_msg = response.text or error_msg
                    
                    file_result["status"] = "failed"
                    file_result["error"] = error_msg
                    results["failed_uploads"] += 1
                    logger.error(f"Failed to upload {dist_file.name}: {error_msg}")
                
            except Exception as e:
                file_result["status"] = "failed"
                file_result["error"] = str(e)
                results["failed_uploads"] += 1
                logger.error(f"Exception during upload of {dist_file.name}: {e}")
            
            results["upload_results"].append(file_result)
        
        # Verify uploads if requested
        if verify_uploads and results["successful_uploads"] > 0:
            logger.info("Verifying uploads...")
            verification_results = []
            
            for file_result in results["upload_results"]:
                if file_result["status"] == "success":
                    # Extract package name from filename
                    filename = file_result["filename"]
                    if filename.endswith('.whl'):
                        # Parse wheel filename: name-version-python-abi-platform.whl
                        parts = filename[:-4].split('-')
                        if len(parts) >= 2:
                            package_name = parts[0]
                        else:
                            continue
                    elif filename.endswith('.tar.gz'):
                        # Parse sdist filename: name-version.tar.gz
                        parts = filename[:-7].split('-')
                        if len(parts) >= 2:
                            package_name = parts[0]
                        else:
                            continue
                    else:
                        continue
                    
                    try:
                        # Check if package is now available
                        verify_url = f"{client.api_url}/{package_name}/json"
                        verify_response = await client._make_request("GET", verify_url)
                        
                        if verify_response.status_code == 200:
                            verification_results.append({
                                "filename": filename,
                                "package_name": package_name,
                                "verified": True,
                            })
                        else:
                            verification_results.append({
                                "filename": filename,
                                "package_name": package_name,
                                "verified": False,
                                "error": f"Package not found (status: {verify_response.status_code})",
                            })
                    except Exception as e:
                        verification_results.append({
                            "filename": filename,
                            "package_name": package_name,
                            "verified": False,
                            "error": str(e),
                        })
            
            results["verification_results"] = verification_results
    
    # Generate summary
    results["summary"] = {
        "total_processed": len(valid_files),
        "successful": results["successful_uploads"],
        "failed": results["failed_uploads"],
        "skipped": results["skipped_uploads"],
        "success_rate": results["successful_uploads"] / len(valid_files) * 100 if valid_files else 0,
    }
    
    logger.info(f"Upload completed: {results['summary']}")
    return results


async def check_pypi_credentials(
    api_token: Optional[str] = None,
    test_pypi: bool = False,
) -> Dict[str, Any]:
    """
    Validate PyPI API token and credentials.
    
    Args:
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to check against TestPyPI instead of production PyPI
        
    Returns:
        Dictionary containing credential validation results
        
    Raises:
        PyPIAuthenticationError: If credential validation fails
        NetworkError: For network-related errors
    """
    logger.info(f"Checking {'TestPyPI' if test_pypi else 'PyPI'} credentials")
    
    token = api_token or os.getenv("PYPI_API_TOKEN")
    if not token:
        return {
            "valid": False,
            "error": "No API token provided",
            "source": "environment_variable" if not api_token else "parameter",
            "test_pypi": test_pypi,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    # Validate token format
    if not token.startswith("pypi-"):
        return {
            "valid": False,
            "error": "Invalid token format (should start with 'pypi-')",
            "test_pypi": test_pypi,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async with PyPIPublishingClient(api_token=token, test_pypi=test_pypi) as client:
        try:
            # Try to access user account information
            if test_pypi:
                # TestPyPI doesn't have a reliable user info endpoint, try upload check instead
                test_url = "https://test.pypi.org/legacy/"
            else:
                test_url = "https://upload.pypi.org/legacy/"
            
            # Make a simple authenticated request
            response = await client._make_request("GET", test_url)
            
            if response.status_code in [200, 405]:  # 405 is expected for GET on upload endpoint
                return {
                    "valid": True,
                    "token_format": "valid",
                    "repository": "TestPyPI" if test_pypi else "PyPI",
                    "test_pypi": test_pypi,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            elif response.status_code == 401:
                return {
                    "valid": False,
                    "error": "Invalid or expired API token",
                    "status_code": 401,
                    "test_pypi": test_pypi,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            elif response.status_code == 403:
                return {
                    "valid": False,
                    "error": "API token lacks required permissions",
                    "status_code": 403,
                    "test_pypi": test_pypi,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "valid": False,
                    "error": f"Unexpected response: {response.status_code}",
                    "status_code": response.status_code,
                    "test_pypi": test_pypi,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                
        except PyPIAuthenticationError as e:
            return {
                "valid": False,
                "error": str(e),
                "status_code": e.status_code,
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error checking credentials: {e}")
            return {
                "valid": False,
                "error": f"Credential check failed: {e}",
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }


async def get_pypi_upload_history(
    package_name: str,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Get upload history for a PyPI package.
    
    Args:
        package_name: Name of the package to get upload history for
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to check TestPyPI instead of production PyPI
        limit: Maximum number of uploads to return
        
    Returns:
        Dictionary containing upload history and metadata
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    logger.info(f"Getting upload history for {package_name} on {'TestPyPI' if test_pypi else 'PyPI'}")
    
    async with PyPIPublishingClient(api_token=api_token, test_pypi=test_pypi) as client:
        try:
            # Get package information
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, f"Failed to fetch package data")
            
            package_data = response.json()
            
            # Extract upload history from releases
            upload_history = []
            releases = package_data.get("releases", {})
            
            for version, files in releases.items():
                for file_info in files:
                    upload_history.append({
                        "version": version,
                        "filename": file_info.get("filename", ""),
                        "upload_time": file_info.get("upload_time", ""),
                        "upload_time_iso": file_info.get("upload_time_iso_8601", ""),
                        "size": file_info.get("size", 0),
                        "python_version": file_info.get("python_version", ""),
                        "packagetype": file_info.get("packagetype", ""),
                        "md5_digest": file_info.get("md5_digest", ""),
                        "sha256_digest": file_info.get("digests", {}).get("sha256", ""),
                        "url": file_info.get("url", ""),
                        "yanked": file_info.get("yanked", False),
                        "yanked_reason": file_info.get("yanked_reason", ""),
                    })
            
            # Sort by upload time (newest first)
            upload_history.sort(
                key=lambda x: x.get("upload_time_iso", x.get("upload_time", "")),
                reverse=True
            )
            
            # Apply limit
            if limit and limit > 0:
                upload_history = upload_history[:limit]
            
            # Calculate statistics
            total_uploads = len(upload_history)
            package_types = {}
            total_size = 0
            yanked_count = 0
            
            for upload in upload_history:
                pkg_type = upload.get("packagetype", "unknown")
                package_types[pkg_type] = package_types.get(pkg_type, 0) + 1
                total_size += upload.get("size", 0)
                if upload.get("yanked", False):
                    yanked_count += 1
            
            # Get latest version info
            info = package_data.get("info", {})
            
            result = {
                "package_name": package_name,
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "upload_history": upload_history,
                "statistics": {
                    "total_uploads": total_uploads,
                    "total_versions": len(releases),
                    "total_size_bytes": total_size,
                    "yanked_uploads": yanked_count,
                    "package_types": package_types,
                },
                "package_info": {
                    "current_version": info.get("version", ""),
                    "author": info.get("author", ""),
                    "maintainer": info.get("maintainer", ""),
                    "license": info.get("license", ""),
                    "homepage": info.get("home_page", ""),
                },
                "limit_applied": limit,
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            logger.info(f"Retrieved {total_uploads} upload records for {package_name}")
            return result
            
        except (PackageNotFoundError, PyPIServerError):
            raise
        except Exception as e:
            logger.error(f"Error getting upload history for {package_name}: {e}")
            raise NetworkError(f"Failed to get upload history: {e}", e)


async def delete_pypi_release(
    package_name: str,
    version: str,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
    confirm_deletion: bool = False,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Delete a specific release from PyPI (with safety checks).
    
    Note: PyPI deletion is very restricted and typically only available to package owners
    within a limited time window after upload.
    
    Args:
        package_name: Name of the package
        version: Version to delete
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        confirm_deletion: Explicit confirmation required for actual deletion
        dry_run: If True, only simulate the deletion without actually performing it
        
    Returns:
        Dictionary containing deletion results and safety information
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package/version is not found
        PyPIPermissionError: If deletion is not permitted
        NetworkError: For network-related errors
    """
    package_name = package_name.strip()
    version = version.strip()
    
    if not package_name:
        raise InvalidPackageNameError(package_name)
    if not version:
        raise ValueError("Version cannot be empty")
    
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Deleting {package_name}=={version} from {'TestPyPI' if test_pypi else 'PyPI'}")
    
    # Safety checks
    safety_warnings = []
    
    # Check if this is production PyPI
    if not test_pypi:
        safety_warnings.append("PRODUCTION PyPI deletion - this action is irreversible!")
    
    # Check for confirmation
    if not confirm_deletion and not dry_run:
        safety_warnings.append("Explicit confirmation required for deletion")
        return {
            "success": False,
            "dry_run": dry_run,
            "safety_warnings": safety_warnings,
            "error": "Deletion not confirmed. Set confirm_deletion=True to proceed.",
            "package_name": package_name,
            "version": version,
            "test_pypi": test_pypi,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async with PyPIPublishingClient(api_token=api_token, test_pypi=test_pypi) as client:
        try:
            # First, verify the release exists
            api_url = f"{client.api_url}/{package_name}/{version}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(f"{package_name}=={version}")
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to verify release")
            
            release_data = response.json()
            release_info = release_data.get("info", {})
            
            # Analyze release details
            upload_time = release_info.get("upload_time", "")
            files = release_data.get("urls", [])
            file_count = len(files)
            
            # Check upload recency (PyPI typically allows deletion only within hours)
            if upload_time:
                try:
                    from datetime import datetime
                    upload_dt = datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - upload_dt).total_seconds() / 3600
                    
                    if age_hours > 24:
                        safety_warnings.append(f"Release is {age_hours:.1f} hours old - deletion may not be permitted")
                except:
                    safety_warnings.append("Could not determine upload time")
            
            if file_count > 1:
                safety_warnings.append(f"Release contains {file_count} distribution files")
            
            result = {
                "package_name": package_name,
                "version": version,
                "dry_run": dry_run,
                "safety_warnings": safety_warnings,
                "release_info": {
                    "upload_time": upload_time,
                    "file_count": file_count,
                    "files": [f.get("filename", "") for f in files],
                    "author": release_info.get("author", ""),
                    "summary": release_info.get("summary", ""),
                },
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            if dry_run:
                result.update({
                    "success": True,
                    "action": "dry_run_completed",
                    "message": "Dry run completed successfully. Release exists and could potentially be deleted.",
                })
                logger.info(f"DRY RUN: {package_name}=={version} deletion simulation completed")
                return result
            
            # Attempt actual deletion
            # Note: PyPI's deletion API is very restricted and may not be available
            delete_url = f"{client.api_url}/{package_name}/{version}/"
            
            try:
                delete_response = await client._make_request("DELETE", delete_url)
                
                if delete_response.status_code in [200, 204]:
                    result.update({
                        "success": True,
                        "action": "deleted",
                        "message": f"Successfully deleted {package_name}=={version}",
                    })
                    logger.info(f"Successfully deleted {package_name}=={version}")
                    
                elif delete_response.status_code == 403:
                    result.update({
                        "success": False,
                        "action": "permission_denied",
                        "error": "Deletion not permitted - insufficient permissions or time window expired",
                    })
                    
                elif delete_response.status_code == 405:
                    result.update({
                        "success": False,
                        "action": "not_supported",
                        "error": "Deletion is not supported or available for this package/version",
                    })
                    
                else:
                    error_msg = f"Deletion failed with status {delete_response.status_code}"
                    try:
                        error_data = delete_response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        pass
                    
                    result.update({
                        "success": False,
                        "action": "failed",
                        "error": error_msg,
                        "status_code": delete_response.status_code,
                    })
                    
            except PyPIPermissionError as e:
                result.update({
                    "success": False,
                    "action": "permission_denied",
                    "error": str(e),
                })
            except Exception as e:
                result.update({
                    "success": False,
                    "action": "error",
                    "error": f"Deletion attempt failed: {e}",
                })
            
            return result
            
        except (PackageNotFoundError, PyPIServerError):
            raise
        except Exception as e:
            logger.error(f"Error deleting release {package_name}=={version}: {e}")
            raise NetworkError(f"Failed to delete release: {e}", e)


async def manage_pypi_maintainers(
    package_name: str,
    action: str,
    username: Optional[str] = None,
    api_token: Optional[str] = None,
    test_pypi: bool = False,
) -> Dict[str, Any]:
    """
    Manage package maintainers (add/remove/list).
    
    Note: Maintainer management requires package owner permissions.
    
    Args:
        package_name: Name of the package
        action: Action to perform ('list', 'add', 'remove')
        username: Username to add/remove (required for add/remove actions)
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        
    Returns:
        Dictionary containing maintainer management results
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        PyPIPermissionError: If action is not permitted
        NetworkError: For network-related errors
    """
    package_name = package_name.strip()
    if not package_name:
        raise InvalidPackageNameError(package_name)
    
    action = action.lower().strip()
    if action not in ['list', 'add', 'remove']:
        raise ValueError(f"Invalid action '{action}'. Must be 'list', 'add', or 'remove'")
    
    if action in ['add', 'remove'] and not username:
        raise ValueError(f"Username required for '{action}' action")
    
    logger.info(f"Managing maintainers for {package_name} on {'TestPyPI' if test_pypi else 'PyPI'}: {action}")
    
    async with PyPIPublishingClient(api_token=api_token, test_pypi=test_pypi) as client:
        try:
            # First verify package exists
            api_url = f"{client.api_url}/{package_name}/json"
            response = await client._make_request("GET", api_url)
            
            if response.status_code == 404:
                raise PackageNotFoundError(package_name)
            elif response.status_code != 200:
                raise PyPIServerError(response.status_code, "Failed to fetch package data")
            
            package_data = response.json()
            info = package_data.get("info", {})
            
            # Extract current maintainer information
            current_maintainers = []
            
            # Get author information
            author = info.get("author", "")
            author_email = info.get("author_email", "")
            if author:
                current_maintainers.append({
                    "type": "author",
                    "name": author,
                    "email": author_email,
                })
            
            # Get maintainer information
            maintainer = info.get("maintainer", "")
            maintainer_email = info.get("maintainer_email", "")
            if maintainer:
                current_maintainers.append({
                    "type": "maintainer", 
                    "name": maintainer,
                    "email": maintainer_email,
                })
            
            result = {
                "package_name": package_name,
                "action": action,
                "current_maintainers": current_maintainers,
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            if action == "list":
                result.update({
                    "success": True,
                    "maintainer_count": len(current_maintainers),
                    "package_info": {
                        "version": info.get("version", ""),
                        "summary": info.get("summary", ""),
                        "license": info.get("license", ""),
                    },
                })
                logger.info(f"Listed {len(current_maintainers)} maintainers for {package_name}")
                return result
            
            # For add/remove actions, we need to use PyPI's management interface
            # Note: This is typically done through the web interface, not API
            
            result.update({
                "username": username,
                "success": False,
                "error": f"Maintainer {action} operations are not supported via API",
                "alternative_method": {
                    "description": f"Use PyPI web interface to {action} maintainers",
                    "url": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/project/{package_name}/collaborators/",
                    "instructions": [
                        "1. Log in to PyPI web interface",
                        "2. Navigate to project management page",
                        "3. Go to 'Collaborators' section",
                        f"4. {action.title()} the specified user",
                    ],
                },
            })
            
            # In a real implementation, you might attempt to use undocumented APIs
            # or web scraping, but this is not recommended due to stability concerns
            
            return result
            
        except (PackageNotFoundError, PyPIServerError):
            raise
        except Exception as e:
            logger.error(f"Error managing maintainers for {package_name}: {e}")
            raise NetworkError(f"Failed to manage maintainers: {e}", e)


async def get_pypi_account_info(
    api_token: Optional[str] = None,
    test_pypi: bool = False,
) -> Dict[str, Any]:
    """
    Get PyPI account information, quotas, and limits.
    
    Args:
        api_token: PyPI API token (or use PYPI_API_TOKEN env var)
        test_pypi: Whether to use TestPyPI instead of production PyPI
        
    Returns:
        Dictionary containing account information and limitations
        
    Raises:
        PyPIAuthenticationError: If authentication fails
        NetworkError: For network-related errors
    """
    logger.info(f"Getting account information for {'TestPyPI' if test_pypi else 'PyPI'}")
    
    async with PyPIPublishingClient(api_token=api_token, test_pypi=test_pypi) as client:
        try:
            # Verify credentials first
            cred_result = await check_pypi_credentials(api_token, test_pypi)
            if not cred_result.get("valid", False):
                raise PyPIAuthenticationError("Invalid credentials")
            
            result = {
                "repository": "TestPyPI" if test_pypi else "PyPI",
                "credentials": cred_result,
                "test_pypi": test_pypi,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Note: PyPI doesn't provide a comprehensive account info API
            # Most account information is only available through the web interface
            
            # Try to get basic account information through available endpoints
            account_info = {
                "api_token_valid": True,
                "token_permissions": "upload",  # Basic assumption for upload tokens
                "account_limitations": {
                    "note": "PyPI does not provide detailed account info via API",
                    "general_limits": {
                        "upload_size_limit": "60 MB per file",
                        "project_name_length": "214 characters maximum",
                        "version_string_length": "64 characters maximum",
                        "description_length": "No specific limit",
                    },
                    "rate_limits": {
                        "uploads": "Varies by account age and reputation",
                        "api_requests": "No published rate limits",
                    },
                },
                "features": {
                    "two_factor_auth": "Available (recommended)",
                    "api_tokens": "Supported",
                    "trusted_publishing": "Available (OIDC)",
                    "project_management": "Via web interface",
                },
            }
            
            # Get user projects if possible (this requires web scraping or undocumented APIs)
            # For now, provide guidance on how to get this information
            account_info["user_projects"] = {
                "note": "Project list not available via API",
                "alternative": f"Visit {'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/projects/ to see your projects",
            }
            
            result["account_info"] = account_info
            
            # Add recommendations
            result["recommendations"] = [
                "Enable two-factor authentication for enhanced security",
                "Use scoped API tokens for specific projects when possible",
                "Consider using trusted publishing (OIDC) for CI/CD workflows",
                "Regularly review and rotate API tokens",
                "Monitor upload quotas and limits through the web interface",
            ]
            
            # Add useful links
            result["useful_links"] = {
                "account_settings": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/account/",
                "api_tokens": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/account/token/",
                "projects": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/projects/",
                "trusted_publishing": f"{'https://test.pypi.org' if test_pypi else 'https://pypi.org'}/manage/account/publishing/",
                "help": "https://pypi.org/help/",
            }
            
            logger.info("Successfully retrieved account information")
            return result
            
        except PyPIAuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error getting account information: {e}")
            raise NetworkError(f"Failed to get account information: {e}", e)
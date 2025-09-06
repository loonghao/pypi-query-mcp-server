"""Security vulnerability scanning tools for PyPI packages."""

import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..tools.security import bulk_security_scan, scan_package_security

logger = logging.getLogger(__name__)


async def scan_pypi_package_security(
    package_name: str,
    version: Optional[str] = None,
    include_dependencies: bool = True,
    severity_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scan a PyPI package for security vulnerabilities.
    
    This tool performs comprehensive security vulnerability scanning of PyPI packages,
    checking against multiple vulnerability databases including OSV (Open Source Vulnerabilities),
    GitHub Security Advisories, and analyzing package metadata for security indicators.
    
    Args:
        package_name: Name of the package to scan for vulnerabilities
        version: Specific version to scan (optional, defaults to latest version)
        include_dependencies: Whether to scan package dependencies for vulnerabilities  
        severity_filter: Filter results by severity level (low, medium, high, critical)
        
    Returns:
        Dictionary containing comprehensive security scan results including:
        - Total vulnerability count and severity breakdown
        - Direct package vulnerabilities vs dependency vulnerabilities
        - Risk score and level assessment (minimal, low, medium, high, critical)
        - Detailed vulnerability information with IDs, descriptions, and references
        - Package metadata security analysis
        - Actionable security recommendations
        
    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
        SearchError: If security scanning fails
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)
        
    logger.info(f"MCP tool: Scanning security for package {package_name}")
    
    try:
        result = await scan_package_security(
            package_name=package_name,
            version=version,
            include_dependencies=include_dependencies,
            severity_filter=severity_filter
        )
        
        logger.info(f"MCP tool: Security scan completed for {package_name} - found {result.get('security_summary', {}).get('total_vulnerabilities', 0)} vulnerabilities")
        return result
        
    except (InvalidPackageNameError, NetworkError, SearchError) as e:
        logger.error(f"Error scanning security for {package_name}: {e}")
        return {
            "error": f"Security scan failed: {e}",
            "error_type": type(e).__name__,
            "package": package_name,
            "version": version,
            "scan_timestamp": "",
            "security_summary": {
                "total_vulnerabilities": 0,
                "direct_vulnerabilities": 0,
                "dependency_vulnerabilities": 0,
                "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0},
                "risk_score": 0,
                "risk_level": "unknown",
            },
            "vulnerabilities": {"direct": [], "dependencies": []},
            "metadata_analysis": {},
            "recommendations": [f"❌ Security scan failed: {e}"],
            "scan_details": {
                "sources_checked": [],
                "dependencies_scanned": False,
                "scan_completion": "error",
            }
        }


async def bulk_scan_package_security(
    package_names: List[str],
    include_dependencies: bool = False,
    severity_threshold: str = "medium"
) -> Dict[str, Any]:
    """
    Perform bulk security scanning of multiple PyPI packages.
    
    This tool scans multiple packages simultaneously for security vulnerabilities,
    providing a consolidated report with summary statistics and prioritized
    recommendations for addressing security issues across your package ecosystem.
    
    Args:
        package_names: List of package names to scan for vulnerabilities
        include_dependencies: Whether to include dependency vulnerability scanning
        severity_threshold: Minimum severity level to report (low, medium, high, critical)
        
    Returns:
        Dictionary containing bulk scan results including:
        - Summary statistics (total packages, packages with vulnerabilities, high-risk packages)
        - Detailed scan results for each package
        - Prioritized recommendations for security remediation
        - Scan timestamp and completion status
        
    Raises:
        ValueError: If package_names list is empty
        NetworkError: For network-related errors during scanning
        SearchError: If bulk scanning fails
    """
    if not package_names:
        raise ValueError("Package names list cannot be empty")
        
    logger.info(f"MCP tool: Starting bulk security scan of {len(package_names)} packages")
    
    try:
        result = await bulk_security_scan(
            package_names=package_names,
            include_dependencies=include_dependencies,
            severity_threshold=severity_threshold
        )
        
        logger.info(f"MCP tool: Bulk security scan completed - {result.get('summary', {}).get('packages_with_vulnerabilities', 0)} packages have vulnerabilities")
        return result
        
    except (ValueError, NetworkError, SearchError) as e:
        logger.error(f"Error in bulk security scan: {e}")
        return {
            "error": f"Bulk security scan failed: {e}",
            "error_type": type(e).__name__,
            "summary": {
                "total_packages": len(package_names),
                "packages_with_vulnerabilities": 0,
                "total_vulnerabilities": 0,
                "high_risk_packages": [],
                "scan_timestamp": ""
            },
            "detailed_results": {},
            "recommendations": [f"❌ Bulk security scan failed: {e}"]
        }
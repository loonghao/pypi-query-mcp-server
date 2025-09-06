"""License compatibility analysis tools for PyPI packages."""

import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..tools.license_analyzer import analyze_package_license_compatibility, check_license_compliance_bulk

logger = logging.getLogger(__name__)


async def analyze_pypi_package_license(
    package_name: str,
    version: Optional[str] = None,
    include_dependencies: bool = True
) -> Dict[str, Any]:
    """
    Analyze license compatibility for a PyPI package.
    
    This tool provides comprehensive license analysis including license identification,
    dependency license scanning, compatibility checking, and risk assessment to help
    ensure your project complies with open source license requirements.
    
    Args:
        package_name: Name of the package to analyze for license compatibility
        version: Specific version to analyze (optional, defaults to latest version)
        include_dependencies: Whether to analyze dependency licenses for compatibility
        
    Returns:
        Dictionary containing comprehensive license analysis including:
        - License identification and normalization (SPDX format)
        - License categorization (permissive, copyleft, proprietary, etc.)
        - Dependency license analysis and compatibility matrix
        - Risk assessment with score and risk level (minimal, low, medium, high, critical)
        - Compatibility analysis highlighting conflicts and review-required combinations
        - Actionable recommendations for license compliance
        
    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
        SearchError: If license analysis fails
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)
        
    logger.info(f"MCP tool: Analyzing license compatibility for package {package_name}")
    
    try:
        result = await analyze_package_license_compatibility(
            package_name=package_name,
            version=version,
            include_dependencies=include_dependencies
        )
        
        logger.info(f"MCP tool: License analysis completed for {package_name} - {result.get('analysis_summary', {}).get('license_conflicts', 0)} conflicts found")
        return result
        
    except (InvalidPackageNameError, NetworkError, SearchError) as e:
        logger.error(f"Error analyzing license for {package_name}: {e}")
        return {
            "error": f"License analysis failed: {e}",
            "error_type": type(e).__name__,
            "package": package_name,
            "version": version,
            "analysis_timestamp": "",
            "license_info": {
                "normalized_license": "Unknown",
                "license_category": "unknown",
                "license_confidence": "low",
            },
            "dependency_licenses": [],
            "compatibility_analysis": {
                "main_license": "Unknown",
                "compatible": [],
                "incompatible": [],
                "review_required": [],
                "conflicts": [],
            },
            "risk_assessment": {
                "risk_score": 100,
                "risk_level": "critical",
                "risk_factors": [f"License analysis failed: {e}"],
                "compliance_status": "unknown",
            },
            "recommendations": [f"❌ License analysis failed: {e}"],
            "analysis_summary": {
                "total_dependencies_analyzed": 0,
                "unique_licenses_found": 0,
                "license_conflicts": 0,
                "review_required_count": 0,
            }
        }


async def check_bulk_license_compliance(
    package_names: List[str],
    target_license: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check license compliance for multiple PyPI packages.
    
    This tool performs bulk license compliance checking across multiple packages,
    providing a consolidated report to help ensure your entire package ecosystem
    complies with license requirements and identifying potential legal risks.
    
    Args:
        package_names: List of package names to check for license compliance
        target_license: Target license for compatibility checking (optional)
        
    Returns:
        Dictionary containing bulk compliance analysis including:
        - Summary statistics (total packages, compliant/non-compliant counts)
        - Detailed license analysis for each package
        - High-risk packages requiring immediate attention
        - Unknown license packages needing investigation
        - Prioritized recommendations for compliance remediation
        
    Raises:
        ValueError: If package_names list is empty
        NetworkError: For network-related errors during analysis
        SearchError: If bulk compliance checking fails
    """
    if not package_names:
        raise ValueError("Package names list cannot be empty")
        
    logger.info(f"MCP tool: Starting bulk license compliance check for {len(package_names)} packages")
    
    try:
        result = await check_license_compliance_bulk(
            package_names=package_names,
            target_license=target_license
        )
        
        logger.info(f"MCP tool: Bulk license compliance completed - {result.get('summary', {}).get('non_compliant_packages', 0)} non-compliant packages found")
        return result
        
    except (ValueError, NetworkError, SearchError) as e:
        logger.error(f"Error in bulk license compliance check: {e}")
        return {
            "error": f"Bulk license compliance check failed: {e}",
            "error_type": type(e).__name__,
            "summary": {
                "total_packages": len(package_names),
                "compliant_packages": 0,
                "non_compliant_packages": 0,
                "unknown_license_packages": len(package_names),
                "high_risk_packages": [],
                "analysis_timestamp": ""
            },
            "detailed_results": {},
            "target_license": target_license,
            "recommendations": [f"❌ Bulk license compliance check failed: {e}"]
        }
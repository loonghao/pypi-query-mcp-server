"""Package health assessment tools for PyPI packages."""

import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..tools.health_scorer import assess_pypi_package_health, compare_package_health

logger = logging.getLogger(__name__)


async def assess_package_health_score(
    package_name: str,
    version: Optional[str] = None,
    include_github_metrics: bool = True
) -> Dict[str, Any]:
    """
    Assess comprehensive health and quality of a PyPI package.
    
    This tool evaluates package health across multiple dimensions including maintenance,
    popularity, documentation, testing, security practices, compatibility, and metadata
    completeness to provide an overall health score and actionable recommendations.
    
    Args:
        package_name: Name of the package to assess for health and quality
        version: Specific version to assess (optional, defaults to latest version)
        include_github_metrics: Whether to fetch GitHub repository metrics for analysis
        
    Returns:
        Dictionary containing comprehensive health assessment including:
        - Overall health score (0-100) and level (excellent/good/fair/poor/critical)
        - Category-specific scores (maintenance, popularity, documentation, testing, etc.)
        - Detailed assessment breakdown with indicators and issues for each category
        - GitHub repository metrics (stars, forks, activity) if available
        - Actionable recommendations for health improvements
        - Strengths, weaknesses, and improvement priorities analysis
        
    Raises:
        InvalidPackageNameError: If package name is empty or invalid
        PackageNotFoundError: If package is not found on PyPI
        NetworkError: For network-related errors
        SearchError: If health assessment fails
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError(package_name)
        
    logger.info(f"MCP tool: Assessing health for package {package_name}")
    
    try:
        result = await assess_pypi_package_health(
            package_name=package_name,
            version=version,
            include_github_metrics=include_github_metrics
        )
        
        overall_score = result.get("overall_health", {}).get("score", 0)
        health_level = result.get("overall_health", {}).get("level", "unknown")
        logger.info(f"MCP tool: Health assessment completed for {package_name} - score: {overall_score:.1f}/100 ({health_level})")
        return result
        
    except (InvalidPackageNameError, NetworkError, SearchError) as e:
        logger.error(f"Error assessing health for {package_name}: {e}")
        return {
            "error": f"Health assessment failed: {e}",
            "error_type": type(e).__name__,
            "package": package_name,
            "version": version,
            "assessment_timestamp": "",
            "overall_health": {
                "score": 0,
                "level": "critical",
                "max_score": 100,
            },
            "category_scores": {
                "maintenance": 0,
                "popularity": 0,
                "documentation": 0,
                "testing": 0,
                "security": 0,
                "compatibility": 0,
                "metadata": 0,
            },
            "detailed_assessment": {},
            "recommendations": [f"❌ Health assessment failed: {e}"],
            "health_summary": {
                "strengths": [],
                "weaknesses": ["Assessment failure"],
                "improvement_priority": ["Resolve package access issues"],
            }
        }


async def compare_packages_health_scores(
    package_names: List[str],
    include_github_metrics: bool = False
) -> Dict[str, Any]:
    """
    Compare health scores across multiple PyPI packages.
    
    This tool performs comparative health analysis across multiple packages,
    providing rankings, insights, and recommendations to help evaluate
    package ecosystem quality and identify the best options.
    
    Args:
        package_names: List of package names to compare for health and quality
        include_github_metrics: Whether to include GitHub metrics in the comparison
        
    Returns:
        Dictionary containing comparative health analysis including:
        - Detailed health results for each package
        - Health score rankings with best/worst package identification
        - Comparison insights (average scores, score ranges, rankings)
        - Recommendations for package selection and improvements
        - Statistical analysis of health across the package set
        
    Raises:
        ValueError: If package_names list is empty
        NetworkError: For network-related errors during analysis
        SearchError: If health comparison fails
    """
    if not package_names:
        raise ValueError("Package names list cannot be empty")
        
    logger.info(f"MCP tool: Starting health comparison for {len(package_names)} packages")
    
    try:
        result = await compare_package_health(
            package_names=package_names,
            include_github_metrics=include_github_metrics
        )
        
        comparison_insights = result.get("comparison_insights", {})
        best_package = comparison_insights.get("best_package", {})
        packages_compared = result.get("packages_compared", 0)
        
        logger.info(f"MCP tool: Health comparison completed for {packages_compared} packages - best: {best_package.get('name', 'unknown')} ({best_package.get('score', 0):.1f}/100)")
        return result
        
    except (ValueError, NetworkError, SearchError) as e:
        logger.error(f"Error in health comparison: {e}")
        return {
            "error": f"Health comparison failed: {e}",
            "error_type": type(e).__name__,
            "comparison_timestamp": "",
            "packages_compared": len(package_names),
            "detailed_results": {},
            "comparison_insights": {
                "best_package": None,
                "worst_package": None,
                "average_score": 0,
                "score_range": 0,
                "rankings": []
            },
            "recommendations": [f"❌ Health comparison failed: {e}"]
        }
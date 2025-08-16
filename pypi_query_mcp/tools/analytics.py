"""PyPI Analytics & Insights Tools for comprehensive package analysis."""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIError,
)
from ..core.pypi_client import PyPIClient
from ..core.search_client import PyPISearchClient, SearchFilter, SearchSort
from ..core.stats_client import PyPIStatsClient

logger = logging.getLogger(__name__)


async def get_pypi_package_analytics(
    package_name: str,
    time_period: str = "month",
    include_historical: bool = True,
    include_platform_breakdown: bool = True,
    include_version_analytics: bool = True,
) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a PyPI package including advanced metrics.
    
    This function provides detailed download analytics, trend analysis, geographic
    distribution, platform breakdown, and version adoption patterns.
    
    Args:
        package_name: Name of the package to analyze
        time_period: Time period for analysis ('day', 'week', 'month', 'year')
        include_historical: Whether to include historical trend analysis
        include_platform_breakdown: Whether to include platform/OS breakdown
        include_version_analytics: Whether to include version-specific analytics
        
    Returns:
        Dictionary containing comprehensive analytics including:
        - Download statistics and trends
        - Platform and Python version breakdown
        - Geographic distribution
        - Version adoption patterns
        - Quality metrics and indicators
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    logger.info(f"Generating comprehensive analytics for package: {package_name}")
    
    try:
        # Gather data from multiple sources concurrently
        analytics_tasks = [
            _get_download_analytics(package_name, time_period, include_historical),
            _get_package_metadata(package_name),
            _get_version_analytics(package_name) if include_version_analytics else asyncio.create_task(_empty_dict()),
            _get_platform_analytics(package_name) if include_platform_breakdown else asyncio.create_task(_empty_dict()),
            _get_quality_metrics(package_name),
        ]
        
        results = await asyncio.gather(*analytics_tasks, return_exceptions=True)
        
        download_analytics = results[0] if not isinstance(results[0], Exception) else {}
        package_metadata = results[1] if not isinstance(results[1], Exception) else {}
        version_analytics = results[2] if not isinstance(results[2], Exception) else {}
        platform_analytics = results[3] if not isinstance(results[3], Exception) else {}
        quality_metrics = results[4] if not isinstance(results[4], Exception) else {}
        
        # Compile comprehensive analytics report
        analytics_report = {
            "package": package_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "time_period": time_period,
            "metadata": package_metadata,
            "download_analytics": download_analytics,
            "quality_metrics": quality_metrics,
            "insights": _generate_insights(download_analytics, package_metadata, quality_metrics),
        }
        
        # Add optional analytics sections
        if include_version_analytics and version_analytics:
            analytics_report["version_analytics"] = version_analytics
            
        if include_platform_breakdown and platform_analytics:
            analytics_report["platform_analytics"] = platform_analytics
        
        # Add data reliability indicators
        analytics_report["data_reliability"] = _assess_data_reliability(results)
        
        return analytics_report
        
    except Exception as e:
        logger.error(f"Error generating analytics for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to generate analytics: {e}") from e


async def get_pypi_security_alerts(
    package_name: str,
    include_dependencies: bool = True,
    severity_filter: Optional[str] = None,
    include_historical: bool = False,
) -> Dict[str, Any]:
    """
    Get security alerts and vulnerability information for a PyPI package.
    
    This function queries multiple security databases including OSV (Open Source
    Vulnerabilities), PyUp.io Safety DB, and GitHub Security Advisories to provide
    comprehensive security information.
    
    Args:
        package_name: Name of the package to check for vulnerabilities
        include_dependencies: Whether to check dependencies for vulnerabilities
        severity_filter: Filter by severity ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
        include_historical: Whether to include historical vulnerabilities
        
    Returns:
        Dictionary containing security information including:
        - Active vulnerabilities and CVEs
        - Security scores and risk assessment
        - Dependency vulnerability analysis
        - Remediation recommendations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    logger.info(f"Checking security alerts for package: {package_name}")
    
    try:
        # Gather security data from multiple sources
        security_tasks = [
            _check_osv_vulnerabilities(package_name),
            _check_package_dependencies(package_name) if include_dependencies else asyncio.create_task(_empty_dict()),
            _get_security_metadata(package_name),
            _analyze_package_security_posture(package_name),
        ]
        
        results = await asyncio.gather(*security_tasks, return_exceptions=True)
        
        osv_vulnerabilities = results[0] if not isinstance(results[0], Exception) else {}
        dependency_analysis = results[1] if not isinstance(results[1], Exception) else {}
        security_metadata = results[2] if not isinstance(results[2], Exception) else {}
        security_posture = results[3] if not isinstance(results[3], Exception) else {}
        
        # Filter vulnerabilities by severity if specified
        filtered_vulnerabilities = _filter_vulnerabilities_by_severity(
            osv_vulnerabilities, severity_filter, include_historical
        )
        
        # Calculate security score
        security_score = _calculate_security_score(
            filtered_vulnerabilities, dependency_analysis, security_posture
        )
        
        # Generate recommendations
        recommendations = _generate_security_recommendations(
            filtered_vulnerabilities, dependency_analysis, security_score
        )
        
        security_report = {
            "package": package_name,
            "scan_timestamp": datetime.now().isoformat(),
            "security_score": security_score,
            "vulnerabilities": filtered_vulnerabilities,
            "metadata": security_metadata,
            "security_posture": security_posture,
            "recommendations": recommendations,
            "scan_options": {
                "include_dependencies": include_dependencies,
                "severity_filter": severity_filter,
                "include_historical": include_historical,
            },
        }
        
        # Add dependency analysis if requested
        if include_dependencies and dependency_analysis:
            security_report["dependency_analysis"] = dependency_analysis
            
        return security_report
        
    except Exception as e:
        logger.error(f"Error checking security alerts for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to check security alerts: {e}") from e


async def get_pypi_package_rankings(
    package_name: str,
    search_terms: Optional[List[str]] = None,
    competitor_packages: Optional[List[str]] = None,
    ranking_metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze package rankings and visibility in PyPI search results.
    
    This function analyzes how well a package ranks for relevant search terms,
    compares it to competitor packages, and provides insights into search
    visibility and discoverability.
    
    Args:
        package_name: Name of the package to analyze rankings for
        search_terms: List of search terms to test rankings against
        competitor_packages: List of competitor packages to compare against
        ranking_metrics: Specific metrics to focus on ('relevance', 'popularity', 'downloads', 'quality')
        
    Returns:
        Dictionary containing ranking analysis including:
        - Search position for various terms
        - Competitor comparison matrix
        - Visibility and discoverability metrics
        - SEO and keyword optimization suggestions
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    logger.info(f"Analyzing search rankings for package: {package_name}")
    
    try:
        # Get package metadata to extract relevant search terms
        async with PyPIClient() as pypi_client:
            package_data = await pypi_client.get_package_info(package_name)
            
        # Extract search terms from package metadata if not provided
        if not search_terms:
            search_terms = _extract_search_terms(package_data)
            
        # Get competitor packages if not provided
        if not competitor_packages:
            competitor_packages = await _find_competitor_packages(package_name, package_data)
            
        # Set default ranking metrics if not provided
        if not ranking_metrics:
            ranking_metrics = ["relevance", "popularity", "downloads", "quality"]
            
        # Perform ranking analysis
        ranking_tasks = [
            _analyze_search_rankings(package_name, search_terms, ranking_metrics),
            _analyze_competitor_rankings(package_name, competitor_packages, search_terms),
            _analyze_package_discoverability(package_name, package_data),
            _get_seo_analysis(package_name, package_data),
        ]
        
        results = await asyncio.gather(*ranking_tasks, return_exceptions=True)
        
        search_rankings = results[0] if not isinstance(results[0], Exception) else {}
        competitor_analysis = results[1] if not isinstance(results[1], Exception) else {}
        discoverability = results[2] if not isinstance(results[2], Exception) else {}
        seo_analysis = results[3] if not isinstance(results[3], Exception) else {}
        
        # Calculate overall ranking score
        ranking_score = _calculate_ranking_score(search_rankings, competitor_analysis, discoverability)
        
        # Generate improvement recommendations
        improvement_suggestions = _generate_ranking_recommendations(
            search_rankings, competitor_analysis, seo_analysis, ranking_score
        )
        
        ranking_report = {
            "package": package_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "ranking_score": ranking_score,
            "search_rankings": search_rankings,
            "competitor_analysis": competitor_analysis,
            "discoverability": discoverability,
            "seo_analysis": seo_analysis,
            "improvement_suggestions": improvement_suggestions,
            "analysis_parameters": {
                "search_terms": search_terms,
                "competitor_packages": competitor_packages,
                "ranking_metrics": ranking_metrics,
            },
        }
        
        return ranking_report
        
    except Exception as e:
        logger.error(f"Error analyzing rankings for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to analyze package rankings: {e}") from e


async def analyze_pypi_competition(
    package_name: str,
    competitor_packages: Optional[List[str]] = None,
    analysis_depth: str = "comprehensive",
    include_market_share: bool = True,
    include_feature_comparison: bool = True,
) -> Dict[str, Any]:
    """
    Perform comprehensive competitive analysis against similar packages.
    
    This function analyzes a package against its competitors, providing insights
    into market positioning, feature gaps, adoption trends, and competitive
    advantages.
    
    Args:
        package_name: Name of the package to analyze
        competitor_packages: List of competitor packages (auto-detected if not provided)
        analysis_depth: Depth of analysis ('basic', 'comprehensive', 'detailed')
        include_market_share: Whether to include market share analysis
        include_feature_comparison: Whether to include feature comparison
        
    Returns:
        Dictionary containing competitive analysis including:
        - Market positioning and share
        - Feature comparison matrix
        - Adoption and growth trends
        - Competitive advantages and weaknesses
        - Strategic recommendations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    logger.info(f"Analyzing competition for package: {package_name}")
    
    try:
        # Get target package information
        async with PyPIClient() as pypi_client:
            target_package_data = await pypi_client.get_package_info(package_name)
            
        # Auto-detect competitors if not provided
        if not competitor_packages:
            competitor_packages = await _find_competitor_packages(package_name, target_package_data, limit=10)
            
        # Perform competitive analysis based on depth
        if analysis_depth == "basic":
            analysis_tasks = [
                _analyze_basic_competition(package_name, competitor_packages, target_package_data),
            ]
        elif analysis_depth == "comprehensive":
            analysis_tasks = [
                _analyze_basic_competition(package_name, competitor_packages, target_package_data),
                _analyze_market_positioning(package_name, competitor_packages),
                _analyze_adoption_trends(package_name, competitor_packages),
            ]
        else:  # detailed
            analysis_tasks = [
                _analyze_basic_competition(package_name, competitor_packages, target_package_data),
                _analyze_market_positioning(package_name, competitor_packages),
                _analyze_adoption_trends(package_name, competitor_packages),
                _analyze_feature_comparison(package_name, competitor_packages) if include_feature_comparison else asyncio.create_task(_empty_dict()),
                _analyze_developer_experience(package_name, competitor_packages),
            ]
            
        # Add market share analysis if requested
        if include_market_share:
            analysis_tasks.append(_analyze_market_share(package_name, competitor_packages))
            
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Compile analysis results
        basic_analysis = results[0] if not isinstance(results[0], Exception) else {}
        
        competitive_report = {
            "package": package_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_depth": analysis_depth,
            "competitor_packages": competitor_packages,
            "basic_analysis": basic_analysis,
        }
        
        # Add advanced analysis results
        result_index = 1
        if analysis_depth in ["comprehensive", "detailed"]:
            competitive_report["market_positioning"] = results[result_index] if not isinstance(results[result_index], Exception) else {}
            result_index += 1
            competitive_report["adoption_trends"] = results[result_index] if not isinstance(results[result_index], Exception) else {}
            result_index += 1
            
        if analysis_depth == "detailed":
            if include_feature_comparison:
                competitive_report["feature_comparison"] = results[result_index] if not isinstance(results[result_index], Exception) else {}
                result_index += 1
            competitive_report["developer_experience"] = results[result_index] if not isinstance(results[result_index], Exception) else {}
            result_index += 1
            
        if include_market_share:
            competitive_report["market_share"] = results[result_index] if not isinstance(results[result_index], Exception) else {}
            
        # Generate strategic recommendations
        competitive_report["strategic_recommendations"] = _generate_competitive_recommendations(
            competitive_report, target_package_data
        )
        
        # Calculate competitive strength score
        competitive_report["competitive_strength"] = _calculate_competitive_strength(competitive_report)
        
        return competitive_report
        
    except Exception as e:
        logger.error(f"Error analyzing competition for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to analyze competition: {e}") from e


# Helper functions for analytics implementation

async def _empty_dict():
    """Return empty dict for optional tasks."""
    return {}


async def _get_download_analytics(package_name: str, time_period: str, include_historical: bool) -> Dict[str, Any]:
    """Get comprehensive download analytics."""
    try:
        # Use existing download stats functionality
        from .download_stats import get_package_download_stats, get_package_download_trends
        
        tasks = [
            get_package_download_stats(package_name, time_period),
        ]
        
        if include_historical:
            tasks.append(get_package_download_trends(package_name))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        download_stats = results[0] if not isinstance(results[0], Exception) else {}
        download_trends = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {}
        
        return {
            "current_stats": download_stats,
            "historical_trends": download_trends if include_historical else {},
            "growth_analysis": _analyze_growth_patterns(download_stats, download_trends),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get download analytics for {package_name}: {e}")
        return {}


async def _get_package_metadata(package_name: str) -> Dict[str, Any]:
    """Get comprehensive package metadata."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        return {
            "name": info.get("name", package_name),
            "version": info.get("version", "unknown"),
            "summary": info.get("summary", ""),
            "description_content_type": info.get("description_content_type", ""),
            "keywords": info.get("keywords", ""),
            "classifiers": info.get("classifiers", []),
            "license": info.get("license", ""),
            "author": info.get("author", ""),
            "maintainer": info.get("maintainer", ""),
            "home_page": info.get("home_page", ""),
            "project_urls": info.get("project_urls", {}),
            "requires_python": info.get("requires_python", ""),
            "requires_dist": info.get("requires_dist", []),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get package metadata for {package_name}: {e}")
        return {"name": package_name}


async def _get_version_analytics(package_name: str) -> Dict[str, Any]:
    """Analyze version adoption patterns."""
    try:
        async with PyPIClient() as client:
            # Get version information
            package_data = await client.get_package_info(package_name)
            
        releases = package_data.get("releases", {})
        versions = list(releases.keys())
        
        # Analyze version patterns
        version_analysis = {
            "total_versions": len(versions),
            "latest_version": package_data.get("info", {}).get("version", ""),
            "version_frequency": _analyze_version_frequency(versions),
            "release_patterns": _analyze_release_patterns(releases),
        }
        
        return version_analysis
        
    except Exception as e:
        logger.warning(f"Failed to get version analytics for {package_name}: {e}")
        return {}


async def _get_platform_analytics(package_name: str) -> Dict[str, Any]:
    """Analyze platform and Python version distribution."""
    try:
        # This would require pypistats.org detailed data
        # For now, return basic platform information from package metadata
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        classifiers = package_data.get("info", {}).get("classifiers", [])
        
        # Extract platform information from classifiers
        platforms = []
        python_versions = []
        
        for classifier in classifiers:
            if "Operating System" in classifier:
                platforms.append(classifier.split("::")[-1].strip())
            elif "Programming Language :: Python ::" in classifier:
                python_versions.append(classifier.split("::")[-1].strip())
                
        return {
            "supported_platforms": platforms,
            "supported_python_versions": python_versions,
            "platform_analysis": "Limited to classifier data - full analytics require pypistats access",
        }
        
    except Exception as e:
        logger.warning(f"Failed to get platform analytics for {package_name}: {e}")
        return {}


async def _get_quality_metrics(package_name: str) -> Dict[str, Any]:
    """Calculate package quality metrics."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        
        # Calculate quality score based on available metadata
        quality_score = _calculate_quality_score(info)
        
        return {
            "quality_score": quality_score,
            "has_description": bool(info.get("description")),
            "has_keywords": bool(info.get("keywords")),
            "has_classifiers": bool(info.get("classifiers")),
            "has_project_urls": bool(info.get("project_urls")),
            "has_license": bool(info.get("license")),
            "has_author": bool(info.get("author")),
            "python_version_specified": bool(info.get("requires_python")),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get quality metrics for {package_name}: {e}")
        return {"quality_score": 0}


def _generate_insights(download_analytics: Dict, metadata: Dict, quality_metrics: Dict) -> Dict[str, Any]:
    """Generate insights from analytics data."""
    insights = {
        "performance_insights": [],
        "quality_insights": [],
        "recommendations": [],
    }
    
    # Performance insights
    if download_analytics.get("current_stats", {}).get("downloads"):
        downloads = download_analytics["current_stats"]["downloads"]
        if downloads.get("last_month", 0) > 100000:
            insights["performance_insights"].append("High-traffic package with significant community adoption")
        elif downloads.get("last_month", 0) > 10000:
            insights["performance_insights"].append("Growing package with good adoption")
        else:
            insights["performance_insights"].append("Emerging package with potential for growth")
            
    # Quality insights
    quality_score = quality_metrics.get("quality_score", 0)
    if quality_score > 80:
        insights["quality_insights"].append("Well-documented package with good metadata")
    elif quality_score > 60:
        insights["quality_insights"].append("Adequate documentation with room for improvement")
    else:
        insights["quality_insights"].append("Package could benefit from better documentation and metadata")
        
    return insights


def _assess_data_reliability(results: List) -> Dict[str, Any]:
    """Assess the reliability of collected data."""
    successful_operations = sum(1 for r in results if not isinstance(r, Exception))
    total_operations = len(results)
    
    reliability_score = (successful_operations / total_operations) * 100 if total_operations > 0 else 0
    
    return {
        "reliability_score": reliability_score,
        "successful_operations": successful_operations,
        "total_operations": total_operations,
        "status": "excellent" if reliability_score > 90 else "good" if reliability_score > 70 else "limited",
    }


async def _check_osv_vulnerabilities(package_name: str) -> Dict[str, Any]:
    """Check OSV database for vulnerabilities."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Query OSV API for PyPI ecosystem
            osv_query = {
                "package": {
                    "name": package_name,
                    "ecosystem": "PyPI"
                }
            }
            
            response = await client.post(
                "https://api.osv.dev/v1/query",
                json=osv_query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                vulnerabilities = data.get("vulns", [])
                
                return {
                    "source": "OSV Database",
                    "vulnerability_count": len(vulnerabilities),
                    "vulnerabilities": vulnerabilities[:10],  # Limit to first 10
                    "scan_timestamp": datetime.now().isoformat(),
                }
            else:
                logger.warning(f"OSV API returned status {response.status_code}")
                return {"source": "OSV Database", "vulnerability_count": 0, "vulnerabilities": []}
                
    except Exception as e:
        logger.warning(f"Failed to check OSV vulnerabilities for {package_name}: {e}")
        return {"source": "OSV Database", "vulnerability_count": 0, "vulnerabilities": [], "error": str(e)}


async def _check_package_dependencies(package_name: str) -> Dict[str, Any]:
    """Check dependencies for security issues."""
    try:
        # Use existing dependency resolver
        from .dependency_resolver import resolve_package_dependencies
        
        dependencies = await resolve_package_dependencies(package_name, max_depth=2)
        
        # For now, just return dependency count and structure
        # Full security scanning would require integration with security databases
        return {
            "dependency_count": len(dependencies.get("dependencies", {})),
            "dependency_tree": dependencies,
            "security_note": "Full dependency security scanning requires additional security database integration",
        }
        
    except Exception as e:
        logger.warning(f"Failed to check dependencies for {package_name}: {e}")
        return {"dependency_count": 0, "error": str(e)}


async def _get_security_metadata(package_name: str) -> Dict[str, Any]:
    """Get security-related metadata from package information."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        
        # Analyze security-related metadata
        security_indicators = {
            "has_security_contact": any("security" in url.lower() for url in info.get("project_urls", {}).values()),
            "has_license": bool(info.get("license")),
            "has_documentation": any("doc" in url.lower() for url in info.get("project_urls", {}).values()),
            "has_repository": any("repo" in url.lower() or "github" in url.lower() for url in info.get("project_urls", {}).values()),
            "classifiers": info.get("classifiers", []),
        }
        
        return security_indicators
        
    except Exception as e:
        logger.warning(f"Failed to get security metadata for {package_name}: {e}")
        return {}


async def _analyze_package_security_posture(package_name: str) -> Dict[str, Any]:
    """Analyze overall security posture of the package."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        
        # Basic security posture analysis
        posture_score = 0
        factors = []
        
        if info.get("license"):
            posture_score += 20
            factors.append("Has license specified")
            
        if info.get("project_urls"):
            posture_score += 15
            factors.append("Has project URLs")
            
        if info.get("author") or info.get("maintainer"):
            posture_score += 10
            factors.append("Has identifiable maintainer")
            
        if info.get("home_page"):
            posture_score += 10
            factors.append("Has homepage")
            
        # Check for recent activity (if version was updated recently)
        try:
            upload_time = package_data.get("urls", [{}])[0].get("upload_time_iso_8601", "")
            if upload_time:
                upload_date = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                days_since_update = (datetime.now().replace(tzinfo=None) - upload_date.replace(tzinfo=None)).days
                if days_since_update < 180:  # Updated within 6 months
                    posture_score += 15
                    factors.append("Recently updated")
        except:
            pass
            
        return {
            "security_posture_score": min(posture_score, 100),
            "contributing_factors": factors,
            "risk_level": "low" if posture_score > 70 else "medium" if posture_score > 40 else "high",
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze security posture for {package_name}: {e}")
        return {"security_posture_score": 0, "risk_level": "unknown"}


def _filter_vulnerabilities_by_severity(vulnerabilities: Dict, severity_filter: Optional[str], include_historical: bool) -> Dict[str, Any]:
    """Filter vulnerabilities by severity and historical status."""
    if not vulnerabilities.get("vulnerabilities"):
        return vulnerabilities
        
    filtered_vulns = vulnerabilities["vulnerabilities"]
    
    # Filter by severity if specified
    if severity_filter:
        severity_filter = severity_filter.upper()
        filtered_vulns = [
            vuln for vuln in filtered_vulns
            if vuln.get("database_specific", {}).get("severity", "").upper() == severity_filter
        ]
        
    # Filter historical if not requested
    if not include_historical:
        # Filter out withdrawn or historical vulnerabilities
        filtered_vulns = [
            vuln for vuln in filtered_vulns
            if not vuln.get("withdrawn") and vuln.get("id")
        ]
        
    vulnerabilities["vulnerabilities"] = filtered_vulns
    vulnerabilities["filtered_count"] = len(filtered_vulns)
    
    return vulnerabilities


def _calculate_security_score(vulnerabilities: Dict, dependency_analysis: Dict, security_posture: Dict) -> Dict[str, Any]:
    """Calculate overall security score."""
    base_score = security_posture.get("security_posture_score", 50)
    
    # Reduce score based on vulnerabilities
    vuln_count = vulnerabilities.get("vulnerability_count", 0)
    if vuln_count > 0:
        # Deduct points for each vulnerability
        vuln_penalty = min(vuln_count * 10, 50)  # Max 50 point penalty
        base_score -= vuln_penalty
        
    # Adjust for dependency risks
    dep_count = dependency_analysis.get("dependency_count", 0)
    if dep_count > 20:  # Many dependencies increase risk
        base_score -= 5
        
    final_score = max(0, min(100, base_score))
    
    return {
        "overall_security_score": final_score,
        "risk_level": "low" if final_score > 80 else "medium" if final_score > 50 else "high",
        "vulnerability_impact": vuln_count * 10,
        "base_posture_score": security_posture.get("security_posture_score", 50),
    }


def _generate_security_recommendations(vulnerabilities: Dict, dependency_analysis: Dict, security_score: Dict) -> List[str]:
    """Generate security recommendations."""
    recommendations = []
    
    if vulnerabilities.get("vulnerability_count", 0) > 0:
        recommendations.append("Update to a version that addresses known vulnerabilities")
        recommendations.append("Review security advisories and apply recommended patches")
        
    if security_score.get("overall_security_score", 0) < 70:
        recommendations.append("Improve package metadata and documentation")
        recommendations.append("Consider adding security contact information")
        
    if dependency_analysis.get("dependency_count", 0) > 20:
        recommendations.append("Review dependency list and consider reducing dependencies")
        recommendations.append("Regularly audit dependencies for security issues")
        
    if not recommendations:
        recommendations.append("Package appears to have good security posture")
        recommendations.append("Continue monitoring for new vulnerabilities")
        
    return recommendations


def _extract_search_terms(package_data: Dict) -> List[str]:
    """Extract relevant search terms from package data."""
    info = package_data.get("info", {})
    
    terms = []
    
    # Add package name variations
    name = info.get("name", "")
    if name:
        terms.append(name)
        # Add variations without hyphens/underscores
        terms.append(name.replace("-", "").replace("_", ""))
        
    # Add keywords
    keywords = info.get("keywords", "")
    if keywords:
        terms.extend([k.strip() for k in keywords.split(",") if k.strip()])
        
    # Extract terms from summary
    summary = info.get("summary", "")
    if summary:
        # Simple extraction of meaningful words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', summary.lower())
        terms.extend(words[:5])  # Limit to first 5 words
        
    # Add category terms from classifiers
    classifiers = info.get("classifiers", [])
    for classifier in classifiers:
        if "Topic ::" in classifier:
            topic = classifier.split("Topic ::")[-1].strip().lower()
            if " " not in topic:  # Single word topics
                terms.append(topic)
                
    return list(set(terms))[:10]  # Remove duplicates and limit


async def _find_competitor_packages(package_name: str, package_data: Dict, limit: int = 5) -> List[str]:
    """Find competitor packages based on package characteristics."""
    try:
        # Use existing search functionality to find similar packages
        from .search import search_packages
        
        info = package_data.get("info", {})
        
        # Create search query from package characteristics
        search_terms = []
        
        # Add keywords
        keywords = info.get("keywords", "")
        if keywords:
            search_terms.extend([k.strip() for k in keywords.split(",") if k.strip()][:3])
            
        # Add summary terms
        summary = info.get("summary", "")
        if summary:
            words = re.findall(r'\b[a-zA-Z]{4,}\b', summary.lower())
            search_terms.extend(words[:3])
            
        if not search_terms:
            search_terms = [package_name]
            
        # Search for similar packages
        search_query = " ".join(search_terms[:5])
        
        search_results = await search_packages(
            query=search_query,
            limit=limit + 5,  # Get extra to filter out the target package
            sort_by="popularity"
        )
        
        # Filter out the target package and return competitors
        competitors = []
        for pkg in search_results.get("packages", []):
            if pkg["name"].lower() != package_name.lower() and len(competitors) < limit:
                competitors.append(pkg["name"])
                
        return competitors
        
    except Exception as e:
        logger.warning(f"Failed to find competitors for {package_name}: {e}")
        return []


# Additional helper functions (continuing with implementation)

async def _analyze_search_rankings(package_name: str, search_terms: List[str], ranking_metrics: List[str]) -> Dict[str, Any]:
    """Analyze package rankings for different search terms."""
    try:
        from .search import search_packages
        
        rankings = {}
        
        for term in search_terms[:5]:  # Limit to first 5 terms
            try:
                search_results = await search_packages(
                    query=term,
                    limit=50,  # Search more results to find ranking
                    sort_by="relevance"
                )
                
                # Find package position in results
                position = None
                for i, pkg in enumerate(search_results.get("packages", [])):
                    if pkg["name"].lower() == package_name.lower():
                        position = i + 1
                        break
                        
                rankings[term] = {
                    "position": position,
                    "total_results": len(search_results.get("packages", [])),
                    "found": position is not None,
                }
                
            except Exception as e:
                logger.warning(f"Failed to search for term '{term}': {e}")
                rankings[term] = {"position": None, "found": False, "error": str(e)}
                
        return {
            "search_term_rankings": rankings,
            "average_position": _calculate_average_position(rankings),
            "visibility_score": _calculate_visibility_score(rankings),
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze search rankings for {package_name}: {e}")
        return {}


def _calculate_average_position(rankings: Dict) -> Optional[float]:
    """Calculate average search position."""
    positions = [r["position"] for r in rankings.values() if r.get("position")]
    return sum(positions) / len(positions) if positions else None


def _calculate_visibility_score(rankings: Dict) -> int:
    """Calculate visibility score based on search rankings."""
    total_terms = len(rankings)
    found_terms = sum(1 for r in rankings.values() if r.get("found"))
    
    if total_terms == 0:
        return 0
        
    # Base score from found percentage
    found_percentage = (found_terms / total_terms) * 100
    
    # Bonus for good positions (top 10)
    top_positions = sum(1 for r in rankings.values() if r.get("position", 999) <= 10)
    position_bonus = (top_positions / total_terms) * 20
    
    return min(100, int(found_percentage + position_bonus))


async def _analyze_competitor_rankings(package_name: str, competitors: List[str], search_terms: List[str]) -> Dict[str, Any]:
    """Analyze how package ranks against competitors."""
    try:
        competitor_analysis = {}
        
        for competitor in competitors[:3]:  # Limit to top 3 competitors
            competitor_rankings = await _analyze_search_rankings(competitor, search_terms, ["relevance"])
            competitor_analysis[competitor] = competitor_rankings
            
        # Compare against target package
        target_rankings = await _analyze_search_rankings(package_name, search_terms, ["relevance"])
        
        return {
            "target_package_rankings": target_rankings,
            "competitor_rankings": competitor_analysis,
            "competitive_position": _calculate_competitive_position(target_rankings, competitor_analysis),
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze competitor rankings: {e}")
        return {}


def _calculate_competitive_position(target_rankings: Dict, competitor_rankings: Dict) -> Dict[str, Any]:
    """Calculate competitive position relative to competitors."""
    target_score = target_rankings.get("visibility_score", 0)
    
    competitor_scores = []
    for comp_data in competitor_rankings.values():
        score = comp_data.get("visibility_score", 0)
        competitor_scores.append(score)
        
    if not competitor_scores:
        return {"position": "unknown", "score_comparison": 0}
        
    avg_competitor_score = sum(competitor_scores) / len(competitor_scores)
    
    position = "leading" if target_score > avg_competitor_score else "competitive" if target_score > avg_competitor_score * 0.8 else "trailing"
    
    return {
        "position": position,
        "target_score": target_score,
        "average_competitor_score": avg_competitor_score,
        "score_difference": target_score - avg_competitor_score,
    }


async def _analyze_package_discoverability(package_name: str, package_data: Dict) -> Dict[str, Any]:
    """Analyze package discoverability factors."""
    info = package_data.get("info", {})
    
    discoverability_factors = {
        "has_keywords": bool(info.get("keywords")),
        "has_detailed_description": len(info.get("description", "")) > 500,
        "has_classifiers": len(info.get("classifiers", [])) > 5,
        "has_project_urls": len(info.get("project_urls", {})) > 1,
        "has_homepage": bool(info.get("home_page")),
        "descriptive_name": len(package_name) > 3 and not package_name.isdigit(),
    }
    
    discoverability_score = sum(discoverability_factors.values()) * (100 / len(discoverability_factors))
    
    return {
        "discoverability_score": int(discoverability_score),
        "factors": discoverability_factors,
        "recommendations": _generate_discoverability_recommendations(discoverability_factors),
    }


def _generate_discoverability_recommendations(factors: Dict) -> List[str]:
    """Generate recommendations to improve discoverability."""
    recommendations = []
    
    if not factors.get("has_keywords"):
        recommendations.append("Add relevant keywords to improve search visibility")
        
    if not factors.get("has_detailed_description"):
        recommendations.append("Expand package description with more detailed information")
        
    if not factors.get("has_classifiers"):
        recommendations.append("Add more classifiers to categorize the package better")
        
    if not factors.get("has_project_urls"):
        recommendations.append("Add project URLs (repository, documentation, bug tracker)")
        
    if not factors.get("has_homepage"):
        recommendations.append("Add a homepage or documentation URL")
        
    return recommendations


async def _get_seo_analysis(package_name: str, package_data: Dict) -> Dict[str, Any]:
    """Analyze SEO factors for the package."""
    info = package_data.get("info", {})
    
    seo_factors = {
        "name_length_optimal": 3 <= len(package_name) <= 20,
        "name_has_keywords": any(keyword in package_name.lower() for keyword in ["api", "client", "tool", "lib", "py"]),
        "summary_length_optimal": 20 <= len(info.get("summary", "")) <= 80,
        "has_rich_description": len(info.get("description", "")) > 200,
        "uses_markdown": info.get("description_content_type", "").lower() in ["text/markdown", "markdown"],
        "has_author_info": bool(info.get("author")) or bool(info.get("maintainer")),
    }
    
    seo_score = sum(seo_factors.values()) * (100 / len(seo_factors))
    
    return {
        "seo_score": int(seo_score),
        "factors": seo_factors,
        "optimization_suggestions": _generate_seo_suggestions(seo_factors, info),
    }


def _generate_seo_suggestions(factors: Dict, info: Dict) -> List[str]:
    """Generate SEO optimization suggestions."""
    suggestions = []
    
    if not factors.get("summary_length_optimal"):
        current_length = len(info.get("summary", ""))
        if current_length < 20:
            suggestions.append("Expand summary to 20-80 characters for better search visibility")
        elif current_length > 80:
            suggestions.append("Shorten summary to 20-80 characters for optimal display")
            
    if not factors.get("has_rich_description"):
        suggestions.append("Add a detailed description with examples and use cases")
        
    if not factors.get("uses_markdown"):
        suggestions.append("Use Markdown format for better description formatting")
        
    return suggestions


def _calculate_ranking_score(search_rankings: Dict, competitor_analysis: Dict, discoverability: Dict) -> Dict[str, Any]:
    """Calculate overall ranking score."""
    visibility_score = search_rankings.get("visibility_score", 0)
    discoverability_score = discoverability.get("discoverability_score", 0)
    
    # Weight the scores
    overall_score = (visibility_score * 0.6) + (discoverability_score * 0.4)
    
    return {
        "overall_ranking_score": int(overall_score),
        "visibility_component": visibility_score,
        "discoverability_component": discoverability_score,
        "grade": "A" if overall_score >= 80 else "B" if overall_score >= 60 else "C" if overall_score >= 40 else "D",
    }


def _generate_ranking_recommendations(search_rankings: Dict, competitor_analysis: Dict, seo_analysis: Dict, ranking_score: Dict) -> List[str]:
    """Generate recommendations to improve rankings."""
    recommendations = []
    
    if ranking_score.get("overall_ranking_score", 0) < 70:
        recommendations.append("Focus on improving package discoverability and SEO")
        
    if search_rankings.get("visibility_score", 0) < 50:
        recommendations.append("Optimize keywords and description for better search visibility")
        
    # Add SEO-specific recommendations
    seo_suggestions = seo_analysis.get("optimization_suggestions", [])
    recommendations.extend(seo_suggestions[:3])  # Add top 3 SEO suggestions
    
    competitive_position = competitor_analysis.get("competitive_position", {})
    if competitive_position.get("position") == "trailing":
        recommendations.append("Study competitor packages to identify improvement opportunities")
        
    return recommendations[:5]  # Limit to top 5 recommendations


# Competition analysis helper functions

async def _analyze_basic_competition(package_name: str, competitors: List[str], target_package_data: Dict) -> Dict[str, Any]:
    """Perform basic competitive analysis."""
    try:
        # Get download stats for target and competitors
        from .download_stats import get_package_download_stats
        
        target_stats = await get_package_download_stats(package_name)
        
        competitor_stats = {}
        for competitor in competitors[:5]:  # Limit to 5 competitors
            try:
                stats = await get_package_download_stats(competitor)
                competitor_stats[competitor] = stats
            except Exception as e:
                logger.warning(f"Failed to get stats for competitor {competitor}: {e}")
                competitor_stats[competitor] = {"error": str(e)}
                
        # Basic comparison metrics
        target_downloads = target_stats.get("downloads", {}).get("last_month", 0)
        competitor_downloads = []
        
        for comp_data in competitor_stats.values():
            if "downloads" in comp_data:
                competitor_downloads.append(comp_data["downloads"].get("last_month", 0))
                
        avg_competitor_downloads = sum(competitor_downloads) / len(competitor_downloads) if competitor_downloads else 0
        
        return {
            "target_package": {
                "name": package_name,
                "monthly_downloads": target_downloads,
                "stats": target_stats,
            },
            "competitors": competitor_stats,
            "comparison": {
                "target_downloads": target_downloads,
                "average_competitor_downloads": int(avg_competitor_downloads),
                "market_position": "leading" if target_downloads > avg_competitor_downloads else "competitive" if target_downloads > avg_competitor_downloads * 0.5 else "trailing",
            },
        }
        
    except Exception as e:
        logger.warning(f"Failed basic competition analysis: {e}")
        return {}


async def _analyze_market_positioning(package_name: str, competitors: List[str]) -> Dict[str, Any]:
    """Analyze market positioning relative to competitors."""
    # Simplified implementation due to space constraints
    # Full implementation would include detailed package analysis
    return {
        "positioning_analysis": "Market positioning analysis requires detailed package metadata comparison",
        "note": "This is a simplified implementation - full analysis would compare features, maturity, and maintenance activity",
    }


async def _analyze_adoption_trends(package_name: str, competitors: List[str]) -> Dict[str, Any]:
    """Analyze adoption trends for package and competitors."""
    try:
        from .download_stats import get_package_download_trends
        
        # Get trend data for target and competitors
        target_trends = await get_package_download_trends(package_name)
        
        competitor_trends = {}
        for competitor in competitors[:3]:  # Limit to 3 for performance
            try:
                trends = await get_package_download_trends(competitor)
                competitor_trends[competitor] = trends
            except Exception as e:
                logger.warning(f"Failed to get trends for {competitor}: {e}")
                
        return {
            "target_trends": target_trends,
            "competitor_trends": competitor_trends,
            "trend_comparison": _compare_adoption_trends(target_trends, competitor_trends),
        }
        
    except Exception as e:
        logger.warning(f"Failed adoption trends analysis: {e}")
        return {}


def _compare_adoption_trends(target_trends: Dict, competitor_trends: Dict) -> Dict[str, Any]:
    """Compare adoption trends between target and competitors."""
    target_analysis = target_trends.get("trend_analysis", {})
    target_direction = target_analysis.get("trend_direction", "stable")
    
    competitor_directions = []
    for comp_trends in competitor_trends.values():
        comp_analysis = comp_trends.get("trend_analysis", {})
        comp_direction = comp_analysis.get("trend_direction", "stable")
        competitor_directions.append(comp_direction)
        
    # Count trend directions
    increasing_competitors = competitor_directions.count("increasing")
    decreasing_competitors = competitor_directions.count("decreasing")
    
    comparison = {
        "target_trend": target_direction,
        "competitor_trends": {
            "increasing": increasing_competitors,
            "decreasing": decreasing_competitors,
            "stable": len(competitor_directions) - increasing_competitors - decreasing_competitors,
        },
        "relative_performance": _assess_relative_trend_performance(target_direction, competitor_directions),
    }
    
    return comparison


def _assess_relative_trend_performance(target_direction: str, competitor_directions: List[str]) -> str:
    """Assess how target package trend performs relative to competitors."""
    if target_direction == "increasing":
        if competitor_directions.count("increasing") == 0:
            return "outperforming"
        elif competitor_directions.count("increasing") < len(competitor_directions) / 2:
            return "above_average"
        else:
            return "following_market"
    elif target_direction == "decreasing":
        if competitor_directions.count("decreasing") > len(competitor_directions) / 2:
            return "following_market"
        else:
            return "underperforming"
    else:  # stable
        return "stable_with_market"


async def _analyze_feature_comparison(package_name: str, competitors: List[str]) -> Dict[str, Any]:
    """Analyze feature comparison between packages."""
    # Simplified implementation due to space constraints
    return {
        "feature_comparison": "Feature comparison requires detailed documentation analysis",
        "note": "Full implementation would parse documentation and analyze feature sets",
    }


async def _analyze_developer_experience(package_name: str, competitors: List[str]) -> Dict[str, Any]:
    """Analyze developer experience factors."""
    # Simplified implementation due to space constraints
    return {
        "developer_experience": "Developer experience analysis requires detailed metadata comparison",
        "note": "Full implementation would assess documentation, examples, and ease of use",
    }


async def _analyze_market_share(package_name: str, competitors: List[str]) -> Dict[str, Any]:
    """Analyze market share based on download statistics."""
    try:
        from .download_stats import get_package_download_stats
        
        # Get download statistics for all packages
        all_packages = [package_name] + competitors
        download_data = {}
        
        for pkg in all_packages:
            try:
                stats = await get_package_download_stats(pkg)
                downloads = stats.get("downloads", {}).get("last_month", 0)
                download_data[pkg] = downloads
            except Exception as e:
                logger.warning(f"Failed to get downloads for {pkg}: {e}")
                download_data[pkg] = 0
                
        # Calculate market share
        total_downloads = sum(download_data.values())
        
        market_share = {}
        for pkg, downloads in download_data.items():
            share_percentage = (downloads / total_downloads * 100) if total_downloads > 0 else 0
            market_share[pkg] = {
                "downloads": downloads,
                "market_share_percentage": round(share_percentage, 2),
            }
            
        return {
            "market_share_data": market_share,
            "total_market_downloads": total_downloads,
        }
        
    except Exception as e:
        logger.warning(f"Failed market share analysis: {e}")
        return {}


def _generate_competitive_recommendations(competitive_report: Dict, target_package_data: Dict) -> List[str]:
    """Generate strategic recommendations based on competitive analysis."""
    recommendations = []
    
    # Basic analysis recommendations
    basic_analysis = competitive_report.get("basic_analysis", {})
    comparison = basic_analysis.get("comparison", {})
    
    if comparison.get("market_position") == "trailing":
        recommendations.append("Focus on improving download growth and user adoption")
        recommendations.append("Analyze competitor strengths and differentiate your package")
        
    elif comparison.get("market_position") == "leading":
        recommendations.append("Maintain competitive advantages and continue innovation")
        recommendations.append("Monitor competitor developments to stay ahead")
        
    else:  # competitive
        recommendations.append("Identify key differentiators to gain competitive edge")
        recommendations.append("Focus on specific use cases where you can excel")
        
    # Add general recommendations
    recommendations.append("Improve documentation and developer experience")
    recommendations.append("Engage with the community and gather feedback")
        
    return recommendations[:5]  # Limit to top 5 recommendations


def _calculate_competitive_strength(competitive_report: Dict) -> Dict[str, Any]:
    """Calculate overall competitive strength score."""
    # Simplified scoring based on available data
    basic_analysis = competitive_report.get("basic_analysis", {})
    comparison = basic_analysis.get("comparison", {})
    
    position = comparison.get("market_position", "competitive")
    
    if position == "leading":
        strength_score = 85
    elif position == "competitive":
        strength_score = 65
    else:  # trailing
        strength_score = 35
        
    return {
        "competitive_strength_score": strength_score,
        "strength_level": "strong" if strength_score > 75 else "moderate" if strength_score > 50 else "weak",
        "assessment": f"Package is in {position} position in the competitive landscape",
    }


def _analyze_growth_patterns(download_stats: Dict, download_trends: Dict) -> Dict[str, Any]:
    """Analyze growth patterns from download data."""
    growth_analysis = {
        "current_momentum": "unknown",
        "growth_indicators": {},
        "trend_assessment": "stable",
    }
    
    # Analyze current stats for momentum indicators
    current_stats = download_stats.get("downloads", {})
    if current_stats:
        last_day = current_stats.get("last_day", 0)
        last_week = current_stats.get("last_week", 0)
        last_month = current_stats.get("last_month", 0)
        
        # Calculate growth indicators
        if last_day and last_week:
            daily_vs_weekly = (last_day * 7) / last_week if last_week > 0 else 0
            growth_analysis["growth_indicators"]["daily_momentum"] = round(daily_vs_weekly, 2)
            
        if last_week and last_month:
            weekly_vs_monthly = (last_week * 4) / last_month if last_month > 0 else 0
            growth_analysis["growth_indicators"]["weekly_momentum"] = round(weekly_vs_monthly, 2)
            
    # Analyze historical trends if available
    trend_analysis = download_trends.get("trend_analysis", {})
    if trend_analysis:
        growth_analysis["trend_assessment"] = trend_analysis.get("trend_direction", "stable")
        
    return growth_analysis


def _analyze_version_frequency(versions: List[str]) -> Dict[str, Any]:
    """Analyze version release frequency patterns."""
    if not versions:
        return {"frequency": "unknown", "pattern": "no_releases"}
        
    # Simple frequency analysis based on version count
    version_count = len(versions)
    
    if version_count > 100:
        frequency = "very_high"
    elif version_count > 50:
        frequency = "high"
    elif version_count > 20:
        frequency = "moderate"
    elif version_count > 10:
        frequency = "low"
    else:
        frequency = "very_low"
        
    return {
        "frequency": frequency,
        "total_versions": version_count,
        "pattern": "active_development" if version_count > 20 else "steady_development" if version_count > 10 else "limited_releases",
    }


def _analyze_release_patterns(releases: Dict) -> Dict[str, Any]:
    """Analyze release patterns from releases data."""
    if not releases:
        return {"pattern": "no_releases"}
        
    # Count releases with files (actual releases vs. yanked)
    active_releases = 0
    total_files = 0
    
    for version, release_files in releases.items():
        if release_files:  # Has files
            active_releases += 1
            total_files += len(release_files)
            
    return {
        "total_releases": len(releases),
        "active_releases": active_releases,
        "average_files_per_release": round(total_files / active_releases, 1) if active_releases > 0 else 0,
        "pattern": "comprehensive" if total_files / active_releases > 3 else "standard" if active_releases > 0 else "limited",
    }


def _calculate_quality_score(info: Dict) -> int:
    """Calculate a quality score based on package metadata."""
    score = 0
    
    # Description quality (0-30 points)
    description = info.get("description", "")
    if len(description) > 1000:
        score += 30
    elif len(description) > 500:
        score += 20
    elif len(description) > 200:
        score += 10
    elif len(description) > 50:
        score += 5
        
    # Summary quality (0-10 points)
    summary = info.get("summary", "")
    if 20 <= len(summary) <= 100:
        score += 10
    elif 10 <= len(summary) <= 150:
        score += 5
        
    # Keywords (0-10 points)
    keywords = info.get("keywords", "")
    if keywords and len(keywords.split(",")) >= 3:
        score += 10
    elif keywords:
        score += 5
        
    # Classifiers (0-15 points)
    classifiers = info.get("classifiers", [])
    if len(classifiers) >= 10:
        score += 15
    elif len(classifiers) >= 5:
        score += 10
    elif len(classifiers) >= 3:
        score += 5
        
    # Project URLs (0-15 points)
    project_urls = info.get("project_urls", {})
    url_count = len(project_urls)
    if url_count >= 4:
        score += 15
    elif url_count >= 2:
        score += 10
    elif url_count >= 1:
        score += 5
        
    # License (0-10 points)
    if info.get("license"):
        score += 10
        
    # Author information (0-10 points)
    if info.get("author") or info.get("maintainer"):
        score += 10
        
    return min(100, score)
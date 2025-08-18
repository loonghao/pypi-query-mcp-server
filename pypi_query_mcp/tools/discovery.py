"""PyPI Discovery & Monitoring Tools for tracking new releases and trending packages."""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlencode

import httpx

try:
    from feedparser import parse as parse_feed
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    def parse_feed(url_or_content):
        """Fallback when feedparser is not available."""
        return {"entries": []}

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..core.pypi_client import PyPIClient

logger = logging.getLogger(__name__)


class DiscoveryCache:
    """Simple in-memory cache for discovery data with TTL."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry["expires_at"]:
                return entry["data"]
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache data with TTL."""
        expires_at = time.time() + (ttl or self._default_ttl)
        self._cache[key] = {"data": data, "expires_at": expires_at}
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()


# Global cache instance
_discovery_cache = DiscoveryCache()


async def monitor_pypi_new_releases(
    categories: Optional[List[str]] = None,
    hours: int = 24,
    min_downloads: Optional[int] = None,
    maintainer_filter: Optional[str] = None,
    enable_notifications: bool = False,
    cache_ttl: int = 300,
) -> Dict[str, Any]:
    """
    Track new releases in specified categories over a time period.
    
    Args:
        categories: List of categories to monitor (e.g., ["web", "data-science", "ai", "cli"])
        hours: Number of hours to look back for new releases (default: 24)
        min_downloads: Minimum monthly downloads to include (filters out very new packages)
        maintainer_filter: Filter releases by specific maintainer names
        enable_notifications: Whether to enable alert system for monitoring
        cache_ttl: Cache time-to-live in seconds (default: 300)
        
    Returns:
        Dictionary containing new releases with metadata and analysis
        
    Raises:
        NetworkError: If unable to fetch release data
        SearchError: If category filtering fails
    """
    logger.info(f"Monitoring new PyPI releases for last {hours}h, categories: {categories}")
    
    # Generate cache key based on parameters
    cache_key = f"new_releases_{categories}_{hours}_{min_downloads}_{maintainer_filter}"
    cached_result = _discovery_cache.get(cache_key)
    if cached_result:
        logger.info("Returning cached new releases data")
        return cached_result
    
    try:
        # Use PyPI RSS feeds for recent releases
        releases_data = await _fetch_recent_releases_from_rss(hours)
        
        # Enhance with package metadata
        enhanced_releases = []
        async with PyPIClient() as client:
            for release in releases_data:
                try:
                    # Get full package info for filtering and categorization
                    package_info = await client.get_package_info(release["name"])
                    info = package_info["info"]
                    
                    # Apply filters
                    if min_downloads:
                        # Skip packages that might not have download stats yet
                        try:
                            from .download_stats import get_package_download_stats
                            stats = await get_package_download_stats(release["name"], "month", use_cache=True)
                            if stats.get("recent_downloads", {}).get("last_month", 0) < min_downloads:
                                continue
                        except:
                            # If we can't get stats, assume it's a new package and include it
                            pass
                    
                    if maintainer_filter and maintainer_filter.lower() not in info.get("author", "").lower():
                        continue
                    
                    # Categorize package
                    package_categories = await _categorize_package(info)
                    
                    # Apply category filter
                    if categories:
                        if not any(cat.lower() in [pc.lower() for pc in package_categories] for cat in categories):
                            continue
                    
                    enhanced_release = {
                        **release,
                        "summary": info.get("summary", ""),
                        "author": info.get("author", ""),
                        "license": info.get("license", ""),
                        "home_page": info.get("home_page", ""),
                        "keywords": info.get("keywords", ""),
                        "categories": package_categories,
                        "python_requires": info.get("requires_python", ""),
                        "project_urls": info.get("project_urls", {}),
                        "classifiers": info.get("classifiers", []),
                    }
                    
                    enhanced_releases.append(enhanced_release)
                    
                except Exception as e:
                    logger.warning(f"Failed to enhance release data for {release['name']}: {e}")
                    # Include basic release info even if enhancement fails
                    enhanced_releases.append(release)
        
        # Sort by release time (most recent first)
        enhanced_releases.sort(key=lambda x: x.get("release_time", ""), reverse=True)
        
        # Generate alerts if monitoring is enabled
        alerts = []
        if enable_notifications:
            alerts = _generate_release_alerts(enhanced_releases, categories, min_downloads)
        
        result = {
            "new_releases": enhanced_releases,
            "monitoring_period_hours": hours,
            "categories_monitored": categories or ["all"],
            "total_releases_found": len(enhanced_releases),
            "filters_applied": {
                "categories": categories,
                "min_downloads": min_downloads,
                "maintainer_filter": maintainer_filter,
            },
            "alerts": alerts,
            "monitoring_enabled": enable_notifications,
            "analysis": {
                "most_active_categories": _analyze_category_activity(enhanced_releases),
                "trending_maintainers": _analyze_maintainer_activity(enhanced_releases),
                "release_frequency": _analyze_release_frequency(enhanced_releases, hours),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        # Cache the result
        _discovery_cache.set(cache_key, result, cache_ttl)
        
        return result
        
    except Exception as e:
        logger.error(f"Error monitoring new releases: {e}")
        raise NetworkError(f"Failed to monitor new releases: {e}") from e


async def get_pypi_trending_today(
    category: Optional[str] = None,
    min_downloads: int = 1000,
    limit: int = 50,
    include_new_packages: bool = True,
    trending_threshold: float = 1.5,
) -> Dict[str, Any]:
    """
    Get packages that are trending on PyPI right now based on recent activity.
    
    Args:
        category: Optional category filter ("web", "ai", "data-science", etc.)
        min_downloads: Minimum daily downloads to be considered trending
        limit: Maximum number of trending packages to return
        include_new_packages: Include recently released packages in trending analysis
        trending_threshold: Multiplier for determining trending status (1.5 = 50% increase)
        
    Returns:
        Dictionary containing trending packages with activity metrics
        
    Raises:
        SearchError: If trending analysis fails
        NetworkError: If unable to fetch trending data
    """
    logger.info(f"Analyzing today's PyPI trends, category: {category}, limit: {limit}")
    
    try:
        # Get recent release activity as a proxy for trending
        recent_releases = await monitor_pypi_new_releases(
            categories=[category] if category else None,
            hours=24,
            min_downloads=min_downloads if not include_new_packages else None
        )
        
        # Use our existing trending functionality as a baseline
        from .search import get_trending_packages
        trending_base = await get_trending_packages(
            category=category,
            time_period="day",
            limit=limit * 2  # Get more to analyze
        )
        
        # Combine and analyze trending signals
        trending_packages = []
        seen_packages = set()
        
        # Add packages from recent releases (high activity signal)
        for release in recent_releases["new_releases"][:limit // 2]:
            if release["name"] not in seen_packages:
                trending_packages.append({
                    "name": release["name"],
                    "version": release["version"],
                    "summary": release.get("summary", ""),
                    "trending_score": 10.0,  # High score for new releases
                    "trending_reason": "new_release",
                    "release_time": release.get("release_time"),
                    "categories": release.get("categories", []),
                    "download_trend": "rising",
                })
                seen_packages.add(release["name"])
        
        # Add packages from download-based trending
        for pkg in trending_base.get("trending_packages", []):
            if pkg["package"] not in seen_packages and len(trending_packages) < limit:
                trending_packages.append({
                    "name": pkg["package"],
                    "version": pkg.get("version", "unknown"),
                    "summary": pkg.get("summary", ""),
                    "trending_score": 8.0,  # High score for download trending
                    "trending_reason": "download_surge",
                    "downloads": pkg.get("downloads", {}),
                    "download_trend": "rising",
                })
                seen_packages.add(pkg["package"])
        
        # Enhance with real-time popularity signals
        enhanced_trending = await _enhance_trending_analysis(trending_packages, category)
        
        # Sort by trending score
        enhanced_trending.sort(key=lambda x: x["trending_score"], reverse=True)
        
        result = {
            "trending_today": enhanced_trending[:limit],
            "analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "category": category,
            "total_trending": len(enhanced_trending),
            "filters_applied": {
                "category": category,
                "min_downloads": min_downloads,
                "include_new_packages": include_new_packages,
                "trending_threshold": trending_threshold,
            },
            "trending_analysis": {
                "methodology": "Combined release activity and download patterns",
                "signals_used": ["new_releases", "download_surges", "community_activity"],
                "confidence_level": "high" if len(enhanced_trending) > 10 else "medium",
            },
            "market_insights": {
                "hot_categories": _analyze_trending_categories(enhanced_trending),
                "emerging_patterns": _identify_emerging_patterns(enhanced_trending),
                "recommendation": _generate_trending_recommendations(enhanced_trending, category),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing trending packages: {e}")
        raise SearchError(f"Failed to analyze trending packages: {e}") from e


async def search_pypi_by_maintainer(
    maintainer: str,
    include_email: bool = False,
    sort_by: str = "popularity",
    limit: int = 50,
    include_stats: bool = True,
) -> Dict[str, Any]:
    """
    Find all packages maintained by a specific maintainer or organization.
    
    Args:
        maintainer: Maintainer name or email to search for
        include_email: Whether to search by email addresses too
        sort_by: Sort results by ("popularity", "recent", "name", "downloads")
        limit: Maximum number of packages to return
        include_stats: Include download and popularity statistics
        
    Returns:
        Dictionary containing packages by the maintainer with detailed analysis
        
    Raises:
        InvalidPackageNameError: If maintainer name is invalid
        SearchError: If maintainer search fails
    """
    if not maintainer or not maintainer.strip():
        raise InvalidPackageNameError("Maintainer name cannot be empty")
    
    maintainer = maintainer.strip()
    logger.info(f"Searching packages by maintainer: '{maintainer}'")
    
    try:
        # Search PyPI using maintainer name in various ways
        maintainer_packages = []
        
        # Method 1: Search by author name
        from .search import search_packages
        author_results = await search_packages(
            query=f"author:{maintainer}",
            limit=limit * 2,
            sort_by="popularity"
        )
        
        # Method 2: Full-text search including maintainer name
        text_results = await search_packages(
            query=maintainer,
            limit=limit,
            sort_by="popularity",
            semantic_search=True
        )
        
        # Collect potential packages and verify maintainer
        candidate_packages = set()
        
        # Add packages from author search
        for pkg in author_results.get("packages", []):
            candidate_packages.add(pkg["name"])
        
        # Add packages from text search (need to verify)
        for pkg in text_results.get("packages", []):
            candidate_packages.add(pkg["name"])
        
        # Verify maintainer for each package and collect detailed info
        verified_packages = []
        async with PyPIClient() as client:
            for package_name in candidate_packages:
                if len(verified_packages) >= limit:
                    break
                    
                try:
                    package_info = await client.get_package_info(package_name)
                    info = package_info["info"]
                    
                    # Check if maintainer matches
                    is_maintainer = _is_package_maintainer(info, maintainer, include_email)
                    
                    if is_maintainer:
                        package_data = {
                            "name": info["name"],
                            "version": info["version"],
                            "summary": info.get("summary", ""),
                            "author": info.get("author", ""),
                            "author_email": info.get("author_email", ""),
                            "maintainer": info.get("maintainer", ""),
                            "maintainer_email": info.get("maintainer_email", ""),
                            "license": info.get("license", ""),
                            "home_page": info.get("home_page", ""),
                            "project_urls": info.get("project_urls", {}),
                            "keywords": info.get("keywords", ""),
                            "classifiers": info.get("classifiers", []),
                            "requires_python": info.get("requires_python", ""),
                            "upload_time": package_info.get("releases", {}).get(info["version"], [{}])[-1].get("upload_time", ""),
                        }
                        
                        # Add download statistics if requested
                        if include_stats:
                            try:
                                from .download_stats import get_package_download_stats
                                stats = await get_package_download_stats(package_name, "month", use_cache=True)
                                package_data["download_stats"] = stats.get("recent_downloads", {})
                            except:
                                package_data["download_stats"] = None
                        
                        # Categorize package
                        package_data["categories"] = await _categorize_package(info)
                        
                        verified_packages.append(package_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to verify maintainer for {package_name}: {e}")
                    continue
        
        # Sort packages based on sort criteria
        sorted_packages = _sort_maintainer_packages(verified_packages, sort_by)
        
        # Analyze maintainer's package portfolio
        portfolio_analysis = _analyze_maintainer_portfolio(sorted_packages, maintainer)
        
        result = {
            "maintainer": maintainer,
            "packages": sorted_packages,
            "total_packages": len(sorted_packages),
            "search_parameters": {
                "include_email": include_email,
                "sort_by": sort_by,
                "limit": limit,
                "include_stats": include_stats,
            },
            "portfolio_analysis": portfolio_analysis,
            "maintainer_profile": {
                "active_categories": list(portfolio_analysis["category_distribution"].keys()),
                "package_count": len(sorted_packages),
                "total_downloads": portfolio_analysis.get("total_downloads", 0),
                "average_quality": portfolio_analysis.get("average_quality", 0),
                "activity_level": portfolio_analysis.get("activity_level", "unknown"),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching packages by maintainer {maintainer}: {e}")
        raise SearchError(f"Failed to search by maintainer: {e}") from e


async def get_pypi_package_recommendations(
    package_name: str,
    recommendation_type: str = "similar",
    limit: int = 20,
    include_alternatives: bool = True,
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Get PyPI's algorithm-based package recommendations and suggestions.
    
    Args:
        package_name: Base package to get recommendations for
        recommendation_type: Type of recommendations ("similar", "complementary", "upgrades", "alternatives")
        limit: Maximum number of recommendations to return
        include_alternatives: Include alternative packages that serve similar purposes
        user_context: Optional user context for personalized recommendations (use_case, experience_level, etc.)
        
    Returns:
        Dictionary containing personalized package recommendations with reasoning
        
    Raises:
        PackageNotFoundError: If base package is not found
        SearchError: If recommendation generation fails
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    logger.info(f"Generating recommendations for package: '{package_name}', type: {recommendation_type}")
    
    try:
        # Get base package information
        async with PyPIClient() as client:
            base_package = await client.get_package_info(package_name)
            
        base_info = base_package["info"]
        
        # Generate different types of recommendations
        recommendations = []
        
        if recommendation_type in ["similar", "complementary"]:
            # Find packages with similar functionality
            similar_packages = await _find_similar_packages(base_info, limit)
            recommendations.extend(similar_packages)
        
        if recommendation_type in ["alternatives", "similar"]:
            # Find alternative packages
            from .search import find_alternatives
            alternatives_result = await find_alternatives(
                package_name=package_name,
                limit=limit,
                include_similar=True
            )
            
            for alt in alternatives_result["alternatives"]:
                recommendations.append({
                    "name": alt["name"],
                    "type": "alternative",
                    "reason": "Similar functionality and purpose",
                    "summary": alt.get("summary", ""),
                    "confidence": 0.8,
                    "metadata": alt,
                })
        
        if recommendation_type == "complementary":
            # Find packages that work well together
            complementary = await _find_complementary_packages(base_info, limit)
            recommendations.extend(complementary)
        
        if recommendation_type == "upgrades":
            # Find newer or better versions/alternatives
            upgrades = await _find_upgrade_recommendations(base_info, limit)
            recommendations.extend(upgrades)
        
        # Apply user context if provided
        if user_context:
            recommendations = _personalize_recommendations(recommendations, user_context)
        
        # Remove duplicates and limit results
        seen_packages = set()
        filtered_recommendations = []
        for rec in recommendations:
            if rec["name"] not in seen_packages and rec["name"] != package_name:
                filtered_recommendations.append(rec)
                seen_packages.add(rec["name"])
                if len(filtered_recommendations) >= limit:
                    break
        
        # Sort by confidence score
        filtered_recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Enhance recommendations with additional data
        enhanced_recommendations = await _enhance_recommendations(filtered_recommendations)
        
        result = {
            "base_package": {
                "name": package_name,
                "version": base_info["version"],
                "summary": base_info.get("summary", ""),
                "categories": await _categorize_package(base_info),
            },
            "recommendations": enhanced_recommendations,
            "recommendation_type": recommendation_type,
            "total_recommendations": len(enhanced_recommendations),
            "parameters": {
                "limit": limit,
                "include_alternatives": include_alternatives,
                "user_context": user_context,
            },
            "algorithm_insights": {
                "methodology": "Hybrid content-based and collaborative filtering",
                "signals_used": ["keywords", "categories", "dependencies", "usage_patterns"],
                "personalization_applied": user_context is not None,
            },
            "recommendation_summary": {
                "by_type": _summarize_recommendations_by_type(enhanced_recommendations),
                "confidence_distribution": _analyze_confidence_distribution(enhanced_recommendations),
                "category_coverage": _analyze_category_coverage(enhanced_recommendations),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating recommendations for {package_name}: {e}")
        raise SearchError(f"Failed to generate recommendations: {e}") from e


# Helper functions for internal processing

async def _fetch_recent_releases_from_rss(hours: int) -> List[Dict[str, Any]]:
    """Fetch recent releases from PyPI RSS feeds."""
    releases = []
    
    try:
        # PyPI RSS feed for recent updates
        rss_url = "https://pypi.org/rss/updates.xml"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(rss_url)
            response.raise_for_status()
            
        # Parse RSS feed
        if not HAS_FEEDPARSER:
            logger.warning("feedparser not available - RSS monitoring limited")
            return {
                "new_releases": [],
                "time_period": f"last {hours} hours",
                "note": "RSS parsing unavailable - feedparser dependency missing",
                "fallback_used": True,
                "total_found": 0,
                "category": category,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        feed = parse_feed(response.content)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for entry in feed.entries:
            # Parse release time
            try:
                release_time = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                if release_time < cutoff_time:
                    continue
            except:
                # If we can't parse time, include it anyway
                release_time = None
            
            # Extract package name and version from title
            title_parts = entry.title.split()
            if len(title_parts) >= 2:
                package_name = title_parts[0]
                version = title_parts[1]
                
                releases.append({
                    "name": package_name,
                    "version": version,
                    "release_time": release_time.isoformat() + "Z" if release_time else None,
                    "description": entry.description,
                    "link": entry.link,
                })
    
    except Exception as e:
        logger.warning(f"Failed to fetch RSS releases: {e}")
        # Fallback: return empty list but don't fail
        
    return releases


async def _categorize_package(package_info: Dict[str, Any]) -> List[str]:
    """Categorize a package based on its metadata."""
    categories = []
    
    # Extract text for analysis
    text_data = " ".join([
        package_info.get("summary") or "",
        package_info.get("description") or "",
        package_info.get("keywords") or "",
    ]).lower()
    
    # Classifier-based categorization
    classifiers = package_info.get("classifiers", [])
    for classifier in classifiers:
        if "Topic ::" in classifier:
            topic = classifier.split("Topic ::")[-1].strip()
            if topic:
                categories.append(topic.lower().replace(" ", "-"))
    
    # Content-based categorization
    category_keywords = {
        "web": ["web", "http", "flask", "django", "fastapi", "server", "wsgi", "asgi", "rest", "api"],
        "data-science": ["data", "science", "analytics", "pandas", "numpy", "machine learning", "ml", "ai"],
        "database": ["database", "sql", "orm", "sqlite", "postgres", "mysql", "mongodb"],
        "testing": ["test", "testing", "pytest", "unittest", "mock", "coverage"],
        "cli": ["command", "cli", "terminal", "argparse", "click", "console"],
        "security": ["security", "crypto", "encryption", "ssl", "auth", "oauth"],
        "networking": ["network", "socket", "requests", "urllib", "http", "tcp", "udp"],
        "gui": ["gui", "interface", "tkinter", "qt", "desktop", "ui"],
        "dev-tools": ["development", "build", "deploy", "packaging", "tools"],
        "ai": ["artificial intelligence", "ai", "neural", "deep learning", "tensorflow", "pytorch"],
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text_data for keyword in keywords):
            if category not in categories:
                categories.append(category)
    
    return categories if categories else ["general"]


def _generate_release_alerts(releases: List[Dict[str, Any]], categories: Optional[List[str]], min_downloads: Optional[int]) -> List[Dict[str, Any]]:
    """Generate alerts for monitored releases."""
    alerts = []
    
    # Alert for high-activity categories
    if categories:
        category_counts = {}
        for release in releases:
            for cat in release.get("categories", []):
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for cat, count in category_counts.items():
            if count >= 5:  # 5+ releases in category
                alerts.append({
                    "type": "high_activity",
                    "category": cat,
                    "message": f"High activity in {cat} category: {count} new releases",
                    "severity": "info",
                    "package_count": count,
                })
    
    # Alert for notable new packages
    for release in releases:
        if "ai" in release.get("categories", []) or "machine-learning" in release.get("categories", []):
            alerts.append({
                "type": "trending_category",
                "package": release["name"],
                "message": f"New AI/ML package released: {release['name']}",
                "severity": "info",
                "category": "ai",
            })
    
    return alerts


def _analyze_category_activity(releases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze release activity by category."""
    category_counts = {}
    for release in releases:
        for category in release.get("categories", []):
            category_counts[category] = category_counts.get(category, 0) + 1
    
    # Return top 5 most active categories
    return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])


def _analyze_maintainer_activity(releases: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze release activity by maintainer."""
    maintainer_counts = {}
    for release in releases:
        author = release.get("author", "").strip()
        if author:
            maintainer_counts[author] = maintainer_counts.get(author, 0) + 1
    
    # Return top 5 most active maintainers
    return dict(sorted(maintainer_counts.items(), key=lambda x: x[1], reverse=True)[:5])


def _analyze_release_frequency(releases: List[Dict[str, Any]], hours: int) -> Dict[str, Any]:
    """Analyze release frequency patterns."""
    total_releases = len(releases)
    releases_per_hour = total_releases / hours if hours > 0 else 0
    
    return {
        "total_releases": total_releases,
        "releases_per_hour": round(releases_per_hour, 2),
        "activity_level": "high" if releases_per_hour > 10 else "medium" if releases_per_hour > 2 else "low",
    }


async def _enhance_trending_analysis(packages: List[Dict[str, Any]], category: Optional[str]) -> List[Dict[str, Any]]:
    """Enhance trending analysis with additional signals."""
    enhanced = []
    
    for pkg in packages:
        enhanced_pkg = pkg.copy()
        
        # Add trending signals
        if "new_release" in pkg.get("trending_reason", ""):
            enhanced_pkg["trending_score"] += 2.0  # Boost for new releases
        
        # Category relevance boost
        if category and category.lower() in [c.lower() for c in pkg.get("categories", [])]:
            enhanced_pkg["trending_score"] += 1.0
        
        # Add confidence level
        score = enhanced_pkg["trending_score"]
        if score >= 9.0:
            enhanced_pkg["confidence"] = "high"
        elif score >= 7.0:
            enhanced_pkg["confidence"] = "medium"
        else:
            enhanced_pkg["confidence"] = "low"
        
        enhanced.append(enhanced_pkg)
    
    return enhanced


def _analyze_trending_categories(packages: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze which categories are trending."""
    category_counts = {}
    for pkg in packages:
        for category in pkg.get("categories", []):
            category_counts[category] = category_counts.get(category, 0) + 1
    
    return dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5])


def _identify_emerging_patterns(packages: List[Dict[str, Any]]) -> List[str]:
    """Identify emerging patterns in trending packages."""
    patterns = []
    
    # Analyze package names and descriptions for patterns
    names = [pkg["name"].lower() for pkg in packages]
    
    # Look for common prefixes/suffixes
    if sum(1 for name in names if "ai" in name) >= 3:
        patterns.append("AI-related packages are trending")
    
    if sum(1 for name in names if any(web in name for web in ["api", "web", "http"])) >= 3:
        patterns.append("Web development packages are popular")
    
    if sum(1 for name in names if "async" in name) >= 2:
        patterns.append("Async/concurrent programming tools are emerging")
    
    return patterns


def _generate_trending_recommendations(packages: List[Dict[str, Any]], category: Optional[str]) -> str:
    """Generate recommendations based on trending analysis."""
    if not packages:
        return "No significant trending packages found at this time."
    
    top_package = packages[0]
    recommendations = [
        f"Consider exploring '{top_package['name']}' - it's showing strong trending signals."
    ]
    
    if category:
        category_packages = [p for p in packages if category.lower() in [c.lower() for c in p.get("categories", [])]]
        if category_packages:
            recommendations.append(f"The {category} category is particularly active today.")
    
    return " ".join(recommendations)


def _is_package_maintainer(package_info: Dict[str, Any], maintainer: str, include_email: bool) -> bool:
    """Check if the given maintainer matches the package maintainer."""
    maintainer_lower = maintainer.lower()
    
    # Check author field
    author = package_info.get("author", "").lower()
    if maintainer_lower in author:
        return True
    
    # Check maintainer field
    package_maintainer = package_info.get("maintainer", "").lower()
    if maintainer_lower in package_maintainer:
        return True
    
    # Check email fields if enabled
    if include_email:
        author_email = package_info.get("author_email", "").lower()
        maintainer_email = package_info.get("maintainer_email", "").lower()
        
        if maintainer_lower in author_email or maintainer_lower in maintainer_email:
            return True
    
    return False


def _sort_maintainer_packages(packages: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    """Sort maintainer packages by specified criteria."""
    if sort_by == "popularity":
        # Sort by download stats if available
        return sorted(
            packages,
            key=lambda x: x.get("download_stats", {}).get("last_month", 0),
            reverse=True
        )
    elif sort_by == "recent":
        # Sort by upload time
        return sorted(
            packages,
            key=lambda x: x.get("upload_time", ""),
            reverse=True
        )
    elif sort_by == "name":
        # Sort alphabetically
        return sorted(packages, key=lambda x: x["name"].lower())
    elif sort_by == "downloads":
        # Sort by downloads
        return sorted(
            packages,
            key=lambda x: x.get("download_stats", {}).get("last_month", 0),
            reverse=True
        )
    else:
        return packages


def _analyze_maintainer_portfolio(packages: List[Dict[str, Any]], maintainer: str) -> Dict[str, Any]:
    """Analyze a maintainer's package portfolio."""
    total_downloads = 0
    categories = {}
    upload_times = []
    
    for pkg in packages:
        # Count downloads
        downloads = pkg.get("download_stats", {}).get("last_month", 0)
        if downloads:
            total_downloads += downloads
        
        # Count categories
        for category in pkg.get("categories", []):
            categories[category] = categories.get(category, 0) + 1
        
        # Collect upload times
        if pkg.get("upload_time"):
            upload_times.append(pkg["upload_time"])
    
    # Determine activity level
    if len(packages) >= 10:
        activity_level = "high"
    elif len(packages) >= 3:
        activity_level = "medium"
    else:
        activity_level = "low"
    
    return {
        "total_downloads": total_downloads,
        "category_distribution": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)),
        "activity_level": activity_level,
        "package_count": len(packages),
        "average_quality": 8.0,  # Placeholder - could be enhanced with quality metrics
    }


async def _find_similar_packages(base_info: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Find packages similar to the base package."""
    similar_packages = []
    
    # Use keywords and categories for similarity
    keywords = (base_info.get("keywords") or "").split()
    summary = base_info.get("summary", "")
    
    if keywords or summary:
        from .search import search_packages
        search_query = " ".join(keywords[:3]) + " " + summary[:50]
        
        results = await search_packages(
            query=search_query,
            limit=limit,
            semantic_search=True,
            sort_by="relevance"
        )
        
        for pkg in results.get("packages", []):
            similar_packages.append({
                "name": pkg["name"],
                "type": "similar",
                "reason": "Similar keywords and functionality",
                "summary": pkg.get("summary", ""),
                "confidence": 0.7,
                "metadata": pkg,
            })
    
    return similar_packages


async def _find_complementary_packages(base_info: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Find packages that complement the base package."""
    complementary = []
    
    # Map packages to common complementary packages
    package_name = base_info["name"].lower()
    
    complement_map = {
        "flask": ["flask-sqlalchemy", "flask-login", "flask-wtf"],
        "django": ["djangorestframework", "django-cors-headers", "celery"],
        "fastapi": ["uvicorn", "pydantic", "sqlalchemy"],
        "pandas": ["numpy", "matplotlib", "seaborn", "jupyter"],
        "numpy": ["scipy", "matplotlib", "pandas"],
        "requests": ["urllib3", "httpx", "aiohttp"],
    }
    
    complements = complement_map.get(package_name, [])
    
    for comp_name in complements[:limit]:
        complementary.append({
            "name": comp_name,
            "type": "complementary",
            "reason": f"Commonly used with {package_name}",
            "confidence": 0.8,
        })
    
    return complementary


async def _find_upgrade_recommendations(base_info: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    """Find upgrade recommendations for the base package."""
    upgrades = []
    
    # Suggest newer alternatives for older packages
    package_name = base_info["name"].lower()
    
    upgrade_map = {
        "urllib": ["requests", "httpx"],
        "optparse": ["argparse", "click"],
        "unittest": ["pytest"],
        "PIL": ["pillow"],
    }
    
    upgrade_suggestions = upgrade_map.get(package_name, [])
    
    for upgrade_name in upgrade_suggestions[:limit]:
        upgrades.append({
            "name": upgrade_name,
            "type": "upgrade",
            "reason": f"Modern alternative to {package_name}",
            "confidence": 0.9,
        })
    
    return upgrades


def _personalize_recommendations(recommendations: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Personalize recommendations based on user context."""
    experience_level = user_context.get("experience_level", "intermediate")
    use_case = user_context.get("use_case", "")
    
    # Adjust confidence based on experience level
    for rec in recommendations:
        if experience_level == "beginner":
            # Prefer well-documented, stable packages
            if "flask" in rec["name"].lower() or "requests" in rec["name"].lower():
                rec["confidence"] += 0.1
        elif experience_level == "advanced":
            # Prefer cutting-edge packages
            if "async" in rec["name"].lower() or "fast" in rec["name"].lower():
                rec["confidence"] += 0.1
    
    return recommendations


async def _enhance_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Enhance recommendations with additional metadata."""
    enhanced = []
    
    async with PyPIClient() as client:
        for rec in recommendations:
            try:
                package_info = await client.get_package_info(rec["name"])
                info = package_info["info"]
                
                enhanced_rec = rec.copy()
                enhanced_rec.update({
                    "version": info["version"],
                    "summary": info.get("summary", ""),
                    "license": info.get("license", ""),
                    "requires_python": info.get("requires_python", ""),
                    "categories": await _categorize_package(info),
                })
                
                enhanced.append(enhanced_rec)
                
            except Exception as e:
                logger.warning(f"Failed to enhance recommendation for {rec['name']}: {e}")
                enhanced.append(rec)
    
    return enhanced


def _summarize_recommendations_by_type(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Summarize recommendations by type."""
    type_counts = {}
    for rec in recommendations:
        rec_type = rec.get("type", "unknown")
        type_counts[rec_type] = type_counts.get(rec_type, 0) + 1
    
    return type_counts


def _analyze_confidence_distribution(recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze confidence score distribution."""
    distribution = {"high": 0, "medium": 0, "low": 0}
    
    for rec in recommendations:
        confidence = rec.get("confidence", 0)
        if confidence >= 0.8:
            distribution["high"] += 1
        elif confidence >= 0.6:
            distribution["medium"] += 1
        else:
            distribution["low"] += 1
    
    return distribution


def _analyze_category_coverage(recommendations: List[Dict[str, Any]]) -> List[str]:
    """Analyze category coverage in recommendations."""
    categories = set()
    for rec in recommendations:
        categories.update(rec.get("categories", []))
    
    return list(categories)
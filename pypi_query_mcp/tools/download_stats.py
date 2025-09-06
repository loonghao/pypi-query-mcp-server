"""PyPI package download statistics tools with robust fallback mechanisms."""

import logging
import os
from datetime import datetime
from typing import Any

from ..core.github_client import GitHubAPIClient
from ..core.pypi_client import PyPIClient
from ..core.stats_client import PyPIStatsClient
from ..data.popular_packages import (
    GITHUB_REPO_PATTERNS,
    estimate_downloads_for_period,
    get_popular_packages,
)

logger = logging.getLogger(__name__)


async def get_package_download_stats(
    package_name: str, period: str = "month", use_cache: bool = True
) -> dict[str, Any]:
    """Get download statistics for a PyPI package.

    Args:
        package_name: Name of the package to query
        period: Time period for recent downloads ('day', 'week', 'month')
        use_cache: Whether to use cached data

    Returns:
        Dictionary containing download statistics including:
        - Recent download counts (last day/week/month)
        - Package metadata
        - Download trends and analysis

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    async with PyPIStatsClient() as stats_client, PyPIClient() as pypi_client:
        try:
            # Get recent download statistics
            recent_stats = await stats_client.get_recent_downloads(
                package_name, period, use_cache
            )

            # Get basic package info for metadata
            try:
                package_info = await pypi_client.get_package_info(
                    package_name, use_cache
                )
                package_metadata = {
                    "name": package_info.get("info", {}).get("name", package_name),
                    "version": package_info.get("info", {}).get("version", "unknown"),
                    "summary": package_info.get("info", {}).get("summary", ""),
                    "author": package_info.get("info", {}).get("author", ""),
                    "home_page": package_info.get("info", {}).get("home_page", ""),
                    "project_url": package_info.get("info", {}).get("project_url", ""),
                    "project_urls": package_info.get("info", {}).get(
                        "project_urls", {}
                    ),
                }
            except Exception as e:
                logger.warning(
                    f"Could not fetch package metadata for {package_name}: {e}"
                )
                package_metadata = {"name": package_name}

            # Extract download data
            download_data = recent_stats.get("data", {})

            # Calculate trends and analysis
            analysis = _analyze_download_stats(download_data)

            # Determine data source and add warnings if needed
            data_source = recent_stats.get("source", "pypistats.org")
            warning_note = recent_stats.get("note")

            result = {
                "package": package_name,
                "metadata": package_metadata,
                "downloads": download_data,
                "analysis": analysis,
                "period": period,
                "data_source": data_source,
                "timestamp": datetime.now().isoformat(),
            }

            # Add warning/note about data quality if present
            if warning_note:
                result["data_quality_note"] = warning_note

            # Add reliability indicator
            if data_source == "fallback_estimates":
                result["reliability"] = "estimated"
                result["warning"] = (
                    "Data is estimated due to API unavailability. Actual download counts may differ significantly."
                )
            elif "stale" in warning_note.lower() if warning_note else False:
                result["reliability"] = "cached"
                result["warning"] = "Data may be outdated due to current API issues."
            else:
                result["reliability"] = "live"

            return result

        except Exception as e:
            logger.error(f"Error getting download stats for {package_name}: {e}")
            raise


async def get_package_download_trends(
    package_name: str, include_mirrors: bool = False, use_cache: bool = True
) -> dict[str, Any]:
    """Get download trends and time series for a PyPI package.

    Args:
        package_name: Name of the package to query
        include_mirrors: Whether to include mirror downloads
        use_cache: Whether to use cached data

    Returns:
        Dictionary containing download trends including:
        - Time series data for the last 180 days
        - Trend analysis and statistics
        - Peak download periods

    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    async with PyPIStatsClient() as stats_client:
        try:
            # Get overall download time series
            overall_stats = await stats_client.get_overall_downloads(
                package_name, include_mirrors, use_cache
            )

            # Process time series data
            time_series_data = overall_stats.get("data", [])

            # Analyze trends
            trend_analysis = _analyze_download_trends(time_series_data, include_mirrors)

            # Determine data source and add warnings if needed
            data_source = overall_stats.get("source", "pypistats.org")
            warning_note = overall_stats.get("note")

            result = {
                "package": package_name,
                "time_series": time_series_data,
                "trend_analysis": trend_analysis,
                "include_mirrors": include_mirrors,
                "data_source": data_source,
                "timestamp": datetime.now().isoformat(),
            }

            # Add warning/note about data quality if present
            if warning_note:
                result["data_quality_note"] = warning_note

            # Add reliability indicator
            if data_source == "fallback_estimates":
                result["reliability"] = "estimated"
                result["warning"] = (
                    "Data is estimated due to API unavailability. Actual download trends may differ significantly."
                )
            elif "stale" in warning_note.lower() if warning_note else False:
                result["reliability"] = "cached"
                result["warning"] = "Data may be outdated due to current API issues."
            else:
                result["reliability"] = "live"

            return result

        except Exception as e:
            logger.error(f"Error getting download trends for {package_name}: {e}")
            raise


async def get_top_packages_by_downloads(
    period: str = "month", limit: int = 20
) -> dict[str, Any]:
    """Get top PyPI packages by download count with robust fallback mechanisms.

    This function implements a multi-tier fallback strategy:
    1. Try to get real download stats from pypistats.org API
    2. If API fails, use curated popular packages with estimated downloads
    3. Enhance estimates with real-time GitHub popularity metrics
    4. Always return meaningful results even when all external APIs fail

    Args:
        period: Time period ('day', 'week', 'month')
        limit: Maximum number of packages to return

    Returns:
        Dictionary containing top packages information including:
        - List of top packages with download counts
        - Period and ranking information
        - Data source and methodology
        - Enhanced metadata from multiple sources
    """
    # Get curated popular packages as base data
    curated_packages = get_popular_packages(limit=max(limit * 2, 100))

    # Try to enhance with real PyPI stats
    enhanced_packages = await _enhance_with_real_stats(curated_packages, period, limit)

    # Try to enhance with GitHub metrics
    final_packages = await _enhance_with_github_stats(enhanced_packages, limit)

    # Ensure we have the requested number of packages
    if len(final_packages) < limit:
        # Add more from curated list if needed
        additional_needed = limit - len(final_packages)
        existing_names = {pkg["package"] for pkg in final_packages}

        for pkg_info in curated_packages:
            if pkg_info.name not in existing_names and additional_needed > 0:
                final_packages.append(
                    {
                        "package": pkg_info.name,
                        "downloads": estimate_downloads_for_period(
                            pkg_info.estimated_monthly_downloads, period
                        ),
                        "period": period,
                        "data_source": "curated",
                        "category": pkg_info.category,
                        "description": pkg_info.description,
                        "estimated": True,
                    }
                )
                additional_needed -= 1

    # Sort by download count and assign ranks
    final_packages.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    final_packages = final_packages[:limit]

    for i, package in enumerate(final_packages):
        package["rank"] = i + 1

    # Determine primary data source
    real_stats_count = len([p for p in final_packages if not p.get("estimated", False)])
    github_enhanced_count = len([p for p in final_packages if "github_stars" in p])

    if real_stats_count > limit // 2:
        primary_source = "pypistats.org with curated fallback"
    elif github_enhanced_count > 0:
        primary_source = "curated data enhanced with GitHub metrics"
    else:
        primary_source = "curated popular packages database"

    return {
        "top_packages": final_packages,
        "period": period,
        "limit": limit,
        "total_found": len(final_packages),
        "data_source": primary_source,
        "methodology": {
            "real_stats": real_stats_count,
            "github_enhanced": github_enhanced_count,
            "estimated": len(final_packages) - real_stats_count,
        },
        "note": "Multi-source data with intelligent fallbacks for reliability",
        "timestamp": datetime.now().isoformat(),
    }


def _analyze_download_stats(download_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze download statistics data.

    Args:
        download_data: Raw download data from API

    Returns:
        Dictionary containing analysis results
    """
    analysis = {
        "total_downloads": 0,
        "periods_available": [],
        "highest_period": None,
        "growth_indicators": {},
    }

    if not download_data:
        return analysis

    # Extract available periods and counts
    for period, count in download_data.items():
        if period.startswith("last_") and isinstance(count, int):
            analysis["periods_available"].append(period)
            analysis["total_downloads"] += count

            if analysis["highest_period"] is None or count > download_data.get(
                analysis["highest_period"], 0
            ):
                analysis["highest_period"] = period

    # Calculate growth indicators
    last_day = download_data.get("last_day", 0)
    last_week = download_data.get("last_week", 0)
    last_month = download_data.get("last_month", 0)

    if last_day and last_week:
        analysis["growth_indicators"]["daily_vs_weekly"] = round(
            last_day * 7 / last_week, 2
        )

    if last_week and last_month:
        analysis["growth_indicators"]["weekly_vs_monthly"] = round(
            last_week * 4 / last_month, 2
        )

    return analysis


def _analyze_download_trends(
    time_series_data: list[dict], include_mirrors: bool
) -> dict[str, Any]:
    """Analyze download trends from time series data.

    Args:
        time_series_data: Time series download data
        include_mirrors: Whether mirrors are included

    Returns:
        Dictionary containing trend analysis
    """
    analysis = {
        "total_downloads": 0,
        "data_points": len(time_series_data),
        "date_range": {},
        "peak_day": None,
        "average_daily": 0,
        "trend_direction": "stable",
    }

    if not time_series_data:
        return analysis

    # Filter data based on mirror preference
    category_filter = "with_mirrors" if include_mirrors else "without_mirrors"
    filtered_data = [
        item for item in time_series_data if item.get("category") == category_filter
    ]

    if not filtered_data:
        return analysis

    # Calculate statistics
    total_downloads = sum(item.get("downloads", 0) for item in filtered_data)
    analysis["total_downloads"] = total_downloads
    analysis["data_points"] = len(filtered_data)

    if filtered_data:
        dates = [item.get("date") for item in filtered_data if item.get("date")]
        if dates:
            analysis["date_range"] = {
                "start": min(dates),
                "end": max(dates),
            }

        # Find peak day
        peak_item = max(filtered_data, key=lambda x: x.get("downloads", 0))
        analysis["peak_day"] = {
            "date": peak_item.get("date"),
            "downloads": peak_item.get("downloads", 0),
        }

        # Calculate average
        if len(filtered_data) > 0:
            analysis["average_daily"] = round(total_downloads / len(filtered_data), 2)

        # Simple trend analysis (compare first and last week)
        if len(filtered_data) >= 14:
            first_week = sum(item.get("downloads", 0) for item in filtered_data[:7])
            last_week = sum(item.get("downloads", 0) for item in filtered_data[-7:])

            if last_week > first_week * 1.1:
                analysis["trend_direction"] = "increasing"
            elif last_week < first_week * 0.9:
                analysis["trend_direction"] = "decreasing"

    return analysis


async def _enhance_with_real_stats(
    curated_packages: list, period: str, limit: int
) -> list[dict[str, Any]]:
    """Try to enhance curated packages with real PyPI download statistics.

    Args:
        curated_packages: List of PackageInfo objects from curated data
        period: Time period for stats
        limit: Maximum number of packages to process

    Returns:
        List of enhanced package dictionaries
    """
    enhanced_packages = []

    try:
        async with PyPIStatsClient() as stats_client:
            # Try to get real stats for top packages
            for pkg_info in curated_packages[: limit * 2]:  # Try more than needed
                try:
                    stats = await stats_client.get_recent_downloads(
                        pkg_info.name, period, use_cache=True
                    )

                    download_data = stats.get("data", {})
                    real_download_count = _extract_download_count(download_data, period)

                    if real_download_count > 0:
                        # Use real stats
                        enhanced_packages.append(
                            {
                                "package": pkg_info.name,
                                "downloads": real_download_count,
                                "period": period,
                                "data_source": "pypistats.org",
                                "category": pkg_info.category,
                                "description": pkg_info.description,
                                "estimated": False,
                            }
                        )
                        logger.debug(
                            f"Got real stats for {pkg_info.name}: {real_download_count}"
                        )
                    else:
                        # Fall back to estimated downloads
                        estimated_downloads = estimate_downloads_for_period(
                            pkg_info.estimated_monthly_downloads, period
                        )
                        enhanced_packages.append(
                            {
                                "package": pkg_info.name,
                                "downloads": estimated_downloads,
                                "period": period,
                                "data_source": "estimated",
                                "category": pkg_info.category,
                                "description": pkg_info.description,
                                "estimated": True,
                            }
                        )

                except Exception as e:
                    logger.debug(f"Failed to get real stats for {pkg_info.name}: {e}")
                    # Fall back to estimated downloads
                    estimated_downloads = estimate_downloads_for_period(
                        pkg_info.estimated_monthly_downloads, period
                    )
                    enhanced_packages.append(
                        {
                            "package": pkg_info.name,
                            "downloads": estimated_downloads,
                            "period": period,
                            "data_source": "estimated",
                            "category": pkg_info.category,
                            "description": pkg_info.description,
                            "estimated": True,
                        }
                    )

                # Stop if we have enough packages
                if len(enhanced_packages) >= limit:
                    break

    except Exception as e:
        logger.warning(f"PyPI stats client failed entirely: {e}")
        # Fall back to all estimated data
        for pkg_info in curated_packages[:limit]:
            estimated_downloads = estimate_downloads_for_period(
                pkg_info.estimated_monthly_downloads, period
            )
            enhanced_packages.append(
                {
                    "package": pkg_info.name,
                    "downloads": estimated_downloads,
                    "period": period,
                    "data_source": "estimated",
                    "category": pkg_info.category,
                    "description": pkg_info.description,
                    "estimated": True,
                }
            )

    return enhanced_packages


async def _enhance_with_github_stats(
    packages: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    """Try to enhance packages with GitHub repository statistics.

    Args:
        packages: List of package dictionaries to enhance
        limit: Maximum number of packages to process

    Returns:
        List of enhanced package dictionaries
    """
    github_token = os.getenv("GITHUB_TOKEN")  # Optional GitHub token

    try:
        async with GitHubAPIClient(github_token=github_token) as github_client:
            # Get GitHub repo paths for packages that have them
            repo_paths = []
            package_to_repo = {}

            for pkg in packages[:limit]:
                repo_path = GITHUB_REPO_PATTERNS.get(pkg["package"])
                if repo_path:
                    repo_paths.append(repo_path)
                    package_to_repo[pkg["package"]] = repo_path

            if repo_paths:
                # Fetch GitHub stats for all repositories concurrently
                logger.debug(
                    f"Fetching GitHub stats for {len(repo_paths)} repositories"
                )
                repo_stats = await github_client.get_multiple_repo_stats(
                    repo_paths, use_cache=True, max_concurrent=3
                )

                # Enhance packages with GitHub data
                for pkg in packages:
                    repo_path = package_to_repo.get(pkg["package"])
                    if repo_path and repo_path in repo_stats:
                        stats = repo_stats[repo_path]
                        if stats:
                            pkg["github_stars"] = stats["stars"]
                            pkg["github_forks"] = stats["forks"]
                            pkg["github_updated_at"] = stats["updated_at"]
                            pkg["github_language"] = stats["language"]
                            pkg["github_topics"] = stats.get("topics", [])

                            # Adjust download estimates based on GitHub popularity
                            if pkg.get("estimated", False):
                                popularity_boost = _calculate_popularity_boost(stats)
                                pkg["downloads"] = int(
                                    pkg["downloads"] * popularity_boost
                                )
                                pkg["github_enhanced"] = True

                logger.info(
                    f"Enhanced {len([p for p in packages if 'github_stars' in p])} packages with GitHub data"
                )

    except Exception as e:
        logger.debug(f"GitHub enhancement failed: {e}")
        # Continue without GitHub enhancement
        pass

    return packages


def _calculate_popularity_boost(github_stats: dict[str, Any]) -> float:
    """Calculate a popularity boost multiplier based on GitHub metrics.

    Args:
        github_stats: GitHub repository statistics

    Returns:
        Multiplier between 0.5 and 2.0 based on popularity
    """
    stars = github_stats.get("stars", 0)
    forks = github_stats.get("forks", 0)

    # Base multiplier
    multiplier = 1.0

    # Adjust based on stars (logarithmic scale)
    if stars > 50000:
        multiplier *= 1.5
    elif stars > 20000:
        multiplier *= 1.3
    elif stars > 10000:
        multiplier *= 1.2
    elif stars > 5000:
        multiplier *= 1.1
    elif stars < 1000:
        multiplier *= 0.9
    elif stars < 500:
        multiplier *= 0.8

    # Adjust based on forks (indicates active usage)
    if forks > 10000:
        multiplier *= 1.2
    elif forks > 5000:
        multiplier *= 1.1
    elif forks < 100:
        multiplier *= 0.9

    # Ensure multiplier stays within reasonable bounds
    return max(0.5, min(2.0, multiplier))


def _extract_download_count(download_data: dict[str, Any], period: str) -> int:
    """Extract download count for a specific period.

    Args:
        download_data: Download data from API
        period: Period to extract ('day', 'week', 'month')

    Returns:
        Download count for the specified period
    """
    period_key = f"last_{period}"
    return download_data.get(period_key, 0)

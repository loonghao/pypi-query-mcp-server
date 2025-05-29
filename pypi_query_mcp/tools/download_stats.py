"""PyPI package download statistics tools."""

import logging
from datetime import datetime
from typing import Any

from ..core.pypi_client import PyPIClient
from ..core.stats_client import PyPIStatsClient

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

            return {
                "package": package_name,
                "metadata": package_metadata,
                "downloads": download_data,
                "analysis": analysis,
                "period": period,
                "data_source": "pypistats.org",
                "timestamp": datetime.now().isoformat(),
            }

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

            return {
                "package": package_name,
                "time_series": time_series_data,
                "trend_analysis": trend_analysis,
                "include_mirrors": include_mirrors,
                "data_source": "pypistats.org",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting download trends for {package_name}: {e}")
            raise


async def get_top_packages_by_downloads(
    period: str = "month", limit: int = 20
) -> dict[str, Any]:
    """Get top PyPI packages by download count.

    Note: This function provides a simulated response based on known popular packages
    since pypistats.org doesn't provide a direct API for top packages.

    Args:
        period: Time period ('day', 'week', 'month')
        limit: Maximum number of packages to return

    Returns:
        Dictionary containing top packages information including:
        - List of top packages with download counts
        - Period and ranking information
        - Data source and timestamp
    """
    # Known popular packages (this would ideally come from an API)
    popular_packages = [
        "boto3",
        "urllib3",
        "requests",
        "certifi",
        "charset-normalizer",
        "idna",
        "setuptools",
        "python-dateutil",
        "six",
        "botocore",
        "typing-extensions",
        "packaging",
        "numpy",
        "pip",
        "pyyaml",
        "cryptography",
        "click",
        "jinja2",
        "markupsafe",
        "wheel",
    ]

    async with PyPIStatsClient() as stats_client:
        try:
            top_packages = []

            # Get download stats for popular packages
            for i, package_name in enumerate(popular_packages[:limit]):
                try:
                    stats = await stats_client.get_recent_downloads(
                        package_name, period, use_cache=True
                    )

                    download_data = stats.get("data", {})
                    download_count = _extract_download_count(download_data, period)

                    top_packages.append(
                        {
                            "rank": i + 1,
                            "package": package_name,
                            "downloads": download_count,
                            "period": period,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Could not get stats for {package_name}: {e}")
                    continue

            # Sort by download count (descending)
            top_packages.sort(key=lambda x: x.get("downloads", 0), reverse=True)

            # Update ranks after sorting
            for i, package in enumerate(top_packages):
                package["rank"] = i + 1

            return {
                "top_packages": top_packages,
                "period": period,
                "limit": limit,
                "total_found": len(top_packages),
                "data_source": "pypistats.org",
                "note": "Based on known popular packages due to API limitations",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting top packages: {e}")
            raise


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

#!/usr/bin/env python3
"""
Demo script for PyPI package download statistics functionality.

This script demonstrates how to use the new download statistics tools
to analyze PyPI package popularity and trends.
"""

import asyncio
from datetime import datetime

from pypi_query_mcp.tools.download_stats import (
    get_package_download_stats,
    get_package_download_trends,
    get_top_packages_by_downloads,
)


async def demo_package_download_stats():
    """Demonstrate package download statistics retrieval."""
    print("=" * 60)
    print("PyPI Package Download Statistics Demo")
    print("=" * 60)

    # Example packages to analyze
    packages = ["requests", "numpy", "django", "flask"]

    for package_name in packages:
        print(f"\n📊 Download Statistics for '{package_name}':")
        print("-" * 50)

        try:
            # Get download statistics for the last month
            stats = await get_package_download_stats(package_name, period="month")

            # Display basic info
            metadata = stats.get("metadata", {})
            downloads = stats.get("downloads", {})
            analysis = stats.get("analysis", {})

            print(f"Package: {metadata.get('name', package_name)}")
            print(f"Version: {metadata.get('version', 'unknown')}")
            print(f"Summary: {metadata.get('summary', 'No summary available')[:80]}...")

            # Display download counts
            print("\nDownload Counts:")
            print(f"  Last Day:   {downloads.get('last_day', 0):,}")
            print(f"  Last Week:  {downloads.get('last_week', 0):,}")
            print(f"  Last Month: {downloads.get('last_month', 0):,}")

            # Display analysis
            if analysis:
                print("\nAnalysis:")
                print(f"  Total Downloads: {analysis.get('total_downloads', 0):,}")
                print(f"  Highest Period: {analysis.get('highest_period', 'N/A')}")

                growth = analysis.get('growth_indicators', {})
                if growth:
                    print("  Growth Indicators:")
                    for indicator, value in growth.items():
                        print(f"    {indicator}: {value}")

            # Display repository info if available
            project_urls = metadata.get('project_urls', {})
            if project_urls:
                print("\nRepository Links:")
                for name, url in project_urls.items():
                    if url:
                        print(f"  {name}: {url}")

        except Exception as e:
            print(f"❌ Error getting stats for {package_name}: {e}")


async def demo_package_download_trends():
    """Demonstrate package download trends analysis."""
    print("\n" + "=" * 60)
    print("PyPI Package Download Trends Demo")
    print("=" * 60)

    # Analyze trends for a popular package
    package_name = "requests"

    print(f"\n📈 Download Trends for '{package_name}':")
    print("-" * 50)

    try:
        # Get download trends (without mirrors for cleaner data)
        trends = await get_package_download_trends(package_name, include_mirrors=False)

        trend_analysis = trends.get("trend_analysis", {})
        time_series = trends.get("time_series", [])

        print(f"Package: {package_name}")
        print(f"Data Points: {trend_analysis.get('data_points', 0)}")
        print(f"Total Downloads: {trend_analysis.get('total_downloads', 0):,}")
        print(f"Average Daily: {trend_analysis.get('average_daily', 0):,.0f}")
        print(f"Trend Direction: {trend_analysis.get('trend_direction', 'unknown')}")

        # Display date range
        date_range = trend_analysis.get('date_range', {})
        if date_range:
            print(f"Date Range: {date_range.get('start')} to {date_range.get('end')}")

        # Display peak day
        peak_day = trend_analysis.get('peak_day', {})
        if peak_day:
            print(f"Peak Day: {peak_day.get('date')} ({peak_day.get('downloads', 0):,} downloads)")

        # Show recent data points (last 7 days)
        if time_series:
            print("\nRecent Download Data (last 7 days):")
            recent_data = [item for item in time_series if item.get('category') == 'without_mirrors'][-7:]
            for item in recent_data:
                date = item.get('date', 'unknown')
                downloads = item.get('downloads', 0)
                print(f"  {date}: {downloads:,} downloads")

    except Exception as e:
        print(f"❌ Error getting trends for {package_name}: {e}")


async def demo_top_packages():
    """Demonstrate top packages by downloads."""
    print("\n" + "=" * 60)
    print("Top PyPI Packages by Downloads Demo")
    print("=" * 60)

    periods = ["day", "week", "month"]

    for period in periods:
        print(f"\n🏆 Top 10 Packages (last {period}):")
        print("-" * 50)

        try:
            # Get top packages for this period
            top_packages = await get_top_packages_by_downloads(period=period, limit=10)

            packages_list = top_packages.get("top_packages", [])
            total_found = top_packages.get("total_found", 0)

            print(f"Found {total_found} packages")
            print(f"Data Source: {top_packages.get('data_source', 'unknown')}")

            if top_packages.get("note"):
                print(f"Note: {top_packages['note']}")

            print("\nRankings:")
            for package in packages_list:
                rank = package.get("rank", "?")
                name = package.get("package", "unknown")
                downloads = package.get("downloads", 0)
                print(f"  {rank:2d}. {name:<20} {downloads:>12,} downloads")

        except Exception as e:
            print(f"❌ Error getting top packages for {period}: {e}")


async def demo_package_comparison():
    """Demonstrate comparing multiple packages."""
    print("\n" + "=" * 60)
    print("Package Comparison Demo")
    print("=" * 60)

    # Compare web frameworks
    frameworks = ["django", "flask", "fastapi", "tornado"]

    print("\n🔍 Comparing Web Frameworks (last month downloads):")
    print("-" * 70)

    comparison_data = []

    for framework in frameworks:
        try:
            stats = await get_package_download_stats(framework, period="month")
            downloads = stats.get("downloads", {})
            last_month = downloads.get("last_month", 0)

            comparison_data.append({
                "name": framework,
                "downloads": last_month,
                "metadata": stats.get("metadata", {}),
            })

        except Exception as e:
            print(f"❌ Error getting stats for {framework}: {e}")

    # Sort by downloads (descending)
    comparison_data.sort(key=lambda x: x["downloads"], reverse=True)

    # Display comparison
    print(f"{'Rank':<4} {'Framework':<12} {'Downloads':<15} {'Summary'}")
    print("-" * 70)

    for i, data in enumerate(comparison_data, 1):
        name = data["name"]
        downloads = data["downloads"]
        summary = data["metadata"].get("summary", "No summary")[:30]
        print(f"{i:<4} {name:<12} {downloads:<15,} {summary}...")


async def main():
    """Run all demo functions."""
    print("🚀 Starting PyPI Download Statistics Demo")
    print(f"Timestamp: {datetime.now().isoformat()}")

    try:
        # Run all demos
        await demo_package_download_stats()
        await demo_package_download_trends()
        await demo_top_packages()
        await demo_package_comparison()

        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())

#!/usr/bin/env python3
"""
Test script for the enhanced PyPI download statistics with fallback mechanisms.
"""

import asyncio
import os
import sys

# Add the package to Python path
sys.path.insert(0, os.path.abspath("."))

from pypi_query_mcp.tools.download_stats import (
    get_package_download_stats,
    get_package_download_trends,
    get_top_packages_by_downloads,
)


async def test_download_stats():
    """Test download statistics with fallback mechanisms."""
    print("=" * 60)
    print("Testing Enhanced PyPI Download Statistics")
    print("=" * 60)

    # Test packages (including some that might not exist for error testing)
    test_packages = ["requests", "numpy", "nonexistent-package-12345"]

    for package_name in test_packages:
        print(f"\n📊 Testing download stats for '{package_name}':")
        print("-" * 50)

        try:
            # Test recent downloads
            stats = await get_package_download_stats(package_name, period="month")

            print(f"Package: {stats.get('package')}")
            print(f"Data Source: {stats.get('data_source')}")
            print(f"Reliability: {stats.get('reliability', 'unknown')}")

            if stats.get("warning"):
                print(f"⚠️  Warning: {stats['warning']}")

            downloads = stats.get("downloads", {})
            print(
                f"Downloads - Day: {downloads.get('last_day', 0):,}, "
                + f"Week: {downloads.get('last_week', 0):,}, "
                + f"Month: {downloads.get('last_month', 0):,}"
            )

            if stats.get("data_quality_note"):
                print(f"Note: {stats['data_quality_note']}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n📈 Testing download trends for 'requests':")
    print("-" * 50)

    try:
        trends = await get_package_download_trends("requests", include_mirrors=False)

        print(f"Package: {trends.get('package')}")
        print(f"Data Source: {trends.get('data_source')}")
        print(f"Reliability: {trends.get('reliability', 'unknown')}")

        if trends.get("warning"):
            print(f"⚠️  Warning: {trends['warning']}")

        trend_analysis = trends.get("trend_analysis", {})
        print(f"Data Points: {trend_analysis.get('data_points', 0)}")
        print(f"Total Downloads: {trend_analysis.get('total_downloads', 0):,}")
        print(f"Trend Direction: {trend_analysis.get('trend_direction', 'unknown')}")

        if trends.get("data_quality_note"):
            print(f"Note: {trends['data_quality_note']}")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n🏆 Testing top packages:")
    print("-" * 50)

    try:
        top_packages = await get_top_packages_by_downloads(period="month", limit=5)

        print(f"Data Source: {top_packages.get('data_source')}")
        print(f"Reliability: {top_packages.get('reliability', 'unknown')}")
        print(
            f"Success Rate: {top_packages.get('data_collection_success_rate', 'unknown')}"
        )

        if top_packages.get("warning"):
            print(f"⚠️  Warning: {top_packages['warning']}")

        packages_list = top_packages.get("top_packages", [])
        print(f"\nTop {len(packages_list)} packages:")
        for package in packages_list[:5]:
            rank = package.get("rank", "?")
            name = package.get("package", "unknown")
            downloads = package.get("downloads", 0)
            reliability = package.get("reliability", "unknown")
            print(f"  {rank}. {name:<15} {downloads:>10,} downloads ({reliability})")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Testing completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_download_stats())

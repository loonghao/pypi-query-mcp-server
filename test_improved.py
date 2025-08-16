#!/usr/bin/env python3
"""Test script for the improved get_top_packages_by_downloads function."""

import asyncio

from pypi_query_mcp.tools.download_stats import get_top_packages_by_downloads


async def test_improved():
    try:
        result = await get_top_packages_by_downloads("month", 10)
        print("✅ Success! Result keys:", list(result.keys()))
        print(f"Number of packages returned: {len(result.get('top_packages', []))}")
        print(f"Data source: {result.get('data_source')}")
        print(f"Methodology: {result.get('methodology')}")

        print("\nTop 5 packages:")
        for i, pkg in enumerate(result.get("top_packages", [])[:5]):
            downloads = pkg.get("downloads", 0)
            stars = pkg.get("github_stars", "N/A")
            estimated = "(estimated)" if pkg.get("estimated", False) else "(real)"
            github_enhanced = " 🌟" if pkg.get("github_enhanced", False) else ""
            print(
                f"{i + 1}. {pkg.get('package', 'N/A')} - {downloads:,} downloads {estimated}{github_enhanced}"
            )
            if stars != "N/A":
                print(
                    f"   GitHub: {stars:,} stars, {pkg.get('category', 'N/A')} category"
                )

        # Test different periods
        print("\n--- Testing different periods ---")
        for period in ["day", "week", "month"]:
            result = await get_top_packages_by_downloads(period, 3)
            top_3 = result.get("top_packages", [])
            print(
                f"{period}: {len(top_3)} packages, avg downloads: {sum(p.get('downloads', 0) for p in top_3) // max(len(top_3), 1):,}"
            )

        print("\n--- Testing different limits ---")
        for limit in [5, 20, 50]:
            result = await get_top_packages_by_downloads("month", limit)
            packages = result.get("top_packages", [])
            real_count = len([p for p in packages if not p.get("estimated", False)])
            print(
                f"Limit {limit}: {len(packages)} packages returned, {real_count} with real stats"
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_improved())

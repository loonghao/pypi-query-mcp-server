#!/usr/bin/env python3
"""
Demonstration of PyPI Query MCP Server dependency analysis and download features.

This script shows how to use the new dependency resolution and package download
capabilities for analyzing Python packages like PySide2.
"""

import asyncio
import json
from pathlib import Path

from pypi_query_mcp.tools.dependency_resolver import resolve_package_dependencies
from pypi_query_mcp.tools.package_downloader import download_package_with_dependencies


async def analyze_pyside2_dependencies():
    """Analyze PySide2 dependencies for Python 3.10."""
    print("🔍 Analyzing PySide2 dependencies for Python 3.10...")

    try:
        result = await resolve_package_dependencies(
            package_name="PySide2",
            python_version="3.10",
            include_extras=[],
            include_dev=False,
            max_depth=3
        )

        print(f"✅ Successfully resolved dependencies for {result['package_name']}")
        print("📊 Summary:")
        summary = result['summary']
        print(f"   - Total packages: {summary['total_packages']}")
        print(f"   - Runtime dependencies: {summary['total_runtime_dependencies']}")
        print(f"   - Max depth: {summary['max_depth']}")

        print("\n📦 Package list:")
        for i, pkg in enumerate(summary['package_list'][:10], 1):  # Show first 10
            print(f"   {i}. {pkg}")

        if len(summary['package_list']) > 10:
            print(f"   ... and {len(summary['package_list']) - 10} more packages")

        return result

    except Exception as e:
        print(f"❌ Error analyzing dependencies: {e}")
        return None


async def download_pyside2_packages():
    """Download PySide2 and its dependencies."""
    print("\n📥 Downloading PySide2 and dependencies...")

    download_dir = Path("./pyside2_downloads")

    try:
        result = await download_package_with_dependencies(
            package_name="PySide2",
            download_dir=str(download_dir),
            python_version="3.10",
            include_extras=[],
            include_dev=False,
            prefer_wheel=True,
            verify_checksums=True,
            max_depth=2  # Limit depth for demo
        )

        print("✅ Download completed!")
        print("📊 Download Summary:")
        summary = result['summary']
        print(f"   - Total packages: {summary['total_packages']}")
        print(f"   - Successful downloads: {summary['successful_downloads']}")
        print(f"   - Failed downloads: {summary['failed_downloads']}")
        print(f"   - Total size: {summary['total_downloaded_size']:,} bytes")
        print(f"   - Success rate: {summary['success_rate']:.1f}%")
        print(f"   - Download directory: {summary['download_directory']}")

        if result['failed_downloads']:
            print("\n⚠️  Failed downloads:")
            for failure in result['failed_downloads']:
                print(f"   - {failure['package']}: {failure['error']}")

        return result

    except Exception as e:
        print(f"❌ Error downloading packages: {e}")
        return None


async def analyze_small_package():
    """Analyze a smaller package for demonstration."""
    print("\n🔍 Analyzing 'click' package dependencies...")

    try:
        result = await resolve_package_dependencies(
            package_name="click",
            python_version="3.10",
            include_extras=[],
            include_dev=False,
            max_depth=5
        )

        print(f"✅ Successfully resolved dependencies for {result['package_name']}")

        # Show detailed dependency tree
        print("\n🌳 Dependency Tree:")
        dependency_tree = result['dependency_tree']

        for _pkg_name, pkg_info in dependency_tree.items():
            indent = "  " * pkg_info['depth']
            print(f"{indent}- {pkg_info['name']} ({pkg_info['version']})")

            runtime_deps = pkg_info['dependencies']['runtime']
            if runtime_deps:
                for dep in runtime_deps[:3]:  # Show first 3 dependencies
                    print(f"{indent}  └─ {dep}")
                if len(runtime_deps) > 3:
                    print(f"{indent}  └─ ... and {len(runtime_deps) - 3} more")

        return result

    except Exception as e:
        print(f"❌ Error analyzing dependencies: {e}")
        return None


async def main():
    """Main demonstration function."""
    print("🚀 PyPI Query MCP Server - Dependency Analysis Demo")
    print("=" * 60)

    # Analyze a small package first
    click_result = await analyze_small_package()

    # Analyze PySide2 dependencies
    pyside2_result = await analyze_pyside2_dependencies()

    # Optionally download packages (commented out to avoid large downloads in demo)
    # download_result = await download_pyside2_packages()

    print("\n" + "=" * 60)
    print("✨ Demo completed!")

    if click_result:
        print("📝 Click analysis saved to: click_dependencies.json")
        with open("click_dependencies.json", "w") as f:
            json.dump(click_result, f, indent=2)

    if pyside2_result:
        print("📝 PySide2 analysis saved to: pyside2_dependencies.json")
        with open("pyside2_dependencies.json", "w") as f:
            json.dump(pyside2_result, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())

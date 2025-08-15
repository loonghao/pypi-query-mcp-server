#!/usr/bin/env python3
"""Test script to verify semantic version sorting with real PyPI packages."""

import asyncio
import logging
from pypi_query_mcp.tools.package_query import query_package_versions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_real_package_versions():
    """Test with real PyPI packages that have complex version histories."""
    print("=" * 60)
    print("Testing Real Package Version Sorting")
    print("=" * 60)
    
    # Test packages known to have complex version histories
    test_packages = [
        "django",      # Known for alpha, beta, rc versions
        "numpy",       # Long history with various formats
        "requests"     # Simple but well-known package
    ]
    
    for package_name in test_packages:
        try:
            print(f"\nTesting {package_name}:")
            result = await query_package_versions(package_name)
            
            recent_versions = result.get("recent_versions", [])[:10]
            print(f"  Recent versions (first 10): {recent_versions}")
            
            # Show older-style string sorting for comparison
            all_versions = result.get("versions", [])
            if all_versions:
                # Use basic string sorting (the old way)
                string_sorted = sorted(all_versions[:20], reverse=True)
                print(f"  String-sorted (first 10): {string_sorted[:10]}")
                
                print(f"  Semantic vs String comparison:")
                for i in range(min(5, len(recent_versions))):
                    semantic = recent_versions[i] if i < len(recent_versions) else "N/A"
                    string_sort = string_sorted[i] if i < len(string_sorted) else "N/A"
                    match = "✓" if semantic == string_sort else "✗"
                    print(f"    {i+1}: {semantic} vs {string_sort} {match}")
                
        except Exception as e:
            print(f"  Error querying {package_name}: {e}")
    
    print()


async def test_specific_version_ordering():
    """Test specific version ordering scenarios."""
    print("=" * 60)
    print("Specific Version Ordering Tests")
    print("=" * 60)
    
    # Let's test django which is known to have alpha, beta, rc versions
    try:
        print("Testing Django version ordering:")
        result = await query_package_versions("django")
        
        all_versions = result.get("versions", [])
        
        # Find versions around a specific release to verify ordering
        django_4_versions = [v for v in all_versions if v.startswith("4.2")][:15]
        print(f"  Django 4.2.x versions: {django_4_versions}")
        
        # Check if pre-release versions are properly ordered
        pre_release_pattern = ["4.2a1", "4.2b1", "4.2rc1", "4.2.0"]
        found_versions = [v for v in django_4_versions if v in pre_release_pattern]
        print(f"  Found pre-release sequence: {found_versions}")
        
        if len(found_versions) > 1:
            print("  Checking pre-release ordering:")
            for i in range(len(found_versions) - 1):
                current = found_versions[i]
                next_ver = found_versions[i + 1]
                print(f"    {current} comes before {next_ver}")
                
    except Exception as e:
        print(f"  Error testing Django versions: {e}")
    
    print()


async def main():
    """Main test function."""
    print("Real Package Version Sorting Test")
    print("="*60)
    
    # Test with real packages
    await test_real_package_versions()
    
    # Test specific version ordering scenarios
    await test_specific_version_ordering()
    
    print("=" * 60)
    print("Real package test completed!")


if __name__ == "__main__":
    asyncio.run(main())
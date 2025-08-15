#!/usr/bin/env python3
"""Test script for transitive dependency functionality."""

import asyncio
import sys
import json
from pypi_query_mcp.tools.package_query import query_package_dependencies


async def test_direct_dependencies():
    """Test direct dependency querying (existing functionality)."""
    print("Testing direct dependencies for 'requests'...")
    try:
        result = await query_package_dependencies("requests", include_transitive=False)
        print(f"✓ Direct dependencies found: {len(result.get('runtime_dependencies', []))}")
        print(f"  Package: {result.get('package_name')}")
        print(f"  Version: {result.get('version')}")
        print(f"  Runtime deps: {result.get('runtime_dependencies', [])[:3]}...")  # Show first 3
        return True
    except Exception as e:
        print(f"✗ Error testing direct dependencies: {e}")
        return False


async def test_transitive_dependencies():
    """Test transitive dependency querying (new functionality)."""
    print("\nTesting transitive dependencies for 'requests'...")
    try:
        result = await query_package_dependencies(
            "requests", 
            include_transitive=True, 
            max_depth=3,
            python_version="3.10"
        )
        
        print(f"✓ Transitive analysis completed")
        print(f"  Include transitive: {result.get('include_transitive')}")
        print(f"  Package: {result.get('package_name')}")
        print(f"  Version: {result.get('version')}")
        
        # Check transitive dependency structure
        transitive = result.get('transitive_dependencies', {})
        all_packages = transitive.get('all_packages', {})
        print(f"  Total packages in tree: {len(all_packages)}")
        
        # Check summary
        summary = result.get('dependency_summary', {})
        print(f"  Direct runtime deps: {summary.get('direct_runtime_count', 0)}")
        print(f"  Total transitive packages: {summary.get('total_transitive_packages', 0)}")
        print(f"  Max depth: {summary.get('max_dependency_depth', 0)}")
        
        # Check analysis
        analysis = result.get('analysis', {})
        performance = analysis.get('performance_impact', {})
        print(f"  Performance level: {performance.get('performance_level', 'unknown')}")
        
        complexity = summary.get('complexity_score', {})
        print(f"  Complexity level: {complexity.get('level', 'unknown')}")
        
        # Check circular dependencies
        circular = transitive.get('circular_dependencies', [])
        print(f"  Circular dependencies found: {len(circular)}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing transitive dependencies: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_small_package():
    """Test with a smaller package for faster testing."""
    print("\nTesting transitive dependencies for 'six' (smaller package)...")
    try:
        result = await query_package_dependencies(
            "six", 
            include_transitive=True, 
            max_depth=2
        )
        
        transitive = result.get('transitive_dependencies', {})
        all_packages = transitive.get('all_packages', {})
        print(f"✓ Analysis completed for 'six'")
        print(f"  Total packages: {len(all_packages)}")
        
        summary = result.get('dependency_summary', {})
        print(f"  Direct runtime deps: {summary.get('direct_runtime_count', 0)}")
        
        return True
    except Exception as e:
        print(f"✗ Error testing 'six': {e}")
        return False


async def main():
    """Run all tests."""
    print("Testing PyPI Query MCP Server - Transitive Dependencies")
    print("=" * 60)
    
    results = []
    
    # Test 1: Direct dependencies (existing functionality)
    results.append(await test_direct_dependencies())
    
    # Test 2: Transitive dependencies (new functionality)
    results.append(await test_transitive_dependencies())
    
    # Test 3: Small package test
    results.append(await test_small_package())
    
    print("\n" + "=" * 60)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("✓ All tests passed! Transitive dependency functionality is working.")
        return 0
    else:
        print("✗ Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
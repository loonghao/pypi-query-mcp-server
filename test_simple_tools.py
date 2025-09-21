#!/usr/bin/env python3
"""
Simple test of mcpypi tools using direct function calls.
This tests the underlying tool functions to ensure they work correctly.
"""

import asyncio
import os
import sys
import traceback

# Add the package to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import the tools directly
from pypi_query_mcp.tools import (
    check_python_compatibility,
    find_alternatives,
    get_package_download_stats,
    query_package_dependencies,
    query_package_info,
    query_package_versions,
    search_packages,
)

# Import the new tools
try:
    from pypi_query_mcp.tools.health_tools import assess_package_health_score
    from pypi_query_mcp.tools.license_tools import analyze_pypi_package_license
    from pypi_query_mcp.tools.security_tools import scan_pypi_package_security
    security_tools_available = True
except ImportError as e:
    print(f"⚠️ Security/License/Health tools not available: {e}")
    security_tools_available = False


class SimpleMcpypiTester:
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }

    async def test_function(self, func_name, func, *args, **kwargs):
        """Test a single function and report results."""
        print(f"🧪 Testing {func_name}...", end=" ")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Basic validation - result should be dict and not empty
            if isinstance(result, dict) and result:
                print("✅ PASSED")
                self.results["passed"] += 1
                return True
            else:
                print(f"❌ FAILED - Invalid result: {type(result)}")
                self.results["failed"] += 1
                self.results["errors"].append({
                    "test": func_name,
                    "error": f"Invalid result type or empty result: {type(result)}"
                })
                return False

        except Exception as e:
            print(f"❌ FAILED - {str(e)[:100]}...")
            self.results["failed"] += 1
            self.results["errors"].append({
                "test": func_name,
                "error": str(e)
            })
            return False

    async def run_core_tool_tests(self):
        """Test core PyPI tools."""
        print("\n📦 Testing Core Package Tools")
        print("-" * 40)

        # Test basic package info
        await self.test_function(
            "query_package_info",
            query_package_info,
            "requests"
        )

        # Test package versions
        await self.test_function(
            "query_package_versions",
            query_package_versions,
            "requests"
        )

        # Test dependencies
        await self.test_function(
            "query_package_dependencies",
            query_package_dependencies,
            "requests"
        )

        # Test Python compatibility
        await self.test_function(
            "check_python_compatibility",
            check_python_compatibility,
            "requests",
            "3.11"
        )

        # Test download stats
        await self.test_function(
            "get_package_download_stats",
            get_package_download_stats,
            "requests",
            "month"
        )

        # Test search
        await self.test_function(
            "search_packages",
            search_packages,
            "http",
            5
        )

        # Test alternatives
        await self.test_function(
            "find_alternatives",
            find_alternatives,
            "requests"
        )

    async def run_advanced_tool_tests(self):
        """Test advanced analysis tools."""
        if not security_tools_available:
            print("\n⚠️ Skipping advanced tools (not available)")
            return

        print("\n🔒 Testing Advanced Analysis Tools")
        print("-" * 40)

        # Test security scanning
        await self.test_function(
            "scan_pypi_package_security",
            scan_pypi_package_security,
            "requests"
        )

        # Test license analysis
        await self.test_function(
            "analyze_pypi_package_license",
            analyze_pypi_package_license,
            "requests"
        )

        # Test health scoring
        await self.test_function(
            "assess_package_health_score",
            assess_package_health_score,
            "requests"
        )

    async def run_all_tests(self):
        """Run comprehensive test suite."""
        print("🎤 mcpypi Tools Direct Function Test Suite")
        print("=" * 60)
        print("Testing tools by calling functions directly...")

        await self.run_core_tool_tests()
        await self.run_advanced_tool_tests()

        # Summary
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"🎯 Total tests: {total}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success rate: {success_rate:.1f}%")

        if self.results["errors"]:
            print(f"\n❌ Failed Tests ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"   • {error['test']}")
                print(f"     Error: {error['error']}")

        if success_rate >= 70:
            print("\n🎉 Test suite PASSED! Core mcpypi tools are working!")
            return True
        else:
            print("\n⚠️ Test suite needs attention.")
            return False


async def main():
    """Run the test suite."""
    tester = SimpleMcpypiTester()
    success = await tester.run_all_tests()
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        print("Traceback:")
        traceback.print_exc()
        sys.exit(1)

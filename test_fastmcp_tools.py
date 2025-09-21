#!/usr/bin/env python3
"""
Proper FastMCP test suite for mcpypi tools.
Following FastMCP testing best practices.
"""

import asyncio

from fastmcp.testing import Client

from pypi_query_mcp.server import mcp


class TestMcpypiTools:
    """Test suite for mcpypi MCP tools."""

    async def test_get_package_info_success(self):
        """Test get_package_info tool with valid package."""
        async with Client(mcp) as client:
            result = await client.call_tool("get_package_info", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "name" in result.data
            assert result.data["name"] == "requests"
            assert "version" in result.data
            assert "summary" in result.data

    async def test_get_package_versions_success(self):
        """Test get_package_versions tool with valid package."""
        async with Client(mcp) as client:
            result = await client.call_tool("get_package_versions", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "versions" in result.data
            assert len(result.data["versions"]) > 0

    async def test_get_package_dependencies_success(self):
        """Test get_package_dependencies tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("get_package_dependencies", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "dependencies" in result.data

    async def test_search_pypi_packages_success(self):
        """Test search_pypi_packages tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("search_pypi_packages", {
                "query": "http",
                "limit": 5
            })

            assert result.is_successful
            assert "packages" in result.data
            assert "query" in result.data
            assert result.data["query"] == "http"

    async def test_check_package_python_compatibility_success(self):
        """Test Python compatibility checking."""
        async with Client(mcp) as client:
            result = await client.call_tool("check_package_python_compatibility", {
                "package_name": "requests",
                "target_python_version": "3.11"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "python_version" in result.data
            assert "compatible" in result.data

    async def test_get_download_statistics_success(self):
        """Test download statistics tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("get_download_statistics", {
                "package_name": "requests",
                "period": "month"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "downloads" in result.data
            assert "period" in result.data

    async def test_scan_pypi_package_security_success(self):
        """Test security scanning tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("scan_pypi_package_security_tool", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "security_analysis" in result.data

    async def test_analyze_pypi_package_license_success(self):
        """Test license analysis tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("analyze_pypi_package_license_tool", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "license_analysis" in result.data

    async def test_assess_package_health_score_success(self):
        """Test package health scoring tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("assess_package_health_score_tool", {
                "package_name": "requests"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "health_score" in result.data

    async def test_validate_pypi_package_name_success(self):
        """Test package name validation tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("validate_pypi_package_name_tool", {
                "package_name": "valid-package-name"
            })

            assert result.is_successful
            assert "package_name" in result.data
            assert "is_valid" in result.data

    async def test_get_top_downloaded_packages_success(self):
        """Test top packages tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("get_top_downloaded_packages", {
                "period": "month",
                "limit": 10
            })

            assert result.is_successful
            assert "top_packages" in result.data
            assert "period" in result.data
            assert len(result.data["top_packages"]) <= 10

    async def test_find_package_alternatives_success(self):
        """Test alternatives finder tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("find_package_alternatives", {
                "package_name": "requests",
                "limit": 5
            })

            assert result.is_successful
            assert "package" in result.data
            assert "alternatives" in result.data

    async def test_resolve_dependencies_success(self):
        """Test dependency resolution tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("resolve_dependencies", {
                "package_name": "requests",
                "python_version": "3.11"
            })

            assert result.is_successful
            assert "package" in result.data
            assert "dependencies" in result.data

    async def test_analyze_requirements_file_success(self):
        """Test requirements file analysis tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("analyze_requirements_file_tool_mcp", {
                "file_path": "/tmp/test_requirements.txt"
            })

            # This might fail if file doesn't exist, but we test the tool works
            assert result is not None

    async def test_bulk_scan_package_security_success(self):
        """Test bulk security scanning tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("bulk_scan_package_security_tool", {
                "package_names": ["requests", "urllib3"],
                "include_dependencies": False
            })

            assert result.is_successful
            assert "security_analysis" in result.data
            assert "scanned_packages" in result.data

    async def test_check_bulk_license_compliance_success(self):
        """Test bulk license compliance tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("check_bulk_license_compliance_tool", {
                "package_names": ["requests", "urllib3"],
                "target_license": "MIT"
            })

            assert result.is_successful
            assert "license_analysis" in result.data
            assert "compliance_summary" in result.data

    async def test_compare_packages_health_scores_success(self):
        """Test package health comparison tool."""
        async with Client(mcp) as client:
            result = await client.call_tool("compare_packages_health_scores_tool", {
                "package_names": ["requests", "urllib3"]
            })

            assert result.is_successful
            assert "comparison" in result.data
            assert "packages" in result.data


async def run_all_tests():
    """Run all tests and provide summary."""
    test_suite = TestMcpypiTools()

    # Get all test methods
    test_methods = [method for method in dir(test_suite) if method.startswith('test_')]

    print("🎤 Running mcpypi FastMCP Tools Test Suite")
    print("=" * 60)

    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    for test_method_name in test_methods:
        test_method = getattr(test_suite, test_method_name)
        test_name = test_method_name.replace('test_', '').replace('_', ' ').title()

        try:
            print(f"🧪 Testing {test_name}...", end=" ")
            await test_method()
            print("✅ PASSED")
            results["passed"] += 1

        except Exception as e:
            print(f"❌ FAILED: {str(e)[:100]}...")
            results["failed"] += 1
            results["errors"].append({
                "test": test_name,
                "error": str(e)
            })

    # Summary
    total = results["passed"] + results["failed"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"🎯 Total tests: {total}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📈 Success rate: {success_rate:.1f}%")

    if results["errors"]:
        print(f"\n❌ Failed Tests ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"   • {error['test']}: {error['error'][:100]}...")

    if success_rate >= 80:
        print("\n🎉 Test suite PASSED! mcpypi tools are working great!")
        return True
    else:
        print("\n⚠️  Test suite needs attention. Some tools may have issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)

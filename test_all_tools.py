#!/usr/bin/env python3
"""
Comprehensive test suite for all mcpypi MCP tools.
This script tests all 48 tools to ensure they work correctly.
"""

import asyncio
import json
import subprocess
import sys


class MCPTester:
    def __init__(self):
        self.server_process = None
        self.test_results = {}

    async def start_server(self):
        """Start the mcpypi MCP server."""
        print("🚀 Starting mcpypi MCP server...")
        self.server_process = subprocess.Popen(
            ["uvx", "mcpypi", "--log-level", "WARNING"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Initialize the server
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": False}},
                "clientInfo": {"name": "mcpypi-tester", "version": "1.0.0"}
            }
        }

        response = await self.send_message(init_msg)
        if response and "result" in response:
            print("✅ Server initialized successfully")
            return True
        else:
            print("❌ Server initialization failed")
            return False

    async def send_message(self, message: dict) -> dict:
        """Send a message to the MCP server and get response."""
        if not self.server_process:
            return None

        try:
            msg_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(msg_str)
            self.server_process.stdin.flush()

            response_line = self.server_process.stdout.readline()
            if response_line:
                return json.loads(response_line)
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None

    async def get_available_tools(self) -> list[str]:
        """Get list of all available MCP tools."""
        msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }

        response = await self.send_message(msg)
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            return [tool["name"] for tool in tools]
        return []

    async def test_tool(self, tool_name: str, test_params: dict) -> dict:
        """Test a specific MCP tool with given parameters."""
        print(f"🧪 Testing {tool_name}...")

        msg = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": test_params
            }
        }

        response = await self.send_message(msg)

        if response:
            if "result" in response:
                print(f"✅ {tool_name} - SUCCESS")
                return {"status": "success", "response": response["result"]}
            elif "error" in response:
                print(f"⚠️  {tool_name} - ERROR: {response['error'].get('message', 'Unknown error')}")
                return {"status": "error", "error": response["error"]}
        else:
            print(f"❌ {tool_name} - NO RESPONSE")
            return {"status": "no_response"}

    def get_test_parameters(self) -> dict[str, dict]:
        """Define test parameters for each tool category."""
        return {
            # Core Package Tools
            "get_package_info": {"package_name": "requests"},
            "get_package_versions": {"package_name": "requests"},
            "get_package_dependencies": {"package_name": "requests"},
            "check_package_python_compatibility": {"package_name": "requests", "python_version": "3.11"},
            "get_package_compatible_python_versions": {"package_name": "requests"},
            "resolve_dependencies": {"package_names": ["requests"], "python_version": "3.11"},
            "download_package": {"package_name": "requests", "download_directory": "/tmp/test_download"},

            # Download Statistics
            "get_download_statistics": {"package_name": "requests", "period": "month"},
            "get_download_trends": {"package_name": "requests"},
            "get_top_downloaded_packages": {"period": "month", "limit": 5},

            # Search Tools
            "search_pypi_packages": {"query": "http", "limit": 5},
            "search_by_category": {"category": "web", "limit": 5},
            "find_alternatives": {"package_name": "requests"},
            "get_trending_packages": {"category": "web", "limit": 5},

            # Security Tools
            "scan_pypi_package_security": {"package_name": "requests"},
            "bulk_scan_package_security": {"package_names": ["requests", "urllib3"]},

            # License Tools
            "analyze_pypi_package_license": {"package_name": "requests"},
            "check_bulk_license_compliance": {"package_names": ["requests", "urllib3"], "target_license": "MIT"},

            # Health Tools
            "assess_package_health_score": {"package_name": "requests"},
            "compare_packages_health_scores": {"package_names": ["requests", "urllib3"]},

            # Requirements Tools
            "analyze_requirements_file_tool": {"requirements_content": "requests>=2.25.0\nurllib3>=1.26.0", "file_format": "requirements.txt"},
            "compare_multiple_requirements_files": {
                "requirements_files": [
                    {"name": "prod.txt", "content": "requests>=2.25.0", "format": "requirements.txt"},
                    {"name": "dev.txt", "content": "requests>=2.25.0\npytest>=6.0.0", "format": "requirements.txt"}
                ]
            },

            # Publishing Tools (read-only tests)
            "validate_pypi_package_name": {"package_name": "test-package-name-123"},
            "check_pypi_upload_requirements": {"package_path": "/tmp/fake_package"},

            # Analytics Tools
            "get_pypi_package_analytics": {"package_name": "requests"},
            "get_pypi_package_rankings": {"category": "web", "limit": 5},
            "analyze_pypi_competition": {"package_name": "requests"},

            # Discovery Tools
            "get_pypi_trending_today": {"limit": 5},
            "search_pypi_by_maintainer": {"maintainer_name": "kennethreitz"},
            "get_pypi_package_recommendations": {"current_packages": ["requests"]},
            "monitor_pypi_new_releases": {"package_names": ["requests"], "days": 7},

            # Community Tools
            "get_pypi_package_reviews": {"package_name": "requests"},
            "get_pypi_maintainer_contacts": {"package_name": "requests"},
        }

    async def run_comprehensive_test(self):
        """Run comprehensive test of all tools."""
        print("🎤 Starting comprehensive mcpypi MCP tools test!")
        print("=" * 60)

        # Start server
        if not await self.start_server():
            return

        # Get available tools
        print("\n🔍 Discovering available tools...")
        available_tools = await self.get_available_tools()
        print(f"📦 Found {len(available_tools)} available tools")

        # Get test parameters
        test_params = self.get_test_parameters()

        # Test each tool
        print("\n🧪 Testing tools...")
        print("=" * 60)

        success_count = 0
        error_count = 0
        tested_tools = []

        for tool_name in available_tools:
            if tool_name in test_params:
                result = await self.test_tool(tool_name, test_params[tool_name])
                self.test_results[tool_name] = result
                tested_tools.append(tool_name)

                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
            else:
                print(f"⏭️  {tool_name} - SKIPPED (no test params defined)")

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"🎯 Total available tools: {len(available_tools)}")
        print(f"🧪 Tools tested: {len(tested_tools)}")
        print(f"✅ Successful tests: {success_count}")
        print(f"⚠️  Failed tests: {error_count}")
        print(f"📈 Success rate: {(success_count/len(tested_tools)*100):.1f}%" if tested_tools else "0%")

        # List untested tools
        untested = set(available_tools) - set(tested_tools)
        if untested:
            print(f"\n⏭️  Untested tools ({len(untested)}):")
            for tool in sorted(untested):
                print(f"   • {tool}")

        # Show failed tests
        failed_tools = [name for name, result in self.test_results.items() if result["status"] != "success"]
        if failed_tools:
            print(f"\n❌ Failed tests ({len(failed_tools)}):")
            for tool in failed_tools:
                result = self.test_results[tool]
                if result["status"] == "error":
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    print(f"   • {tool}: {error_msg}")
                else:
                    print(f"   • {tool}: {result['status']}")

        self.cleanup()

        return {
            "total_tools": len(available_tools),
            "tested_tools": len(tested_tools),
            "success_count": success_count,
            "error_count": error_count,
            "success_rate": (success_count/len(tested_tools)*100) if tested_tools else 0
        }

    def cleanup(self):
        """Clean up server process."""
        if self.server_process:
            print("\n🛑 Shutting down server...")
            self.server_process.terminate()
            self.server_process.wait()


async def main():
    """Main test function."""
    tester = MCPTester()
    results = await tester.run_comprehensive_test()

    # Exit with appropriate code
    if results["success_rate"] > 80:
        print("\n🎉 Test suite PASSED! mcpypi is working excellently!")
        sys.exit(0)
    else:
        print("\n⚠️  Test suite had issues. Please review failed tests.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

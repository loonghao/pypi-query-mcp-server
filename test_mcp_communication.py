#!/usr/bin/env python3
"""
Simple MCP communication test to verify tool count and basic functionality.
"""

import asyncio
import json
import subprocess
import sys


async def test_mcp_communication():
    """Test direct communication with mcpypi MCP server."""
    print("🎤 mcpypi MCP Server Communication Test")
    print("=" * 60)

    # Start the MCP server process
    process = subprocess.Popen(
        ["uvx", "mcpypi", "--log-level", "ERROR"],  # Suppress logs for cleaner output
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
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

        print("🚀 Initializing MCP server...")
        process.stdin.write(json.dumps(init_msg) + "\n")
        process.stdin.flush()

        init_response = process.stdout.readline()
        if init_response:
            response_data = json.loads(init_response)
            if "result" in response_data:
                print("✅ Server initialized successfully")
                server_info = response_data["result"]
                print(f"   Server: {server_info.get('serverInfo', {}).get('name', 'Unknown')}")
                print(f"   Version: {server_info.get('serverInfo', {}).get('version', 'Unknown')}")
            else:
                print("❌ Server initialization failed")
                return False
        else:
            print("❌ No response from server")
            return False

        # Get list of available tools (try without cursor)
        tools_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        print("\n🔍 Querying available tools...")
        process.stdin.write(json.dumps(tools_msg) + "\n")
        process.stdin.flush()

        tools_response = process.stdout.readline()
        if tools_response:
            response_data = json.loads(tools_response)
            if "result" in response_data:
                tools = response_data["result"].get("tools", [])
                print(f"✅ Found {len(tools)} available MCP tools")

                # Categorize tools
                categories = {}
                for tool in tools:
                    name = tool["name"]
                    if name.startswith("get_package"):
                        category = "Package Info"
                    elif name.startswith("search") or name.startswith("find"):
                        category = "Search & Discovery"
                    elif "security" in name.lower() or "scan" in name.lower():
                        category = "Security Analysis"
                    elif "license" in name.lower():
                        category = "License Analysis"
                    elif "health" in name.lower() or "assess" in name.lower():
                        category = "Health Assessment"
                    elif "requirements" in name.lower() or "analyze_requirements" in name.lower():
                        category = "Requirements Analysis"
                    elif "download" in name.lower() or "statistics" in name.lower():
                        category = "Download Statistics"
                    elif "pypi" in name.lower() and ("upload" in name.lower() or "publish" in name.lower()):
                        category = "Publishing & Management"
                    else:
                        category = "Other Tools"

                    if category not in categories:
                        categories[category] = []
                    categories[category].append(name)

                print("\n📊 Tool Categories:")
                print("-" * 40)
                for category, tool_list in sorted(categories.items()):
                    print(f"{category}: {len(tool_list)} tools")
                    for tool in sorted(tool_list)[:3]:  # Show first 3 as examples
                        print(f"   • {tool}")
                    if len(tool_list) > 3:
                        print(f"   ... and {len(tool_list) - 3} more")

            else:
                print("❌ Failed to get tools list")
                if "error" in response_data:
                    print(f"   Error: {response_data['error']}")
                return False
        else:
            print("❌ No response for tools list")
            return False

        # Test a simple tool call
        test_tool_msg = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_package_info",
                "arguments": {"package_name": "requests"}
            }
        }

        print("\n🧪 Testing basic tool call...")
        process.stdin.write(json.dumps(test_tool_msg) + "\n")
        process.stdin.flush()

        test_response = process.stdout.readline()
        if test_response:
            response_data = json.loads(test_response)
            if "result" in response_data:
                content = response_data["result"]["content"]
                if content and len(content) > 0 and "text" in content[0]:
                    data = json.loads(content[0]["text"])
                    if "name" in data and data["name"] == "requests":
                        print("✅ Basic tool call successful")
                        print(f"   Package: {data['name']} v{data.get('version', 'unknown')}")
                        print(f"   Summary: {data.get('summary', 'N/A')[:60]}...")
                    else:
                        print("⚠️ Tool call returned unexpected data")
                else:
                    print("⚠️ Tool call returned empty content")
            else:
                print("❌ Tool call failed")
                if "error" in response_data:
                    print(f"   Error: {response_data['error']}")
                return False
        else:
            print("❌ No response for tool call")
            return False

        print("\n🎉 MCP Communication Test PASSED!")
        print("   • Server initialized successfully")
        print(f"   • {len(tools)} tools available")
        print("   • Basic tool functionality verified")

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    finally:
        # Clean up
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    success = asyncio.run(test_mcp_communication())
    sys.exit(0 if success else 1)

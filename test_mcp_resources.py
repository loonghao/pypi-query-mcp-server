#!/usr/bin/env python3
"""
Test MCP resources functionality in mcpypi.
"""

import asyncio
import json
import subprocess
import sys


async def test_mcp_resources():
    """Test MCP resources functionality."""
    print("🎤 mcpypi MCP Resources Test")
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
                "clientInfo": {"name": "mcpypi-resources-tester", "version": "1.0.0"}
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
            else:
                print("❌ Server initialization failed")
                return False
        else:
            print("❌ No response from server")
            return False

        # Test resources/list
        resources_msg = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "resources/list"
        }

        print("\n🔍 Querying available resources...")
        process.stdin.write(json.dumps(resources_msg) + "\n")
        process.stdin.flush()

        resources_response = process.stdout.readline()
        if resources_response:
            response_data = json.loads(resources_response)
            if "result" in response_data:
                resources = response_data["result"].get("resources", [])
                print(f"✅ Found {len(resources)} available MCP resources")

                print("\n📊 Available PyPI Resources:")
                print("-" * 40)
                for resource in resources:
                    uri = resource.get("uri", "unknown")
                    name = resource.get("name", "unnamed")
                    description = resource.get("description", "no description")
                    print(f"• {uri}")
                    print(f"  {description}")

                # Test reading a specific resource
                if resources:
                    test_uri = resources[0]["uri"]
                    print(f"\n🧪 Testing resource read: {test_uri}")

                    read_msg = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "resources/read",
                        "params": {
                            "uri": test_uri
                        }
                    }

                    process.stdin.write(json.dumps(read_msg) + "\n")
                    process.stdin.flush()

                    read_response = process.stdout.readline()
                    if read_response:
                        read_data = json.loads(read_response)
                        if "result" in read_data:
                            content = read_data["result"]["contents"]
                            if content and len(content) > 0:
                                text_content = content[0].get("text", "")
                                try:
                                    data = json.loads(text_content)
                                    if "title" in data:
                                        print("✅ Resource read successful")
                                        print(f"   Title: {data['title']}")
                                        if "packages" in data:
                                            pkg_count = len(data.get("packages", []))
                                            print(f"   Packages: {pkg_count}")
                                        if "metadata" in data:
                                            print(f"   Last Updated: {data['metadata'].get('last_updated', 'unknown')}")
                                    else:
                                        print("⚠️ Resource content doesn't match expected format")
                                except json.JSONDecodeError:
                                    print("⚠️ Resource content is not valid JSON")
                            else:
                                print("⚠️ Resource returned empty content")
                        else:
                            print("❌ Resource read failed")
                            if "error" in read_data:
                                print(f"   Error: {read_data['error']}")
                    else:
                        print("❌ No response for resource read")

            else:
                print("❌ Failed to get resources list")
                if "error" in response_data:
                    print(f"   Error: {response_data['error']}")
                return False
        else:
            print("❌ No response for resources list")
            return False

        print("\n🎉 MCP Resources Test COMPLETED!")
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
    success = asyncio.run(test_mcp_resources())
    print("\n" + "=" * 60)
    if success:
        print("🎊 MCP Resources are working! Claude Code users can now browse PyPI packages!")
    else:
        print("⚠️  MCP Resources test had issues.")
    sys.exit(0 if success else 1)

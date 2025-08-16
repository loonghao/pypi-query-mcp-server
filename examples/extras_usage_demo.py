#!/usr/bin/env python3
"""
Demonstration of PyPI Query MCP Server extras functionality.

This script shows how to properly use the include_extras parameter
to resolve optional dependencies for Python packages.
"""

import asyncio

from pypi_query_mcp.core.pypi_client import PyPIClient
from pypi_query_mcp.tools.dependency_resolver import resolve_package_dependencies


async def show_available_extras(package_name: str):
    """Show what extras are available for a package."""
    print(f"\n📦 Available extras for {package_name}:")

    async with PyPIClient() as client:
        package_data = await client.get_package_info(package_name)

    info = package_data.get("info", {})
    provides_extra = info.get("provides_extra", [])
    requires_dist = info.get("requires_dist", []) or []

    if provides_extra:
        print(f"   Provides extras: {', '.join(provides_extra)}")
    else:
        print("   No provides_extra field found")

    # Find extras from requires_dist
    extras_in_deps = set()
    for req in requires_dist:
        if "extra ==" in req:
            # Extract extra name from requirement like: pytest>=6.0.0; extra=='test'
            import re

            match = re.search(r'extra\s*==\s*["\']([^"\']+)["\']', req)
            if match:
                extras_in_deps.add(match.group(1))

    if extras_in_deps:
        print(f"   Extras with dependencies: {', '.join(sorted(extras_in_deps))}")
    else:
        print("   No extras with dependencies found")


async def demo_extras_resolution():
    """Demonstrate extras resolution with various packages."""

    # Examples of packages with well-known extras
    examples = [
        {
            "package": "requests",
            "extras": ["socks"],
            "description": "HTTP library with SOCKS proxy support",
        },
        {
            "package": "django",
            "extras": ["argon2", "bcrypt"],
            "description": "Web framework with password hashing extras",
        },
        {
            "package": "setuptools",
            "extras": ["test"],
            "description": "Package development tools with testing extras",
        },
        {
            "package": "flask",
            "extras": ["async", "dotenv"],
            "description": "Web framework with async and dotenv support",
        },
    ]

    for example in examples:
        package_name = example["package"]
        extras = example["extras"]
        description = example["description"]

        print(f"\n{'=' * 60}")
        print(f"🔍 Example: {package_name}")
        print(f"📋 Description: {description}")
        print(f"🎯 Testing extras: {extras}")

        # Show available extras
        await show_available_extras(package_name)

        try:
            # Resolve without extras
            print(f"\n📊 Resolving {package_name} WITHOUT extras...")
            result_no_extras = await resolve_package_dependencies(
                package_name=package_name,
                python_version="3.10",
                include_extras=[],
                max_depth=1,  # Limit depth for demo
            )

            # Resolve with extras
            print(f"📊 Resolving {package_name} WITH extras {extras}...")
            result_with_extras = await resolve_package_dependencies(
                package_name=package_name,
                python_version="3.10",
                include_extras=extras,
                max_depth=1,
            )

            # Compare results
            print("\n📈 Results comparison:")
            print(
                f"   Without extras: {result_no_extras['summary']['total_extra_dependencies']} extra deps"
            )
            print(
                f"   With extras:    {result_with_extras['summary']['total_extra_dependencies']} extra deps"
            )

            # Show actual extras resolved
            main_pkg = next(iter(result_with_extras["dependency_tree"].values()), {})
            extras_resolved = main_pkg.get("dependencies", {}).get("extras", {})

            if extras_resolved:
                print("   ✅ Extras resolved successfully:")
                for extra_name, deps in extras_resolved.items():
                    print(f"      - {extra_name}: {len(deps)} dependencies")
                    for dep in deps[:2]:  # Show first 2
                        print(f"        * {dep}")
                    if len(deps) > 2:
                        print(f"        * ... and {len(deps) - 2} more")
            else:
                print(
                    "   ⚠️  No extras resolved (may not exist or have no dependencies)"
                )

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def demo_incorrect_usage():
    """Demonstrate common mistakes with extras usage."""
    print(f"\n{'=' * 60}")
    print("❌ Common Mistakes with Extras")
    print("='*60")

    mistakes = [
        {
            "package": "requests",
            "extras": ["dev", "test"],  # These don't exist for requests
            "error": "Using generic extra names instead of package-specific ones",
        },
        {
            "package": "setuptools",
            "extras": ["testing"],  # Should be "test" not "testing"
            "error": "Using similar but incorrect extra names",
        },
    ]

    for mistake in mistakes:
        package_name = mistake["package"]
        extras = mistake["extras"]
        error_desc = mistake["error"]

        print(f"\n🚫 Mistake: {error_desc}")
        print(f"   Package: {package_name}")
        print(f"   Incorrect extras: {extras}")

        try:
            result = await resolve_package_dependencies(
                package_name=package_name,
                python_version="3.10",
                include_extras=extras,
                max_depth=1,
            )

            total_extras = result["summary"]["total_extra_dependencies"]
            print(f"   Result: {total_extras} extra dependencies resolved")
            if total_extras == 0:
                print("   ⚠️  No extras resolved - these extras likely don't exist")

        except Exception as e:
            print(f"   ❌ Error: {e}")


async def main():
    """Main demonstration function."""
    print("🚀 PyPI Query MCP Server - Extras Usage Demo")
    print("=" * 60)
    print()
    print("This demo shows how to properly use the include_extras parameter")
    print("to resolve optional dependencies for Python packages.")

    await demo_extras_resolution()
    await demo_incorrect_usage()

    print(f"\n{'=' * 60}")
    print("✨ Demo completed!")
    print()
    print("💡 Key takeaways:")
    print("   1. Always check what extras are available for a package first")
    print("   2. Use the exact extra names defined by the package")
    print("   3. Check package documentation or PyPI page for available extras")
    print(
        "   4. Not all packages have extras, and some extras may have no dependencies"
    )
    print()
    print("📚 To find available extras:")
    print("   - Check the package's PyPI page")
    print("   - Look for 'provides_extra' in package metadata")
    print("   - Check package documentation")
    print("   - Look for requirements with 'extra ==' in requires_dist")


if __name__ == "__main__":
    asyncio.run(main())

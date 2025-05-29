#!/usr/bin/env python3
"""
PyPI Query MCP Server - Prompt Templates Demo

This script demonstrates how to use the MCP prompt templates for PyPI package analysis,
dependency management, and migration planning.

The prompt templates provide structured guidance for common PyPI package scenarios:
- Package quality analysis
- Package comparison and selection
- Dependency conflict resolution
- Security auditing
- Migration planning

Usage:
    python examples/prompt_templates_demo.py
"""

import asyncio

from fastmcp import Client


async def demo_package_analysis_prompts():
    """Demonstrate package analysis prompt templates."""
    print("🔍 Package Analysis Prompt Templates Demo")
    print("=" * 50)

    client = Client("pypi_query_mcp.server:mcp")

    async with client:
        # Demo 1: Package Quality Analysis
        print("\n1. Package Quality Analysis")
        print("-" * 30)

        result = await client.get_prompt(
            "analyze_package_quality",
            {"package_name": "requests", "version": "2.31.0"}
        )

        print("Prompt generated for analyzing 'requests' package quality:")
        print(result.messages[0].content.text[:200] + "...")

        # Demo 2: Package Comparison
        print("\n2. Package Comparison")
        print("-" * 30)

        result = await client.get_prompt(
            "compare_packages",
            {
                "packages": ["requests", "httpx", "aiohttp"],
                "use_case": "Building a high-performance web API client",
                "criteria": ["performance", "async support", "ease of use"]
            }
        )

        print("Prompt generated for comparing HTTP client libraries:")
        print(result.messages[0].content.text[:200] + "...")

        # Demo 3: Package Alternatives
        print("\n3. Package Alternatives")
        print("-" * 30)

        result = await client.get_prompt(
            "suggest_alternatives",
            {
                "package_name": "flask",
                "reason": "performance",
                "requirements": "Need async support and better performance for high-traffic API"
            }
        )

        print("Prompt generated for finding Flask alternatives:")
        print(result.messages[0].content.text[:200] + "...")


async def demo_dependency_management_prompts():
    """Demonstrate dependency management prompt templates."""
    print("\n\n🔧 Dependency Management Prompt Templates Demo")
    print("=" * 50)

    client = Client("pypi_query_mcp.server:mcp")

    async with client:
        # Demo 1: Dependency Conflicts
        print("\n1. Dependency Conflict Resolution")
        print("-" * 35)

        result = await client.get_prompt(
            "resolve_dependency_conflicts",
            {
                "conflicts": [
                    "django 4.2.0 requires sqlparse>=0.3.1, but you have sqlparse 0.2.4",
                    "Package A requires numpy>=1.20.0, but Package B requires numpy<1.19.0"
                ],
                "python_version": "3.10",
                "project_context": "Django web application with data analysis features"
            }
        )

        print("Prompt generated for resolving dependency conflicts:")
        print(result.messages[0].content.text[:200] + "...")

        # Demo 2: Version Upgrade Planning
        print("\n2. Version Upgrade Planning")
        print("-" * 30)

        result = await client.get_prompt(
            "plan_version_upgrade",
            {
                "package_name": "django",
                "current_version": "3.2.0",
                "target_version": "4.2.0",
                "project_size": "large"
            }
        )

        print("Prompt generated for Django upgrade planning:")
        print(result.messages[0].content.text[:200] + "...")

        # Demo 3: Security Audit
        print("\n3. Security Risk Audit")
        print("-" * 25)

        result = await client.get_prompt(
            "audit_security_risks",
            {
                "packages": ["django", "requests", "pillow", "cryptography"],
                "environment": "production",
                "compliance_requirements": "SOC2, GDPR compliance required"
            }
        )

        print("Prompt generated for security audit:")
        print(result.messages[0].content.text[:200] + "...")


async def demo_migration_prompts():
    """Demonstrate migration planning prompt templates."""
    print("\n\n🚀 Migration Planning Prompt Templates Demo")
    print("=" * 50)

    client = Client("pypi_query_mcp.server:mcp")

    async with client:
        # Demo 1: Package Migration Planning
        print("\n1. Package Migration Planning")
        print("-" * 30)

        result = await client.get_prompt(
            "plan_package_migration",
            {
                "from_package": "flask",
                "to_package": "fastapi",
                "codebase_size": "medium",
                "timeline": "2 months",
                "team_size": 4
            }
        )

        print("Prompt generated for Flask to FastAPI migration:")
        print(result.messages[0].content.text[:200] + "...")

        # Demo 2: Migration Checklist
        print("\n2. Migration Checklist")
        print("-" * 25)

        result = await client.get_prompt(
            "generate_migration_checklist",
            {
                "migration_type": "package_replacement",
                "packages_involved": ["flask", "fastapi", "pydantic"],
                "environment": "production"
            }
        )

        print("Prompt generated for migration checklist:")
        print(result.messages[0].content.text[:200] + "...")


async def demo_prompt_list():
    """List all available prompt templates."""
    print("\n\n📋 Available Prompt Templates")
    print("=" * 50)

    client = Client("pypi_query_mcp.server:mcp")

    async with client:
        prompts = await client.list_prompts()

        print(f"\nFound {len(prompts)} prompt templates:")

        for prompt in prompts:
            print(f"\n• {prompt.name}")
            print(f"  Description: {prompt.description}")
            if prompt.arguments:
                print("  Arguments:")
                for arg in prompt.arguments:
                    required = " (required)" if arg.required else " (optional)"
                    print(f"    - {arg.name}{required}: {arg.description or 'No description'}")


async def main():
    """Run all prompt template demonstrations."""
    print("PyPI Query MCP Server - Prompt Templates Demo")
    print("=" * 60)

    try:
        # List available prompts
        await demo_prompt_list()

        # Demo package analysis prompts
        await demo_package_analysis_prompts()

        # Demo dependency management prompts
        await demo_dependency_management_prompts()

        # Demo migration prompts
        await demo_migration_prompts()

        print("\n\n✅ Demo completed successfully!")
        print("\nThese prompt templates can be used in any MCP-compatible client")
        print("(Claude Desktop, Cursor, Cline, etc.) to get structured guidance")
        print("for PyPI package analysis and management tasks.")

    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        print("\nMake sure the PyPI Query MCP Server is properly installed and configured.")


if __name__ == "__main__":
    asyncio.run(main())

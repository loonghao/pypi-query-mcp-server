#!/usr/bin/env python3
"""Simple test for prompt templates functionality."""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypi_query_mcp.prompts.package_analysis import analyze_package_quality
from pypi_query_mcp.prompts.dependency_management import resolve_dependency_conflicts
from pypi_query_mcp.prompts.migration_guidance import plan_package_migration


async def test_prompt_templates():
    """Test that prompt templates work correctly."""
    print("Testing PyPI Query MCP Server Prompt Templates")
    print("=" * 50)
    
    try:
        # Test package analysis prompt
        print("\n1. Testing Package Analysis Prompt")
        result = await analyze_package_quality("requests", "2.31.0")
        assert len(result) == 1
        assert "requests" in result[0].text
        assert "version 2.31.0" in result[0].text
        print("✅ Package analysis prompt works correctly")
        
        # Test dependency conflict resolution prompt
        print("\n2. Testing Dependency Conflict Resolution Prompt")
        conflicts = ["django 4.2.0 requires sqlparse>=0.3.1, but you have sqlparse 0.2.4"]
        result = await resolve_dependency_conflicts(conflicts, "3.10", "Django web app")
        assert len(result) == 1
        assert "django 4.2.0" in result[0].text
        assert "Python version: 3.10" in result[0].text
        print("✅ Dependency conflict resolution prompt works correctly")
        
        # Test migration planning prompt
        print("\n3. Testing Migration Planning Prompt")
        result = await plan_package_migration("flask", "fastapi", "medium", "2 months", 4)
        assert len(result) == 1
        assert "flask" in result[0].text
        assert "fastapi" in result[0].text
        assert "medium codebase" in result[0].text
        print("✅ Migration planning prompt works correctly")
        
        print("\n" + "=" * 50)
        print("🎉 All prompt template tests passed!")
        print("\nThe MCP prompt templates are working correctly and can be used")
        print("in any MCP-compatible client (Claude Desktop, Cursor, etc.)")
        
        # Show a sample prompt output
        print("\n📋 Sample Prompt Output:")
        print("-" * 30)
        sample_result = await analyze_package_quality("numpy")
        print(sample_result[0].text[:300] + "...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_prompt_templates())
    sys.exit(0 if success else 1)

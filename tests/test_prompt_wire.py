"""Regression tests for the five prompts that failed on the MCP wire.

The MCP ``prompts/get`` spec only allows string argument values. These tests
drive the real FastMCP client against the registered server instance so the
wire-level contract (argument coercion and prompt rendering) is exercised,
not just the prompt generator functions in isolation.
"""

import pytest
from fastmcp import Client

from pypi_query_mcp.server import mcp


async def get_prompt_text(name: str, arguments: dict) -> str:
    """Fetch a prompt through an MCP client and return its text content."""
    async with Client(mcp) as client:
        result = await client.get_prompt(name, arguments)
    assert result.messages, "prompt returned no messages"
    return result.messages[0].content.text


class TestAffectedPromptWireRendering:
    """The five prompts from issue #77 must render with string arguments."""

    @pytest.mark.asyncio
    async def test_analyze_package_quality_renders(self):
        text = await get_prompt_text(
            "analyze_package_quality_prompt",
            {"package_name": "requests", "version": "2.31.0"},
        )
        assert "requests" in text
        assert "version 2.31.0" in text
        assert "{{" not in text  # all placeholders resolved

    @pytest.mark.asyncio
    async def test_compare_packages_splits_comma_separated_args(self):
        text = await get_prompt_text(
            "compare_packages_prompt",
            {
                "packages": "django, flask",
                "use_case": "building an API",
                "criteria": "performance, security",
            },
        )
        assert "'django'" in text
        assert "'flask'" in text
        assert "building an API" in text
        assert "performance, security" in text
        assert "{{" not in text

    @pytest.mark.asyncio
    async def test_audit_security_risks_splits_comma_separated_args(self):
        text = await get_prompt_text(
            "audit_security_risks_prompt",
            {"packages": "django, requests", "environment": "production"},
        )
        assert "'django'" in text
        assert "'requests'" in text
        assert "Environment: production" in text
        assert "{{" not in text

    @pytest.mark.asyncio
    async def test_resolve_dependency_conflicts_splits_comma_separated_args(self):
        text = await get_prompt_text(
            "resolve_dependency_conflicts_prompt",
            {"conflicts": "A requires X, B requires Y", "python_version": "3.10"},
        )
        assert "- A requires X" in text
        assert "- B requires Y" in text
        assert "Python version: 3.10" in text
        assert "{{" not in text

    @pytest.mark.asyncio
    async def test_generate_migration_checklist_splits_comma_separated_args(self):
        text = await get_prompt_text(
            "generate_migration_checklist_prompt",
            {
                "migration_type": "package_replacement",
                "packages_involved": "flask, fastapi",
            },
        )
        assert "'flask'" in text
        assert "'fastapi'" in text
        assert "replacing one package with another" in text
        assert "{{" not in text


class TestAffectedPromptSchemas:
    """Registered schemas must advertise string (not array) arguments."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("prompt_name", "arg_name"),
        [
            ("compare_packages_prompt", "packages"),
            ("audit_security_risks_prompt", "packages"),
            ("resolve_dependency_conflicts_prompt", "conflicts"),
            ("generate_migration_checklist_prompt", "packages_involved"),
        ],
    )
    async def test_list_args_are_declared_as_strings(self, prompt_name, arg_name):
        async with Client(mcp) as client:
            prompts = {p.name: p for p in await client.list_prompts()}
        arguments = {a.name: a for a in prompts[prompt_name].arguments}
        schema = arguments[arg_name].description
        assert '"type":"string"' in schema
        assert "Comma-separated" in schema

# PyPI Query MCP Server - Prompt Templates

This document describes the MCP prompt templates available in the PyPI Query MCP Server. These templates provide structured guidance for common PyPI package analysis, dependency management, and migration scenarios.

## 🎯 Overview

Prompt templates are reusable message templates that help you get structured guidance from LLMs for specific PyPI package management tasks. They provide comprehensive frameworks for analysis and decision-making.

## 📋 Available Prompt Templates

### Package Analysis Templates

#### 1. `analyze_package_quality`
Generate a comprehensive quality analysis prompt for a PyPI package.

**Parameters:**
- `package_name` (required): Name of the PyPI package to analyze
- `version` (optional): Specific version to analyze

**Use Case:** When you need to evaluate a package's quality, maintenance status, security, and suitability for your project.

**Example:**
```json
{
  "package_name": "requests",
  "version": "2.31.0"
}
```

#### 2. `compare_packages`
Generate a detailed comparison prompt for multiple PyPI packages.

**Parameters:**
- `packages` (required): List of package names to compare (2-5 packages)
- `use_case` (required): Specific use case or project context
- `criteria` (optional): Specific criteria to focus on

**Use Case:** When choosing between multiple packages that serve similar purposes.

**Example:**
```json
{
  "packages": ["requests", "httpx", "aiohttp"],
  "use_case": "Building a high-performance web API client",
  "criteria": ["performance", "async support", "ease of use"]
}
```

#### 3. `suggest_alternatives`
Generate a prompt for finding package alternatives.

**Parameters:**
- `package_name` (required): Package to find alternatives for
- `reason` (required): Reason for seeking alternatives (deprecated, security, performance, licensing, maintenance, features)
- `requirements` (optional): Specific requirements for alternatives

**Use Case:** When you need to replace a package due to specific concerns.

**Example:**
```json
{
  "package_name": "flask",
  "reason": "performance",
  "requirements": "Need async support and better performance"
}
```

### Dependency Management Templates

#### 4. `resolve_dependency_conflicts`
Generate a prompt for resolving dependency conflicts.

**Parameters:**
- `conflicts` (required): List of conflicting dependencies or error messages
- `python_version` (optional): Target Python version
- `project_context` (optional): Brief project description

**Use Case:** When facing dependency version conflicts that need resolution.

**Example:**
```json
{
  "conflicts": [
    "django 4.2.0 requires sqlparse>=0.3.1, but you have sqlparse 0.2.4"
  ],
  "python_version": "3.10",
  "project_context": "Django web application"
}
```

#### 5. `plan_version_upgrade`
Generate a prompt for planning package version upgrades.

**Parameters:**
- `package_name` (required): Package to upgrade
- `current_version` (required): Current version being used
- `target_version` (optional): Target version or 'latest'
- `project_size` (optional): Project size context (small/medium/large/enterprise)

**Use Case:** When planning major version upgrades that might have breaking changes.

**Example:**
```json
{
  "package_name": "django",
  "current_version": "3.2.0",
  "target_version": "4.2.0",
  "project_size": "large"
}
```

#### 6. `audit_security_risks`
Generate a prompt for security risk auditing of packages.

**Parameters:**
- `packages` (required): List of packages to audit
- `environment` (optional): Environment context (development/staging/production)
- `compliance_requirements` (optional): Specific compliance requirements

**Use Case:** When conducting security audits or compliance assessments.

**Example:**
```json
{
  "packages": ["django", "requests", "pillow"],
  "environment": "production",
  "compliance_requirements": "SOC2, GDPR compliance"
}
```

### Migration Planning Templates

#### 7. `plan_package_migration`
Generate a comprehensive package migration plan prompt.

**Parameters:**
- `from_package` (required): Package to migrate from
- `to_package` (required): Package to migrate to
- `codebase_size` (optional): Size of codebase (small/medium/large/enterprise)
- `timeline` (optional): Desired timeline
- `team_size` (optional): Number of developers involved

**Use Case:** When planning to migrate from one package to another.

**Example:**
```json
{
  "from_package": "flask",
  "to_package": "fastapi",
  "codebase_size": "medium",
  "timeline": "2 months",
  "team_size": 4
}
```

#### 8. `generate_migration_checklist`
Generate a detailed migration checklist prompt.

**Parameters:**
- `migration_type` (required): Type of migration (package_replacement, version_upgrade, framework_migration, dependency_cleanup)
- `packages_involved` (required): List of packages involved
- `environment` (optional): Target environment (development/staging/production/all)

**Use Case:** When you need a comprehensive checklist for migration tasks.

**Example:**
```json
{
  "migration_type": "package_replacement",
  "packages_involved": ["flask", "fastapi"],
  "environment": "production"
}
```

## 🚀 Usage Examples

### In Claude Desktop

Add the PyPI Query MCP Server to your Claude Desktop configuration, then use prompts like:

```
Use the "analyze_package_quality" prompt template to analyze the requests package version 2.31.0
```

### In Cursor

Configure the MCP server in Cursor, then access prompts through the command palette or by typing:

```
@pypi-query analyze_package_quality requests 2.31.0
```

### Programmatic Usage

```python
from fastmcp import Client

async def use_prompt_template():
    client = Client("pypi_query_mcp.server:mcp")
    
    async with client:
        # Get a prompt template
        result = await client.get_prompt(
            "analyze_package_quality",
            {"package_name": "requests", "version": "2.31.0"}
        )
        
        # The result contains structured messages for the LLM
        print(result.messages[0].content.text)
```

## 🎨 Customization

The prompt templates are designed to be comprehensive but can be customized by:

1. **Modifying parameters**: Adjust the input parameters to focus on specific aspects
2. **Combining templates**: Use multiple templates for complex scenarios
3. **Extending context**: Add project-specific context through optional parameters

## 🔧 Development

To add new prompt templates:

1. Create the template function in the appropriate module under `pypi_query_mcp/prompts/`
2. Register it in `pypi_query_mcp/server.py` using the `@mcp.prompt()` decorator
3. Add it to the `__all__` list in `pypi_query_mcp/prompts/__init__.py`
4. Update this documentation

## 📚 Best Practices

1. **Be Specific**: Provide detailed context in the parameters for better results
2. **Use Appropriate Templates**: Choose the template that best matches your scenario
3. **Combine with Tools**: Use prompt templates alongside the MCP tools for comprehensive analysis
4. **Iterate**: Refine your parameters based on the LLM responses to get better guidance

## 🤝 Contributing

We welcome contributions to improve existing templates or add new ones. Please:

1. Follow the existing template structure and patterns
2. Include comprehensive parameter validation
3. Add examples and documentation
4. Test with various scenarios

## 📄 License

These prompt templates are part of the PyPI Query MCP Server and are licensed under the same terms.

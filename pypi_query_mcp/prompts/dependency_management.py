"""Dependency management prompt templates for PyPI MCP server."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field


class Message:
    """Simple message class for prompt templates."""

    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


async def resolve_dependency_conflicts(
    conflicts: Annotated[
        list[str],
        Field(
            description="List of conflicting dependencies or error messages",
            min_length=1,
        ),
    ],
    python_version: Annotated[
        str | None, Field(description="Target Python version (e.g., '3.10', '3.11')")
    ] = None,
    project_context: Annotated[
        str | None,
        Field(description="Brief description of the project and its requirements"),
    ] = None,
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a prompt for resolving dependency conflicts.

    This prompt template helps analyze and resolve Python package dependency conflicts
    with specific strategies and recommendations.
    """
    conflicts_text = "\n".join(f"- {conflict}" for conflict in conflicts)
    python_text = f"\nPython version: {python_version}" if python_version else ""
    context_text = f"\nProject context: {project_context}" if project_context else ""

    return [
        Message(
            f"""I'm experiencing dependency conflicts in my Python project. Please help me resolve them.

## 🚨 Conflict Details
{conflicts_text}{python_text}{context_text}

## 🔧 Resolution Strategy

Please provide a comprehensive resolution plan:

### Conflict Analysis
- Identify the root cause of each conflict
- Explain why these dependencies are incompatible
- Assess the severity and impact of each conflict

### Resolution Options
1. **Version Pinning Strategy**
   - Specific version combinations that work together
   - Version ranges that maintain compatibility
   - Lock file recommendations

2. **Alternative Packages**
   - Drop-in replacements for conflicting packages
   - Packages with better compatibility profiles
   - Lighter alternatives with fewer dependencies

3. **Environment Isolation**
   - Virtual environment strategies
   - Docker containerization approaches
   - Dependency grouping techniques

### Implementation Steps
- Step-by-step resolution commands
- Testing procedures to verify fixes
- Preventive measures for future conflicts

## 🛡️ Best Practices
- Dependency management tools recommendations
- Version constraint strategies
- Monitoring and maintenance approaches

Please provide specific commands and configuration examples where applicable."""
        )
    ]


async def plan_version_upgrade(
    package_name: Annotated[str, Field(description="Name of the package to upgrade")],
    current_version: Annotated[str, Field(description="Current version being used")],
    target_version: Annotated[
        str | None,
        Field(description="Target version (if known), or 'latest' for newest"),
    ] = None,
    project_size: Annotated[
        str | None,
        Field(description="Project size context (small/medium/large/enterprise)"),
    ] = None,
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a prompt for planning package version upgrades.

    This prompt template helps create a comprehensive upgrade plan for Python packages,
    including risk assessment and migration strategies.
    """
    target_text = target_version or "latest available version"
    size_text = f" ({project_size} project)" if project_size else ""

    return [
        Message(
            f"""I need to upgrade '{package_name}' from version {current_version} to {target_text}{size_text}.

Please create a comprehensive upgrade plan:

## 📋 Pre-Upgrade Assessment

### Version Analysis
- Changes between {current_version} and {target_text}
- Breaking changes and deprecations
- New features and improvements
- Security fixes included

### Risk Assessment
- Compatibility with existing dependencies
- Potential breaking changes impact
- Testing requirements and scope
- Rollback complexity

## 🚀 Upgrade Strategy

### Preparation Phase
- Backup and version control recommendations
- Dependency compatibility checks
- Test environment setup
- Documentation review

### Migration Steps
1. **Incremental Upgrade Path**
   - Intermediate versions to consider
   - Step-by-step upgrade sequence
   - Validation points between steps

2. **Code Changes Required**
   - API changes to address
   - Deprecated feature replacements
   - Configuration updates needed

3. **Testing Strategy**
   - Unit test updates required
   - Integration test considerations
   - Performance regression testing

### Post-Upgrade Validation
- Functionality verification checklist
- Performance monitoring points
- Error monitoring and alerting

## 🛡️ Risk Mitigation
- Rollback procedures
- Gradual deployment strategies
- Monitoring and alerting setup

Please provide specific commands, code examples, and timelines where applicable."""
        )
    ]


async def audit_security_risks(
    packages: Annotated[
        list[str],
        Field(description="List of packages to audit for security risks", min_length=1),
    ],
    environment: Annotated[
        str | None,
        Field(description="Environment context (development/staging/production)"),
    ] = None,
    compliance_requirements: Annotated[
        str | None,
        Field(
            description="Specific compliance requirements (e.g., SOC2, HIPAA, PCI-DSS)"
        ),
    ] = None,
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a prompt for security risk auditing of packages.

    This prompt template helps conduct comprehensive security audits of Python packages
    and their dependencies.
    """
    packages_text = ", ".join(f"'{pkg}'" for pkg in packages)
    env_text = f"\nEnvironment: {environment}" if environment else ""
    compliance_text = (
        f"\nCompliance requirements: {compliance_requirements}"
        if compliance_requirements
        else ""
    )

    return [
        Message(
            f"""Please conduct a comprehensive security audit of these Python packages: {packages_text}{env_text}{compliance_text}

## 🔍 Security Assessment Framework

### Vulnerability Analysis
- Known CVEs and security advisories
- Severity levels and CVSS scores
- Affected versions and fix availability
- Exploit likelihood and impact assessment

### Dependency Security
- Transitive dependency vulnerabilities
- Dependency chain analysis
- Supply chain risk assessment
- License compliance issues

### Package Integrity
- Package authenticity verification
- Maintainer reputation and history
- Code review and audit history
- Distribution security (PyPI, mirrors)

## 🛡️ Risk Evaluation

### Critical Findings
- High-severity vulnerabilities requiring immediate action
- Packages with known malicious activity
- Unmaintained packages with security issues

### Medium Risk Issues
- Outdated packages with available security updates
- Packages with poor security practices
- Dependencies with concerning patterns

### Recommendations
- Immediate remediation steps
- Alternative secure packages
- Security monitoring setup
- Update and patching strategies

## 📋 Compliance Assessment
- Regulatory requirement alignment
- Security policy compliance
- Audit trail and documentation needs
- Reporting and monitoring requirements

## 🚀 Action Plan
- Prioritized remediation roadmap
- Timeline and resource requirements
- Monitoring and maintenance procedures
- Incident response preparations

Please provide specific vulnerability details, remediation commands, and compliance guidance."""
        )
    ]

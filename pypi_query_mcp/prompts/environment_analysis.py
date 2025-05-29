"""Environment analysis prompt templates for PyPI MCP server."""

from typing import Annotated

from fastmcp import Context
from pydantic import Field


class Message:
    """Simple message class for prompt templates."""

    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


async def analyze_environment_dependencies(
    environment_type: Annotated[
        str, Field(description="Type of environment (local, virtual, docker, conda)")
    ] = "local",
    python_version: Annotated[
        str | None, Field(description="Python version in the environment")
    ] = None,
    project_path: Annotated[
        str | None, Field(description="Path to the project directory")
    ] = None,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for analyzing environment dependencies.

    This prompt template helps analyze the current Python environment dependencies,
    check for outdated packages, and provide upgrade recommendations.

    Returns a template string with {{environment_type}}, {{python_version}}, and {{project_path}} variables.
    """
    template = """Please analyze the Python environment dependencies {{environment_info}}.

## 🔍 Environment Analysis Request

I need to analyze my current Python environment to understand:

### Current Environment Status
- List all installed packages and their versions (use `{{command_prefix}}pip list`)
- Identify the Python version and environment type
- Check for any conflicting or problematic installations

### Package Version Analysis
- Compare installed versions with latest available on PyPI
- Identify outdated packages that have newer versions
- Highlight packages with security updates available
- Check for packages with major version updates

### Dependency Health Check
- Analyze dependency relationships and conflicts
- Identify unused or redundant packages
- Check for packages with known vulnerabilities
- Assess overall environment health

## 📊 Detailed Analysis Framework

### For Each Package, Provide:
1. **Current vs Latest Version**
   - Installed version
   - Latest stable version on PyPI
   - Version gap analysis (patch/minor/major updates)

2. **Update Priority Assessment**
   - Security updates (HIGH priority)
   - Bug fixes and stability improvements (MEDIUM priority)
   - New features and enhancements (LOW priority)

3. **Compatibility Impact**
   - Breaking changes in newer versions
   - Dependency chain effects
   - Potential conflicts with other packages

### Environment Optimization Recommendations
- Packages safe to update immediately
- Packages requiring careful testing before update
- Packages to avoid updating (due to breaking changes)
- Cleanup recommendations for unused packages

## 🚀 Action Plan

Provide a prioritized action plan with:
- Immediate updates (security and critical fixes)
- Planned updates (with testing requirements)
- Long-term upgrade strategy
- Environment maintenance best practices

Please include specific commands for package management and update procedures."""

    return template


async def check_outdated_packages(
    package_filter: Annotated[
        str | None, Field(description="Filter packages by name pattern (optional)")
    ] = None,
    severity_level: Annotated[
        str, Field(description="Focus level: all, security, major, minor")
    ] = "all",
    include_dev_dependencies: Annotated[
        bool, Field(description="Include development dependencies in analysis")
    ] = True,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for checking outdated packages.

    This prompt template helps identify and prioritize outdated packages
    in the current environment with specific focus criteria.

    Returns a template string with {{package_filter}}, {{severity_level}}, and {{dev_deps}} variables.
    """
    template = """Please check for outdated packages in my Python environment {{filter_info}}.

## 🔍 Outdated Package Analysis

Focus on {{severity_level}} updates{{dev_deps_text}}.

### Analysis Scope
- Check all installed packages against PyPI latest versions
- Identify packages with available updates
- Categorize updates by severity and importance
- Assess update risks and benefits

## 📋 Update Categories

### 🚨 Security Updates (Critical)
- Packages with known security vulnerabilities
- CVE fixes and security patches
- Immediate action required packages

### 🔧 Bug Fixes & Stability (Important)
- Critical bug fixes
- Stability improvements
- Performance enhancements

### ✨ Feature Updates (Optional)
- New features and capabilities
- API improvements
- Non-breaking enhancements

### ⚠️ Major Version Updates (Careful)
- Breaking changes
- API modifications
- Requires thorough testing

## 📊 For Each Outdated Package, Provide:

1. **Version Information**
   - Current version installed
   - Latest available version
   - Release date of latest version
   - Version type (patch/minor/major)

2. **Update Assessment**
   - Change log highlights
   - Breaking changes (if any)
   - Security implications
   - Dependency impact

3. **Recommendation**
   - Update priority (High/Medium/Low)
   - Testing requirements
   - Rollback considerations
   - Best update timing

## 🎯 Prioritized Update Plan

Create a step-by-step update plan:
1. **Immediate Updates** (security and critical fixes)
2. **Planned Updates** (important improvements)
3. **Future Considerations** (major version upgrades)
4. **Monitoring Setup** (track future updates)

Include specific pip/uv commands for each update category."""

    return template


async def generate_update_plan(
    update_strategy: Annotated[
        str, Field(description="Update strategy: conservative, balanced, aggressive")
    ] = "balanced",
    environment_constraints: Annotated[
        str | None, Field(description="Environment constraints or requirements")
    ] = None,
    testing_requirements: Annotated[
        str | None, Field(description="Testing requirements before updates")
    ] = None,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for creating package update plans.

    This prompt template helps create comprehensive update plans for Python environments
    with specific strategies and constraints.

    Returns a template string with {{strategy}}, {{constraints}}, and {{testing}} variables.
    """
    template = """Please create a comprehensive package update plan using a {{strategy}} strategy{{constraints_text}}{{testing_text}}.

## 🎯 Update Strategy: {{strategy}}

### Strategy Guidelines
- **Conservative**: Only security and critical bug fixes
- **Balanced**: Security fixes + stable improvements + selected features
- **Aggressive**: Latest versions with careful testing

## 📋 Update Plan Framework

### Phase 1: Pre-Update Assessment
1. **Environment Backup**
   - Create requirements.txt snapshot
   - Document current working state
   - Set up rollback procedures

2. **Dependency Analysis**
   - Map dependency relationships
   - Identify potential conflicts
   - Plan update order

3. **Risk Assessment**
   - Categorize packages by update risk
   - Identify critical dependencies
   - Plan testing scope

### Phase 2: Staged Update Execution

#### Stage 1: Critical Security Updates
- Packages with known vulnerabilities
- Zero-day fixes and security patches
- Immediate deployment candidates

#### Stage 2: Stability Improvements
- Bug fixes and performance improvements
- Compatibility updates
- Low-risk enhancements

#### Stage 3: Feature Updates
- New functionality additions
- API improvements
- Non-breaking enhancements

#### Stage 4: Major Version Updates
- Breaking changes requiring code updates
- Comprehensive testing required
- Gradual rollout recommended

### Phase 3: Validation & Monitoring

#### Testing Protocol
- Unit test execution
- Integration testing
- Performance regression testing
- User acceptance testing

#### Deployment Strategy
- Development environment first
- Staging environment validation
- Production deployment with monitoring
- Rollback procedures ready

## 🔧 Implementation Commands

Provide specific commands for:
1. **Environment preparation**
2. **Package updates by category**
3. **Testing and validation**
4. **Rollback procedures**

## 📊 Success Metrics

Define success criteria:
- All tests passing
- No performance degradation
- Security vulnerabilities addressed
- Functionality maintained

Include monitoring setup for ongoing package management."""

    return template

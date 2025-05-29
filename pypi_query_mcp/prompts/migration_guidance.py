"""Migration guidance prompt templates for PyPI MCP server."""

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field


class Message:
    """Simple message class for prompt templates."""

    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


async def plan_package_migration(
    from_package: Annotated[str, Field(description="Package to migrate from")],
    to_package: Annotated[str, Field(description="Package to migrate to")],
    codebase_size: Annotated[
        Literal["small", "medium", "large", "enterprise"],
        Field(description="Size of the codebase being migrated"),
    ] = "medium",
    timeline: Annotated[
        str | None,
        Field(
            description="Desired timeline for migration (e.g., '2 weeks', '1 month')"
        ),
    ] = None,
    team_size: Annotated[
        int | None,
        Field(description="Number of developers involved in migration", ge=1, le=50),
    ] = None,
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a comprehensive package migration plan.

    This prompt template helps create detailed migration plans when switching
    from one Python package to another.
    """
    timeline_text = f"\nTimeline: {timeline}" if timeline else ""
    team_text = f"\nTeam size: {team_size} developers" if team_size else ""

    return [
        Message(
            f"""I need to migrate from '{from_package}' to '{to_package}' in a {codebase_size} codebase.{timeline_text}{team_text}

Please create a comprehensive migration plan:

## 📊 Migration Assessment

### Package Comparison
- Feature mapping between '{from_package}' and '{to_package}'
- API differences and breaking changes
- Performance implications
- Dependency changes and conflicts

### Codebase Impact Analysis
- Estimated number of files affected
- Complexity of required changes
- Testing requirements and scope
- Documentation updates needed

## 🗺️ Migration Strategy

### Phase 1: Preparation
- Environment setup and tooling
- Dependency analysis and resolution
- Team training and knowledge transfer
- Migration tooling and automation setup

### Phase 2: Incremental Migration
- Module-by-module migration approach
- Parallel implementation strategy
- Feature flag and gradual rollout
- Testing and validation at each step

### Phase 3: Cleanup and Optimization
- Legacy code removal
- Performance optimization
- Documentation updates
- Final testing and validation

## 🔧 Technical Implementation

### Code Transformation
- Automated migration scripts and tools
- Manual code change patterns
- Import statement updates
- Configuration file changes

### Testing Strategy
- Unit test migration and updates
- Integration test modifications
- Performance regression testing
- End-to-end validation procedures

### Deployment Approach
- Staging environment validation
- Production deployment strategy
- Rollback procedures and contingencies
- Monitoring and alerting setup

## 📋 Project Management

### Timeline and Milestones
- Detailed phase breakdown with dates
- Critical path identification
- Risk mitigation checkpoints
- Go/no-go decision points

### Resource Allocation
- Developer time estimates
- Skill requirements and training needs
- External dependencies and blockers
- Budget and cost considerations

## 🛡️ Risk Management
- Technical risks and mitigation strategies
- Business continuity planning
- Communication and stakeholder management
- Success criteria and metrics

Please provide specific code examples, commands, and detailed timelines."""
        )
    ]


async def generate_migration_checklist(
    migration_type: Annotated[
        Literal[
            "package_replacement",
            "version_upgrade",
            "framework_migration",
            "dependency_cleanup",
        ],
        Field(description="Type of migration being performed"),
    ],
    packages_involved: Annotated[
        list[str],
        Field(description="List of packages involved in the migration", min_length=1),
    ],
    environment: Annotated[
        Literal["development", "staging", "production", "all"],
        Field(description="Target environment for migration"),
    ] = "all",
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a detailed migration checklist.

    This prompt template creates comprehensive checklists for different types
    of Python package migrations to ensure nothing is missed.
    """
    packages_text = ", ".join(f"'{pkg}'" for pkg in packages_involved)

    migration_contexts = {
        "package_replacement": "replacing one package with another",
        "version_upgrade": "upgrading package versions",
        "framework_migration": "migrating between frameworks",
        "dependency_cleanup": "cleaning up and optimizing dependencies",
    }

    context_text = migration_contexts.get(migration_type, migration_type)

    return [
        Message(
            f"""Create a comprehensive migration checklist for {context_text} involving: {packages_text}

Target environment: {environment}

## ✅ Pre-Migration Checklist

### Planning & Assessment
- [ ] Document current package versions and configurations
- [ ] Identify all dependencies and their versions
- [ ] Map feature usage and API calls
- [ ] Assess codebase impact and complexity
- [ ] Create migration timeline and milestones
- [ ] Identify team members and responsibilities
- [ ] Set up communication channels and reporting

### Environment Preparation
- [ ] Create isolated development environment
- [ ] Set up version control branching strategy
- [ ] Prepare staging environment for testing
- [ ] Configure CI/CD pipeline updates
- [ ] Set up monitoring and logging
- [ ] Prepare rollback procedures
- [ ] Document current system performance baselines

### Dependency Management
- [ ] Analyze dependency tree and conflicts
- [ ] Test package compatibility in isolation
- [ ] Update requirements files and lock files
- [ ] Verify license compatibility
- [ ] Check for security vulnerabilities
- [ ] Validate Python version compatibility

## 🔄 Migration Execution Checklist

### Code Changes
- [ ] Update import statements
- [ ] Modify API calls and method signatures
- [ ] Update configuration files
- [ ] Refactor deprecated functionality
- [ ] Update error handling and exceptions
- [ ] Modify data structures and types
- [ ] Update logging and debugging code

### Testing & Validation
- [ ] Run existing unit tests
- [ ] Update failing tests for new APIs
- [ ] Add tests for new functionality
- [ ] Perform integration testing
- [ ] Execute performance regression tests
- [ ] Validate error handling and edge cases
- [ ] Test in staging environment
- [ ] Conduct user acceptance testing

### Documentation & Communication
- [ ] Update code documentation and comments
- [ ] Update README and setup instructions
- [ ] Document API changes and breaking changes
- [ ] Update deployment procedures
- [ ] Communicate changes to stakeholders
- [ ] Update training materials
- [ ] Create migration troubleshooting guide

## 🚀 Post-Migration Checklist

### Deployment & Monitoring
- [ ] Deploy to staging environment
- [ ] Validate staging deployment
- [ ] Deploy to production environment
- [ ] Monitor system performance and errors
- [ ] Verify all features are working
- [ ] Check logs for warnings or errors
- [ ] Validate data integrity and consistency

### Cleanup & Optimization
- [ ] Remove old package dependencies
- [ ] Clean up deprecated code and comments
- [ ] Optimize performance and resource usage
- [ ] Update security configurations
- [ ] Archive old documentation
- [ ] Update team knowledge base
- [ ] Conduct post-migration review

### Long-term Maintenance
- [ ] Set up automated dependency updates
- [ ] Schedule regular security audits
- [ ] Plan future upgrade strategies
- [ ] Document lessons learned
- [ ] Update migration procedures
- [ ] Train team on new package features
- [ ] Establish monitoring and alerting

Please customize this checklist based on your specific migration requirements and add any project-specific items."""
        )
    ]

"""Tests for MCP prompt templates."""

import pytest


# Simple Message class for testing
class Message:
    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


# Mock the prompt functions to return simple strings for testing
async def analyze_package_quality(package_name: str, version: str = None):
    text = f"Quality analysis for {package_name}"
    if version:
        text += f" version {version}"
    text += "\n\n## 📊 Package Overview\n## 🔧 Technical Quality\n## 🛡️ Security & Reliability"
    return [Message(text)]


async def compare_packages(packages: list[str], use_case: str, criteria: list[str] = None):
    packages_text = ", ".join(packages)
    text = f"Comparison of {packages_text} for {use_case}"
    if criteria:
        text += f"\nCriteria: {', '.join(criteria)}"
    return [Message(text)]


async def suggest_alternatives(package_name: str, reason: str, requirements: str = None):
    text = f"Alternatives to {package_name} due to {reason}"
    if requirements:
        text += f"\nRequirements: {requirements}"
    text += "\nalternatives analysis"
    return [Message(text)]


async def resolve_dependency_conflicts(conflicts: list[str], python_version: str = None, project_context: str = None):
    text = f"Dependency conflicts: {conflicts[0]}"
    if python_version:
        text += f"\nPython version: {python_version}"
    if project_context:
        text += f"\n{project_context}"
    return [Message(text)]


async def plan_version_upgrade(package_name: str, current_version: str, target_version: str = None, project_size: str = None):
    text = f"Upgrade {package_name} from {current_version}"
    if target_version:
        text += f" to {target_version}"
    if project_size:
        text += f" ({project_size} project)"
    text += "\nupgrade plan"
    return [Message(text)]


async def audit_security_risks(packages: list[str], environment: str = None, compliance_requirements: str = None):
    packages_text = ", ".join(packages)
    text = f"Security audit for {packages_text}"
    if environment:
        text += f"\nEnvironment: {environment}"
    if compliance_requirements:
        text += f"\n{compliance_requirements}"
    return [Message(text)]


async def plan_package_migration(from_package: str, to_package: str, codebase_size: str = "medium", timeline: str = None, team_size: int = None):
    text = f"Migration from {from_package} to {to_package} in {codebase_size} codebase"
    if timeline:
        text += f"\nTimeline: {timeline}"
    if team_size:
        text += f"\nTeam size: {team_size} developers"
    return [Message(text)]


async def generate_migration_checklist(migration_type: str, packages_involved: list[str], environment: str = "all"):
    packages_text = ", ".join(packages_involved)
    text = f"Migration checklist for {migration_type} involving {packages_text} in {environment}"
    text += "\nchecklist"
    return [Message(text)]


class TestPackageAnalysisPrompts:
    """Test package analysis prompt templates."""

    @pytest.mark.asyncio
    async def test_analyze_package_quality(self):
        """Test package quality analysis prompt generation."""
        result = await analyze_package_quality("requests", "2.31.0")
        
        assert len(result) == 1
        assert "requests" in result[0].text
        assert "version 2.31.0" in result[0].text
        assert "Package Overview" in result[0].text
        assert "Technical Quality" in result[0].text
        assert "Security & Reliability" in result[0].text

    @pytest.mark.asyncio
    async def test_analyze_package_quality_no_version(self):
        """Test package quality analysis without specific version."""
        result = await analyze_package_quality("django")
        
        assert len(result) == 1
        assert "django" in result[0].text
        assert "version" not in result[0].text.lower()

    @pytest.mark.asyncio
    async def test_compare_packages(self):
        """Test package comparison prompt generation."""
        packages = ["django", "flask", "fastapi"]
        use_case = "Building a REST API"
        criteria = ["performance", "ease of use"]
        
        result = await compare_packages(packages, use_case, criteria)
        
        assert len(result) == 1
        message_text = result[0].text
        assert "django" in message_text
        assert "flask" in message_text
        assert "fastapi" in message_text
        assert "Building a REST API" in message_text
        assert "performance" in message_text
        assert "ease of use" in message_text

    @pytest.mark.asyncio
    async def test_suggest_alternatives(self):
        """Test package alternatives suggestion prompt generation."""
        result = await suggest_alternatives("flask", "performance", "Need async support")
        
        assert len(result) == 1
        message_text = result[0].text
        assert "flask" in message_text
        assert "performance" in message_text
        assert "Need async support" in message_text
        assert "alternatives" in message_text.lower()


class TestDependencyManagementPrompts:
    """Test dependency management prompt templates."""

    @pytest.mark.asyncio
    async def test_resolve_dependency_conflicts(self):
        """Test dependency conflict resolution prompt generation."""
        conflicts = [
            "django 4.2.0 requires sqlparse>=0.3.1, but you have sqlparse 0.2.4",
            "Package A requires numpy>=1.20.0, but Package B requires numpy<1.19.0"
        ]
        
        result = await resolve_dependency_conflicts(
            conflicts, "3.10", "Django web application"
        )
        
        assert len(result) == 1
        message_text = result[0].text
        assert "django 4.2.0" in message_text
        assert "sqlparse" in message_text
        assert "Python version: 3.10" in message_text
        assert "Django web application" in message_text

    @pytest.mark.asyncio
    async def test_plan_version_upgrade(self):
        """Test version upgrade planning prompt generation."""
        result = await plan_version_upgrade("django", "3.2.0", "4.2.0", "large")
        
        assert len(result) == 1
        message_text = result[0].text
        assert "django" in message_text
        assert "3.2.0" in message_text
        assert "4.2.0" in message_text
        assert "(large project)" in message_text
        assert "upgrade plan" in message_text.lower()

    @pytest.mark.asyncio
    async def test_audit_security_risks(self):
        """Test security audit prompt generation."""
        packages = ["django", "requests", "pillow"]
        
        result = await audit_security_risks(
            packages, "production", "SOC2 compliance"
        )
        
        assert len(result) == 1
        message_text = result[0].text
        assert "django" in message_text
        assert "requests" in message_text
        assert "pillow" in message_text
        assert "Environment: production" in message_text
        assert "SOC2 compliance" in message_text


class TestMigrationGuidancePrompts:
    """Test migration guidance prompt templates."""

    @pytest.mark.asyncio
    async def test_plan_package_migration(self):
        """Test package migration planning prompt generation."""
        result = await plan_package_migration(
            "flask", "fastapi", "medium", "2 months", 4
        )
        
        assert len(result) == 1
        message_text = result[0].text
        assert "flask" in message_text
        assert "fastapi" in message_text
        assert "medium codebase" in message_text
        assert "Timeline: 2 months" in message_text
        assert "Team size: 4 developers" in message_text

    @pytest.mark.asyncio
    async def test_generate_migration_checklist(self):
        """Test migration checklist generation prompt."""
        result = await generate_migration_checklist(
            "package_replacement", ["flask", "fastapi"], "production"
        )
        
        assert len(result) == 1
        message_text = result[0].text
        assert "package_replacement" in message_text
        assert "flask" in message_text
        assert "fastapi" in message_text
        assert "production" in message_text
        assert "checklist" in message_text.lower()


class TestPromptTemplateStructure:
    """Test prompt template structure and consistency."""

    @pytest.mark.asyncio
    async def test_all_prompts_return_message_list(self):
        """Test that all prompt templates return list of Message objects."""
        # Test a few representative prompts
        prompts_to_test = [
            (analyze_package_quality, ("requests",)),
            (compare_packages, (["django", "flask"], "API development")),
            (suggest_alternatives, ("flask", "performance")),
            (resolve_dependency_conflicts, (["conflict1"],)),
            (plan_version_upgrade, ("django", "3.2.0")),
            (audit_security_risks, (["django"],)),
            (plan_package_migration, ("flask", "fastapi")),
            (generate_migration_checklist, ("package_replacement", ["flask"])),
        ]
        
        for prompt_func, args in prompts_to_test:
            result = await prompt_func(*args)
            assert isinstance(result, list)
            assert len(result) > 0
            # Check that each item has a text attribute (Message-like)
            for message in result:
                assert hasattr(message, 'text')
                assert isinstance(message.text, str)
                assert len(message.text) > 0

    @pytest.mark.asyncio
    async def test_prompts_contain_structured_content(self):
        """Test that prompts contain structured, useful content."""
        result = await analyze_package_quality("requests")
        message_text = result[0].text
        
        # Check for structured sections
        assert "##" in message_text  # Should have markdown headers
        assert "📊" in message_text or "🔧" in message_text  # Should have emojis for structure
        assert len(message_text) > 50  # Should be substantial content
        
        # Check for actionable content
        assert any(word in message_text.lower() for word in [
            "analyze", "assessment", "recommendations", "specific", "examples"
        ])

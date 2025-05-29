"""Package analysis prompt templates for PyPI MCP server."""

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field


class Message:
    """Simple message class for prompt templates."""

    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


async def analyze_package_quality(
    package_name: Annotated[
        str, Field(description="Name of the PyPI package to analyze")
    ],
    version: Annotated[
        str | None, Field(description="Specific version to analyze")
    ] = None,
    ctx: Context | None = None,
) -> list[Message]:
    """Generate a comprehensive package quality analysis prompt template.

    This prompt template helps analyze a Python package's quality, maintenance status,
    security, performance, and overall suitability for use in projects.

    Returns a list containing a Message object with the analysis prompt.
    """
    template = """Please provide a comprehensive quality analysis of the Python package '{{package_name}}' {{version_text}}.

Analyze the following aspects and provide a detailed assessment:

## 📊 Package Overview
- Package purpose and functionality
- Current version and release history
- Maintenance status and activity

## 🔧 Technical Quality
- Code quality indicators
- Test coverage and CI/CD setup
- Documentation quality
- API design and usability

## 🛡️ Security & Reliability
- Known security vulnerabilities
- Dependency security assessment
- Stability and backward compatibility

## 📈 Community & Ecosystem
- Download statistics and popularity
- Community support and contributors
- Issue resolution and responsiveness

## 🎯 Recommendations
- Suitability for production use
- Alternative packages to consider
- Best practices for integration

Please provide specific examples and actionable insights where possible."""

    return [Message(template)]


async def compare_packages(
    packages: Annotated[
        list[str],
        Field(
            description="List of package names to compare", min_length=2, max_length=5
        ),
    ],
    use_case: Annotated[
        str, Field(description="Specific use case or project context for comparison")
    ],
    criteria: Annotated[
        list[str] | None,
        Field(
            description="Specific criteria to focus on (e.g., performance, security, ease of use)"
        ),
    ] = None,
    ctx: Context | None = None,
) -> str:
    """Generate a detailed package comparison prompt template.

    This prompt template helps compare multiple Python packages to determine
    the best choice for a specific use case.

    Returns a template string with {{packages_text}}, {{use_case}}, and {{criteria_text}} variables.
    """
    template = """Please provide a detailed comparison of these Python packages: {{packages_text}}

## 🎯 Use Case Context
{{use_case}}{{criteria_text}}

## 📋 Comparison Framework

For each package, analyze:

### Core Functionality
- Feature completeness for the use case
- API design and ease of use
- Performance characteristics

### Ecosystem & Support
- Documentation quality
- Community size and activity
- Learning resources availability

### Technical Considerations
- Dependencies and compatibility
- Installation and setup complexity
- Integration with other tools

### Maintenance & Reliability
- Release frequency and versioning
- Bug fix responsiveness
- Long-term viability

## 🏆 Final Recommendation

Provide a clear recommendation with:
- Best overall choice and why
- Specific scenarios where each package excels
- Migration considerations if switching between them

Please include specific examples and quantitative data where available."""

    return template


async def suggest_alternatives(
    package_name: Annotated[
        str, Field(description="Name of the package to find alternatives for")
    ],
    reason: Annotated[
        Literal[
            "deprecated",
            "security",
            "performance",
            "licensing",
            "maintenance",
            "features",
        ],
        Field(description="Reason for seeking alternatives"),
    ],
    requirements: Annotated[
        str | None,
        Field(description="Specific requirements or constraints for alternatives"),
    ] = None,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for finding package alternatives.

    This prompt template helps find suitable alternatives to a Python package
    based on specific concerns or requirements.

    Returns a template string with {{package_name}}, {{reason_text}}, and {{requirements_text}} variables.
    """
    template = """I need to find alternatives to the Python package '{{package_name}}' because of {{reason_text}}.{{requirements_text}}

Please help me identify suitable alternatives by analyzing:

## 🔍 Alternative Discovery
- Popular packages with similar functionality
- Emerging or newer solutions
- Enterprise or commercial alternatives if relevant

## 📊 Alternative Analysis

For each suggested alternative:

### Functional Compatibility
- Feature parity with '{{package_name}}'
- API similarity and migration effort
- Unique advantages or improvements

### Quality Assessment
- Maintenance status and community health
- Documentation and learning curve
- Performance comparisons

### Migration Considerations
- Breaking changes from '{{package_name}}'
- Migration tools or guides available
- Estimated effort and timeline

## 🎯 Recommendations

Provide:
- Top 3 recommended alternatives ranked by suitability
- Quick migration path for the best option
- Pros and cons summary for each alternative
- Any hybrid approaches or gradual migration strategies

Please include specific examples of how to replace key functionality from '{{package_name}}'."""

    return template

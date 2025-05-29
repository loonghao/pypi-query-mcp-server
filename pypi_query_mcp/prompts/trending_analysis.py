"""Trending analysis prompt templates for PyPI MCP server."""

from typing import Annotated, Literal

from fastmcp import Context
from pydantic import Field


class Message:
    """Simple message class for prompt templates."""

    def __init__(self, text: str, role: str = "user"):
        self.text = text
        self.role = role


async def analyze_daily_trends(
    date: Annotated[
        str | None,
        Field(description="Specific date to analyze (YYYY-MM-DD) or 'today'"),
    ] = "today",
    category: Annotated[
        str | None,
        Field(description="Package category to focus on (web, data, ml, etc.)"),
    ] = None,
    limit: Annotated[
        int, Field(description="Number of top packages to analyze", ge=5, le=50)
    ] = 20,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for analyzing daily PyPI trends.

    This prompt template helps analyze the most downloaded packages on PyPI
    for a specific day and understand trending patterns.

    Returns a template string with {{date}}, {{category_filter}}, and {{limit}} variables.
    """
    template = """Please analyze the daily PyPI download trends for {{date}}{{category_filter}}.

## 📊 Daily PyPI Trends Analysis

Show me the top {{limit}} most downloaded Python packages and provide insights into current trends.

### Download Statistics Analysis
- **Top Downloaded Packages**: List the most popular packages by download count
- **Download Numbers**: Specific download counts for each package
- **Growth Patterns**: Compare with previous days/weeks if possible
- **Market Share**: Relative popularity within the ecosystem

## 🔍 Trend Analysis Framework

### For Each Top Package, Analyze:

1. **Package Overview**
   - Package name and primary purpose
   - Current version and release status
   - Maintainer and community info

2. **Download Metrics**
   - Daily download count
   - Weekly/monthly trends (if available)
   - Growth rate and momentum
   - Geographic distribution (if available)

3. **Ecosystem Context**
   - Category/domain (web, data science, ML, etc.)
   - Competing packages in same space
   - Integration with other popular packages
   - Enterprise vs. individual usage patterns

### Trending Insights

#### 🚀 Rising Stars
- Packages with significant growth
- New packages gaining traction
- Emerging technologies and frameworks

#### 📈 Steady Leaders
- Consistently popular packages
- Foundational libraries and tools
- Mature ecosystem components

#### 📉 Declining Trends
- Packages losing popularity
- Potential reasons for decline
- Alternative packages gaining ground

## 🎯 Market Intelligence

### Technology Trends
- What technologies are developers adopting?
- Which frameworks are gaining momentum?
- What problem domains are hot?

### Developer Behavior
- Package selection patterns
- Adoption speed of new technologies
- Community preferences and choices

### Ecosystem Health
- Diversity of popular packages
- Innovation vs. stability balance
- Open source project vitality

## 📋 Actionable Insights

Provide recommendations for:
- **Developers**: Which packages to consider for new projects
- **Maintainers**: Opportunities for package improvement
- **Organizations**: Technology adoption strategies
- **Investors**: Emerging technology trends

Include specific download numbers, growth percentages, and trend analysis."""

    return template


async def find_trending_packages(
    time_period: Annotated[
        Literal["daily", "weekly", "monthly"],
        Field(description="Time period for trend analysis"),
    ] = "weekly",
    trend_type: Annotated[
        Literal["rising", "declining", "new", "all"],
        Field(description="Type of trends to focus on"),
    ] = "rising",
    domain: Annotated[
        str | None,
        Field(description="Specific domain or category (web, ai, data, etc.)"),
    ] = None,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for finding trending packages.

    This prompt template helps identify packages that are trending up or down
    in the PyPI ecosystem over specific time periods.

    Returns a template string with {{time_period}}, {{trend_type}}, and {{domain_filter}} variables.
    """
    template = """Please identify {{trend_type}} trending Python packages over the {{time_period}} period{{domain_filter}}.

## 📈 Trending Package Discovery

Focus on packages showing significant {{trend_type}} trends in downloads and adoption.

### Trend Analysis Criteria

#### For {{trend_type}} Packages:
- **Rising**: Packages with increasing download velocity
- **Declining**: Packages losing popularity or downloads
- **New**: Recently published packages gaining traction
- **All**: Comprehensive trend analysis across categories

### Time Period: {{time_period}}
- **Daily**: Last 24-48 hours trend analysis
- **Weekly**: 7-day trend patterns and changes
- **Monthly**: 30-day trend analysis and momentum

## 🔍 Discovery Framework

### Trend Identification Metrics
1. **Download Growth Rate**
   - Percentage increase/decrease in downloads
   - Velocity of change (acceleration/deceleration)
   - Consistency of trend direction

2. **Community Engagement**
   - GitHub stars and forks growth
   - Issue activity and resolution
   - Community discussions and mentions

3. **Release Activity**
   - Recent version releases
   - Update frequency and quality
   - Feature development pace

### For Each Trending Package, Provide:

#### 📊 Trend Metrics
- Current download numbers
- Growth/decline percentage
- Trend duration and stability
- Comparison with similar packages

#### 🔍 Package Analysis
- **Purpose and Functionality**: What problem does it solve?
- **Target Audience**: Who is using this package?
- **Unique Value Proposition**: Why is it trending?
- **Competition Analysis**: How does it compare to alternatives?

#### 🚀 Trend Drivers
- **Technology Shifts**: New frameworks or paradigms
- **Community Events**: Conferences, tutorials, viral content
- **Industry Adoption**: Enterprise or startup usage
- **Integration Opportunities**: Works well with popular tools

## 🎯 Trend Categories

### 🌟 Breakout Stars
- New packages with explosive growth
- Innovative solutions to common problems
- Next-generation tools and frameworks

### 📈 Steady Climbers
- Consistent growth over time
- Building solid user base
- Proven value and reliability

### ⚡ Viral Hits
- Sudden popularity spikes
- Social media or community driven
- May need sustainability assessment

### 🔄 Comeback Stories
- Previously popular packages regaining traction
- Major updates or improvements
- Community revival efforts

## 📋 Strategic Insights

### For Developers
- Which trending packages to evaluate for projects
- Early adoption opportunities and risks
- Technology direction indicators

### For Package Maintainers
- Competitive landscape changes
- Opportunities for collaboration
- Feature gaps in trending solutions

### For Organizations
- Technology investment directions
- Skill development priorities
- Strategic technology partnerships

Include specific trend data, growth metrics, and actionable recommendations."""

    return template


async def track_package_updates(
    time_range: Annotated[
        Literal["today", "week", "month"],
        Field(description="Time range for update tracking"),
    ] = "today",
    update_type: Annotated[
        Literal["all", "major", "security", "new"],
        Field(description="Type of updates to track"),
    ] = "all",
    popular_only: Annotated[
        bool, Field(description="Focus only on popular packages (>1M downloads)")
    ] = False,
    ctx: Context | None = None,
) -> str:
    """Generate a prompt template for tracking recent package updates.

    This prompt template helps track and analyze recent package updates
    on PyPI with filtering and categorization options.

    Returns a template string with {{time_range}}, {{update_type}}, and {{popularity_filter}} variables.
    """
    template = """Please track and analyze Python package updates from {{time_range}}{{popularity_filter}}.

## 📦 Package Update Tracking

Focus on {{update_type}} updates and provide insights into recent changes in the Python ecosystem.

### Update Analysis Scope
- **Time Range**: {{time_range}}
- **Update Type**: {{update_type}} updates
- **Package Selection**: {{popularity_description}}

## 🔍 Update Categories

### 🚨 Security Updates
- CVE fixes and security patches
- Vulnerability remediation
- Security-related improvements

### 🎯 Major Version Updates
- Breaking changes and API modifications
- New features and capabilities
- Architecture improvements

### 🔧 Minor Updates & Bug Fixes
- Bug fixes and stability improvements
- Performance enhancements
- Compatibility updates

### 🌟 New Package Releases
- Brand new packages published
- First stable releases (1.0.0)
- Emerging tools and libraries

## 📊 For Each Update, Provide:

### Update Details
1. **Package Information**
   - Package name and description
   - Previous version → New version
   - Release date and timing

2. **Change Analysis**
   - Key changes and improvements
   - Breaking changes (if any)
   - New features and capabilities
   - Bug fixes and security patches

3. **Impact Assessment**
   - Who should update and when
   - Compatibility considerations
   - Testing requirements
   - Migration effort (for major updates)

### Ecosystem Impact
- **Dependency Effects**: How updates affect dependent packages
- **Community Response**: Developer adoption and feedback
- **Integration Impact**: Effects on popular development stacks

## 🎯 Update Insights

### 🔥 Notable Updates
- Most significant updates of the period
- High-impact changes for developers
- Security-critical updates requiring immediate attention

### 📈 Trend Patterns
- Which types of updates are most common
- Package maintenance activity levels
- Ecosystem health indicators

### ⚠️ Breaking Changes Alert
- Major version updates with breaking changes
- Migration guides and resources
- Timeline recommendations for updates

### 🌟 Innovation Highlights
- New features and capabilities
- Emerging patterns and technologies
- Developer experience improvements

## 📋 Action Recommendations

### Immediate Actions
- Critical security updates to apply now
- High-priority bug fixes
- Compatibility updates needed

### Planned Updates
- Major version upgrades requiring testing
- Feature updates worth evaluating
- Performance improvements to consider

### Monitoring Setup
- Packages to watch for future updates
- Automated update strategies
- Dependency management improvements

Include specific version numbers, release notes highlights, and update commands."""

    return template

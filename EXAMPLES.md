# 🎤 mcpypi Examples & Project Bootstrap Guide

This guide provides practical examples of using mcpypi's 48 tools to bootstrap projects and demonstrate advanced PyPI intelligence capabilities.

## 🚀 Project Bootstrap Examples

### 1. Starting a New Web API Project

**Prompt**: "Help me choose the best packages for a new Python web API project that needs authentication, database ORM, and fast performance."

**mcpypi tools to use**:
```
get_pypi_package_rankings + category=web
compare_packages_health_scores + packages=[fastapi, django, flask]
analyze_pypi_package_license + package=fastapi
scan_pypi_package_security + package=fastapi
get_package_dependencies + package=fastapi
```

**Example Claude Code session**:
```
User: I'm starting a new web API project. Help me compare FastAPI, Django, and Flask.

Claude: I'll analyze these three popular web frameworks for you using mcpypi.

[Uses compare_packages_health_scores tool]
Based on the health analysis:
- FastAPI: Score 9.2/10 (excellent maintenance, high GitHub stars, active development)
- Django: Score 8.8/10 (mature, stable, large community)  
- Flask: Score 8.5/10 (simple, flexible, well-maintained)

[Uses scan_pypi_package_security tool for each]
Security analysis shows all three are actively maintained with no critical vulnerabilities.

[Uses analyze_pypi_package_license tool]
All three use permissive licenses compatible with commercial projects.

**Recommendation**: FastAPI for modern async APIs, Django for full-featured applications, Flask for microservices.
```

### 2. Machine Learning Project Setup

**Prompt**: "Set up a machine learning project with the latest compatible versions of numpy, pandas, scikit-learn, and tensorflow."

**mcpypi tools to use**:
```
get_package_compatible_python_versions + package=tensorflow
resolve_dependencies + packages=[numpy, pandas, scikit-learn, tensorflow] + python_version=3.11
check_bulk_license_compliance + packages=[numpy, pandas, scikit-learn, tensorflow]
assess_package_health_score + package=tensorflow
get_download_statistics + package=tensorflow
```

### 3. Security-First Development

**Prompt**: "Audit my project dependencies for security vulnerabilities and license compliance before production deployment."

**mcpypi tools to use**:
```
analyze_requirements_file_tool + requirements.txt
bulk_scan_package_security + all_packages_from_requirements
check_bulk_license_compliance + target_license=MIT
compare_multiple_requirements_files + [dev.txt, prod.txt]
```

## 🎯 Demonstration Scenarios

### Advanced Package Intelligence

**Scenario**: "I need to understand the entire ecosystem around web scraping in Python."

```python
# 1. Find the top web scraping packages
get_pypi_package_rankings(category="web-scraping", limit=10)

# 2. Compare the leaders
compare_packages_health_scores(["requests", "scrapy", "beautifulsoup4", "selenium"])

# 3. Analyze dependencies and conflicts
resolve_dependencies("scrapy", python_version="3.11")
resolve_dependencies("selenium", python_version="3.11")

# 4. Check for security issues
bulk_scan_package_security(["requests", "scrapy", "beautifulsoup4", "selenium"])

# 5. License compatibility analysis
check_bulk_license_compliance(
    package_names=["requests", "scrapy", "beautifulsoup4", "selenium"],
    target_license="MIT"
)
```

### Trend Analysis & Discovery

**Scenario**: "What are the emerging trends in AI/ML packages this month?"

```python
# 1. Get trending packages
get_pypi_trending_today(category="artificial-intelligence", limit=20)

# 2. Analyze top downloads
get_top_downloaded_packages(period="month", limit=50)

# 3. Find new releases
monitor_pypi_new_releases(time_window="30d", category_filter="machine-learning")

# 4. Get recommendations based on popular packages
get_pypi_package_recommendations("transformers", recommendation_type="trending")
```

### Production Deployment Audit

**Scenario**: "Comprehensive pre-production audit of our Python application."

```python
# 1. Parse and analyze requirements
analyze_requirements_file_tool("requirements.txt", check_updates=True)

# 2. Security vulnerability scan
bulk_scan_package_security(all_requirements_packages, include_dependencies=True)

# 3. License compliance check
check_bulk_license_compliance(all_requirements_packages, target_license="MIT")

# 4. Health assessment of critical packages
assess_package_health_score("critical-package-1")
assess_package_health_score("critical-package-2")

# 5. Check for newer versions
get_download_trends("numpy")  # Check if using latest stable version
```

## 🛠️ Development Workflow Examples

### Package Publishing Workflow

```python
# 1. Validate package name availability
validate_pypi_package_name("my-awesome-package")

# 2. Check upload requirements
check_pypi_upload_requirements("./dist/my-package-1.0.0/")

# 3. Preview how package page will look
preview_pypi_package_page("my-awesome-package")

# 4. Upload to PyPI (requires API token)
upload_package_to_pypi(["dist/my-package-1.0.0.tar.gz"])

# 5. Monitor upload history
get_pypi_upload_history("my-awesome-package")
```

### Dependency Management

```python
# 1. Analyze current environment
analyze_requirements_file_tool("requirements.txt")

# 2. Find alternatives to problematic packages
find_package_alternatives("problematic-package")

# 3. Check Python version compatibility
get_package_compatible_python_versions("target-package", ["3.9", "3.10", "3.11", "3.12"])

# 4. Resolve dependency conflicts
resolve_dependencies("package-with-conflicts", python_version="3.11")
```

## 🎨 Creative Use Cases

### Package Ecosystem Analysis

**Use Case**: Create a comprehensive report on the Python web framework ecosystem.

```python
frameworks = ["django", "flask", "fastapi", "tornado", "pyramid", "bottle"]

for framework in frameworks:
    health = assess_package_health_score(framework)
    security = scan_pypi_package_security(framework)  
    stats = get_download_statistics(framework, period="month")
    license_info = analyze_pypi_package_license(framework)
    
    # Compile comprehensive ecosystem report
```

### Alternative Package Discovery

**Use Case**: Find lesser-known but high-quality alternatives to popular packages.

```python
# Find alternatives to popular packages
alternatives_requests = find_package_alternatives("requests")
alternatives_numpy = find_package_alternatives("numpy")

# Health score the alternatives
for alt in alternatives_requests:
    health = assess_package_health_score(alt["name"])
    if health["overall_score"] > 8.0:
        print(f"High-quality alternative found: {alt['name']}")
```

### License Compliance Automation

**Use Case**: Automate license compliance across multiple projects.

```python
projects = [
    {"name": "web-app", "requirements": "web-app/requirements.txt"},
    {"name": "ml-model", "requirements": "ml-model/requirements.txt"},
    {"name": "data-pipeline", "requirements": "pipeline/requirements.txt"}
]

for project in projects:
    compliance = analyze_requirements_file_tool(
        project["requirements"], 
        check_updates=True
    )
    
    license_check = check_bulk_license_compliance(
        compliance["packages"],
        target_license="MIT"
    )
    
    if license_check["has_conflicts"]:
        print(f"⚠️ License conflicts in {project['name']}")
```

## 🎪 Fun & Educational Examples

### Package Popularity Contest

```python
# Compare download stats of competing packages
web_frameworks = ["django", "flask", "fastapi"]
for framework in web_frameworks:
    stats = get_download_statistics(framework, period="month")
    trends = get_download_trends(framework)
    print(f"{framework}: {stats['downloads']['last_month']:,} downloads this month")
```

### Security Leaderboard

```python
# Find the most secure packages in a category
packages = get_pypi_package_rankings(category="web", limit=20)
security_scores = []

for package in packages:
    security = scan_pypi_package_security(package["name"])
    health = assess_package_health_score(package["name"])
    security_scores.append({
        "name": package["name"],
        "security_score": security.get("risk_score", 0),
        "health_score": health["overall_score"]
    })

# Sort by security and health
top_secure = sorted(security_scores, key=lambda x: (x["security_score"], x["health_score"]), reverse=True)
```

### Trend Prediction

```python
# Analyze trends to predict rising packages
trending = get_pypi_trending_today(limit=50)
for package in trending:
    if package["growth_rate"] > 500:  # 500% growth
        health = assess_package_health_score(package["name"])
        if health["overall_score"] > 7.0:
            print(f"🚀 Rising star: {package['name']} - {package['growth_rate']}% growth")
```

## 🎤 Integration with Other Tools

### CI/CD Pipeline Integration

```bash
# Example GitHub Actions workflow
name: mcpypi Security Check
on: [push, pull_request]
jobs:
  security-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: uvx mcpypi # Start MCP server
      - run: |
          # Use claude-cli or custom script to run security checks
          claude mcp add mcpypi -- uvx mcpypi
          claude "Scan all packages in requirements.txt for security vulnerabilities"
```

### IDE Integration Examples

```python
# VS Code extension idea - Package Intelligence
def on_requirements_file_open():
    packages = parse_requirements_file()
    for package in packages:
        health = assess_package_health_score(package)
        if health["overall_score"] < 6.0:
            show_warning(f"Package {package} has low health score")
```

---

## 🎊 Getting Started

1. **Install mcpypi**: `uvx mcpypi`
2. **Connect to Claude Code**: `claude mcp add mcpypi -- uvx mcpypi`
3. **Start exploring**: Ask Claude to help you with any of these examples!

**Pro Tip**: Combine multiple tools in a single conversation for comprehensive analysis. mcpypi's 48 tools work together to give you complete PyPI intelligence! 🎯
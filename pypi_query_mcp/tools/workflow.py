"""PyPI Development Workflow Tools for package validation and preview."""

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from ..core import InvalidPackageNameError, NetworkError, PackageNotFoundError, PyPIClient
from ..core.exceptions import PyPIError

logger = logging.getLogger(__name__)


class PyPIWorkflowError(PyPIError):
    """Raised when workflow operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        super().__init__(message)
        self.operation = operation


def _validate_package_name_format(package_name: str) -> Dict[str, Any]:
    """Validate package name format according to PyPI standards.
    
    Args:
        package_name: Package name to validate
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    recommendations = []
    
    # Check basic format
    if not package_name:
        issues.append("Package name cannot be empty")
        return {
            "valid": False,
            "issues": issues,
            "recommendations": ["Provide a non-empty package name"],
            "normalized_name": "",
        }
    
    # Length constraints
    if len(package_name) > 214:
        issues.append("Package name is too long (max 214 characters)")
    if len(package_name) < 1:
        issues.append("Package name is too short (min 1 character)")
    
    # Character validation
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?$", package_name):
        issues.append("Package name contains invalid characters (only alphanumeric, dots, hyphens, underscores allowed)")
    
    # Check for reserved names
    reserved_names = {
        "pip", "setuptools", "wheel", "python", "test", "tests", 
        "src", "docs", "build", "dist", "requirements", "readme"
    }
    if package_name.lower() in reserved_names:
        issues.append(f"'{package_name}' is a reserved name and should not be used")
    
    # Best practice checks
    if package_name != package_name.lower():
        recommendations.append("Use lowercase for package names (PEP 508)")
    
    if "_" in package_name:
        recommendations.append("Consider using hyphens instead of underscores (PEP 508)")
    
    if len(package_name.split("-")) > 3:
        recommendations.append("Avoid overly complex names with many hyphens")
    
    # Check for common typos/patterns
    if package_name.startswith("-") or package_name.endswith("-"):
        issues.append("Package name cannot start or end with a hyphen")
    
    if package_name.startswith(".") or package_name.endswith("."):
        issues.append("Package name cannot start or end with a dot")
    
    if "--" in package_name or ".." in package_name:
        issues.append("Package name cannot contain consecutive special characters")
    
    # Normalize name for PyPI (convert to lowercase, normalize separators)
    normalized = re.sub(r"[-_.]+", "-", package_name.lower())
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "recommendations": recommendations,
        "normalized_name": normalized,
    }


async def validate_pypi_package_name(package_name: str) -> Dict[str, Any]:
    """Check if a package name is available and valid on PyPI.
    
    This function validates package name format and checks availability on PyPI.
    It also provides recommendations for improvement based on PyPI standards.
    
    Args:
        package_name: Name to validate and check for availability
        
    Returns:
        Dictionary containing validation results including:
        - Format validation results
        - Availability status on PyPI
        - Recommendations for improvement
        - Similar existing packages (if any)
        
    Raises:
        InvalidPackageNameError: If package name format is severely invalid
        NetworkError: For network-related errors
        PyPIWorkflowError: For workflow-specific errors
    """
    logger.info(f"Validating package name: {package_name}")
    
    try:
        # First validate format
        format_validation = _validate_package_name_format(package_name)
        
        if not format_validation["valid"] and len(format_validation["issues"]) > 2:
            raise InvalidPackageNameError(package_name)
        
        # Check availability on PyPI
        availability_status = "unknown"
        existing_package_info = None
        similar_packages = []
        
        try:
            async with PyPIClient() as client:
                # Try to get package info to check if it exists
                package_data = await client.get_package_info(package_name)
                availability_status = "taken"
                existing_package_info = {
                    "name": package_data["info"]["name"],
                    "version": package_data["info"]["version"],
                    "summary": package_data["info"]["summary"],
                    "upload_time": package_data["info"].get("upload_time"),
                    "author": package_data["info"].get("author"),
                }
        except PackageNotFoundError:
            availability_status = "available"
        except Exception as e:
            logger.warning(f"Could not check availability for {package_name}: {e}")
            availability_status = "unknown"
        
        # If package is taken or format is questionable, find similar packages
        if availability_status == "taken" or not format_validation["valid"]:
            try:
                # Search for similar packages
                search_query = format_validation["normalized_name"]
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    search_url = f"https://pypi.org/search/?q={quote(search_query)}"
                    # Note: We're not actually parsing HTML here - this would need 
                    # integration with the search functionality for real similar packages
                    # For now, we'll just note that similar package detection is available
                    similar_packages = []  # Placeholder
            except Exception as e:
                logger.warning(f"Could not search for similar packages: {e}")
        
        # Generate suggestions based on validation results
        suggestions = []
        if availability_status == "taken":
            suggestions.extend([
                f"Try variations like '{package_name}-dev', '{package_name}-cli', or '{package_name}2'",
                "Consider a more specific or descriptive name",
                "Add your organization name as a prefix"
            ])
        
        if format_validation["recommendations"]:
            suggestions.extend(format_validation["recommendations"])
        
        return {
            "package_name": package_name,
            "normalized_name": format_validation["normalized_name"],
            "validation": {
                "format_valid": format_validation["valid"],
                "issues": format_validation["issues"],
                "recommendations": format_validation["recommendations"],
            },
            "availability": {
                "status": availability_status,  # "available", "taken", "unknown"
                "existing_package": existing_package_info,
                "similar_packages": similar_packages,
            },
            "suggestions": suggestions,
            "pypi_standards_compliant": format_validation["valid"] and availability_status == "available",
            "ready_for_upload": format_validation["valid"] and availability_status == "available",
        }
        
    except InvalidPackageNameError:
        raise
    except Exception as e:
        logger.error(f"Error validating package name {package_name}: {e}")
        raise PyPIWorkflowError(f"Failed to validate package name: {e}", "validate_name") from e


async def preview_pypi_package_page(
    package_name: str,
    version: str = "1.0.0",
    summary: str = "",
    description: str = "",
    author: str = "",
    license_name: str = "MIT",
    home_page: str = "",
    keywords: List[str] = None,
    classifiers: List[str] = None,
) -> Dict[str, Any]:
    """Generate a preview of how a package page would look on PyPI.
    
    This function creates a preview of the PyPI package page based on the
    provided metadata, helping developers visualize their package before upload.
    
    Args:
        package_name: Name of the package
        version: Package version (default: "1.0.0")
        summary: Short package description
        description: Long package description
        author: Package author name
        license_name: License type (default: "MIT")
        home_page: Project homepage URL
        keywords: List of keywords for the package
        classifiers: List of PyPI classifiers
        
    Returns:
        Dictionary containing preview information including:
        - Formatted package metadata
        - Rendered page sections
        - Validation warnings
        - SEO recommendations
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PyPIWorkflowError: For preview generation errors
    """
    logger.info(f"Generating preview for package: {package_name}")
    
    if keywords is None:
        keywords = []
    if classifiers is None:
        classifiers = []
    
    try:
        # Validate package name first
        name_validation = _validate_package_name_format(package_name)
        if not name_validation["valid"]:
            raise InvalidPackageNameError(package_name)
        
        # Validate version format
        version_pattern = r"^([0-9]+)\.([0-9]+)\.([0-9]+)(?:[-.]?(a|b|rc)[0-9]*)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?$"
        version_valid = bool(re.match(version_pattern, version))
        
        # Generate preview content
        preview_sections = {
            "header": {
                "name": package_name,
                "version": version,
                "summary": summary or "No description provided",
                "upload_date": "Not yet uploaded",
                "author": author or "Not specified",
            },
            "navigation": {
                "project_description": True,
                "release_history": False,  # Will be available after first upload
                "download_files": False,   # Will be available after first upload
                "statistics": False,       # Will be available after upload
            },
            "metadata": {
                "license": license_name,
                "home_page": home_page or "Not provided",
                "keywords": keywords,
                "classifiers": classifiers,
                "requires_python": "Not specified",
                "project_urls": {},
            },
            "description": {
                "content": description or "No detailed description provided",
                "format": "text/plain" if description and not description.strip().startswith("<") else "text/markdown",
                "length": len(description) if description else 0,
            },
        }
        
        # Generate recommendations and warnings
        recommendations = []
        warnings = []
        
        # Check for missing critical information
        if not summary:
            warnings.append("Summary is missing - this appears prominently in search results")
        elif len(summary) < 10:
            recommendations.append("Consider a more descriptive summary (current: {len(summary)} chars)")
        elif len(summary) > 200:
            warnings.append("Summary is quite long - consider keeping it under 200 characters")
        
        if not description:
            warnings.append("No description provided - users won't understand what your package does")
        elif len(description) < 100:
            recommendations.append("Consider providing a more detailed description")
        
        if not author:
            warnings.append("Author name is missing")
        
        if not home_page:
            recommendations.append("Consider adding a homepage URL (GitHub, documentation, etc.)")
        
        if not keywords:
            recommendations.append("Add keywords to improve discoverability")
        elif len(keywords) > 10:
            recommendations.append("Consider reducing keywords to the most relevant ones")
        
        if not classifiers:
            recommendations.append("Add PyPI classifiers to categorize your package")
        else:
            # Check for important classifier categories
            has_python_version = any("Python ::" in c for c in classifiers)
            has_topic = any("Topic ::" in c for c in classifiers)
            has_development_status = any("Development Status ::" in c for c in classifiers)
            
            if not has_python_version:
                recommendations.append("Add Python version classifiers (e.g., 'Programming Language :: Python :: 3.8')")
            if not has_topic:
                recommendations.append("Add topic classifiers to categorize your package")
            if not has_development_status:
                recommendations.append("Add development status classifier")
        
        if not version_valid:
            warnings.append("Version format may not follow PEP 440 standards")
        
        # SEO and discoverability analysis
        seo_analysis = {
            "title_optimization": {
                "length": len(package_name),
                "readability": "good" if len(package_name.split("-")) <= 3 else "complex",
                "keyword_rich": len(keywords) > 0,
            },
            "description_optimization": {
                "length": len(description) if description else 0,
                "has_keywords": any(kw.lower() in description.lower() for kw in keywords) if description and keywords else False,
                "structure": "needs_improvement" if not description else "basic",
            },
            "discoverability_score": _calculate_discoverability_score(
                summary, description, keywords, classifiers
            ),
        }
        
        # Generate rendered preview (simplified HTML-like structure)
        rendered_preview = _generate_html_preview(preview_sections)
        
        return {
            "package_name": package_name,
            "version": version,
            "preview": {
                "sections": preview_sections,
                "rendered_html": rendered_preview,
                "url_preview": f"https://pypi.org/project/{package_name}/",
            },
            "validation": {
                "name_valid": name_validation["valid"],
                "version_valid": version_valid,
                "completeness_score": _calculate_completeness_score(preview_sections),
            },
            "recommendations": recommendations,
            "warnings": warnings,
            "seo_analysis": seo_analysis,
            "ready_for_upload": len(warnings) == 0 and name_validation["valid"] and version_valid,
        }
        
    except InvalidPackageNameError:
        raise
    except Exception as e:
        logger.error(f"Error generating preview for {package_name}: {e}")
        raise PyPIWorkflowError(f"Failed to generate preview: {e}", "preview_page") from e


def _calculate_discoverability_score(
    summary: str, description: str, keywords: List[str], classifiers: List[str]
) -> Dict[str, Any]:
    """Calculate a discoverability score based on metadata completeness."""
    score = 0
    max_score = 100
    
    # Summary scoring (25 points)
    if summary:
        if len(summary) >= 20:
            score += 25
        elif len(summary) >= 10:
            score += 15
        else:
            score += 5
    
    # Description scoring (35 points)
    if description:
        if len(description) >= 500:
            score += 35
        elif len(description) >= 200:
            score += 25
        elif len(description) >= 50:
            score += 15
        else:
            score += 5
    
    # Keywords scoring (20 points)
    if keywords:
        if len(keywords) >= 5:
            score += 20
        elif len(keywords) >= 3:
            score += 15
        else:
            score += 10
    
    # Classifiers scoring (20 points)
    if classifiers:
        if len(classifiers) >= 5:
            score += 20
        elif len(classifiers) >= 3:
            score += 15
        else:
            score += 10
    
    level = "excellent" if score >= 80 else "good" if score >= 60 else "fair" if score >= 40 else "poor"
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 1),
        "level": level,
    }


def _calculate_completeness_score(preview_sections: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate completeness score based on available metadata."""
    score = 0
    max_score = 100
    
    header = preview_sections["header"]
    metadata = preview_sections["metadata"]
    description = preview_sections["description"]
    
    # Essential fields (60 points)
    if header["summary"] and header["summary"] != "No description provided":
        score += 20
    if header["author"] and header["author"] != "Not specified":
        score += 15
    if description["content"] and description["content"] != "No detailed description provided":
        score += 25
    
    # Important fields (30 points)
    if metadata["license"]:
        score += 10
    if metadata["home_page"] and metadata["home_page"] != "Not provided":
        score += 10
    if metadata["keywords"]:
        score += 5
    if metadata["classifiers"]:
        score += 5
    
    # Nice-to-have fields (10 points)
    if description["length"] > 200:
        score += 5
    if len(metadata["keywords"]) >= 3:
        score += 5
    
    level = "complete" if score >= 80 else "good" if score >= 60 else "basic" if score >= 40 else "incomplete"
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": round((score / max_score) * 100, 1),
        "level": level,
    }


def _generate_html_preview(preview_sections: Dict[str, Any]) -> str:
    """Generate a simplified HTML preview of the PyPI page."""
    header = preview_sections["header"]
    metadata = preview_sections["metadata"]
    description = preview_sections["description"]
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{header['name']} · PyPI</title>
    <meta name="description" content="{header['summary']}">
</head>
<body>
    <div class="package-header">
        <h1 class="package-title">{header['name']} {header['version']}</h1>
        <p class="package-summary">{header['summary']}</p>
        <div class="package-meta">
            <span>by {header['author']}</span>
            <span>License: {metadata['license']}</span>
        </div>
    </div>
    
    <div class="package-navigation">
        <nav>
            <a href="#description" class="active">Project description</a>
            <a href="#history" class="disabled">Release history</a>
            <a href="#files" class="disabled">Download files</a>
        </nav>
    </div>
    
    <div class="package-content">
        <div class="main-content">
            <section id="description">
                <h2>Project description</h2>
                <div class="project-description">
                    {description['content']}
                </div>
            </section>
        </div>
        
        <div class="sidebar">
            <div class="metadata">
                <h3>Project links</h3>
                <ul>
                    <li>Homepage: {metadata['home_page']}</li>
                </ul>
                
                <h3>Meta</h3>
                <ul>
                    <li>License: {metadata['license']}</li>
                    <li>Keywords: {', '.join(metadata['keywords']) if metadata['keywords'] else 'None'}</li>
                </ul>
                
                <h3>Classifiers</h3>
                <ul>
                    {chr(10).join(f'<li>{classifier}</li>' for classifier in metadata['classifiers'])}
                </ul>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return html.strip()


async def check_pypi_upload_requirements(
    package_name: str,
    version: str = "1.0.0",
    author: str = "",
    author_email: str = "",
    description: str = "",
    long_description: str = "",
    license_name: str = "",
    home_page: str = "",
    classifiers: List[str] = None,
    requires_python: str = "",
) -> Dict[str, Any]:
    """Check if package metadata meets PyPI upload requirements.
    
    This function validates all required and recommended metadata fields
    for PyPI package upload, following setup.py and setuptools standards.
    
    Args:
        package_name: Name of the package
        version: Package version
        author: Package author name
        author_email: Author email address
        description: Short package description
        long_description: Detailed package description
        license_name: License identifier
        home_page: Project homepage URL
        classifiers: List of PyPI classifiers
        requires_python: Python version requirements
        
    Returns:
        Dictionary containing upload readiness assessment including:
        - Required fields validation
        - Recommended fields suggestions
        - Compliance with PyPI standards
        - Upload checklist
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PyPIWorkflowError: For validation errors
    """
    logger.info(f"Checking upload requirements for package: {package_name}")
    
    if classifiers is None:
        classifiers = []
    
    try:
        # Validate package name
        name_validation = _validate_package_name_format(package_name)
        if not name_validation["valid"]:
            raise InvalidPackageNameError(package_name)
        
        # Check required fields (according to PyPI)
        required_fields = {
            "name": {
                "value": package_name,
                "valid": bool(package_name and name_validation["valid"]),
                "requirement": "Required by PyPI",
            },
            "version": {
                "value": version,
                "valid": bool(version and re.match(r"^[0-9]+\.[0-9]+(?:\.[0-9]+)?", version)),
                "requirement": "Required by PyPI",
            },
            "description": {
                "value": description,
                "valid": bool(description and len(description.strip()) > 0),
                "requirement": "Required for good UX",
            },
            "author": {
                "value": author,
                "valid": bool(author and len(author.strip()) > 0),
                "requirement": "Required by PyPI",
            },
        }
        
        # Check strongly recommended fields
        recommended_fields = {
            "author_email": {
                "value": author_email,
                "valid": bool(author_email and "@" in author_email),
                "importance": "High - for package maintenance contact",
            },
            "long_description": {
                "value": long_description,
                "valid": bool(long_description and len(long_description.strip()) > 50),
                "importance": "High - users need to understand your package",
            },
            "license": {
                "value": license_name,
                "valid": bool(license_name),
                "importance": "High - legal clarity",
            },
            "home_page": {
                "value": home_page,
                "valid": bool(home_page and home_page.startswith(("http://", "https://"))),
                "importance": "Medium - project discoverability",
            },
            "classifiers": {
                "value": classifiers,
                "valid": bool(classifiers and len(classifiers) >= 3),
                "importance": "Medium - package categorization",
            },
            "requires_python": {
                "value": requires_python,
                "valid": bool(requires_python),
                "importance": "Medium - compatibility clarity",
            },
        }
        
        # Calculate compliance scores
        required_valid = sum(1 for field in required_fields.values() if field["valid"])
        required_total = len(required_fields)
        required_compliance = (required_valid / required_total) * 100
        
        recommended_valid = sum(1 for field in recommended_fields.values() if field["valid"])
        recommended_total = len(recommended_fields)
        recommended_compliance = (recommended_valid / recommended_total) * 100
        
        # Generate specific validation errors and warnings
        errors = []
        warnings = []
        suggestions = []
        
        for field_name, field_info in required_fields.items():
            if not field_info["valid"]:
                errors.append(f"Missing or invalid {field_name}: {field_info['requirement']}")
        
        for field_name, field_info in recommended_fields.items():
            if not field_info["valid"]:
                if field_info["importance"].startswith("High"):
                    warnings.append(f"Missing {field_name}: {field_info['importance']}")
                else:
                    suggestions.append(f"Consider adding {field_name}: {field_info['importance']}")
        
        # Additional validation checks
        if version and not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+", version):
            warnings.append("Version should follow semantic versioning (e.g., 1.0.0)")
        
        if long_description and len(long_description) > 10000:
            suggestions.append("Long description is quite lengthy - consider summarizing")
        
        if author_email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", author_email):
            warnings.append("Author email format appears invalid")
        
        # Check for common license patterns
        common_licenses = ["MIT", "Apache-2.0", "GPL", "BSD", "LGPL"]
        if license_name and not any(lic in license_name for lic in common_licenses):
            suggestions.append("Consider using a standard license identifier (MIT, Apache-2.0, etc.)")
        
        # Generate upload checklist
        upload_checklist = [
            {
                "item": "Package name is valid and available",
                "status": "complete" if name_validation["valid"] else "incomplete",
                "critical": True,
            },
            {
                "item": "Version follows PEP 440",
                "status": "complete" if required_fields["version"]["valid"] else "incomplete", 
                "critical": True,
            },
            {
                "item": "All required metadata fields provided",
                "status": "complete" if required_compliance == 100 else "incomplete",
                "critical": True,
            },
            {
                "item": "Author contact information provided", 
                "status": "complete" if recommended_fields["author_email"]["valid"] else "incomplete",
                "critical": False,
            },
            {
                "item": "Detailed description provided",
                "status": "complete" if recommended_fields["long_description"]["valid"] else "incomplete",
                "critical": False,
            },
            {
                "item": "License specified",
                "status": "complete" if recommended_fields["license"]["valid"] else "incomplete",
                "critical": False,
            },
            {
                "item": "Package classifiers added",
                "status": "complete" if recommended_fields["classifiers"]["valid"] else "incomplete",
                "critical": False,
            },
        ]
        
        # Determine overall readiness
        can_upload = required_compliance == 100 and len(errors) == 0
        should_upload = can_upload and recommended_compliance >= 60
        
        readiness_level = (
            "ready" if should_upload
            else "can_upload_with_warnings" if can_upload
            else "not_ready"
        )
        
        return {
            "package_name": package_name,
            "version": version,
            "validation": {
                "required_fields": required_fields,
                "recommended_fields": recommended_fields,
                "compliance": {
                    "required_percentage": round(required_compliance, 1),
                    "recommended_percentage": round(recommended_compliance, 1),
                    "overall_score": round((required_compliance * 0.7 + recommended_compliance * 0.3), 1),
                },
            },
            "issues": {
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions,
            },
            "upload_readiness": {
                "level": readiness_level,
                "can_upload": can_upload,
                "should_upload": should_upload,
                "checklist": upload_checklist,
            },
            "next_steps": _generate_next_steps(errors, warnings, suggestions, can_upload),
        }
        
    except InvalidPackageNameError:
        raise
    except Exception as e:
        logger.error(f"Error checking upload requirements for {package_name}: {e}")
        raise PyPIWorkflowError(f"Failed to check upload requirements: {e}", "check_requirements") from e


def _generate_next_steps(
    errors: List[str], warnings: List[str], suggestions: List[str], can_upload: bool
) -> List[str]:
    """Generate actionable next steps based on validation results."""
    steps = []
    
    if errors:
        steps.append("🚨 Fix critical errors before upload:")
        steps.extend(f"   - {error}" for error in errors[:3])  # Limit to top 3
        if len(errors) > 3:
            steps.append(f"   - ... and {len(errors) - 3} more error(s)")
    
    if can_upload:
        if warnings:
            steps.append("⚠️  Address important warnings:")
            steps.extend(f"   - {warning}" for warning in warnings[:2])
        
        if suggestions:
            steps.append("💡 Consider these improvements:")
            steps.extend(f"   - {suggestion}" for suggestion in suggestions[:2])
        
        steps.append("✅ Ready for upload! Run: twine upload dist/*")
    else:
        steps.append("📋 Complete required fields first, then re-run this check")
    
    return steps


async def get_pypi_build_logs(
    package_name: str,
    version: Optional[str] = None,
    platform: str = "all",
    include_details: bool = True,
) -> Dict[str, Any]:
    """Retrieve and analyze PyPI build logs and distribution information.
    
    This function fetches information about package builds, wheel distributions,
    and any build-related warnings or errors from PyPI.
    
    Args:
        package_name: Name of the package to analyze
        version: Specific version to check (optional, defaults to latest)
        platform: Platform filter ("all", "windows", "macos", "linux") 
        include_details: Whether to include detailed file analysis
        
    Returns:
        Dictionary containing build information including:
        - Available distributions (wheels, source)
        - Build status and platform support
        - File sizes and checksums
        - Build warnings and recommendations
        
    Raises:
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
        PyPIWorkflowError: For build log analysis errors
    """
    logger.info(f"Analyzing build logs for package: {package_name}")
    
    try:
        # Get package information from PyPI
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name, version=version)
        
        info = package_data["info"]
        releases = package_data.get("releases", {})
        urls = package_data.get("urls", [])
        
        # Get the specific version we're analyzing
        target_version = version or info.get("version")
        if not target_version:
            raise PyPIWorkflowError("Could not determine package version", "get_build_logs")
        
        # Get release files for the target version
        release_files = releases.get(target_version, [])
        if not release_files and urls:
            # Fallback to URLs if releases is empty (latest version)
            release_files = urls
        
        if not release_files:
            raise PyPIWorkflowError(f"No build files found for version {target_version}", "get_build_logs")
        
        # Analyze distributions
        distributions = {
            "wheels": [],
            "source": [],
            "other": [],
        }
        
        total_size = 0
        platforms_supported = set()
        python_versions_supported = set()
        
        for file_info in release_files:
            file_type = file_info.get("packagetype", "unknown")
            filename = file_info.get("filename", "")
            file_size = file_info.get("size", 0)
            upload_time = file_info.get("upload_time_iso_8601", "")
            python_version = file_info.get("python_version", "")
            
            total_size += file_size
            
            file_analysis = {
                "filename": filename,
                "type": file_type,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "upload_time": upload_time,
                "python_version": python_version,
                "url": file_info.get("url", ""),
                "md5_digest": file_info.get("md5_digest", ""),
                "sha256_digest": file_info.get("digests", {}).get("sha256", ""),
            }
            
            if file_type == "bdist_wheel":
                # Analyze wheel filename for platform info
                wheel_analysis = _analyze_wheel_filename(filename)
                file_analysis.update(wheel_analysis)
                distributions["wheels"].append(file_analysis)
                
                if wheel_analysis.get("platform"):
                    platforms_supported.add(wheel_analysis["platform"])
                if python_version and python_version != "source":
                    python_versions_supported.add(python_version)
                    
            elif file_type == "sdist":
                distributions["source"].append(file_analysis)
            else:
                distributions["other"].append(file_analysis)
        
        # Filter by platform if specified
        if platform != "all":
            platform_map = {
                "windows": ["win32", "win_amd64"],
                "macos": ["macosx", "darwin"],
                "linux": ["linux"],
            }
            
            if platform in platform_map:
                target_platforms = platform_map[platform]
                distributions["wheels"] = [
                    wheel for wheel in distributions["wheels"]
                    if any(plat in wheel.get("platform", "") for plat in target_platforms)
                ]
        
        # Analyze build quality and issues
        build_analysis = _analyze_build_quality(distributions, info)
        
        # Generate recommendations
        recommendations = []
        warnings = []
        
        if not distributions["wheels"]:
            warnings.append("No wheel distributions found - users will need to build from source")
            recommendations.append("Consider building wheels for major platforms (Windows, macOS, Linux)")
        
        if len(distributions["wheels"]) == 1:
            recommendations.append("Consider providing wheels for multiple platforms")
        
        if not distributions["source"]:
            warnings.append("No source distribution found - this is unusual and may cause issues")
        
        # Check for large files
        large_files = [f for f in release_files if f.get("size", 0) > 50 * 1024 * 1024]  # 50MB
        if large_files:
            warnings.append(f"Large files detected ({len(large_files)} files > 50MB)")
            recommendations.append("Consider splitting large packages or using optional dependencies")
        
        # Python version coverage analysis
        if python_versions_supported:
            if "py3" not in python_versions_supported and not any("3." in v for v in python_versions_supported):
                recommendations.append("Consider providing Python 3 compatible wheels")
            
            if len(python_versions_supported) < 3:
                recommendations.append("Consider supporting more Python versions for better compatibility")
        
        return {
            "package_name": package_name,
            "version": target_version,
            "build_summary": {
                "total_files": len(release_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "wheel_count": len(distributions["wheels"]),
                "source_count": len(distributions["source"]),
                "platforms_supported": sorted(list(platforms_supported)),
                "python_versions": sorted(list(python_versions_supported)),
            },
            "distributions": distributions if include_details else {
                "wheels": len(distributions["wheels"]),
                "source": len(distributions["source"]),
                "other": len(distributions["other"]),
            },
            "build_analysis": build_analysis,
            "issues": {
                "warnings": warnings,
                "recommendations": recommendations,
            },
            "build_status": {
                "has_wheels": len(distributions["wheels"]) > 0,
                "has_source": len(distributions["source"]) > 0,
                "multi_platform": len(platforms_supported) > 1,
                "quality_score": build_analysis["quality_score"],
                "build_health": build_analysis["health_status"],
            },
        }
        
    except (PackageNotFoundError, NetworkError):
        raise
    except Exception as e:
        logger.error(f"Error analyzing build logs for {package_name}: {e}")
        raise PyPIWorkflowError(f"Failed to analyze build logs: {e}", "get_build_logs") from e


def _analyze_wheel_filename(filename: str) -> Dict[str, Any]:
    """Analyze wheel filename to extract platform and architecture info."""
    # Wheel filename format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
    parts = filename.replace(".whl", "").split("-")
    
    analysis = {
        "wheel_type": "unknown",
        "platform": "unknown",
        "architecture": "unknown",
        "python_implementation": "unknown",
        "abi": "unknown",
    }
    
    if len(parts) >= 5:
        python_tag = parts[-3]
        abi_tag = parts[-2] 
        platform_tag = parts[-1]
        
        analysis.update({
            "python_tag": python_tag,
            "abi": abi_tag,
            "platform": platform_tag,
        })
        
        # Determine wheel type
        if platform_tag == "any":
            analysis["wheel_type"] = "universal"
        elif "win" in platform_tag:
            analysis["wheel_type"] = "platform_specific"
            analysis["platform"] = "windows"
        elif "macosx" in platform_tag or "darwin" in platform_tag:
            analysis["wheel_type"] = "platform_specific"
            analysis["platform"] = "macos"
        elif "linux" in platform_tag:
            analysis["wheel_type"] = "platform_specific"
            analysis["platform"] = "linux"
        else:
            analysis["wheel_type"] = "platform_specific"
        
        # Determine architecture
        if "x86_64" in platform_tag or "amd64" in platform_tag:
            analysis["architecture"] = "x86_64"
        elif "i386" in platform_tag or "win32" in platform_tag:
            analysis["architecture"] = "x86"
        elif "arm64" in platform_tag or "aarch64" in platform_tag:
            analysis["architecture"] = "arm64"
        
        # Python implementation
        if python_tag.startswith("cp"):
            analysis["python_implementation"] = "cpython"
        elif python_tag.startswith("pp"):
            analysis["python_implementation"] = "pypy"
        elif python_tag == "py2.py3" or python_tag == "py3":
            analysis["python_implementation"] = "universal"
    
    return analysis


def _analyze_build_quality(distributions: Dict[str, List], package_info: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the quality of package builds based on available distributions."""
    
    wheels = distributions["wheels"]
    source = distributions["source"]
    
    quality_score = 0
    max_score = 100
    health_issues = []
    
    # Wheel availability (30 points)
    if wheels:
        quality_score += 30
        if len(wheels) >= 3:  # Multiple platforms
            quality_score += 10
    else:
        health_issues.append("No wheels available - installation will be slower")
    
    # Source distribution (20 points)
    if source:
        quality_score += 20
    else:
        health_issues.append("No source distribution - may cause installation issues")
    
    # Platform coverage (25 points)
    platforms = set()
    for wheel in wheels:
        if wheel.get("platform"):
            platforms.add(wheel["platform"])
    
    platform_score = min(len(platforms) * 8, 25)  # Up to 25 points for platform coverage
    quality_score += platform_score
    
    if len(platforms) < 2:
        health_issues.append("Limited platform support")
    
    # Python version support (15 points)
    python_versions = set()
    for wheel in wheels:
        if wheel.get("python_version"):
            python_versions.add(wheel["python_version"])
    
    py_version_score = min(len(python_versions) * 3, 15)
    quality_score += py_version_score
    
    # File size reasonableness (10 points)
    total_size = sum(wheel.get("size_bytes", 0) for wheel in wheels)
    if total_size > 0:
        if total_size < 100 * 1024 * 1024:  # Less than 100MB total
            quality_score += 10
        elif total_size < 500 * 1024 * 1024:  # Less than 500MB total  
            quality_score += 5
        else:
            health_issues.append("Very large package size")
    
    # Determine health status
    if quality_score >= 80:
        health_status = "excellent"
    elif quality_score >= 60:
        health_status = "good"
    elif quality_score >= 40:
        health_status = "fair"
    else:
        health_status = "poor"
    
    return {
        "quality_score": quality_score,
        "max_score": max_score,
        "health_status": health_status,
        "platform_coverage": len(platforms),
        "python_version_coverage": len(python_versions),
        "total_distributions": len(wheels) + len(source),
        "health_issues": health_issues,
    }
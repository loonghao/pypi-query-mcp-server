"""Requirements file analysis tools for Python projects."""

import logging
from typing import Any, Dict, List

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..tools.requirements_analyzer import analyze_project_requirements, compare_requirements_files

logger = logging.getLogger(__name__)


async def analyze_requirements_file_tool(
    file_path: str,
    check_updates: bool = True,
    security_scan: bool = True,
    compatibility_check: bool = True
) -> Dict[str, Any]:
    """
    Analyze project requirements file for dependencies, security, and compatibility.
    
    This tool provides comprehensive analysis of Python project requirements files
    including dependency parsing, version checking, security vulnerability scanning,
    Python compatibility assessment, and actionable recommendations for improvements.
    
    Args:
        file_path: Path to the requirements file (requirements.txt, pyproject.toml, setup.py, etc.)
        check_updates: Whether to check for available package updates
        security_scan: Whether to perform security vulnerability scanning on dependencies
        compatibility_check: Whether to check Python version compatibility for all dependencies
        
    Returns:
        Dictionary containing comprehensive requirements analysis including:
        - File information and detected format (requirements.txt, pyproject.toml, etc.)
        - Parsed dependencies with version specifiers and extras
        - Dependency health analysis with specification issues and recommendations
        - Package update analysis showing outdated packages and latest versions
        - Security vulnerability scan results for all dependencies
        - Python version compatibility assessment
        - Overall risk level and actionable improvement recommendations
        
    Raises:
        FileNotFoundError: If the requirements file is not found
        NetworkError: For network-related errors during analysis
        SearchError: If requirements analysis fails
    """
    logger.info(f"MCP tool: Analyzing requirements file {file_path}")
    
    try:
        result = await analyze_project_requirements(
            file_path=file_path,
            check_updates=check_updates,
            security_scan=security_scan,
            compatibility_check=compatibility_check
        )
        
        summary = result.get("analysis_summary", {})
        total_deps = summary.get("total_dependencies", 0)
        risk_level = summary.get("overall_risk_level", "unknown")
        logger.info(f"MCP tool: Requirements analysis completed for {file_path} - {total_deps} dependencies, risk level: {risk_level}")
        return result
        
    except (FileNotFoundError, NetworkError, SearchError) as e:
        logger.error(f"Error analyzing requirements file {file_path}: {e}")
        return {
            "error": f"Requirements analysis failed: {e}",
            "error_type": type(e).__name__,
            "file_path": file_path,
            "analysis_timestamp": "",
            "file_info": {"name": file_path, "format": "unknown"},
            "dependencies": [],
            "dependency_analysis": {},
            "analysis_summary": {
                "total_dependencies": 0,
                "health_score": 0,
                "packages_with_issues": 0,
                "outdated_packages": 0,
                "security_vulnerabilities": 0,
                "compatibility_issues": 0,
                "overall_risk_level": "critical",
            },
            "recommendations": [f"❌ Requirements analysis failed: {e}"],
            "python_requirements": None,
        }


async def compare_multiple_requirements_files(
    file_paths: List[str]
) -> Dict[str, Any]:
    """
    Compare multiple requirements files to identify differences and conflicts.
    
    This tool analyzes multiple requirements files simultaneously to identify
    version conflicts, unique dependencies, and inconsistencies across different
    project configurations or environments.
    
    Args:
        file_paths: List of paths to requirements files to compare and analyze
        
    Returns:
        Dictionary containing comparative requirements analysis including:
        - Detailed analysis results for each individual file
        - Common packages shared across all files
        - Conflicting package versions between files with specific version details
        - Packages unique to specific files
        - Recommendations for resolving conflicts and standardizing requirements
        - Statistics on package overlap and conflict rates
        
    Raises:
        ValueError: If file_paths list is empty
        NetworkError: For network-related errors during analysis
        SearchError: If requirements comparison fails
    """
    if not file_paths:
        raise ValueError("File paths list cannot be empty")
        
    logger.info(f"MCP tool: Comparing {len(file_paths)} requirements files")
    
    try:
        result = await compare_requirements_files(file_paths=file_paths)
        
        comparison_results = result.get("comparison_results", {})
        conflicts = len(comparison_results.get("conflicting_packages", []))
        total_packages = comparison_results.get("total_unique_packages", 0)
        
        logger.info(f"MCP tool: Requirements comparison completed - {total_packages} unique packages, {conflicts} conflicts found")
        return result
        
    except (ValueError, NetworkError, SearchError) as e:
        logger.error(f"Error comparing requirements files: {e}")
        return {
            "error": f"Requirements comparison failed: {e}",
            "error_type": type(e).__name__,
            "comparison_timestamp": "",
            "files_compared": len(file_paths),
            "file_analyses": {},
            "comparison_results": {
                "total_unique_packages": 0,
                "common_packages": [],
                "conflicting_packages": [],
                "unique_to_files": {},
            },
            "recommendations": [f"❌ Requirements comparison failed: {e}"]
        }
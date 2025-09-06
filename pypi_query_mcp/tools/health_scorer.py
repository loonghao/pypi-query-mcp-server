"""Package health scoring and quality assessment tools for PyPI packages."""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..core.pypi_client import PyPIClient

logger = logging.getLogger(__name__)


class PackageHealthScorer:
    """Comprehensive health and quality scorer for PyPI packages."""

    def __init__(self):
        self.timeout = 30.0
        
        # Health scoring weights (total = 100)
        self.weights = {
            "maintenance": 25,     # Maintenance indicators
            "popularity": 20,      # Download stats, stars, usage
            "documentation": 15,   # Documentation quality
            "testing": 15,         # Testing and CI indicators
            "security": 10,        # Security practices
            "compatibility": 10,   # Python version support
            "metadata": 5,         # Metadata completeness
        }
        
        # Quality metrics thresholds
        self.thresholds = {
            "downloads_monthly_excellent": 1000000,
            "downloads_monthly_good": 100000,
            "downloads_monthly_fair": 10000,
            "version_age_days_fresh": 90,
            "version_age_days_good": 365,
            "version_age_days_stale": 730,
            "python_versions_excellent": 4,
            "python_versions_good": 3,
            "python_versions_fair": 2,
        }

    async def assess_package_health(
        self, 
        package_name: str,
        version: Optional[str] = None,
        include_github_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Assess comprehensive health and quality of a PyPI package.
        
        Args:
            package_name: Name of the package to assess
            version: Specific version to assess (optional)
            include_github_metrics: Whether to fetch GitHub repository metrics
            
        Returns:
            Dictionary containing health assessment results
        """
        logger.info(f"Starting health assessment for package: {package_name}")
        
        try:
            async with PyPIClient() as client:
                package_data = await client.get_package_info(package_name, version)
                
            package_version = version or package_data["info"]["version"]
            
            # Run parallel health assessments
            assessment_tasks = [
                self._assess_maintenance_health(package_data),
                self._assess_popularity_metrics(package_data),
                self._assess_documentation_quality(package_data),
                self._assess_testing_indicators(package_data),
                self._assess_security_practices(package_data),
                self._assess_compatibility_support(package_data),
                self._assess_metadata_completeness(package_data),
            ]
            
            if include_github_metrics:
                github_url = self._extract_github_url(package_data)
                if github_url:
                    assessment_tasks.append(self._fetch_github_metrics(github_url))
                else:
                    assessment_tasks.append(asyncio.create_task(self._empty_github_metrics()))
            else:
                assessment_tasks.append(asyncio.create_task(self._empty_github_metrics()))
            
            results = await asyncio.gather(*assessment_tasks, return_exceptions=True)
            
            # Unpack results
            (maintenance, popularity, documentation, testing, 
             security, compatibility, metadata, github_metrics) = results
            
            # Handle exceptions
            if isinstance(github_metrics, Exception):
                github_metrics = self._empty_github_metrics()
            
            # Calculate overall health score
            health_scores = {
                "maintenance": maintenance.get("score", 0) if not isinstance(maintenance, Exception) else 0,
                "popularity": popularity.get("score", 0) if not isinstance(popularity, Exception) else 0,
                "documentation": documentation.get("score", 0) if not isinstance(documentation, Exception) else 0,
                "testing": testing.get("score", 0) if not isinstance(testing, Exception) else 0,
                "security": security.get("score", 0) if not isinstance(security, Exception) else 0,
                "compatibility": compatibility.get("score", 0) if not isinstance(compatibility, Exception) else 0,
                "metadata": metadata.get("score", 0) if not isinstance(metadata, Exception) else 0,
            }
            
            overall_score = sum(
                health_scores[category] * (self.weights[category] / 100)
                for category in health_scores
            )
            
            health_level = self._calculate_health_level(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_health_recommendations(
                health_scores, maintenance, popularity, documentation, 
                testing, security, compatibility, metadata, github_metrics
            )
            
            return {
                "package": package_name,
                "version": package_version,
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_health": {
                    "score": round(overall_score, 2),
                    "level": health_level,
                    "max_score": 100,
                },
                "category_scores": health_scores,
                "detailed_assessment": {
                    "maintenance": maintenance if not isinstance(maintenance, Exception) else {"score": 0, "indicators": [], "issues": [str(maintenance)]},
                    "popularity": popularity if not isinstance(popularity, Exception) else {"score": 0, "metrics": {}, "issues": [str(popularity)]},
                    "documentation": documentation if not isinstance(documentation, Exception) else {"score": 0, "indicators": [], "issues": [str(documentation)]},
                    "testing": testing if not isinstance(testing, Exception) else {"score": 0, "indicators": [], "issues": [str(testing)]},
                    "security": security if not isinstance(security, Exception) else {"score": 0, "practices": [], "issues": [str(security)]},
                    "compatibility": compatibility if not isinstance(compatibility, Exception) else {"score": 0, "support": [], "issues": [str(compatibility)]},
                    "metadata": metadata if not isinstance(metadata, Exception) else {"score": 0, "completeness": {}, "issues": [str(metadata)]},
                    "github_metrics": github_metrics,
                },
                "recommendations": recommendations,
                "health_summary": {
                    "strengths": self._identify_strengths(health_scores),
                    "weaknesses": self._identify_weaknesses(health_scores),
                    "improvement_priority": self._prioritize_improvements(health_scores),
                }
            }
            
        except Exception as e:
            logger.error(f"Health assessment failed for {package_name}: {e}")
            raise SearchError(f"Health assessment failed: {e}") from e

    async def _assess_maintenance_health(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess package maintenance health indicators."""
        info = package_data.get("info", {})
        releases = package_data.get("releases", {})
        
        score = 0
        indicators = []
        issues = []
        
        # Check release frequency
        if releases:
            release_dates = []
            for version_releases in releases.values():
                for release in version_releases:
                    upload_time = release.get("upload_time_iso_8601")
                    if upload_time:
                        try:
                            release_dates.append(datetime.fromisoformat(upload_time.replace('Z', '+00:00')))
                        except:
                            pass
            
            if release_dates:
                release_dates.sort(reverse=True)
                latest_release = release_dates[0]
                days_since_release = (datetime.now(timezone.utc) - latest_release).days
                
                if days_since_release <= self.thresholds["version_age_days_fresh"]:
                    score += 25
                    indicators.append(f"Recent release ({days_since_release} days ago)")
                elif days_since_release <= self.thresholds["version_age_days_good"]:
                    score += 20
                    indicators.append(f"Moderately recent release ({days_since_release} days ago)")
                elif days_since_release <= self.thresholds["version_age_days_stale"]:
                    score += 10
                    indicators.append(f"Older release ({days_since_release} days ago)")
                else:
                    issues.append(f"Very old release ({days_since_release} days ago)")
                
                # Check release consistency (last 5 releases)
                if len(release_dates) >= 5:
                    recent_releases = release_dates[:5]
                    intervals = []
                    for i in range(len(recent_releases) - 1):
                        interval = (recent_releases[i] - recent_releases[i + 1]).days
                        intervals.append(interval)
                    
                    avg_interval = sum(intervals) / len(intervals)
                    if avg_interval <= 180:  # Releases every 6 months or less
                        score += 15
                        indicators.append(f"Regular releases (avg {avg_interval:.0f} days)")
                    elif avg_interval <= 365:
                        score += 10
                        indicators.append(f"Periodic releases (avg {avg_interval:.0f} days)")
                    else:
                        issues.append(f"Infrequent releases (avg {avg_interval:.0f} days)")
        else:
            issues.append("No release history available")
        
        # Check for development indicators
        if "dev" in info.get("version", "").lower() or "alpha" in info.get("version", "").lower():
            issues.append("Development/alpha version")
        elif "beta" in info.get("version", "").lower():
            score += 5
            indicators.append("Beta version (active development)")
        else:
            score += 10
            indicators.append("Stable version")
        
        # Check for author/maintainer info
        if info.get("author") or info.get("maintainer"):
            score += 10
            indicators.append("Active maintainer information")
        else:
            issues.append("No maintainer information")
        
        return {
            "score": min(score, 100),
            "indicators": indicators,
            "issues": issues,
            "metrics": {
                "days_since_last_release": days_since_release if 'days_since_release' in locals() else None,
                "total_releases": len(releases),
            }
        }

    async def _assess_popularity_metrics(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess package popularity and usage metrics."""
        info = package_data.get("info", {})
        
        score = 0
        metrics = {}
        
        # Estimate download popularity (since we don't have direct access)
        # Use proxy indicators: project URLs, description length, classifiers
        
        # Check for GitHub stars indicator
        project_urls = info.get("project_urls", {}) or {}
        github_url = None
        for key, url in project_urls.items():
            if "github.com" in (url or "").lower():
                github_url = url
                break
        
        if not github_url:
            home_page = info.get("home_page", "")
            if "github.com" in home_page:
                github_url = home_page
        
        if github_url:
            score += 15
            metrics["has_github_repo"] = True
        else:
            metrics["has_github_repo"] = False
        
        # Check description quality as popularity indicator
        description = info.get("description", "") or ""
        summary = info.get("summary", "") or ""
        
        if len(description) > 1000:
            score += 20
            metrics["description_quality"] = "excellent"
        elif len(description) > 500:
            score += 15
            metrics["description_quality"] = "good"
        elif len(description) > 100:
            score += 10
            metrics["description_quality"] = "fair"
        else:
            metrics["description_quality"] = "poor"
        
        # Check for comprehensive metadata (popularity indicator)
        if info.get("keywords"):
            score += 10
        if len(info.get("classifiers", [])) > 5:
            score += 15
        if info.get("project_urls") and len(info.get("project_urls", {})) > 2:
            score += 10
        
        # Check for documentation links
        docs_indicators = ["documentation", "docs", "readthedocs", "github.io"]
        has_docs = any(
            any(indicator in (url or "").lower() for indicator in docs_indicators)
            for url in project_urls.values()
        )
        if has_docs:
            score += 15
            metrics["has_documentation"] = True
        else:
            metrics["has_documentation"] = False
        
        # Check for community indicators
        community_urls = ["issues", "bug", "tracker", "discussion", "forum"]
        has_community = any(
            any(indicator in key.lower() for indicator in community_urls)
            for key in project_urls.keys()
        )
        if has_community:
            score += 15
            metrics["has_community_links"] = True
        else:
            metrics["has_community_links"] = False
        
        return {
            "score": min(score, 100),
            "metrics": metrics,
        }

    async def _assess_documentation_quality(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess documentation quality indicators."""
        info = package_data.get("info", {})
        
        score = 0
        indicators = []
        issues = []
        
        # Check description completeness
        description = info.get("description", "") or ""
        summary = info.get("summary", "") or ""
        
        if len(description) > 2000:
            score += 30
            indicators.append("Comprehensive description")
        elif len(description) > 1000:
            score += 25
            indicators.append("Good description length")
        elif len(description) > 500:
            score += 15
            indicators.append("Adequate description")
        elif len(description) > 100:
            score += 10
            indicators.append("Basic description")
        else:
            issues.append("Very short or missing description")
        
        # Check for README indicators in description
        readme_indicators = ["## ", "### ", "```", "# Installation", "# Usage", "# Examples"]
        if any(indicator in description for indicator in readme_indicators):
            score += 20
            indicators.append("Structured documentation (README-style)")
        
        # Check for documentation URLs
        project_urls = info.get("project_urls", {}) or {}
        docs_urls = []
        for key, url in project_urls.items():
            if any(term in key.lower() for term in ["doc", "guide", "manual", "wiki"]):
                docs_urls.append(url)
        
        if docs_urls:
            score += 25
            indicators.append(f"Documentation links ({len(docs_urls)} found)")
        else:
            issues.append("No dedicated documentation links")
        
        # Check for example code in description
        if "```" in description or "    " in description:  # Code blocks
            score += 15
            indicators.append("Contains code examples")
        
        # Check for installation instructions
        install_keywords = ["install", "pip install", "setup.py", "requirements"]
        if any(keyword in description.lower() for keyword in install_keywords):
            score += 10
            indicators.append("Installation instructions provided")
        else:
            issues.append("No clear installation instructions")
        
        return {
            "score": min(score, 100),
            "indicators": indicators,
            "issues": issues,
        }

    async def _assess_testing_indicators(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess testing and CI/CD indicators."""
        info = package_data.get("info", {})
        
        score = 0
        indicators = []
        issues = []
        
        # Check for testing-related classifiers
        classifiers = info.get("classifiers", [])
        testing_classifiers = [c for c in classifiers if "testing" in c.lower()]
        if testing_classifiers:
            score += 15
            indicators.append("Testing framework classifiers")
        
        # Check for CI/CD indicators in URLs
        project_urls = info.get("project_urls", {}) or {}
        ci_indicators = ["travis", "circleci", "appveyor", "azure", "github", "actions", "ci", "build"]
        ci_urls = []
        for key, url in project_urls.items():
            if any(indicator in key.lower() or indicator in (url or "").lower() for indicator in ci_indicators):
                ci_urls.append(key)
        
        if ci_urls:
            score += 25
            indicators.append(f"CI/CD indicators ({len(ci_urls)} found)")
        
        # Check description for testing mentions
        description = (info.get("description", "") or "").lower()
        testing_keywords = ["test", "pytest", "unittest", "nose", "coverage", "tox", "ci/cd", "continuous integration"]
        testing_mentions = [kw for kw in testing_keywords if kw in description]
        
        if testing_mentions:
            score += 20
            indicators.append(f"Testing framework mentions ({len(testing_mentions)} found)")
        else:
            issues.append("No testing framework mentions")
        
        # Check for test dependencies (common patterns)
        requires_dist = info.get("requires_dist", []) or []
        test_deps = []
        for req in requires_dist:
            req_lower = req.lower()
            if any(test_pkg in req_lower for test_pkg in ["pytest", "unittest", "nose", "coverage", "tox", "test"]):
                test_deps.append(req.split()[0])
        
        if test_deps:
            score += 20
            indicators.append(f"Test dependencies ({len(test_deps)} found)")
        else:
            issues.append("No test dependencies found")
        
        # Check for badges (often indicate CI/testing)
        badge_indicators = ["[![", "https://img.shields.io", "badge", "build status", "coverage"]
        if any(indicator in description for indicator in badge_indicators):
            score += 20
            indicators.append("Status badges (likely CI integration)")
        
        return {
            "score": min(score, 100),
            "indicators": indicators,
            "issues": issues,
        }

    async def _assess_security_practices(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security practices and indicators."""
        info = package_data.get("info", {})
        
        score = 0
        practices = []
        issues = []
        
        # Check for security-related URLs
        project_urls = info.get("project_urls", {}) or {}
        security_urls = []
        for key, url in project_urls.items():
            if any(term in key.lower() for term in ["security", "vulnerability", "report", "bug"]):
                security_urls.append(key)
        
        if security_urls:
            score += 25
            practices.append(f"Security reporting channels ({len(security_urls)} found)")
        else:
            issues.append("No security reporting channels")
        
        # Check for HTTPS URLs
        https_urls = [url for url in project_urls.values() if (url or "").startswith("https://")]
        if len(https_urls) == len([url for url in project_urls.values() if url]):
            score += 15
            practices.append("All URLs use HTTPS")
        elif https_urls:
            score += 10
            practices.append("Some URLs use HTTPS")
        else:
            issues.append("No HTTPS URLs found")
        
        # Check for security mentions in description
        description = (info.get("description", "") or "").lower()
        security_keywords = ["security", "secure", "vulnerability", "encryption", "authentication", "authorization"]
        security_mentions = [kw for kw in security_keywords if kw in description]
        
        if security_mentions:
            score += 20
            practices.append(f"Security awareness ({len(security_mentions)} mentions)")
        
        # Check for license (security practice)
        if info.get("license") or any("license" in c.lower() for c in info.get("classifiers", [])):
            score += 15
            practices.append("Clear license information")
        else:
            issues.append("No clear license information")
        
        # Check for author/maintainer email (security contact)
        if info.get("author_email") or info.get("maintainer_email"):
            score += 10
            practices.append("Maintainer contact information")
        else:
            issues.append("No maintainer contact information")
        
        # Check for requirements specification (dependency security)
        requires_dist = info.get("requires_dist", [])
        if requires_dist:
            # Check for version pinning (security practice)
            pinned_deps = [req for req in requires_dist if any(op in req for op in ["==", ">=", "~="])]
            if pinned_deps:
                score += 15
                practices.append(f"Version-pinned dependencies ({len(pinned_deps)}/{len(requires_dist)})")
            else:
                issues.append("No version-pinned dependencies")
        
        return {
            "score": min(score, 100),
            "practices": practices,
            "issues": issues,
        }

    async def _assess_compatibility_support(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess Python version and platform compatibility."""
        info = package_data.get("info", {})
        
        score = 0
        support = []
        issues = []
        
        # Check Python version support from classifiers
        classifiers = info.get("classifiers", [])
        python_versions = []
        for classifier in classifiers:
            if "Programming Language :: Python ::" in classifier:
                version_part = classifier.split("::")[-1].strip()
                if re.match(r'^\d+\.\d+$', version_part):  # Like "3.8", "3.9"
                    python_versions.append(version_part)
        
        if len(python_versions) >= self.thresholds["python_versions_excellent"]:
            score += 30
            support.append(f"Excellent Python version support ({len(python_versions)} versions)")
        elif len(python_versions) >= self.thresholds["python_versions_good"]:
            score += 25
            support.append(f"Good Python version support ({len(python_versions)} versions)")
        elif len(python_versions) >= self.thresholds["python_versions_fair"]:
            score += 15
            support.append(f"Fair Python version support ({len(python_versions)} versions)")
        elif python_versions:
            score += 10
            support.append(f"Limited Python version support ({len(python_versions)} versions)")
        else:
            issues.append("No explicit Python version support")
        
        # Check requires_python specification
        requires_python = info.get("requires_python")
        if requires_python:
            score += 20
            support.append(f"Python requirement specified: {requires_python}")
        else:
            issues.append("No Python version requirement specified")
        
        # Check platform support
        platform_classifiers = [c for c in classifiers if "Operating System" in c]
        if platform_classifiers:
            if any("OS Independent" in c for c in platform_classifiers):
                score += 20
                support.append("Cross-platform support (OS Independent)")
            else:
                score += 15
                support.append(f"Platform support ({len(platform_classifiers)} platforms)")
        else:
            issues.append("No platform support information")
        
        # Check for wheel distribution (compatibility indicator)
        urls = info.get("urls", []) or []
        has_wheel = any(url.get("packagetype") == "bdist_wheel" for url in urls)
        if has_wheel:
            score += 15
            support.append("Wheel distribution available")
        else:
            issues.append("No wheel distribution")
        
        # Check development status
        status_classifiers = [c for c in classifiers if "Development Status" in c]
        if status_classifiers:
            status = status_classifiers[0]
            if "5 - Production/Stable" in status:
                score += 15
                support.append("Production/Stable status")
            elif "4 - Beta" in status:
                score += 10
                support.append("Beta status")
            elif "3 - Alpha" in status:
                score += 5
                support.append("Alpha status")
            else:
                issues.append(f"Early development status: {status}")
        
        return {
            "score": min(score, 100),
            "support": support,
            "issues": issues,
            "python_versions": python_versions,
        }

    async def _assess_metadata_completeness(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess metadata completeness and quality."""
        info = package_data.get("info", {})
        
        score = 0
        completeness = {}
        
        # Essential fields
        essential_fields = ["name", "version", "summary", "description", "author", "license"]
        present_essential = [field for field in essential_fields if info.get(field)]
        score += (len(present_essential) / len(essential_fields)) * 40
        completeness["essential_fields"] = f"{len(present_essential)}/{len(essential_fields)}"
        
        # Additional metadata fields
        additional_fields = ["keywords", "home_page", "author_email", "classifiers", "project_urls"]
        present_additional = [field for field in additional_fields if info.get(field)]
        score += (len(present_additional) / len(additional_fields)) * 30
        completeness["additional_fields"] = f"{len(present_additional)}/{len(additional_fields)}"
        
        # Classifier completeness
        classifiers = info.get("classifiers", [])
        classifier_categories = set()
        for classifier in classifiers:
            category = classifier.split("::")[0].strip()
            classifier_categories.add(category)
        
        expected_categories = ["Development Status", "Intended Audience", "License", "Programming Language", "Topic"]
        present_categories = [cat for cat in expected_categories if cat in classifier_categories]
        score += (len(present_categories) / len(expected_categories)) * 20
        completeness["classifier_categories"] = f"{len(present_categories)}/{len(expected_categories)}"
        
        # URLs completeness
        project_urls = info.get("project_urls", {}) or {}
        expected_url_types = ["homepage", "repository", "documentation", "bug tracker"]
        present_url_types = []
        for expected in expected_url_types:
            if any(expected.lower() in key.lower() for key in project_urls.keys()):
                present_url_types.append(expected)
        
        score += (len(present_url_types) / len(expected_url_types)) * 10
        completeness["url_types"] = f"{len(present_url_types)}/{len(expected_url_types)}"
        
        return {
            "score": min(score, 100),
            "completeness": completeness,
        }

    def _extract_github_url(self, package_data: Dict[str, Any]) -> Optional[str]:
        """Extract GitHub repository URL from package data."""
        info = package_data.get("info", {})
        
        # Check project URLs
        project_urls = info.get("project_urls", {}) or {}
        for url in project_urls.values():
            if url and "github.com" in url:
                return url
        
        # Check home page
        home_page = info.get("home_page", "")
        if home_page and "github.com" in home_page:
            return home_page
        
        return None

    async def _fetch_github_metrics(self, github_url: str) -> Dict[str, Any]:
        """Fetch GitHub repository metrics."""
        try:
            # Parse GitHub URL to get owner/repo
            parsed = urlparse(github_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                
                # GitHub API call (public API, no auth required for basic info)
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(
                        api_url,
                        headers={
                            "Accept": "application/vnd.github.v3+json",
                            "User-Agent": "PyPI-Health-Scorer/1.0"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "stars": data.get("stargazers_count", 0),
                            "forks": data.get("forks_count", 0),
                            "watchers": data.get("watchers_count", 0),
                            "issues": data.get("open_issues_count", 0),
                            "has_wiki": data.get("has_wiki", False),
                            "has_pages": data.get("has_pages", False),
                            "language": data.get("language", ""),
                            "created_at": data.get("created_at", ""),
                            "updated_at": data.get("pushed_at", ""),
                            "default_branch": data.get("default_branch", ""),
                            "archived": data.get("archived", False),
                            "disabled": data.get("disabled", False),
                        }
                    else:
                        logger.warning(f"GitHub API returned status {response.status_code}")
                        
        except Exception as e:
            logger.debug(f"Failed to fetch GitHub metrics: {e}")
            
        return self._empty_github_metrics()

    async def _empty_github_metrics(self) -> Dict[str, Any]:
        """Return empty GitHub metrics."""
        return {
            "stars": 0,
            "forks": 0,
            "watchers": 0,
            "issues": 0,
            "has_wiki": False,
            "has_pages": False,
            "language": "",
            "created_at": "",
            "updated_at": "",
            "default_branch": "",
            "archived": False,
            "disabled": False,
            "available": False,
        }

    def _calculate_health_level(self, score: float) -> str:
        """Calculate health level from score."""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"

    def _identify_strengths(self, health_scores: Dict[str, float]) -> List[str]:
        """Identify package strengths."""
        strengths = []
        for category, score in health_scores.items():
            if score >= 80:
                strengths.append(f"Excellent {category} ({score:.0f}/100)")
            elif score >= 65:
                strengths.append(f"Good {category} ({score:.0f}/100)")
        return strengths

    def _identify_weaknesses(self, health_scores: Dict[str, float]) -> List[str]:
        """Identify package weaknesses."""
        weaknesses = []
        for category, score in health_scores.items():
            if score < 40:
                weaknesses.append(f"Poor {category} ({score:.0f}/100)")
            elif score < 55:
                weaknesses.append(f"Fair {category} ({score:.0f}/100)")
        return weaknesses

    def _prioritize_improvements(self, health_scores: Dict[str, float]) -> List[str]:
        """Prioritize improvement areas by weight and score."""
        weighted_gaps = []
        for category, score in health_scores.items():
            gap = 100 - score
            weighted_gap = gap * (self.weights[category] / 100)
            weighted_gaps.append((category, weighted_gap, score))
        
        # Sort by weighted gap (highest impact first)
        weighted_gaps.sort(key=lambda x: x[1], reverse=True)
        
        priorities = []
        for category, weighted_gap, score in weighted_gaps[:3]:  # Top 3
            if weighted_gap > 5:  # Only include significant gaps
                priorities.append(f"Improve {category} (current: {score:.0f}/100, impact: {self.weights[category]}%)")
        
        return priorities

    def _generate_health_recommendations(
        self, health_scores: Dict[str, float], *assessment_results
    ) -> List[str]:
        """Generate actionable health improvement recommendations."""
        recommendations = []
        
        overall_score = sum(
            health_scores[category] * (self.weights[category] / 100)
            for category in health_scores
        )
        
        # Overall recommendations
        if overall_score >= 85:
            recommendations.append("🌟 Excellent package health - maintain current standards")
        elif overall_score >= 70:
            recommendations.append("✅ Good package health - minor improvements possible")
        elif overall_score >= 55:
            recommendations.append("⚠️  Fair package health - several areas need improvement")
        elif overall_score >= 40:
            recommendations.append("🔶 Poor package health - significant improvements needed")
        else:
            recommendations.append("🚨 Critical package health - major overhaul required")
        
        # Specific recommendations based on low scores
        if health_scores.get("maintenance", 0) < 60:
            recommendations.append("📅 Improve maintenance: Update package more regularly, provide clear version history")
        
        if health_scores.get("documentation", 0) < 60:
            recommendations.append("📚 Improve documentation: Add comprehensive README, usage examples, and API docs")
        
        if health_scores.get("testing", 0) < 60:
            recommendations.append("🧪 Add testing: Implement test suite, CI/CD pipeline, and code coverage")
        
        if health_scores.get("security", 0) < 60:
            recommendations.append("🔒 Enhance security: Add security reporting, use HTTPS, specify dependencies properly")
        
        if health_scores.get("compatibility", 0) < 60:
            recommendations.append("🔧 Improve compatibility: Support more Python versions, add wheel distribution")
        
        if health_scores.get("metadata", 0) < 60:
            recommendations.append("📝 Complete metadata: Add missing package information, keywords, and classifiers")
        
        if health_scores.get("popularity", 0) < 60:
            recommendations.append("📈 Build community: Create documentation site, engage with users, add project URLs")
        
        return recommendations


# Main health assessment functions
async def assess_pypi_package_health(
    package_name: str,
    version: Optional[str] = None,
    include_github_metrics: bool = True
) -> Dict[str, Any]:
    """
    Assess comprehensive health and quality of a PyPI package.
    
    Args:
        package_name: Name of the package to assess
        version: Specific version to assess (optional)
        include_github_metrics: Whether to fetch GitHub repository metrics
        
    Returns:
        Comprehensive health assessment including scores and recommendations
    """
    scorer = PackageHealthScorer()
    return await scorer.assess_package_health(
        package_name, version, include_github_metrics
    )


async def compare_package_health(
    package_names: List[str],
    include_github_metrics: bool = False
) -> Dict[str, Any]:
    """
    Compare health scores across multiple packages.
    
    Args:
        package_names: List of package names to compare
        include_github_metrics: Whether to include GitHub metrics
        
    Returns:
        Comparative health analysis with rankings
    """
    logger.info(f"Starting health comparison for {len(package_names)} packages")
    
    scorer = PackageHealthScorer()
    results = {}
    
    # Assess packages in parallel batches
    batch_size = 3
    for i in range(0, len(package_names), batch_size):
        batch = package_names[i:i + batch_size]
        batch_tasks = [
            scorer.assess_package_health(pkg_name, include_github_metrics=include_github_metrics)
            for pkg_name in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for pkg_name, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                results[pkg_name] = {
                    "error": str(result),
                    "overall_health": {"score": 0, "level": "critical"},
                    "category_scores": {cat: 0 for cat in scorer.weights.keys()}
                }
            else:
                results[pkg_name] = result
    
    # Create comparison rankings
    package_scores = [
        (pkg, result.get("overall_health", {}).get("score", 0))
        for pkg, result in results.items()
        if "error" not in result
    ]
    package_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Generate comparison insights
    if package_scores:
        best_package, best_score = package_scores[0]
        worst_package, worst_score = package_scores[-1]
        avg_score = sum(score for _, score in package_scores) / len(package_scores)
        
        comparison_insights = {
            "best_package": {"name": best_package, "score": best_score},
            "worst_package": {"name": worst_package, "score": worst_score},
            "average_score": round(avg_score, 2),
            "score_range": best_score - worst_score,
            "rankings": [{"package": pkg, "score": score, "rank": i+1} 
                        for i, (pkg, score) in enumerate(package_scores)]
        }
    else:
        comparison_insights = {
            "best_package": None,
            "worst_package": None,
            "average_score": 0,
            "score_range": 0,
            "rankings": []
        }
    
    return {
        "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
        "packages_compared": len(package_names),
        "detailed_results": results,
        "comparison_insights": comparison_insights,
        "recommendations": _generate_comparison_recommendations(comparison_insights, results)
    }


def _generate_comparison_recommendations(
    insights: Dict[str, Any], results: Dict[str, Any]
) -> List[str]:
    """Generate recommendations for package comparison."""
    recommendations = []
    
    if not insights.get("rankings"):
        recommendations.append("❌ No successful health assessments to compare")
        return recommendations
    
    best = insights.get("best_package")
    worst = insights.get("worst_package")
    avg_score = insights.get("average_score", 0)
    
    if best and worst:
        recommendations.append(
            f"🥇 Best package: {best['name']} (score: {best['score']:.1f}/100)"
        )
        recommendations.append(
            f"🥉 Needs improvement: {worst['name']} (score: {worst['score']:.1f}/100)"
        )
        
        if best['score'] - worst['score'] > 30:
            recommendations.append("📊 Significant quality variation - consider standardizing practices")
        
        recommendations.append(f"📈 Average health score: {avg_score:.1f}/100")
        
        if avg_score >= 70:
            recommendations.append("✅ Overall good package health across portfolio")
        elif avg_score >= 55:
            recommendations.append("⚠️  Mixed package health - focus on improving lower-scoring packages")
        else:
            recommendations.append("🚨 Poor overall package health - systematic improvements needed")
    
    return recommendations
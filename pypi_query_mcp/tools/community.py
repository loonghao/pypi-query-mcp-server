"""PyPI Community & Social Tools for package community interactions and maintainer communication."""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, urljoin, urlparse

import httpx

from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
    PyPIError,
)
from ..core.pypi_client import PyPIClient
from ..core.github_client import GitHubClient

logger = logging.getLogger(__name__)


async def get_pypi_package_reviews(
    package_name: str,
    include_ratings: bool = True,
    include_community_feedback: bool = True,
    sentiment_analysis: bool = False,
    max_reviews: int = 50,
) -> Dict[str, Any]:
    """
    Get community reviews and feedback for a PyPI package.
    
    This function aggregates community feedback from various sources including
    GitHub discussions, issues, Stack Overflow mentions, and social media to
    provide comprehensive community sentiment analysis.
    
    Note: This is a future-ready implementation as PyPI doesn't currently have
    a native review system. The function prepares for when such features become
    available while providing useful community sentiment analysis from existing sources.
    
    Args:
        package_name: Name of the package to get reviews for
        include_ratings: Whether to include numerical ratings (when available)
        include_community_feedback: Whether to include textual feedback analysis
        sentiment_analysis: Whether to perform sentiment analysis on feedback
        max_reviews: Maximum number of reviews to return
        
    Returns:
        Dictionary containing review and feedback information including:
        - Community sentiment and ratings
        - Feedback from GitHub issues and discussions
        - Social media mentions and sentiment
        - Quality indicators and community health metrics
        - Future-ready structure for native PyPI reviews
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    logger.info(f"Gathering community reviews and feedback for package: {package_name}")
    
    try:
        # Gather data from multiple community sources concurrently
        review_tasks = [
            _get_package_metadata_for_reviews(package_name),
            _analyze_github_community_sentiment(package_name) if include_community_feedback else asyncio.create_task(_empty_dict()),
            _check_stackoverflow_mentions(package_name) if include_community_feedback else asyncio.create_task(_empty_dict()),
            _analyze_pypi_downloads_as_quality_indicator(package_name),
            _get_community_health_metrics(package_name),
        ]
        
        results = await asyncio.gather(*review_tasks, return_exceptions=True)
        
        package_metadata = results[0] if not isinstance(results[0], Exception) else {}
        github_sentiment = results[1] if not isinstance(results[1], Exception) else {}
        stackoverflow_data = results[2] if not isinstance(results[2], Exception) else {}
        quality_indicators = results[3] if not isinstance(results[3], Exception) else {}
        community_health = results[4] if not isinstance(results[4], Exception) else {}
        
        # Perform sentiment analysis if requested
        sentiment_analysis_results = {}
        if sentiment_analysis and (github_sentiment or stackoverflow_data):
            sentiment_analysis_results = await _perform_sentiment_analysis(
                github_sentiment, stackoverflow_data
            )
        
        # Calculate overall community score
        community_score = _calculate_community_score(
            github_sentiment, stackoverflow_data, quality_indicators, community_health
        )
        
        # Generate community insights
        insights = _generate_community_insights(
            github_sentiment, stackoverflow_data, community_score, package_metadata
        )
        
        review_report = {
            "package": package_name,
            "review_timestamp": datetime.now().isoformat(),
            "community_score": community_score,
            "metadata": package_metadata,
            "community_health": community_health,
            "quality_indicators": quality_indicators,
            "insights": insights,
            "data_sources": {
                "github_analysis": bool(github_sentiment),
                "stackoverflow_mentions": bool(stackoverflow_data),
                "pypi_metrics": bool(quality_indicators),
                "community_health": bool(community_health),
            },
            "review_system_status": {
                "native_pypi_reviews": "not_available",
                "note": "PyPI does not currently have a native review system. This analysis aggregates community feedback from external sources.",
                "future_ready": True,
                "implementation_note": "This function is designed to seamlessly integrate native PyPI reviews when they become available.",
            },
        }
        
        # Add optional sections based on flags
        if include_community_feedback and github_sentiment:
            review_report["github_community_feedback"] = github_sentiment
            
        if include_community_feedback and stackoverflow_data:
            review_report["stackoverflow_mentions"] = stackoverflow_data
            
        if sentiment_analysis and sentiment_analysis_results:
            review_report["sentiment_analysis"] = sentiment_analysis_results
            
        # Add ratings section (prepared for future PyPI native ratings)
        if include_ratings:
            review_report["ratings"] = {
                "average_rating": None,
                "total_ratings": 0,
                "rating_distribution": {},
                "community_derived_score": community_score.get("overall_score", 0),
                "note": "Native PyPI ratings not yet available. Community-derived score provided based on external feedback.",
            }
            
        return review_report
        
    except Exception as e:
        logger.error(f"Error gathering reviews for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to gather community reviews: {e}") from e


async def manage_pypi_package_discussions(
    package_name: str,
    action: str = "get_status",
    discussion_settings: Optional[Dict[str, Any]] = None,
    moderator_controls: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Manage and interact with PyPI package discussions.
    
    This function provides management capabilities for package discussions,
    including enabling/disabling discussions, setting moderation policies,
    and retrieving discussion status and metrics.
    
    Note: This is a future-ready implementation as PyPI doesn't currently have
    native discussion features. The function prepares for when such features
    become available while providing integration with existing discussion platforms.
    
    Args:
        package_name: Name of the package to manage discussions for
        action: Action to perform ('get_status', 'enable', 'disable', 'configure', 'moderate')
        discussion_settings: Settings for discussions (when enabling/configuring)
        moderator_controls: Moderation settings and controls
        
    Returns:
        Dictionary containing discussion management results including:
        - Current discussion status and settings
        - Available discussion platforms and integration status
        - Moderation settings and community guidelines
        - Discussion metrics and engagement data
        - Future-ready structure for native PyPI discussions
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
        PyPIError: For PyPI-specific errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    valid_actions = ["get_status", "enable", "disable", "configure", "moderate", "get_metrics"]
    
    if action not in valid_actions:
        raise InvalidPackageNameError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")
    
    logger.info(f"Managing discussions for package: {package_name}, action: {action}")
    
    try:
        # Get package metadata and current discussion status
        package_data = await _get_package_metadata_for_discussions(package_name)
        current_status = await _get_current_discussion_status(package_name, package_data)
        
        # Perform the requested action
        if action == "get_status":
            result = await _get_discussion_status(package_name, current_status)
        elif action == "enable":
            result = await _enable_discussions(package_name, discussion_settings, current_status)
        elif action == "disable":
            result = await _disable_discussions(package_name, current_status)
        elif action == "configure":
            result = await _configure_discussions(package_name, discussion_settings, current_status)
        elif action == "moderate":
            result = await _moderate_discussions(package_name, moderator_controls, current_status)
        elif action == "get_metrics":
            result = await _get_discussion_metrics(package_name, current_status)
        else:
            result = {"error": f"Action {action} not implemented"}
            
        # Add common metadata to all responses
        result.update({
            "package": package_name,
            "action_performed": action,
            "timestamp": datetime.now().isoformat(),
            "discussion_system_status": {
                "native_pypi_discussions": "not_available",
                "note": "PyPI does not currently have native discussion features. This function manages external discussion platforms and prepares for future PyPI integration.",
                "supported_platforms": ["GitHub Discussions", "Community Forums", "Social Media"],
                "future_ready": True,
            },
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error managing discussions for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError, PyPIError)):
            raise
        raise NetworkError(f"Failed to manage package discussions: {e}") from e


async def get_pypi_maintainer_contacts(
    package_name: str,
    contact_types: Optional[List[str]] = None,
    include_social_profiles: bool = False,
    include_contribution_guidelines: bool = True,
    respect_privacy_settings: bool = True,
) -> Dict[str, Any]:
    """
    Get contact information and communication channels for package maintainers.
    
    This function retrieves publicly available contact information for package
    maintainers while respecting privacy settings and providing appropriate
    communication channels for different types of inquiries.
    
    Args:
        package_name: Name of the package to get maintainer contacts for
        contact_types: Types of contact info to retrieve ('email', 'github', 'social', 'support')
        include_social_profiles: Whether to include social media profiles
        include_contribution_guidelines: Whether to include contribution guidelines
        respect_privacy_settings: Whether to respect maintainer privacy preferences
        
    Returns:
        Dictionary containing maintainer contact information including:
        - Publicly available contact methods
        - Communication preferences and guidelines
        - Support channels and community resources
        - Privacy-respecting contact recommendations
        - Contribution guidelines and community standards
        
    Raises:
        InvalidPackageNameError: If package name is invalid
        PackageNotFoundError: If package is not found
        NetworkError: For network-related errors
    """
    if not package_name or not package_name.strip():
        raise InvalidPackageNameError("Package name cannot be empty")
    
    package_name = package_name.strip()
    
    # Set default contact types if not provided
    if contact_types is None:
        contact_types = ["github", "support", "community"]
    
    # Validate contact types
    valid_contact_types = ["email", "github", "social", "support", "community", "documentation"]
    invalid_types = [ct for ct in contact_types if ct not in valid_contact_types]
    if invalid_types:
        raise InvalidPackageNameError(f"Invalid contact types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_contact_types)}")
    
    logger.info(f"Gathering maintainer contact information for package: {package_name}")
    
    try:
        # Gather data from multiple sources concurrently
        contact_tasks = [
            _get_package_metadata_for_contacts(package_name),
            _analyze_github_maintainer_info(package_name) if "github" in contact_types else asyncio.create_task(_empty_dict()),
            _get_support_channels(package_name) if "support" in contact_types else asyncio.create_task(_empty_dict()),
            _get_community_channels(package_name) if "community" in contact_types else asyncio.create_task(_empty_dict()),
            _get_contribution_guidelines(package_name) if include_contribution_guidelines else asyncio.create_task(_empty_dict()),
        ]
        
        results = await asyncio.gather(*contact_tasks, return_exceptions=True)
        
        package_metadata = results[0] if not isinstance(results[0], Exception) else {}
        github_info = results[1] if not isinstance(results[1], Exception) else {}
        support_channels = results[2] if not isinstance(results[2], Exception) else {}
        community_channels = results[3] if not isinstance(results[3], Exception) else {}
        contribution_info = results[4] if not isinstance(results[4], Exception) else {}
        
        # Extract contact information from package metadata
        contact_info = _extract_contact_info_from_metadata(
            package_metadata, contact_types, respect_privacy_settings
        )
        
        # Get social profiles if requested
        social_profiles = {}
        if include_social_profiles and "social" in contact_types:
            social_profiles = await _get_social_profiles(package_name, github_info, respect_privacy_settings)
        
        # Generate contact recommendations
        contact_recommendations = _generate_contact_recommendations(
            contact_info, github_info, support_channels, community_channels
        )
        
        # Assess contact accessibility and responsiveness
        accessibility_assessment = _assess_contact_accessibility(
            contact_info, github_info, support_channels
        )
        
        contact_report = {
            "package": package_name,
            "contact_timestamp": datetime.now().isoformat(),
            "contact_information": contact_info,
            "accessibility_assessment": accessibility_assessment,
            "contact_recommendations": contact_recommendations,
            "privacy_compliance": {
                "respects_privacy_settings": respect_privacy_settings,
                "data_sources": "Publicly available information only",
                "privacy_note": "All contact information is sourced from publicly available package metadata and repositories",
            },
        }
        
        # Add optional sections based on flags and availability
        if github_info:
            contact_report["github_information"] = github_info
            
        if support_channels:
            contact_report["support_channels"] = support_channels
            
        if community_channels:
            contact_report["community_channels"] = community_channels
            
        if include_contribution_guidelines and contribution_info:
            contact_report["contribution_guidelines"] = contribution_info
            
        if include_social_profiles and social_profiles:
            contact_report["social_profiles"] = social_profiles
            
        # Add communication guidelines
        contact_report["communication_guidelines"] = _generate_communication_guidelines(
            contact_info, github_info, package_metadata
        )
        
        return contact_report
        
    except Exception as e:
        logger.error(f"Error gathering maintainer contacts for {package_name}: {e}")
        if isinstance(e, (InvalidPackageNameError, PackageNotFoundError, NetworkError)):
            raise
        raise NetworkError(f"Failed to gather maintainer contact information: {e}") from e


# Helper functions for community tools implementation

async def _empty_dict():
    """Return empty dict for optional tasks."""
    return {}


async def _get_package_metadata_for_reviews(package_name: str) -> Dict[str, Any]:
    """Get package metadata relevant for review analysis."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        return {
            "name": info.get("name", package_name),
            "version": info.get("version", "unknown"),
            "summary": info.get("summary", ""),
            "description": info.get("description", ""),
            "author": info.get("author", ""),
            "maintainer": info.get("maintainer", ""),
            "home_page": info.get("home_page", ""),
            "project_urls": info.get("project_urls", {}),
            "keywords": info.get("keywords", ""),
            "classifiers": info.get("classifiers", []),
            "license": info.get("license", ""),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get package metadata for reviews: {e}")
        return {"name": package_name}


async def _analyze_github_community_sentiment(package_name: str) -> Dict[str, Any]:
    """Analyze GitHub community sentiment through issues and discussions."""
    try:
        # Get GitHub repository information
        github_info = await _find_github_repository(package_name)
        if not github_info.get("repository_url"):
            return {"status": "no_github_repository"}
            
        # Use GitHub client to get community data
        async with GitHubClient() as github_client:
            # Get recent issues for sentiment analysis
            issues_data = await github_client.get_repository_issues(
                github_info["owner"], 
                github_info["repo"], 
                state="all", 
                limit=50
            )
            
            # Analyze sentiment from issue titles and comments
            sentiment_analysis = _analyze_issue_sentiment(issues_data)
            
            # Get repository stats for community health
            repo_stats = await github_client.get_repository_stats(
                github_info["owner"], 
                github_info["repo"]
            )
            
        return {
            "repository": github_info["repository_url"],
            "sentiment_analysis": sentiment_analysis,
            "repository_stats": repo_stats,
            "issues_analyzed": len(issues_data.get("issues", [])),
            "analysis_timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze GitHub sentiment for {package_name}: {e}")
        return {"error": str(e), "status": "analysis_failed"}


async def _check_stackoverflow_mentions(package_name: str) -> Dict[str, Any]:
    """Check Stack Overflow for package mentions and sentiment."""
    try:
        # Use Stack Exchange API to search for package mentions
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Search for questions mentioning the package
            stackoverflow_url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "site": "stackoverflow",
                "q": package_name,
                "sort": "relevance",
                "order": "desc",
                "pagesize": 20,
            }
            
            response = await client.get(stackoverflow_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                questions = data.get("items", [])
                
                # Analyze question sentiment and topics
                stackoverflow_analysis = _analyze_stackoverflow_sentiment(questions, package_name)
                
                return {
                    "questions_found": len(questions),
                    "sentiment_analysis": stackoverflow_analysis,
                    "search_timestamp": datetime.now().isoformat(),
                    "data_source": "Stack Overflow API",
                }
            else:
                logger.warning(f"Stack Overflow API returned status {response.status_code}")
                return {"status": "api_unavailable", "questions_found": 0}
                
    except Exception as e:
        logger.warning(f"Failed to check Stack Overflow mentions for {package_name}: {e}")
        return {"error": str(e), "status": "analysis_failed"}


async def _analyze_pypi_downloads_as_quality_indicator(package_name: str) -> Dict[str, Any]:
    """Use download statistics as a quality and adoption indicator."""
    try:
        # Use existing download stats functionality
        from .download_stats import get_package_download_stats
        
        download_stats = await get_package_download_stats(package_name)
        
        # Convert download numbers to quality indicators
        downloads = download_stats.get("downloads", {})
        last_month = downloads.get("last_month", 0)
        
        # Categorize adoption level
        if last_month > 1000000:
            adoption_level = "very_high"
        elif last_month > 100000:
            adoption_level = "high"
        elif last_month > 10000:
            adoption_level = "moderate"
        elif last_month > 1000:
            adoption_level = "growing"
        else:
            adoption_level = "emerging"
            
        return {
            "download_stats": downloads,
            "adoption_level": adoption_level,
            "quality_indicator_score": min(100, (last_month / 10000) * 10),  # Scale to 0-100
            "analysis_timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze download stats for {package_name}: {e}")
        return {"error": str(e), "adoption_level": "unknown"}


async def _get_community_health_metrics(package_name: str) -> Dict[str, Any]:
    """Get community health metrics from various sources."""
    try:
        # Get GitHub repository for community metrics
        github_info = await _find_github_repository(package_name)
        
        if github_info.get("repository_url"):
            async with GitHubClient() as github_client:
                # Get community health data
                community_profile = await github_client.get_community_profile(
                    github_info["owner"], 
                    github_info["repo"]
                )
                
                return {
                    "github_community_health": community_profile,
                    "has_repository": True,
                    "repository_url": github_info["repository_url"],
                }
        else:
            return {
                "has_repository": False,
                "note": "No GitHub repository found for community health analysis",
            }
            
    except Exception as e:
        logger.warning(f"Failed to get community health metrics for {package_name}: {e}")
        return {"error": str(e), "has_repository": False}


async def _perform_sentiment_analysis(github_sentiment: Dict, stackoverflow_data: Dict) -> Dict[str, Any]:
    """Perform sentiment analysis on community feedback."""
    try:
        # Simple sentiment analysis based on available data
        sentiment_scores = []
        
        # Analyze GitHub sentiment
        if github_sentiment.get("sentiment_analysis"):
            github_score = github_sentiment["sentiment_analysis"].get("overall_sentiment_score", 50)
            sentiment_scores.append(("github", github_score))
            
        # Analyze Stack Overflow sentiment  
        if stackoverflow_data.get("sentiment_analysis"):
            so_score = stackoverflow_data["sentiment_analysis"].get("overall_sentiment_score", 50)
            sentiment_scores.append(("stackoverflow", so_score))
            
        # Calculate overall sentiment
        if sentiment_scores:
            overall_score = sum(score for _, score in sentiment_scores) / len(sentiment_scores)
            sentiment_level = "positive" if overall_score > 60 else "neutral" if overall_score > 40 else "negative"
        else:
            overall_score = 50
            sentiment_level = "neutral"
            
        return {
            "overall_sentiment_score": round(overall_score, 1),
            "sentiment_level": sentiment_level,
            "source_scores": dict(sentiment_scores),
            "confidence": "medium" if len(sentiment_scores) > 1 else "low",
            "analysis_timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Failed to perform sentiment analysis: {e}")
        return {"error": str(e), "sentiment_level": "unknown"}


def _calculate_community_score(
    github_sentiment: Dict, 
    stackoverflow_data: Dict, 
    quality_indicators: Dict, 
    community_health: Dict
) -> Dict[str, Any]:
    """Calculate overall community score based on multiple factors."""
    score_components = {}
    total_weight = 0
    weighted_score = 0
    
    # GitHub sentiment component (weight: 30%)
    if github_sentiment.get("sentiment_analysis"):
        github_score = github_sentiment["sentiment_analysis"].get("overall_sentiment_score", 50)
        score_components["github_sentiment"] = github_score
        weighted_score += github_score * 0.3
        total_weight += 0.3
        
    # Stack Overflow mentions component (weight: 20%)
    if stackoverflow_data.get("sentiment_analysis"):
        so_score = stackoverflow_data["sentiment_analysis"].get("overall_sentiment_score", 50)
        score_components["stackoverflow_sentiment"] = so_score
        weighted_score += so_score * 0.2
        total_weight += 0.2
        
    # Download/adoption component (weight: 25%)
    if quality_indicators.get("quality_indicator_score"):
        adoption_score = quality_indicators["quality_indicator_score"]
        score_components["adoption_level"] = adoption_score
        weighted_score += adoption_score * 0.25
        total_weight += 0.25
        
    # Community health component (weight: 25%)
    if community_health.get("github_community_health"):
        # Simplified health score based on repository activity
        health_score = 70  # Default moderate score
        score_components["community_health"] = health_score
        weighted_score += health_score * 0.25
        total_weight += 0.25
        
    # Calculate final score
    overall_score = weighted_score / total_weight if total_weight > 0 else 50
    
    # Determine community status
    if overall_score >= 80:
        status = "excellent"
    elif overall_score >= 65:
        status = "good"
    elif overall_score >= 50:
        status = "moderate"
    elif overall_score >= 35:
        status = "limited"
    else:
        status = "poor"
        
    return {
        "overall_score": round(overall_score, 1),
        "community_status": status,
        "score_components": score_components,
        "data_reliability": total_weight,
        "calculation_timestamp": datetime.now().isoformat(),
    }


def _generate_community_insights(
    github_sentiment: Dict, 
    stackoverflow_data: Dict, 
    community_score: Dict, 
    package_metadata: Dict
) -> Dict[str, Any]:
    """Generate insights from community analysis."""
    insights = {
        "key_insights": [],
        "recommendations": [],
        "community_strengths": [],
        "areas_for_improvement": [],
    }
    
    score = community_score.get("overall_score", 50)
    
    # Generate insights based on score
    if score >= 70:
        insights["key_insights"].append("Package has strong community support and positive sentiment")
        insights["community_strengths"].append("Active and engaged community")
    elif score >= 50:
        insights["key_insights"].append("Package has moderate community engagement")
        insights["recommendations"].append("Consider increasing community engagement initiatives")
    else:
        insights["key_insights"].append("Package has limited community feedback available")
        insights["areas_for_improvement"].append("Community engagement and visibility")
        
    # Add specific insights from GitHub
    if github_sentiment.get("repository_stats"):
        stars = github_sentiment["repository_stats"].get("stargazers_count", 0)
        if stars > 1000:
            insights["community_strengths"].append("High GitHub stars indicating community appreciation")
        elif stars > 100:
            insights["community_strengths"].append("Moderate GitHub community following")
            
    # Add Stack Overflow insights
    if stackoverflow_data.get("questions_found", 0) > 10:
        insights["community_strengths"].append("Active discussion on Stack Overflow")
    elif stackoverflow_data.get("questions_found", 0) > 0:
        insights["key_insights"].append("Some Stack Overflow discussion available")
    else:
        insights["areas_for_improvement"].append("Limited presence in developer Q&A platforms")
        
    return insights


# Helper functions for discussion management

async def _get_package_metadata_for_discussions(package_name: str) -> Dict[str, Any]:
    """Get package metadata relevant for discussion management."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
        return package_data
    except Exception as e:
        logger.warning(f"Failed to get package metadata for discussions: {e}")
        return {}


async def _get_current_discussion_status(package_name: str, package_data: Dict) -> Dict[str, Any]:
    """Get current discussion status from various platforms."""
    try:
        # Check GitHub Discussions
        github_status = await _check_github_discussions_status(package_name, package_data)
        
        # Check other community platforms
        community_platforms = await _check_community_platforms(package_name, package_data)
        
        return {
            "github_discussions": github_status,
            "community_platforms": community_platforms,
            "native_pypi_discussions": {
                "available": False,
                "note": "PyPI does not currently support native discussions",
            },
        }
        
    except Exception as e:
        logger.warning(f"Failed to get discussion status for {package_name}: {e}")
        return {"error": str(e)}


async def _get_discussion_status(package_name: str, current_status: Dict) -> Dict[str, Any]:
    """Get comprehensive discussion status."""
    return {
        "status": "retrieved",
        "current_discussion_status": current_status,
        "available_platforms": [
            {
                "platform": "GitHub Discussions",
                "status": current_status.get("github_discussions", {}).get("enabled", False),
                "url": current_status.get("github_discussions", {}).get("url"),
            }
        ],
        "management_options": [
            "Enable/disable GitHub Discussions",
            "Configure community guidelines",
            "Set up moderation policies",
            "Monitor discussion metrics",
        ],
    }


async def _enable_discussions(package_name: str, settings: Optional[Dict], current_status: Dict) -> Dict[str, Any]:
    """Enable discussions for the package."""
    # This is a placeholder for future implementation
    # Would integrate with GitHub API to enable discussions
    
    return {
        "status": "configured",
        "action": "enable_discussions",
        "message": "Discussion enabling configured (requires repository admin access)",
        "settings_applied": settings or {},
        "next_steps": [
            "Verify repository admin access",
            "Enable GitHub Discussions in repository settings",
            "Configure community guidelines",
            "Set up moderation policies",
        ],
        "note": "Actual enabling requires repository admin privileges and GitHub API integration",
    }


async def _disable_discussions(package_name: str, current_status: Dict) -> Dict[str, Any]:
    """Disable discussions for the package."""
    return {
        "status": "configured",
        "action": "disable_discussions",
        "message": "Discussion disabling configured (requires repository admin access)",
        "current_status": current_status,
        "next_steps": [
            "Verify repository admin access",
            "Disable GitHub Discussions in repository settings",
            "Archive existing discussions if needed",
        ],
        "note": "Actual disabling requires repository admin privileges",
    }


async def _configure_discussions(package_name: str, settings: Optional[Dict], current_status: Dict) -> Dict[str, Any]:
    """Configure discussion settings."""
    return {
        "status": "configured",
        "action": "configure_discussions",
        "settings": settings or {},
        "current_status": current_status,
        "configuration_options": {
            "categories": ["General", "Q&A", "Ideas", "Show and Tell"],
            "moderation": ["Auto-moderation", "Manual review", "Community moderation"],
            "notifications": ["Email notifications", "Web notifications", "Digest emails"],
        },
        "note": "Configuration changes require repository admin access",
    }


async def _moderate_discussions(package_name: str, moderator_controls: Optional[Dict], current_status: Dict) -> Dict[str, Any]:
    """Apply moderation controls to discussions."""
    return {
        "status": "moderation_configured",
        "action": "moderate_discussions",
        "moderator_controls": moderator_controls or {},
        "current_status": current_status,
        "moderation_features": {
            "content_filtering": "Automatic filtering of inappropriate content",
            "user_management": "Block/unblock users, assign moderator roles",
            "discussion_management": "Lock/unlock, pin/unpin discussions",
            "reporting": "Community reporting and review systems",
        },
        "note": "Moderation requires appropriate permissions and platform integration",
    }


async def _get_discussion_metrics(package_name: str, current_status: Dict) -> Dict[str, Any]:
    """Get discussion engagement metrics."""
    try:
        github_metrics = {}
        if current_status.get("github_discussions", {}).get("enabled"):
            github_metrics = await _get_github_discussion_metrics(package_name)
            
        return {
            "status": "metrics_retrieved",
            "github_metrics": github_metrics,
            "overall_engagement": _calculate_discussion_engagement(github_metrics),
            "metrics_timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get discussion metrics: {e}")
        return {"error": str(e), "status": "metrics_unavailable"}


# Helper functions for maintainer contacts

async def _get_package_metadata_for_contacts(package_name: str) -> Dict[str, Any]:
    """Get package metadata relevant for contact information."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        return {
            "name": info.get("name", package_name),
            "author": info.get("author", ""),
            "author_email": info.get("author_email", ""),
            "maintainer": info.get("maintainer", ""),
            "maintainer_email": info.get("maintainer_email", ""),
            "home_page": info.get("home_page", ""),
            "project_urls": info.get("project_urls", {}),
            "download_url": info.get("download_url", ""),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get package metadata for contacts: {e}")
        return {"name": package_name}


async def _analyze_github_maintainer_info(package_name: str) -> Dict[str, Any]:
    """Analyze GitHub repository for maintainer information."""
    try:
        github_info = await _find_github_repository(package_name)
        if not github_info.get("repository_url"):
            return {"status": "no_github_repository"}
            
        async with GitHubClient() as github_client:
            # Get repository information
            repo_data = await github_client.get_repository_info(
                github_info["owner"], 
                github_info["repo"]
            )
            
            # Get contributors
            contributors = await github_client.get_repository_contributors(
                github_info["owner"], 
                github_info["repo"], 
                limit=10
            )
            
        return {
            "repository": github_info["repository_url"],
            "owner": github_info["owner"],
            "repository_data": repo_data,
            "contributors": contributors,
            "primary_maintainer": repo_data.get("owner", {}),
        }
        
    except Exception as e:
        logger.warning(f"Failed to analyze GitHub maintainer info: {e}")
        return {"error": str(e), "status": "analysis_failed"}


async def _get_support_channels(package_name: str) -> Dict[str, Any]:
    """Get available support channels for the package."""
    try:
        # Check common support channels
        support_channels = {
            "issue_tracker": None,
            "documentation": None,
            "community_forum": None,
            "chat_channels": [],
        }
        
        # Get GitHub repository for issue tracker
        github_info = await _find_github_repository(package_name)
        if github_info.get("repository_url"):
            support_channels["issue_tracker"] = f"{github_info['repository_url']}/issues"
            
            # Check for documentation links
            async with GitHubClient() as github_client:
                repo_data = await github_client.get_repository_info(
                    github_info["owner"], 
                    github_info["repo"]
                )
                
                if repo_data.get("has_pages"):
                    support_channels["documentation"] = f"https://{github_info['owner']}.github.io/{github_info['repo']}/"
                    
        return support_channels
        
    except Exception as e:
        logger.warning(f"Failed to get support channels: {e}")
        return {}


async def _get_community_channels(package_name: str) -> Dict[str, Any]:
    """Get available community channels for the package."""
    try:
        community_channels = {
            "github_discussions": None,
            "stackoverflow_tag": None,
            "reddit_community": None,
            "discord_server": None,
        }
        
        # Check for GitHub Discussions
        github_info = await _find_github_repository(package_name)
        if github_info.get("repository_url"):
            # Check if discussions are enabled
            discussions_enabled = await _check_github_discussions_enabled(
                github_info["owner"], 
                github_info["repo"]
            )
            if discussions_enabled:
                community_channels["github_discussions"] = f"{github_info['repository_url']}/discussions"
                
        # Check for Stack Overflow tag
        stackoverflow_tag = await _check_stackoverflow_tag(package_name)
        if stackoverflow_tag:
            community_channels["stackoverflow_tag"] = f"https://stackoverflow.com/questions/tagged/{stackoverflow_tag}"
            
        return community_channels
        
    except Exception as e:
        logger.warning(f"Failed to get community channels: {e}")
        return {}


async def _get_contribution_guidelines(package_name: str) -> Dict[str, Any]:
    """Get contribution guidelines for the package."""
    try:
        github_info = await _find_github_repository(package_name)
        if not github_info.get("repository_url"):
            return {"status": "no_repository"}
            
        async with GitHubClient() as github_client:
            # Check for common contribution files
            contribution_files = await github_client.get_community_files(
                github_info["owner"], 
                github_info["repo"]
            )
            
        return {
            "repository": github_info["repository_url"],
            "contribution_files": contribution_files,
            "guidelines_available": bool(contribution_files),
        }
        
    except Exception as e:
        logger.warning(f"Failed to get contribution guidelines: {e}")
        return {"error": str(e)}


def _extract_contact_info_from_metadata(
    package_metadata: Dict, 
    contact_types: List[str], 
    respect_privacy: bool
) -> Dict[str, Any]:
    """Extract contact information from package metadata."""
    contact_info = {
        "available_contacts": {},
        "project_urls": {},
        "privacy_compliant": respect_privacy,
    }
    
    # Extract email contacts if requested and available
    if "email" in contact_types:
        if package_metadata.get("author_email") and not respect_privacy:
            contact_info["available_contacts"]["author_email"] = package_metadata["author_email"]
        if package_metadata.get("maintainer_email") and not respect_privacy:
            contact_info["available_contacts"]["maintainer_email"] = package_metadata["maintainer_email"]
        if respect_privacy:
            contact_info["available_contacts"]["email_note"] = "Email addresses hidden due to privacy settings"
            
    # Extract project URLs
    project_urls = package_metadata.get("project_urls", {})
    for url_type, url in project_urls.items():
        if _is_relevant_project_url(url_type, contact_types):
            contact_info["project_urls"][url_type] = url
            
    # Add homepage if available
    if package_metadata.get("home_page"):
        contact_info["project_urls"]["Homepage"] = package_metadata["home_page"]
        
    return contact_info


async def _get_social_profiles(package_name: str, github_info: Dict, respect_privacy: bool) -> Dict[str, Any]:
    """Get social media profiles for maintainers."""
    if respect_privacy:
        return {
            "status": "privacy_protected",
            "note": "Social profiles hidden due to privacy settings",
        }
        
    # This would require additional API integrations
    # For now, return a placeholder structure
    return {
        "status": "limited_data",
        "note": "Social profile discovery requires additional API integrations",
        "available_platforms": ["GitHub", "Twitter", "LinkedIn"],
    }


def _generate_contact_recommendations(
    contact_info: Dict, 
    github_info: Dict, 
    support_channels: Dict, 
    community_channels: Dict
) -> List[str]:
    """Generate recommendations for contacting maintainers."""
    recommendations = []
    
    # Recommend GitHub issues for bugs and features
    if github_info.get("repository"):
        recommendations.append("Use GitHub issues for bug reports and feature requests")
        
    # Recommend GitHub discussions for general questions
    if community_channels.get("github_discussions"):
        recommendations.append("Use GitHub Discussions for general questions and community interaction")
        
    # Recommend proper channels based on inquiry type
    recommendations.extend([
        "Check existing issues before creating new ones",
        "Follow contribution guidelines when proposing changes",
        "Be respectful and patient when seeking support",
        "Provide detailed information when reporting issues",
    ])
    
    return recommendations


def _assess_contact_accessibility(
    contact_info: Dict, 
    github_info: Dict, 
    support_channels: Dict
) -> Dict[str, Any]:
    """Assess how accessible maintainers are for contact."""
    accessibility_score = 0
    factors = []
    
    # GitHub repository increases accessibility
    if github_info.get("repository"):
        accessibility_score += 40
        factors.append("GitHub repository available")
        
    # Issue tracker increases accessibility
    if support_channels.get("issue_tracker"):
        accessibility_score += 30
        factors.append("Issue tracker available")
        
    # Project URLs increase accessibility
    if contact_info.get("project_urls"):
        accessibility_score += 20
        factors.append("Project URLs provided")
        
    # Documentation increases accessibility
    if support_channels.get("documentation"):
        accessibility_score += 10
        factors.append("Documentation available")
        
    # Determine accessibility level
    if accessibility_score >= 80:
        level = "excellent"
    elif accessibility_score >= 60:
        level = "good"
    elif accessibility_score >= 40:
        level = "moderate"
    else:
        level = "limited"
        
    return {
        "accessibility_score": accessibility_score,
        "accessibility_level": level,
        "contributing_factors": factors,
        "assessment_timestamp": datetime.now().isoformat(),
    }


def _generate_communication_guidelines(
    contact_info: Dict, 
    github_info: Dict, 
    package_metadata: Dict
) -> Dict[str, Any]:
    """Generate communication guidelines for contacting maintainers."""
    return {
        "best_practices": [
            "Be clear and concise in your communication",
            "Provide reproducible examples for bug reports",
            "Search existing issues before creating new ones",
            "Follow the project's code of conduct",
            "Be patient and respectful in all interactions",
        ],
        "communication_channels": {
            "bug_reports": "GitHub Issues (if available)",
            "feature_requests": "GitHub Issues or Discussions",
            "general_questions": "GitHub Discussions or community forums",
            "security_issues": "Private communication via email or security contact",
        },
        "response_expectations": {
            "bug_reports": "Response within 1-7 days (varies by project)",
            "feature_requests": "Response time varies significantly",
            "general_questions": "Community may respond faster than maintainers",
            "note": "Response times depend on maintainer availability and project activity",
        },
    }


# Additional helper functions for GitHub and community analysis

async def _find_github_repository(package_name: str) -> Dict[str, Any]:
    """Find GitHub repository for a package."""
    try:
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data.get("info", {})
        
        # Check project URLs for GitHub
        project_urls = info.get("project_urls", {})
        for url_type, url in project_urls.items():
            if "github.com" in url.lower():
                return _parse_github_url(url)
                
        # Check homepage for GitHub
        home_page = info.get("home_page", "")
        if "github.com" in home_page.lower():
            return _parse_github_url(home_page)
            
        return {"status": "no_github_repository"}
        
    except Exception as e:
        logger.warning(f"Failed to find GitHub repository: {e}")
        return {"error": str(e)}


def _parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub URL to extract owner and repo."""
    try:
        # Remove .git suffix and clean URL
        clean_url = url.replace(".git", "").rstrip("/")
        
        # Parse URL
        parsed = urlparse(clean_url)
        if parsed.netloc != "github.com":
            return {"status": "not_github"}
            
        # Extract owner and repo from path
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            
            return {
                "repository_url": f"https://github.com/{owner}/{repo}",
                "owner": owner,
                "repo": repo,
            }
        else:
            return {"status": "invalid_github_url"}
            
    except Exception as e:
        logger.warning(f"Failed to parse GitHub URL {url}: {e}")
        return {"error": str(e)}


def _analyze_issue_sentiment(issues_data: Dict) -> Dict[str, Any]:
    """Analyze sentiment from GitHub issues."""
    issues = issues_data.get("issues", [])
    if not issues:
        return {"status": "no_issues", "overall_sentiment_score": 50}
        
    # Simple sentiment analysis based on issue characteristics
    positive_indicators = 0
    negative_indicators = 0
    total_issues = len(issues)
    
    for issue in issues:
        title = issue.get("title", "").lower()
        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]
        state = issue.get("state", "")
        
        # Count positive indicators
        if state == "closed":
            positive_indicators += 1
        if any(label in ["enhancement", "feature", "good first issue"] for label in labels):
            positive_indicators += 1
            
        # Count negative indicators
        if any(label in ["bug", "critical", "high priority"] for label in labels):
            negative_indicators += 1
        if any(word in title for word in ["crash", "broken", "error", "fail"]):
            negative_indicators += 1
            
    # Calculate sentiment score (0-100)
    if total_issues > 0:
        positive_ratio = positive_indicators / (total_issues * 2)  # Max 2 positive per issue
        negative_ratio = negative_indicators / (total_issues * 2)  # Max 2 negative per issue
        sentiment_score = max(0, min(100, 50 + (positive_ratio - negative_ratio) * 100))
    else:
        sentiment_score = 50
        
    return {
        "overall_sentiment_score": round(sentiment_score, 1),
        "issues_analyzed": total_issues,
        "positive_indicators": positive_indicators,
        "negative_indicators": negative_indicators,
        "sentiment_factors": {
            "closed_issues": sum(1 for issue in issues if issue.get("state") == "closed"),
            "open_issues": sum(1 for issue in issues if issue.get("state") == "open"),
            "enhancement_requests": len([issue for issue in issues if any("enhancement" in label.get("name", "").lower() for label in issue.get("labels", []))]),
            "bug_reports": len([issue for issue in issues if any("bug" in label.get("name", "").lower() for label in issue.get("labels", []))]),
        },
    }


def _analyze_stackoverflow_sentiment(questions: List[Dict], package_name: str) -> Dict[str, Any]:
    """Analyze sentiment from Stack Overflow questions."""
    if not questions:
        return {"status": "no_questions", "overall_sentiment_score": 50}
        
    # Simple sentiment analysis based on question characteristics
    positive_indicators = 0
    negative_indicators = 0
    total_questions = len(questions)
    
    for question in questions:
        title = question.get("title", "").lower()
        tags = question.get("tags", [])
        score = question.get("score", 0)
        is_answered = question.get("is_answered", False)
        
        # Count positive indicators
        if is_answered:
            positive_indicators += 1
        if score > 0:
            positive_indicators += 1
        if any(word in title for word in ["how to", "tutorial", "example", "best practice"]):
            positive_indicators += 1
            
        # Count negative indicators
        if any(word in title for word in ["error", "problem", "issue", "broken", "not working"]):
            negative_indicators += 1
        if score < 0:
            negative_indicators += 1
            
    # Calculate sentiment score
    if total_questions > 0:
        positive_ratio = positive_indicators / (total_questions * 3)  # Max 3 positive per question
        negative_ratio = negative_indicators / (total_questions * 2)  # Max 2 negative per question
        sentiment_score = max(0, min(100, 50 + (positive_ratio - negative_ratio) * 100))
    else:
        sentiment_score = 50
        
    return {
        "overall_sentiment_score": round(sentiment_score, 1),
        "questions_analyzed": total_questions,
        "positive_indicators": positive_indicators,
        "negative_indicators": negative_indicators,
        "question_characteristics": {
            "answered_questions": sum(1 for q in questions if q.get("is_answered")),
            "unanswered_questions": sum(1 for q in questions if not q.get("is_answered")),
            "average_score": sum(q.get("score", 0) for q in questions) / total_questions if total_questions > 0 else 0,
        },
    }


# Additional placeholder functions for future implementation

async def _check_github_discussions_status(package_name: str, package_data: Dict) -> Dict[str, Any]:
    """Check if GitHub Discussions are enabled for the repository."""
    github_info = await _find_github_repository(package_name)
    if not github_info.get("repository_url"):
        return {"enabled": False, "reason": "no_github_repository"}
        
    # This would require GitHub API integration to check discussions status
    return {
        "enabled": False,
        "reason": "requires_github_api_integration",
        "repository": github_info["repository_url"],
        "note": "Checking discussions status requires GitHub API integration",
    }


async def _check_community_platforms(package_name: str, package_data: Dict) -> Dict[str, Any]:
    """Check other community platforms for discussions."""
    return {
        "discord": {"available": False, "note": "Discord integration not implemented"},
        "reddit": {"available": False, "note": "Reddit integration not implemented"},
        "forums": {"available": False, "note": "Forum integration not implemented"},
    }


async def _get_github_discussion_metrics(package_name: str) -> Dict[str, Any]:
    """Get GitHub discussion engagement metrics."""
    return {
        "discussions_count": 0,
        "participants": 0,
        "note": "Requires GitHub API integration for actual metrics",
    }


def _calculate_discussion_engagement(github_metrics: Dict) -> Dict[str, Any]:
    """Calculate overall discussion engagement score."""
    return {
        "engagement_score": 0,
        "engagement_level": "unknown",
        "note": "Engagement calculation requires actual discussion data",
    }


async def _check_github_discussions_enabled(owner: str, repo: str) -> bool:
    """Check if GitHub Discussions are enabled for a repository."""
    # This would require GitHub GraphQL API to check discussions
    return False


async def _check_stackoverflow_tag(package_name: str) -> Optional[str]:
    """Check if there's a Stack Overflow tag for the package."""
    # This would require Stack Exchange API integration
    return None


def _is_relevant_project_url(url_type: str, contact_types: List[str]) -> bool:
    """Check if a project URL is relevant for the requested contact types."""
    url_type_lower = url_type.lower()
    
    if "github" in contact_types and any(keyword in url_type_lower for keyword in ["repository", "source", "github"]):
        return True
    if "support" in contact_types and any(keyword in url_type_lower for keyword in ["support", "help", "issues", "bug"]):
        return True
    if "documentation" in contact_types and any(keyword in url_type_lower for keyword in ["documentation", "docs", "wiki"]):
        return True
    if "community" in contact_types and any(keyword in url_type_lower for keyword in ["community", "forum", "chat", "discussion"]):
        return True
        
    return False
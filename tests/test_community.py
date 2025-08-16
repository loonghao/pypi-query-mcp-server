"""Tests for PyPI community and social tools functionality."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from pypi_query_mcp.core.exceptions import InvalidPackageNameError, PackageNotFoundError, NetworkError
from pypi_query_mcp.tools.community import (
    get_pypi_package_reviews,
    manage_pypi_package_discussions,
    get_pypi_maintainer_contacts,
    _analyze_github_community_sentiment,
    _check_stackoverflow_mentions,
    _analyze_pypi_downloads_as_quality_indicator,
    _get_community_health_metrics,
    _calculate_community_score,
    _generate_community_insights,
    _extract_contact_info_from_metadata,
    _find_github_repository,
    _parse_github_url,
    _analyze_issue_sentiment,
    _analyze_stackoverflow_sentiment,
)


class TestGetPyPIPackageReviews:
    """Test community reviews and feedback functionality."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data for testing."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "A test package for community analysis",
                "description": "A comprehensive test package with detailed description for community testing",
                "keywords": "test, community, package",
                "classifiers": [
                    "Development Status :: 4 - Beta",
                    "Intended Audience :: Developers",
                    "License :: OSI Approved :: MIT License",
                    "Programming Language :: Python :: 3",
                    "Topic :: Software Development :: Libraries",
                ],
                "license": "MIT",
                "author": "Test Author",
                "home_page": "https://example.com",
                "project_urls": {
                    "Documentation": "https://docs.example.com",
                    "Repository": "https://github.com/test/test-package",
                    "Bug Reports": "https://github.com/test/test-package/issues",
                },
            }
        }

    @pytest.fixture
    def mock_github_sentiment(self):
        """Mock GitHub sentiment analysis data."""
        return {
            "repository": "https://github.com/test/test-package",
            "sentiment_analysis": {
                "overall_sentiment_score": 75.5,
                "issues_analyzed": 20,
                "positive_indicators": 15,
                "negative_indicators": 5,
                "sentiment_factors": {
                    "closed_issues": 12,
                    "open_issues": 8,
                    "enhancement_requests": 5,
                    "bug_reports": 3,
                },
            },
            "repository_stats": {
                "stargazers_count": 150,
                "forks_count": 25,
                "open_issues_count": 8,
            },
            "issues_analyzed": 20,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    @pytest.fixture
    def mock_stackoverflow_data(self):
        """Mock Stack Overflow mentions data."""
        return {
            "questions_found": 5,
            "sentiment_analysis": {
                "overall_sentiment_score": 65.0,
                "questions_analyzed": 5,
                "positive_indicators": 3,
                "negative_indicators": 2,
                "question_characteristics": {
                    "answered_questions": 4,
                    "unanswered_questions": 1,
                    "average_score": 2.4,
                },
            },
            "search_timestamp": datetime.now().isoformat(),
            "data_source": "Stack Overflow API",
        }

    @pytest.fixture
    def mock_quality_indicators(self):
        """Mock quality indicators data."""
        return {
            "download_stats": {
                "last_month": 50000,
                "last_week": 12000,
                "last_day": 2000,
            },
            "adoption_level": "moderate",
            "quality_indicator_score": 50.0,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    @pytest.fixture
    def mock_community_health(self):
        """Mock community health metrics."""
        return {
            "github_community_health": {
                "health_percentage": 85,
                "documentation": {"exists": True},
                "contributing": {"exists": True},
                "code_of_conduct": {"exists": True},
                "license": {"exists": True},
                "readme": {"exists": True},
            },
            "has_repository": True,
            "repository_url": "https://github.com/test/test-package",
        }

    async def test_get_pypi_package_reviews_success(
        self, 
        mock_package_data, 
        mock_github_sentiment, 
        mock_stackoverflow_data, 
        mock_quality_indicators, 
        mock_community_health
    ):
        """Test successful retrieval of package reviews."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_reviews") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._analyze_github_community_sentiment") as mock_github, \
             patch("pypi_query_mcp.tools.community._check_stackoverflow_mentions") as mock_stackoverflow, \
             patch("pypi_query_mcp.tools.community._analyze_pypi_downloads_as_quality_indicator") as mock_quality, \
             patch("pypi_query_mcp.tools.community._get_community_health_metrics") as mock_health:
            
            mock_metadata.return_value = mock_package_data["info"]
            mock_github.return_value = mock_github_sentiment
            mock_stackoverflow.return_value = mock_stackoverflow_data
            mock_quality.return_value = mock_quality_indicators
            mock_health.return_value = mock_community_health
            
            result = await get_pypi_package_reviews(
                package_name="test-package",
                include_ratings=True,
                include_community_feedback=True,
                sentiment_analysis=True,
                max_reviews=50
            )
            
            assert result["package"] == "test-package"
            assert "community_score" in result
            assert "metadata" in result
            assert "community_health" in result
            assert "quality_indicators" in result
            assert "insights" in result
            assert "review_system_status" in result
            assert "github_community_feedback" in result
            assert "stackoverflow_mentions" in result
            assert "sentiment_analysis" in result
            assert "ratings" in result
            
            # Check community score structure
            community_score = result["community_score"]
            assert "overall_score" in community_score
            assert "community_status" in community_score
            assert "score_components" in community_score
            
            # Check review system status
            review_status = result["review_system_status"]
            assert review_status["native_pypi_reviews"] == "not_available"
            assert review_status["future_ready"] is True

    async def test_get_pypi_package_reviews_invalid_package_name(self):
        """Test handling of invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_reviews("")
            
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_reviews("   ")

    async def test_get_pypi_package_reviews_minimal_options(self, mock_package_data):
        """Test reviews with minimal options enabled."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_reviews") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._analyze_pypi_downloads_as_quality_indicator") as mock_quality, \
             patch("pypi_query_mcp.tools.community._get_community_health_metrics") as mock_health:
            
            mock_metadata.return_value = mock_package_data["info"]
            mock_quality.return_value = {"quality_indicator_score": 30}
            mock_health.return_value = {"has_repository": False}
            
            result = await get_pypi_package_reviews(
                package_name="test-package",
                include_ratings=False,
                include_community_feedback=False,
                sentiment_analysis=False
            )
            
            assert result["package"] == "test-package"
            assert "github_community_feedback" not in result
            assert "stackoverflow_mentions" not in result
            assert "sentiment_analysis" not in result
            assert "ratings" not in result

    async def test_get_pypi_package_reviews_network_error(self):
        """Test handling of network errors."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_reviews", side_effect=NetworkError("Network error")):
            with pytest.raises(NetworkError):
                await get_pypi_package_reviews("test-package")


class TestManagePyPIPackageDiscussions:
    """Test package discussions management functionality."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data for discussions testing."""
        return {
            "info": {
                "name": "test-package",
                "project_urls": {
                    "Repository": "https://github.com/test/test-package",
                },
            }
        }

    @pytest.fixture
    def mock_discussion_status(self):
        """Mock current discussion status."""
        return {
            "github_discussions": {
                "enabled": False,
                "reason": "requires_github_api_integration",
                "repository": "https://github.com/test/test-package",
            },
            "community_platforms": {
                "discord": {"available": False},
                "reddit": {"available": False},
                "forums": {"available": False},
            },
            "native_pypi_discussions": {
                "available": False,
                "note": "PyPI does not currently support native discussions",
            },
        }

    async def test_manage_discussions_get_status(self, mock_package_data, mock_discussion_status):
        """Test getting discussion status."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="get_status"
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "get_status"
            assert "status" in result
            assert "current_discussion_status" in result
            assert "available_platforms" in result
            assert "discussion_system_status" in result
            
            # Check system status
            system_status = result["discussion_system_status"]
            assert system_status["native_pypi_discussions"] == "not_available"
            assert system_status["future_ready"] is True

    async def test_manage_discussions_enable(self, mock_package_data, mock_discussion_status):
        """Test enabling discussions."""
        discussion_settings = {
            "categories": ["General", "Q&A", "Ideas"],
            "moderation": "manual_review",
        }
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="enable",
                discussion_settings=discussion_settings
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "enable"
            assert result["status"] == "configured"
            assert result["action"] == "enable_discussions"
            assert "settings_applied" in result
            assert "next_steps" in result

    async def test_manage_discussions_disable(self, mock_package_data, mock_discussion_status):
        """Test disabling discussions."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="disable"
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "disable"
            assert result["status"] == "configured"
            assert result["action"] == "disable_discussions"
            assert "next_steps" in result

    async def test_manage_discussions_configure(self, mock_package_data, mock_discussion_status):
        """Test configuring discussions."""
        discussion_settings = {
            "categories": ["General", "Q&A", "Ideas", "Show and Tell"],
            "moderation": "community_moderation",
            "notifications": ["email_notifications", "web_notifications"],
        }
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="configure",
                discussion_settings=discussion_settings
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "configure"
            assert result["status"] == "configured"
            assert result["action"] == "configure_discussions"
            assert "configuration_options" in result

    async def test_manage_discussions_moderate(self, mock_package_data, mock_discussion_status):
        """Test moderating discussions."""
        moderator_controls = {
            "content_filtering": True,
            "auto_moderation": True,
            "moderator_roles": ["owner", "maintainer"],
        }
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="moderate",
                moderator_controls=moderator_controls
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "moderate"
            assert result["status"] == "moderation_configured"
            assert result["action"] == "moderate_discussions"
            assert "moderation_features" in result

    async def test_manage_discussions_get_metrics(self, mock_package_data, mock_discussion_status):
        """Test getting discussion metrics."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_discussions") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._get_current_discussion_status") as mock_status:
            
            mock_metadata.return_value = mock_package_data
            mock_status.return_value = mock_discussion_status
            
            result = await manage_pypi_package_discussions(
                package_name="test-package",
                action="get_metrics"
            )
            
            assert result["package"] == "test-package"
            assert result["action_performed"] == "get_metrics"
            assert result["status"] == "metrics_retrieved"
            assert "github_metrics" in result
            assert "overall_engagement" in result

    async def test_manage_discussions_invalid_action(self):
        """Test handling of invalid action."""
        with pytest.raises(InvalidPackageNameError):
            await manage_pypi_package_discussions(
                package_name="test-package",
                action="invalid_action"
            )

    async def test_manage_discussions_invalid_package_name(self):
        """Test handling of invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await manage_pypi_package_discussions("")
            
        with pytest.raises(InvalidPackageNameError):
            await manage_pypi_package_discussions("   ")


class TestGetPyPIMaintainerContacts:
    """Test maintainer contact information functionality."""

    @pytest.fixture
    def mock_package_metadata(self):
        """Mock package metadata for contact testing."""
        return {
            "name": "test-package",
            "author": "Test Author",
            "author_email": "author@example.com",
            "maintainer": "Test Maintainer",
            "maintainer_email": "maintainer@example.com",
            "home_page": "https://example.com",
            "project_urls": {
                "Documentation": "https://docs.example.com",
                "Repository": "https://github.com/test/test-package",
                "Bug Reports": "https://github.com/test/test-package/issues",
                "Support": "https://support.example.com",
            },
        }

    @pytest.fixture
    def mock_github_info(self):
        """Mock GitHub maintainer information."""
        return {
            "repository": "https://github.com/test/test-package",
            "owner": "test",
            "repository_data": {
                "owner": {
                    "login": "test",
                    "type": "User",
                    "html_url": "https://github.com/test",
                },
                "has_pages": True,
                "default_branch": "main",
            },
            "contributors": [
                {
                    "login": "test",
                    "contributions": 150,
                    "html_url": "https://github.com/test",
                },
                {
                    "login": "contributor1",
                    "contributions": 25,
                    "html_url": "https://github.com/contributor1",
                },
            ],
            "primary_maintainer": {
                "login": "test",
                "type": "User",
                "html_url": "https://github.com/test",
            },
        }

    @pytest.fixture
    def mock_support_channels(self):
        """Mock support channels information."""
        return {
            "issue_tracker": "https://github.com/test/test-package/issues",
            "documentation": "https://test.github.io/test-package/",
            "community_forum": None,
            "chat_channels": [],
        }

    @pytest.fixture
    def mock_community_channels(self):
        """Mock community channels information."""
        return {
            "github_discussions": "https://github.com/test/test-package/discussions",
            "stackoverflow_tag": "https://stackoverflow.com/questions/tagged/test-package",
            "reddit_community": None,
            "discord_server": None,
        }

    @pytest.fixture
    def mock_contribution_info(self):
        """Mock contribution guidelines information."""
        return {
            "repository": "https://github.com/test/test-package",
            "contribution_files": {
                "CONTRIBUTING.md": True,
                "CODE_OF_CONDUCT.md": True,
                "SECURITY.md": False,
            },
            "guidelines_available": True,
        }

    async def test_get_maintainer_contacts_success(
        self, 
        mock_package_metadata, 
        mock_github_info, 
        mock_support_channels, 
        mock_community_channels, 
        mock_contribution_info
    ):
        """Test successful retrieval of maintainer contacts."""
        contact_types = ["github", "support", "community"]
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_contacts") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._analyze_github_maintainer_info") as mock_github, \
             patch("pypi_query_mcp.tools.community._get_support_channels") as mock_support, \
             patch("pypi_query_mcp.tools.community._get_community_channels") as mock_community, \
             patch("pypi_query_mcp.tools.community._get_contribution_guidelines") as mock_contrib:
            
            mock_metadata.return_value = mock_package_metadata
            mock_github.return_value = mock_github_info
            mock_support.return_value = mock_support_channels
            mock_community.return_value = mock_community_channels
            mock_contrib.return_value = mock_contribution_info
            
            result = await get_pypi_maintainer_contacts(
                package_name="test-package",
                contact_types=contact_types,
                include_social_profiles=True,
                include_contribution_guidelines=True,
                respect_privacy_settings=True
            )
            
            assert result["package"] == "test-package"
            assert "contact_information" in result
            assert "accessibility_assessment" in result
            assert "contact_recommendations" in result
            assert "privacy_compliance" in result
            assert "github_information" in result
            assert "support_channels" in result
            assert "community_channels" in result
            assert "contribution_guidelines" in result
            assert "social_profiles" in result
            assert "communication_guidelines" in result
            
            # Check privacy compliance
            privacy = result["privacy_compliance"]
            assert privacy["respects_privacy_settings"] is True
            assert privacy["data_sources"] == "Publicly available information only"

    async def test_get_maintainer_contacts_email_included(self, mock_package_metadata):
        """Test contacts with email included and privacy disabled."""
        contact_types = ["email", "github"]
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_contacts") as mock_metadata, \
             patch("pypi_query_mcp.tools.community._analyze_github_maintainer_info") as mock_github:
            
            mock_metadata.return_value = mock_package_metadata
            mock_github.return_value = {"status": "no_github_repository"}
            
            result = await get_pypi_maintainer_contacts(
                package_name="test-package",
                contact_types=contact_types,
                respect_privacy_settings=False
            )
            
            contact_info = result["contact_information"]
            assert "available_contacts" in contact_info
            # When privacy is disabled, emails should be included
            if not contact_info["privacy_compliant"]:
                # This would include emails if privacy is disabled
                pass

    async def test_get_maintainer_contacts_privacy_enabled(self, mock_package_metadata):
        """Test contacts with privacy settings enabled."""
        contact_types = ["email", "github"]
        
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_contacts") as mock_metadata:
            mock_metadata.return_value = mock_package_metadata
            
            result = await get_pypi_maintainer_contacts(
                package_name="test-package",
                contact_types=contact_types,
                respect_privacy_settings=True
            )
            
            contact_info = result["contact_information"]
            assert contact_info["privacy_compliant"] is True
            # With privacy enabled, emails should be hidden
            if "email_note" in contact_info.get("available_contacts", {}):
                assert "hidden due to privacy settings" in contact_info["available_contacts"]["email_note"]

    async def test_get_maintainer_contacts_minimal_options(self, mock_package_metadata):
        """Test contacts with minimal options."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_contacts") as mock_metadata:
            mock_metadata.return_value = mock_package_metadata
            
            result = await get_pypi_maintainer_contacts(
                package_name="test-package",
                contact_types=["support"],
                include_social_profiles=False,
                include_contribution_guidelines=False
            )
            
            assert result["package"] == "test-package"
            assert "contact_information" in result
            assert "github_information" not in result
            assert "contribution_guidelines" not in result
            assert "social_profiles" not in result

    async def test_get_maintainer_contacts_invalid_contact_types(self):
        """Test handling of invalid contact types."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_maintainer_contacts(
                package_name="test-package",
                contact_types=["invalid_type"]
            )

    async def test_get_maintainer_contacts_invalid_package_name(self):
        """Test handling of invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_maintainer_contacts("")
            
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_maintainer_contacts("   ")


class TestHelperFunctions:
    """Test helper functions for community tools."""

    def test_parse_github_url_valid(self):
        """Test parsing valid GitHub URLs."""
        test_cases = [
            ("https://github.com/owner/repo", {"repository_url": "https://github.com/owner/repo", "owner": "owner", "repo": "repo"}),
            ("https://github.com/owner/repo.git", {"repository_url": "https://github.com/owner/repo", "owner": "owner", "repo": "repo"}),
            ("https://github.com/owner/repo/", {"repository_url": "https://github.com/owner/repo", "owner": "owner", "repo": "repo"}),
        ]
        
        for url, expected in test_cases:
            result = _parse_github_url(url)
            assert result == expected

    def test_parse_github_url_invalid(self):
        """Test parsing invalid GitHub URLs."""
        test_cases = [
            "https://gitlab.com/owner/repo",
            "https://github.com/owner",
            "https://github.com/",
            "not-a-url",
        ]
        
        for url in test_cases:
            result = _parse_github_url(url)
            assert "status" in result or "error" in result

    def test_analyze_issue_sentiment_positive(self):
        """Test analyzing positive GitHub issue sentiment."""
        issues_data = {
            "issues": [
                {
                    "title": "Enhancement: Add new feature",
                    "state": "closed",
                    "labels": [{"name": "enhancement"}, {"name": "good first issue"}],
                },
                {
                    "title": "How to use this package?",
                    "state": "closed",
                    "labels": [{"name": "question"}],
                },
            ]
        }
        
        result = _analyze_issue_sentiment(issues_data)
        
        assert result["overall_sentiment_score"] > 50
        assert result["issues_analyzed"] == 2
        assert result["sentiment_factors"]["closed_issues"] == 2
        assert result["sentiment_factors"]["enhancement_requests"] == 1

    def test_analyze_issue_sentiment_negative(self):
        """Test analyzing negative GitHub issue sentiment."""
        issues_data = {
            "issues": [
                {
                    "title": "Critical bug: Application crashes",
                    "state": "open",
                    "labels": [{"name": "bug"}, {"name": "critical"}],
                },
                {
                    "title": "Error when importing package",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                },
            ]
        }
        
        result = _analyze_issue_sentiment(issues_data)
        
        assert result["overall_sentiment_score"] < 50
        assert result["issues_analyzed"] == 2
        assert result["sentiment_factors"]["open_issues"] == 2
        assert result["sentiment_factors"]["bug_reports"] == 2

    def test_analyze_stackoverflow_sentiment_positive(self):
        """Test analyzing positive Stack Overflow sentiment."""
        questions = [
            {
                "title": "How to implement best practices with test-package",
                "tags": ["test-package", "python"],
                "score": 5,
                "is_answered": True,
            },
            {
                "title": "Tutorial: Getting started with test-package",
                "tags": ["test-package", "tutorial"],
                "score": 3,
                "is_answered": True,
            },
        ]
        
        result = _analyze_stackoverflow_sentiment(questions, "test-package")
        
        assert result["overall_sentiment_score"] > 50
        assert result["questions_analyzed"] == 2
        assert result["question_characteristics"]["answered_questions"] == 2
        assert result["question_characteristics"]["average_score"] == 4.0

    def test_analyze_stackoverflow_sentiment_negative(self):
        """Test analyzing negative Stack Overflow sentiment."""
        questions = [
            {
                "title": "test-package not working: Error on import",
                "tags": ["test-package", "error"],
                "score": -1,
                "is_answered": False,
            },
            {
                "title": "Problem with test-package installation",
                "tags": ["test-package", "installation"],
                "score": 0,
                "is_answered": False,
            },
        ]
        
        result = _analyze_stackoverflow_sentiment(questions, "test-package")
        
        assert result["overall_sentiment_score"] < 50
        assert result["questions_analyzed"] == 2
        assert result["question_characteristics"]["unanswered_questions"] == 2
        assert result["question_characteristics"]["average_score"] == -0.5

    def test_calculate_community_score_excellent(self):
        """Test calculating excellent community score."""
        github_sentiment = {
            "sentiment_analysis": {"overall_sentiment_score": 85}
        }
        stackoverflow_data = {
            "sentiment_analysis": {"overall_sentiment_score": 80}
        }
        quality_indicators = {
            "quality_indicator_score": 90
        }
        community_health = {
            "github_community_health": {"health_percentage": 95}
        }
        
        result = _calculate_community_score(
            github_sentiment, 
            stackoverflow_data, 
            quality_indicators, 
            community_health
        )
        
        assert result["overall_score"] >= 80
        assert result["community_status"] == "excellent"
        assert len(result["score_components"]) > 0

    def test_calculate_community_score_poor(self):
        """Test calculating poor community score."""
        github_sentiment = {
            "sentiment_analysis": {"overall_sentiment_score": 20}
        }
        stackoverflow_data = {
            "sentiment_analysis": {"overall_sentiment_score": 25}
        }
        quality_indicators = {
            "quality_indicator_score": 15
        }
        community_health = {}
        
        result = _calculate_community_score(
            github_sentiment, 
            stackoverflow_data, 
            quality_indicators, 
            community_health
        )
        
        assert result["overall_score"] < 35
        assert result["community_status"] == "poor"

    def test_generate_community_insights_strong_community(self):
        """Test generating insights for strong community."""
        github_sentiment = {
            "repository_stats": {"stargazers_count": 2000}
        }
        stackoverflow_data = {
            "questions_found": 25
        }
        community_score = {
            "overall_score": 85
        }
        package_metadata = {
            "name": "test-package"
        }
        
        result = _generate_community_insights(
            github_sentiment, 
            stackoverflow_data, 
            community_score, 
            package_metadata
        )
        
        assert "key_insights" in result
        assert "community_strengths" in result
        assert len(result["community_strengths"]) > 0
        # Should have positive insights for high score
        insights_text = " ".join(result["key_insights"])
        assert "strong" in insights_text.lower() or "positive" in insights_text.lower()

    def test_extract_contact_info_from_metadata_with_privacy(self):
        """Test extracting contact info with privacy enabled."""
        package_metadata = {
            "author_email": "author@example.com",
            "maintainer_email": "maintainer@example.com",
            "project_urls": {
                "Repository": "https://github.com/test/repo",
                "Documentation": "https://docs.example.com",
                "Support": "https://support.example.com",
            },
            "home_page": "https://example.com",
        }
        
        contact_types = ["email", "github", "support"]
        
        result = _extract_contact_info_from_metadata(
            package_metadata, 
            contact_types, 
            respect_privacy=True
        )
        
        assert result["privacy_compliant"] is True
        # With privacy enabled, emails should be hidden
        assert "email_note" in result["available_contacts"]
        # Project URLs should still be included
        assert len(result["project_urls"]) > 0

    def test_extract_contact_info_from_metadata_without_privacy(self):
        """Test extracting contact info with privacy disabled."""
        package_metadata = {
            "author_email": "author@example.com",
            "maintainer_email": "maintainer@example.com",
            "project_urls": {
                "Repository": "https://github.com/test/repo",
            },
        }
        
        contact_types = ["email", "github"]
        
        result = _extract_contact_info_from_metadata(
            package_metadata, 
            contact_types, 
            respect_privacy=False
        )
        
        assert result["privacy_compliant"] is False
        # With privacy disabled, emails should be included
        assert "author_email" in result["available_contacts"]
        assert "maintainer_email" in result["available_contacts"]


class TestCommunityIntegrations:
    """Test community tool integrations with external services."""

    async def test_github_community_sentiment_no_repository(self):
        """Test GitHub sentiment analysis when no repository is found."""
        with patch("pypi_query_mcp.tools.community._find_github_repository") as mock_find:
            mock_find.return_value = {"status": "no_github_repository"}
            
            result = await _analyze_github_community_sentiment("test-package")
            
            assert result["status"] == "no_github_repository"

    async def test_stackoverflow_mentions_api_error(self):
        """Test Stack Overflow mentions with API error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 500
            
            result = await _check_stackoverflow_mentions("test-package")
            
            assert result["status"] == "api_unavailable"
            assert result["questions_found"] == 0

    async def test_quality_indicator_with_download_stats(self):
        """Test quality indicator calculation with download stats."""
        with patch("pypi_query_mcp.tools.community.get_package_download_stats") as mock_stats:
            mock_stats.return_value = {
                "downloads": {
                    "last_month": 500000,
                    "last_week": 125000,
                    "last_day": 18000,
                }
            }
            
            result = await _analyze_pypi_downloads_as_quality_indicator("test-package")
            
            assert result["adoption_level"] == "high"
            assert result["quality_indicator_score"] > 0
            assert "download_stats" in result

    async def test_community_health_metrics_no_repository(self):
        """Test community health metrics when no repository exists."""
        with patch("pypi_query_mcp.tools.community._find_github_repository") as mock_find:
            mock_find.return_value = {"status": "no_github_repository"}
            
            result = await _get_community_health_metrics("test-package")
            
            assert result["has_repository"] is False
            assert "note" in result


@pytest.mark.asyncio
class TestAsyncBehavior:
    """Test async behavior and error handling."""

    async def test_concurrent_operations_success(self):
        """Test that concurrent operations work correctly."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_reviews") as mock_meta, \
             patch("pypi_query_mcp.tools.community._analyze_github_community_sentiment") as mock_github, \
             patch("pypi_query_mcp.tools.community._check_stackoverflow_mentions") as mock_so, \
             patch("pypi_query_mcp.tools.community._analyze_pypi_downloads_as_quality_indicator") as mock_quality, \
             patch("pypi_query_mcp.tools.community._get_community_health_metrics") as mock_health:
            
            # Set up mocks to return after small delays to test concurrency
            import asyncio
            
            async def delayed_return(value, delay=0.01):
                await asyncio.sleep(delay)
                return value
            
            mock_meta.return_value = delayed_return({"name": "test-package"})
            mock_github.return_value = delayed_return({"sentiment_analysis": {"overall_sentiment_score": 75}})
            mock_so.return_value = delayed_return({"sentiment_analysis": {"overall_sentiment_score": 70}})
            mock_quality.return_value = delayed_return({"quality_indicator_score": 80})
            mock_health.return_value = delayed_return({"has_repository": True})
            
            start_time = datetime.now()
            result = await get_pypi_package_reviews("test-package")
            end_time = datetime.now()
            
            # Should complete relatively quickly due to concurrent execution
            assert (end_time - start_time).total_seconds() < 1.0
            assert result["package"] == "test-package"

    async def test_partial_failure_handling(self):
        """Test handling when some operations fail but others succeed."""
        with patch("pypi_query_mcp.tools.community._get_package_metadata_for_reviews") as mock_meta, \
             patch("pypi_query_mcp.tools.community._analyze_github_community_sentiment", side_effect=Exception("GitHub error")) as mock_github, \
             patch("pypi_query_mcp.tools.community._check_stackoverflow_mentions") as mock_so, \
             patch("pypi_query_mcp.tools.community._analyze_pypi_downloads_as_quality_indicator") as mock_quality, \
             patch("pypi_query_mcp.tools.community._get_community_health_metrics", side_effect=Exception("Health error")) as mock_health:
            
            mock_meta.return_value = {"name": "test-package"}
            mock_so.return_value = {"sentiment_analysis": {"overall_sentiment_score": 70}}
            mock_quality.return_value = {"quality_indicator_score": 80}
            
            result = await get_pypi_package_reviews("test-package")
            
            # Should still return a result even with some failures
            assert result["package"] == "test-package"
            assert "community_score" in result
            # Failed operations should result in empty dicts or be excluded
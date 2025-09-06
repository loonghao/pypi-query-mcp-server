"""Tests for PyPI Discovery & Monitoring Tools."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, Mock

from pypi_query_mcp.core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from pypi_query_mcp.tools.discovery import (
    DiscoveryCache,
    get_pypi_package_recommendations,
    get_pypi_trending_today,
    monitor_pypi_new_releases,
    search_pypi_by_maintainer,
    _categorize_package,
    _is_package_maintainer,
    _discovery_cache,
)


class TestDiscoveryCache:
    """Test the DiscoveryCache functionality."""

    def test_cache_basic_operations(self):
        """Test basic cache get/set operations."""
        cache = DiscoveryCache(default_ttl=60)
        
        # Test empty cache
        assert cache.get("nonexistent") is None
        
        # Test set and get
        test_data = {"test": "value"}
        cache.set("test_key", test_data)
        assert cache.get("test_key") == test_data
        
        # Test clear
        cache.clear()
        assert cache.get("test_key") is None

    def test_cache_expiration(self):
        """Test cache expiration functionality."""
        cache = DiscoveryCache(default_ttl=1)  # 1 second TTL
        
        test_data = {"test": "value"}
        cache.set("test_key", test_data)
        
        # Should be available immediately
        assert cache.get("test_key") == test_data
        
        # Mock time to simulate expiration
        with patch("time.time", return_value=1000000):
            cache.set("test_key", test_data)
        
        with patch("time.time", return_value=1000002):  # 2 seconds later
            assert cache.get("test_key") is None

    def test_cache_custom_ttl(self):
        """Test cache with custom TTL."""
        cache = DiscoveryCache(default_ttl=60)
        
        test_data = {"test": "value"}
        cache.set("test_key", test_data, ttl=120)  # Custom 2-minute TTL
        
        # Should still be available after default TTL would expire
        with patch("time.time", return_value=1000000):
            cache.set("test_key", test_data, ttl=120)
        
        with patch("time.time", return_value=1000060):  # 1 minute later
            assert cache.get("test_key") == test_data
        
        with patch("time.time", return_value=1000130):  # 2+ minutes later
            assert cache.get("test_key") is None


class TestMonitorPyPINewReleases:
    """Test the monitor_pypi_new_releases function."""

    @pytest.mark.asyncio
    async def test_monitor_basic_functionality(self):
        """Test basic monitoring functionality."""
        mock_releases = [
            {
                "name": "test-package",
                "version": "1.0.0",
                "release_time": "2023-01-01T12:00:00Z",
                "description": "Test package",
                "link": "https://pypi.org/project/test-package/",
            }
        ]
        
        mock_package_info = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "A test package",
                "author": "Test Author",
                "license": "MIT",
                "home_page": "https://example.com",
                "keywords": "test, package",
                "requires_python": ">=3.8",
                "project_urls": {},
                "classifiers": ["Topic :: Software Development"],
            }
        }
        
        with patch("pypi_query_mcp.tools.discovery._fetch_recent_releases_from_rss") as mock_fetch:
            mock_fetch.return_value = mock_releases
            
            with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get_package_info.return_value = mock_package_info
                
                with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                    mock_categorize.return_value = ["software-development"]
                    
                    result = await monitor_pypi_new_releases(hours=24)
                    
                    assert "new_releases" in result
                    assert result["total_releases_found"] == 1
                    assert result["monitoring_period_hours"] == 24
                    assert len(result["new_releases"]) == 1
                    
                    release = result["new_releases"][0]
                    assert release["name"] == "test-package"
                    assert release["summary"] == "A test package"
                    assert "categories" in release

    @pytest.mark.asyncio
    async def test_monitor_with_filters(self):
        """Test monitoring with various filters."""
        mock_releases = [
            {
                "name": "web-package",
                "version": "1.0.0",
                "release_time": "2023-01-01T12:00:00Z",
                "description": "Web framework",
                "link": "https://pypi.org/project/web-package/",
            },
            {
                "name": "data-package",
                "version": "2.0.0",
                "release_time": "2023-01-01T13:00:00Z",
                "description": "Data science package",
                "link": "https://pypi.org/project/data-package/",
            }
        ]
        
        with patch("pypi_query_mcp.tools.discovery._fetch_recent_releases_from_rss") as mock_fetch:
            mock_fetch.return_value = mock_releases
            
            with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                def mock_get_package_info(package_name):
                    if package_name == "web-package":
                        return {
                            "info": {
                                "name": "web-package",
                                "author": "Web Author",
                                "summary": "Web framework",
                                "license": "MIT",
                            }
                        }
                    elif package_name == "data-package":
                        return {
                            "info": {
                                "name": "data-package", 
                                "author": "Data Author",
                                "summary": "Data science package",
                                "license": "Apache",
                            }
                        }
                
                mock_client.get_package_info.side_effect = mock_get_package_info
                
                with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                    def mock_categorize_func(info):
                        if "web" in info.get("summary", "").lower():
                            return ["web"]
                        elif "data" in info.get("summary", "").lower():
                            return ["data-science"]
                        return ["general"]
                    
                    mock_categorize.side_effect = mock_categorize_func
                    
                    # Test category filtering
                    result = await monitor_pypi_new_releases(
                        categories=["web"],
                        hours=24
                    )
                    
                    assert result["total_releases_found"] == 1
                    assert result["new_releases"][0]["name"] == "web-package"
                    
                    # Test maintainer filtering
                    result = await monitor_pypi_new_releases(
                        maintainer_filter="Web Author",
                        hours=24
                    )
                    
                    assert result["total_releases_found"] == 1
                    assert result["new_releases"][0]["name"] == "web-package"

    @pytest.mark.asyncio
    async def test_monitor_cache_functionality(self):
        """Test cache functionality in monitoring."""
        # Clear cache first
        _discovery_cache.clear()
        
        mock_releases = [
            {
                "name": "cached-package",
                "version": "1.0.0",
                "release_time": "2023-01-01T12:00:00Z",
                "description": "Cached package",
                "link": "https://pypi.org/project/cached-package/",
            }
        ]
        
        with patch("pypi_query_mcp.tools.discovery._fetch_recent_releases_from_rss") as mock_fetch:
            mock_fetch.return_value = mock_releases
            
            with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get_package_info.return_value = {
                    "info": {
                        "name": "cached-package",
                        "summary": "Cached package",
                        "author": "Cache Author",
                    }
                }
                
                with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                    mock_categorize.return_value = ["general"]
                    
                    # First call should fetch data
                    result1 = await monitor_pypi_new_releases(hours=24, cache_ttl=300)
                    assert mock_fetch.call_count == 1
                    
                    # Second call with same parameters should use cache
                    result2 = await monitor_pypi_new_releases(hours=24, cache_ttl=300)
                    assert mock_fetch.call_count == 1  # Should not increase
                    
                    # Results should be identical
                    assert result1["timestamp"] == result2["timestamp"]

    @pytest.mark.asyncio
    async def test_monitor_error_handling(self):
        """Test error handling in monitoring."""
        with patch("pypi_query_mcp.tools.discovery._fetch_recent_releases_from_rss") as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")
            
            with pytest.raises(NetworkError):
                await monitor_pypi_new_releases(hours=24)


class TestGetPyPITrendingToday:
    """Test the get_pypi_trending_today function."""

    @pytest.mark.asyncio
    async def test_trending_basic_functionality(self):
        """Test basic trending analysis."""
        mock_releases_result = {
            "new_releases": [
                {
                    "name": "trending-package",
                    "version": "1.0.0",
                    "summary": "Trending package",
                    "categories": ["web"],
                    "release_time": "2023-01-01T12:00:00Z",
                }
            ]
        }
        
        mock_trending_result = {
            "trending_packages": [
                {
                    "package": "popular-package",
                    "downloads": {"last_day": 10000},
                    "summary": "Popular package",
                }
            ]
        }
        
        with patch("pypi_query_mcp.tools.discovery.monitor_pypi_new_releases") as mock_monitor:
            mock_monitor.return_value = mock_releases_result
            
            with patch("pypi_query_mcp.tools.search.get_trending_packages") as mock_trending:
                mock_trending.return_value = mock_trending_result
                
                with patch("pypi_query_mcp.tools.discovery._enhance_trending_analysis") as mock_enhance:
                    mock_enhance.return_value = [
                        {
                            "name": "trending-package",
                            "trending_score": 10.0,
                            "trending_reason": "new_release",
                        },
                        {
                            "name": "popular-package",
                            "trending_score": 8.0,
                            "trending_reason": "download_surge",
                        }
                    ]
                    
                    result = await get_pypi_trending_today(
                        category="web",
                        limit=10
                    )
                    
                    assert "trending_today" in result
                    assert result["total_trending"] == 2
                    assert result["category"] == "web"
                    assert len(result["trending_today"]) == 2

    @pytest.mark.asyncio
    async def test_trending_with_filters(self):
        """Test trending analysis with filters."""
        with patch("pypi_query_mcp.tools.discovery.monitor_pypi_new_releases") as mock_monitor:
            mock_monitor.return_value = {"new_releases": []}
            
            with patch("pypi_query_mcp.tools.search.get_trending_packages") as mock_trending:
                mock_trending.return_value = {"trending_packages": []}
                
                with patch("pypi_query_mcp.tools.discovery._enhance_trending_analysis") as mock_enhance:
                    mock_enhance.return_value = []
                    
                    result = await get_pypi_trending_today(
                        category="ai",
                        min_downloads=5000,
                        limit=20,
                        include_new_packages=False,
                        trending_threshold=2.0
                    )
                    
                    assert result["category"] == "ai"
                    assert result["filters_applied"]["min_downloads"] == 5000
                    assert result["filters_applied"]["trending_threshold"] == 2.0
                    assert not result["filters_applied"]["include_new_packages"]

    @pytest.mark.asyncio
    async def test_trending_error_handling(self):
        """Test error handling in trending analysis."""
        with patch("pypi_query_mcp.tools.discovery.monitor_pypi_new_releases") as mock_monitor:
            mock_monitor.side_effect = Exception("Monitoring error")
            
            with pytest.raises(SearchError):
                await get_pypi_trending_today()


class TestSearchPyPIByMaintainer:
    """Test the search_pypi_by_maintainer function."""

    @pytest.mark.asyncio
    async def test_search_by_maintainer_basic(self):
        """Test basic maintainer search functionality."""
        mock_search_results = {
            "packages": [
                {
                    "name": "maintainer-package-1",
                    "summary": "First package",
                },
                {
                    "name": "maintainer-package-2", 
                    "summary": "Second package",
                }
            ]
        }
        
        mock_package_info = {
            "info": {
                "name": "maintainer-package-1",
                "version": "1.0.0",
                "summary": "First package",
                "author": "Test Maintainer",
                "author_email": "test@example.com",
                "license": "MIT",
                "keywords": "test",
                "classifiers": [],
                "requires_python": ">=3.8",
            }
        }
        
        with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
            mock_search.return_value = mock_search_results
            
            with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get_package_info.return_value = mock_package_info
                
                with patch("pypi_query_mcp.tools.discovery._is_package_maintainer") as mock_is_maintainer:
                    mock_is_maintainer.return_value = True
                    
                    with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                        mock_categorize.return_value = ["development"]
                        
                        result = await search_pypi_by_maintainer(
                            maintainer="Test Maintainer",
                            sort_by="popularity"
                        )
                        
                        assert result["maintainer"] == "Test Maintainer"
                        assert result["total_packages"] == 1
                        assert len(result["packages"]) == 1
                        assert "portfolio_analysis" in result
                        assert "maintainer_profile" in result

    @pytest.mark.asyncio
    async def test_search_by_maintainer_invalid_input(self):
        """Test maintainer search with invalid input."""
        with pytest.raises(InvalidPackageNameError):
            await search_pypi_by_maintainer("")
        
        with pytest.raises(InvalidPackageNameError):
            await search_pypi_by_maintainer("   ")

    @pytest.mark.asyncio
    async def test_search_by_maintainer_with_stats(self):
        """Test maintainer search with download statistics."""
        mock_search_results = {"packages": [{"name": "stats-package"}]}
        mock_package_info = {
            "info": {
                "name": "stats-package",
                "version": "1.0.0",
                "author": "Stats Maintainer",
                "summary": "Package with stats",
            }
        }
        mock_stats = {
            "recent_downloads": {
                "last_month": 50000,
                "last_week": 12000,
                "last_day": 2000,
            }
        }
        
        with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
            mock_search.return_value = mock_search_results
            
            with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get_package_info.return_value = mock_package_info
                
                with patch("pypi_query_mcp.tools.discovery._is_package_maintainer") as mock_is_maintainer:
                    mock_is_maintainer.return_value = True
                    
                    with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                        mock_categorize.return_value = ["general"]
                        
                        with patch("pypi_query_mcp.tools.download_stats.get_package_download_stats") as mock_get_stats:
                            mock_get_stats.return_value = mock_stats
                            
                            result = await search_pypi_by_maintainer(
                                maintainer="Stats Maintainer",
                                include_stats=True
                            )
                            
                            assert result["total_packages"] == 1
                            package = result["packages"][0]
                            assert "download_stats" in package
                            assert package["download_stats"]["last_month"] == 50000

    @pytest.mark.asyncio
    async def test_search_by_maintainer_error_handling(self):
        """Test error handling in maintainer search."""
        with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
            mock_search.side_effect = Exception("Search error")
            
            with pytest.raises(SearchError):
                await search_pypi_by_maintainer("Error Maintainer")


class TestGetPyPIPackageRecommendations:
    """Test the get_pypi_package_recommendations function."""

    @pytest.mark.asyncio
    async def test_recommendations_basic_functionality(self):
        """Test basic recommendation functionality."""
        mock_package_info = {
            "info": {
                "name": "base-package",
                "version": "1.0.0",
                "summary": "Base package for recommendations",
                "keywords": "test, recommendations",
                "classifiers": ["Topic :: Software Development"],
            }
        }
        
        with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_info
            
            with patch("pypi_query_mcp.tools.discovery._find_similar_packages") as mock_similar:
                mock_similar.return_value = [
                    {
                        "name": "similar-package",
                        "type": "similar",
                        "confidence": 0.8,
                        "reason": "Similar functionality",
                    }
                ]
                
                with patch("pypi_query_mcp.tools.discovery._enhance_recommendations") as mock_enhance:
                    mock_enhance.return_value = [
                        {
                            "name": "similar-package",
                            "type": "similar",
                            "confidence": 0.8,
                            "summary": "Similar package",
                            "categories": ["development"],
                        }
                    ]
                    
                    with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                        mock_categorize.return_value = ["development"]
                        
                        result = await get_pypi_package_recommendations(
                            package_name="base-package",
                            recommendation_type="similar"
                        )
                        
                        assert result["base_package"]["name"] == "base-package"
                        assert result["total_recommendations"] == 1
                        assert result["recommendation_type"] == "similar"
                        assert len(result["recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_recommendations_different_types(self):
        """Test different recommendation types."""
        mock_package_info = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "Test package",
            }
        }
        
        with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_info
            
            with patch("pypi_query_mcp.tools.discovery._find_complementary_packages") as mock_complementary:
                mock_complementary.return_value = [
                    {
                        "name": "complementary-package",
                        "type": "complementary",
                        "confidence": 0.9,
                    }
                ]
                
                with patch("pypi_query_mcp.tools.discovery._enhance_recommendations") as mock_enhance:
                    mock_enhance.return_value = [
                        {
                            "name": "complementary-package",
                            "type": "complementary",
                            "confidence": 0.9,
                        }
                    ]
                    
                    with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                        mock_categorize.return_value = ["general"]
                        
                        result = await get_pypi_package_recommendations(
                            package_name="test-package",
                            recommendation_type="complementary"
                        )
                        
                        assert result["recommendation_type"] == "complementary"
                        assert result["total_recommendations"] == 1

    @pytest.mark.asyncio
    async def test_recommendations_with_user_context(self):
        """Test recommendations with user context."""
        mock_package_info = {
            "info": {
                "name": "context-package",
                "version": "1.0.0",
                "summary": "Package with context",
            }
        }
        
        user_context = {
            "experience_level": "beginner",
            "use_case": "web development",
        }
        
        with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.return_value = mock_package_info
            
            with patch("pypi_query_mcp.tools.discovery._find_similar_packages") as mock_similar:
                mock_similar.return_value = []
                
                with patch("pypi_query_mcp.tools.discovery._enhance_recommendations") as mock_enhance:
                    mock_enhance.return_value = []
                    
                    with patch("pypi_query_mcp.tools.discovery._categorize_package") as mock_categorize:
                        mock_categorize.return_value = ["web"]
                        
                        result = await get_pypi_package_recommendations(
                            package_name="context-package",
                            user_context=user_context
                        )
                        
                        assert result["parameters"]["user_context"] == user_context
                        assert result["algorithm_insights"]["personalization_applied"] == True

    @pytest.mark.asyncio
    async def test_recommendations_invalid_input(self):
        """Test recommendations with invalid input."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_recommendations("")
        
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_recommendations("   ")

    @pytest.mark.asyncio
    async def test_recommendations_error_handling(self):
        """Test error handling in recommendations."""
        with patch("pypi_query_mcp.tools.discovery.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_package_info.side_effect = Exception("Package error")
            
            with pytest.raises(SearchError):
                await get_pypi_package_recommendations("error-package")


class TestHelperFunctions:
    """Test helper functions used by discovery tools."""

    def test_categorize_package(self):
        """Test package categorization."""
        # Test with classifiers
        package_info = {
            "summary": "Web framework for Python",
            "description": "A micro web framework",
            "keywords": "web, framework, api",
            "classifiers": [
                "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
                "Topic :: Software Development :: Libraries :: Python Modules"
            ],
        }
        
        with patch("pypi_query_mcp.tools.discovery._categorize_package", return_value=["web", "internet"]):
            categories = _categorize_package(package_info)
            assert "web" in categories

    def test_is_package_maintainer(self):
        """Test maintainer checking functionality."""
        package_info = {
            "author": "John Doe",
            "author_email": "john@example.com",
            "maintainer": "Jane Smith",
            "maintainer_email": "jane@example.com",
        }
        
        # Test author match
        assert _is_package_maintainer(package_info, "John Doe", False) == True
        assert _is_package_maintainer(package_info, "john doe", False) == True
        
        # Test maintainer match
        assert _is_package_maintainer(package_info, "Jane Smith", False) == True
        
        # Test no match
        assert _is_package_maintainer(package_info, "Bob Wilson", False) == False
        
        # Test email match (when enabled)
        assert _is_package_maintainer(package_info, "john@example.com", True) == True
        assert _is_package_maintainer(package_info, "john@example.com", False) == False


@pytest.fixture
def mock_rss_response():
    """Mock RSS response for testing."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>PyPI Recent Updates</title>
            <item>
                <title>test-package 1.0.0</title>
                <description>Test package description</description>
                <link>https://pypi.org/project/test-package/</link>
                <pubDate>Mon, 01 Jan 2023 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>'''


class TestIntegration:
    """Integration tests for discovery tools."""

    @pytest.mark.asyncio
    async def test_full_workflow_monitoring_to_recommendations(self):
        """Test full workflow from monitoring to recommendations."""
        # This would be a more complex integration test
        # that combines multiple functions in a realistic workflow
        pass

    @pytest.mark.asyncio
    async def test_cache_consistency_across_functions(self):
        """Test cache consistency across different discovery functions."""
        # Clear cache first
        _discovery_cache.clear()
        
        # Test that cache is properly shared between functions
        with patch("pypi_query_mcp.tools.discovery._fetch_recent_releases_from_rss") as mock_fetch:
            mock_fetch.return_value = []
            
            # First call should populate cache
            await monitor_pypi_new_releases(hours=24, cache_ttl=300)
            assert mock_fetch.call_count == 1
            
            # Second call should use cache
            await monitor_pypi_new_releases(hours=24, cache_ttl=300)
            assert mock_fetch.call_count == 1  # Should not increase

    def test_error_propagation(self):
        """Test that errors are properly propagated and handled."""
        # Test various error scenarios and ensure they're handled consistently
        pass


# Additional test classes for edge cases and performance testing could be added here
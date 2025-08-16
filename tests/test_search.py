"""Tests for PyPI search functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from pypi_query_mcp.core.search_client import PyPISearchClient, SearchFilter, SearchSort
from pypi_query_mcp.tools.search import (
    find_alternatives,
    get_trending_packages,
    search_by_category, 
    search_packages,
)


class TestSearchPackages:
    """Test the search_packages function."""

    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Test basic package search functionality."""
        # Mock the search client
        with patch("pypi_query_mcp.tools.search.PyPISearchClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_result = {
                "query": "flask",
                "total_found": 5,
                "filtered_count": 5,
                "returned_count": 5,
                "packages": [
                    {
                        "name": "Flask",
                        "summary": "A micro web framework",
                        "version": "2.3.3",
                        "license_type": "bsd",
                        "categories": ["web"],
                        "quality_score": 95.0,
                    }
                ],
                "filters_applied": {},
                "sort_applied": {"field": "relevance", "reverse": True},
                "semantic_search": False,
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_client.search_packages.return_value = mock_result
            
            result = await search_packages(query="flask", limit=20)
            
            assert result["query"] == "flask"
            assert len(result["packages"]) == 1
            assert result["packages"][0]["name"] == "Flask"
            mock_client.search_packages.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with filtering options."""
        with patch("pypi_query_mcp.tools.search.PyPISearchClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_result = {
                "query": "web framework",
                "total_found": 10,
                "filtered_count": 3,
                "returned_count": 3,
                "packages": [
                    {"name": "Flask", "license_type": "bsd", "categories": ["web"]},
                    {"name": "Django", "license_type": "bsd", "categories": ["web"]},
                    {"name": "FastAPI", "license_type": "mit", "categories": ["web"]},
                ],
                "filters_applied": {
                    "python_versions": ["3.9"],
                    "licenses": ["mit", "bsd"],
                    "categories": ["web"],
                    "min_downloads": 1000,
                },
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_client.search_packages.return_value = mock_result
            
            result = await search_packages(
                query="web framework",
                python_versions=["3.9"],
                licenses=["mit", "bsd"],
                categories=["web"],
                min_downloads=1000,
            )
            
            assert result["filtered_count"] == 3
            assert all(pkg["categories"] == ["web"] for pkg in result["packages"])

    @pytest.mark.asyncio
    async def test_empty_query_error(self):
        """Test that empty query raises appropriate error."""
        from pypi_query_mcp.core.exceptions import InvalidPackageNameError
        
        with pytest.raises(InvalidPackageNameError):
            await search_packages(query="")

    @pytest.mark.asyncio
    async def test_search_with_semantic_search(self):
        """Test search with semantic search enabled."""
        with patch("pypi_query_mcp.tools.search.PyPISearchClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_result = {
                "query": "machine learning",
                "packages": [
                    {"name": "scikit-learn", "semantic_score": 0.95},
                    {"name": "pandas", "semantic_score": 0.80},
                ],
                "semantic_search": True,
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_client.search_packages.return_value = mock_result
            
            result = await search_packages(
                query="machine learning",
                semantic_search=True,
            )
            
            assert result["semantic_search"] is True
            assert result["packages"][0]["semantic_score"] == 0.95


class TestSearchByCategory:
    """Test the search_by_category function."""

    @pytest.mark.asyncio
    async def test_web_category_search(self):
        """Test searching for web packages."""
        with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
            mock_result = {
                "query": "web framework flask django fastapi",
                "packages": [
                    {"name": "Flask", "categories": ["web"]},
                    {"name": "Django", "categories": ["web"]},
                ],
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_search.return_value = mock_result
            
            result = await search_by_category(category="web", limit=10)
            
            assert len(result["packages"]) == 2
            mock_search.assert_called_once_with(
                query="web framework flask django fastapi",
                limit=10,
                categories=["web"],
                python_versions=None,
                sort_by="popularity",
                semantic_search=True,
            )

    @pytest.mark.asyncio
    async def test_data_science_category(self):
        """Test searching for data science packages."""
        with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
            mock_result = {
                "query": "data science machine learning pandas numpy",
                "packages": [
                    {"name": "pandas", "categories": ["data-science"]},
                    {"name": "numpy", "categories": ["data-science"]},
                ],
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_search.return_value = mock_result
            
            result = await search_by_category(
                category="data-science", 
                python_version="3.10"
            )
            
            mock_search.assert_called_once_with(
                query="data science machine learning pandas numpy",
                limit=20,
                categories=["data-science"],
                python_versions=["3.10"],
                sort_by="popularity",
                semantic_search=True,
            )


class TestFindAlternatives:
    """Test the find_alternatives function."""

    @pytest.mark.asyncio
    async def test_find_flask_alternatives(self):
        """Test finding alternatives to Flask."""
        with patch("pypi_query_mcp.core.pypi_client.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock Flask package data
            mock_flask_data = {
                "info": {
                    "name": "Flask",
                    "summary": "A micro web framework",
                    "keywords": "web framework micro",
                    "classifiers": [
                        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
                        "Topic :: Software Development :: Libraries :: Application Frameworks",
                    ],
                }
            }
            
            mock_client.get_package_info.return_value = mock_flask_data
            
            with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
                mock_search_result = {
                    "packages": [
                        {"name": "Django", "summary": "High-level web framework"},
                        {"name": "FastAPI", "summary": "Modern web framework"},
                        {"name": "Flask", "summary": "A micro web framework"},  # Original package
                        {"name": "Bottle", "summary": "Micro web framework"},
                    ],
                    "timestamp": "2023-01-01T00:00:00Z",
                }
                
                mock_search.return_value = mock_search_result
                
                result = await find_alternatives(
                    package_name="Flask",
                    limit=5,
                    include_similar=True,
                )
                
                # Should exclude the original Flask package
                assert result["target_package"]["name"] == "Flask"
                assert len(result["alternatives"]) == 3
                assert not any(alt["name"] == "Flask" for alt in result["alternatives"])
                assert result["analysis"]["semantic_search_used"] is True

    @pytest.mark.asyncio 
    async def test_alternatives_with_keywords(self):
        """Test alternatives finding using package keywords."""
        with patch("pypi_query_mcp.core.pypi_client.PyPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_package_data = {
                "info": {
                    "name": "requests",
                    "summary": "HTTP library for Python",
                    "keywords": "http client requests api",
                    "classifiers": ["Topic :: Internet :: WWW/HTTP"],
                }
            }
            
            mock_client.get_package_info.return_value = mock_package_data
            
            with patch("pypi_query_mcp.tools.search.search_packages") as mock_search:
                mock_search.return_value = {
                    "packages": [
                        {"name": "httpx", "summary": "Next generation HTTP client"},
                        {"name": "urllib3", "summary": "HTTP library with connection pooling"},
                    ],
                    "timestamp": "2023-01-01T00:00:00Z",
                }
                
                result = await find_alternatives(package_name="requests")
                
                assert "http client requests api" in result["search_query_used"]
                assert result["analysis"]["search_method"] == "keyword_similarity"


class TestGetTrendingPackages:
    """Test the get_trending_packages function."""

    @pytest.mark.asyncio
    async def test_get_trending_all_categories(self):
        """Test getting trending packages across all categories."""
        with patch("pypi_query_mcp.tools.download_stats.get_top_packages_by_downloads") as mock_top_packages:
            mock_result = {
                "top_packages": [
                    {"package": "requests", "downloads": 1000000},
                    {"package": "urllib3", "downloads": 900000},
                    {"package": "certifi", "downloads": 800000},
                ],
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_top_packages.return_value = mock_result
            
            result = await get_trending_packages(
                time_period="week",
                limit=10,
            )
            
            assert result["time_period"] == "week"
            assert result["category"] is None
            assert len(result["trending_packages"]) == 3
            assert result["analysis"]["category_filtered"] is False

    @pytest.mark.asyncio
    async def test_get_trending_by_category(self):
        """Test getting trending packages filtered by category."""
        with patch("pypi_query_mcp.tools.download_stats.get_top_packages_by_downloads") as mock_top_packages:
            mock_result = {
                "top_packages": [
                    {"package": "flask", "downloads": 500000},
                    {"package": "django", "downloads": 400000},
                    {"package": "requests", "downloads": 1000000},  # Should be filtered out
                ],
                "timestamp": "2023-01-01T00:00:00Z",
            }
            
            mock_top_packages.return_value = mock_result
            
            # Mock PyPI client for package metadata
            with patch("pypi_query_mcp.core.pypi_client.PyPIClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                
                def mock_get_package_info(package_name):
                    if package_name == "flask":
                        return {
                            "info": {
                                "keywords": "web framework micro",
                                "summary": "A micro web framework",
                            }
                        }
                    elif package_name == "django":
                        return {
                            "info": {
                                "keywords": "web framework",
                                "summary": "High-level web framework",
                            }
                        }
                    else:
                        return {
                            "info": {
                                "keywords": "http client",
                                "summary": "HTTP library",
                            }
                        }
                
                mock_client.get_package_info.side_effect = mock_get_package_info
                
                result = await get_trending_packages(
                    category="web",
                    time_period="month",
                    limit=5,
                )
                
                assert result["category"] == "web"
                assert result["analysis"]["category_filtered"] is True
                # Should only include web packages (flask, django)
                assert len(result["trending_packages"]) == 2


class TestSearchClient:
    """Test the PyPISearchClient class."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test that the search client works as an async context manager."""
        async with PyPISearchClient() as client:
            assert client is not None
            assert hasattr(client, 'search_packages')

    def test_search_filter_creation(self):
        """Test SearchFilter creation."""
        filters = SearchFilter(
            python_versions=["3.9", "3.10"],
            licenses=["mit", "apache"],
            categories=["web", "data-science"],
            min_downloads=1000,
        )
        
        assert filters.python_versions == ["3.9", "3.10"]
        assert filters.licenses == ["mit", "apache"]
        assert filters.categories == ["web", "data-science"]
        assert filters.min_downloads == 1000

    def test_search_sort_creation(self):
        """Test SearchSort creation."""
        sort = SearchSort(field="popularity", reverse=True)
        
        assert sort.field == "popularity"
        assert sort.reverse is True
        
        # Test defaults
        default_sort = SearchSort()
        assert default_sort.field == "relevance"
        assert default_sort.reverse is True
"""Tests for PyPI analytics functionality."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from pypi_query_mcp.core.exceptions import InvalidPackageNameError, PackageNotFoundError
from pypi_query_mcp.tools.analytics import (
    analyze_pypi_competition,
    get_pypi_package_analytics,
    get_pypi_package_rankings,
    get_pypi_security_alerts,
    _analyze_growth_patterns,
    _assess_data_reliability,
    _calculate_quality_score,
    _extract_search_terms,
    _filter_vulnerabilities_by_severity,
    _generate_insights,
)


class TestGetPyPIPackageAnalytics:
    """Test comprehensive package analytics functionality."""

    @pytest.fixture
    def mock_package_data(self):
        """Mock package data for testing."""
        return {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "A test package for analytics",
                "description": "A comprehensive test package with detailed description for analytics testing",
                "keywords": "test, analytics, package",
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
                },
                "requires_python": ">=3.8",
                "requires_dist": ["requests>=2.25.0", "click>=7.0"],
            },
            "releases": {
                "1.0.0": [{"upload_time_iso_8601": "2024-01-15T10:00:00Z"}],
                "0.9.0": [{"upload_time_iso_8601": "2023-12-01T10:00:00Z"}],
            },
        }

    @pytest.fixture
    def mock_download_stats(self):
        """Mock download statistics for testing."""
        return {
            "downloads": {
                "last_day": 1000,
                "last_week": 7000,
                "last_month": 30000,
            },
            "analysis": {
                "total_downloads": 38000,
                "growth_indicators": {
                    "daily_vs_weekly": 1.0,
                    "weekly_vs_monthly": 0.93,
                },
            },
        }

    @pytest.mark.asyncio
    async def test_get_package_analytics_success(self, mock_package_data, mock_download_stats):
        """Test successful package analytics retrieval."""
        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.get_package_download_stats") as mock_download_stats_func,
            patch("pypi_query_mcp.tools.analytics.get_package_download_trends") as mock_download_trends_func,
        ):
            # Setup mocks
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = mock_package_data
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_download_stats_func.return_value = mock_download_stats
            mock_download_trends_func.return_value = {
                "trend_analysis": {"trend_direction": "increasing"}
            }

            # Call function
            result = await get_pypi_package_analytics("test-package")

            # Assertions
            assert result["package"] == "test-package"
            assert "analysis_timestamp" in result
            assert result["time_period"] == "month"
            assert "metadata" in result
            assert "download_analytics" in result
            assert "quality_metrics" in result
            assert "insights" in result
            assert "data_reliability" in result

            # Check metadata
            metadata = result["metadata"]
            assert metadata["name"] == "test-package"
            assert metadata["version"] == "1.0.0"
            assert metadata["author"] == "Test Author"

            # Check quality metrics
            quality_metrics = result["quality_metrics"]
            assert "quality_score" in quality_metrics
            assert quality_metrics["has_description"] is True
            assert quality_metrics["has_keywords"] is True

    @pytest.mark.asyncio
    async def test_get_package_analytics_invalid_package_name(self):
        """Test analytics with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_analytics("")

        with pytest.raises(InvalidPackageNameError):
            await get_pypi_package_analytics("   ")

    @pytest.mark.asyncio
    async def test_get_package_analytics_minimal_options(self, mock_package_data):
        """Test analytics with minimal options."""
        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.get_package_download_stats") as mock_download_stats_func,
        ):
            # Setup mocks
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = mock_package_data
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_download_stats_func.return_value = {"downloads": {"last_day": 100}}

            # Call function with minimal options
            result = await get_pypi_package_analytics(
                "test-package",
                include_historical=False,
                include_platform_breakdown=False,
                include_version_analytics=False,
            )

            # Should not include optional sections
            assert "version_analytics" not in result
            assert "platform_analytics" not in result


class TestGetPyPISecurityAlerts:
    """Test security alerts functionality."""

    @pytest.fixture
    def mock_osv_response(self):
        """Mock OSV API response."""
        return {
            "vulns": [
                {
                    "id": "GHSA-xxxx-xxxx-xxxx",
                    "summary": "Test vulnerability",
                    "details": "This is a test vulnerability",
                    "affected": [{"package": {"name": "test-package", "ecosystem": "PyPI"}}],
                    "database_specific": {"severity": "HIGH"},
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_security_alerts_success(self, mock_osv_response):
        """Test successful security alerts retrieval."""
        with (
            patch("httpx.AsyncClient") as mock_httpx_client,
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
        ):
            # Setup OSV API mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_osv_response
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

            # Setup PyPI client mock
            mock_pypi_client_instance = AsyncMock()
            mock_pypi_client_instance.get_package_info.return_value = {
                "info": {"name": "test-package", "license": "MIT"}
            }
            mock_pypi_client.return_value.__aenter__.return_value = mock_pypi_client_instance

            # Call function
            result = await get_pypi_security_alerts("test-package")

            # Assertions
            assert result["package"] == "test-package"
            assert "scan_timestamp" in result
            assert "security_score" in result
            assert "vulnerabilities" in result
            assert "recommendations" in result

            # Check vulnerabilities
            vulns = result["vulnerabilities"]
            assert vulns["vulnerability_count"] == 1
            assert len(vulns["vulnerabilities"]) == 1
            assert vulns["vulnerabilities"][0]["id"] == "GHSA-xxxx-xxxx-xxxx"

    @pytest.mark.asyncio
    async def test_get_security_alerts_no_vulnerabilities(self):
        """Test security alerts when no vulnerabilities found."""
        with (
            patch("httpx.AsyncClient") as mock_httpx_client,
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
        ):
            # Setup OSV API mock with no vulnerabilities
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"vulns": []}
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

            # Setup PyPI client mock
            mock_pypi_client_instance = AsyncMock()
            mock_pypi_client_instance.get_package_info.return_value = {
                "info": {"name": "test-package", "license": "MIT"}
            }
            mock_pypi_client.return_value.__aenter__.return_value = mock_pypi_client_instance

            # Call function
            result = await get_pypi_security_alerts("test-package")

            # Should have no vulnerabilities but still provide security analysis
            assert result["vulnerabilities"]["vulnerability_count"] == 0
            assert len(result["vulnerabilities"]["vulnerabilities"]) == 0
            assert "security_score" in result

    @pytest.mark.asyncio
    async def test_get_security_alerts_with_severity_filter(self, mock_osv_response):
        """Test security alerts with severity filtering."""
        # Add different severity vulnerabilities
        mock_osv_response["vulns"].append({
            "id": "GHSA-yyyy-yyyy-yyyy",
            "summary": "Low severity vulnerability",
            "database_specific": {"severity": "LOW"},
        })

        with (
            patch("httpx.AsyncClient") as mock_httpx_client,
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
        ):
            # Setup mocks
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_osv_response
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

            mock_pypi_client_instance = AsyncMock()
            mock_pypi_client_instance.get_package_info.return_value = {
                "info": {"name": "test-package"}
            }
            mock_pypi_client.return_value.__aenter__.return_value = mock_pypi_client_instance

            # Call function with HIGH severity filter
            result = await get_pypi_security_alerts("test-package", severity_filter="HIGH")

            # Should only include HIGH severity vulnerabilities
            vulns = result["vulnerabilities"]["vulnerabilities"]
            assert len(vulns) == 1
            assert vulns[0]["database_specific"]["severity"] == "HIGH"

    @pytest.mark.asyncio
    async def test_get_security_alerts_invalid_package_name(self):
        """Test security alerts with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await get_pypi_security_alerts("")


class TestGetPyPIPackageRankings:
    """Test package rankings functionality."""

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing."""
        return {
            "packages": [
                {"name": "popular-package", "summary": "A popular package"},
                {"name": "test-package", "summary": "Test package"},
                {"name": "another-package", "summary": "Another package"},
            ]
        }

    @pytest.mark.asyncio
    async def test_get_package_rankings_success(self, mock_search_results):
        """Test successful package rankings analysis."""
        mock_package_data = {
            "info": {
                "name": "test-package",
                "summary": "A test package for ranking analysis",
                "keywords": "test, ranking, analysis",
                "classifiers": ["Topic :: Software Development"],
            }
        }

        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.search_packages") as mock_search,
        ):
            # Setup mocks
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = mock_package_data
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_search.return_value = mock_search_results

            # Call function
            result = await get_pypi_package_rankings("test-package")

            # Assertions
            assert result["package"] == "test-package"
            assert "ranking_score" in result
            assert "search_rankings" in result
            assert "competitor_analysis" in result
            assert "improvement_suggestions" in result

            # Check that search terms were extracted
            analysis_parameters = result["analysis_parameters"]
            assert "search_terms" in analysis_parameters
            assert len(analysis_parameters["search_terms"]) > 0

    @pytest.mark.asyncio
    async def test_get_package_rankings_with_custom_terms(self):
        """Test package rankings with custom search terms."""
        custom_terms = ["web", "framework", "python"]
        custom_competitors = ["flask", "django", "fastapi"]

        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.search_packages") as mock_search,
        ):
            # Setup mocks
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = {
                "info": {"name": "test-package"}
            }
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_search.return_value = {"packages": []}

            # Call function with custom parameters
            result = await get_pypi_package_rankings(
                "test-package",
                search_terms=custom_terms,
                competitor_packages=custom_competitors,
            )

            # Check that custom parameters were used
            analysis_parameters = result["analysis_parameters"]
            assert analysis_parameters["search_terms"] == custom_terms
            assert analysis_parameters["competitor_packages"] == custom_competitors


class TestAnalyzePyPICompetition:
    """Test competitive analysis functionality."""

    @pytest.fixture
    def mock_competitor_data(self):
        """Mock competitor package data."""
        return {
            "flask": {
                "info": {
                    "name": "flask",
                    "version": "2.3.0",
                    "summary": "A lightweight WSGI web application framework",
                    "keywords": "web, framework, wsgi",
                }
            },
            "django": {
                "info": {
                    "name": "django",
                    "version": "4.2.0",
                    "summary": "A high-level Python web framework",
                    "keywords": "web, framework, mvc",
                }
            },
        }

    @pytest.mark.asyncio
    async def test_analyze_competition_basic(self, mock_competitor_data):
        """Test basic competitive analysis."""
        target_package_data = {
            "info": {
                "name": "test-web-framework",
                "version": "1.0.0",
                "summary": "A test web framework",
                "keywords": "web, framework, test",
            }
        }

        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.get_package_download_stats") as mock_stats,
        ):
            # Setup mocks
            def mock_get_package_info(package_name):
                if package_name == "test-web-framework":
                    return target_package_data
                return mock_competitor_data.get(package_name, {})

            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.side_effect = mock_get_package_info
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_stats.return_value = {
                "downloads": {"last_month": 10000}
            }

            # Call function with basic analysis
            result = await analyze_pypi_competition(
                "test-web-framework",
                competitor_packages=["flask", "django"],
                analysis_depth="basic",
            )

            # Assertions
            assert result["package"] == "test-web-framework"
            assert result["analysis_depth"] == "basic"
            assert "basic_analysis" in result
            assert "strategic_recommendations" in result
            assert "competitive_strength" in result

            # Check competitor packages
            assert result["competitor_packages"] == ["flask", "django"]

    @pytest.mark.asyncio
    async def test_analyze_competition_comprehensive(self):
        """Test comprehensive competitive analysis."""
        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics._find_competitor_packages") as mock_find_competitors,
            patch("pypi_query_mcp.tools.analytics.get_package_download_stats") as mock_stats,
        ):
            # Setup mocks
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = {
                "info": {"name": "test-package", "version": "1.0.0"}
            }
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_find_competitors.return_value = ["competitor1", "competitor2"]
            mock_stats.return_value = {"downloads": {"last_month": 5000}}

            # Call function with comprehensive analysis
            result = await analyze_pypi_competition(
                "test-package",
                analysis_depth="comprehensive",
            )

            # Should include additional analysis sections
            assert "market_positioning" in result
            assert "adoption_trends" in result

    @pytest.mark.asyncio
    async def test_analyze_competition_invalid_package_name(self):
        """Test competitive analysis with invalid package name."""
        with pytest.raises(InvalidPackageNameError):
            await analyze_pypi_competition("")


class TestHelperFunctions:
    """Test helper functions used in analytics."""

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        # High quality package info
        high_quality_info = {
            "description": "A" * 1500,  # Long description
            "summary": "A comprehensive test package",  # Good summary
            "keywords": "test, analytics, package, quality",  # Keywords
            "classifiers": [f"Classifier :: {i}" for i in range(15)],  # Many classifiers
            "project_urls": {
                "Documentation": "https://docs.example.com",
                "Repository": "https://github.com/test/test",
                "Bug Tracker": "https://github.com/test/test/issues",
                "Changelog": "https://github.com/test/test/releases",
            },
            "license": "MIT",
            "author": "Test Author",
        }
        
        score = _calculate_quality_score(high_quality_info)
        assert score >= 80  # Should be high quality score

        # Low quality package info
        low_quality_info = {
            "description": "Short",
            "summary": "",
            "keywords": "",
            "classifiers": [],
            "project_urls": {},
            "license": "",
            "author": "",
        }
        
        score = _calculate_quality_score(low_quality_info)
        assert score <= 20  # Should be low quality score

    def test_extract_search_terms(self):
        """Test search terms extraction."""
        package_data = {
            "info": {
                "name": "test-web-framework",
                "keywords": "web, framework, wsgi, python",
                "summary": "A lightweight web framework for rapid development",
                "classifiers": [
                    "Topic :: Internet :: WWW/HTTP",
                    "Topic :: Software Development :: Libraries",
                ],
            }
        }
        
        terms = _extract_search_terms(package_data)
        
        assert "test-web-framework" in terms
        assert "web" in terms
        assert "framework" in terms
        assert len(terms) <= 10  # Should limit terms

    def test_filter_vulnerabilities_by_severity(self):
        """Test vulnerability filtering by severity."""
        vulnerabilities = {
            "vulnerabilities": [
                {"id": "vuln1", "database_specific": {"severity": "HIGH"}},
                {"id": "vuln2", "database_specific": {"severity": "LOW"}},
                {"id": "vuln3", "database_specific": {"severity": "HIGH"}},
                {"id": "vuln4", "withdrawn": True},  # Should be filtered out
            ],
            "vulnerability_count": 4,
        }
        
        # Filter by HIGH severity
        filtered = _filter_vulnerabilities_by_severity(
            vulnerabilities, "HIGH", include_historical=False
        )
        
        assert filtered["filtered_count"] == 2  # Only HIGH severity, non-withdrawn
        assert all(
            v["database_specific"]["severity"] == "HIGH" 
            for v in filtered["vulnerabilities"]
            if "database_specific" in v
        )

    def test_generate_insights(self):
        """Test insights generation."""
        download_analytics = {
            "current_stats": {
                "downloads": {"last_month": 150000}  # High traffic
            }
        }
        
        metadata = {"name": "test-package"}
        
        quality_metrics = {"quality_score": 85}  # High quality
        
        insights = _generate_insights(download_analytics, metadata, quality_metrics)
        
        assert "performance_insights" in insights
        assert "quality_insights" in insights
        assert "recommendations" in insights
        
        # Should identify high traffic
        performance_insights = insights["performance_insights"]
        assert any("High-traffic" in insight for insight in performance_insights)
        
        # Should identify good quality
        quality_insights = insights["quality_insights"]
        assert any("Well-documented" in insight for insight in quality_insights)

    def test_assess_data_reliability(self):
        """Test data reliability assessment."""
        # All operations successful
        all_successful = [{"data": "test"}, {"data": "test2"}]
        reliability = _assess_data_reliability(all_successful)
        
        assert reliability["reliability_score"] == 100.0
        assert reliability["status"] == "excellent"
        
        # Some operations failed
        mixed_results = [{"data": "test"}, Exception("error"), {"data": "test2"}]
        reliability = _assess_data_reliability(mixed_results)
        
        assert reliability["reliability_score"] < 100.0
        assert reliability["successful_operations"] == 2
        assert reliability["total_operations"] == 3

    def test_analyze_growth_patterns(self):
        """Test growth pattern analysis."""
        download_stats = {
            "downloads": {
                "last_day": 1000,
                "last_week": 7000,
                "last_month": 30000,
            }
        }
        
        download_trends = {
            "trend_analysis": {
                "trend_direction": "increasing",
                "peak_day": {"date": "2024-01-15", "downloads": 2000},
            }
        }
        
        growth_analysis = _analyze_growth_patterns(download_stats, download_trends)
        
        assert "growth_indicators" in growth_analysis
        assert "trend_assessment" in growth_analysis
        assert growth_analysis["trend_assessment"] == "increasing"
        
        # Check growth indicators
        indicators = growth_analysis["growth_indicators"]
        assert "daily_momentum" in indicators
        assert "weekly_momentum" in indicators


class TestIntegration:
    """Integration tests for analytics functionality."""

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self):
        """Test complete analytics workflow with mocked dependencies."""
        package_name = "requests"
        
        # Mock all external dependencies
        with (
            patch("pypi_query_mcp.tools.analytics.PyPIClient") as mock_pypi_client,
            patch("pypi_query_mcp.tools.analytics.get_package_download_stats") as mock_download_stats,
            patch("pypi_query_mcp.tools.analytics.get_package_download_trends") as mock_download_trends,
            patch("httpx.AsyncClient") as mock_httpx_client,
        ):
            # Setup comprehensive mocks
            mock_package_data = {
                "info": {
                    "name": package_name,
                    "version": "2.31.0",
                    "summary": "Python HTTP for Humans.",
                    "description": "A" * 2000,  # Long description
                    "keywords": "http, requests, python, web",
                    "classifiers": [f"Classifier :: {i}" for i in range(20)],
                    "license": "Apache 2.0",
                    "author": "Kenneth Reitz",
                    "project_urls": {
                        "Documentation": "https://docs.python-requests.org",
                        "Repository": "https://github.com/psf/requests",
                    },
                },
                "releases": {f"2.{i}.0": [{}] for i in range(30, 20, -1)},
            }
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get_package_info.return_value = mock_package_data
            mock_pypi_client.return_value.__aenter__.return_value = mock_client_instance
            
            mock_download_stats.return_value = {
                "downloads": {"last_month": 50000000},  # Very popular
                "analysis": {"total_downloads": 50000000}
            }
            
            mock_download_trends.return_value = {
                "trend_analysis": {"trend_direction": "increasing"}
            }
            
            # Mock OSV response (no vulnerabilities)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"vulns": []}
            
            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.post.return_value = mock_response
            mock_httpx_client.return_value.__aenter__.return_value = mock_httpx_instance

            # Test analytics
            analytics_result = await get_pypi_package_analytics(package_name)
            assert analytics_result["package"] == package_name
            assert analytics_result["quality_metrics"]["quality_score"] > 80

            # Test security alerts
            security_result = await get_pypi_security_alerts(package_name)
            assert security_result["package"] == package_name
            assert security_result["vulnerabilities"]["vulnerability_count"] == 0

            # Test rankings (with search mock)
            with patch("pypi_query_mcp.tools.analytics.search_packages") as mock_search:
                mock_search.return_value = {
                    "packages": [{"name": package_name}, {"name": "urllib3"}]
                }
                
                rankings_result = await get_pypi_package_rankings(package_name)
                assert rankings_result["package"] == package_name

            # Test competition analysis
            competition_result = await analyze_pypi_competition(
                package_name, 
                competitor_packages=["urllib3", "httpx"],
                analysis_depth="basic"
            )
            assert competition_result["package"] == package_name
            assert "competitive_strength" in competition_result
"""Tests for download statistics functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from pypi_query_mcp.tools.download_stats import (
    get_package_download_stats,
    get_package_download_trends,
    get_top_packages_by_downloads,
    _analyze_download_stats,
    _analyze_download_trends,
    _extract_download_count,
)
from pypi_query_mcp.core.exceptions import PackageNotFoundError, InvalidPackageNameError


class TestDownloadStats:
    """Test download statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_package_download_stats_success(self):
        """Test successful package download stats retrieval."""
        mock_stats_data = {
            "data": {
                "last_day": 1000,
                "last_week": 7000,
                "last_month": 30000,
            },
            "package": "test-package",
            "type": "recent_downloads",
        }

        mock_package_info = {
            "info": {
                "name": "test-package",
                "version": "1.0.0",
                "summary": "A test package",
                "author": "Test Author",
                "home_page": "https://example.com",
                "project_urls": {"Repository": "https://github.com/test/test-package"},
            }
        }

        with patch("pypi_query_mcp.tools.download_stats.PyPIStatsClient") as mock_stats_client, \
             patch("pypi_query_mcp.tools.download_stats.PyPIClient") as mock_pypi_client:
            
            # Setup mocks
            mock_stats_instance = AsyncMock()
            mock_stats_instance.get_recent_downloads.return_value = mock_stats_data
            mock_stats_client.return_value.__aenter__.return_value = mock_stats_instance

            mock_pypi_instance = AsyncMock()
            mock_pypi_instance.get_package_info.return_value = mock_package_info
            mock_pypi_client.return_value.__aenter__.return_value = mock_pypi_instance

            # Test the function
            result = await get_package_download_stats("test-package", "month")

            # Assertions
            assert result["package"] == "test-package"
            assert result["downloads"]["last_month"] == 30000
            assert result["metadata"]["name"] == "test-package"
            assert result["metadata"]["version"] == "1.0.0"
            assert result["period"] == "month"
            assert "analysis" in result
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_package_download_stats_package_not_found(self):
        """Test package download stats with non-existent package."""
        with patch("pypi_query_mcp.tools.download_stats.PyPIStatsClient") as mock_stats_client:
            mock_stats_instance = AsyncMock()
            mock_stats_instance.get_recent_downloads.side_effect = PackageNotFoundError("nonexistent")
            mock_stats_client.return_value.__aenter__.return_value = mock_stats_instance

            with pytest.raises(PackageNotFoundError):
                await get_package_download_stats("nonexistent", "month")

    @pytest.mark.asyncio
    async def test_get_package_download_trends_success(self):
        """Test successful package download trends retrieval."""
        mock_trends_data = {
            "data": [
                {"category": "without_mirrors", "date": "2024-01-01", "downloads": 1000},
                {"category": "without_mirrors", "date": "2024-01-02", "downloads": 1200},
                {"category": "with_mirrors", "date": "2024-01-01", "downloads": 1100},
                {"category": "with_mirrors", "date": "2024-01-02", "downloads": 1300},
            ],
            "package": "test-package",
            "type": "overall_downloads",
        }

        with patch("pypi_query_mcp.tools.download_stats.PyPIStatsClient") as mock_stats_client:
            mock_stats_instance = AsyncMock()
            mock_stats_instance.get_overall_downloads.return_value = mock_trends_data
            mock_stats_client.return_value.__aenter__.return_value = mock_stats_instance

            result = await get_package_download_trends("test-package", include_mirrors=False)

            assert result["package"] == "test-package"
            assert result["include_mirrors"] is False
            assert len(result["time_series"]) == 4
            assert "trend_analysis" in result
            assert result["trend_analysis"]["data_points"] == 2  # Only without_mirrors data

    @pytest.mark.asyncio
    async def test_get_top_packages_by_downloads_success(self):
        """Test successful top packages retrieval."""
        mock_stats_data = {
            "data": {
                "last_month": 50000000,
            },
            "package": "boto3",
            "type": "recent_downloads",
        }

        with patch("pypi_query_mcp.tools.download_stats.PyPIStatsClient") as mock_stats_client:
            mock_stats_instance = AsyncMock()
            mock_stats_instance.get_recent_downloads.return_value = mock_stats_data
            mock_stats_client.return_value.__aenter__.return_value = mock_stats_instance

            result = await get_top_packages_by_downloads("month", 5)

            assert "top_packages" in result
            assert result["period"] == "month"
            assert result["limit"] == 5
            assert len(result["top_packages"]) <= 5
            assert all("rank" in pkg for pkg in result["top_packages"])
            assert all("package" in pkg for pkg in result["top_packages"])
            assert all("downloads" in pkg for pkg in result["top_packages"])

    def test_analyze_download_stats(self):
        """Test download statistics analysis."""
        download_data = {
            "last_day": 1000,
            "last_week": 7000,
            "last_month": 30000,
        }

        analysis = _analyze_download_stats(download_data)

        assert analysis["total_downloads"] == 38000
        assert "last_day" in analysis["periods_available"]
        assert "last_week" in analysis["periods_available"]
        assert "last_month" in analysis["periods_available"]
        assert analysis["highest_period"] == "last_month"
        assert "growth_indicators" in analysis

    def test_analyze_download_stats_empty(self):
        """Test download statistics analysis with empty data."""
        analysis = _analyze_download_stats({})

        assert analysis["total_downloads"] == 0
        assert analysis["periods_available"] == []
        assert analysis["highest_period"] is None
        assert analysis["growth_indicators"] == {}

    def test_analyze_download_trends(self):
        """Test download trends analysis."""
        time_series_data = [
            {"category": "without_mirrors", "date": "2024-01-01", "downloads": 1000},
            {"category": "without_mirrors", "date": "2024-01-02", "downloads": 1200},
            {"category": "without_mirrors", "date": "2024-01-03", "downloads": 1100},
        ]

        analysis = _analyze_download_trends(time_series_data, include_mirrors=False)

        assert analysis["total_downloads"] == 3300
        assert analysis["data_points"] == 3
        assert analysis["average_daily"] == 1100.0
        assert analysis["peak_day"]["downloads"] == 1200
        assert analysis["peak_day"]["date"] == "2024-01-02"
        assert "date_range" in analysis

    def test_analyze_download_trends_empty(self):
        """Test download trends analysis with empty data."""
        analysis = _analyze_download_trends([], include_mirrors=False)

        assert analysis["total_downloads"] == 0
        assert analysis["data_points"] == 0
        assert analysis["average_daily"] == 0
        assert analysis["peak_day"] is None

    def test_extract_download_count(self):
        """Test download count extraction."""
        download_data = {
            "last_day": 1000,
            "last_week": 7000,
            "last_month": 30000,
        }

        assert _extract_download_count(download_data, "day") == 1000
        assert _extract_download_count(download_data, "week") == 7000
        assert _extract_download_count(download_data, "month") == 30000
        assert _extract_download_count(download_data, "year") == 0  # Not present

    def test_extract_download_count_empty(self):
        """Test download count extraction with empty data."""
        assert _extract_download_count({}, "month") == 0

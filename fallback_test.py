#!/usr/bin/env python3
"""Direct test of fallback mechanisms."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from pypi_query_mcp.core.stats_client import PyPIStatsClient


async def test_fallback():
    """Test fallback data generation directly."""
    print("Testing fallback data generation...")
    
    async with PyPIStatsClient() as client:
        # Force API failure tracking to trigger fallback
        client._api_health["consecutive_failures"] = 5  # Force fallback mode
        
        # Test recent downloads fallback
        fallback_recent = client._generate_fallback_recent_downloads("requests", "month")
        print(f"✅ Fallback recent downloads generated for requests:")
        print(f"   Source: {fallback_recent.get('source')}")
        print(f"   Downloads: {fallback_recent['data']['last_month']:,}")
        print(f"   Note: {fallback_recent.get('note')}")
        
        # Test overall downloads fallback  
        fallback_overall = client._generate_fallback_overall_downloads("numpy", False)
        print(f"\n✅ Fallback time series generated for numpy:")
        print(f"   Source: {fallback_overall.get('source')}")
        print(f"   Data points: {len(fallback_overall['data'])}")
        print(f"   Note: {fallback_overall.get('note')}")
        
        # Test the should_use_fallback logic
        should_fallback = client._should_use_fallback()
        print(f"\n✅ Fallback logic working: {should_fallback}")


if __name__ == "__main__":
    asyncio.run(test_fallback())
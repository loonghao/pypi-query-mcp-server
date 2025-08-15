#!/usr/bin/env python3
"""Quick test to verify fallback mechanism works."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from pypi_query_mcp.tools.download_stats import get_package_download_stats


async def quick_test():
    """Quick test with a single package."""
    print("Testing fallback mechanism with requests package...")
    
    try:
        stats = await get_package_download_stats("requests", period="month")
        
        print(f"✅ Success!")
        print(f"Package: {stats.get('package')}")
        print(f"Data Source: {stats.get('data_source')}")
        print(f"Reliability: {stats.get('reliability')}")
        
        if stats.get('warning'):
            print(f"⚠️  Warning: {stats['warning']}")
        
        downloads = stats.get("downloads", {})
        print(f"Downloads - Month: {downloads.get('last_month', 0):,}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""Demo script showing multi-mirror source configuration."""

import asyncio
import os

from pypi_query_mcp.config import get_repository_manager, get_settings


async def demo_multi_mirror_configuration():
    """Demonstrate multi-mirror source configuration."""
    print("🔧 PyPI Query MCP Server - Multi-Mirror Configuration Demo")
    print("=" * 60)

    # Set up environment variables for demo
    os.environ.update(
        {
            "PYPI_INDEX_URL": "https://pypi.org/pypi",
            "PYPI_INDEX_URLS": "https://mirrors.aliyun.com/pypi/simple/,https://pypi.tuna.tsinghua.edu.cn/simple/",
            "PYPI_EXTRA_INDEX_URLS": "https://test.pypi.org/simple/",
            "PYPI_PRIVATE_PYPI_URL": "https://private.company.com/pypi",
            "PYPI_PRIVATE_PYPI_USERNAME": "demo_user",
            "PYPI_PRIVATE_PYPI_PASSWORD": "demo_password",
            "PYPI_CACHE_TTL": "7200",
            "PYPI_LOG_LEVEL": "DEBUG",
        }
    )

    # Load settings
    settings = get_settings()

    print("\n📋 Configuration Settings:")
    print(f"  Primary Index URL: {settings.index_url}")
    print(f"  Cache TTL: {settings.cache_ttl} seconds")
    print(f"  Log Level: {settings.log_level}")
    print(f"  Request Timeout: {settings.request_timeout} seconds")

    print("\n🌐 Index URLs Configuration:")
    all_urls = settings.get_all_index_urls()
    primary_urls = settings.get_primary_index_urls()
    fallback_urls = settings.get_fallback_index_urls()

    print(f"  All Index URLs ({len(all_urls)}):")
    for i, url in enumerate(all_urls, 1):
        print(f"    {i}. {url}")

    print(f"\n  Primary URLs ({len(primary_urls)}):")
    for i, url in enumerate(primary_urls, 1):
        print(f"    {i}. {url}")

    print(f"\n  Fallback URLs ({len(fallback_urls)}):")
    for i, url in enumerate(fallback_urls, 1):
        print(f"    {i}. {url}")

    print("\n🔐 Private Repository Configuration:")
    print(f"  Has Private Repo: {settings.has_private_repo()}")
    print(f"  Has Private Auth: {settings.has_private_auth()}")
    if settings.has_private_repo():
        print(f"  Private URL: {settings.private_pypi_url}")
        print(f"  Username: {settings.private_pypi_username}")
        print(f"  Password: {'***' if settings.private_pypi_password else 'None'}")

    print("\n⚙️ Advanced Settings:")
    print(f"  Dependency Max Depth: {settings.dependency_max_depth}")
    print(f"  Dependency Max Concurrent: {settings.dependency_max_concurrent}")
    print(f"  Security Analysis: {settings.enable_security_analysis}")

    # Load repository manager
    repo_manager = get_repository_manager()
    repo_manager.load_repositories_from_settings(settings)

    print("\n📦 Repository Manager Configuration:")
    all_repos = repo_manager.list_repositories()
    enabled_repos = repo_manager.get_enabled_repositories()
    private_repos = repo_manager.get_private_repositories()

    print(f"  Total Repositories: {len(all_repos)}")
    print(f"  Enabled Repositories: {len(enabled_repos)}")
    print(f"  Private Repositories: {len(private_repos)}")
    print(f"  Has Private Repos: {repo_manager.has_private_repositories()}")

    print("\n📋 Repository Details (by priority):")
    for repo in enabled_repos:
        auth_info = f" (Auth: {repo.auth_type.value})" if repo.requires_auth() else ""
        print(
            f"  {repo.priority:3d}. {repo.name:12s} - {repo.type.value:7s} - {repo.url}{auth_info}"
        )

    print("\n✅ Configuration loaded successfully!")
    print("\nThis configuration provides:")
    print("  • High availability through multiple mirror sources")
    print("  • Automatic fallback to backup mirrors")
    print("  • Private repository support with authentication")
    print("  • Configurable dependency analysis settings")
    print("  • Secure credential management")


if __name__ == "__main__":
    asyncio.run(demo_multi_mirror_configuration())

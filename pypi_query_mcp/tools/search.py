"""PyPI search tools with advanced filtering and sorting capabilities."""

import logging
from typing import Any, Dict, List, Optional

from ..core.exceptions import InvalidPackageNameError, SearchError
from ..core.search_client import PyPISearchClient, SearchFilter, SearchSort

logger = logging.getLogger(__name__)


async def search_packages(
    query: str,
    limit: int = 20,
    python_versions: Optional[List[str]] = None,
    licenses: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    min_downloads: Optional[int] = None,
    maintenance_status: Optional[str] = None,
    has_wheels: Optional[bool] = None,
    sort_by: str = "relevance",
    sort_desc: bool = True,
    semantic_search: bool = False,
) -> Dict[str, Any]:
    """
    Search PyPI packages with advanced filtering and sorting.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 20)
        python_versions: List of Python versions to filter by (e.g., ["3.9", "3.10"])
        licenses: List of license types to filter by (e.g., ["mit", "apache", "bsd"])
        categories: List of categories to filter by (e.g., ["web", "data-science"])
        min_downloads: Minimum monthly downloads threshold
        maintenance_status: Filter by maintenance status ("active", "maintained", "stale", "abandoned")
        has_wheels: Filter packages that have/don't have wheel distributions
        sort_by: Sort field ("relevance", "popularity", "recency", "quality", "name", "downloads")
        sort_desc: Sort in descending order (default: True)
        semantic_search: Use semantic search on package descriptions (default: False)
        
    Returns:
        Dictionary containing search results and metadata
        
    Raises:
        InvalidPackageNameError: If search query is invalid
        SearchError: If search operation fails
    """
    if not query or not query.strip():
        raise InvalidPackageNameError("Search query cannot be empty")
    
    if limit <= 0 or limit > 100:
        limit = 20
    
    logger.info(f"Searching PyPI: '{query}' (limit: {limit}, sort: {sort_by})")
    
    try:
        # Create search filters
        filters = SearchFilter(
            python_versions=python_versions,
            licenses=licenses,
            categories=categories,
            min_downloads=min_downloads,
            maintenance_status=maintenance_status,
            has_wheels=has_wheels,
        )
        
        # Create sort configuration
        sort = SearchSort(field=sort_by, reverse=sort_desc)
        
        # Perform search
        async with PyPISearchClient() as search_client:
            result = await search_client.search_packages(
                query=query,
                limit=limit,
                filters=filters,
                sort=sort,
                semantic_search=semantic_search,
            )
        
        return result
        
    except SearchError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise SearchError(f"Search failed: {e}") from e


async def search_by_category(
    category: str,
    limit: int = 20,
    sort_by: str = "popularity",
    python_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search packages by category with popularity sorting.
    
    Args:
        category: Category to search for (e.g., "web", "data-science", "testing")
        limit: Maximum number of results to return
        sort_by: Sort field (default: "popularity")
        python_version: Filter by Python version compatibility
        
    Returns:
        Dictionary containing categorized search results
    """
    logger.info(f"Searching category: '{category}' (limit: {limit})")
    
    # Map category to search query and filters
    category_queries = {
        "web": "web framework flask django fastapi",
        "data-science": "data science machine learning pandas numpy",
        "database": "database sql orm sqlite postgres mysql",
        "testing": "testing pytest unittest mock coverage",
        "cli": "command line interface cli argparse click",
        "security": "security encryption crypto ssl authentication",
        "networking": "network http requests urllib socket",
        "dev-tools": "development tools build package deploy",
        "cloud": "cloud aws azure gcp docker kubernetes",
        "gui": "gui interface tkinter qt desktop",
    }
    
    query = category_queries.get(category.lower(), category)
    
    return await search_packages(
        query=query,
        limit=limit,
        categories=[category.lower()],
        python_versions=[python_version] if python_version else None,
        sort_by=sort_by,
        semantic_search=True,
    )


async def find_alternatives(
    package_name: str,
    limit: int = 10,
    include_similar: bool = True,
) -> Dict[str, Any]:
    """
    Find alternative packages to a given package.
    
    Args:
        package_name: Name of the package to find alternatives for
        limit: Maximum number of alternatives to return
        include_similar: Include packages with similar functionality
        
    Returns:
        Dictionary containing alternative packages and analysis
    """
    logger.info(f"Finding alternatives for: '{package_name}'")
    
    try:
        # First, get information about the target package
        from ..core.pypi_client import PyPIClient
        
        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)
            
        info = package_data["info"]
        keywords = info.get("keywords", "")
        summary = info.get("summary", "")
        categories = info.get("classifiers", [])
        
        # Extract category information
        category_terms = []
        for classifier in categories:
            if "Topic ::" in classifier:
                topic = classifier.split("Topic ::")[-1].strip().lower()
                category_terms.append(topic)
        
        # Create search query from package metadata
        search_terms = []
        if keywords:
            search_terms.extend(keywords.split())
        if summary:
            # Extract key terms from summary
            summary_words = [w for w in summary.lower().split() if len(w) > 3]
            search_terms.extend(summary_words[:5])
        
        search_query = " ".join(search_terms[:8])  # Limit to most relevant terms
        
        if not search_query:
            search_query = package_name  # Fallback to package name
        
        # Search for alternatives
        results = await search_packages(
            query=search_query,
            limit=limit + 5,  # Get extra to filter out the original package
            sort_by="popularity",
            semantic_search=include_similar,
        )
        
        # Filter out the original package
        alternatives = []
        for pkg in results["packages"]:
            if pkg["name"].lower() != package_name.lower():
                alternatives.append(pkg)
        
        alternatives = alternatives[:limit]
        
        return {
            "target_package": {
                "name": package_name,
                "summary": summary,
                "keywords": keywords,
                "categories": category_terms,
            },
            "alternatives": alternatives,
            "search_query_used": search_query,
            "total_alternatives": len(alternatives),
            "analysis": {
                "search_method": "keyword_similarity" if search_terms else "name_based",
                "semantic_search_used": include_similar,
                "category_based": len(category_terms) > 0,
            },
            "timestamp": results["timestamp"],
        }
        
    except Exception as e:
        logger.error(f"Error finding alternatives for {package_name}: {e}")
        raise SearchError(f"Failed to find alternatives: {e}") from e


async def get_trending_packages(
    category: Optional[str] = None,
    time_period: str = "week",
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Get trending packages based on recent download activity.
    
    Args:
        category: Optional category filter
        time_period: Time period for trending analysis ("day", "week", "month")
        limit: Maximum number of packages to return
        
    Returns:
        Dictionary containing trending packages
    """
    logger.info(f"Getting trending packages: category={category}, period={time_period}")
    
    try:
        # Use our top packages functionality as a base
        from .download_stats import get_top_packages_by_downloads
        
        top_packages_result = await get_top_packages_by_downloads(period=time_period, limit=limit * 2)
        
        # Filter by category if specified
        if category:
            # Enhance with category information
            enhanced_packages = []
            for pkg in top_packages_result["top_packages"]:
                try:
                    # Get package metadata for category classification
                    from ..core.pypi_client import PyPIClient
                    async with PyPIClient() as client:
                        package_data = await client.get_package_info(pkg["package"])
                        
                    # Simple category matching
                    info = package_data["info"]
                    text = f"{info.get('keywords', '')} {info.get('summary', '')}".lower()
                    
                    category_keywords = {
                        "web": ["web framework", "web", "flask", "django", "fastapi", "wsgi", "asgi"],
                        "data-science": ["data", "science", "pandas", "numpy", "ml"],
                        "database": ["database", "sql", "orm"],
                        "testing": ["test", "pytest", "mock"],
                        "cli": ["cli", "command", "argparse", "click"],
                    }
                    
                    if category.lower() in category_keywords:
                        keywords = category_keywords[category.lower()]
                        # For web category, be more specific to avoid HTTP clients
                        if category.lower() == "web":
                            web_patterns = ["web framework", "micro web", "flask", "django", "fastapi", "wsgi", "asgi"]
                            match_found = any(pattern in text for pattern in web_patterns)
                        else:
                            match_found = any(keyword in text for keyword in keywords)
                        
                        if match_found:
                            enhanced_packages.append({
                                **pkg,
                                "category_match": True,
                                "summary": info.get("summary", ""),
                            })
                except:
                    continue
            
            trending_packages = enhanced_packages[:limit]
        else:
            trending_packages = top_packages_result["top_packages"][:limit]
        
        return {
            "trending_packages": trending_packages,
            "time_period": time_period,
            "category": category,
            "total_found": len(trending_packages),
            "analysis": {
                "source": "download_statistics",
                "category_filtered": category is not None,
                "methodology": "Based on download counts and popularity metrics",
            },
            "timestamp": top_packages_result["timestamp"],
        }
        
    except Exception as e:
        logger.error(f"Error getting trending packages: {e}")
        raise SearchError(f"Failed to get trending packages: {e}") from e
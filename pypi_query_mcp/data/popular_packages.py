"""Curated lists of popular PyPI packages organized by category and estimated download rankings.

This data provides fallback information when PyPI statistics APIs are unavailable.
The rankings and download estimates are based on:
- Historical PyPI download statistics
- GitHub star counts and activity
- Community surveys and package popularity
- Industry usage patterns

Data is organized by categories and includes estimated relative popularity.
"""

from typing import NamedTuple


class PackageInfo(NamedTuple):
    """Information about a popular package."""

    name: str
    category: str
    estimated_monthly_downloads: int
    github_stars: int  # Approximate, for popularity estimation
    description: str
    primary_use_case: str


# Core packages that are dependencies for many other packages
INFRASTRUCTURE_PACKAGES = [
    PackageInfo(
        "setuptools",
        "packaging",
        800_000_000,
        2100,
        "Package development tools",
        "packaging",
    ),
    PackageInfo(
        "wheel", "packaging", 700_000_000, 400, "Binary package format", "packaging"
    ),
    PackageInfo(
        "pip", "packaging", 600_000_000, 9500, "Package installer", "packaging"
    ),
    PackageInfo(
        "certifi", "security", 500_000_000, 800, "Certificate bundle", "security"
    ),
    PackageInfo(
        "urllib3", "networking", 450_000_000, 3600, "HTTP client library", "networking"
    ),
    PackageInfo(
        "charset-normalizer",
        "text",
        400_000_000,
        400,
        "Character encoding detection",
        "text-processing",
    ),
    PackageInfo(
        "idna",
        "networking",
        380_000_000,
        200,
        "Internationalized domain names",
        "networking",
    ),
    PackageInfo(
        "six",
        "compatibility",
        350_000_000,
        900,
        "Python 2 and 3 compatibility",
        "compatibility",
    ),
    PackageInfo(
        "python-dateutil",
        "datetime",
        320_000_000,
        2200,
        "Date and time utilities",
        "datetime",
    ),
    PackageInfo(
        "requests", "networking", 300_000_000, 51000, "HTTP library", "networking"
    ),
]

# AWS and cloud packages
CLOUD_PACKAGES = [
    PackageInfo("boto3", "cloud", 280_000_000, 8900, "AWS SDK", "cloud"),
    PackageInfo("botocore", "cloud", 275_000_000, 1400, "AWS SDK core", "cloud"),
    PackageInfo(
        "s3transfer", "cloud", 250_000_000, 200, "S3 transfer utilities", "cloud"
    ),
    PackageInfo("awscli", "cloud", 80_000_000, 15000, "AWS command line", "cloud"),
    PackageInfo("azure-core", "cloud", 45_000_000, 400, "Azure SDK core", "cloud"),
    PackageInfo(
        "google-cloud-storage",
        "cloud",
        35_000_000,
        300,
        "Google Cloud Storage",
        "cloud",
    ),
    PackageInfo(
        "azure-storage-blob", "cloud", 30_000_000, 200, "Azure Blob Storage", "cloud"
    ),
]

# Data science and ML packages
DATA_SCIENCE_PACKAGES = [
    PackageInfo(
        "numpy",
        "data-science",
        200_000_000,
        26000,
        "Numerical computing",
        "data-science",
    ),
    PackageInfo(
        "pandas",
        "data-science",
        150_000_000,
        42000,
        "Data manipulation",
        "data-science",
    ),
    PackageInfo(
        "scikit-learn",
        "machine-learning",
        80_000_000,
        58000,
        "Machine learning",
        "machine-learning",
    ),
    PackageInfo(
        "matplotlib",
        "visualization",
        75_000_000,
        19000,
        "Plotting library",
        "visualization",
    ),
    PackageInfo(
        "scipy",
        "data-science",
        70_000_000,
        12000,
        "Scientific computing",
        "data-science",
    ),
    PackageInfo(
        "seaborn",
        "visualization",
        45_000_000,
        11000,
        "Statistical visualization",
        "visualization",
    ),
    PackageInfo(
        "plotly",
        "visualization",
        40_000_000,
        15000,
        "Interactive plots",
        "visualization",
    ),
    PackageInfo(
        "jupyter",
        "development",
        35_000_000,
        7000,
        "Interactive notebooks",
        "development",
    ),
    PackageInfo(
        "ipython", "development", 50_000_000, 8000, "Interactive Python", "development"
    ),
    PackageInfo(
        "tensorflow",
        "machine-learning",
        25_000_000,
        185000,
        "Deep learning",
        "machine-learning",
    ),
    PackageInfo(
        "torch",
        "machine-learning",
        20_000_000,
        81000,
        "PyTorch deep learning",
        "machine-learning",
    ),
    PackageInfo(
        "transformers",
        "machine-learning",
        15_000_000,
        130000,
        "NLP transformers",
        "machine-learning",
    ),
]

# Development and testing
DEVELOPMENT_PACKAGES = [
    PackageInfo(
        "typing-extensions",
        "development",
        180_000_000,
        3000,
        "Typing extensions",
        "development",
    ),
    PackageInfo(
        "packaging", "development", 160_000_000, 600, "Package utilities", "development"
    ),
    PackageInfo(
        "pytest", "testing", 100_000_000, 11000, "Testing framework", "testing"
    ),
    PackageInfo("click", "cli", 90_000_000, 15000, "Command line interface", "cli"),
    PackageInfo(
        "pyyaml", "serialization", 85_000_000, 2200, "YAML parser", "serialization"
    ),
    PackageInfo(
        "jinja2", "templating", 80_000_000, 10000, "Template engine", "templating"
    ),
    PackageInfo(
        "markupsafe", "templating", 75_000_000, 600, "Safe markup", "templating"
    ),
    PackageInfo(
        "attrs",
        "development",
        60_000_000,
        5000,
        "Classes without boilerplate",
        "development",
    ),
    PackageInfo(
        "black", "development", 40_000_000, 38000, "Code formatter", "development"
    ),
    PackageInfo(
        "flake8", "development", 35_000_000, 3000, "Code linting", "development"
    ),
    PackageInfo(
        "mypy", "development", 30_000_000, 17000, "Static type checker", "development"
    ),
]

# Web development
WEB_PACKAGES = [
    PackageInfo("django", "web", 60_000_000, 77000, "Web framework", "web"),
    PackageInfo("flask", "web", 55_000_000, 66000, "Micro web framework", "web"),
    PackageInfo("fastapi", "web", 35_000_000, 74000, "Modern web API framework", "web"),
    PackageInfo("sqlalchemy", "database", 50_000_000, 8000, "SQL toolkit", "database"),
    PackageInfo(
        "psycopg2", "database", 25_000_000, 3000, "PostgreSQL adapter", "database"
    ),
    PackageInfo("redis", "database", 30_000_000, 12000, "Redis client", "database"),
    PackageInfo(
        "celery", "async", 25_000_000, 23000, "Distributed task queue", "async"
    ),
    PackageInfo("gunicorn", "web", 20_000_000, 9000, "WSGI server", "web"),
    PackageInfo("uvicorn", "web", 15_000_000, 8000, "ASGI server", "web"),
]

# Security and cryptography
SECURITY_PACKAGES = [
    PackageInfo(
        "cryptography",
        "security",
        120_000_000,
        6000,
        "Cryptographic library",
        "security",
    ),
    PackageInfo(
        "pyopenssl", "security", 60_000_000, 800, "OpenSSL wrapper", "security"
    ),
    PackageInfo("pyjwt", "security", 40_000_000, 5000, "JSON Web Tokens", "security"),
    PackageInfo("bcrypt", "security", 35_000_000, 1200, "Password hashing", "security"),
    PackageInfo(
        "pycryptodome",
        "security",
        30_000_000,
        2700,
        "Cryptographic library",
        "security",
    ),
]

# Networking and API
NETWORKING_PACKAGES = [
    PackageInfo("httpx", "networking", 25_000_000, 12000, "HTTP client", "networking"),
    PackageInfo("aiohttp", "networking", 35_000_000, 14000, "Async HTTP", "networking"),
    PackageInfo(
        "websockets",
        "networking",
        20_000_000,
        5000,
        "WebSocket implementation",
        "networking",
    ),
    PackageInfo("paramiko", "networking", 25_000_000, 8000, "SSH client", "networking"),
]

# Text processing and parsing
TEXT_PACKAGES = [
    PackageInfo(
        "beautifulsoup4", "parsing", 40_000_000, 13000, "HTML/XML parser", "parsing"
    ),
    PackageInfo("lxml", "parsing", 35_000_000, 2600, "XML/HTML parser", "parsing"),
    PackageInfo(
        "regex", "text", 30_000_000, 700, "Regular expressions", "text-processing"
    ),
    PackageInfo(
        "python-docx",
        "text",
        15_000_000,
        4000,
        "Word document processing",
        "text-processing",
    ),
    PackageInfo("pillow", "imaging", 60_000_000, 11000, "Image processing", "imaging"),
]

# All packages combined for easy access
ALL_POPULAR_PACKAGES = (
    INFRASTRUCTURE_PACKAGES
    + CLOUD_PACKAGES
    + DATA_SCIENCE_PACKAGES
    + DEVELOPMENT_PACKAGES
    + WEB_PACKAGES
    + SECURITY_PACKAGES
    + NETWORKING_PACKAGES
    + TEXT_PACKAGES
)

# Create lookup dictionaries
PACKAGES_BY_NAME = {pkg.name: pkg for pkg in ALL_POPULAR_PACKAGES}
PACKAGES_BY_CATEGORY = {}
for pkg in ALL_POPULAR_PACKAGES:
    if pkg.category not in PACKAGES_BY_CATEGORY:
        PACKAGES_BY_CATEGORY[pkg.category] = []
    PACKAGES_BY_CATEGORY[pkg.category].append(pkg)


def get_popular_packages(
    category: str = None, limit: int = 50, min_downloads: int = 0
) -> list[PackageInfo]:
    """Get popular packages filtered by criteria.

    Args:
        category: Filter by category (e.g., 'web', 'data-science', 'cloud')
        limit: Maximum number of packages to return
        min_downloads: Minimum estimated monthly downloads

    Returns:
        List of PackageInfo objects sorted by estimated downloads
    """
    packages = ALL_POPULAR_PACKAGES

    if category:
        packages = [pkg for pkg in packages if pkg.category == category]

    if min_downloads:
        packages = [
            pkg for pkg in packages if pkg.estimated_monthly_downloads >= min_downloads
        ]

    # Sort by estimated downloads (descending)
    packages = sorted(
        packages, key=lambda x: x.estimated_monthly_downloads, reverse=True
    )

    return packages[:limit]


def estimate_downloads_for_period(monthly_downloads: int, period: str) -> int:
    """Estimate downloads for different time periods.

    Args:
        monthly_downloads: Estimated monthly downloads
        period: Time period ('day', 'week', 'month')

    Returns:
        Estimated downloads for the period
    """
    if period == "day":
        return int(monthly_downloads / 30)
    elif period == "week":
        return int(monthly_downloads / 4.3)  # ~4.3 weeks per month
    elif period == "month":
        return monthly_downloads
    else:
        return monthly_downloads


def get_package_info(package_name: str) -> PackageInfo:
    """Get information about a specific package.

    Args:
        package_name: Name of the package

    Returns:
        PackageInfo object or None if not found
    """
    return PACKAGES_BY_NAME.get(
        package_name.lower().replace("-", "_").replace("_", "-")
    )


# GitHub repository URL patterns for fetching real-time data
GITHUB_REPO_PATTERNS = {
    "requests": "psf/requests",
    "django": "django/django",
    "flask": "pallets/flask",
    "fastapi": "tiangolo/fastapi",
    "numpy": "numpy/numpy",
    "pandas": "pandas-dev/pandas",
    "scikit-learn": "scikit-learn/scikit-learn",
    "tensorflow": "tensorflow/tensorflow",
    "torch": "pytorch/pytorch",
    "transformers": "huggingface/transformers",
    "click": "pallets/click",
    "black": "psf/black",
    "boto3": "boto/boto3",
    "sqlalchemy": "sqlalchemy/sqlalchemy",
    # Add more mappings as needed
}

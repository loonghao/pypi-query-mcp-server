"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_package_data():
    """Sample package data for testing."""
    return {
        "info": {
            "name": "test-package",
            "version": "1.0.0",
            "summary": "A test package",
            "description": "This is a test package for testing purposes.",
            "author": "Test Author",
            "author_email": "test@example.com",
            "license": "MIT",
            "requires_python": ">=3.8",
            "requires_dist": [
                "requests>=2.25.0",
                "click>=8.0.0",
                "pytest>=6.0.0; extra == 'test'"
            ],
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Intended Audience :: Developers",
                "License :: OSI Approved :: MIT License",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Programming Language :: Python :: Implementation :: CPython"
            ]
        },
        "releases": {
            "1.0.0": [
                {
                    "filename": "test_package-1.0.0-py3-none-any.whl",
                    "packagetype": "bdist_wheel",
                    "python_version": "py3"
                },
                {
                    "filename": "test-package-1.0.0.tar.gz",
                    "packagetype": "sdist",
                    "python_version": "source"
                }
            ],
            "0.9.0": [
                {
                    "filename": "test-package-0.9.0.tar.gz",
                    "packagetype": "sdist",
                    "python_version": "source"
                }
            ]
        }
    }


@pytest.fixture
def mock_pypi_response(sample_package_data):
    """Mock PyPI API response."""
    return sample_package_data

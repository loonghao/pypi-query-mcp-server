"""Package download tools for PyPI packages."""

import hashlib
import logging
from pathlib import Path
from typing import Any

import httpx

from ..core import PyPIClient, PyPIError
from ..core.exceptions import (
    InvalidPackageNameError,
    NetworkError,
    PackageNotFoundError,
)
from .dependency_resolver import DependencyResolver

logger = logging.getLogger(__name__)


class PackageDownloader:
    """Downloads PyPI packages and their dependencies."""

    def __init__(self, download_dir: str = "./downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.resolver = DependencyResolver()

    async def download_package_with_dependencies(
        self,
        package_name: str,
        python_version: str | None = None,
        include_extras: list[str] | None = None,
        include_dev: bool = False,
        prefer_wheel: bool = True,
        verify_checksums: bool = True,
        max_depth: int = 5,
    ) -> dict[str, Any]:
        """Download a package and all its dependencies.

        Args:
            package_name: Name of the package to download
            python_version: Target Python version (e.g., "3.10")
            include_extras: List of extra dependencies to include
            include_dev: Whether to include development dependencies
            prefer_wheel: Whether to prefer wheel files over source distributions
            verify_checksums: Whether to verify file checksums
            max_depth: Maximum dependency resolution depth

        Returns:
            Dictionary containing download results and statistics
        """
        if not package_name or not package_name.strip():
            raise InvalidPackageNameError(package_name)

        logger.info(f"Starting download of {package_name} and dependencies")

        try:
            # First resolve all dependencies
            resolution_result = await self.resolver.resolve_dependencies(
                package_name=package_name,
                python_version=python_version,
                include_extras=include_extras,
                include_dev=include_dev,
                max_depth=max_depth,
            )

            dependency_tree = resolution_result["dependency_tree"]

            # Download all packages
            download_results = {}
            failed_downloads = []

            for pkg_name, pkg_info in dependency_tree.items():
                try:
                    result = await self._download_single_package(
                        package_name=pkg_info["name"],
                        version=pkg_info["version"],
                        python_version=python_version,
                        prefer_wheel=prefer_wheel,
                        verify_checksums=verify_checksums,
                    )
                    download_results[pkg_name] = result

                except Exception as e:
                    logger.error(f"Failed to download {pkg_name}: {e}")
                    failed_downloads.append({"package": pkg_name, "error": str(e)})

            # Generate summary
            summary = self._generate_download_summary(
                download_results, failed_downloads
            )

            return {
                "package_name": package_name,
                "python_version": python_version,
                "download_directory": str(self.download_dir),
                "resolution_result": resolution_result,
                "download_results": download_results,
                "failed_downloads": failed_downloads,
                "summary": summary,
            }

        except PyPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading {package_name}: {e}")
            raise NetworkError(f"Failed to download package: {e}", e) from e

    async def _download_single_package(
        self,
        package_name: str,
        version: str | None = None,
        python_version: str | None = None,
        prefer_wheel: bool = True,
        verify_checksums: bool = True,
    ) -> dict[str, Any]:
        """Download a single package."""

        logger.info(f"Downloading {package_name} version {version or 'latest'}")

        async with PyPIClient() as client:
            package_data = await client.get_package_info(package_name)

        info = package_data.get("info", {})
        releases = package_data.get("releases", {})

        # Determine version to download
        target_version = version or info.get("version")
        if not target_version or target_version not in releases:
            raise PackageNotFoundError(
                f"Version {target_version} not found for {package_name}"
            )

        # Get release files
        release_files = releases[target_version]
        if not release_files:
            raise PackageNotFoundError(
                f"No files found for {package_name} {target_version}"
            )

        # Select best file to download
        selected_file = self._select_best_file(
            release_files, python_version, prefer_wheel
        )

        if not selected_file:
            raise PackageNotFoundError(
                f"No suitable file found for {package_name} {target_version}"
            )

        # Download the file
        download_result = await self._download_file(selected_file, verify_checksums)

        return {
            "package_name": package_name,
            "version": target_version,
            "file_info": selected_file,
            "download_result": download_result,
        }

    def _select_best_file(
        self,
        release_files: list[dict[str, Any]],
        python_version: str | None = None,
        prefer_wheel: bool = True,
    ) -> dict[str, Any] | None:
        """Select the best file to download from available release files."""

        # Separate wheels and source distributions
        wheels = [f for f in release_files if f.get("packagetype") == "bdist_wheel"]
        sdists = [f for f in release_files if f.get("packagetype") == "sdist"]

        # If prefer wheel and wheels available
        if prefer_wheel and wheels:
            # Try to find compatible wheel
            if python_version:
                compatible_wheels = self._filter_compatible_wheels(
                    wheels, python_version
                )
                if compatible_wheels:
                    return compatible_wheels[0]

            # Return any wheel if no specific version or no compatible found
            return wheels[0]

        # Fall back to source distribution
        if sdists:
            return sdists[0]

        # Last resort: any file
        return release_files[0] if release_files else None

    def _filter_compatible_wheels(
        self, wheels: list[dict[str, Any]], python_version: str
    ) -> list[dict[str, Any]]:
        """Filter wheels compatible with the specified Python version."""

        # Simple compatibility check based on filename
        # This is a basic implementation - could be enhanced with proper wheel tag parsing
        compatible = []

        major_minor = ".".join(python_version.split(".")[:2])
        major_minor_nodot = major_minor.replace(".", "")

        for wheel in wheels:
            filename = wheel.get("filename", "")

            # Check for Python version in filename
            if (
                f"py{major_minor_nodot}" in filename
                or f"cp{major_minor_nodot}" in filename
                or "py3" in filename
                or "py2.py3" in filename
            ):
                compatible.append(wheel)

        return compatible

    async def _download_file(
        self, file_info: dict[str, Any], verify_checksums: bool = True
    ) -> dict[str, Any]:
        """Download a single file."""

        url = file_info.get("url")
        filename = file_info.get("filename")
        expected_md5 = file_info.get("md5_digest")
        expected_size = file_info.get("size")

        if not url or not filename:
            raise ValueError("Invalid file info: missing URL or filename")

        # Create package-specific directory
        file_path = self.download_dir / filename

        logger.info(f"Downloading {filename} from {url}")

        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                # Download with progress tracking
                downloaded_size = 0
                md5_hash = hashlib.md5()

                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if verify_checksums:
                            md5_hash.update(chunk)

        # Verify download
        verification_result = {}
        if verify_checksums and expected_md5:
            actual_md5 = md5_hash.hexdigest()
            verification_result["md5_match"] = actual_md5 == expected_md5
            verification_result["expected_md5"] = expected_md5
            verification_result["actual_md5"] = actual_md5

        if expected_size:
            verification_result["size_match"] = downloaded_size == expected_size
            verification_result["expected_size"] = expected_size
            verification_result["actual_size"] = downloaded_size

        return {
            "filename": filename,
            "file_path": str(file_path),
            "downloaded_size": downloaded_size,
            "verification": verification_result,
            "success": True,
        }

    def _generate_download_summary(
        self, download_results: dict[str, Any], failed_downloads: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate download summary statistics."""

        successful_downloads = len(download_results)
        failed_count = len(failed_downloads)
        total_size = sum(
            result["download_result"]["downloaded_size"]
            for result in download_results.values()
        )

        return {
            "total_packages": successful_downloads + failed_count,
            "successful_downloads": successful_downloads,
            "failed_downloads": failed_count,
            "total_downloaded_size": total_size,
            "download_directory": str(self.download_dir),
            "success_rate": successful_downloads
            / (successful_downloads + failed_count)
            * 100
            if (successful_downloads + failed_count) > 0
            else 0,
        }


async def download_package_with_dependencies(
    package_name: str,
    download_dir: str = "./downloads",
    python_version: str | None = None,
    include_extras: list[str] | None = None,
    include_dev: bool = False,
    prefer_wheel: bool = True,
    verify_checksums: bool = True,
    max_depth: int = 5,
) -> dict[str, Any]:
    """Download a package and its dependencies to local directory.

    Args:
        package_name: Name of the package to download
        download_dir: Directory to download packages to
        python_version: Target Python version (e.g., "3.10")
        include_extras: List of extra dependencies to include
        include_dev: Whether to include development dependencies
        prefer_wheel: Whether to prefer wheel files over source distributions
        verify_checksums: Whether to verify file checksums
        max_depth: Maximum dependency resolution depth

    Returns:
        Comprehensive download results
    """
    downloader = PackageDownloader(download_dir)
    return await downloader.download_package_with_dependencies(
        package_name=package_name,
        python_version=python_version,
        include_extras=include_extras,
        include_dev=include_dev,
        prefer_wheel=prefer_wheel,
        verify_checksums=verify_checksums,
        max_depth=max_depth,
    )

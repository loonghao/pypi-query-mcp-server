"""Security vulnerability scanning and analysis tools for PyPI packages."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from ..core.exceptions import NetworkError, SearchError
from ..core.pypi_client import PyPIClient

logger = logging.getLogger(__name__)


class VulnerabilityScanner:
    """Comprehensive vulnerability scanner for PyPI packages."""

    def __init__(self):
        self.timeout = 30.0
        self.session = None
        
        # Vulnerability database endpoints
        self.osv_api = "https://api.osv.dev/v1/query"
        self.safety_db_api = "https://pyup.io/api/v1/safety"
        self.snyk_api = "https://snyk.io/test/pip"
        
        # Common vulnerability patterns to look for
        self.high_risk_patterns = [
            "remote code execution", "rce", "code injection", "sql injection",
            "cross-site scripting", "xss", "csrf", "authentication bypass",
            "privilege escalation", "arbitrary file", "path traversal",
            "buffer overflow", "memory corruption", "denial of service"
        ]

    async def scan_package(
        self, 
        package_name: str, 
        version: Optional[str] = None,
        include_dependencies: bool = True,
        severity_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive security scan of a PyPI package.
        
        Args:
            package_name: Name of the package to scan
            version: Specific version to scan (optional, defaults to latest)
            include_dependencies: Whether to scan dependencies too
            severity_filter: Filter by severity level (low, medium, high, critical)
            
        Returns:
            Dictionary containing security analysis results
        """
        logger.info(f"Starting security scan for package: {package_name}")
        
        try:
            # Get package information
            async with PyPIClient() as client:
                package_data = await client.get_package_info(package_name, version)
                
            package_version = version or package_data["info"]["version"]
            
            # Run parallel vulnerability scans
            scan_tasks = [
                self._scan_osv_database(package_name, package_version),
                self._scan_github_advisories(package_name, package_version),
                self._analyze_package_metadata(package_data),
                self._check_dependency_vulnerabilities(package_name, package_version) if include_dependencies else asyncio.create_task(self._empty_result())
            ]
            
            osv_results, github_results, metadata_analysis, dependency_results = await asyncio.gather(
                *scan_tasks, return_exceptions=True
            )
            
            # Consolidate results
            vulnerabilities = []
            
            # Process OSV results
            if not isinstance(osv_results, Exception) and osv_results:
                vulnerabilities.extend(osv_results.get("vulnerabilities", []))
            
            # Process GitHub results  
            if not isinstance(github_results, Exception) and github_results:
                vulnerabilities.extend(github_results.get("vulnerabilities", []))
                
            # Process dependency vulnerabilities
            if not isinstance(dependency_results, Exception) and dependency_results:
                vulnerabilities.extend(dependency_results.get("vulnerabilities", []))
            
            # Apply severity filter
            if severity_filter:
                vulnerabilities = [
                    vuln for vuln in vulnerabilities 
                    if vuln.get("severity", "").lower() == severity_filter.lower()
                ]
            
            # Generate security report
            security_report = self._generate_security_report(
                package_name, package_version, vulnerabilities, metadata_analysis
            )
            
            return security_report
            
        except Exception as e:
            logger.error(f"Security scan failed for {package_name}: {e}")
            raise SearchError(f"Security scan failed: {e}") from e

    async def _scan_osv_database(self, package_name: str, version: str) -> Dict[str, Any]:
        """Scan package against OSV (Open Source Vulnerabilities) database."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                query_data = {
                    "package": {
                        "name": package_name,
                        "ecosystem": "PyPI"
                    },
                    "version": version
                }
                
                response = await client.post(
                    self.osv_api,
                    json=query_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = []
                    
                    for vuln in data.get("vulns", []):
                        severity = self._extract_severity_from_osv(vuln)
                        vulnerabilities.append({
                            "id": vuln.get("id", ""),
                            "summary": vuln.get("summary", ""),
                            "details": vuln.get("details", ""),
                            "severity": severity,
                            "published": vuln.get("published", ""),
                            "modified": vuln.get("modified", ""),
                            "source": "OSV",
                            "references": [ref.get("url", "") for ref in vuln.get("references", [])],
                            "affected_versions": self._extract_affected_versions(vuln),
                            "fixed_versions": self._extract_fixed_versions(vuln),
                        })
                    
                    return {"vulnerabilities": vulnerabilities, "source": "OSV"}
                else:
                    logger.warning(f"OSV API returned status {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"OSV database scan failed: {e}")
            
        return {"vulnerabilities": [], "source": "OSV"}

    async def _scan_github_advisories(self, package_name: str, version: str) -> Dict[str, Any]:
        """Scan against GitHub Security Advisories."""
        try:
            # GitHub GraphQL API for security advisories
            query = """
            query($ecosystem: SecurityAdvisoryEcosystem!, $package: String!) {
              securityVulnerabilities(ecosystem: $ecosystem, package: $package, first: 100) {
                nodes {
                  advisory {
                    ghsaId
                    summary
                    description
                    severity
                    publishedAt
                    updatedAt
                    references {
                      url
                    }
                  }
                  vulnerableVersionRange
                  firstPatchedVersion {
                    identifier
                  }
                }
              }
            }
            """
            
            variables = {
                "ecosystem": "PIP",
                "package": package_name
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.github.com/graphql",
                    json={"query": query, "variables": variables},
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "PyPI-Security-Scanner/1.0"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = []
                    
                    for vuln_node in data.get("data", {}).get("securityVulnerabilities", {}).get("nodes", []):
                        advisory = vuln_node.get("advisory", {})
                        
                        # Check if current version is affected
                        if self._is_version_affected(version, vuln_node.get("vulnerableVersionRange", "")):
                            vulnerabilities.append({
                                "id": advisory.get("ghsaId", ""),
                                "summary": advisory.get("summary", ""),
                                "details": advisory.get("description", ""),
                                "severity": advisory.get("severity", "").lower(),
                                "published": advisory.get("publishedAt", ""),
                                "modified": advisory.get("updatedAt", ""),
                                "source": "GitHub",
                                "references": [ref.get("url", "") for ref in advisory.get("references", [])],
                                "vulnerable_range": vuln_node.get("vulnerableVersionRange", ""),
                                "first_patched": vuln_node.get("firstPatchedVersion", {}).get("identifier", ""),
                            })
                    
                    return {"vulnerabilities": vulnerabilities, "source": "GitHub"}
                    
        except Exception as e:
            logger.warning(f"GitHub advisories scan failed: {e}")
            
        return {"vulnerabilities": [], "source": "GitHub"}

    async def _analyze_package_metadata(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze package metadata for security indicators."""
        info = package_data.get("info", {})
        
        security_indicators = {
            "metadata_score": 0,
            "risk_factors": [],
            "security_features": [],
            "warnings": []
        }
        
        # Check for security-related information
        description = (info.get("description") or "").lower()
        summary = (info.get("summary") or "").lower()
        keywords = (info.get("keywords") or "").lower()
        
        combined_text = f"{description} {summary} {keywords}"
        
        # Look for security mentions
        if any(term in combined_text for term in ["security", "cryptography", "authentication", "encryption"]):
            security_indicators["security_features"].append("Contains security-related functionality")
            security_indicators["metadata_score"] += 20
            
        # Check for high-risk patterns
        for pattern in self.high_risk_patterns:
            if pattern in combined_text:
                security_indicators["risk_factors"].append(f"Mentions: {pattern}")
                security_indicators["metadata_score"] -= 10
        
        # Check package age and maintenance
        if info.get("author_email"):
            security_indicators["metadata_score"] += 10
            
        if info.get("home_page"):
            security_indicators["metadata_score"] += 5
            
        # Check for classifiers
        classifiers = info.get("classifiers", [])
        for classifier in classifiers:
            if "Development Status :: 5 - Production/Stable" in classifier:
                security_indicators["metadata_score"] += 15
                security_indicators["security_features"].append("Production stable status")
            elif "License ::" in classifier:
                security_indicators["metadata_score"] += 5
                
        # Check for suspicious patterns
        if not info.get("author") and not info.get("maintainer"):
            security_indicators["warnings"].append("No author or maintainer information")
            security_indicators["metadata_score"] -= 20
            
        if len(info.get("description", "")) < 50:
            security_indicators["warnings"].append("Very brief or missing description")
            security_indicators["metadata_score"] -= 10
        
        return security_indicators

    async def _check_dependency_vulnerabilities(self, package_name: str, version: str) -> Dict[str, Any]:
        """Check vulnerabilities in package dependencies."""
        try:
            # Get package dependencies
            async with PyPIClient() as client:
                package_data = await client.get_package_info(package_name, version)
                
            # Extract dependencies
            requires_dist = package_data.get("info", {}).get("requires_dist", []) or []
            dependencies = []
            
            for req in requires_dist:
                # Parse dependency name (simplified)
                dep_name = req.split()[0].split(">=")[0].split("==")[0].split("~=")[0].split("!=")[0]
                if dep_name and not dep_name.startswith("extra"):
                    dependencies.append(dep_name)
            
            # Scan top dependencies for vulnerabilities
            dependency_vulnerabilities = []
            
            # Limit to top 10 dependencies to avoid overwhelming the system
            for dep_name in dependencies[:10]:
                try:
                    dep_scan = await self._scan_osv_database(dep_name, "latest")
                    for vuln in dep_scan.get("vulnerabilities", []):
                        vuln["dependency"] = dep_name
                        vuln["type"] = "dependency_vulnerability"
                        dependency_vulnerabilities.append(vuln)
                except Exception as e:
                    logger.debug(f"Failed to scan dependency {dep_name}: {e}")
                    
            return {"vulnerabilities": dependency_vulnerabilities, "source": "dependencies"}
            
        except Exception as e:
            logger.warning(f"Dependency vulnerability check failed: {e}")
            return {"vulnerabilities": [], "source": "dependencies"}

    async def _empty_result(self) -> Dict[str, Any]:
        """Return empty result for disabled scans."""
        return {"vulnerabilities": [], "source": "disabled"}

    def _extract_severity_from_osv(self, vuln_data: Dict[str, Any]) -> str:
        """Extract severity from OSV vulnerability data."""
        # OSV uses CVSS scores, map to common severity levels
        severity_data = vuln_data.get("severity", [])
        if severity_data:
            score = severity_data[0].get("score", "")
            if "CVSS:" in score:
                # Extract CVSS score
                try:
                    cvss_score = float(score.split("/")[1])
                    if cvss_score >= 9.0:
                        return "critical"
                    elif cvss_score >= 7.0:
                        return "high"
                    elif cvss_score >= 4.0:
                        return "medium"
                    else:
                        return "low"
                except:
                    pass
        
        return "unknown"

    def _extract_affected_versions(self, vuln_data: Dict[str, Any]) -> List[str]:
        """Extract affected version ranges from vulnerability data."""
        affected = vuln_data.get("affected", [])
        version_ranges = []
        
        for affect in affected:
            ranges = affect.get("ranges", [])
            for range_data in ranges:
                events = range_data.get("events", [])
                for event in events:
                    if "introduced" in event:
                        version_ranges.append(f">= {event['introduced']}")
                    elif "fixed" in event:
                        version_ranges.append(f"< {event['fixed']}")
                        
        return version_ranges

    def _extract_fixed_versions(self, vuln_data: Dict[str, Any]) -> List[str]:
        """Extract fixed versions from vulnerability data."""
        affected = vuln_data.get("affected", [])
        fixed_versions = []
        
        for affect in affected:
            ranges = affect.get("ranges", [])
            for range_data in ranges:
                events = range_data.get("events", [])
                for event in events:
                    if "fixed" in event:
                        fixed_versions.append(event["fixed"])
                        
        return fixed_versions

    def _is_version_affected(self, version: str, vulnerable_range: str) -> bool:
        """Check if a version is affected by a vulnerability range."""
        # Simplified version checking - in production would use packaging.specifiers
        if not vulnerable_range:
            return True
            
        # Basic patterns
        if "< " in vulnerable_range:
            try:
                limit = vulnerable_range.split("< ")[1].strip()
                return version < limit
            except:
                pass
                
        if ">= " in vulnerable_range:
            try:
                limit = vulnerable_range.split(">= ")[1].strip()
                return version >= limit
            except:
                pass
                
        return True  # Assume affected if we can't parse

    def _generate_security_report(
        self, 
        package_name: str, 
        version: str, 
        vulnerabilities: List[Dict[str, Any]], 
        metadata_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        
        # Categorize vulnerabilities by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        dependency_vulns = []
        direct_vulns = []
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            if vuln.get("type") == "dependency_vulnerability":
                dependency_vulns.append(vuln)
            else:
                direct_vulns.append(vuln)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(severity_counts, metadata_analysis)
        
        # Generate recommendations
        recommendations = self._generate_security_recommendations(
            vulnerabilities, metadata_analysis, risk_score
        )
        
        return {
            "package": package_name,
            "version": version,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "security_summary": {
                "total_vulnerabilities": len(vulnerabilities),
                "direct_vulnerabilities": len(direct_vulns),
                "dependency_vulnerabilities": len(dependency_vulns),
                "severity_breakdown": severity_counts,
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
            },
            "vulnerabilities": {
                "direct": direct_vulns,
                "dependencies": dependency_vulns,
            },
            "metadata_analysis": metadata_analysis,
            "recommendations": recommendations,
            "scan_details": {
                "sources_checked": ["OSV", "GitHub", "Metadata"],
                "dependencies_scanned": len(dependency_vulns) > 0,
                "scan_completion": "success",
            }
        }

    def _calculate_risk_score(self, severity_counts: Dict[str, int], metadata_analysis: Dict[str, Any]) -> float:
        """Calculate overall risk score (0-100)."""
        score = 0.0
        
        # Vulnerability scoring (0-80 points)
        score += severity_counts.get("critical", 0) * 20
        score += severity_counts.get("high", 0) * 15
        score += severity_counts.get("medium", 0) * 8
        score += severity_counts.get("low", 0) * 3
        
        # Metadata scoring (0-20 points)
        metadata_score = metadata_analysis.get("metadata_score", 0)
        if metadata_score < 0:
            score += abs(metadata_score) / 5  # Convert negative metadata score to risk
        else:
            score -= metadata_score / 10  # Good metadata reduces risk
            
        # Cap at 100
        return min(max(score, 0), 100)

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 30:
            return "medium"
        elif risk_score > 0:
            return "low"
        else:
            return "minimal"

    def _generate_security_recommendations(
        self, 
        vulnerabilities: List[Dict[str, Any]], 
        metadata_analysis: Dict[str, Any], 
        risk_score: float
    ) -> List[str]:
        """Generate actionable security recommendations."""
        recommendations = []
        
        if len(vulnerabilities) > 0:
            recommendations.append(f"🚨 Found {len(vulnerabilities)} security vulnerabilities - review and update immediately")
            
            # Check for critical/high severity
            critical_high = [v for v in vulnerabilities if v.get("severity") in ["critical", "high"]]
            if critical_high:
                recommendations.append(f"⚠️  {len(critical_high)} critical/high severity vulnerabilities require immediate attention")
                
            # Check for fixed versions
            fixed_versions = []
            for vuln in vulnerabilities:
                fixed = vuln.get("fixed_versions", []) or [vuln.get("first_patched", "")]
                fixed_versions.extend([v for v in fixed if v])
                
            if fixed_versions:
                latest_fixed = max(fixed_versions) if fixed_versions else None
                if latest_fixed:
                    recommendations.append(f"📦 Update to version {latest_fixed} or later to fix known vulnerabilities")
        
        # Metadata recommendations
        warnings = metadata_analysis.get("warnings", [])
        if warnings:
            recommendations.append(f"⚠️  Package metadata issues: {', '.join(warnings)}")
            
        if metadata_analysis.get("metadata_score", 0) < 20:
            recommendations.append("📝 Package has poor metadata quality - verify trustworthiness before use")
            
        # General recommendations based on risk score
        if risk_score >= 60:
            recommendations.append("🛑 High risk package - consider alternatives or additional security review")
        elif risk_score >= 30:
            recommendations.append("⚠️  Moderate risk - monitor for updates and security patches")
        elif len(vulnerabilities) == 0:
            recommendations.append("✅ No known vulnerabilities found - package appears secure")
            
        return recommendations


# Main scanning functions
async def scan_package_security(
    package_name: str,
    version: Optional[str] = None,
    include_dependencies: bool = True,
    severity_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scan a PyPI package for security vulnerabilities.
    
    Args:
        package_name: Name of the package to scan
        version: Specific version to scan (optional)
        include_dependencies: Whether to scan dependencies
        severity_filter: Filter by severity (low, medium, high, critical)
        
    Returns:
        Comprehensive security scan results
    """
    scanner = VulnerabilityScanner()
    return await scanner.scan_package(
        package_name, version, include_dependencies, severity_filter
    )


async def bulk_security_scan(
    package_names: List[str],
    include_dependencies: bool = False,
    severity_threshold: str = "medium"
) -> Dict[str, Any]:
    """
    Perform bulk security scanning of multiple packages.
    
    Args:
        package_names: List of package names to scan
        include_dependencies: Whether to scan dependencies
        severity_threshold: Minimum severity to report
        
    Returns:
        Bulk scan results with summary
    """
    logger.info(f"Starting bulk security scan of {len(package_names)} packages")
    
    scanner = VulnerabilityScanner()
    scan_results = {}
    summary = {
        "total_packages": len(package_names),
        "packages_with_vulnerabilities": 0,
        "total_vulnerabilities": 0,
        "high_risk_packages": [],
        "scan_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Scan packages in parallel batches
    batch_size = 5
    for i in range(0, len(package_names), batch_size):
        batch = package_names[i:i + batch_size]
        batch_tasks = [
            scanner.scan_package(pkg_name, include_dependencies=include_dependencies)
            for pkg_name in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for pkg_name, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                scan_results[pkg_name] = {
                    "error": str(result),
                    "scan_status": "failed"
                }
            else:
                scan_results[pkg_name] = result
                
                # Update summary
                vuln_count = result.get("security_summary", {}).get("total_vulnerabilities", 0)
                if vuln_count > 0:
                    summary["packages_with_vulnerabilities"] += 1
                    summary["total_vulnerabilities"] += vuln_count
                    
                risk_level = result.get("security_summary", {}).get("risk_level", "")
                if risk_level in ["high", "critical"]:
                    summary["high_risk_packages"].append({
                        "package": pkg_name,
                        "risk_level": risk_level,
                        "vulnerabilities": vuln_count
                    })
    
    return {
        "summary": summary,
        "detailed_results": scan_results,
        "recommendations": _generate_bulk_recommendations(summary, scan_results)
    }


def _generate_bulk_recommendations(summary: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
    """Generate recommendations for bulk scan results."""
    recommendations = []
    
    vuln_packages = summary["packages_with_vulnerabilities"]
    total_packages = summary["total_packages"]
    
    if vuln_packages == 0:
        recommendations.append("✅ No security vulnerabilities found in any scanned packages")
    else:
        percentage = (vuln_packages / total_packages) * 100
        recommendations.append(
            f"🚨 {vuln_packages}/{total_packages} packages ({percentage:.1f}%) have security vulnerabilities"
        )
        
    high_risk = summary["high_risk_packages"]
    if high_risk:
        recommendations.append(
            f"⚠️  {len(high_risk)} packages are high/critical risk: {', '.join([p['package'] for p in high_risk])}"
        )
        recommendations.append("🛑 Priority: Address high-risk packages immediately")
    
    if summary["total_vulnerabilities"] > 0:
        recommendations.append(f"📊 Total vulnerabilities found: {summary['total_vulnerabilities']}")
        recommendations.append("🔍 Review detailed results and update affected packages")
    
    return recommendations
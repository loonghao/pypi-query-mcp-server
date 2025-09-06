"""License compatibility analysis tools for PyPI packages."""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..core.pypi_client import PyPIClient

logger = logging.getLogger(__name__)


class LicenseCompatibilityAnalyzer:
    """Comprehensive license compatibility analyzer for PyPI packages."""

    def __init__(self):
        self.timeout = 30.0
        
        # License compatibility matrix based on common license interactions
        # Key: primary license, Value: dict of compatible licenses with compatibility level
        self.compatibility_matrix = {
            "MIT": {
                "MIT": "compatible",
                "BSD": "compatible", 
                "Apache-2.0": "compatible",
                "ISC": "compatible",
                "GPL-2.0": "one-way",  # MIT can be used in GPL, not vice versa
                "GPL-3.0": "one-way",
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
            "BSD": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "compatible", 
                "ISC": "compatible",
                "GPL-2.0": "one-way",
                "GPL-3.0": "one-way",
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
            "Apache-2.0": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "compatible",
                "ISC": "compatible",
                "GPL-2.0": "incompatible",  # Patent clause conflicts
                "GPL-3.0": "one-way",  # Apache can go into GPL-3.0
                "LGPL-2.1": "review-required",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
            "GPL-2.0": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "incompatible",
                "ISC": "compatible",
                "GPL-2.0": "compatible",
                "GPL-3.0": "incompatible",  # GPL-2.0 and GPL-3.0 are incompatible
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "incompatible",
                "MPL-2.0": "incompatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "incompatible",
            },
            "GPL-3.0": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "compatible",
                "ISC": "compatible",
                "GPL-2.0": "incompatible",
                "GPL-3.0": "compatible",
                "LGPL-2.1": "review-required",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "incompatible",
            },
            "LGPL-2.1": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "review-required",
                "ISC": "compatible", 
                "GPL-2.0": "compatible",
                "GPL-3.0": "review-required",
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
            "LGPL-3.0": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "compatible",
                "ISC": "compatible",
                "GPL-2.0": "incompatible",
                "GPL-3.0": "compatible",
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
            "MPL-2.0": {
                "MIT": "compatible",
                "BSD": "compatible",
                "Apache-2.0": "compatible",
                "ISC": "compatible",
                "GPL-2.0": "incompatible",
                "GPL-3.0": "compatible",
                "LGPL-2.1": "compatible",
                "LGPL-3.0": "compatible",
                "MPL-2.0": "compatible",
                "Unlicense": "compatible",
                "Public Domain": "compatible",
                "Proprietary": "review-required",
            },
        }
        
        # License categorization for easier analysis
        self.license_categories = {
            "permissive": ["MIT", "BSD", "Apache-2.0", "ISC", "Unlicense", "Public Domain"],
            "copyleft_weak": ["LGPL-2.1", "LGPL-3.0", "MPL-2.0"],
            "copyleft_strong": ["GPL-2.0", "GPL-3.0", "AGPL-3.0"],
            "proprietary": ["Proprietary", "Commercial", "All Rights Reserved"],
            "unknown": ["Unknown", "Other", "Custom"],
        }
        
        # Common license normalization patterns
        self.license_patterns = {
            r"MIT\s*License": "MIT",
            r"BSD\s*3[-\s]*Clause": "BSD",
            r"BSD\s*2[-\s]*Clause": "BSD",
            r"Apache\s*2\.0": "Apache-2.0",
            r"Apache\s*License\s*2\.0": "Apache-2.0",
            r"GNU\s*General\s*Public\s*License\s*v?2": "GPL-2.0", 
            r"GNU\s*General\s*Public\s*License\s*v?3": "GPL-3.0",
            r"GNU\s*Lesser\s*General\s*Public\s*License\s*v?2": "LGPL-2.1",
            r"GNU\s*Lesser\s*General\s*Public\s*License\s*v?3": "LGPL-3.0",
            r"Mozilla\s*Public\s*License\s*2\.0": "MPL-2.0",
            r"ISC\s*License": "ISC",
            r"Unlicense": "Unlicense",
            r"Public\s*Domain": "Public Domain",
        }

    async def analyze_package_license(
        self, 
        package_name: str,
        version: Optional[str] = None,
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze license information for a PyPI package.
        
        Args:
            package_name: Name of the package to analyze
            version: Specific version to analyze (optional)
            include_dependencies: Whether to analyze dependency licenses
            
        Returns:
            Dictionary containing license analysis results
        """
        logger.info(f"Starting license analysis for package: {package_name}")
        
        try:
            async with PyPIClient() as client:
                package_data = await client.get_package_info(package_name, version)
                
            package_version = version or package_data["info"]["version"]
            
            # Analyze package license
            license_info = self._extract_license_info(package_data)
            
            # Analyze dependencies if requested
            dependency_licenses = []
            if include_dependencies:
                dependency_licenses = await self._analyze_dependency_licenses(
                    package_name, package_version
                )
            
            # Generate compatibility analysis
            compatibility_analysis = self._analyze_license_compatibility(
                license_info, dependency_licenses
            )
            
            # Calculate risk assessment
            risk_assessment = self._assess_license_risks(
                license_info, dependency_licenses, compatibility_analysis
            )
            
            return {
                "package": package_name,
                "version": package_version,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "license_info": license_info,
                "dependency_licenses": dependency_licenses,
                "compatibility_analysis": compatibility_analysis,
                "risk_assessment": risk_assessment,
                "recommendations": self._generate_license_recommendations(
                    license_info, dependency_licenses, compatibility_analysis, risk_assessment
                ),
                "analysis_summary": {
                    "total_dependencies_analyzed": len(dependency_licenses),
                    "unique_licenses_found": len(set(
                        [license_info.get("normalized_license", "Unknown")] + 
                        [dep.get("normalized_license", "Unknown") for dep in dependency_licenses]
                    )),
                    "license_conflicts": len(compatibility_analysis.get("conflicts", [])),
                    "review_required_count": len(compatibility_analysis.get("review_required", [])),
                }
            }
            
        except Exception as e:
            logger.error(f"License analysis failed for {package_name}: {e}")
            raise SearchError(f"License analysis failed: {e}") from e

    def _extract_license_info(self, package_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize license information from package data."""
        info = package_data.get("info", {})
        
        # Extract license from multiple sources
        license_field = info.get("license", "")
        license_classifier = self._extract_license_from_classifiers(
            info.get("classifiers", [])
        )
        
        # Normalize license
        normalized_license = self._normalize_license(license_field or license_classifier)
        
        # Categorize license
        license_category = self._categorize_license(normalized_license)
        
        return {
            "raw_license": license_field,
            "classifier_license": license_classifier,
            "normalized_license": normalized_license,
            "license_category": license_category,
            "license_url": self._extract_license_url(info),
            "license_confidence": self._assess_license_confidence(
                license_field, license_classifier, normalized_license
            ),
        }

    def _extract_license_from_classifiers(self, classifiers: List[str]) -> str:
        """Extract license information from PyPI classifiers."""
        license_classifiers = [
            c for c in classifiers if c.startswith("License ::")
        ]
        
        if not license_classifiers:
            return ""
            
        # Return the most specific license classifier
        return license_classifiers[-1].replace("License ::", "").strip()

    def _normalize_license(self, license_text: str) -> str:
        """Normalize license text to standard SPDX identifiers."""
        if not license_text:
            return "Unknown"
            
        license_text_clean = license_text.strip()
        
        # Check for exact matches first
        common_licenses = {
            "MIT": "MIT",
            "BSD": "BSD", 
            "Apache": "Apache-2.0",
            "GPL": "GPL-3.0",  # Default to GPL-3.0 if version unspecified
            "LGPL": "LGPL-3.0",
            "MPL": "MPL-2.0",
        }
        
        if license_text_clean in common_licenses:
            return common_licenses[license_text_clean]
        
        # Pattern matching
        for pattern, normalized in self.license_patterns.items():
            if re.search(pattern, license_text_clean, re.IGNORECASE):
                return normalized
        
        # Check if it contains known license names
        license_lower = license_text_clean.lower()
        if "mit" in license_lower:
            return "MIT"
        elif "bsd" in license_lower:
            return "BSD"
        elif "apache" in license_lower:
            return "Apache-2.0"
        elif "gpl" in license_lower and "lgpl" not in license_lower:
            return "GPL-3.0"
        elif "lgpl" in license_lower:
            return "LGPL-3.0"
        elif "mozilla" in license_lower or "mpl" in license_lower:
            return "MPL-2.0"
        elif "unlicense" in license_lower:
            return "Unlicense"
        elif "public domain" in license_lower:
            return "Public Domain"
        elif any(prop in license_lower for prop in ["proprietary", "commercial", "all rights reserved"]):
            return "Proprietary"
        
        return "Other"

    def _categorize_license(self, normalized_license: str) -> str:
        """Categorize license into major categories."""
        for category, licenses in self.license_categories.items():
            if normalized_license in licenses:
                return category
        return "unknown"

    def _extract_license_url(self, info: Dict[str, Any]) -> str:
        """Extract license URL from package info."""
        # Check project URLs
        project_urls = info.get("project_urls", {}) or {}
        for key, url in project_urls.items():
            if "license" in key.lower():
                return url
                
        # Check home page for license info
        home_page = info.get("home_page", "")
        if home_page and "github.com" in home_page:
            return f"{home_page.rstrip('/')}/blob/main/LICENSE"
            
        return ""

    def _assess_license_confidence(
        self, raw_license: str, classifier_license: str, normalized_license: str
    ) -> str:
        """Assess confidence level in license detection."""
        if not raw_license and not classifier_license:
            return "low"
        
        if normalized_license == "Unknown" or normalized_license == "Other":
            return "low"
            
        if raw_license and classifier_license and raw_license in classifier_license:
            return "high"
        elif raw_license or classifier_license:
            return "medium"
        else:
            return "low"

    async def _analyze_dependency_licenses(
        self, package_name: str, version: str
    ) -> List[Dict[str, Any]]:
        """Analyze licenses of package dependencies."""
        try:
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
                
                # Analyze dependency licenses (limit to top 15 to avoid overwhelming)
                dependency_licenses = []
                
                for dep_name in dependencies[:15]:
                    try:
                        dep_data = await client.get_package_info(dep_name)
                        dep_license_info = self._extract_license_info(dep_data)
                        
                        dependency_licenses.append({
                            "package": dep_name,
                            "version": dep_data.get("info", {}).get("version", ""),
                            **dep_license_info
                        })
                    except Exception as e:
                        logger.debug(f"Failed to analyze license for dependency {dep_name}: {e}")
                        dependency_licenses.append({
                            "package": dep_name,
                            "version": "",
                            "normalized_license": "Unknown",
                            "license_category": "unknown",
                            "license_confidence": "low",
                            "error": str(e)
                        })
                        
                return dependency_licenses
            
        except Exception as e:
            logger.warning(f"Dependency license analysis failed: {e}")
            return []

    def _analyze_license_compatibility(
        self, package_license: Dict[str, Any], dependency_licenses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze license compatibility between package and its dependencies."""
        main_license = package_license.get("normalized_license", "Unknown")
        
        compatible = []
        incompatible = []
        review_required = []
        one_way = []
        unknown = []
        
        for dep in dependency_licenses:
            dep_license = dep.get("normalized_license", "Unknown")
            dep_package = dep.get("package", "unknown")
            
            if main_license == "Unknown" or dep_license == "Unknown":
                unknown.append({
                    "package": dep_package,
                    "license": dep_license,
                    "reason": "License information unavailable"
                })
                continue
            
            compatibility = self._check_license_compatibility(main_license, dep_license)
            
            if compatibility == "compatible":
                compatible.append({
                    "package": dep_package,
                    "license": dep_license,
                })
            elif compatibility == "incompatible":
                incompatible.append({
                    "package": dep_package,
                    "license": dep_license,
                    "reason": f"{main_license} and {dep_license} are incompatible"
                })
            elif compatibility == "review-required":
                review_required.append({
                    "package": dep_package,
                    "license": dep_license,
                    "reason": f"Manual review needed for {main_license} + {dep_license}"
                })
            elif compatibility == "one-way":
                one_way.append({
                    "package": dep_package,
                    "license": dep_license,
                    "reason": f"{dep_license} can be used in {main_license} project"
                })
        
        return {
            "main_license": main_license,
            "compatible": compatible,
            "incompatible": incompatible,
            "review_required": review_required,
            "one_way": one_way,
            "unknown": unknown,
            "conflicts": incompatible,  # Alias for easier access
        }

    def _check_license_compatibility(self, license1: str, license2: str) -> str:
        """Check compatibility between two licenses."""
        if license1 in self.compatibility_matrix:
            return self.compatibility_matrix[license1].get(license2, "unknown")
        
        # Fallback compatibility rules
        if license1 == license2:
            return "compatible"
        
        # Default to review required for unknown combinations
        return "review-required"

    def _assess_license_risks(
        self, 
        package_license: Dict[str, Any], 
        dependency_licenses: List[Dict[str, Any]], 
        compatibility_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall license risks for the project."""
        risks = []
        risk_score = 0
        
        main_license = package_license.get("normalized_license", "Unknown")
        main_category = package_license.get("license_category", "unknown")
        
        # Check for incompatible licenses
        incompatible_count = len(compatibility_analysis.get("incompatible", []))
        if incompatible_count > 0:
            risks.append(f"Found {incompatible_count} incompatible license(s)")
            risk_score += incompatible_count * 30
        
        # Check for unknown licenses
        unknown_count = len(compatibility_analysis.get("unknown", []))
        if unknown_count > 0:
            risks.append(f"Found {unknown_count} dependency(ies) with unknown licenses")
            risk_score += unknown_count * 10
        
        # Check for review-required licenses
        review_count = len(compatibility_analysis.get("review_required", []))
        if review_count > 0:
            risks.append(f"Found {review_count} license(s) requiring manual review")
            risk_score += review_count * 15
        
        # Check for copyleft contamination risk
        if main_category == "permissive":
            copyleft_deps = [
                dep for dep in dependency_licenses 
                if dep.get("license_category") in ["copyleft_weak", "copyleft_strong"]
            ]
            if copyleft_deps:
                risks.append(f"Permissive project using {len(copyleft_deps)} copyleft dependencies")
                risk_score += len(copyleft_deps) * 20
        
        # Check for proprietary license risks
        proprietary_deps = [
            dep for dep in dependency_licenses 
            if dep.get("license_category") == "proprietary"
        ]
        if proprietary_deps:
            risks.append(f"Found {len(proprietary_deps)} proprietary dependencies")
            risk_score += len(proprietary_deps) * 25
        
        # Calculate risk level
        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        elif risk_score > 0:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "risk_factors": risks,
            "compliance_status": "compliant" if risk_score < 25 else "review-needed",
        }

    def _generate_license_recommendations(
        self,
        package_license: Dict[str, Any],
        dependency_licenses: List[Dict[str, Any]],
        compatibility_analysis: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable license recommendations."""
        recommendations = []
        
        main_license = package_license.get("normalized_license", "Unknown")
        risk_level = risk_assessment.get("risk_level", "unknown")
        
        # High-level recommendations based on risk
        if risk_level == "critical":
            recommendations.append("🚨 Critical license issues detected - immediate legal review required")
        elif risk_level == "high":
            recommendations.append("⚠️  High license risk - review and resolve conflicts before release")
        elif risk_level == "medium":
            recommendations.append("⚠️  Moderate license risk - review recommendations below")
        elif risk_level == "minimal":
            recommendations.append("✅ License compatibility appears good")
        
        # Specific recommendations for incompatible licenses
        incompatible = compatibility_analysis.get("incompatible", [])
        if incompatible:
            recommendations.append(f"🔴 Remove or replace {len(incompatible)} incompatible dependencies:")
            for dep in incompatible[:3]:  # Show first 3
                recommendations.append(f"  - {dep['package']} ({dep['license']}): {dep.get('reason', '')}")
        
        # Recommendations for review-required licenses
        review_required = compatibility_analysis.get("review_required", [])
        if review_required:
            recommendations.append(f"📋 Manual review needed for {len(review_required)} dependencies:")
            for dep in review_required[:3]:
                recommendations.append(f"  - {dep['package']} ({dep['license']})")
        
        # Unknown license recommendations
        unknown = compatibility_analysis.get("unknown", [])
        if unknown:
            recommendations.append(f"❓ Investigate {len(unknown)} dependencies with unknown licenses")
        
        # License confidence recommendations
        if package_license.get("license_confidence") == "low":
            recommendations.append("📝 Consider adding clear license information to your package")
        
        # Category-specific recommendations
        main_category = package_license.get("license_category", "unknown")
        if main_category == "copyleft_strong":
            recommendations.append("ℹ️  GPL license requires derivative works to also be GPL")
        elif main_category == "permissive":
            recommendations.append("ℹ️  Permissive license allows flexible usage")
        
        return recommendations


# Main analysis functions
async def analyze_package_license_compatibility(
    package_name: str,
    version: Optional[str] = None,
    include_dependencies: bool = True
) -> Dict[str, Any]:
    """
    Analyze license compatibility for a PyPI package.
    
    Args:
        package_name: Name of the package to analyze
        version: Specific version to analyze (optional)
        include_dependencies: Whether to analyze dependency licenses
        
    Returns:
        Comprehensive license compatibility analysis
    """
    analyzer = LicenseCompatibilityAnalyzer()
    return await analyzer.analyze_package_license(
        package_name, version, include_dependencies
    )


async def check_license_compliance_bulk(
    package_names: List[str],
    target_license: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check license compliance for multiple packages.
    
    Args:
        package_names: List of package names to check
        target_license: Target license for compatibility checking
        
    Returns:
        Bulk license compliance report
    """
    logger.info(f"Starting bulk license compliance check for {len(package_names)} packages")
    
    analyzer = LicenseCompatibilityAnalyzer()
    results = {}
    summary = {
        "total_packages": len(package_names),
        "compliant_packages": 0,
        "non_compliant_packages": 0,
        "unknown_license_packages": 0,
        "high_risk_packages": [],
        "analysis_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # Analyze packages in parallel batches
    batch_size = 5
    for i in range(0, len(package_names), batch_size):
        batch = package_names[i:i + batch_size]
        batch_tasks = [
            analyzer.analyze_package_license(pkg_name, include_dependencies=False)
            for pkg_name in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for pkg_name, result in zip(batch, batch_results):
            if isinstance(result, Exception):
                results[pkg_name] = {
                    "error": str(result),
                    "analysis_status": "failed"
                }
                summary["unknown_license_packages"] += 1
            else:
                results[pkg_name] = result
                
                # Update summary
                risk_level = result.get("risk_assessment", {}).get("risk_level", "unknown")
                if risk_level in ["minimal", "low"]:
                    summary["compliant_packages"] += 1
                else:
                    summary["non_compliant_packages"] += 1
                    
                if risk_level in ["high", "critical"]:
                    summary["high_risk_packages"].append({
                        "package": pkg_name,
                        "license": result.get("license_info", {}).get("normalized_license", "Unknown"),
                        "risk_level": risk_level
                    })
    
    return {
        "summary": summary,
        "detailed_results": results,
        "target_license": target_license,
        "recommendations": _generate_bulk_license_recommendations(summary, results)
    }


def _generate_bulk_license_recommendations(summary: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
    """Generate recommendations for bulk license analysis."""
    recommendations = []
    
    compliant = summary["compliant_packages"]
    total = summary["total_packages"]
    
    if compliant == total:
        recommendations.append("✅ All packages appear to have compliant licenses")
    else:
        non_compliant = summary["non_compliant_packages"]
        percentage = (non_compliant / total) * 100
        recommendations.append(
            f"⚠️  {non_compliant}/{total} packages ({percentage:.1f}%) have license compliance issues"
        )
    
    high_risk = summary["high_risk_packages"]
    if high_risk:
        recommendations.append(
            f"🚨 {len(high_risk)} packages are high risk: {', '.join([p['package'] for p in high_risk])}"
        )
        recommendations.append("Priority: Address high-risk packages immediately")
    
    unknown = summary["unknown_license_packages"]
    if unknown > 0:
        recommendations.append(f"❓ {unknown} packages have unknown or unclear licenses")
        recommendations.append("Consider investigating these packages for license clarity")
    
    return recommendations
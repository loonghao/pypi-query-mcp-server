"""Requirements file parsing and analysis tools for Python projects."""

import asyncio
import logging
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.exceptions import InvalidPackageNameError, NetworkError, SearchError
from ..core.pypi_client import PyPIClient

logger = logging.getLogger(__name__)


class RequirementsAnalyzer:
    """Comprehensive requirements file analyzer for Python projects."""

    def __init__(self):
        self.timeout = 30.0
        
        # Supported requirement file patterns
        self.requirement_patterns = {
            "requirements.txt": r"requirements.*\.txt",
            "pyproject.toml": r"pyproject\.toml",
            "setup.py": r"setup\.py",
            "Pipfile": r"Pipfile",
            "poetry.lock": r"poetry\.lock",
            "conda.yml": r"(conda|environment)\.ya?ml",
        }
        
        # Version specifier patterns
        self.version_patterns = {
            "exact": r"==\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "gte": r">=\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "gt": r">\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "lte": r"<=\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "lt": r"<\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "compatible": r"~=\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
            "not_equal": r"!=\s*([0-9]+(?:\.[0-9]+)*(?:[a-zA-Z][0-9]*)?)",
        }

    async def analyze_requirements_file(
        self,
        file_path: str,
        check_updates: bool = True,
        security_scan: bool = True,
        compatibility_check: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a requirements file for dependencies, versions, security, and compatibility.
        
        Args:
            file_path: Path to the requirements file
            check_updates: Whether to check for package updates
            security_scan: Whether to perform security vulnerability scanning  
            compatibility_check: Whether to check Python version compatibility
            
        Returns:
            Dictionary containing comprehensive requirements analysis
        """
        logger.info(f"Starting requirements analysis for: {file_path}")
        
        try:
            # Parse requirements file
            parsed_requirements = await self._parse_requirements_file(file_path)
            
            if not parsed_requirements["dependencies"]:
                return {
                    "file_path": file_path,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "file_info": parsed_requirements["file_info"],
                    "dependencies": [],
                    "analysis_summary": {
                        "total_dependencies": 0,
                        "outdated_packages": 0,
                        "security_vulnerabilities": 0,
                        "compatibility_issues": 0,
                    },
                    "recommendations": ["No dependencies found to analyze"],
                    "error": "No dependencies found in requirements file"
                }
            
            # Analyze dependencies in parallel
            analysis_tasks = []
            
            # Basic dependency analysis (always done)
            analysis_tasks.append(self._analyze_dependency_health(parsed_requirements["dependencies"]))
            
            # Optional analyses
            if check_updates:
                analysis_tasks.append(self._check_package_updates(parsed_requirements["dependencies"]))
            else:
                analysis_tasks.append(asyncio.create_task(self._empty_updates_result()))
            
            if security_scan:
                analysis_tasks.append(self._scan_dependencies_security(parsed_requirements["dependencies"]))
            else:
                analysis_tasks.append(asyncio.create_task(self._empty_security_result()))
                
            if compatibility_check:
                python_version = parsed_requirements.get("python_version")
                analysis_tasks.append(self._check_dependencies_compatibility(parsed_requirements["dependencies"], python_version))
            else:
                analysis_tasks.append(asyncio.create_task(self._empty_compatibility_result()))
            
            # Execute analyses
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Unpack results
            health_analysis = results[0] if not isinstance(results[0], Exception) else {"healthy": [], "issues": []}
            update_analysis = results[1] if not isinstance(results[1], Exception) else {"outdated": [], "current": []}
            security_analysis = results[2] if not isinstance(results[2], Exception) else {"vulnerabilities": [], "secure": []}
            compatibility_analysis = results[3] if not isinstance(results[3], Exception) else {"compatible": [], "incompatible": []}
            
            # Generate comprehensive analysis
            analysis_summary = self._generate_analysis_summary(
                parsed_requirements["dependencies"],
                health_analysis,
                update_analysis, 
                security_analysis,
                compatibility_analysis
            )
            
            recommendations = self._generate_requirements_recommendations(
                parsed_requirements,
                health_analysis,
                update_analysis,
                security_analysis,
                compatibility_analysis,
                analysis_summary
            )
            
            return {
                "file_path": file_path,
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "file_info": parsed_requirements["file_info"],
                "dependencies": parsed_requirements["dependencies"],
                "dependency_analysis": {
                    "health": health_analysis,
                    "updates": update_analysis if check_updates else None,
                    "security": security_analysis if security_scan else None,
                    "compatibility": compatibility_analysis if compatibility_check else None,
                },
                "analysis_summary": analysis_summary,
                "recommendations": recommendations,
                "python_requirements": parsed_requirements.get("python_version"),
            }
            
        except Exception as e:
            logger.error(f"Requirements analysis failed for {file_path}: {e}")
            raise SearchError(f"Requirements analysis failed: {e}") from e

    async def _parse_requirements_file(self, file_path: str) -> Dict[str, Any]:
        """Parse requirements from various file formats."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {file_path}")
        
        file_info = {
            "name": path.name,
            "format": self._detect_file_format(path.name),
            "size_bytes": path.stat().st_size,
            "modified_time": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        }
        
        # Parse based on file format
        if path.name.endswith('.txt'):
            dependencies, python_version = await self._parse_requirements_txt(path)
        elif path.name == 'pyproject.toml':
            dependencies, python_version = await self._parse_pyproject_toml(path)
        elif path.name == 'setup.py':
            dependencies, python_version = await self._parse_setup_py(path)
        elif path.name == 'Pipfile':
            dependencies, python_version = await self._parse_pipfile(path)
        elif path.name.endswith('.yml') or path.name.endswith('.yaml'):
            dependencies, python_version = await self._parse_conda_yml(path)
        else:
            # Try to parse as requirements.txt format
            dependencies, python_version = await self._parse_requirements_txt(path)
        
        return {
            "file_info": file_info,
            "dependencies": dependencies,
            "python_version": python_version,
        }

    def _detect_file_format(self, filename: str) -> str:
        """Detect requirements file format."""
        filename_lower = filename.lower()
        
        for fmt, pattern in self.requirement_patterns.items():
            if re.match(pattern, filename_lower):
                return fmt
        
        return "unknown"

    async def _parse_requirements_txt(self, path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Parse requirements.txt format files."""
        dependencies = []
        python_version = None
        
        try:
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Skip -r and -e directives (for now)
                if line.startswith(('-r', '-e', '--')):
                    continue
                
                # Parse requirement line
                dep = self._parse_requirement_line(line, line_num)
                if dep:
                    dependencies.append(dep)
                    
        except Exception as e:
            logger.warning(f"Failed to parse requirements.txt {path}: {e}")
            
        return dependencies, python_version

    async def _parse_pyproject_toml(self, path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Parse pyproject.toml files."""
        dependencies = []
        python_version = None
        
        try:
            content = path.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            
            # Extract Python version requirement
            build_system = data.get("build-system", {})
            project = data.get("project", {})
            tool_poetry = data.get("tool", {}).get("poetry", {})
            
            # Check for Python version in different places
            if project.get("requires-python"):
                python_version = project["requires-python"]
            elif tool_poetry.get("dependencies", {}).get("python"):
                python_version = tool_poetry["dependencies"]["python"]
            
            # Extract dependencies from project.dependencies
            if "dependencies" in project:
                for dep_line in project["dependencies"]:
                    dep = self._parse_requirement_line(dep_line, 0)
                    if dep:
                        dependencies.append(dep)
            
            # Extract from tool.poetry.dependencies
            if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
                poetry_deps = data["tool"]["poetry"]["dependencies"]
                for name, version_spec in poetry_deps.items():
                    if name.lower() == "python":
                        continue  # Skip Python version
                    
                    if isinstance(version_spec, str):
                        req_line = f"{name}{version_spec}" if version_spec.startswith(('=', '<', '>', '~', '^', '!')) else f"{name}=={version_spec}"
                    else:
                        # Handle complex version specifications
                        req_line = f"{name}>={version_spec.get('version', '0.0.0')}"
                    
                    dep = self._parse_requirement_line(req_line, 0)
                    if dep:
                        dependencies.append(dep)
                        
        except Exception as e:
            logger.warning(f"Failed to parse pyproject.toml {path}: {e}")
            
        return dependencies, python_version

    async def _parse_setup_py(self, path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Parse setup.py files (basic extraction)."""
        dependencies = []
        python_version = None
        
        try:
            content = path.read_text(encoding="utf-8")
            
            # Look for install_requires
            install_requires_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if install_requires_match:
                deps_text = install_requires_match.group(1)
                # Extract quoted strings
                quoted_deps = re.findall(r'["\']([^"\']+)["\']', deps_text)
                
                for dep_line in quoted_deps:
                    dep = self._parse_requirement_line(dep_line, 0)
                    if dep:
                        dependencies.append(dep)
            
            # Look for python_requires
            python_requires_match = re.search(r"python_requires\s*=\s*[\"']([^\"']+)[\"']", content)
            if python_requires_match:
                python_version = python_requires_match.group(1)
                
        except Exception as e:
            logger.warning(f"Failed to parse setup.py {path}: {e}")
            
        return dependencies, python_version

    async def _parse_pipfile(self, path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Parse Pipfile format."""
        dependencies = []
        python_version = None
        
        try:
            content = path.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            
            # Extract Python version
            if "requires" in data and "python_version" in data["requires"]:
                python_version = f">={data['requires']['python_version']}"
            
            # Extract packages
            for section in ["packages", "dev-packages"]:
                if section in data:
                    for name, version_spec in data[section].items():
                        if isinstance(version_spec, str):
                            req_line = f"{name}{version_spec}" if version_spec.startswith(('=', '<', '>', '~', '^', '!')) else f"{name}=={version_spec}"
                        else:
                            req_line = f"{name}>={version_spec.get('version', '0.0.0')}"
                        
                        dep = self._parse_requirement_line(req_line, 0)
                        if dep:
                            dep["dev_dependency"] = (section == "dev-packages")
                            dependencies.append(dep)
                            
        except Exception as e:
            logger.warning(f"Failed to parse Pipfile {path}: {e}")
            
        return dependencies, python_version

    async def _parse_conda_yml(self, path: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """Parse conda environment.yml files."""
        dependencies = []
        python_version = None
        
        try:
            import yaml
            
            content = path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
            
            if "dependencies" in data:
                for dep in data["dependencies"]:
                    if isinstance(dep, str):
                        if dep.startswith("python"):
                            # Extract Python version
                            python_match = re.search(r"python\s*([><=~!]+)\s*([0-9.]+)", dep)
                            if python_match:
                                python_version = f"{python_match.group(1)}{python_match.group(2)}"
                        else:
                            parsed_dep = self._parse_requirement_line(dep, 0)
                            if parsed_dep:
                                dependencies.append(parsed_dep)
                                
        except Exception as e:
            logger.warning(f"Failed to parse conda.yml {path}: {e}")
            
        return dependencies, python_version

    def _parse_requirement_line(self, line: str, line_number: int) -> Optional[Dict[str, Any]]:
        """Parse a single requirement line."""
        try:
            # Remove inline comments
            if '#' in line:
                line = line[:line.index('#')].strip()
            
            if not line:
                return None
            
            # Handle extras (package[extra1,extra2])
            extras = []
            extras_match = re.search(r'\[([^\]]+)\]', line)
            if extras_match:
                extras = [e.strip() for e in extras_match.group(1).split(',')]
                line = re.sub(r'\[([^\]]+)\]', '', line)
            
            # Parse package name and version specifiers
            # Split on version operators
            version_ops = ['>=', '<=', '==', '!=', '~=', '>', '<']
            package_name = line
            version_specifiers = []
            
            for op in version_ops:
                if op in line:
                    parts = line.split(op)
                    package_name = parts[0].strip()
                    if len(parts) > 1:
                        version_specifiers.append({
                            "operator": op,
                            "version": parts[1].strip().split(',')[0].strip()
                        })
                    break
            
            # Handle comma-separated version specs
            if ',' in line and version_specifiers:
                remaining = line.split(version_specifiers[0]["operator"], 1)[1]
                for spec in remaining.split(',')[1:]:
                    spec = spec.strip()
                    for op in version_ops:
                        if spec.startswith(op):
                            version_specifiers.append({
                                "operator": op,
                                "version": spec[len(op):].strip()
                            })
                            break
            
            # Clean package name
            package_name = re.sub(r'[<>=!~,\s].*', '', package_name).strip()
            
            if not package_name:
                return None
            
            return {
                "name": package_name,
                "version_specifiers": version_specifiers,
                "extras": extras,
                "line_number": line_number,
                "raw_line": line.strip(),
            }
            
        except Exception as e:
            logger.debug(f"Failed to parse requirement line '{line}': {e}")
            return None

    async def _analyze_dependency_health(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall health of dependencies."""
        healthy = []
        issues = []
        
        for dep in dependencies:
            name = dep["name"]
            version_specs = dep["version_specifiers"]
            
            # Check for problematic version specifications
            health_issues = []
            
            if not version_specs:
                health_issues.append("No version constraint (could lead to instability)")
            else:
                # Check for overly restrictive versions
                exact_versions = [spec for spec in version_specs if spec["operator"] == "=="]
                if exact_versions:
                    health_issues.append("Exact version pinning (may cause conflicts)")
                
                # Check for very loose constraints
                loose_constraints = [spec for spec in version_specs if spec["operator"] in [">", ">="]]
                if loose_constraints and not any(spec["operator"] in ["<", "<="] for spec in version_specs):
                    health_issues.append("No upper bound (may break with future versions)")
            
            if health_issues:
                issues.append({
                    "package": name,
                    "issues": health_issues,
                    "current_spec": version_specs
                })
            else:
                healthy.append({
                    "package": name,
                    "version_spec": version_specs
                })
        
        return {
            "healthy": healthy,
            "issues": issues,
            "health_score": len(healthy) / len(dependencies) * 100 if dependencies else 0
        }

    async def _check_package_updates(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for available package updates."""
        outdated = []
        current = []
        
        async with PyPIClient() as client:
            # Process in batches to avoid overwhelming PyPI
            batch_size = 10
            for i in range(0, len(dependencies), batch_size):
                batch = dependencies[i:i + batch_size]
                batch_tasks = []
                
                for dep in batch:
                    task = self._check_single_package_update(client, dep)
                    batch_tasks.append(task)
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for dep, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.debug(f"Failed to check updates for {dep['name']}: {result}")
                        continue
                    
                    if result["has_update"]:
                        outdated.append(result)
                    else:
                        current.append(result)
        
        return {
            "outdated": outdated,
            "current": current,
            "update_percentage": len(outdated) / len(dependencies) * 100 if dependencies else 0
        }

    async def _check_single_package_update(self, client: PyPIClient, dep: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a single package has updates available."""
        try:
            package_data = await client.get_package_info(dep["name"])
            latest_version = package_data["info"]["version"]
            
            # For now, we'll do a simple comparison
            # In a real implementation, you'd want proper version comparison
            has_update = True  # Placeholder logic
            
            return {
                "package": dep["name"],
                "current_spec": dep["version_specifiers"],
                "latest_version": latest_version,
                "has_update": has_update,
                "update_recommendation": f"Update to {latest_version}"
            }
            
        except Exception as e:
            return {
                "package": dep["name"],
                "current_spec": dep["version_specifiers"],
                "latest_version": "unknown",
                "has_update": False,
                "error": str(e)
            }

    async def _scan_dependencies_security(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scan dependencies for security vulnerabilities."""
        # Import security scanner if available
        try:
            from .security import scan_package_security
            
            vulnerabilities = []
            secure = []
            
            # Process in small batches
            batch_size = 5
            for i in range(0, len(dependencies), batch_size):
                batch = dependencies[i:i + batch_size]
                batch_tasks = []
                
                for dep in batch:
                    task = self._scan_single_dependency_security(dep)
                    batch_tasks.append(task)
                
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                for dep, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.debug(f"Failed to scan security for {dep['name']}: {result}")
                        continue
                    
                    if result["vulnerabilities"]:
                        vulnerabilities.append(result)
                    else:
                        secure.append(result)
            
            return {
                "vulnerabilities": vulnerabilities,
                "secure": secure,
                "vulnerability_count": sum(len(v["vulnerabilities"]) for v in vulnerabilities),
            }
            
        except ImportError:
            logger.warning("Security scanner not available")
            return await self._empty_security_result()

    async def _scan_single_dependency_security(self, dep: Dict[str, Any]) -> Dict[str, Any]:
        """Scan a single dependency for security issues."""
        try:
            from .security import scan_package_security
            
            result = await scan_package_security(
                dep["name"], 
                version=None,  # Latest version
                include_dependencies=False
            )
            
            vuln_summary = result.get("security_summary", {})
            return {
                "package": dep["name"],
                "vulnerabilities": result.get("vulnerabilities", {}).get("direct", []),
                "risk_level": vuln_summary.get("risk_level", "minimal"),
                "total_vulnerabilities": vuln_summary.get("total_vulnerabilities", 0)
            }
            
        except Exception as e:
            return {
                "package": dep["name"],
                "vulnerabilities": [],
                "risk_level": "unknown",
                "error": str(e)
            }

    async def _check_dependencies_compatibility(
        self, dependencies: List[Dict[str, Any]], python_version: Optional[str]
    ) -> Dict[str, Any]:
        """Check Python version compatibility for dependencies."""
        if not python_version:
            return await self._empty_compatibility_result()
        
        compatible = []
        incompatible = []
        
        # Process in batches
        batch_size = 10
        for i in range(0, len(dependencies), batch_size):
            batch = dependencies[i:i + batch_size]
            batch_tasks = []
            
            for dep in batch:
                task = self._check_single_dependency_compatibility(dep, python_version)
                batch_tasks.append(task)
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for dep, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.debug(f"Failed to check compatibility for {dep['name']}: {result}")
                    continue
                
                if result["compatible"]:
                    compatible.append(result)
                else:
                    incompatible.append(result)
        
        return {
            "compatible": compatible,
            "incompatible": incompatible,
            "python_version": python_version,
            "compatibility_percentage": len(compatible) / len(dependencies) * 100 if dependencies else 0
        }

    async def _check_single_dependency_compatibility(
        self, dep: Dict[str, Any], python_version: str
    ) -> Dict[str, Any]:
        """Check compatibility for a single dependency."""
        try:
            from .compatibility_check import check_python_compatibility
            
            # Extract target Python version (simplified)
            target_version = "3.9"  # Default fallback
            version_match = re.search(r'(\d+\.\d+)', python_version)
            if version_match:
                target_version = version_match.group(1)
            
            result = await check_python_compatibility(dep["name"], target_version)
            
            return {
                "package": dep["name"],
                "compatible": result.get("compatible", False),
                "python_version": target_version,
                "details": result.get("compatibility_info", "")
            }
            
        except Exception as e:
            return {
                "package": dep["name"],
                "compatible": True,  # Assume compatible on error
                "python_version": python_version,
                "error": str(e)
            }

    # Helper methods for empty results
    async def _empty_updates_result(self) -> Dict[str, Any]:
        return {"outdated": [], "current": [], "update_percentage": 0}

    async def _empty_security_result(self) -> Dict[str, Any]:
        return {"vulnerabilities": [], "secure": [], "vulnerability_count": 0}

    async def _empty_compatibility_result(self) -> Dict[str, Any]:
        return {"compatible": [], "incompatible": [], "python_version": None, "compatibility_percentage": 100}

    def _generate_analysis_summary(
        self,
        dependencies: List[Dict[str, Any]],
        health_analysis: Dict[str, Any],
        update_analysis: Dict[str, Any],
        security_analysis: Dict[str, Any],
        compatibility_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive analysis summary."""
        return {
            "total_dependencies": len(dependencies),
            "health_score": round(health_analysis.get("health_score", 0), 1),
            "packages_with_issues": len(health_analysis.get("issues", [])),
            "outdated_packages": len(update_analysis.get("outdated", [])),
            "security_vulnerabilities": security_analysis.get("vulnerability_count", 0),
            "compatibility_issues": len(compatibility_analysis.get("incompatible", [])),
            "overall_risk_level": self._calculate_overall_risk_level(
                health_analysis, update_analysis, security_analysis, compatibility_analysis
            )
        }

    def _calculate_overall_risk_level(
        self, health: Dict[str, Any], updates: Dict[str, Any], 
        security: Dict[str, Any], compatibility: Dict[str, Any]
    ) -> str:
        """Calculate overall risk level for the project."""
        risk_score = 0
        
        # Health risks
        health_score = health.get("health_score", 100)
        if health_score < 50:
            risk_score += 30
        elif health_score < 75:
            risk_score += 15
        
        # Security risks
        vuln_count = security.get("vulnerability_count", 0)
        if vuln_count > 10:
            risk_score += 40
        elif vuln_count > 5:
            risk_score += 25
        elif vuln_count > 0:
            risk_score += 15
        
        # Compatibility risks
        incompat_count = len(compatibility.get("incompatible", []))
        if incompat_count > 5:
            risk_score += 25
        elif incompat_count > 0:
            risk_score += 10
        
        # Update risks (outdated packages)
        outdated_count = len(updates.get("outdated", []))
        total_deps = len(updates.get("outdated", [])) + len(updates.get("current", []))
        if total_deps > 0:
            outdated_percentage = (outdated_count / total_deps) * 100
            if outdated_percentage > 50:
                risk_score += 20
            elif outdated_percentage > 25:
                risk_score += 10
        
        # Calculate risk level
        if risk_score >= 70:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 30:
            return "medium"
        elif risk_score > 0:
            return "low"
        else:
            return "minimal"

    def _generate_requirements_recommendations(
        self,
        parsed_requirements: Dict[str, Any],
        health_analysis: Dict[str, Any],
        update_analysis: Dict[str, Any],
        security_analysis: Dict[str, Any],
        compatibility_analysis: Dict[str, Any],
        summary: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for requirements management."""
        recommendations = []
        
        risk_level = summary.get("overall_risk_level", "minimal")
        
        # Overall assessment
        if risk_level == "critical":
            recommendations.append("🚨 Critical issues detected - immediate action required")
        elif risk_level == "high":
            recommendations.append("⚠️  High risk dependencies - review and update urgently")
        elif risk_level == "medium":
            recommendations.append("⚠️  Moderate risk - address issues when possible")
        elif risk_level == "minimal":
            recommendations.append("✅ Requirements appear healthy")
        
        # Specific recommendations
        health_issues = health_analysis.get("issues", [])
        if health_issues:
            recommendations.append(f"🔧 Fix {len(health_issues)} dependency specification issues")
        
        outdated_count = len(update_analysis.get("outdated", []))
        if outdated_count > 0:
            recommendations.append(f"📦 Update {outdated_count} outdated packages")
        
        vuln_count = security_analysis.get("vulnerability_count", 0)
        if vuln_count > 0:
            recommendations.append(f"🔒 Address {vuln_count} security vulnerabilities")
        
        incompat_count = len(compatibility_analysis.get("incompatible", []))
        if incompat_count > 0:
            recommendations.append(f"🐍 Fix {incompat_count} Python compatibility issues")
        
        # File format recommendations
        file_format = parsed_requirements["file_info"]["format"]
        if file_format == "requirements.txt":
            recommendations.append("💡 Consider migrating to pyproject.toml for better dependency management")
        elif file_format == "unknown":
            recommendations.append("📝 Use standard requirements file formats (requirements.txt, pyproject.toml)")
        
        return recommendations


# Main analysis functions
async def analyze_project_requirements(
    file_path: str,
    check_updates: bool = True,
    security_scan: bool = True,
    compatibility_check: bool = True
) -> Dict[str, Any]:
    """
    Analyze project requirements file for dependencies, security, and compatibility.
    
    Args:
        file_path: Path to the requirements file
        check_updates: Whether to check for package updates
        security_scan: Whether to perform security vulnerability scanning
        compatibility_check: Whether to check Python version compatibility
        
    Returns:
        Comprehensive requirements file analysis
    """
    analyzer = RequirementsAnalyzer()
    return await analyzer.analyze_requirements_file(
        file_path, check_updates, security_scan, compatibility_check
    )


async def compare_requirements_files(
    file_paths: List[str]
) -> Dict[str, Any]:
    """
    Compare multiple requirements files to identify differences and conflicts.
    
    Args:
        file_paths: List of paths to requirements files to compare
        
    Returns:
        Comparative analysis of requirements files
    """
    logger.info(f"Starting requirements comparison for {len(file_paths)} files")
    
    analyzer = RequirementsAnalyzer()
    file_analyses = {}
    
    # Analyze each file
    for file_path in file_paths:
        try:
            analysis = await analyzer.analyze_requirements_file(
                file_path, check_updates=False, security_scan=False, compatibility_check=False
            )
            file_analyses[file_path] = analysis
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            file_analyses[file_path] = {"error": str(e), "dependencies": []}
    
    # Compare dependencies
    all_packages = set()
    for analysis in file_analyses.values():
        if "dependencies" in analysis:
            for dep in analysis["dependencies"]:
                all_packages.add(dep["name"])
    
    # Generate comparison results
    conflicts = []
    common_packages = []
    unique_packages = {}
    
    for package in all_packages:
        versions_by_file = {}
        for file_path, analysis in file_analyses.items():
            if "dependencies" in analysis:
                for dep in analysis["dependencies"]:
                    if dep["name"] == package:
                        versions_by_file[file_path] = dep["version_specifiers"]
                        break
        
        if len(versions_by_file) == len(file_paths):
            # Package is in all files
            version_specs = list(versions_by_file.values())
            if len(set(str(spec) for spec in version_specs)) > 1:
                conflicts.append({
                    "package": package,
                    "versions_by_file": versions_by_file
                })
            else:
                common_packages.append(package)
        else:
            # Package is unique to some files
            for file_path, versions in versions_by_file.items():
                if file_path not in unique_packages:
                    unique_packages[file_path] = []
                unique_packages[file_path].append({
                    "package": package,
                    "version_specifiers": versions
                })
    
    return {
        "comparison_timestamp": datetime.now(timezone.utc).isoformat(),
        "files_compared": len(file_paths),
        "file_analyses": file_analyses,
        "comparison_results": {
            "total_unique_packages": len(all_packages),
            "common_packages": common_packages,
            "conflicting_packages": conflicts,
            "unique_to_files": unique_packages,
        },
        "recommendations": _generate_comparison_recommendations(conflicts, unique_packages, file_analyses)
    }


def _generate_comparison_recommendations(
    conflicts: List[Dict[str, Any]], 
    unique_packages: Dict[str, List[Dict[str, Any]]], 
    file_analyses: Dict[str, Any]
) -> List[str]:
    """Generate recommendations for requirements file comparison."""
    recommendations = []
    
    if conflicts:
        recommendations.append(f"🔄 Resolve {len(conflicts)} version conflicts across files")
        for conflict in conflicts[:3]:  # Show first 3
            recommendations.append(f"  - {conflict['package']}: inconsistent versions")
    
    if unique_packages:
        total_unique = sum(len(packages) for packages in unique_packages.values())
        recommendations.append(f"📦 {total_unique} packages are unique to specific files")
    
    if not conflicts and not unique_packages:
        recommendations.append("✅ All requirements files are consistent")
    
    # File format recommendations
    formats = set()
    for analysis in file_analyses.values():
        if "file_info" in analysis:
            formats.add(analysis["file_info"]["format"])
    
    if len(formats) > 1:
        recommendations.append("📝 Consider standardizing on a single requirements file format")
    
    return recommendations
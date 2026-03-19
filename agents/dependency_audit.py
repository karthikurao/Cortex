"""Dependency Audit Agent — deep dependency analysis, license compliance, and upgrade paths."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.dependency_audit_prompt import DEPENDENCY_AUDIT_SYSTEM_PROMPT
from tools.code_analysis_tools import analyze_dependency_security, find_imports
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_diff, git_log, git_status


class DependencyAuditAgent(BaseAgent):
    """Specialist agent for dependency analysis and supply chain security.

    Performs comprehensive dependency auditing:
    - CVE/security vulnerability scanning across all dependency files
    - License compliance analysis (copyleft, permissive, SPDX)
    - Outdated dependency detection with upgrade path planning
    - Supply chain risk assessment (abandoned packages, typosquatting)
    - Transitive dependency analysis
    - Unused dependency identification
    - Lock file completeness and version pinning review
    - SBOM awareness and reproducible build assessment
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="dependency_audit",
            name="Dependency Audit",
            tools=[
                read_file,
                list_directory,
                read_multiple_files,
                search_in_files,
                git_status,
                git_diff,
                git_log,
                find_imports,
                analyze_dependency_security,
            ],
        )

    def get_system_prompt(self) -> str:
        return DEPENDENCY_AUDIT_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "dependency_audit_protocol": (
                    "=== PHASE 1: DISCOVERY ===\n"
                    "1. Run list_directory (depth 3) to find ALL dependency manifest files.\n"
                    "   Look for: requirements.txt, pyproject.toml, setup.py, setup.cfg,\n"
                    "   package.json, package-lock.json, yarn.lock, pnpm-lock.yaml,\n"
                    "   go.mod, go.sum, Cargo.toml, Cargo.lock, Gemfile, Gemfile.lock,\n"
                    "   composer.json, composer.lock, *.csproj, pom.xml, build.gradle\n"
                    "2. Read ALL discovered dependency files.\n"
                    "\n"
                    "=== PHASE 2: SECURITY SCAN ===\n"
                    "3. Run analyze_dependency_security on each dependency file.\n"
                    "4. For each package, check known CVE status, severity, and available patches.\n"
                    "5. Identify abandoned/deprecated packages (no releases in 2+ years).\n"
                    "\n"
                    "=== PHASE 3: LICENSE AUDIT ===\n"
                    "6. For every direct dependency, identify its license (SPDX identifier).\n"
                    "7. Flag copyleft licenses: GPL-2.0, GPL-3.0, LGPL-2.1, LGPL-3.0, AGPL-3.0, EUPL.\n"
                    "8. Check for license incompatibilities within the dependency tree.\n"
                    "9. Flag dependencies with missing or undeclared licenses.\n"
                    "\n"
                    "=== PHASE 4: VERSION AND PINNING ANALYSIS ===\n"
                    "10. Identify unpinned dependencies (ranges like >=1.0, ^1.0, ~1.0).\n"
                    "11. Flag dependencies significantly behind the latest release.\n"
                    "12. Check if lock files exist and are up-to-date.\n"
                    "\n"
                    "=== PHASE 5: USAGE VERIFICATION ===\n"
                    "13. Run find_imports and search_in_files to verify each dependency is actually used.\n"
                    "14. Identify dev-only dependencies incorrectly listed as runtime dependencies.\n"
                    "\n"
                    "=== PHASE 6: REPORTING ===\n"
                    "15. Provide prioritized upgrade recommendations ordered by security severity.\n"
                    "16. Include the exact upgrade command for the detected package manager.\n"
                    "17. Flag breaking changes for each upgrade."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        if "license" not in result.lower() and "cve" not in result.lower() and "vulnerabilit" not in result.lower():
            result += (
                "\n\n---\n### Dependency Audit Note\n"
                "_No dependency manifest files (requirements.txt, package.json, etc.) were found. "
                "Provide the path to your project's root directory or dependency files for a full audit._\n"
            )
        return result

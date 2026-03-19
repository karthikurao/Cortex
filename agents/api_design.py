"""API Design Agent — reviews REST/GraphQL API design, OpenAPI specs, and developer experience."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.api_design_prompt import API_DESIGN_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_diff, git_log, git_status
from tools.security_tools import analyze_attack_surface


class APIDesignAgent(BaseAgent):
    """Specialist agent for API design review and quality assessment.

    Performs comprehensive API design analysis:
    - RESTful resource naming and URL structure review
    - HTTP method semantics and idempotency verification
    - Status code correctness audit
    - Authentication and authorization flow review
    - Pagination, filtering, and sorting design
    - Error response consistency and RFC 7807 compliance
    - OpenAPI/Swagger specification review
    - Rate limiting and throttling design
    - API versioning and deprecation strategy
    - Developer experience assessment
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="api_design",
            name="API Design",
            tools=[
                read_file,
                list_directory,
                read_multiple_files,
                search_in_files,
                git_status,
                git_diff,
                git_log,
                find_imports,
                find_function_definitions,
                analyze_complexity,
                analyze_attack_surface,
            ],
        )

    def get_system_prompt(self) -> str:
        return API_DESIGN_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "api_review_protocol": (
                    "=== PHASE 1: DISCOVERY ===\n"
                    "1. Run list_directory (depth 3) to find all route files, controller files,\n"
                    "   view files, serializer files, and OpenAPI/Swagger specs.\n"
                    "   Look for: routes.py, views.py, urls.py, controllers/, *.yaml, *.json (openapi/swagger)\n"
                    "2. Run find_imports to detect the API framework in use (Flask, FastAPI, Django, Express, etc.).\n"
                    "3. Read ALL route/endpoint definition files and OpenAPI specs.\n"
                    "\n"
                    "=== PHASE 2: ENDPOINT INVENTORY ===\n"
                    "4. Use search_in_files to find all HTTP method decorators and route registrations.\n"
                    "   Search for: @app.route, @router., app.get(, app.post(, urlpatterns, path(, re_path(\n"
                    "5. Build a complete inventory of every endpoint: method, path, auth requirement.\n"
                    "\n"
                    "=== PHASE 3: DESIGN REVIEW ===\n"
                    "6. Check URL naming: nouns vs verbs, plural resources, nesting depth.\n"
                    "7. Verify HTTP method semantics (GET=safe, PUT/DELETE=idempotent, POST=create).\n"
                    "8. Audit status codes returned by every endpoint.\n"
                    "9. Check collection endpoints for pagination (missing pagination = unbounded results).\n"
                    "10. Review error response structure for consistency and RFC 7807 compliance.\n"
                    "\n"
                    "=== PHASE 4: SECURITY REVIEW ===\n"
                    "11. Run analyze_attack_surface to map all API entry points.\n"
                    "12. Verify authentication on every non-public endpoint.\n"
                    "13. Check CORS configuration and rate limiting.\n"
                    "\n"
                    "=== PHASE 5: REPORTING ===\n"
                    "14. Provide prioritized findings with specific file/line references.\n"
                    "15. Include copy-paste-ready code examples for every fix."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        if "endpoint" not in result.lower() and "route" not in result.lower() and "api" not in result.lower():
            result += (
                "\n\n---\n### API Design Review Note\n"
                "_No API route or endpoint files were found to analyze. "
                "Provide paths to your route definitions, controllers, or OpenAPI spec for a detailed review._\n"
            )
        return result

"""Database Agent — reviews schemas, ORM usage, query optimization, and migrations."""

from typing import Any

from agents.base_agent import BaseAgent
from prompts.database_prompt import DATABASE_SYSTEM_PROMPT
from tools.code_analysis_tools import (
    analyze_complexity,
    analyze_dependency_security,
    find_function_definitions,
    find_imports,
)
from tools.file_tools import list_directory, read_file, read_multiple_files, search_in_files
from tools.git_tools import git_diff, git_log, git_status


class DatabaseAgent(BaseAgent):
    """Specialist agent for database architecture review.

    Performs end-to-end database analysis:
    - Schema design review (normalization, constraints, data types)
    - Index audit (missing indexes, redundant indexes, partial indexes)
    - N+1 query detection and ORM optimization
    - Migration safety review (zero-downtime concerns, lock risk)
    - Connection pool and transaction analysis
    - SQL injection and database security checks
    - Query performance analysis and execution plan review
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="database",
            name="Database",
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
                analyze_dependency_security,
            ],
        )

    def get_system_prompt(self) -> str:
        return DATABASE_SYSTEM_PROMPT

    def pre_process(self, user_request: str, context: dict[str, Any] | None) -> dict[str, Any]:
        return {
            "enriched_context": {
                "database_review_protocol": (
                    "=== PHASE 1: DISCOVERY ===\n"
                    "1. Run list_directory (depth 3) to find all schema, migration, and model files.\n"
                    "   Look for: *.sql, models.py, schema.prisma, migrations/, alembic/, db/, database/\n"
                    "2. Read ALL discovered schema and migration files.\n"
                    "3. Run find_imports to identify which database libraries are used (SQLAlchemy, Django ORM, Prisma, etc.).\n"
                    "\n"
                    "=== PHASE 2: SCHEMA ANALYSIS ===\n"
                    "4. Map every table/collection: columns, types, nullable settings, default values.\n"
                    "5. Identify all primary keys, foreign keys, unique constraints, and check constraints.\n"
                    "6. Check for normalization issues: duplicate data, missing constraints, inappropriate types.\n"
                    "\n"
                    "=== PHASE 3: QUERY ANALYSIS ===\n"
                    "7. Use search_in_files to find all database queries (raw SQL, ORM calls, filter chains).\n"
                    "8. Detect N+1 query patterns: queries inside loops, missing select_related/prefetch_related.\n"
                    "9. Identify missing indexes on JOIN, WHERE, and ORDER BY columns.\n"
                    "\n"
                    "=== PHASE 4: MIGRATION REVIEW ===\n"
                    "10. Read all migration files in chronological order.\n"
                    "11. Flag unsafe migrations: ADD COLUMN NOT NULL without DEFAULT, DROP COLUMN, RENAME COLUMN.\n"
                    "12. Check for missing rollback (down) migrations.\n"
                    "\n"
                    "=== PHASE 5: REPORTING ===\n"
                    "13. Provide prioritized findings with specific file/line references.\n"
                    "14. Include copy-paste-ready SQL or ORM code fixes.\n"
                    "15. Quantify performance impact where possible."
                ),
            }
        }

    def post_process(self, result: str, user_request: str) -> str:
        if "index" not in result.lower() and "n+1" not in result.lower() and "schema" not in result.lower():
            result += (
                "\n\n---\n### Database Review Note\n"
                "_No specific schema, index, or query files were found to analyze. "
                "Provide paths to your migration files, model definitions, or ORM code for a detailed review._\n"
            )
        return result

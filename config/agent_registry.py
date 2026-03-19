"""Agent registry — metadata and discovery for all specialist agents."""

from dataclasses import dataclass


@dataclass
class AgentInfo:
    """Metadata for a registered agent."""

    name: str
    agent_id: str
    description: str
    capabilities: list[str]
    keywords: list[str]


AGENT_REGISTRY: list[AgentInfo] = [
    AgentInfo(
        name="Code Reviewer",
        agent_id="code_reviewer",
        description=(
            "Reviews code for quality, readability, and adherence to best practices. "
            "Performs multi-pass analysis covering SOLID principles, DRY/KISS violations, "
            "naming conventions, error handling, type safety, testability, and code style. "
            "Uses tools to read actual code, search for patterns, and detect code smells "
            "before providing evidence-based findings with line references."
        ),
        capabilities=[
            "Multi-pass code quality review with evidence",
            "SOLID/DRY/KISS/YAGNI compliance analysis",
            "Naming convention and readability assessment",
            "Error handling completeness review",
            "Type safety and annotation coverage check",
            "Testability evaluation",
            "Code smell detection (long methods, God classes, etc.)",
            "Git blame analysis for change context",
            "Function signature and complexity analysis",
            "Prioritized findings with severity ratings",
        ],
        keywords=[
            "review",
            "code review",
            "pull request",
            "PR",
            "quality",
            "readability",
            "naming",
            "style",
            "conventions",
            "SOLID",
            "DRY",
            "KISS",
            "clean code",
            "best practice",
            "code smell",
            "maintainability",
            "refactor suggestion",
        ],
    ),
    AgentInfo(
        name="Bug Analyzer",
        agent_id="bug_analyzer",
        description=(
            "Diagnoses bugs through evidence-based root cause analysis. Parses stack traces, "
            "traces execution paths, analyzes data flow, and identifies failure modes. "
            "Searches codebases for related patterns and provides specific, tested fixes."
        ),
        capabilities=[
            "Stack trace parsing and error chain analysis",
            "Root cause identification with evidence chains",
            "Execution path tracing through code",
            "Data flow and state analysis",
            "Reproduction step generation",
            "Fix suggestions with before/after code",
            "Related bug pattern detection",
            "Regression risk assessment",
            "Code smell detection in error-prone areas",
            "Prevention recommendations",
        ],
        keywords=[
            "bug",
            "error",
            "exception",
            "crash",
            "fix",
            "debug",
            "trace",
            "stacktrace",
            "issue",
            "broken",
            "failing",
            "500",
            "404",
            "null",
            "undefined",
            "NoneType",
            "TypeError",
            "ValueError",
            "timeout",
            "race condition",
            "deadlock",
            "memory leak",
            "regression",
        ],
    ),
    AgentInfo(
        name="Architecture",
        agent_id="architecture",
        description=(
            "Evaluates system architecture, design patterns, and structural decisions. "
            "Analyzes dependency graphs, coupling/cohesion metrics, layer violations, "
            "and scalability concerns. Provides migration roadmaps and pattern recommendations."
        ),
        capabilities=[
            "Design pattern evaluation and recommendations",
            "Dependency graph and coupling analysis",
            "Cohesion measurement across modules",
            "Layer violation and circular dependency detection",
            "Scalability and distributed systems assessment",
            "Technology stack evaluation",
            "Migration path planning with risk assessment",
            "API boundary and contract analysis",
            "Domain-driven design alignment",
            "Complexity hotspot identification",
        ],
        keywords=[
            "architecture",
            "design",
            "pattern",
            "structure",
            "scalability",
            "microservice",
            "monolith",
            "dependency",
            "coupling",
            "cohesion",
            "layer",
            "module",
            "component",
            "system design",
            "migration",
            "API",
            "boundary",
            "domain",
            "DDD",
            "event-driven",
            "CQRS",
        ],
    ),
    AgentInfo(
        name="Testing",
        agent_id="testing",
        description=(
            "Designs comprehensive test strategies, identifies coverage gaps, and generates "
            "test cases. Covers unit, integration, E2E, and property-based testing. "
            "Evaluates test quality, mock strategies, and provides test pyramid analysis."
        ),
        capabilities=[
            "Test strategy and pyramid design",
            "Coverage gap identification",
            "Unit test generation with edge cases",
            "Integration test planning",
            "BDD/TDD scenario writing",
            "Parameterized and property-based test design",
            "Mock/stub/fake strategy evaluation",
            "Mutation testing opportunity identification",
            "Test quality and assertion review",
            "CI test pipeline recommendations",
        ],
        keywords=[
            "test",
            "testing",
            "unit test",
            "integration",
            "coverage",
            "TDD",
            "BDD",
            "pytest",
            "junit",
            "selenium",
            "mock",
            "assertion",
            "test case",
            "fixture",
            "parameterize",
            "property-based",
            "mutation testing",
            "E2E",
            "end-to-end",
            "test pyramid",
            "regression test",
        ],
    ),
    AgentInfo(
        name="Security",
        agent_id="security",
        description=(
            "Performs evidence-based security audits following OWASP Top 10, CWE, and SANS guidelines. "
            "Scans for injection vulnerabilities, authentication/authorization flaws, secrets exposure, "
            "dependency CVEs, and supply chain risks. Provides proof-of-concept exploit scenarios."
        ),
        capabilities=[
            "OWASP Top 10 compliance scanning",
            "Injection vulnerability detection (SQL, XSS, command, LDAP)",
            "Authentication/authorization flow audit",
            "Secrets and credential detection in code/config",
            "Dependency vulnerability and CVE analysis",
            "Supply chain security assessment",
            "Cryptographic implementation review",
            "Input validation and sanitization audit",
            "Security header and CORS analysis",
            "Structured vulnerability reports with CWE references",
        ],
        keywords=[
            "security",
            "vulnerability",
            "OWASP",
            "XSS",
            "SQL injection",
            "CSRF",
            "authentication",
            "authorization",
            "secrets",
            "CVE",
            "exploit",
            "injection",
            "encryption",
            "hash",
            "token",
            "session",
            "CORS",
            "SSRF",
            "RCE",
            "supply chain",
            "dependency audit",
            "penetration",
        ],
    ),
    AgentInfo(
        name="Documentation",
        agent_id="documentation",
        description=(
            "Generates and reviews technical documentation with evidence-based analysis. "
            "Creates README files, API documentation, docstrings, changelogs, and Architecture "
            "Decision Records (ADRs). Assesses documentation completeness and accuracy."
        ),
        capabilities=[
            "README generation with standard sections",
            "API documentation with endpoint specs",
            "Docstring generation and review",
            "Changelog and release notes creation",
            "Architecture Decision Records (ADRs)",
            "Documentation completeness audit",
            "Code-documentation accuracy verification",
            "Inline comment quality review",
            "Getting-started guide creation",
            "Configuration documentation",
        ],
        keywords=[
            "documentation",
            "docs",
            "README",
            "API docs",
            "comment",
            "changelog",
            "ADR",
            "javadoc",
            "docstring",
            "document",
            "explain",
            "describe",
            "getting started",
            "guide",
            "tutorial",
            "reference",
            "wiki",
        ],
    ),
    AgentInfo(
        name="Refactoring",
        agent_id="refactoring",
        description=(
            "Identifies code smells and performs systematic refactoring analysis. "
            "Follows Martin Fowler's catalog, detects complexity hotspots, dead code, "
            "and proposes safe transformations with before/after examples and risk assessment."
        ),
        capabilities=[
            "Full Fowler code smell catalog detection",
            "Complexity reduction with specific techniques",
            "Extract method/class/interface suggestions",
            "Dead code and unreachable code identification",
            "Dependency injection improvements",
            "Before/after code examples for each refactoring",
            "Risk assessment for each transformation",
            "Git history analysis for change hotspots",
            "Modernization opportunities (patterns, idioms)",
            "Prioritized refactoring roadmap",
        ],
        keywords=[
            "refactor",
            "refactoring",
            "code smell",
            "complexity",
            "simplify",
            "extract",
            "clean up",
            "improve",
            "dead code",
            "duplicate",
            "DRY",
            "technical debt",
            "modernize",
            "rename",
            "restructure",
            "decompose",
        ],
    ),
    AgentInfo(
        name="DevOps/CI-CD",
        agent_id="devops",
        description=(
            "Reviews CI/CD pipelines, Dockerfiles, IaC templates, and deployment configurations. "
            "Analyzes build optimization, supply chain security, GitOps practices, and "
            "environment management. Covers GitHub Actions, Jenkins, Docker, Kubernetes, and Terraform."
        ),
        capabilities=[
            "CI/CD pipeline review (GitHub Actions, Jenkins, GitLab CI)",
            "Dockerfile analysis and optimization",
            "Docker Compose and orchestration review",
            "Kubernetes manifest and Helm chart analysis",
            "Terraform/CloudFormation IaC review",
            "Build optimization and caching strategies",
            "Supply chain security (pinned actions, signed images)",
            "Environment and secrets management",
            "Deployment strategy evaluation (blue-green, canary)",
            "GitOps workflow assessment",
        ],
        keywords=[
            "devops",
            "CI/CD",
            "pipeline",
            "docker",
            "deployment",
            "github actions",
            "jenkins",
            "kubernetes",
            "terraform",
            "build",
            "deploy",
            "infrastructure",
            "container",
            "helm",
            "GitOps",
            "ArgoCD",
            "monitoring",
            "observability",
        ],
    ),
    AgentInfo(
        name="Performance",
        agent_id="performance",
        description=(
            "Identifies performance bottlenecks through data-driven analysis. "
            "Evaluates algorithmic complexity (Big-O), memory usage, I/O patterns, "
            "concurrency issues, caching strategies, and database query efficiency."
        ),
        capabilities=[
            "Algorithmic complexity analysis (Big-O quantification)",
            "Database query optimization (N+1, missing indexes)",
            "Memory usage and leak detection patterns",
            "I/O bottleneck identification",
            "Concurrency and parallelism analysis",
            "Caching strategy design and evaluation",
            "Network and API call optimization",
            "Load and scalability recommendations",
            "Resource pool and connection management",
            "Performance regression prevention",
        ],
        keywords=[
            "performance",
            "slow",
            "bottleneck",
            "optimize",
            "cache",
            "memory",
            "latency",
            "throughput",
            "query",
            "N+1",
            "load",
            "speed",
            "fast",
            "Big-O",
            "complexity",
            "profiling",
            "benchmark",
            "concurrency",
            "connection pool",
            "async",
            "batch",
            "pagination",
        ],
    ),
    AgentInfo(
        name="Database",
        agent_id="database",
        description=(
            "Reviews database schemas, ORM models, query patterns, and migration files. "
            "Detects N+1 queries, missing indexes, unsafe migrations, normalization issues, "
            "and database security concerns. Provides copy-paste-ready SQL and ORM fixes."
        ),
        capabilities=[
            "Schema design review (normalization, constraints, data types)",
            "Index audit (missing, redundant, partial indexes)",
            "N+1 query detection and ORM optimization",
            "Migration safety review (lock risk, zero-downtime strategies)",
            "Connection pool and transaction analysis",
            "SQL injection and database security checks",
            "ORM usage review (SQLAlchemy, Django ORM, Prisma, TypeORM)",
            "Query performance analysis",
            "Soft-delete and audit log pattern evaluation",
            "Replication and sharding readiness assessment",
        ],
        keywords=[
            "database",
            "SQL",
            "schema",
            "migration",
            "ORM",
            "SQLAlchemy",
            "Django ORM",
            "Prisma",
            "index",
            "query",
            "N+1",
            "table",
            "model",
            "foreign key",
            "normalization",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Redis",
            "Alembic",
            "db",
            "transaction",
            "connection pool",
            "slow query",
            "database design",
        ],
    ),
    AgentInfo(
        name="API Design",
        agent_id="api_design",
        description=(
            "Reviews REST and GraphQL API design for correctness, consistency, and developer "
            "experience. Audits URL structure, HTTP semantics, status codes, authentication, "
            "pagination, error handling, OpenAPI specs, and versioning strategy."
        ),
        capabilities=[
            "RESTful resource naming and URL structure review",
            "HTTP method semantics and idempotency verification",
            "Status code correctness audit",
            "Authentication and authorization flow review",
            "Pagination, filtering, and sorting design",
            "Error response consistency and RFC 7807 compliance",
            "OpenAPI/Swagger specification review",
            "Rate limiting and throttling design",
            "API versioning and deprecation strategy",
            "GraphQL schema design and resolver review",
        ],
        keywords=[
            "API",
            "REST",
            "RESTful",
            "GraphQL",
            "endpoint",
            "route",
            "HTTP",
            "status code",
            "OpenAPI",
            "Swagger",
            "pagination",
            "versioning",
            "CORS",
            "rate limit",
            "authentication",
            "authorization",
            "request",
            "response",
            "JSON",
            "URL",
            "webhook",
            "gRPC",
            "API design",
            "API review",
            "developer experience",
        ],
    ),
    AgentInfo(
        name="Dependency Audit",
        agent_id="dependency_audit",
        description=(
            "Performs comprehensive dependency auditing covering CVE/security vulnerabilities, "
            "license compliance, outdated packages, supply chain risks, and upgrade path planning. "
            "Analyzes requirements.txt, package.json, go.mod, Cargo.toml, and lock files."
        ),
        capabilities=[
            "CVE/security vulnerability scanning across all dependency files",
            "License compliance analysis (copyleft, permissive, SPDX)",
            "Outdated dependency detection with upgrade path planning",
            "Supply chain risk assessment (abandoned packages, typosquatting)",
            "Transitive dependency analysis",
            "Unused dependency identification",
            "Lock file completeness and version pinning review",
            "SBOM and reproducible build assessment",
            "Dev vs runtime dependency classification",
            "Package manager-specific upgrade command generation",
        ],
        keywords=[
            "dependency",
            "dependencies",
            "package",
            "library",
            "CVE",
            "vulnerability",
            "license",
            "GPL",
            "MIT",
            "Apache",
            "AGPL",
            "outdated",
            "upgrade",
            "npm",
            "pip",
            "requirements",
            "package.json",
            "pyproject.toml",
            "go.mod",
            "Cargo.toml",
            "supply chain",
            "SBOM",
            "lock file",
            "abandoned",
            "deprecated",
            "audit",
            "Dependabot",
            "Renovate",
        ],
    ),
    AgentInfo(
        name="Exploit Analyzer",
        agent_id="exploit_analyzer",
        description=(
            "Performs offensive security analysis to find exploitable vulnerabilities and "
            "construct attack chains. Uses CVSS v3.1 scoring, STRIDE threat modeling, and "
            "proof-of-concept exploit scenarios. Scans for injection sinks, unsafe deserialization, "
            "hardcoded secrets, cryptographic weaknesses, path traversal, and supply chain risks. "
            "Chains multiple low-severity findings into critical attack paths."
        ),
        capabilities=[
            "Attack surface enumeration and entry point mapping",
            "Exploit chain construction (chaining vulnerabilities)",
            "CVSS v3.1 base score calculation for every finding",
            "STRIDE threat modeling (Spoofing, Tampering, Repudiation, Info Disclosure, DoS, EoP)",
            "Proof-of-concept exploit scenario descriptions",
            "Automated injection sink detection (SQL, XSS, command, LDAP, SSTI)",
            "Unsafe deserialization scanning (pickle, YAML, eval — RCE vectors)",
            "Hardcoded secrets and credential scanning",
            "Cryptographic weakness detection (weak hash, broken cipher, insecure PRNG)",
            "Path traversal and open redirect detection",
            "Authentication and authorization bypass analysis",
            "Supply chain and dependency vulnerability assessment",
            "Post-exploitation impact analysis",
            "Remediation with defense-in-depth recommendations",
        ],
        keywords=[
            "exploit",
            "attack",
            "penetration",
            "pentest",
            "offensive",
            "red team",
            "attack surface",
            "attack chain",
            "exploit chain",
            "CVSS",
            "STRIDE",
            "threat model",
            "proof of concept",
            "PoC",
            "RCE",
            "remote code execution",
            "injection",
            "deserialization",
            "secrets",
            "credentials",
            "hardcoded",
            "path traversal",
            "open redirect",
            "SSRF",
            "XSS",
            "SQL injection",
            "command injection",
            "privilege escalation",
            "lateral movement",
            "supply chain",
            "OWASP",
            "CWE",
            "vulnerability",
            "hack",
            "breach",
        ],
    ),
]


class AgentRegistry:
    """Provides lookup and discovery of registered agents."""

    def __init__(self) -> None:
        self._agents = {agent.agent_id: agent for agent in AGENT_REGISTRY}

    def get(self, agent_id: str) -> AgentInfo | None:
        return self._agents.get(agent_id)

    def list_all(self) -> list[AgentInfo]:
        return list(self._agents.values())

    def get_ids(self) -> list[str]:
        return list(self._agents.keys())

    def get_registry_summary(self) -> str:
        """Return a formatted summary for the orchestrator's system prompt."""
        lines = []
        for agent in self._agents.values():
            caps = ", ".join(agent.capabilities)
            lines.append(f"- **{agent.name}** (id: `{agent.agent_id}`): {agent.description}\n  Capabilities: {caps}")
        return "\n".join(lines)

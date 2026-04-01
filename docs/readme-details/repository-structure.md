# Repository Structure

Full directory tree for the rebuilder template.

```
rebuilder-template/
├── STANDARDS.md                # Migration reference — architecture, data migration, cutover, DR, ADRs
├── README.md                  # Project overview and quick start
├── spec-driven-development.md # Leadership doc — reproducibility, agent architecture
├── spec-process-overview.md   # Process overview — high-level summary of the rebuild workflow
├── scope.md                   # Scope template — copy to a working directory before filling out
├── prompting.md               # Audit trail of prompting commands and outcomes
├── AGENTS.md                  # Cross-tool agent bootstrap (Windsurf, Claude Code, others)
├── .gitignore                 # Python, Terraform, IDE, OS ignores + rebuild-inputs/
├── .windsurfrules             # Windsurf IDE — loads {lang}-developer-agent + {lang}-qa-agent
├── .github/
│   ├── copilot-instructions.md    # VS Code Copilot — loads {lang}-developer-agent + {lang}-qa-agent
│   └── PULL_REQUEST_TEMPLATE.md   # PR template — engineer sign-off
├── rebuild/
│   ├── IDEATION_PROCESS.md    # The rebuild analysis process definition (18 steps)
│   ├── input.md               # Input template — copy to a working directory before filling out
│   └── run.sh                 # Runner script — creates output structure in the input directory
├── rebuild-inputs/            # Per-project working directories (gitignored)
│   └── <project-name>/       # One directory per rebuild project
│       ├── repo/                         # Cloned primary legacy codebase
│       ├── template/                     # Cloned template repo (build standard — not an adjacent repo)
│       │   └── skill.md                  # Authoritative checklist for built service structure
│       ├── adjacent/                     # Optional: related repos included in rebuild scope
│       │   └── <related-repo>/
│       ├── scope.md                      # Filled-out scope
│       ├── input.md                      # Filled-out input
│       ├── output/                       # Steps 1-6: analysis artifacts and PRD
│       │   ├── legacy_assessment.md
│       │   ├── modernization_opportunities.md
│       │   ├── feasibility.md
│       │   ├── candidate_N.md
│       │   ├── prd.md
│       │   ├── summary-of-work.md         # Build summary — what was built, commits, quality gates
│       │   ├── compliance-audit.md        # Compliance audit results
│       │   └── process-feedback.md        # Process improvement notes
│       ├── {lang}-developer-agent/               # Step 8: populated dev agent config
│       │   ├── skill.md
│       │   └── config.md
│       ├── {lang}-qa-agent/                      # Step 8d: populated QA agent config
│       │   ├── skill.md
│       │   ├── config.md
│       │   ├── TEST_RESULTS_TEMPLATE.md
│       │   └── examples/
│       ├── sre-agent/                    # Step 7: populated SRE agent config
│       │   ├── skill.md
│       │   └── config.md
│       └── docs/
│           ├── adr/                      # Step 9: architecture decision records
│           │   └── *.md
│           ├── feature-parity.md         # Step 10: feature parity matrix
│           ├── data-migration-mapping.md  # Step 11: schema mapping
│           ├── cutover-report.md         # Template — filled post-cutover
│           └── disaster-recovery.md      # Template — filled during ops setup
├── docs/                      # Migration planning document templates
│   ├── readme-refactor/       # Detailed docs extracted from README
│   │   ├── how-to-use.md
│   │   ├── architecture.md
│   │   ├── agents.md
│   │   ├── repository-structure.md
│   │   └── ide-compatibility.md
│   ├── data-migration-mapping.md  # Schema mapping between legacy and target
│   ├── feature-parity.md         # Feature parity matrix and status tracking
│   ├── cutover-report.md         # Post-cutover documentation
│   ├── disaster-recovery.md      # DR plan — RTO/RPO, backups, runbooks
│   ├── rebuilder-architecture-diagrams.pdf  # Downloadable PDF of all mermaid diagrams
│   ├── adr/                      # Template directory (generated ADRs go in rebuild-inputs/)
│   └── postmortems/              # Incident postmortems
├── python-developer-agent/
│   ├── README.md              # Developer agent overview
│   ├── skill.md               # Daily dev instructions template — coding, testing, CI/CD, environments, bootstrap
│   ├── config.md              # Per-project config template — commands, environments, services, CI/CD
│   ├── .windsurfrules         # Windsurf IDE hook — reads {lang}-developer-agent + {lang}-qa-agent on session start
│   └── .github/
│       └── copilot-instructions.md  # VS Code Copilot hook — reads {lang}-developer-agent + {lang}-qa-agent
├── c-developer-agent/         # C developer agent (Inscape C coding standard)
│   ├── README.md
│   ├── skill.md
│   └── config.md
├── go-developer-agent/        # Go developer agent (idiomatic Go patterns)
│   ├── README.md
│   ├── skill.md
│   └── config.md
├── python-qa-agent/
│   ├── README.md              # QA agent overview — activation, customization, IDE usage
│   ├── skill.md               # QA verification — quality gates, test strategy, /ops/* contract
│   ├── config.md              # Per-project QA config — thresholds, env vars, acceptance criteria
│   ├── TEST_RESULTS_TEMPLATE.md  # Quality gate report template
│   └── examples/              # Example test patterns for rebuilt Python services
│       ├── conftest.py        # Fixtures — OTEL disable, env vars, sys.modules mocks
│       ├── test_routes.py     # API endpoint tests — status, health, main endpoint
│       ├── test_ops_endpoints.py  # /ops/* SRE contract tests (14 endpoints)
│       └── e2e/               # E2E shell scripts for live instance verification
│           ├── test_health.sh
│           ├── test_ops_contract.sh
│           └── test_smoke.sh
├── performance-agent/
│   ├── README.md              # Performance agent overview
│   ├── skill.md               # Profiling tools, optimization patterns, best practices
│   ├── config.md              # Per-project performance targets, hot paths, infrastructure context
│   └── references/
│       └── advanced-patterns.md  # NumPy, caching, __slots__, multiprocessing, async I/O, DB optimization
├── sre-agent/
│   ├── README.md              # SRE agent overview
│   ├── skill.md               # SRE agent instructions template — diagnostic workflow and response framework
│   ├── config.md              # Per-project config template — service registry, SLOs, PagerDuty, escalation
│   ├── playbooks/             # Remediation playbooks by incident type
│   │   ├── high-error-rate.md
│   │   ├── high-latency.md
│   │   ├── dependency-failure.md
│   │   ├── saturation.md
│   │   ├── service-down.md
│   │   └── certificate-expiry.md
│   ├── incidents/             # Agent-written incident reports
│   └── runtime/               # SRE agent runtime service
│       ├── README.md          # Architecture, setup, and deployment guide
│       ├── main.py            # FastAPI webhook receiver + alert intake pipeline
│       ├── agent.py           # Agentic loop — OpenAI-compatible LLM orchestration
│       ├── tools.py           # Tool definitions and executor
│       ├── intake.py          # Alert dedup, service serialization, priority queue
│       ├── config.py          # Configuration from environment variables
│       ├── models.py          # Pydantic models for alert payloads
│       ├── state.py           # Runtime state tracking for Golden Signals
│       ├── telemetry.py       # OpenTelemetry instruments
│       ├── pagerduty_setup.py # PagerDuty service/escalation bootstrapper
│       ├── deploy.sh          # Deployment script
│       ├── requirements.txt   # Python dependencies
│       ├── requirements-dev.txt # Dev dependencies — pytest, black, pylint
│       ├── pyproject.toml     # Linter and test configuration
│       ├── .env.example       # Environment variable template
│       ├── Dockerfile         # Container image
│       ├── tests/             # Unit and API tests
│       └── terraform/         # Cloud Run deployment
│           ├── main.tf
│           ├── variables.tf
│           ├── outputs.tf
│           └── deploy.auto.tfvars
└── .windsurf/
    ├── skills/                # Windsurf Skills — progressive disclosure, auto-invoked
    │   └── legacy-rebuild/    # @legacy-rebuild — rebuild process entry point
    │       └── SKILL.md
    └── workflows/             # Windsurf workflow definitions
        ├── developer.md       # /developer — reload developer + QA agent mid-session
        ├── qa.md              # /qa — run all quality gates and generate verification report
        ├── populate-templates.md
        └── run-replicator.md  # /run-replicator — invokes @legacy-rebuild skill
```

# Legacy Assessment

> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## Application Overview
[Summary from scope.md and input.md]

## Architecture Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## API Surface Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Observability & SRE Readiness
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Auth & Access Control
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Code & Dependency Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Operational Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Data Health
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Developer Experience
- Rating: [Good / Acceptable / Poor / Critical]
- [Findings]

## Infrastructure Health
- Rating: [Good / Acceptable / Poor / Critical]
- Cloud Provider(s): [current provider(s)]
- Containerized: [Yes/No — current container and orchestration status]
- IaC: [Terraform / CloudFormation / Pulumi / None]
- Managed Services: [list of cloud-managed services the app depends on — RDS, ElastiCache, SQS, etc.]
- Provider Lock-in: [Low / Medium / High — what ties the app to the current provider]
- Cloud Migration Impact: [Only if scope.md specifies a provider change. What managed services need equivalents? What SDK/API references exist in code? What has no direct equivalent on the target provider?]
- [Findings]

## External Dependencies & Integration Health
- Rating: [Good / Acceptable / Poor / Critical]
- Outbound Dependencies: [list of services this app calls, or "None"]
- Inbound Consumers: [list of known consumers, or "Unknown — risk finding"]
- Shared Infrastructure: [databases, caches, queues shared with other repos, or "None"]
- Internal Libraries: [shared repos or packages, or "None"]
- Data Dependencies: [ETL, CDC, warehouse feeds, or "None"]
- Tightly Coupled: [dependencies that cannot be stubbed — scope escalation required, or "None"]
- [Findings and risk assessment]

## Adjacent Repository Analysis
[Include this section only if adjacent repos were provided. Omit entirely for single-repo rebuilds.]

### [Adjacent Repo Name]
- **Purpose:** [what it does]
- **Tech Stack:** [language, framework, database]
- **Integration Points:** [how it connects to the primary repo — API calls, shared DB, shared cache, queues]
- **Shared State:** [specific tables, schemas, cache keys, queue topics shared with primary]
- **Coupling Assessment:** [tight / moderate / loose] — [explanation]
- **Rebuild Recommendation:** [absorb into primary rebuild / keep as separate service / rebuild independently]

### Cross-Repo Integration Summary
- **Total integration points:** [count]
- **Shared databases/schemas:** [list]
- **Shared infrastructure:** [caches, queues, storage]
- **Risk if rebuilt independently:** [what breaks if primary is rebuilt without changing adjacent repos]

## Summary
- Overall Risk Level: [Low / Medium / High / Critical]
- Top 3 Risks: [list]
- Strongest Assets to Preserve: [list — what's working well and should carry forward]

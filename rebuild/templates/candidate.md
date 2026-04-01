# Rebuild Candidate: [Working Title]

> **Reference document.** This is analysis output from the ideation process. It informs decisions but does not override {lang}-developer-agent/skill.md.

## One-Sentence Summary

[What does this rebuild accomplish in one sentence?]

## Current State

[What exists today — architecture, stack, problems]

## Target State

[What this looks like after the rebuild]

## Tech Stack

[Specific technologies, frameworks, and versions]

## Migration Strategy

[How you get from current to target — step by step]

## Data Migration

[How data moves from old to new — schema changes, ETL, backfill]

## What Breaks

[Features, integrations, or workflows that will be disrupted during migration]

## Phased Scope

### Phase 1 (MVP — [timeframe])
[What ships first — the minimum viable rebuild]

### Phase 2
[What comes next]

### Phase 3 (if applicable)
[Longer-term improvements]

## Estimated Effort

[T-shirt size with breakdown by phase]

## Biggest Risk

[Single biggest reason this fails]

## API Design

[API-first approach. Target API surface, versioning, OpenAPI spec plan.]

## Observability & SRE

[Golden Signals, RED metrics, SLOs, /ops/* SRE agent endpoints for diagnostics and safe remediation.]

## Auth & RBAC

[Identity provider, roles and permissions, service-to-service auth.]

## Dependency Contracts

[For each external dependency — outbound services, inbound consumers, shared infrastructure, internal libraries, data feeds:]
- Classification: inside rebuild boundary / outside rebuild boundary
- Interface: [REST, gRPC, SDK, direct DB, message queue, etc.]
- Contract: [documented / undocumented — if undocumented, must be documented as part of rebuild]
- Fallback: [behavior if this dependency is unavailable]
- Tightly Coupled: [Yes/No — if Yes, scope escalation required per STANDARDS.md Dependency Boundaries]
- Integration Tests: [what contract tests are needed at this boundary]

[If the application has no external dependencies, state "None — application is self-contained."]

## Infrastructure Migration

[Only include this section if scope.md specifies a cloud provider change or significant infrastructure transformation. Omit for rebuilds that stay on the same provider.]

### Provider Change
- Moving from: [current provider]
- Moving to: [target provider]
- Rationale: [why — from scope.md]

### Managed Service Mapping
| Current Service | Current Provider | Target Equivalent | Target Provider | Migration Notes |
|---|---|---|---|---|
| [e.g., RDS PostgreSQL] | [AWS] | [Cloud SQL PostgreSQL] | [GCP] | [compatible / requires changes / no equivalent] |

### Application Code Changes
[Cloud-provider-specific code that must change — SDK imports (boto3 → google-cloud-*), API calls, auth mechanisms, storage interfaces. List specific files and modules affected.]

### Cross-Cloud Dependencies
[Services or dependencies that remain on the original provider. For each: what it is, why it cannot move, how the rebuilt app will reach it (VPN, public API, interconnect), and the latency/reliability implications.]

### IaC Migration
[Current IaC state and target. If moving from CloudFormation to Terraform, or from no IaC to Terraform, describe the scope.]

## Rollback Plan

[How to revert if things go wrong]

# Rebuild Scope

**Instructions:** This is a template. Copy this file and `rebuild/input.md` to a working directory before filling out. This document is the bridge between where the application is today and where it needs to go.

---

## Current Application

### Overview

> *[What does this application do? Who uses it? When was it built? How actively is it maintained?]*

### Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend | *[framework or "None"]* | | |
| Backend | *[language/framework]* | | |
| Database | *[engine]* | | |
| Infrastructure | *[hosting/orchestration]* | | *[see Infrastructure section below]* |
| CI/CD | *[pipeline tool or "None"]* | | |
| Auth | *[auth mechanism]* | | |
| Other | *[caching, queues, etc.]* | | |

### Infrastructure

> *Detail the runtime infrastructure. The rebuilder reads code, not cloud consoles — this section provides the infrastructure context the code alone cannot reveal.*

| Question | Answer |
|---|---|
| Cloud provider(s) | *[AWS, GCP, Azure, on-prem, hybrid — list all]* |
| Compute | *[EC2, ECS, Lambda, bare metal VMs, etc.]* |
| Managed database services | *[RDS, Cloud SQL, ElastiCache, Memorystore, etc.]* |
| Managed cache/queue services | *[ElastiCache Redis, SQS, Pub/Sub, etc.]* |
| Containerized? | *[Yes — Docker/Podman/etc., or No]* |
| Container orchestration | *[ECS, EKS, GKE, Docker Compose, none]* |
| IaC tool | *[Terraform, CloudFormation, Pulumi, none]* |
| Regions/zones | *[e.g., us-east-1, us-central1-a]* |
| Networking | *[VPC, peering, VPN, load balancers — anything relevant to connectivity]* |

> *If the application runs across multiple cloud providers or a mix of cloud and on-prem, list each component and where it runs. This is critical for understanding what can move and what stays behind.*

### Architecture

> *[How is the application structured? Monolith, microservices, serverless? How are components organized? What are the data flow patterns?]*

### Known Pain Points

> *[Enumerated list of known issues — technical debt, security concerns, reliability problems, operational gaps]*

### API Surface

> *[Summary of the API: endpoints, resource groups, documentation status, authentication. Include an endpoint table if applicable.]*

### Dependencies and Integrations

#### Package Dependencies

> *[Direct package/library dependencies with versions]*

#### Outbound Dependencies (services this app calls)

> *[What APIs, services, or systems does this application call at runtime? For each: service name, interface type (REST, gRPC, SDK, direct DB), and whether the interface is documented. If none, state "None — application is self-contained."]*

#### Inbound Consumers (services that call this app)

> *[What services, systems, or scheduled jobs call this application's API? If consumers are unknown, state that explicitly — it is a risk finding that affects the rebuild.]*

#### Shared Infrastructure

> *[Databases, caches, message queues, or storage shared with other repos or services. Shared infrastructure creates implicit coupling that survives a rebuild. If none, state "None."]*

#### Internal Libraries / Shared Repos

> *[Libraries or packages imported from internal repos (not public registries). Include shared utility libraries, common auth packages, internal SDKs. If none, state "None."]*

#### Data Dependencies

> *[ETL pipelines, data warehouse feeds, CDC streams, reporting systems, or any process that reads from or writes to this application's data. If none, state "None."]*

### Observability & Monitoring

> *[What monitoring, logging, alerting, and tracing exists? Are there SLOs/SLAs? How are failures detected?]*

### Authentication & Authorization

> *[How do users authenticate? Is there RBAC? Are there shared credentials or hardcoded keys? Is there service-to-service auth?]*

### Data

> *[Data model summary: tables/collections, relationships, data volume, migration complexity]*

### Users

> *[Who uses this application? How? What are the usage patterns?]*

### Adjacent Repositories (Optional)

> *If this rebuild involves multiple legacy repos that work together, list them here. Clone each into `adjacent/<name>/` in your working directory. Only repos listed here are included in the rebuild scope — all other dependencies are treated as external services.*
>
> *If this is a single-repo rebuild, skip this section.*

| Repo | Clone Location | Relationship to Primary | Shared State |
|---|---|---|---|
| *[repo name/URL]* | `adjacent/[name]/` | *[e.g., "Provides auth API consumed by primary", "Shares PostgreSQL database", "Worker that processes primary's queue"]*  | *[shared DBs, caches, queues, or "None"]* |

> **Why are these repos included?**
> *[Explain why these repos cannot be treated as external services. Are they tightly coupled? Do they share a database? Would the rebuild be incomplete without understanding their code?]*

---

## Target State

### Target Repository

> *[A new repository for the rebuilt application. The legacy codebase will not be modified.]*

### Goals

> *[Numbered list of rebuild goals — what the rebuild should achieve]*

### Proposed Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | | |
| Backend | *[To be determined]* | |
| Database | *[To be determined]* | |
| CI/CD | *[To be determined]* | |
| Auth | *[To be determined]* | |
| Other | *[To be determined]* | |

### Target Infrastructure

> *Where will the rebuilt application run? If moving cloud providers, what stays behind and why?*

| Question | Answer |
|---|---|
| Target cloud provider | *[GCP, AWS, Azure — pick one primary]* |
| Target compute | *[Cloud Run, GKE, ECS, EKS, etc.]* |
| Containerization | *[Docker — or current container strategy if already containerized]* |
| Container orchestration | *[Kubernetes (GKE/EKS), Cloud Run, ECS, etc.]* |
| IaC tool | *[Terraform, Pulumi, CloudFormation]* |
| Target regions | *[e.g., us-central1 for GCP, us-east-1 for AWS]* |

#### Cloud migration (if changing providers)

> *If the rebuilt application is moving to a different cloud provider than the current one, answer these questions. If staying on the same provider, skip this section.*

| Question | Answer |
|---|---|
| Moving from → to | *[e.g., AWS → GCP]* |
| Why moving? | *[Cost, team expertise, organizational mandate, managed services, etc.]* |
| What stays behind? | *[List specific services/dependencies that cannot move and why — e.g., "Shared RDS PostgreSQL used by 5 other services — cannot migrate until they rebuild"]* |
| Cross-cloud connectivity | *[How will the rebuilt app on the new provider reach dependencies on the old provider? VPN, public API, private interconnect, etc.]* |
| Managed service mapping | *[Current → target equivalents: e.g., RDS → Cloud SQL, ElastiCache → Memorystore, SQS → Pub/Sub]* |

### Architecture

> *[Target architecture — layered monolith, microservices, event-driven, etc.]*

### API Design

> *[API versioning strategy, backward compatibility requirements, OpenAPI spec, pagination, error formatting]*

### Observability & SRE

> *[Target observability: structured logging, metrics, tracing, SLOs, /ops/* endpoints]*

### Auth & RBAC

> *[Target auth model: identity provider, roles, service-to-service auth, audit logging]*

### Dependency Contracts

> *For each external dependency identified in the Current Application section — outbound services, inbound consumers, shared infrastructure, internal libraries, data dependencies — document how the rebuilt service will interact with it: the interface, the contract, the fallback behavior if unavailable, and whether it's inside or outside the rebuild boundary.*

> *If the application is self-contained, state so. Unknown inbound consumers should be called out as a risk with a mitigation strategy (e.g., backward-compatible response shapes).*

### Migration Strategy

> *[How data and traffic transition from old to new — big-bang, parallel run, canary, blue/green]*

### Constraints

> *[Budget, timeline, team size, organizational constraints]*

### Out of Scope

> *[Items explicitly excluded from the rebuild effort]*

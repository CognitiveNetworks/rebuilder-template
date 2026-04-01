# Rebuild Scope

---

## Current Application

### Overview

The tvevents-k8s application is Vizio's TV Events collector service. It receives telemetry payloads from SmartCast TVs via HTTP POST, validates the payload structure and security hash, classifies events by type (NATIVEAPP_TELEMETRY, ACR_TUNER_DATA, PLATFORM_TELEMETRY), flattens and transforms the event data, applies channel blacklist obfuscation, and forwards the processed data to AWS Kinesis Data Firehose streams for downstream analytics. It has been running in production on AWS EKS since its containerization. It is actively maintained with recent OTEL instrumentation and CVE remediation work.

### Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend | None | | API-only service |
| Backend | Python / Flask | 3.10 / Flask 3.1.1 | Gunicorn with gevent workers |
| Database | PostgreSQL (RDS) | 14+ | Blacklist channel IDs lookup |
| Infrastructure | AWS EKS | | Kubernetes on AWS |
| CI/CD | GitHub Actions | | Build, test, push to ECR |
| Auth | HMAC (T1_SALT) | | Token hash security validation via cnlib |
| Other | AWS Kinesis Data Firehose, cnlib (git submodule), OTEL | | Firehose for data delivery, cnlib for shared utilities |

### Infrastructure

| Question | Answer |
|---|---|
| Cloud provider(s) | AWS |
| Compute | AWS EKS (Kubernetes) |
| Managed database services | AWS RDS PostgreSQL |
| Managed cache/queue services | AWS Kinesis Data Firehose (data delivery) |
| Containerized? | Yes — Docker |
| Container orchestration | Kubernetes (EKS) |
| IaC tool | Helm charts (no Terraform) |
| Regions/zones | us-east-1 |
| Networking | VPC, AGA (AWS Global Accelerator) for traffic management |

### Architecture

Monolithic Flask application. Single service that:
1. Receives TV event payloads via HTTP POST at `/`
2. Validates required parameters, security hash (T1_SALT via cnlib), and timestamps
3. Classifies events by EventType and validates type-specific payload schemas
4. Generates flattened output JSON with event-type-specific transformations
5. Checks channel blacklist (3-tier: in-memory → file cache → RDS) and obfuscates if needed
6. Sends processed data to Kinesis Data Firehose streams (evergreen + legacy, with debug variants)

### Known Pain Points

1. **Python 3.10** — behind current LTS (3.12), missing modern type hint features and performance improvements
2. **Flask** — synchronous WSGI framework requiring gevent for concurrency; not ideal for async workloads
3. **cnlib git submodule** — tightly coupled shared library installed via `setup.py install`, fragile dependency management
4. **Kinesis Data Firehose** — AWS-specific data delivery, no abstraction layer
5. **No /ops/* endpoints** — no SRE diagnostic or remediation endpoints; debugging requires SSH/kubectl
6. **No OpenAPI spec** — API not documented, no typed response models
7. **psycopg2 direct connections** — no connection pooling, opens/closes connection per query
8. **No dependency pinning via pip-compile** — requirements.txt is manually maintained
9. **Massive dependency list** — 87+ runtime dependencies including unused ones (pymemcache, PyMySQL, redis, fakeredis, google-cloud-monitoring, pygerduty, pyzmq, python-consul)
10. **No docker-compose for local dev** — local development requires manual setup of RDS, Firehose, etc.

### API Surface

Single POST endpoint and a health check:

| Method | Path | Description |
|---|---|---|
| POST | `/` | Receive TV event payload, validate, transform, send to Firehose |
| GET | `/status` | Returns `OK` for health checks |

Authentication: HMAC-based security hash validation using T1_SALT via `cnlib.cnlib.token_hash.security_hash_match()`.

### Dependencies and Integrations

#### Package Dependencies

87+ runtime dependencies pinned in pyproject.toml. Key ones: Flask 3.1.1, Gunicorn 23.0.0, psycopg2-binary 2.9.10, boto3 1.38.14, jsonschema 3.2.0, gevent 25.5.1, OpenTelemetry SDK 1.31.1. Many unused: pymemcache, PyMySQL, redis, fakeredis, google-cloud-monitoring, pygerduty, pyzmq, python-consul.

#### Outbound Dependencies (services this app calls)

- **AWS RDS PostgreSQL** — blacklisted channel IDs lookup (direct psycopg2, no pool)
- **AWS Kinesis Data Firehose** — data delivery via cnlib.firehose.Firehose (boto3 under the hood)

#### Inbound Consumers (services that call this app)

- **SmartCast TVs** — primary consumers, send telemetry via HTTP POST
- **Internal monitoring** — hits `/status` for health checks
- **AGA (AWS Global Accelerator)** — routes TV traffic to the service

#### Shared Infrastructure

- **RDS PostgreSQL** — `tvevents_blacklisted_station_channel_map` table shared with other services

#### Internal Libraries / Shared Repos

- **cntools_py3/cnlib** — git submodule providing `firehose.Firehose`, `token_hash.security_hash_match`, `log.getLogger`

#### Data Dependencies

- Downstream analytics pipelines consume data from the Kinesis Firehose S3 destinations

### Observability & Monitoring

- **OTEL instrumentation** — TracerProvider, MeterProvider, LoggerProvider configured with OTLP HTTP exporters
- **Flask instrumented** via FlaskInstrumentor, Psycopg2Instrumentor, BotocoreInstrumentor, etc.
- **Custom OTEL metrics** — counters for firehose sends, DB operations, event validation, heartbeats
- **No SLOs/SLAs defined**
- **No /ops/* endpoints** — no SRE diagnostic or remediation capabilities
- **Logging** via cnlib.log (wraps Python logging)

### Authentication & Authorization

- **HMAC-based** — T1_SALT used with cnlib.token_hash.security_hash_match() to validate TV identity
- **No RBAC** — single authentication model for all TV payloads
- **No service-to-service auth** beyond AWS IAM for Firehose/RDS access

### Data

- **RDS PostgreSQL** — single table `tvevents_blacklisted_station_channel_map` with `channel_id` column
- **3-tier cache** — in-memory dict → file cache (`/tmp/.blacklisted_channel_ids_cache`) → RDS query
- **No migrations** — schema managed outside this service
- Data volume: high-throughput TV telemetry (hundreds of millions of events/day in production, up to 500 pods)

### Users

- **SmartCast TVs** — automated telemetry submissions via firmware
- **Platform engineers** — maintain and operate the service
- **Data analytics teams** — consume downstream Firehose data

### Template Repository (Required)

| Field | Value |
|---|---|
| Target Language | `python` |
| Repo | [`rebuilder-evergreen-template-repo-python`](https://github.com/CognitiveNetworks/rebuilder-evergreen-template-repo-python) |
| Clone Location | `template/` |
| Authoritative Checklist | `template/skill.md` — every checkbox must be completed during the Build phase |
| What it defines | Dockerfile, entrypoint.sh, environment-check.sh, Helm charts, CI workflows, quality gate tooling, coding practices |

### Adjacent Repositories (Optional)

None — the standalone RDS and Kafka modules (`rebuilder-evergreen-rds-python` and `rebuilder-evergreen-kafka-python`) are external library dependencies, not adjacent repos.

---

## Target State

### Target Repository

`CognitiveNetworks/rebuilder-evergreen-tvevents` — a new repository for the rebuilt application. The legacy codebase (`evergreen-tvevents`) will not be modified.

### Goals

1. Modernize to Python 3.12 with FastAPI (async-ready, OpenAPI auto-generation, typed response models)
2. Replace Kinesis Data Firehose with Kafka via standalone `kafka_module` (`rebuilder-evergreen-kafka-python`)
3. Replace direct psycopg2 connections with standalone `rds_module` (`rebuilder-evergreen-rds-python`) with connection pooling
4. Replace cnlib git submodule with standalone modules (rds_module, kafka_module) and inline security hash
5. Add full `/ops/*` SRE diagnostic and remediation endpoints
6. Add OpenAPI spec with typed Pydantic response models and examples
7. Implement docker-compose for full local development (PostgreSQL, Kafka, app)
8. Reduce dependency count by removing unused packages
9. Add comprehensive test suite with ≥80% coverage
10. Conform to all template repo standards (Dockerfile, entrypoint, Helm, CI, quality gates)

### Proposed Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | None | API-only service |
| Backend | Python 3.12 / FastAPI | Modern async framework, auto OpenAPI, typed |
| Database | PostgreSQL (RDS) | Same engine, new rds_module with pooling |
| CI/CD | GitHub Actions | Same as legacy, enhanced pipeline |
| Auth | HMAC (T1_SALT) | Same security model, inline implementation |
| Other | Kafka (via kafka_module), OTEL, DAPR sidecars | Kafka replaces Firehose |

### Target Infrastructure

| Question | Answer |
|---|---|
| Target cloud provider | AWS |
| Target compute | AWS EKS |
| Containerization | Docker |
| Container orchestration | Kubernetes (EKS) |
| IaC tool | Terraform |
| Target regions | us-east-1 |

### Architecture

Layered monolith with clear separation:
- `src/app/` — FastAPI application
  - `routes.py` — HTTP endpoints
  - `event_types.py` — event classification and validation
  - `output.py` — JSON flattening and output generation
  - `obfuscation.py` — channel blacklist and obfuscation logic
  - `config.py` — configuration management
  - `deps.py` — dependency injection
  - `main.py` — application factory

### API Design

- POST `/` — existing TV event ingestion (backward-compatible)
- GET `/status` — simple health check returning `OK`
- GET `/health` — deep health check with dependency status
- GET/POST `/ops/*` — full SRE diagnostic and remediation endpoints
- OpenAPI auto-generated by FastAPI with typed Pydantic models

### Observability & SRE

- OTEL auto-instrumentation via opentelemetry-instrument
- Golden Signals and RED metrics via middleware
- `/ops/status`, `/ops/health`, `/ops/metrics`, `/ops/config`, `/ops/errors`, `/ops/cache`
- `/ops/loglevel`, `/ops/log-level`, `/ops/cache/flush`, `/ops/cache/refresh`, `/ops/circuits`
- Structured JSON logging via Python logging

### Auth & RBAC

- Same HMAC-based T1_SALT validation (cnlib.token_hash replaced with inline or extracted utility)
- No RBAC changes needed — single authentication model

### Dependency Contracts

- **rds_module** (rebuilder-evergreen-rds-python) — PostgreSQL client with connection pooling, mounted as local package
- **kafka_module** (rebuilder-evergreen-kafka-python) — Kafka producer replacing Firehose, mounted as local package
- **cnlib.token_hash** — security hash validation, to be inlined or mocked

### Migration Strategy

Parallel run: deploy rebuilt service alongside legacy, validate output parity with production traffic, then cut over.

### Constraints

- Must maintain backward compatibility with TV firmware (same POST `/` payload format)
- Must preserve T1_SALT HMAC security validation
- Must preserve channel blacklist obfuscation behavior
- Standalone rds_module and kafka_module already exist — use them as-is

### Out of Scope

- Changing the TV firmware payload format
- Migrating from AWS to GCP
- Rebuilding downstream analytics pipelines
- Modifying the RDS schema

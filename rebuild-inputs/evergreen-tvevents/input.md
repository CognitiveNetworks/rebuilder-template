# Rebuild Input

## Original Prompt

> Run all phases and all steps for evergreen-tvevents as the primary repo. The rebuilder process will create a new repo named rebuilder-evergreen-tvevents. You will use Kafka for Firehose and create a standalone RDS and Kafka python modules outside the repo, located at rebuilder-evergreen-rds-python and rebuilder-evergreen-kafka-python. These modules are already created, just need to make sure they're included and that the whole project can run locally.

## Application Name

> evergreen-tvevents (tvevents-k8s)

## Repository / Source Location

> https://github.com/CognitiveNetworks/evergreen-tvevents (local: /Users/dan.gorman/Vizio/evergreen-tvevents)

## Current Tech Stack Summary

> Python 3.10 Flask application running on AWS EKS with Gunicorn/gevent workers. Uses PostgreSQL (RDS) for blacklist channel ID lookups with a 3-tier cache (memory → file → DB). Sends processed TV telemetry to AWS Kinesis Data Firehose streams. Authentication via HMAC T1_SALT through cnlib git submodule (cntools_py3). OTEL instrumentation with OTLP HTTP exporters to New Relic.

## Current API Surface

> 2 endpoints: POST `/` (main ingestion) and GET `/status` (health check). Authentication via HMAC security hash in payload. No OpenAPI documentation. Consumers: SmartCast TVs (firmware-driven telemetry), internal monitoring, AGA traffic routing.

## Current Observability

> OTEL TracerProvider, MeterProvider, LoggerProvider with OTLP HTTP exporters. Flask, psycopg2, boto3/botocore, requests, urllib3 auto-instrumented. Custom OTEL counters for firehose sends, DB operations, event validation, heartbeats. No SLOs/SLAs defined. No /ops/* diagnostic endpoints. Logging via cnlib.log wrapper.

## Current Auth Model

> HMAC-based: T1_SALT environment variable used with cnlib.cnlib.token_hash.security_hash_match(tvid, h_value, salt) to validate TV identity. No RBAC. AWS IAM for Firehose/RDS access.

## External Dependencies & Integrations

### Outbound Dependencies (services this app calls)

- **AWS RDS PostgreSQL** — blacklisted channel IDs lookup via direct psycopg2 connections (no pooling). Interface: direct SQL. Documented in dbhelper.py.
- **AWS Kinesis Data Firehose** — data delivery via cnlib.firehose.Firehose.send_records(). Interface: AWS SDK (boto3). Multiple streams: evergreen, legacy, debug variants.

### Inbound Consumers (services that call this app)

- **SmartCast TVs** — millions of devices sending telemetry via HTTP POST. Firmware-driven, backward compatibility critical.
- **AWS Global Accelerator** — routes TV traffic to EKS pods.
- **Internal monitoring** — health check on `/status`.

### Shared Infrastructure

- **RDS PostgreSQL** — `tvevents_blacklisted_station_channel_map` table. Other services may also reference this table.

### Internal Libraries / Shared Repos

- **cntools_py3/cnlib** — git submodule. Used for: `firehose.Firehose` (Kinesis delivery), `token_hash.security_hash_match` (HMAC validation), `log.getLogger` (logging wrapper).

### Data Dependencies

- Downstream analytics pipelines consume data from Kinesis Firehose S3 destinations (e.g., `cn-tvevents/<zoo>/tvevents/` buckets).

## Age of Application

> Originally built as part of the Inscape/Vizio TV analytics platform. Containerized as tvevents-k8s. Recent work includes OTEL instrumentation, CVE remediation, and GitHub Actions CI. Actively maintained.

## Why Rebuild Now

> The application needs modernization: Python 3.10 → 3.12, Flask → FastAPI, cnlib git submodule → standalone modules, Kinesis Firehose → Kafka, no connection pooling → pooled RDS client, no /ops/* endpoints → full SRE contract, no OpenAPI → auto-generated spec, massive unused dependency list → lean dependencies. The standalone rds_module and kafka_module have already been built and need to be integrated.

## Known Technical Debt

1. **Python 3.10** — behind LTS, missing modern features
2. **Flask WSGI** — synchronous, requires gevent workaround
3. **cnlib git submodule** — fragile dependency, setup.py install pattern
4. **No connection pooling** — psycopg2 opens/closes per query
5. **87+ runtime dependencies** — many unused (pymemcache, PyMySQL, redis, fakeredis, google-cloud-monitoring, pygerduty, pyzmq, python-consul)
6. **No OpenAPI spec** — undocumented API
7. **No /ops/* endpoints** — no SRE diagnostics
8. **No docker-compose** — manual local dev setup
9. **AWS Kinesis lock-in** — Firehose for data delivery
10. **pylint disable comments** — suppressed warnings throughout codebase
11. **Mutable default argument** — `flatten_request_json(ignore_keys=[])`
12. **Mixed error handling** — some exceptions swallowed, inconsistent patterns

## What Must Be Preserved

- POST `/` payload format and behavior (TV firmware backward compatibility)
- GET `/status` returning `OK`
- T1_SALT HMAC security validation
- Event type classification: NATIVEAPP_TELEMETRY, ACR_TUNER_DATA, PLATFORM_TELEMETRY
- JSON flattening logic and output field names
- Channel blacklist obfuscation (3-tier cache pattern)
- PanelData validation schema for PLATFORM_TELEMETRY
- Heartbeat validation for ACR_TUNER_DATA

## What Can Be Dropped

- cnlib git submodule (replaced by standalone modules + inline hash)
- Kinesis Data Firehose (replaced by Kafka via kafka_module)
- Unused dependencies: pymemcache, PyMySQL, redis, fakeredis, google-cloud-monitoring, pygerduty, pyzmq, python-consul, boto (v2), google-api-core, google-auth, google-cloud-core, schema, sortedcontainers
- Gunicorn/gevent (replaced by uvicorn)
- cnlib.log wrapper (replaced by standard Python logging)
- Legacy firehose stream naming (SEND_LEGACY, SEND_EVERGREEN flags)
- pygerduty (PagerDuty SDK — alerting is now external via SRE agent)
- google-cloud-monitoring (Stackdriver — replaced by OTEL)

## Template Repository (Required)

| Field | Value |
|---|---|
| Repo | [`rebuilder-evergreen-template-repo-python`](https://github.com/CognitiveNetworks/rebuilder-evergreen-template-repo-python) |
| Clone Location | `template/` |
| Authoritative Checklist | `template/skill.md` — every checkbox must be completed during the Build phase |
| What it defines | Dockerfile, entrypoint.sh, environment-check.sh, Helm charts, CI workflows, pip-compile, OTEL auto-instrumentation, quality gate tooling, coding practices |

## Developer Context (Optional)

> The standalone modules `rebuilder-evergreen-rds-python` (rds_module) and `rebuilder-evergreen-kafka-python` (kafka_module) are already created and tested. They should be included as local path dependencies in the rebuilt service and mounted via docker-compose for local development. The rebuilt service must be able to run locally with `docker compose up --build`. The target repo is `rebuilder-evergreen-tvevents`.

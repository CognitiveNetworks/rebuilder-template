# Rebuild Candidate 1: Full Rebuild — Python 3.12 / FastAPI with Kafka and Standalone Modules

> **Reference document.** This candidate was generated during Step 5 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## Summary

Complete rebuild of evergreen-tvevents as a modern Python 3.12 / FastAPI service. Replace Kinesis Data Firehose with Kafka (via standalone kafka_module), replace direct psycopg2 with pooled RDS client (via standalone rds_module), eliminate cnlib git submodule, add full /ops/* SRE endpoints, auto-generated OpenAPI spec, docker-compose local stack, and full template compliance.

## Approach

| Aspect | Decision |
|---|---|
| **Language** | Python 3.12 |
| **Framework** | FastAPI + uvicorn |
| **Database** | PostgreSQL via `rds_module` (connection pooling, retry, OTEL) |
| **Data Delivery** | Kafka via `kafka_module` (replaces Kinesis Firehose) |
| **Security** | Inline HMAC (replaces cnlib.token_hash) |
| **Logging** | Standard Python `logging` with structured JSON output |
| **Observability** | OTEL auto-instrumentation + custom metrics + /ops/* endpoints |
| **Container** | `python:3.12-slim` base, non-root user, multi-stage optional |
| **Orchestration** | Kubernetes (EKS) via Helm charts |
| **IaC** | Terraform (new — legacy has none) |
| **CI/CD** | GitHub Actions (enhanced pipeline per template) |
| **Local Dev** | docker-compose with PostgreSQL, Kafka, app, seed data |
| **Cloud** | AWS (same as legacy — no migration) |

## Architecture

```
src/app/
├── __init__.py          # Package init
├── main.py              # FastAPI app factory, OTEL setup, lifespan
├── config.py            # Pydantic Settings configuration
├── deps.py              # Dependency injection (RDS, Kafka, cache)
├── routes.py            # HTTP endpoints (POST /, GET /status, /health)
├── ops.py               # /ops/* SRE diagnostic and remediation endpoints
├── event_types.py       # Event type classification and validation
├── output.py            # JSON flattening and output generation
├── obfuscation.py       # Blacklist lookup and channel obfuscation
├── security.py          # HMAC hash validation (inline, replaces cnlib)
├── models.py            # Pydantic request/response models
├── middleware.py         # Request logging, metrics middleware
└── exceptions.py        # Custom exception classes and handlers
```

## What Changes

| Component | Legacy | Target |
|---|---|---|
| Framework | Flask 3.1.1 + Gunicorn/gevent | FastAPI + uvicorn |
| Python | 3.10 | 3.12 |
| Data delivery | Kinesis Firehose (cnlib) | Kafka (kafka_module) |
| RDS client | psycopg2 direct (no pool) | rds_module (ThreadedConnectionPool) |
| Security hash | cnlib.token_hash | Inline HMAC in security.py |
| Logging | cnlib.log wrapper | Standard Python logging |
| API documentation | None | OpenAPI auto-generated |
| Health check | Shallow `/status` → "OK" | Deep `/health` + `/ops/health` with dependency checks |
| SRE endpoints | None | Full /ops/* contract (11 endpoints) |
| Dependencies | 87+ runtime | ~15-20 runtime |
| Local dev | Manual minikube setup | docker-compose up --build |
| Type annotations | None | Full type hints |
| Error handling | Broad catch-all, all 400 | Typed exceptions, appropriate HTTP codes |
| Configuration | os.environ.get scattered | Pydantic Settings centralized |

## What Stays the Same

| Aspect | Detail |
|---|---|
| POST `/` payload format | Identical — TV firmware backward compatibility |
| GET `/status` | Identical — returns "OK" |
| Event types | NATIVEAPP_TELEMETRY, ACR_TUNER_DATA, PLATFORM_TELEMETRY |
| Validation logic | Same required params, timestamp checks, event-type schemas |
| JSON flattening | Same algorithm, same output field names |
| Channel obfuscation | Same 3-tier cache, same obfuscation rules |
| T1_SALT HMAC | Same algorithm, different implementation |
| Cloud provider | AWS (no migration) |
| Container orchestration | Kubernetes (EKS) |

## External Module Integration

### kafka_module (rebuilder-evergreen-kafka-python)

- **Location:** `/Users/dan.gorman/Vizio/rebuilder-evergreen-kafka-python`
- **Integration:** Local path dependency in pyproject.toml; volume mount in docker-compose
- **Usage:** `kafka_module.producer.send_message(topic, payload_bytes, key)` replaces `cnlib.firehose.Firehose.send_records()`
- **Health check:** `kafka_module.producer.health_check()` used by `/health` and `/ops/health`

### rds_module (rebuilder-evergreen-rds-python)

- **Location:** `/Users/dan.gorman/Vizio/rebuilder-evergreen-rds-python`
- **Integration:** Local path dependency in pyproject.toml; volume mount in docker-compose
- **Usage:** `rds_module.client.execute_query(sql, params)` replaces `TvEventsRds._execute(query)`
- **Connection pooling:** ThreadedConnectionPool with configurable min/max, retry on DatabaseError/InterfaceError

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| token_hash algorithm must match production | Extract from cnlib source; test with known tvid/hash/salt vectors |
| Kafka topic naming must align with downstream consumers | Document topic mapping; coordinate with data engineering team |
| TV firmware backward compatibility | Preserve exact POST `/` URL params and JSON response ("OK") |
| rds_module/kafka_module not pip-installable in CI | Use `--disable=import-error` for pylint; `--ignore-missing-imports` for mypy |

## Recommendation

**This is the recommended approach.** It addresses all 10 modernization opportunities, uses the already-built standalone modules, conforms to template repo standards, and maintains full backward compatibility with TV firmware. The application's small size (1,169 source lines) makes a full rebuild faster and cleaner than incremental migration.

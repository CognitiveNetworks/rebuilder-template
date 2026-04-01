# ADR-001: Use FastAPI as Web Framework

## Status

Accepted

## Context

The legacy evergreen-tvevents application uses Flask 3.1.1 with Gunicorn and gevent workers. Flask is a synchronous WSGI framework that requires gevent for concurrent request handling. It does not auto-generate OpenAPI specs, does not provide typed request/response models, and requires manual validation logic. The application has only 2 endpoints (POST `/` and GET `/status`), making migration straightforward.

## Decision

Replace Flask with FastAPI as the web framework. Use uvicorn as the ASGI server.

## Rationale

1. **Auto-generated OpenAPI** — FastAPI generates OpenAPI documentation from Pydantic models and type hints, eliminating the need for manual API documentation
2. **Typed request/response models** — Pydantic v2 models provide automatic validation, serialization, and documentation with `json_schema_extra` examples
3. **Async support** — Native async/await support without gevent workarounds
4. **Modern Python patterns** — Type hints, dependency injection, lifespan events
5. **Template compliance** — The template repo (`rebuilder-evergreen-template-repo-python`) uses FastAPI as the standard framework
6. **OTEL auto-instrumentation** — OpenTelemetry has a FastAPI instrumentor (`opentelemetry-instrumentation-fastapi`)

## Consequences

- **Positive:** OpenAPI spec at `/docs`, typed APIs, better performance, async-ready
- **Positive:** Simplified error handling via FastAPI exception handlers
- **Negative:** Gunicorn/gevent replaced with uvicorn (different worker model)
- **Negative:** Flask test client replaced with FastAPI TestClient (httpx-based)
- **Migration effort:** Low — only 2 endpoints to migrate

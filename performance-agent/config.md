# Performance Agent Configuration

**Instructions:** Fill out this file when setting up the performance agent for a specific project. This provides project-specific context that the agent needs for profiling and optimization work. Replace all `[TODO]` placeholders with actual values.

## Project

- **Project Name:** *[TODO: e.g., evergreen-tvevents]*
- **Repository:** *[TODO: e.g., CognitiveNetworks/evergreen-tvevents]*
- **Primary Language:** Python 3.12
- **Framework:** *[TODO: e.g., FastAPI ≥ 0.115.0]*

## Profiling Commands

| Command | Purpose |
|---|---|
| `pip install -e ".[dev]"` | Install all dependencies including profiling tools |
| `python -m cProfile -o output.prof src/app/main.py` | CPU profile the application |
| `python -m memory_profiler src/app/main.py` | Memory profile the application |
| `py-spy top --pid <PID>` | Live profile a running process |
| `py-spy record -o profile.svg --pid <PID>` | Generate flamegraph for running process |
| `pytest tests/ --benchmark-compare` | Run performance benchmarks |

## Performance Targets

> Define latency and resource targets for the service. Use `N/A` for targets that don't apply.

| Metric | Target | Measurement Method |
|---|---|---|
| P50 response latency | *[TODO: e.g., < 50ms]* | *[TODO: e.g., OTEL histogram]* |
| P99 response latency | *[TODO: e.g., < 200ms]* | *[TODO: e.g., OTEL histogram]* |
| Peak memory per container | *[TODO: e.g., < 256MB]* | *[TODO: e.g., container metrics]* |
| Startup time | *[TODO: e.g., < 5s]* | *[TODO: e.g., health endpoint check]* |
| Requests per second | *[TODO: e.g., ≥ 1000 RPS per pod]* | *[TODO: e.g., load test]* |

## Known Hot Paths

> List the critical code paths that handle the most traffic or are most latency-sensitive.

| Path | Description | Current Performance |
|---|---|---|
| *[TODO: e.g., POST /events]* | *[TODO: e.g., Main event ingestion endpoint]* | *[TODO: e.g., P50=30ms, P99=150ms]* |

## Profiling Dependencies

> Additional packages needed for profiling. These should be in `requirements-dev.txt`.

| Package | Version | Purpose |
|---|---|---|
| `line-profiler` | latest | Line-by-line CPU profiling |
| `memory-profiler` | latest | Memory usage profiling |
| `py-spy` | latest | Production process profiling |
| `pytest-benchmark` | latest | Repeatable benchmark tests |
| `tracemalloc` | stdlib | Memory leak detection |

## Infrastructure Context

> Context the performance agent needs about the runtime environment.

- **Container Memory Limit:** *[TODO: e.g., 512MB]*
- **Container CPU Limit:** *[TODO: e.g., 500m]*
- **Replicas (prod):** *[TODO: e.g., 3]*
- **Database:** *[TODO: e.g., PostgreSQL 15 on RDS, r6g.large]*
- **Cache:** *[TODO: e.g., Redis 7 on ElastiCache, cache.t4g.micro]*
- **Message Queue:** *[TODO: e.g., Kafka on MSK, 3 brokers]*

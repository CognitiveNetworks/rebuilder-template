# Playbook: High Latency

## Trigger Condition

- Monitoring alert indicating elevated response times
- `/ops/status` shows **degraded** or **unhealthy** with latency as the contributing signal
- `/ops/metrics` shows p95 or p99 latency above SLO threshold

## Diagnostic Steps

1. **Check `/ops/status`** — Confirm the service is degraded/unhealthy and latency is the primary signal.
2. **Check `/ops/metrics`** — Review latency distribution (p50, p95, p99).
   - Is p50 elevated (everything is slow) or only p99 (tail latency)?
   - Check saturation — CPU, memory, connection pool utilization. Is the service resource-constrained?
3. **Check `/ops/health`** — Is a downstream service slow?
   - If a dependency shows degraded latency, the root cause is likely downstream. Follow the chain.
4. **Check `/ops/health`** — Are connection pools exhausted? Queue depths elevated?
5. **Check `/ops/errors`** — Are there timeout errors correlating with the latency spike?

## Remediation Actions

| Condition | Action |
|---|---|
| Latency caused by stale or oversized cache responses | Flush cache via `/ops/cache/flush` |
| Latency caused by a slow dependency with an open circuit | Reset circuit via `/ops/circuits` (only if dependency has recovered) |
| Single instance with high latency, others normal | **Escalate** — the orchestrator (KEDA/HPA) should handle instance rotation |
| Connection pool exhaustion | **Escalate** — may need pool size increase or connection leak investigation |
| CPU/memory saturation across all instances | **Escalate** — scaling is managed by cloud-native auto-scaling (KEDA/HPA/Cloud Run). If auto-scaling hasn’t resolved the issue, escalate for capacity planning |
| Downstream dependency is the root cause | Triage the dependency service (run this workflow against it) |

## After Remediation

1. Wait 5 minutes.
2. Re-check `/ops/status` and `/ops/metrics` latency values.
3. If p99 returns within SLO, monitor for 5 minutes.
4. If latency does not improve, escalate.

## Escalation Criteria

- Latency remains above SLO after remediation (including scaling if attempted).
- Service is already at its configured maximum instance count and saturation persists.
- Saturation is at capacity and cannot be relieved by draining a single instance (and no scaling is configured).
- Root cause is a slow database query or missing index (requires code/schema change).
- Latency spike correlates with a recent deployment.

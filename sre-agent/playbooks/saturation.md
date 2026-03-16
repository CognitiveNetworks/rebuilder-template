# Playbook: Saturation

## Trigger Condition

- Monitoring alert indicating resource exhaustion (CPU, memory, disk, connections)
- `/ops/status` shows **degraded** or **unhealthy** with saturation as the contributing signal
- `/ops/metrics` shows saturation above warning threshold (typically >80%)

## Diagnostic Steps

1. **Check `/ops/status`** — Confirm the service is degraded/unhealthy and saturation is the primary signal.
2. **Check `/ops/metrics`** — Identify which resource is saturated:
   - **CPU:** Compute-bound. Check if traffic spiked or if a runaway process is consuming cycles.
   - **Memory:** Possible memory leak, oversized cache, or connection accumulation.
   - **Disk:** Log accumulation, temp file buildup, or database growth.
   - **Connection pool:** All connections to database or cache are in use. Possible connection leak or slow query holding connections.
   - **Queue depth:** Background job backlog growing faster than workers can process.
3. **Check `/ops/health`** — Look at connection pool utilization and queue depths specifically.
4. **Check `/ops/health`** — Is the saturation caused by a slow dependency holding resources open?
5. **Check `/ops/errors`** — Are there timeout errors or rejected connection errors correlating with saturation?

## Remediation Actions

| Condition | Action |
|---|---|
| Single instance saturated, others healthy | **Escalate** — the orchestrator (KEDA/HPA) should handle instance rotation. If it doesn’t, a human must investigate. |
| Cache is consuming excessive memory | Flush cache via `/ops/cache/flush`. Monitor memory after flush. |
| Connection pool exhausted due to tripped circuit (connections stuck waiting) | Reset circuit via `/ops/circuits`. Connections should release. |
| All instances saturated — traffic spike | **Escalate** — scaling is managed by cloud-native auto-scaling (KEDA/HPA/Cloud Run). If auto-scaling hasn’t resolved the issue, escalate for capacity planning. |
| All instances saturated — no traffic spike | **Escalate** — likely a memory leak, connection leak, or runaway process. Scaling will not fix the root cause. Requires investigation. |
| Disk saturation | **Escalate** — agent does not delete files or modify storage. |
| Queue depth growing — workers cannot keep pace | **Escalate** — scaling is managed by cloud-native auto-scaling. If auto-scaling hasn’t resolved the issue, escalate for capacity planning or investigation into why jobs are failing/slow. |

## After Remediation

1. Wait 5 minutes after cache flush or circuit reset.
2. Re-check `/ops/status` and `/ops/metrics` saturation values.
3. If saturation drops below warning threshold, monitor for 5 minutes.
4. If scaling was performed, verify that new instances are healthy via `/ops/status`.
5. If saturation does not decrease, escalate.

## Escalation Criteria

- All instances are saturated and auto-scaling has not resolved the issue.
- Service is already at its configured maximum instance count and still saturated.
- Saturation is caused by a resource leak (memory, connections) that requires a code fix. Scaling will not resolve leaks.
- Disk is full — requires log rotation, cleanup, or storage expansion.
- Queue backlog is growing without bound and workers are already at max scale.
- Saturation persists after cache flush, circuit reset, and scaling.

# Playbook: High Error Rate

## Trigger Condition

- PagerDuty alert indicating elevated error rate (5xx responses, unhandled exceptions, application errors)
- `/ops/status` shows **degraded** or **unhealthy** with errors as the contributing signal
- `/ops/metrics` shows error rate above SLO threshold

## Diagnostic Steps

1. **Check `/ops/status`** — Confirm the service is degraded/unhealthy and errors are the primary signal.
2. **Check `/ops/errors`** — Get error types, counts, and sample stack traces.
   - Are the errors a single type (one root cause) or multiple types (systemic issue)?
   - Are the stack traces pointing to application code or a dependency call?
3. **Check `/ops/dependencies`** — Is a downstream service failing?
   - If yes, follow the dependency chain — the error source may be upstream.
4. **Check `/ops/metrics`** — Look at traffic and latency.
   - Did traffic spike before errors started? (load-related)
   - Is latency elevated alongside errors? (saturation or dependency slowdown)
5. **Check `/ops/circuits`** — Are circuit breakers tripped?
   - If a circuit is open, the service is already protecting itself from a failed dependency.

## Remediation Actions

| Condition | Action |
|---|---|
| Errors caused by a dependency that has recovered | Reset circuit breakers via `/ops/circuits` |
| Errors correlate with stale cache data | Flush cache via `/ops/cache/flush` |
| Single instance producing all errors | Drain the instance via `/ops/drain` |
| Errors are application bugs (NPE, type errors, logic errors) | **Escalate** — requires a code fix |
| Errors across all instances with no dependency issue | **Escalate** — likely a bad deployment or config change |

## After Remediation

1. Wait 5 minutes.
2. Re-check `/ops/status`.
3. If status improves, monitor for 5 minutes.
4. If status does not improve, escalate.

## Escalation Criteria

- Error rate does not decrease after remediation actions.
- Errors are caused by application code (not infrastructure or dependencies).
- Error pattern is unknown or does not match any condition above.
- Multiple services are showing the same error pattern simultaneously.

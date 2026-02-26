# Playbook: Dependency Failure

## Trigger Condition

- PagerDuty alert indicating a downstream service or external dependency is unreachable
- `/ops/status` shows **degraded** or **unhealthy** with dependency health as the contributing signal
- `/ops/dependencies` shows one or more dependencies as impaired or unreachable

## Diagnostic Steps

1. **Check `/ops/status`** — Confirm the service is degraded/unhealthy.
2. **Check `/ops/dependencies`** — Identify which dependencies are impaired.
   - Is it an internal service or an external third-party API?
   - Is it the database, cache, or a downstream microservice?
3. **For each impaired dependency:**
   - If it's an internal service, call `/ops/status` on that service. Determine if the dependency is unhealthy or if the network path is broken.
   - If it's an external service, check `/ops/errors` for timeout patterns and error messages.
4. **Check `/ops/circuits`** — Are circuit breakers open for the failed dependency?
   - If yes, the service is already protecting itself. Determine if the dependency has recovered.
5. **Check `/ops/metrics`** — Is the failure causing cascading effects? Elevated error rates, latency spikes, or saturation on the affected service?

## Remediation Actions

| Condition | Action |
|---|---|
| Dependency has recovered but circuit breaker is still open | Reset circuit via `/ops/circuits` |
| Non-critical dependency is down, service can function without it | Verify service is degraded (not unhealthy). Monitor. No action needed unless it escalates. |
| Critical dependency (database, auth) is down | **Escalate immediately** — this requires infrastructure intervention |
| External third-party API is down | **Escalate** — nothing the agent can do. Document and notify. |
| Cache dependency is down but service can fall back to database | Verify fallback is working via `/ops/errors`. Monitor. |
| Multiple dependencies failing simultaneously | **Escalate** — likely infrastructure-level issue (network, cloud provider) |

## After Remediation

1. If a circuit was reset, wait 5 minutes.
2. Re-check `/ops/status` and `/ops/dependencies`.
3. If the dependency shows as healthy and the service status improves, monitor for 5 minutes.
4. If the dependency remains impaired, escalate.

## Escalation Criteria

- Critical dependency is unreachable (database, auth provider, primary data store).
- Dependency failure is causing cascading failures across multiple services.
- Circuit reset did not restore connectivity.
- External dependency is down with no ETA from the provider.
- Root cause is a network partition or cloud provider issue.

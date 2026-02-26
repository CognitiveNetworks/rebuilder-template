# Playbook: Service Down (Cloud Run)

## Trigger

- GCP Uptime Check fails (health endpoint returns non-2xx or times out)
- PagerDuty alert with description matching: "Uptime Check", "health check failed", "service unavailable", "Cloud Run service not responding"
- `/ops/status` returns connection refused, timeout, or 503

## Severity

- **P1 — Critical** if the service is marked `critical: true` in the service registry
- **P2 — High** otherwise

## Impact

Service is completely unavailable. All API requests fail. Downstream consumers receive errors.

## Diagnosis Steps

1. **Attempt to reach the service:**
   - Call `/ops/status` on the affected service
   - If connection refused or timeout → the service is down, not just degraded
   - If 503 → the service is running but unhealthy (see dependency-failure playbook instead)

2. **Check Cloud Run revision status:**
   - Use `query_cloud_metrics` to check `run.googleapis.com/container/instance_count`
   - If instance count is 0 → Cloud Run has scaled to zero or the revision is not serving
   - If instance count > 0 but health check fails → application crash loop

3. **Check for recent deployment:**
   - Use `query_cloud_logs` with filter: `resource.type="cloud_run_revision"` and look for revision creation events
   - A bad deployment may have introduced a crash

4. **Check Cloud Run logs for crash reasons:**
   - Use `query_cloud_logs` with filter: `resource.type="cloud_run_revision" AND severity>=ERROR`
   - Common causes: missing environment variable, failed secret access, dependency timeout on startup, OOM kill

## Root Causes

| Cause | Evidence | Remediation |
|---|---|---|
| Scaled to zero + cold start failure | Instance count = 0, startup errors in logs | Force new revision (scale up) |
| Bad revision deployed | Recent revision creation, crash loop in logs | Escalate for rollback |
| Secret access failure | `PermissionDenied` or `SecretNotFound` in logs | Escalate (config change needed) |
| Dependency timeout on startup | Startup probe timeout, connection errors to Redis/DB | Check dependency health, may self-resolve |
| OOM kill | `Memory limit exceeded` in logs | Escalate (resource config change needed) |
| Cloud Run platform issue | No application logs, GCP status page shows incident | Document and wait for GCP resolution |

## Remediation

### If the service is scaled to zero or has no healthy instances:

1. **Force a new instance** by calling the health endpoint directly — Cloud Run will spin up a new instance to handle the request
2. Wait 60 seconds
3. Re-check `/ops/status`
4. If still down, the issue is not just cold start — proceed to escalation

### If the service is crash-looping:

1. Check logs for the specific error
2. If it's a dependency timeout (Redis, DB) → check `/ops/dependencies` on the service (if reachable) or check the dependency directly
3. If the dependency has recovered, the service may self-heal on next restart attempt
4. Wait 2 minutes for Cloud Run to retry
5. Re-check `/ops/status`
6. If still down → escalate (likely requires code fix or config change)

### If a bad revision was deployed:

1. **Escalate immediately** — the agent does not perform rollbacks
2. Include in escalation: the revision ID, the error from logs, and the timestamp of the deployment
3. Recommended action for human: roll back to previous revision via `gcloud run services update-traffic`

## Escalation Triggers

- Service remains down after 2 re-check cycles (5 minutes total)
- Crash loop with application error (requires code fix)
- Secret or IAM permission error (requires config change)
- OOM kill (requires resource limit change)
- Bad deployment (requires rollback)
- GCP platform issue (nothing the agent can do)

## Post-Resolution

1. Verify `/ops/status` returns healthy
2. Verify `/ops/metrics` shows requests being processed
3. Acknowledge the PagerDuty alert
4. Write incident report
5. Email incident report

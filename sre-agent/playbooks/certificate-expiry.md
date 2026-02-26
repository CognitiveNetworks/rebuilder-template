# Playbook: Certificate Expiry

## Trigger Condition

- PagerDuty alert indicating TLS certificate is expiring or has expired
- `/ops/errors` shows TLS handshake failures, certificate validation errors, or connection refused errors with TLS context
- `/ops/dependencies` shows a dependency as unreachable with TLS-related error messages

## Diagnostic Steps

1. **Check `/ops/status`** — Determine overall service health. Certificate issues may show as dependency failures.
2. **Check `/ops/errors`** — Look for error patterns:
   - `certificate has expired` — the cert is already expired
   - `certificate is not yet valid` — clock skew or premature cert rotation
   - `unable to verify the first certificate` — CA chain issue
   - `TLS handshake timeout` — may be cert-related or network-related
3. **Check `/ops/dependencies`** — Identify which connections are failing with TLS errors.
   - Is it the service's own certificate (clients can't connect to it)?
   - Is it a dependency's certificate (this service can't connect to a downstream)?
   - Is it an external third-party API with an expired cert?
4. **Check `/ops/config`** — Verify certificate paths and expected expiry dates if exposed in sanitized config.

## Remediation Actions

| Condition | Action |
|---|---|
| Any certificate issue | **Escalate** — the agent does not manage certificates, rotate secrets, or modify TLS configuration. |

Certificate issues always require human intervention. The agent's role is:
1. Diagnose and confirm the issue is certificate-related (not a network partition or DNS failure).
2. Identify exactly which certificate is affected (service cert, dependency cert, CA cert).
3. Provide the human responder with all diagnostic context to act quickly.

## Temporary Mitigation

There is no safe temporary mitigation the agent can perform for certificate issues. Do not:
- Disable TLS verification
- Bypass certificate checks
- Modify any TLS configuration

## Escalation — Always

Certificate expiry is always an escalation. Include in the escalation:
1. Which service is affected.
2. Whether it's the service's own cert or a dependency's cert.
3. The exact error message from `/ops/errors`.
4. Which connections are failing from `/ops/dependencies`.
5. When the alert first fired (to determine urgency — expired vs. expiring soon).

## Prevention Note

Certificate expiry alerts should fire at 30, 14, and 7 days before expiry. If this alert fired on an already-expired certificate, file a GitHub issue to add or fix the early-warning monitoring.

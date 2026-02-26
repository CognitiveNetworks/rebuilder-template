# Disaster Recovery Plan

> Documented recovery procedures for each production service. An on-call engineer who did not build the system should be able to follow this at 3 AM.
>
> See `WINDSURF.md` > Disaster Recovery & Business Continuity for requirements.

## Recovery Objectives

| Service | RTO (Recovery Time) | RPO (Recovery Point) | Tier |
|---|---|---|---|
| | | | |

### Tier Definitions

- **Tier 1** — business-critical, multi-zone/region, RTO < 1 hour
- **Tier 2** — important, single-region with failover, RTO < 4 hours
- **Tier 3** — internal/non-critical, single-zone acceptable, RTO < 24 hours

## Backup Strategy

| Data Store | Backup Method | Frequency | Retention | Storage Location | Last Tested |
|---|---|---|---|---|---|
| | | | | | |

## Recovery Runbook

### Scenario: Database Failure

1. [step-by-step instructions]
2. [verification steps]

### Scenario: Full Region Outage

1. [step-by-step instructions]
2. [verification steps]

### Scenario: Infrastructure Rebuild from Scratch

1. [Terraform commands to recreate all resources]
2. [Data restore procedure]
3. [Service deployment order]
4. [Verification steps]

## Dependencies

| Dependency | Recovery Mechanism | Contact |
|---|---|---|
| | | |

## Communication Plan

| Audience | Channel | Responsible | Template |
|---|---|---|---|
| Engineering | | | |
| Stakeholders | | | |
| Customers (if applicable) | | | |

## Testing Schedule

- **Backup restore test:** [quarterly / monthly]
- **Failover test:** [quarterly / annually]
- **Full DR drill:** [annually]
- **Last drill date:** [date]
- **Last drill outcome:** [summary]

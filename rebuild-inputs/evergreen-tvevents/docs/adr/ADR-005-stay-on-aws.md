# ADR-005: Stay on AWS

## Status

Accepted

## Context

The legacy application runs on AWS EKS with dependencies on AWS RDS PostgreSQL and AWS Kinesis Data Firehose. The scope.md specifies no cloud migration — the rebuilt service stays on AWS.

## Decision

The rebuilt service remains on AWS. Use AWS EKS for container orchestration, AWS RDS PostgreSQL for the database, and AWS Secrets Manager for secrets. Replace Kinesis Firehose with Kafka (see ADR-002), which can run on AWS MSK.

## Rationale

1. **No migration required** — The scope explicitly states AWS as the target cloud
2. **Existing infrastructure** — EKS clusters, RDS instances, VPC networking, IAM roles are already provisioned
3. **Team expertise** — Operations team has AWS expertise
4. **Kafka on MSK** — AWS MSK provides managed Kafka, maintaining the AWS operational model while reducing Firehose-specific lock-in

## Consequences

- **Positive:** No infrastructure migration, no new cloud provider learning curve
- **Positive:** Existing IAM roles, VPC, and networking can be reused
- **Negative:** AWS-specific Terraform (EKS, MSK, RDS) — not portable to GCP without rewrite

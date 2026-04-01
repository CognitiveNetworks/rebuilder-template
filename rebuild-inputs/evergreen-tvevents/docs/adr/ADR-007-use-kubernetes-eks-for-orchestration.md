# ADR-007: Use Kubernetes (EKS) for Container Orchestration

## Status

Accepted

## Context

The legacy application runs on AWS EKS with Helm charts, KEDA autoscaling (up to 500 pods in production), rolling update deployments, pod disruption budgets, and OTEL Collector sidecars. The Kubernetes operational model is well-established for the team.

## Decision

Continue using AWS EKS for container orchestration. Use Helm charts from the template repo. Add Terraform for infrastructure-as-code (the legacy app has no IaC).

## Rationale

1. **Existing expertise** — Team operates EKS clusters with established Helm chart patterns
2. **Scaling requirements** — KEDA autoscaling (up to 500 pods) is already proven for this workload
3. **Template compliance** — The template repo defines Helm chart templates for EKS deployments
4. **Infrastructure-as-code** — Adding Terraform provides reproducible infrastructure provisioning (missing from legacy)

## Consequences

- **Positive:** Same operational model, same scaling, same monitoring
- **Positive:** Terraform adds IaC where legacy had none
- **Negative:** EKS is AWS-specific (acceptable per ADR-005)

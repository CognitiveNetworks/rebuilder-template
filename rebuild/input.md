# Rebuild Input

**Instructions:** This is a template. Copy this file and `scope.md` to a working directory before filling out. Both files must be completed before running the rebuild process.

## Application Name

> *[Name of the application being rebuilt]*

## Repository / Source Location

> *[Path or URL to the legacy codebase]*

## Current Tech Stack Summary

> *[One-paragraph summary: language, framework, database, infrastructure, auth model]*

## Current API Surface

> *[Summary of the API: number of endpoints, resource groups, authentication method, documentation status, known consumers]*

## Current Observability

> *[What monitoring, logging, alerting, and tracing exists today? Are there SLOs/SLAs? How are failures detected?]*

## Current Auth Model

> *[How do users and services authenticate? Is there RBAC? Are there shared credentials or hardcoded keys?]*

## External Dependencies & Integrations

> **Instructions:** Document every service, system, or repo this application interacts with at runtime or through data exchange. This is critical for multi-repo rebuilds — dependencies discovered late derail timelines.

### Outbound Dependencies (services this app calls)

> *What APIs, services, or systems does this application call at runtime? Include internal services, third-party APIs, payment processors, email providers, notification services, etc. For each, note: the service name, the interface (REST, gRPC, SDK, direct DB), and whether the interface is documented.*

### Inbound Consumers (services that call this app)

> *What services, systems, or scheduled jobs call this application's API? Include known API consumers, webhook subscribers, batch processes, and internal tools. If consumers are unknown, say so — that is a risk finding.*

### Shared Infrastructure

> *Does this application share databases, caches, message queues, storage buckets, or other infrastructure with other repos or services? Shared infrastructure creates implicit coupling that survives a rebuild.*

### Internal Libraries / Shared Repos

> *Does this application import libraries or packages from internal repos (not public package registries)? Include shared utility libraries, common auth packages, internal SDKs, or any dependency that comes from a repo your organization owns.*

### Data Dependencies

> *Do other systems read from or write to this application's data? Include ETL pipelines, data warehouse feeds, CDC streams, reporting systems, analytics platforms, or any process that depends on this application's database or API for data.*

## Age of Application

> *[When was it originally built? When was the last significant change? How actively is it maintained?]*

## Why Rebuild Now

> *[What is the trigger for this rebuild? What makes incremental improvement impractical?]*

## Known Technical Debt

> *[Enumerated list of known issues across security, reliability, maintainability, and operations]*

## What Must Be Preserved

> *[Non-negotiable behaviors, data, and interfaces that must survive the rebuild]*

## What Can Be Dropped

> *[Aspects of the current system that are not worth preserving]*

## Developer Context (Optional)

> *[Any additional context that would help the rebuild process — team size, constraints, timeline, organizational context]*

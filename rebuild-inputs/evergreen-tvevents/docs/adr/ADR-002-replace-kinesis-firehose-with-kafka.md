# ADR-002: Replace Kinesis Data Firehose with Kafka

## Status

Accepted

## Context

The legacy application sends processed TV event data to AWS Kinesis Data Firehose streams via `cnlib.firehose.Firehose.send_records()`. Four streams are configured: evergreen, legacy, debug-evergreen, and debug-legacy. Firehose delivery is tightly coupled to AWS and the cnlib git submodule. The organization is moving to Kafka for event streaming to reduce AWS lock-in and enable replay/reprocessing capabilities.

## Decision

Replace Kinesis Data Firehose with Kafka topics. Use the standalone `kafka_module` (`rebuilder-evergreen-kafka-python`) for message delivery via `send_message(topic, payload_bytes, key)`.

## Rationale

1. **Reduce AWS lock-in** — Kafka is cloud-agnostic; can run on MSK, Confluent Cloud, or self-hosted
2. **Standalone module already built** — `kafka_module/producer.py` provides `send_message()`, `health_check()`, `flush()` with full OTEL instrumentation
3. **Simpler interface** — Single `send_message(topic, payload_bytes, key)` replaces per-stream Firehose objects and ThreadPoolExecutor parallel delivery
4. **Replay capability** — Kafka retention enables downstream consumers to replay events; Firehose is fire-and-forget
5. **Existing MSK credentials** — Legacy app already has `ACR_DATA_MSK_USERNAME` / `ACR_DATA_MSK_PASSWORD` env vars, indicating MSK infrastructure exists

## Topic Mapping

| Legacy Firehose Stream | Kafka Topic | Condition |
|---|---|---|
| `EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_EVERGREEN` | Always active |
| `LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_LEGACY` | When `SEND_LEGACY=true` |
| `DEBUG_EVERGREEN_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_EVERGREEN` | When `TVEVENTS_DEBUG=true` |
| `DEBUG_LEGACY_FIREHOSE_NAME` | `KAFKA_TOPIC_DEBUG_LEGACY` | When `TVEVENTS_DEBUG=true` and `SEND_LEGACY=true` |

## Consequences

- **Positive:** Cloud-agnostic delivery, replay capability, simpler code, health_check() for /ops/health
- **Positive:** Eliminates cnlib.firehose dependency and boto3 Firehose SDK
- **Negative:** Downstream analytics pipelines must be updated to consume from Kafka topics instead of Firehose S3 destinations
- **Negative:** Kafka infrastructure (MSK or equivalent) must be provisioned if not already available
- **Migration effort:** Low — kafka_module already exists; integration is mapping firehose streams to topics

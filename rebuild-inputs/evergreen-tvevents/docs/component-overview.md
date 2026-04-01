# Component Overview: evergreen-tvevents

> **Reference document.** This component overview was generated during Step 2 of the ideation process. It informs decisions but does not override python-developer-agent/skill.md.

## System Context

The tvevents-k8s application sits at the ingestion boundary of Vizio's TV analytics platform. SmartCast TVs send telemetry payloads via HTTP POST to this service through AWS Global Accelerator. The service validates, classifies, transforms, and forwards events to Kinesis Data Firehose streams, which deposit data into S3 buckets for downstream analytics pipelines.

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌─────────────┐
│ SmartCast TV │────▶│ AWS Global   │────▶│  tvevents-k8s    │────▶│ Kinesis     │
│ (firmware)   │     │ Accelerator  │     │  (Flask/EKS)     │     │ Firehose    │
└─────────────┘     └──────────────┘     │                  │     └──────┬──────┘
                                         │  ┌────────────┐  │            │
                                         │  │ cnlib      │  │     ┌──────▼──────┐
                                         │  │ (submodule)│  │     │ S3 Buckets  │
                                         │  └────────────┘  │     │ (analytics) │
                                         │  ┌────────────┐  │     └─────────────┘
                                         │  │ RDS        │  │
                                         │  │ PostgreSQL │  │
                                         │  └────────────┘  │
                                         └──────────────────┘
```

## Domain Terminology

| Term | Definition |
|---|---|
| **TvEvent** | Top-level payload wrapper containing tvid, client, security hash (h), timestamp, and EventType |
| **EventData** | Nested payload containing event-type-specific telemetry data |
| **EventType** | Classification of the telemetry event: `NATIVEAPP_TELEMETRY`, `ACR_TUNER_DATA`, `PLATFORM_TELEMETRY` |
| **tvid** | Unique TV device identifier |
| **h** | HMAC security hash derived from tvid + T1_SALT; validates request authenticity |
| **T1_SALT** | Shared secret used for HMAC hash verification |
| **Namespace** | Event source namespace (e.g., SmartCast app namespace) |
| **AppId** | Application identifier for NATIVEAPP_TELEMETRY events |
| **PanelData** | Panel state telemetry (ON/OFF, WakeupReason) for PLATFORM_TELEMETRY events |
| **Heartbeat** | Keep-alive event subtype within ACR_TUNER_DATA |
| **channelData** | Channel tuning information (majorId, minorId) within ACR_TUNER_DATA |
| **programData** | Program metadata (starttime) within ACR_TUNER_DATA |
| **Blacklisted Channel** | A channel_id flagged in the RDS `tvevents_blacklisted_station_channel_map` table; triggers obfuscation |
| **Obfuscation** | Replacing channelid, programid, channelname with "OBFUSCATED" for blacklisted/content-blocked channels |
| **Zoo** | Environment name (from FLASK_ENV) appended to output data |
| **Firehose** | AWS Kinesis Data Firehose stream — destination for processed events |
| **cnlib** | Internal shared library (git submodule) providing Firehose, token_hash, and logging utilities |

## Components

### 1. Application Factory (`app/__init__.py`)

**Purpose:** Initializes the Flask application, OTEL instrumentation (tracing, metrics, logging), and registers routes.

**Key Responsibilities:**
- Configure OTEL TracerProvider, MeterProvider, LoggerProvider with OTLP HTTP exporters
- Auto-instrument Flask, psycopg2, boto3/botocore, requests, urllib3
- Create Flask app via `create_app()` factory pattern
- Register route blueprint and initialize route handlers
- Provide shared `meter` and `LOGGER` instances

**Dependencies:** Flask, OpenTelemetry SDK, cnlib.log

**Integration Points:** Every other module imports `meter`, `configure_logging()`, or `LOGGER` from this module.

### 2. HTTP Routes (`app/routes.py`)

**Purpose:** Defines the HTTP endpoints and request lifecycle hooks.

**Endpoints:**
| Method | Path | Handler | Description |
|---|---|---|---|
| POST | `/` | `send_request_firehose()` | Main ingestion endpoint |
| GET | `/status` | `status()` | Health check returning "OK" |

**Lifecycle Hooks:**
- `@app.before_request` → `log_request()` — logs every incoming request with method, path, headers, args
- `@app.errorhandler(TvEventsCatchallException)` → `handle_exceptions()` — returns JSON error response with 400 status

**Data Flow (POST `/`):**
1. Extract tvid from URL params, payload from JSON body
2. Set OTEL span attributes (tvid, event_type)
3. Call `utils.validate_request(args, payload)` — validates params, hash, timestamps, event-type schema
4. Call `utils.push_changes_to_firehose(payload)` — generates output JSON, applies obfuscation, sends to Firehose
5. Return "OK"

**OTEL Metrics:** `send_request_firehose_counter` — incremented on every POST request.

### 3. Event Type System (`app/event_type.py`)

**Purpose:** Classifies TV events and provides type-specific validation and output generation.

**Class Hierarchy:**

```
EventType (ABC)
├── NativeAppTelemetryEventType   (NATIVEAPP_TELEMETRY)
├── AcrTunerDataEventType         (ACR_TUNER_DATA)
└── PlatformTelemetryEventType    (PLATFORM_TELEMETRY)
```

**Event Type Details:**

| Event Type | Validation Rules | Output Transformation |
|---|---|---|
| `NATIVEAPP_TELEMETRY` | Requires `Timestamp` in EventData; timestamp validation | Flattens EventData (ignoring Timestamp key), adds `eventdata_timestamp` |
| `ACR_TUNER_DATA` | Requires `channelData` or `programData` (or Heartbeat with those nested); validates majorId/minorId for channelData, vRes/hRes for resolution | Flattens EventData; converts programdata_starttime to ms; marks heartbeats with `eventtype: Heartbeat` |
| `PLATFORM_TELEMETRY` | JSON Schema validation: PanelData required with Timestamp (number), PanelState (ON/OFF pattern), WakeupReason (0-128) | Flattens EventData; normalizes PanelState to uppercase |

**Event Type Registry:** `event_type_map` dict maps string EventType names to classes.

**OTEL Metrics:** `validate_payload_counter`, `generate_event_data_output_counter`, `heart_beat_counter`, `verify_panel_data_counter`.

### 4. Database Helper (`app/dbhelper.py`)

**Purpose:** Manages RDS PostgreSQL connections and blacklisted channel ID operations with 3-tier caching.

**Class:** `TvEventsRds`

**Operations:**

| Method | Purpose |
|---|---|
| `_connect()` | Opens psycopg2 connection to RDS using env vars (RDS_HOST, RDS_DB, RDS_USER, RDS_PASS, RDS_PORT) |
| `_execute(query)` | Connects, executes SQL, returns list of dicts (RealDictCursor), closes connection |
| `blacklisted_channel_ids()` | 3-tier cache lookup: memory → file → RDS |
| `fetchall_channel_ids_from_blacklisted_station_channel_map()` | SELECT DISTINCT channel_id from blacklist table |
| `initialize_blacklisted_channel_ids_cache()` | Startup cache initialization (raises RuntimeError on failure) |
| `store_data_in_channel_ids_cache(ids)` | Write to file cache |
| `read_data_from_channel_ids_cache()` | Read from file cache |

**Cache Architecture:**
```
blacklisted_channel_ids()
    → check _blacklisted_channel_ids (in-memory)
        → check /tmp/.blacklisted_channel_ids_cache (file)
            → SELECT from RDS (database)
```

**OTEL Metrics:** `connect_to_db_counter`, `db_connection_error_counter`, `db_query_duration_seconds`, `read_from_db_counter`, `write_to_db_counter`, `db_query_error_counter`, `read_from_cache_counter`, `write_to_cache_counter`.

### 5. Utilities (`app/utils.py`)

**Purpose:** Core business logic: validation, security, transformation, delivery, and obfuscation.

**Functions:**

| Function | Purpose | Key Dependency |
|---|---|---|
| `verify_required_params(payload, required_params)` | Validates required fields in TvEvent payload | None |
| `timestamp_check(ts, tvid, is_ms)` | Validates timestamp is parseable | None |
| `unix_time_to_ms(ts)` | Converts seconds to milliseconds | None |
| `params_match_check(name, url, payload)` | Checks URL param matches payload param | None |
| `validate_security_hash(tvid, h_value)` | HMAC hash validation | cnlib.token_hash |
| `validate_request(url_params, payload)` | Full request validation orchestrator | All above + event_type system |
| `flatten_request_json(json, prefix, ignore_keys)` | Recursive JSON flattening with key prefixing | None |
| `get_payload_namespace(payload)` | Extracts namespace (case-insensitive key lookup) | None |
| `get_event_type_mapping(event_type)` | Looks up EventType class from registry | event_type_map |
| `is_blacklisted_channel(channelid)` | Checks if channel is in blacklist | dbhelper.TvEventsRds |
| `should_obfuscate_channel(output_json)` | Determines if obfuscation needed (iscontentblocked or blacklisted) | is_blacklisted_channel |
| `generate_output_json(request_json)` | Generates flattened output with event-type-specific transforms | event_type system |
| `push_changes_to_firehose(payload)` | Main delivery: generate output → obfuscate if needed → send to firehoses | Firehose, obfuscation |
| `send_to_valid_firehoses(data, debug)` | Parallel firehose delivery via ThreadPoolExecutor | cnlib.firehose.Firehose |

**Custom Exceptions:**

| Exception | Status Code | Use Case |
|---|---|---|
| `TvEventsDefaultException` | 400 | Base exception |
| `TvEventsCatchallException` | 400 | Generic route errors |
| `TvEventsMissingRequiredParamError` | 400 | Missing required fields |
| `TvEventsSecurityValidationError` | 400 | HMAC hash mismatch |
| `TvEventsInvalidPayloadError` | 400 | Schema/format violations |

**Module-Level State:**
- `REQUIRED_PARAMS` — tuple of required TvEvent fields
- `SALT_KEY` — T1_SALT env var
- `TVEVENTS_RDS` — singleton TvEventsRds instance
- `ZOO` — FLASK_ENV value
- `VALID_TVEVENTS_FIREHOSES` — list of active firehose names (built from env vars at import)
- `VALID_TVEVENTS_DEBUG_FIREHOSES` — list of debug firehose names

### 6. cnlib Shared Library (git submodule)

**Purpose:** Internal shared utility library providing Firehose, token hash, and logging.

**Functions consumed by tvevents:**

| Module | Function | Usage in tvevents |
|---|---|---|
| `cnlib.cnlib.firehose.Firehose` | `Firehose(name).send_records([{'Data': json.dumps(data)}])` | Sends processed events to Kinesis Data Firehose |
| `cnlib.cnlib.token_hash` | `security_hash_match(tvid, h_value, salt_key)` | Validates HMAC security hash |
| `cnlib.cnlib.log` | `getLogger(__name__)` | Logging wrapper |

**Replacement plan:**
- `firehose.Firehose` → `kafka_module.producer.send_message()` (rebuilder-evergreen-kafka-python)
- `token_hash.security_hash_match` → inline implementation in rebuilt service
- `log.getLogger` → standard Python `logging.getLogger`

## Integration Points

### Inbound

| Source | Interface | Protocol | Auth | Payload |
|---|---|---|---|---|
| SmartCast TVs | POST `/` | HTTP | HMAC (T1_SALT) | JSON: `{TvEvent: {...}, EventData: {...}}` |
| Infrastructure | GET `/status` | HTTP | None | None |

### Outbound

| Destination | Interface | Protocol | Auth | Data |
|---|---|---|---|---|
| Kinesis Firehose (evergreen) | cnlib.firehose.Firehose | AWS SDK (boto3) | AWS IAM | Flattened JSON records |
| Kinesis Firehose (legacy) | cnlib.firehose.Firehose | AWS SDK (boto3) | AWS IAM | Same data, different stream |
| Kinesis Firehose (debug variants) | cnlib.firehose.Firehose | AWS SDK (boto3) | AWS IAM | Debug copies |
| RDS PostgreSQL | psycopg2 | TCP/SQL | Password auth | SELECT channel_id queries |

### Shared State

| Resource | Type | Shared With | Access Pattern |
|---|---|---|---|
| `tvevents_blacklisted_station_channel_map` | RDS table | Other tvevents services | Read-only (SELECT DISTINCT channel_id) |
| File cache `/tmp/.blacklisted_channel_ids_cache` | Local file | Same pod only | Read/write JSON array |

## Configuration

### Environment Variables (40+)

**Always Required:**
- `ENV`, `LOG_LEVEL`, `FLASK_ENV`, `AWS_REGION`, `SERVICE_NAME`, `OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED`, `FLASK_APP`

**RDS:**
- `RDS_HOST`, `RDS_DB`, `RDS_USER`, `RDS_PASS`, `RDS_PORT`

**Firehose:**
- `SEND_EVERGREEN`, `SEND_LEGACY`, `TVEVENTS_DEBUG`
- `EVERGREEN_FIREHOSE_NAME`, `DEBUG_EVERGREEN_FIREHOSE_NAME`
- `LEGACY_FIREHOSE_NAME`, `DEBUG_LEGACY_FIREHOSE_NAME`

**Application:**
- `BLACKLIST_CHANNEL_IDS_CACHE_FILEPATH`, `T1_SALT`

**MSK/Kafka (already present but unused in app code):**
- `ACR_DATA_MSK_USERNAME`, `ACR_DATA_MSK_PASSWORD`

**OTEL (11 variables):**
- Endpoints, protocol, headers, compression, logging, correlation settings

## Helm Chart Structure

16 templates in `charts/templates/`:

| Template | Purpose |
|---|---|
| `ClusterDeployment.yaml` | Main K8s Deployment for cluster environments |
| `LocalDeployment.yaml` | Deployment variant for local/minikube |
| `tv-events-service.yaml` | K8s Service (ClusterIP, port 80 → 8000) |
| `HTTPRoute.yaml` | Gateway API HTTPRoute |
| `KongUpstreamPolicy.yaml` | Kong ingress upstream policy |
| `ScaledObject.yaml` | KEDA autoscaler (CPU-based, up to 500 pods in prod) |
| `PodDisruptionBudget.yaml` | PDB for availability during rollouts |
| `ServiceAccount.yaml` | K8s ServiceAccount |
| `ApplicationSecrets.yaml` | ExternalSecret for app secrets (RDS, T1_SALT, Firehose) |
| `O11ySecrets.yaml` | ExternalSecret for observability secrets (OTEL) |
| `LocalSecrets.yaml` | Secrets for local development |
| `SecretStore.yaml` | ExternalSecret SecretStore configuration |
| `ClusterOtelCollector.yaml` | OTEL Collector for cluster environments |
| `LocalOtelCollector.yaml` | OTEL Collector for local development |
| `PrNamespace.yaml` | Namespace for PR preview environments |
| `_helpers.tpl` | Helm template helpers |

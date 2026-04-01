"""
Example conftest.py for a rebuilt Evergreen Python service.

Copy this file to tests/conftest.py and customize:
1. Replace env var defaults with your service's values.
2. Add/remove sys.modules mocks for your external dependencies.
3. Add domain-realistic payload fixtures for your event types.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

# ─── 1. Disable OTEL before ANY app imports ───────────────────────────
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

# ─── 2. Set all required env vars (from environment-check.sh) ─────────
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("SERVICE_NAME", "my-service")  # TODO: your service name
os.environ.setdefault("TEST_CONTAINER", "true")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("OTEL_PYTHON_AUTO_INSTRUMENTATION_ENABLED", "false")
# TODO: add app-specific env vars here
# os.environ.setdefault("T1_SALT", "test-salt-value")
# os.environ.setdefault("SEND_EVERGREEN", "true")

# ─── 3. Mock external modules BEFORE app imports ──────────────────────
# Use MagicMock() — not types.ModuleType(). MagicMock returns Any for attribute
# access, so mypy allows dynamic attribute assignment. types.ModuleType triggers
# attr-defined errors unless every variable is annotated as Any.
# RDS standalone module
mock_rds = MagicMock()
mock_rds.execute_query = MagicMock(return_value=[])
sys.modules["rds_module"] = mock_rds

# Kafka standalone module
mock_kafka = MagicMock()
mock_kafka.send_message = MagicMock()
mock_kafka.health_check = MagicMock()
sys.modules["kafka_module"] = mock_kafka

# ─── 4. Mock cnlib ────────────────────────────────────────────────────
mock_cnlib = MagicMock()
mock_cnlib_cnlib = MagicMock()
mock_token_hash = MagicMock()
mock_token_hash.security_hash_match = MagicMock(return_value=True)
mock_cnlib_cnlib.token_hash = mock_token_hash

mock_cnlib_log = MagicMock()
mock_cnlib_log.Log = MagicMock()
mock_cnlib_log.Log.return_value.LOGGER = MagicMock()

mock_cnlib.cnlib = mock_cnlib_cnlib
sys.modules["cnlib"] = mock_cnlib
sys.modules["cnlib.cnlib"] = mock_cnlib_cnlib
sys.modules["cnlib.cnlib.token_hash"] = mock_token_hash
sys.modules["cnlib.log"] = mock_cnlib_log


# ─── 5. Reset fixtures ───────────────────────────────────────────────
@pytest.fixture
def mock_rds_module():
    """Provide the mocked rds_module with clean state."""
    mock_rds.execute_query.reset_mock()
    mock_rds.execute_query.return_value = []
    mock_rds.execute_query.side_effect = None
    return mock_rds


@pytest.fixture
def mock_kafka_module():
    """Provide the mocked kafka_module with clean state."""
    mock_kafka.send_message.reset_mock()
    mock_kafka.send_message.side_effect = None
    mock_kafka.health_check.reset_mock()
    mock_kafka.health_check.side_effect = None
    return mock_kafka


@pytest.fixture
def mock_security_hash():
    """Provide the mocked security_hash_match with clean state."""
    mock_token_hash.security_hash_match.reset_mock()
    mock_token_hash.security_hash_match.return_value = True
    return mock_token_hash


# ─── 6. Domain-realistic payload fixtures ─────────────────────────────
# TODO: Replace with your service's actual payload shapes.
# Use realistic values — not "test-1", "foo", or "user_abc".

@pytest.fixture
def sample_request_payload():
    """Valid request payload — customize for your service."""
    return {
        "TvEvent": {
            "tvid": "VZR2023A7F4E9B01",
            "client": "smartcast",
            "h": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            "EventType": "NATIVEAPP_TELEMETRY",
            "timestamp": "1700000000000",
        },
        "EventData": {
            "Timestamp": 1700000000000,
            "AppId": "com.vizio.smartcast.gallery",
            "Namespace": "smartcast_apps",
        },
    }


@pytest.fixture
def sample_url_params():
    """Valid URL query parameters matching the request payload."""
    return {
        "tvid": "VZR2023A7F4E9B01",
        "client": "smartcast",
        "h": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        "EventType": "NATIVEAPP_TELEMETRY",
        "timestamp": "1700000000000",
    }

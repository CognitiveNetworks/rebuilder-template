"""
Example API endpoint tests for a rebuilt Evergreen Python service.

Copy to tests/test_routes.py and customize for your service's endpoints.
Uses httpx AsyncClient for async FastAPI testing.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app import create_app


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    return create_app()


@pytest.fixture
async def client(app):
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── Health / Status ──────────────────────────────────────────────────

class TestStatusEndpoint:
    @pytest.mark.asyncio
    async def test_status_returns_ok(self, client):
        """GET /status returns 200 OK."""
        response = await client.get("/status")
        assert response.status_code == 200
        assert response.text == "OK"


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_200_when_healthy(
        self, client, mock_rds_module, mock_kafka_module
    ):
        """GET /health returns 200 with status=healthy when deps are up."""
        mock_rds_module.execute_query.return_value = [(1,)]
        mock_kafka_module.health_check.return_value = True
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_returns_503_when_dep_down(
        self, client, mock_rds_module, mock_kafka_module
    ):
        """GET /health returns 503 when a critical dependency is down."""
        mock_rds_module.execute_query.side_effect = Exception("connection refused")
        mock_kafka_module.health_check.return_value = True
        response = await client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "unhealthy"


# ─── Main Endpoint ────────────────────────────────────────────────────
# TODO: Replace with your service's main endpoint tests.

class TestMainEndpoint:
    @pytest.mark.asyncio
    async def test_valid_request_returns_ok(
        self, client, sample_request_payload, mock_security_hash, mock_kafka_module
    ):
        """POST / with valid payload returns 200."""
        response = await client.post(
            "/?tvid=VZR2023A7F4E9B01&client=smartcast"
            "&h=a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
            "&EventType=NATIVEAPP_TELEMETRY&timestamp=1700000000000",
            json=sample_request_payload,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, client):
        """POST / with invalid JSON body returns 400."""
        response = await client.post(
            "/?tvid=VZR2023A7F4E9B01",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_params_returns_400(self, client, mock_security_hash):
        """POST / with incomplete payload returns 400."""
        incomplete_payload = {"TvEvent": {"tvid": "VZR2023A7F4E9B01"}}
        response = await client.post(
            "/?tvid=VZR2023A7F4E9B01",
            json=incomplete_payload,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_security_hash_returns_400(
        self, client, sample_request_payload, mock_security_hash
    ):
        """POST / with bad HMAC hash returns 400."""
        mock_security_hash.security_hash_match.return_value = False
        response = await client.post(
            "/?tvid=VZR2023A7F4E9B01&client=smartcast"
            "&h=badhash&EventType=NATIVEAPP_TELEMETRY&timestamp=1700000000000",
            json=sample_request_payload,
        )
        assert response.status_code == 400

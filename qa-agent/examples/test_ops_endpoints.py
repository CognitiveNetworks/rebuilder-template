"""
Example /ops/* SRE contract tests for a rebuilt Evergreen Python service.

Copy to tests/test_ops_endpoints.py and customize.
Every /ops/* endpoint must return the required fields per the SRE agent contract.
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


# ─── Diagnostic Endpoints (GET) ──────────────────────────────────────


class TestOpsStatus:
    @pytest.mark.asyncio
    async def test_returns_verdict(self, client, mock_rds_module, mock_kafka_module):
        """GET /ops/status returns composite health verdict."""
        mock_rds_module.execute_query.return_value = [(1,)]
        mock_kafka_module.health_check.return_value = True
        response = await client.get("/ops/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "uptime_seconds" in data
        assert "request_count" in data

    @pytest.mark.asyncio
    async def test_degraded_when_deps_fail(
        self, client, mock_rds_module, mock_kafka_module
    ):
        """GET /ops/status reports degraded/unhealthy when deps are down."""
        mock_rds_module.execute_query.side_effect = Exception("down")
        mock_kafka_module.health_check.side_effect = Exception("down")
        response = await client.get("/ops/status")
        data = response.json()
        assert data["status"] in ("degraded", "unhealthy")


class TestOpsHealth:
    @pytest.mark.asyncio
    async def test_returns_checks(self, client, mock_rds_module, mock_kafka_module):
        """GET /ops/health returns per-dependency check results."""
        mock_rds_module.execute_query.return_value = [(1,)]
        mock_kafka_module.health_check.return_value = True
        response = await client.get("/ops/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "checks" in data


class TestOpsMetrics:
    @pytest.mark.asyncio
    async def test_returns_golden_signals(self, client):
        """GET /ops/metrics returns Golden Signals and RED metrics."""
        response = await client.get("/ops/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "golden_signals" in data
        gs = data["golden_signals"]
        assert "latency" in gs
        assert "traffic" in gs
        assert "errors" in gs
        assert "saturation" in gs
        assert "red" in data
        assert "uptime_seconds" in data


class TestOpsConfig:
    @pytest.mark.asyncio
    async def test_returns_config(self, client):
        """GET /ops/config returns non-sensitive runtime configuration."""
        response = await client.get("/ops/config")
        assert response.status_code == 200
        data = response.json()
        assert "service_name" in data




class TestOpsErrors:
    @pytest.mark.asyncio
    async def test_returns_error_summary(self, client):
        """GET /ops/errors returns error totals and recent list."""
        response = await client.get("/ops/errors")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "recent" in data


class TestOpsCache:
    @pytest.mark.asyncio
    async def test_returns_cache_stats(self, client):
        """GET /ops/cache returns cache statistics."""
        response = await client.get("/ops/cache")
        assert response.status_code == 200
        data = response.json()
        assert "entry_count" in data




# ─── Remediation Endpoints (POST) ────────────────────────────────────




class TestOpsLogLevel:
    @pytest.mark.asyncio
    async def test_set_valid_level(self, client):
        """POST /ops/loglevel with valid level returns new level."""
        response = await client.post("/ops/loglevel", json={"level": "DEBUG"})
        assert response.status_code == 200
        assert response.json()["level"] == "DEBUG"

    @pytest.mark.asyncio
    async def test_set_invalid_level_returns_400(self, client):
        """POST /ops/loglevel with invalid level returns 400."""
        response = await client.post("/ops/loglevel", json={"level": "TRACE"})
        assert response.status_code == 400


class TestOpsCacheFlush:
    @pytest.mark.asyncio
    async def test_flush_success(self, client, mock_rds_module):
        """POST /ops/cache/flush refreshes cache and returns ok."""
        mock_rds_module.execute_query.return_value = [{"channel_id": "ch1"}]
        response = await client.post("/ops/cache/flush")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_flush_failure_returns_500(self, client, mock_rds_module):
        """POST /ops/cache/flush returns 500 when source is unavailable."""
        mock_rds_module.execute_query.side_effect = Exception("db error")
        response = await client.post("/ops/cache/flush")
        assert response.status_code == 500


class TestOpsCacheRefresh:
    @pytest.mark.asyncio
    async def test_refresh_success(self, client, mock_rds_module):
        """POST /ops/cache/refresh returns result."""
        mock_rds_module.execute_query.return_value = [
            {"channel_id": "ch1"},
            {"channel_id": "ch2"},
        ]
        response = await client.post("/ops/cache/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestOpsCircuits:
    @pytest.mark.asyncio
    async def test_returns_circuit_state(self, client):
        """POST /ops/circuits returns per-dependency circuit state."""
        response = await client.post("/ops/circuits")
        assert response.status_code == 200
        data = response.json()
        assert "circuits" in data


# ─── Drain Mode Integration ──────────────────────────────────────────



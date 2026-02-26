"""Tests for tool definitions and executor."""

import json

import pytest

from models import ScalingConfig, ScalingMode
from tools import TOOL_DEFINITIONS, ToolExecutor


class TestToolDefinitions:
    """Tests for tool schema completeness."""

    def test_all_tools_have_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool, f"Tool missing name: {tool}"
            assert "description" in tool, f"Tool {tool['name']} missing description"
            assert "input_schema" in tool, f"Tool {tool['name']} missing input_schema"

    def test_all_tools_have_required_properties(self):
        for tool in TOOL_DEFINITIONS:
            schema = tool["input_schema"]
            assert schema.get("type") == "object", f"Tool {tool['name']} schema must be object"
            assert "properties" in schema, f"Tool {tool['name']} missing properties"
            assert "required" in schema, f"Tool {tool['name']} missing required list"

    def test_expected_tools_exist(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        expected = {
            "call_ops_endpoint",
            "query_cloud_logs",
            "query_cloud_metrics",
            "escalate_pagerduty",
            "acknowledge_alert",
            "write_incident_report",
            "scale_service",
        }
        assert expected == names


class TestToolExecutor:
    """Tests for ToolExecutor.execute."""

    @pytest.fixture()
    def executor(self, tmp_path):
        return ToolExecutor(
            services={"api": "https://api.example.com", "worker": "https://worker.example.com"},
            ops_auth_token="test-token",
            pagerduty_api_token="pd-token",
            incidents_dir=str(tmp_path),
            trace_id="test-trace-123",
        )

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, executor):
        result = await executor.execute("nonexistent_tool", {})
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Unknown tool" in parsed["error"]

    @pytest.mark.asyncio
    async def test_call_ops_endpoint_validates_service_name(self, executor):
        result = await executor.execute(
            "call_ops_endpoint",
            {"service_name": "", "endpoint": "/ops/status", "method": "GET"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_call_ops_endpoint_rejects_non_ops_path(self, executor):
        result = await executor.execute(
            "call_ops_endpoint",
            {"service_name": "api", "endpoint": "/admin/delete", "method": "GET"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "/ops/" in parsed["error"]

    @pytest.mark.asyncio
    async def test_call_ops_endpoint_rejects_invalid_method(self, executor):
        result = await executor.execute(
            "call_ops_endpoint",
            {"service_name": "api", "endpoint": "/ops/status", "method": "DELETE"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_call_ops_endpoint_rejects_unknown_service(self, executor):
        result = await executor.execute(
            "call_ops_endpoint",
            {"service_name": "unknown", "endpoint": "/ops/status", "method": "GET"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Unknown service" in parsed["error"]

    @pytest.mark.asyncio
    async def test_write_incident_report_creates_file(self, executor, tmp_path):
        result = await executor.execute(
            "write_incident_report",
            {"filename": "2025-01-15-test-incident.md", "content": "# Incident Report\n\nTest."},
        )
        parsed = json.loads(result)
        assert parsed["status"] == "written"
        assert (tmp_path / "2025-01-15-test-incident.md").exists()

    @pytest.mark.asyncio
    async def test_write_incident_report_rejects_path_traversal(self, executor):
        result = await executor.execute(
            "write_incident_report",
            {"filename": "../../../etc/passwd", "content": "malicious"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "path traversal" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_write_incident_report_rejects_subdirectory(self, executor):
        result = await executor.execute(
            "write_incident_report",
            {"filename": "subdir/report.md", "content": "content"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_write_incident_report_requires_filename(self, executor):
        result = await executor.execute(
            "write_incident_report",
            {"filename": "", "content": "content"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_escalate_requires_incident_id(self, executor):
        result = await executor.execute(
            "escalate_pagerduty",
            {"incident_id": "", "escalation_message": "test"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_acknowledge_requires_incident_id(self, executor):
        result = await executor.execute(
            "acknowledge_alert",
            {"incident_id": "", "resolution_note": "test"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_cloud_logs_returns_not_implemented(self, executor):
        result = await executor.execute(
            "query_cloud_logs",
            {"service_name": "api", "query": "severity=ERROR"},
        )
        parsed = json.loads(result)
        assert "not yet implemented" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_cloud_metrics_returns_not_implemented(self, executor):
        result = await executor.execute(
            "query_cloud_metrics",
            {"resource": "cloud-sql/main", "metric": "cpu_utilization"},
        )
        parsed = json.loads(result)
        assert "not yet implemented" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_base_headers_includes_trace_id(self, executor):
        headers = executor._base_headers()
        assert headers["X-Trace-Id"] == "test-trace-123"

    @pytest.mark.asyncio
    async def test_base_headers_empty_without_trace_id(self, tmp_path):
        executor = ToolExecutor(
            services={},
            ops_auth_token="",
            pagerduty_api_token="",
            incidents_dir=str(tmp_path),
        )
        headers = executor._base_headers()
        assert "X-Trace-Id" not in headers

    @pytest.mark.asyncio
    async def test_close_cleans_up_client(self, executor):
        await executor.close()
        assert executor.http_client.is_closed


class TestScaleService:
    """Tests for the scale_service tool."""

    @pytest.fixture()
    def scaling_config(self):
        return {
            "api": ScalingConfig(
                service_name="api",
                min_instances=2,
                max_instances=10,
                mode=ScalingMode.APPLICATION,
            ),
            "worker": ScalingConfig(
                service_name="worker",
                min_instances=1,
                max_instances=5,
                mode=ScalingMode.CLOUD_NATIVE,
            ),
        }

    @pytest.fixture()
    def executor_with_scaling(self, tmp_path, scaling_config):
        return ToolExecutor(
            services={"api": "https://api.example.com", "worker": "https://worker.example.com"},
            ops_auth_token="test-token",
            pagerduty_api_token="pd-token",
            incidents_dir=str(tmp_path),
            trace_id="test-trace-123",
            scaling_config=scaling_config,
        )

    @pytest.mark.asyncio
    async def test_scale_rejects_service_not_in_scaling_config(self, tmp_path):
        executor = ToolExecutor(
            services={"api": "https://api.example.com"},
            ops_auth_token="test-token",
            pagerduty_api_token="pd-token",
            incidents_dir=str(tmp_path),
            trace_id="test-trace-123",
            scaling_config={},
        )
        result = await executor.execute(
            "scale_service",
            {"service_name": "api", "target_instances": 5, "reason": "traffic spike"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "scaling limits" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_scale_rejects_below_min(self, executor_with_scaling):
        result = await executor_with_scaling.execute(
            "scale_service",
            {"service_name": "api", "target_instances": 1, "reason": "scale down"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "below minimum" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_scale_rejects_above_max(self, executor_with_scaling):
        result = await executor_with_scaling.execute(
            "scale_service",
            {"service_name": "api", "target_instances": 15, "reason": "scale up"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "exceeds maximum" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_scale_rejects_missing_fields(self, executor_with_scaling):
        result = await executor_with_scaling.execute(
            "scale_service",
            {"service_name": "", "target_instances": 5, "reason": "test"},
        )
        parsed = json.loads(result)
        assert "error" in parsed

    @pytest.mark.asyncio
    async def test_scale_cloud_native_returns_not_implemented(self, executor_with_scaling):
        result = await executor_with_scaling.execute(
            "scale_service",
            {"service_name": "worker", "target_instances": 3, "reason": "queue backlog"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "not yet implemented" in parsed["error"].lower()

    @pytest.mark.asyncio
    async def test_scale_application_rejects_unknown_service_in_registry(self, tmp_path):
        """Service in scaling config but not in service registry."""
        scaling_config = {
            "ghost": ScalingConfig(
                service_name="ghost",
                min_instances=1,
                max_instances=5,
                mode=ScalingMode.APPLICATION,
            ),
        }
        executor = ToolExecutor(
            services={},
            ops_auth_token="test-token",
            pagerduty_api_token="pd-token",
            incidents_dir=str(tmp_path),
            trace_id="test-trace-123",
            scaling_config=scaling_config,
        )
        result = await executor.execute(
            "scale_service",
            {"service_name": "ghost", "target_instances": 3, "reason": "test"},
        )
        parsed = json.loads(result)
        assert "error" in parsed
        assert "not in service registry" in parsed["error"].lower()

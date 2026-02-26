"""Tests for configuration loading and validation."""

import os
from unittest.mock import patch

import pytest

from config import Config, _require


class TestRequire:
    """Tests for the _require helper."""

    def test_returns_value_when_set(self):
        with patch.dict(os.environ, {"TEST_VAR": "value"}):
            assert _require("TEST_VAR") == "value"

    def test_raises_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TEST_VAR is not set"):
                _require("TEST_VAR")

    def test_raises_when_empty(self):
        with patch.dict(os.environ, {"TEST_VAR": ""}):
            with pytest.raises(ValueError, match="TEST_VAR is not set"):
                _require("TEST_VAR")


class TestConfig:
    """Tests for Config initialization and validation."""

    REQUIRED_ENV = {
        "LLM_API_KEY": "ghp-test",
        "PAGERDUTY_API_TOKEN": "pd-test",
        "OPS_AUTH_TOKEN": "ops-test",
        "SERVICE_REGISTRY": "api|https://api.example.com|true",
    }

    def test_loads_required_config(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.llm_api_key == "ghp-test"
            assert cfg.pagerduty_api_token == "pd-test"
            assert cfg.ops_auth_token == "ops-test"

    def test_loads_service_registry(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert len(cfg.services) == 1
            assert cfg.services[0].name == "api"
            assert cfg.services[0].base_url == "https://api.example.com"
            assert cfg.services[0].critical is True

    def test_loads_multiple_services(self):
        env = {
            **self.REQUIRED_ENV,
            "SERVICE_REGISTRY": "api|https://api.example.com|true,worker|https://worker.example.com|false",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert len(cfg.services) == 2
            assert cfg.services[1].name == "worker"
            assert cfg.services[1].critical is False

    def test_defaults_critical_to_true(self):
        env = {
            **self.REQUIRED_ENV,
            "SERVICE_REGISTRY": "api|https://api.example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert cfg.services[0].critical is True

    def test_rejects_invalid_url_scheme(self):
        env = {
            **self.REQUIRED_ENV,
            "SERVICE_REGISTRY": "api|ftp://api.example.com|true",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Invalid URL scheme"):
                Config()

    def test_rejects_malformed_registry_entry(self):
        env = {
            **self.REQUIRED_ENV,
            "SERVICE_REGISTRY": "just-a-name",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Invalid SERVICE_REGISTRY entry"):
                Config()

    def test_uses_default_llm_model(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.llm_model == "gpt-4o"

    def test_uses_default_llm_api_base_url(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.llm_api_base_url == "https://models.inference.ai.azure.com"

    def test_overrides_llm_model(self):
        env = {**self.REQUIRED_ENV, "LLM_MODEL": "gpt-4o-mini"}
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert cfg.llm_model == "gpt-4o-mini"

    def test_uses_default_prompt_path(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.sre_prompt_path == "/app/WINDSURF_SRE.md"

    def test_overrides_prompt_path(self):
        env = {**self.REQUIRED_ENV, "SRE_PROMPT_PATH": "/custom/path.md"}
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert cfg.sre_prompt_path == "/custom/path.md"

    def test_loads_optional_webhook_secret(self):
        env = {**self.REQUIRED_ENV, "PAGERDUTY_WEBHOOK_SECRET": "secret123"}
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert cfg.pagerduty_webhook_secret == "secret123"

    def test_raises_when_registry_empty(self):
        env = {**self.REQUIRED_ENV, "SERVICE_REGISTRY": ""}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="SERVICE_REGISTRY"):
                Config()

    def test_raises_when_registry_missing(self):
        env = {k: v for k, v in self.REQUIRED_ENV.items() if k != "SERVICE_REGISTRY"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="SERVICE_REGISTRY"):
                Config()

    def test_loads_scaling_limits(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|2|10|application,worker|1|5|cloud_native",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert len(cfg.scaling_limits) == 2
            assert cfg.scaling_limits["api"].min_instances == 2
            assert cfg.scaling_limits["api"].max_instances == 10
            assert cfg.scaling_limits["api"].mode == "application"
            assert cfg.scaling_limits["worker"].min_instances == 1
            assert cfg.scaling_limits["worker"].max_instances == 5
            assert cfg.scaling_limits["worker"].mode == "cloud_native"

    def test_empty_scaling_limits_returns_empty_dict(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.scaling_limits == {}

    def test_rejects_scaling_limits_max_below_min(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|5|2|application",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="max.*must be >= min"):
                Config()

    def test_rejects_scaling_limits_invalid_mode(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|2|10|manual",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Invalid scaling mode"):
                Config()

    def test_rejects_scaling_limits_malformed_entry(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|2|10",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Invalid SCALING_LIMITS entry"):
                Config()

    def test_rejects_scaling_limits_non_integer(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|two|10|application",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="min and max must be integers"):
                Config()

    def test_rejects_scaling_limits_min_below_one(self):
        env = {
            **self.REQUIRED_ENV,
            "SCALING_LIMITS": "api|0|10|application",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="Must be >= 1"):
                Config()

    def test_loads_intake_defaults(self):
        with patch.dict(os.environ, self.REQUIRED_ENV, clear=True):
            cfg = Config()
            assert cfg.max_concurrent_alerts == 3
            assert cfg.alert_queue_ttl_seconds == 600

    def test_loads_intake_overrides(self):
        env = {
            **self.REQUIRED_ENV,
            "MAX_CONCURRENT_ALERTS": "5",
            "ALERT_QUEUE_TTL_SECONDS": "300",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = Config()
            assert cfg.max_concurrent_alerts == 5
            assert cfg.alert_queue_ttl_seconds == 300

    def test_rejects_max_concurrent_below_one(self):
        env = {**self.REQUIRED_ENV, "MAX_CONCURRENT_ALERTS": "0"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="MAX_CONCURRENT_ALERTS must be >= 1"):
                Config()

    def test_rejects_negative_queue_ttl(self):
        env = {**self.REQUIRED_ENV, "ALERT_QUEUE_TTL_SECONDS": "-1"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValueError, match="ALERT_QUEUE_TTL_SECONDS must be >= 0"):
                Config()

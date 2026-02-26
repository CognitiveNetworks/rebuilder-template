"""Configuration loaded from environment variables.

All secrets are loaded from environment variables, which should be
injected from your cloud provider's secrets manager at deploy time.
Never hardcode secrets in this file.
"""

import logging
import os
from urllib.parse import urlparse

from models import ScalingConfig, ScalingMode, ServiceEndpoint

logger = logging.getLogger(__name__)


class Config:
    """Runtime configuration for the SRE agent."""

    def __init__(self) -> None:
        # LLM provider (OpenAI-compatible — GitHub Models, OpenAI, Azure, Vertex AI)
        self.llm_api_base_url: str = os.environ.get(
            "LLM_API_BASE_URL", "https://models.inference.ai.azure.com"
        )
        self.llm_model: str = os.environ.get(
            "LLM_MODEL", "gpt-4o"
        )

        # Two-phase model escalation: start with fast model, upgrade after N turns
        self.llm_model_escalation: str = os.environ.get(
            "LLM_MODEL_ESCALATION", ""
        )
        self.llm_escalation_turn: int = int(
            os.environ.get("LLM_ESCALATION_TURN", "5")
        )

        # Detect Vertex AI from base URL — uses ADC instead of an API key
        self.vertex_ai: bool = "aiplatform.googleapis.com" in self.llm_api_base_url

        if self.vertex_ai:
            # On Cloud Run, ADC is provided by the service account automatically.
            # LLM_API_KEY is ignored — we fetch a fresh token per agent run.
            self.llm_api_key: str = self._get_vertex_ai_token()
            logger.info(
                "Vertex AI mode: model=%s base_url=%s",
                self.llm_model,
                self.llm_api_base_url,
            )
        else:
            self.llm_api_key = _require("LLM_API_KEY")

        # PagerDuty
        self.pagerduty_api_token: str = _require("PAGERDUTY_API_TOKEN")
        self.pagerduty_escalation_policy_id: str = os.environ.get(
            "PAGERDUTY_ESCALATION_POLICY_ID", ""
        )

        # PagerDuty Events API v2 routing key — used to CREATE new incidents
        # when the agent cannot resolve a GCP-sourced alert
        self.pagerduty_routing_key: str = os.environ.get(
            "PAGERDUTY_ROUTING_KEY", ""
        )

        # Webhook verification
        self.pagerduty_webhook_secret: str = os.environ.get(
            "PAGERDUTY_WEBHOOK_SECRET", ""
        )

        # SRE agent instructions
        self.sre_prompt_path: str = os.environ.get(
            "SRE_PROMPT_PATH", "/app/WINDSURF_SRE.md"
        )

        # Incident reports
        self.incidents_dir: str = os.environ.get("INCIDENTS_DIR", "/app/incidents")

        # Service registry — loaded from environment.
        # Format: SERVICE_REGISTRY=name1|url1|critical,name2|url2|critical
        self.services: list[ServiceEndpoint] = self._load_services()

        # Scaling limits — loaded from environment.
        # Format: SCALING_LIMITS=name1|min|max|mode,name2|min|max|mode
        self.scaling_limits: dict[str, ScalingConfig] = self._load_scaling_limits()

        # Alert intake pipeline
        self.max_concurrent_alerts: int = int(
            os.environ.get("MAX_CONCURRENT_ALERTS", "3")
        )
        self.alert_queue_ttl_seconds: int = int(
            os.environ.get("ALERT_QUEUE_TTL_SECONDS", "600")
        )
        if self.max_concurrent_alerts < 1:
            raise ValueError(
                f"MAX_CONCURRENT_ALERTS must be >= 1, got {self.max_concurrent_alerts}"
            )
        if self.alert_queue_ttl_seconds < 0:
            raise ValueError(
                f"ALERT_QUEUE_TTL_SECONDS must be >= 0, got {self.alert_queue_ttl_seconds}"
            )

        # Token budget controls
        self.max_tokens_per_incident: int = int(
            os.environ.get("MAX_TOKENS_PER_INCIDENT", "100000")
        )
        self.max_tokens_per_hour: int = int(
            os.environ.get("MAX_TOKENS_PER_HOUR", "0")  # 0 = unlimited
        )
        if self.max_tokens_per_incident < 0:
            raise ValueError(
                f"MAX_TOKENS_PER_INCIDENT must be >= 0, got {self.max_tokens_per_incident}"
            )
        if self.max_tokens_per_hour < 0:
            raise ValueError(
                f"MAX_TOKENS_PER_HOUR must be >= 0, got {self.max_tokens_per_hour}"
            )

        # SMTP — for emailing incident reports (optional)
        self.smtp_host: str = os.environ.get("SMTP_HOST", "")
        self.smtp_port: str = os.environ.get("SMTP_PORT", "587")
        self.smtp_username: str = os.environ.get("SMTP_USERNAME", "")
        self.smtp_password: str = os.environ.get("SMTP_PASSWORD", "")
        self.smtp_from: str = os.environ.get("SMTP_FROM", self.smtp_username)
        self.smtp_to: str = os.environ.get("SMTP_TO", "")

        # Agent auth for /ops/* endpoints on monitored services
        self.ops_auth_token: str = _require("OPS_AUTH_TOKEN")

    def _load_services(self) -> list[ServiceEndpoint]:
        """Parse and validate service registry from SERVICE_REGISTRY env var."""
        raw = _require("SERVICE_REGISTRY")
        if not raw:
            return []

        services = []
        for entry in raw.split(","):
            parts = entry.strip().split("|")
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid SERVICE_REGISTRY entry: '{entry.strip()}'. "
                    f"Expected format: name|url|critical"
                )
            name = parts[0].strip()
            url = parts[1].strip()
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Invalid URL scheme for service '{name}': {url}. "
                    f"Must be http or https."
                )
            services.append(
                ServiceEndpoint(
                    name=name,
                    base_url=url,
                    critical=parts[2].strip().lower() == "true"
                    if len(parts) > 2
                    else True,
                )
            )
        return services

    def _load_scaling_limits(self) -> dict[str, ScalingConfig]:
        """Parse and validate scaling limits from SCALING_LIMITS env var."""
        raw = os.environ.get("SCALING_LIMITS", "")
        if not raw:
            return {}

        limits: dict[str, ScalingConfig] = {}
        for entry in raw.split(","):
            parts = entry.strip().split("|")
            if len(parts) != 4:
                raise ValueError(
                    f"Invalid SCALING_LIMITS entry: '{entry.strip()}'. "
                    f"Expected format: name|min|max|mode"
                )
            name = parts[0].strip()
            try:
                min_inst = int(parts[1].strip())
                max_inst = int(parts[2].strip())
            except ValueError as exc:
                raise ValueError(
                    f"Invalid SCALING_LIMITS entry for '{name}': "
                    f"min and max must be integers"
                ) from exc
            mode_str = parts[3].strip()
            if mode_str not in ("application", "cloud_native"):
                raise ValueError(
                    f"Invalid scaling mode for '{name}': '{mode_str}'. "
                    f"Must be 'application' or 'cloud_native'."
                )
            if min_inst < 1:
                raise ValueError(
                    f"Invalid min_instances for '{name}': {min_inst}. Must be >= 1."
                )
            if max_inst < min_inst:
                raise ValueError(
                    f"Invalid scaling limits for '{name}': "
                    f"max ({max_inst}) must be >= min ({min_inst})."
                )
            limits[name] = ScalingConfig(
                service_name=name,
                min_instances=min_inst,
                max_instances=max_inst,
                mode=ScalingMode(mode_str),
            )
        return limits

    def _get_vertex_ai_token(self) -> str:
        """Get a fresh access token via Application Default Credentials.

        On Cloud Run, the service account's token is provided by the
        metadata server. Locally, uses gcloud ADC. Tokens expire after
        ~1 hour — call refresh_llm_token() before each agent run.
        """
        try:
            import google.auth
            import google.auth.transport.requests

            credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials.refresh(google.auth.transport.requests.Request())
            return credentials.token
        except Exception as exc:
            raise ValueError(
                "Vertex AI mode requires Application Default Credentials. "
                "On Cloud Run this is automatic. Locally, run: "
                "gcloud auth application-default login"
            ) from exc

    def refresh_llm_token(self) -> str:
        """Refresh the LLM API token if using Vertex AI (ADC tokens expire).

        Call this before each agent run. For non-Vertex providers, this
        is a no-op and returns the existing key.
        """
        if self.vertex_ai:
            self.llm_api_key = self._get_vertex_ai_token()
        return self.llm_api_key

    def load_system_prompt(self) -> str:
        """Load the WINDSURF_SRE.md system prompt from disk."""
        with open(self.sre_prompt_path) as f:
            return f.read()


def _require(var: str) -> str:
    """Require an environment variable to be set and non-empty."""
    value = os.environ.get(var, "")
    if not value:
        raise ValueError(
            f"Required environment variable {var} is not set. "
            f"Set it in your deployment configuration or secrets manager."
        )
    return value

"""Agentic diagnostic loop for the SRE agent.

Uses the OpenAI-compatible chat completions API (works with GitHub Models,
OpenAI, Azure OpenAI, Vertex AI, or any compatible provider). The agent
loads WINDSURF_SRE.md as the system prompt, sends the alert as the first
user message, and loops: the LLM responds with function calls (tool_use),
the service executes them via ToolExecutor, and feeds the results back
until the LLM produces a final text response (resolved or escalated).

The LLM provider is configured via environment variables:
  LLM_API_BASE_URL  — API endpoint (default: GitHub Models)
  LLM_API_KEY       — API key or token (not needed for Vertex AI — uses ADC)
  LLM_MODEL         — Model ID (default: gpt-4o)
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from config import Config
from models import PagerDutyAlert
from telemetry import get_tracer
from tools import TOOL_DEFINITIONS, ToolExecutor

logger = logging.getLogger(__name__)

# Safety limits
MAX_TURNS = 20
MAX_DURATION_SECONDS = 300


# Pricing per 1M tokens (USD). Used for cost estimation only — not billing.
# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing
# Update these when pricing changes.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "google/gemini-2.0-flash": (0.10, 0.40),
    "google/gemini-2.5-flash": (0.15, 0.60),
    "google/gemini-2.5-pro": (1.25, 10.00),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate LLM cost in USD from token usage and model pricing."""
    pricing = MODEL_PRICING.get(model, (0.0, 0.0))
    return (input_tokens * pricing[0] + output_tokens * pricing[1]) / 1_000_000


@dataclass
class AgentResult:
    """Result of a single agent run."""

    summary: str = ""
    turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    models_used: list[str] = field(default_factory=list)
    tool_calls_made: list[str] = field(default_factory=list)


def _convert_tools_to_openai_format() -> list[dict[str, Any]]:
    """Convert tool_use schema definitions to OpenAI function calling format."""
    functions = []
    for tool in TOOL_DEFINITIONS:
        functions.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        })
    return functions


async def run_agent(
    alert: PagerDutyAlert,
    config: Config,
    trace_id: str = "",
) -> AgentResult:
    """Run the agentic diagnostic loop for a single alert.

    Returns an AgentResult with the summary, turn count, and token usage.
    Raises on unrecoverable errors (caller handles logging and state).
    """
    tracer = get_tracer()
    result = AgentResult()
    start_time = time.time()

    # Refresh token for Vertex AI (ADC tokens expire after ~1 hour).
    # For other providers this is a no-op.
    config.refresh_llm_token()

    # Build the OpenAI client pointing at the configured provider
    client = AsyncOpenAI(
        api_key=config.llm_api_key,
        base_url=config.llm_api_base_url,
    )

    # Load system prompt
    system_prompt = config.load_system_prompt()

    # Build the initial user message from the alert
    user_message = _format_alert_message(alert)

    # Conversation history
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # OpenAI function definitions
    tools = _convert_tools_to_openai_format()

    # Initialize tool executor
    services = {svc.name: svc.base_url for svc in config.services}
    executor = ToolExecutor(
        services=services,
        ops_auth_token=config.ops_auth_token,
        pagerduty_api_token=config.pagerduty_api_token,
        incidents_dir=config.incidents_dir,
        trace_id=trace_id,
        scaling_config=config.scaling_limits,
        smtp_config={
            "host": config.smtp_host,
            "port": config.smtp_port,
            "username": config.smtp_username,
            "password": config.smtp_password,
            "from": config.smtp_from,
            "to": config.smtp_to,
        },
        pagerduty_routing_key=config.pagerduty_routing_key,
    )

    # Two-phase model escalation: start with fast model, upgrade after N turns
    current_model = config.llm_model
    escalated_model = False

    logger.info(
        "Agent starting: incident_id=%s service=%s model=%s escalation=%s@turn%d trace_id=%s",
        alert.incident_id,
        alert.service_name,
        current_model,
        config.llm_model_escalation or "none",
        config.llm_escalation_turn,
        trace_id,
    )

    try:
        for turn in range(MAX_TURNS):
            result.turns = turn + 1

            # Model escalation: switch to stronger model after N turns
            if (
                not escalated_model
                and config.llm_model_escalation
                and turn >= config.llm_escalation_turn
            ):
                current_model = config.llm_model_escalation
                escalated_model = True
                logger.info(
                    "Model escalated: %s -> %s at turn %d, incident_id=%s trace_id=%s",
                    config.llm_model,
                    current_model,
                    turn + 1,
                    alert.incident_id,
                    trace_id,
                )

            # Safety: check duration
            elapsed = time.time() - start_time
            if elapsed > MAX_DURATION_SECONDS:
                logger.warning(
                    "Agent duration limit reached: %.0fs > %ds, escalating: "
                    "incident_id=%s trace_id=%s",
                    elapsed,
                    MAX_DURATION_SECONDS,
                    alert.incident_id,
                    trace_id,
                )
                result.summary = (
                    f"Duration limit exceeded ({elapsed:.0f}s). "
                    f"Escalating after {result.turns} turns."
                )
                break

            # Safety: check per-incident token budget
            tokens_used = result.input_tokens + result.output_tokens
            if config.max_tokens_per_incident > 0 and tokens_used >= config.max_tokens_per_incident:
                logger.warning(
                    "Per-incident token budget exceeded: %d >= %d, escalating: "
                    "incident_id=%s trace_id=%s",
                    tokens_used,
                    config.max_tokens_per_incident,
                    alert.incident_id,
                    trace_id,
                )
                result.summary = (
                    f"Token budget exceeded ({tokens_used:,}/{config.max_tokens_per_incident:,}). "
                    f"Escalating after {result.turns} turns."
                )
                break

            # Call the LLM
            with tracer.start_as_current_span(
                "sre_agent.agent.turn",
                attributes={
                    "agent.turn": turn + 1,
                    "agent.model": current_model,
                    "agent.model_escalated": escalated_model,
                    "incident.id": alert.incident_id,
                },
            ):
                response = await client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096,
                )

            # Track token usage and cost
            if response.usage:
                turn_in = response.usage.prompt_tokens
                turn_out = response.usage.completion_tokens
                result.input_tokens += turn_in
                result.output_tokens += turn_out
                result.estimated_cost_usd += estimate_cost(
                    current_model, turn_in, turn_out
                )
                if current_model not in result.models_used:
                    result.models_used.append(current_model)

            choice = response.choices[0]
            message = choice.message

            # If the model produced tool calls, execute them
            if message.tool_calls:
                # Add the assistant message (with tool calls) to history
                messages.append(message.model_dump())

                for tool_call in message.tool_calls:
                    fn = tool_call.function
                    tool_name = fn.name
                    try:
                        tool_input = json.loads(fn.arguments)
                    except json.JSONDecodeError:
                        tool_input = {}

                    result.tool_calls_made.append(tool_name)

                    # Execute the tool
                    with tracer.start_as_current_span(
                        "sre_agent.tool.execute",
                        attributes={
                            "tool.name": tool_name,
                            "incident.id": alert.incident_id,
                        },
                    ):
                        tool_result = await executor.execute(tool_name, tool_input)

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                    logger.info(
                        "Tool executed: tool=%s turn=%d incident_id=%s trace_id=%s",
                        tool_name,
                        turn + 1,
                        alert.incident_id,
                        trace_id,
                    )

            # If the model produced a final text response (no tool calls), we're done
            elif message.content:
                result.summary = message.content
                logger.info(
                    "Agent finished: turns=%d incident_id=%s trace_id=%s",
                    result.turns,
                    alert.incident_id,
                    trace_id,
                )
                break

            # Edge case: no tool calls and no content
            else:
                result.summary = "Agent produced empty response."
                logger.warning(
                    "Agent empty response: turn=%d incident_id=%s trace_id=%s",
                    turn + 1,
                    alert.incident_id,
                    trace_id,
                )
                break
        else:
            # Exhausted MAX_TURNS
            result.summary = f"Max turns reached ({MAX_TURNS}). Escalating."
            logger.warning(
                "Agent max turns: incident_id=%s trace_id=%s",
                alert.incident_id,
                trace_id,
            )

    finally:
        await executor.http_client.aclose()

    return result


def _format_alert_message(alert: PagerDutyAlert) -> str:
    """Format a PagerDuty alert as the initial user message for the agent."""
    parts = [
        f"## PagerDuty Alert — {alert.severity.value.upper()}",
        "",
        f"**Incident ID:** {alert.incident_id}",
        f"**Service:** {alert.service_name}",
        f"**Severity:** {alert.severity.value}",
        f"**Description:** {alert.description}",
    ]

    if alert.priority:
        parts.append(f"**Priority:** {alert.priority.value}")
    if alert.dedup_key:
        parts.append(f"**Dedup Key:** {alert.dedup_key}")
    if alert.runbook_url:
        parts.append(f"**Runbook:** {alert.runbook_url}")
    if alert.timestamp:
        parts.append(f"**Triggered At:** {alert.timestamp.isoformat()}")
    if alert.details:
        parts.append("")
        parts.append("**Additional Details:**")
        parts.append(f"```json\n{json.dumps(alert.details, indent=2)}\n```")

    parts.append("")
    parts.append(
        "Diagnose this alert following the workflow in your system prompt. "
        "Start by checking /ops/status on the affected service."
    )

    return "\n".join(parts)

"""Runtime state tracking for /ops/* endpoints.

Tracks Golden Signals, RED metrics, active incidents, and recent errors
so the SRE agent service can report its own health via /ops/* endpoints.
"""

import time
from collections import deque
from dataclasses import dataclass, field


@dataclass
class RuntimeState:
    """Tracks runtime metrics for the SRE agent service."""

    start_time: float = field(default_factory=time.time)

    # Webhook counters
    webhooks_received: int = 0
    webhooks_processed: int = 0
    webhooks_ignored: int = 0
    webhooks_failed: int = 0

    # Agent run counters
    agent_runs_completed: int = 0
    agent_runs_failed: int = 0

    # Token usage counters
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_estimated_cost_usd: float = 0.0

    # Per-run token usage (bounded, for percentile computation)
    run_token_usage: deque = field(default_factory=lambda: deque(maxlen=500))

    # Rolling hourly token tracking: (timestamp, token_count) tuples
    hourly_token_log: deque = field(default_factory=lambda: deque(maxlen=10000))

    # Alert intake counters
    alerts_deduplicated: int = 0
    alerts_queued: int = 0
    alerts_expired: int = 0

    # Active incidents: incident_id -> start_time
    active_incidents: dict[str, float] = field(default_factory=dict)

    # Recent errors (bounded, oldest dropped first)
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=50))

    # Agent run durations in seconds (bounded)
    run_durations: deque = field(default_factory=lambda: deque(maxlen=500))

    # Drain mode — stops accepting new webhooks, finishes in-flight work
    draining: bool = False

"""Alert intake pipeline with dedup, service serialization, and concurrency control.

Sits between the webhook handler and _process_alert. Replaces
BackgroundTasks.add_task() with a controlled dispatch pipeline:

1. Incident-level dedup — same incident_id is never processed twice concurrently.
2. Service-level serialization — one agent loop per service at a time.
3. Global concurrency limit — caps total concurrent agent runs.
4. Priority ordering — P1 alerts dispatch before P4 when slots open.
5. Stale alert expiry — queued alerts expire after a configurable TTL.
"""

import asyncio
import heapq
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from models import PagerDutyAlert, Priority
from state import RuntimeState
from telemetry import (
    alerts_deduplicated_counter,
    alerts_expired_counter,
    alerts_queued_counter,
    incidents_active_updown,
    intake_queue_depth_updown,
)

logger = logging.getLogger(__name__)


def _priority_rank(priority: Priority | None) -> int:
    """Map Priority enum to sort rank. P1=1 (highest), None=99 (lowest)."""
    if priority is None:
        return 99
    return {"P1": 1, "P2": 2, "P3": 3, "P4": 4}[priority.value]


@dataclass(order=False)
class QueuedAlert:
    """An alert waiting in the intake queue."""

    alert: PagerDutyAlert
    trace_id: str
    enqueued_at: float
    priority_rank: int

    def __lt__(self, other: "QueuedAlert") -> bool:
        """Lower priority_rank wins (P1 < P2). Ties broken by enqueue time (FIFO)."""
        if self.priority_rank != other.priority_rank:
            return self.priority_rank < other.priority_rank
        return self.enqueued_at < other.enqueued_at

    def __le__(self, other: "QueuedAlert") -> bool:
        return self == other or self < other


class AlertIntake:
    """Alert intake pipeline with dedup, service serialization, and concurrency control.

    All mutable state is protected by self._lock (asyncio.Lock). Dispatch
    decisions — which alert to run next — happen atomically under the lock.
    """

    def __init__(
        self,
        process_fn: Callable[[PagerDutyAlert, str], Awaitable[None]],
        state: RuntimeState,
        max_concurrent: int = 3,
        queue_ttl_seconds: int = 600,
    ) -> None:
        self._process_fn = process_fn
        self._state = state
        self._max_concurrent = max_concurrent
        self._queue_ttl_seconds = queue_ttl_seconds

        # All fields below are protected by _lock
        self._lock = asyncio.Lock()
        self._known_incidents: set[str] = set()
        self._active_services: dict[str, str] = {}  # service_name -> incident_id
        self._active_count: int = 0
        self._queue: list[QueuedAlert] = []
        self._tasks: set[asyncio.Task] = set()
        self._shutting_down: bool = False

    async def submit(self, alert: PagerDutyAlert, trace_id: str) -> str:
        """Submit an alert for processing.

        Returns:
            "dispatched" — processing started immediately
            "queued"     — service busy or concurrency limit; alert is queued
            "deduplicated" — same incident_id already processing or queued
            "rejected"   — intake is shutting down
        """
        if self._shutting_down:
            return "rejected"

        async with self._lock:
            # Incident-level dedup
            if alert.incident_id in self._known_incidents:
                logger.info(
                    "Deduplicated: incident_id=%s trace_id=%s",
                    alert.incident_id,
                    trace_id,
                )
                self._state.alerts_deduplicated += 1
                alerts_deduplicated_counter.add(1)
                return "deduplicated"

            # Register this incident
            self._known_incidents.add(alert.incident_id)

            # Can we dispatch immediately?
            can_dispatch = (
                alert.service_name not in self._active_services
                and self._active_count < self._max_concurrent
            )

            if can_dispatch:
                self._active_count += 1
                self._active_services[alert.service_name] = alert.incident_id
                self._state.active_incidents[alert.incident_id] = time.time()
                incidents_active_updown.add(1)
                self._start_run(alert, trace_id)
                return "dispatched"

            # Queue with priority
            queued = QueuedAlert(
                alert=alert,
                trace_id=trace_id,
                enqueued_at=time.time(),
                priority_rank=_priority_rank(alert.priority),
            )
            heapq.heappush(self._queue, queued)
            self._state.alerts_queued += 1
            alerts_queued_counter.add(1)
            intake_queue_depth_updown.add(1)
            logger.info(
                "Queued: incident_id=%s service=%s priority=%s queue_depth=%d trace_id=%s",
                alert.incident_id,
                alert.service_name,
                alert.priority,
                len(self._queue),
                trace_id,
            )
            return "queued"

    async def shutdown(self) -> None:
        """Graceful shutdown: discard queued alerts, wait for active runs."""
        async with self._lock:
            self._shutting_down = True
            discarded = len(self._queue)
            for item in self._queue:
                self._known_incidents.discard(item.alert.incident_id)
                intake_queue_depth_updown.add(-1)
            self._queue.clear()
            if discarded:
                logger.info("Shutdown: discarded %d queued alerts", discarded)

        if self._tasks:
            logger.info("Shutdown: waiting for %d active runs...", len(self._tasks))
            done, pending = await asyncio.wait(self._tasks, timeout=30)
            if pending:
                logger.warning(
                    "Shutdown: %d runs did not complete within 30s",
                    len(pending),
                )

    @property
    def queue_depth(self) -> int:
        """Current number of alerts waiting in the queue."""
        return len(self._queue)

    @property
    def active_count(self) -> int:
        """Current number of alerts actively being processed."""
        return self._active_count

    def _start_run(self, alert: PagerDutyAlert, trace_id: str) -> None:
        """Launch a processing task. Caller must hold self._lock."""
        task = asyncio.create_task(
            self._run_wrapper(alert, trace_id),
            name=f"alert-{alert.incident_id}",
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_wrapper(self, alert: PagerDutyAlert, trace_id: str) -> None:
        """Run the processing function and trigger next dispatch on completion."""
        try:
            await self._process_fn(alert, trace_id)
        finally:
            await self._on_complete(alert)

    async def _on_complete(self, alert: PagerDutyAlert) -> None:
        """Clean up after a processing task finishes and dispatch the next alert."""
        async with self._lock:
            self._active_count -= 1
            self._known_incidents.discard(alert.incident_id)
            self._active_services.pop(alert.service_name, None)

            if not self._shutting_down:
                self._dispatch_next()

    def _dispatch_next(self) -> None:
        """Pick the next eligible alert from the queue. Caller must hold self._lock.

        Scans the heap for the highest-priority alert whose service has no active
        run and the concurrency limit is not reached. Expires stale alerts along
        the way.
        """
        if not self._queue or self._active_count >= self._max_concurrent:
            return

        now = time.time()
        eligible: QueuedAlert | None = None
        remaining: list[QueuedAlert] = []

        while self._queue:
            candidate = heapq.heappop(self._queue)

            # Check TTL expiry
            age = now - candidate.enqueued_at
            if age > self._queue_ttl_seconds:
                self._known_incidents.discard(candidate.alert.incident_id)
                self._state.alerts_expired += 1
                alerts_expired_counter.add(1)
                intake_queue_depth_updown.add(-1)
                logger.info(
                    "Expired: incident_id=%s age=%.0fs ttl=%ds trace_id=%s",
                    candidate.alert.incident_id,
                    age,
                    self._queue_ttl_seconds,
                    candidate.trace_id,
                )
                continue

            # Check if this alert's service is available
            if (
                eligible is None
                and candidate.alert.service_name not in self._active_services
            ):
                eligible = candidate
                intake_queue_depth_updown.add(-1)
                continue

            remaining.append(candidate)

        # Restore remaining items as a heap
        self._queue = remaining
        heapq.heapify(self._queue)

        if eligible is not None:
            alert = eligible.alert
            self._active_count += 1
            self._active_services[alert.service_name] = alert.incident_id
            self._state.active_incidents[alert.incident_id] = time.time()
            incidents_active_updown.add(1)
            self._start_run(alert, eligible.trace_id)

"""Tests for alert intake pipeline — dedup, service serialization, concurrency, priority."""

import asyncio
import time
from datetime import datetime

from intake import AlertIntake, QueuedAlert, _priority_rank
from models import AlertSeverity, PagerDutyAlert, Priority
from state import RuntimeState


def _make_alert(
    incident_id: str = "inc-1",
    service_name: str = "api",
    priority: Priority | None = Priority.P2,
) -> PagerDutyAlert:
    """Create a test alert with minimal required fields."""
    return PagerDutyAlert(
        incident_id=incident_id,
        service_name=service_name,
        severity=AlertSeverity.HIGH,
        priority=priority,
        description="Test alert",
        timestamp=datetime.now(),
    )


class TestPriorityRank:
    def test_p1_is_highest(self):
        assert _priority_rank(Priority.P1) == 1

    def test_p4_is_lowest_named(self):
        assert _priority_rank(Priority.P4) == 4

    def test_none_is_lowest(self):
        assert _priority_rank(None) == 99

    def test_ordering(self):
        assert _priority_rank(Priority.P1) < _priority_rank(Priority.P2)
        assert _priority_rank(Priority.P2) < _priority_rank(Priority.P3)
        assert _priority_rank(Priority.P3) < _priority_rank(Priority.P4)
        assert _priority_rank(Priority.P4) < _priority_rank(None)


class TestQueuedAlertOrdering:
    def test_lower_priority_rank_wins(self):
        a = QueuedAlert(_make_alert(), "t1", time.time(), 1)
        b = QueuedAlert(_make_alert(), "t2", time.time(), 4)
        assert a < b

    def test_same_priority_fifo(self):
        t1 = time.time()
        t2 = t1 + 1
        a = QueuedAlert(_make_alert(), "t1", t1, 2)
        b = QueuedAlert(_make_alert(), "t2", t2, 2)
        assert a < b


class TestDeduplication:
    async def test_same_incident_id_deduplicated(self):
        state = RuntimeState()
        calls = []

        async def process(alert, trace_id):
            calls.append(alert.incident_id)
            await asyncio.sleep(0.1)

        intake = AlertIntake(process, state, max_concurrent=3)
        alert = _make_alert(incident_id="inc-1")

        result1 = await intake.submit(alert, "t1")
        result2 = await intake.submit(alert, "t2")

        assert result1 == "dispatched"
        assert result2 == "deduplicated"
        assert state.alerts_deduplicated == 1
        await asyncio.sleep(0.2)

    async def test_different_incidents_both_dispatched(self):
        state = RuntimeState()
        calls = []

        async def process(alert, trace_id):
            calls.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=3)

        r1 = await intake.submit(_make_alert("inc-1", "api"), "t1")
        r2 = await intake.submit(_make_alert("inc-2", "worker"), "t2")

        assert r1 == "dispatched"
        assert r2 == "dispatched"
        await asyncio.sleep(0.1)
        assert len(calls) == 2

    async def test_resubmit_after_completion(self):
        state = RuntimeState()
        calls = []

        async def process(alert, trace_id):
            calls.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=3)

        r1 = await intake.submit(_make_alert("inc-1", "api"), "t1")
        assert r1 == "dispatched"
        await asyncio.sleep(0.1)

        # After completion, same incident_id should be accepted again
        r2 = await intake.submit(_make_alert("inc-1", "api"), "t2")
        assert r2 == "dispatched"
        await asyncio.sleep(0.1)
        assert len(calls) == 2


class TestServiceSerialization:
    async def test_same_service_queued(self):
        state = RuntimeState()
        started = asyncio.Event()
        release = asyncio.Event()

        async def process(alert, trace_id):
            started.set()
            await release.wait()

        intake = AlertIntake(process, state, max_concurrent=3)

        r1 = await intake.submit(_make_alert("inc-1", "api"), "t1")
        await asyncio.sleep(0)  # let task start
        await started.wait()

        r2 = await intake.submit(_make_alert("inc-2", "api"), "t2")

        assert r1 == "dispatched"
        assert r2 == "queued"
        assert state.alerts_queued == 1

        release.set()
        await asyncio.sleep(0.1)

    async def test_queued_dispatches_after_completion(self):
        state = RuntimeState()
        calls = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            calls.append(alert.incident_id)
            if alert.incident_id == "inc-1":
                await release.wait()

        intake = AlertIntake(process, state, max_concurrent=3)

        await intake.submit(_make_alert("inc-1", "api"), "t1")
        await asyncio.sleep(0)  # let task start

        await intake.submit(_make_alert("inc-2", "api"), "t2")

        # Only inc-1 should have started
        assert "inc-1" in calls
        assert "inc-2" not in calls

        # Release inc-1 — inc-2 should dispatch
        release.set()
        await asyncio.sleep(0.1)
        assert "inc-2" in calls

    async def test_different_services_concurrent(self):
        state = RuntimeState()
        calls = []

        async def process(alert, trace_id):
            calls.append(alert.incident_id)
            await asyncio.sleep(0.1)

        intake = AlertIntake(process, state, max_concurrent=3)

        r1 = await intake.submit(_make_alert("inc-1", "api"), "t1")
        r2 = await intake.submit(_make_alert("inc-2", "worker"), "t2")

        assert r1 == "dispatched"
        assert r2 == "dispatched"
        assert intake.active_count == 2
        await asyncio.sleep(0.2)


class TestConcurrencyLimit:
    async def test_excess_queued(self):
        state = RuntimeState()
        release = asyncio.Event()

        async def process(alert, trace_id):
            await release.wait()

        intake = AlertIntake(process, state, max_concurrent=2)

        r1 = await intake.submit(_make_alert("inc-1", "svc-a"), "t1")
        r2 = await intake.submit(_make_alert("inc-2", "svc-b"), "t2")
        await asyncio.sleep(0)  # let tasks start
        r3 = await intake.submit(_make_alert("inc-3", "svc-c"), "t3")

        assert r1 == "dispatched"
        assert r2 == "dispatched"
        assert r3 == "queued"
        assert intake.active_count == 2
        assert intake.queue_depth == 1

        release.set()
        await asyncio.sleep(0.1)

    async def test_queued_dispatches_on_completion(self):
        state = RuntimeState()
        calls = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            calls.append(alert.incident_id)
            if alert.incident_id in ("inc-1", "inc-2"):
                await release.wait()

        intake = AlertIntake(process, state, max_concurrent=1)

        await intake.submit(_make_alert("inc-1", "svc-a"), "t1")
        await asyncio.sleep(0)
        await intake.submit(_make_alert("inc-2", "svc-b"), "t2")

        assert len(calls) == 1
        assert intake.queue_depth == 1

        release.set()
        await asyncio.sleep(0.1)
        assert "inc-2" in calls


class TestPriorityOrdering:
    async def test_p1_before_p4(self):
        state = RuntimeState()
        order = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            if alert.incident_id == "blocker":
                await release.wait()
            order.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=1)

        # Fill the slot
        await intake.submit(_make_alert("blocker", "svc-x"), "t0")
        await asyncio.sleep(0)

        # Queue P4 first, then P1
        await intake.submit(
            _make_alert("low", "svc-a", Priority.P4), "t1"
        )
        await intake.submit(
            _make_alert("critical", "svc-b", Priority.P1), "t2"
        )

        release.set()
        await asyncio.sleep(0.2)

        # P1 should have run before P4
        assert order.index("critical") < order.index("low")

    async def test_fifo_within_same_priority(self):
        state = RuntimeState()
        order = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            if alert.incident_id == "blocker":
                await release.wait()
            order.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=1)

        await intake.submit(_make_alert("blocker", "svc-x"), "t0")
        await asyncio.sleep(0)

        await intake.submit(
            _make_alert("first", "svc-a", Priority.P2), "t1"
        )
        await intake.submit(
            _make_alert("second", "svc-b", Priority.P2), "t2"
        )

        release.set()
        await asyncio.sleep(0.2)

        assert order.index("first") < order.index("second")

    async def test_none_priority_is_lowest(self):
        state = RuntimeState()
        order = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            if alert.incident_id == "blocker":
                await release.wait()
            order.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=1)

        await intake.submit(_make_alert("blocker", "svc-x"), "t0")
        await asyncio.sleep(0)

        await intake.submit(
            _make_alert("no-pri", "svc-a", None), "t1"
        )
        await intake.submit(
            _make_alert("p4", "svc-b", Priority.P4), "t2"
        )

        release.set()
        await asyncio.sleep(0.2)

        assert order.index("p4") < order.index("no-pri")


class TestStaleExpiry:
    async def test_expired_alert_discarded(self):
        state = RuntimeState()
        calls = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            if alert.incident_id == "blocker":
                await release.wait()
            calls.append(alert.incident_id)

        # TTL of 0 seconds — everything expires immediately
        intake = AlertIntake(process, state, max_concurrent=1, queue_ttl_seconds=0)

        await intake.submit(_make_alert("blocker", "svc-x"), "t0")
        await asyncio.sleep(0)

        await intake.submit(_make_alert("stale", "svc-a"), "t1")
        assert intake.queue_depth == 1

        # Wait a tiny bit so the queued alert's age > 0
        await asyncio.sleep(0.01)

        release.set()
        await asyncio.sleep(0.1)

        assert "stale" not in calls
        assert state.alerts_expired == 1

    async def test_non_expired_alert_dispatches(self):
        state = RuntimeState()
        calls = []
        release = asyncio.Event()

        async def process(alert, trace_id):
            if alert.incident_id == "blocker":
                await release.wait()
            calls.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=1, queue_ttl_seconds=60)

        await intake.submit(_make_alert("blocker", "svc-x"), "t0")
        await asyncio.sleep(0)
        await intake.submit(_make_alert("fresh", "svc-a"), "t1")

        release.set()
        await asyncio.sleep(0.1)

        assert "fresh" in calls
        assert state.alerts_expired == 0


class TestShutdown:
    async def test_discards_queue(self):
        state = RuntimeState()
        release = asyncio.Event()

        async def process(alert, trace_id):
            await release.wait()

        intake = AlertIntake(process, state, max_concurrent=1)

        await intake.submit(_make_alert("active", "svc-a"), "t0")
        await asyncio.sleep(0)
        await intake.submit(_make_alert("queued", "svc-b"), "t1")

        assert intake.queue_depth == 1

        release.set()
        await intake.shutdown()

        assert intake.queue_depth == 0

    async def test_waits_for_active_runs(self):
        state = RuntimeState()
        completed = []

        async def process(alert, trace_id):
            await asyncio.sleep(0.1)
            completed.append(alert.incident_id)

        intake = AlertIntake(process, state, max_concurrent=3)

        await intake.submit(_make_alert("inc-1", "api"), "t1")
        await asyncio.sleep(0)

        await intake.shutdown()
        assert "inc-1" in completed

    async def test_submit_rejected_after_shutdown(self):
        state = RuntimeState()

        async def process(alert, trace_id):
            pass

        intake = AlertIntake(process, state)
        await intake.shutdown()

        result = await intake.submit(_make_alert(), "t1")
        assert result == "rejected"


class TestObservability:
    async def test_queue_depth_accurate(self):
        state = RuntimeState()
        release = asyncio.Event()

        async def process(alert, trace_id):
            await release.wait()

        intake = AlertIntake(process, state, max_concurrent=1)

        await intake.submit(_make_alert("a", "svc-a"), "t0")
        await asyncio.sleep(0)
        await intake.submit(_make_alert("b", "svc-b"), "t1")
        await intake.submit(_make_alert("c", "svc-c"), "t2")

        assert intake.queue_depth == 2

        release.set()
        await asyncio.sleep(0.2)

    async def test_active_count_accurate(self):
        state = RuntimeState()
        release = asyncio.Event()

        async def process(alert, trace_id):
            await release.wait()

        intake = AlertIntake(process, state, max_concurrent=3)

        await intake.submit(_make_alert("a", "svc-a"), "t1")
        await intake.submit(_make_alert("b", "svc-b"), "t2")
        await asyncio.sleep(0)

        assert intake.active_count == 2

        release.set()
        await asyncio.sleep(0.1)
        assert intake.active_count == 0

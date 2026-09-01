"""Shared fixtures.

No live Marquez. Tests assert on the event the client produced, which needs no
server, runs in milliseconds and works in CI, per this lab's own testing
standard.
"""

from __future__ import annotations

from typing import Any

import pytest
from openlineage.client import OpenLineageClient
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from mcp_server_ol.lineage import LineageEmitter
from mcp_server_ol.naming import target_from_dsn

DEMO_DSN = "postgresql://postgres:postgres@postgres:5432/warehouse"


class CapturingTransport:
    """Collects emitted events instead of sending them anywhere."""

    kind = "capturing"

    def __init__(self) -> None:
        self.events: list[Any] = []

    def emit(self, event: Any) -> None:
        self.events.append(event)


@pytest.fixture
def transport() -> CapturingTransport:
    return CapturingTransport()


@pytest.fixture
def emitter(transport: CapturingTransport) -> LineageEmitter:
    return LineageEmitter(
        OpenLineageClient(transport=transport),  # type: ignore[arg-type]
        target_from_dsn(DEMO_DSN),
        job_namespace="mcp-lineage-demo",
        default_schema="obsinsure",
    )


# -- telemetry (RAID D12/I29) ------------------------------------------------
#
# The OTel API permits one global provider per process, so these are session
# scoped and read destructively per test. Without them, `record_dropped` is a
# no-op and every assertion about lineage loss being *visible* would pass
# vacuously — which is precisely the bug I29 recorded.


@pytest.fixture(scope="session")
def _otel() -> tuple[InMemoryMetricReader, InMemorySpanExporter]:
    reader = InMemoryMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    return reader, exporter


def _read(reader: InMemoryMetricReader, counter_name: str) -> dict[str, int]:
    data = reader.get_metrics_data()
    found: dict[str, int] = {}
    for rm in data.resource_metrics if data else []:
        for sm in rm.scope_metrics:
            for metric in sm.metrics:
                if metric.name != counter_name:
                    continue
                for point in metric.data.data_points:
                    found[str(point.attributes.get("reason"))] = point.value
    return found


@pytest.fixture
def telemetry_counts(_otel) -> Any:
    """Counters our instrumentation emitted *during this test*, by reason.

    Counters are cumulative for the life of the process, so a raw read leaks
    every earlier test's increments into this one. Baseline at setup and report
    deltas — otherwise "this path emits no signal" can never be asserted, and
    that assertion is half of what these tests exist for.
    """
    reader, exporter = _otel
    exporter.clear()

    class Counts:
        def __init__(self) -> None:
            self._baseline: dict[str, dict[str, int]] = {}

        def _base(self, counter_name: str) -> dict[str, int]:
            if counter_name not in self._baseline:
                self._baseline[counter_name] = _read(reader, counter_name)
            return self._baseline[counter_name]

        def by_reason(self, counter_name: str) -> dict[str, int]:
            base = self._base(counter_name)
            now = _read(reader, counter_name)
            return {k: v - base.get(k, 0) for k, v in now.items() if v - base.get(k, 0) != 0}

        @property
        def span_events(self) -> list[str]:
            return [e.name for span in exporter.get_finished_spans() for e in span.events]

    counts = Counts()
    # Snapshot both counters before the test body runs, so deltas are honest.
    from mcp_server_ol import telemetry

    counts._base(telemetry.DROPPED_COUNTER)
    counts._base(telemetry.DEGRADED_COUNTER)
    return counts

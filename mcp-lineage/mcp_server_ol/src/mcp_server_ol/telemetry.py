"""Software-observability signals for lineage that arrived degraded or not at all.

**This module exists because of RAID D12**, and its shape is the decision:

> A lineage store reports on the events it received. It cannot report on the
> events it never received — it has no record of them and no basis for
> expecting them. Ask Marquez "what did you not get?" and the question is
> malformed: there is no denominator.

So the two failure classes route to different planes, and the split is not a
matter of taste:

1. **An event that is sent but incomplete** declares that *on itself*, as an
   OpenLineage facet — see the `lineage.*` tags in `lineage.py`. The event
   exists, so it can tell the truth about its own completeness. This module
   *additionally* counts those, because an operator wants the rate; the event
   remains the authority.
2. **An event that is never sent at all** is invisible to OpenLineage by
   definition. It surfaces here, as a span event and a counter, with the reason
   attached. There is no other plane that can see it.
3. **Logs are operator diagnostics** and are never the primary signal for
   either. `configure_logging()` exists because they were not even that:
   RAID I29 found two lineage-loss paths logged at `debug` in a process where
   nothing called `logging.basicConfig`, so Python's `lastResort` handler
   dropped them entirely. Silent loss, in the reference implementation built to
   argue that silent loss is the normal case.

Nothing here may raise. A telemetry side-channel that breaks the tool call is
the D11 failure in a new costume.
"""

from __future__ import annotations

import logging
import os
from enum import StrEnum
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

SERVICE = "mcp-server-ol"

DROPPED_COUNTER = "mcp_lineage.events.dropped"
DEGRADED_COUNTER = "mcp_lineage.events.degraded"

_configured = False


class Dropped(StrEnum):
    """Reasons a lineage event never reached the collector (D12 class 2).

    Each value is a path RAID I29 found. `IDENTITY_MALFORMED` is the subtle one:
    the *event* is still sent, but the caller's identity is lost, and an event
    with no parent looks identical whether the caller sent nothing or sent
    garbage. Only the malformed case is an error, so only it is counted here —
    see `meta.ParentStatus`.
    """

    EMIT_FAILED = "emit-failed"
    NO_REQUEST_CONTEXT = "no-request-context"
    IDENTITY_MALFORMED = "identity-malformed"
    TRACEPARENT_MALFORMED = "traceparent-malformed"


class Degraded(StrEnum):
    """Reasons a lineage event was sent but is known to be incomplete (D12 class 1)."""

    PARSE_FAILED = "parse-failed"
    PARSE_INCOMPLETE = "parse-incomplete"


def configure_logging() -> None:
    """Configure logging explicitly rather than inheriting `lastResort`.

    RAID I29: without this, DEBUG and INFO are discarded and WARNING reaches
    stderr only by fallback. `LOG_LEVEL` overrides; INFO is the default so that
    the absence of identity is observable in a demo without a debug build.
    """
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    )


def configure_telemetry() -> None:
    """Install tracer and meter providers, exporting over OTLP where configured.

    Idempotent, and a no-op for exporters when `OTEL_EXPORTER_OTLP_ENDPOINT` is
    unset — the API degrades to no-ops, so unit tests need no collector.
    """
    global _configured
    if _configured:
        return
    _configured = True

    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    resource = Resource.create({SERVICE_NAME: SERVICE})

    if not endpoint:
        trace.set_tracer_provider(TracerProvider(resource=resource))
        logger.info("telemetry: no OTLP endpoint configured; spans are local only")
        return

    try:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
        trace.set_tracer_provider(provider)

        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=[
                    PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint, insecure=True))
                ],
            )
        )
        logger.info("telemetry: exporting spans and metrics to %s", endpoint)
    except Exception:  # noqa: BLE001 - telemetry setup must never stop the server
        logger.warning("telemetry: OTLP setup failed; continuing without export", exc_info=True)


def tracer() -> trace.Tracer:
    return trace.get_tracer(SERVICE)


def current_trace_context() -> tuple[str, str] | None:
    """`(trace_id, span_id)` as W3C-format hex, or `None` outside a recording span.

    RAID D15: this is what makes the link between the two records bidirectional.
    The span already carries `lineage.run_id`; without this the lineage event has
    no route back, and third line — who start from the lineage graph, not from
    the tracing backend — reach a dead end.
    """
    try:
        ctx = trace.get_current_span().get_span_context()
        if not ctx.is_valid:
            return None
        return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
    except Exception:  # noqa: BLE001
        logger.debug("telemetry: no trace context available", exc_info=True)
        return None


def _counter(name: str, description: str) -> Any:
    return metrics.get_meter(SERVICE).create_counter(name, description=description)


def record_dropped(reason: Dropped, detail: str | None = None) -> None:
    """Record a lineage event that was lost, or sent with the caller's identity lost.

    **This is the only signal that exists for it.** By D12 the lineage store
    cannot report its own absences, so if this call is missing or unexported,
    the loss is undetectable by anyone.
    """
    _record(
        DROPPED_COUNTER,
        "Lineage events lost, or sent with the caller's identity lost",
        "lineage.dropped",
        reason,
        detail,
        mark_span=True,
    )


def record_degraded(reason: Degraded, detail: str | None = None) -> None:
    """Record a lineage event that was sent but is known to be incomplete.

    The event itself carries the authoritative statement (`lineage.completeness`);
    this is the operator-facing rate.
    """
    _record(
        DEGRADED_COUNTER,
        "Lineage events sent with known incompleteness",
        "lineage.degraded",
        reason,
        detail,
    )


def _record(
    counter_name: str,
    description: str,
    event_name: str,
    reason: StrEnum,
    detail: str | None,
    *,
    mark_span: bool = False,
) -> None:
    attributes: dict[str, str] = {"reason": str(reason)}
    if detail:
        attributes["detail"] = detail[:200]

    try:
        _counter(counter_name, description).add(1, attributes)
    except Exception:  # noqa: BLE001
        logger.debug("telemetry: counter %s failed", counter_name, exc_info=True)

    try:
        span = trace.get_current_span()
        if span.is_recording():
            span.add_event(event_name, attributes=dict(attributes))
            if mark_span:
                # A tail-sampling hook, not decoration. The collector keeps any
                # trace carrying this attribute regardless of the sampling
                # percentage — see `otel-collector-config.yaml`. Without it, the
                # span event recording a lost lineage event is itself ~90%
                # likely to be sampled away (RAID R09): the record of the loss,
                # lost. The counter is unsampled and remains the durable signal;
                # this is what makes the *trace* worth pivoting to.
                span.set_attribute("lineage.dropped", "true")
    except Exception:  # noqa: BLE001
        logger.debug("telemetry: span event %s failed", event_name, exc_info=True)

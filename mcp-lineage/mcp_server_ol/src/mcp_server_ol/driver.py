"""The instrumentation seam: a `SqlDriver` that emits lineage.

`postgres-mcp` is not forked. Every SQL-bearing tool it exposes reaches the
database through `SqlDriver.execute_query`, and `get_sql_driver()` is a
module-level factory — so subclassing the driver and swapping the factory is
the whole integration. Upstream stays unmodified and pinned (RAID D03).

That is deliberately the evidence: instrumenting a real, widely-used MCP server
for lineage takes a subclass. What is missing from the ecosystem is not the
means but the convention.

**Why this is not the proxy D02 rejected.** The distinction D02 draws is about
*who declares*, not *how they know*. A proxy parsing traffic is an outside
party guessing about somebody else's action. This runs inside the process that
executes the statement — the acting entity declaring its own behaviour. The
declaration is still imperfect (R03) and is labelled as intent rather than
effect, which is what keeps the position honest rather than convenient (R04).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from openlineage_sql import parse
from opentelemetry import trace
from postgres_mcp.sql import SqlDriver

from mcp_server_ol import telemetry
from mcp_server_ol.lineage import LineageEmitter, ParsedStatement
from mcp_server_ol.meta import (
    ABSENT,
    ABSENT_TRACEPARENT,
    ParentLookup,
    ParentStatus,
    TraceparentLookup,
    TraceparentStatus,
)

logger = logging.getLogger(__name__)

DIALECT = "postgres"


class FailureMode(StrEnum):
    """What happens when lineage cannot be recorded — RAID D11, R08.

    **This was an unstated assumption until it was challenged, and the challenge
    was right.** D11 takes fail-open as the default and defends it: an
    observability side-channel that can break the thing it observes gets removed
    by the first person it pages, and a lineage integration nobody dares deploy
    evidences nothing.

    But R08 records the counter-position, which is not weak: in a regulated
    setting a query that executed with no record that it executed is precisely
    the state a control exists to prevent. Third line will ask for this by name,
    and `REQUIREMENTS.md` § 3a now argues safety explicitly — an agent acting
    autonomously with no surviving record of what it touched is the failure that
    section describes.

    So the posture is a deployment choice rather than an opinion baked into the
    code. Neither mode is presented as correct; both are demonstrated.
    """

    OPEN = "open"
    CLOSED = "closed"


class LineageEmissionError(RuntimeError):
    """Raised in `FailureMode.CLOSED` when a lineage event cannot be recorded.

    Deliberately distinct from any database error: the statement was fine, the
    *control* failed, and a reader of the resulting failure must be able to tell
    those apart.
    """


def parse_statement(sql: str) -> ParsedStatement:
    """Parse one statement into declared inputs and outputs.

    A parse failure is not fatal. The statement still runs, and lineage is
    emitted with no datasets rather than not at all — an event that records
    *that a governed database was reached* is worth more than silence, and
    silence is indistinguishable from the tool never having been called.

    But the resulting event **must not read as "this touched nothing"** (RAID
    I29). The failure is carried on `ParsedStatement.parse_error`, which puts a
    `parse-failed` completeness tag on the event, and counted as a degraded
    emission for the operator (D12 class 1).
    """
    try:
        meta = parse([sql], dialect=DIALECT)
    except Exception as exc:  # noqa: BLE001 - parser errors must never break the tool
        logger.warning("lineage: SQL parse failed, emitting with no datasets: %s", exc)
        telemetry.record_degraded(telemetry.Degraded.PARSE_FAILED, str(exc))
        return ParsedStatement(sql=sql, inputs=(), outputs=(), parse_error=str(exc))

    if meta.errors:
        logger.warning("lineage: SQL parse reported errors: %s", meta.errors)
        telemetry.record_degraded(telemetry.Degraded.PARSE_INCOMPLETE, str(meta.errors))
        return ParsedStatement(
            sql=sql,
            inputs=tuple(str(t) for t in meta.in_tables),
            outputs=tuple(str(t) for t in meta.out_tables),
            parse_error=str(meta.errors),
        )

    return ParsedStatement(
        sql=sql,
        inputs=tuple(str(t) for t in meta.in_tables),
        outputs=tuple(str(t) for t in meta.out_tables),
    )


class LineageSqlDriver(SqlDriver):
    """`SqlDriver` that emits an OpenLineage run around each query.

    Ordering matters and is not incidental:

    1. parse, then
    2. emit START (before execution — a process killed mid-statement still
       leaves a record that the database was reached), then
    3. execute, then
    4. emit COMPLETE, or FAIL if it raised.

    **Whether emission can change the outcome of the tool call is a deployment
    choice** — `FailureMode`, RAID D11 and R08. By default it cannot: a lineage
    failure is recorded and swallowed, because an observability side-channel
    that can break the thing it observes will be removed by the first person it
    pages. Configured `CLOSED`, it can: the statement is refused rather than
    left unrecorded, which is what a control environment asks for.

    The START-before-execution ordering is what makes the second mode coherent
    rather than theatrical — a failure to record is caught before the data is
    reached, not after.
    """

    def __init__(
        self,
        conn: Any = None,
        engine_url: str | None = None,
        *,
        emitter: LineageEmitter,
        parent_provider: Callable[[], ParentLookup] | None = None,
        traceparent_provider: Callable[[], TraceparentLookup] | None = None,
        job_name: str = "mcp.execute_sql",
        failure_mode: FailureMode = FailureMode.OPEN,
    ) -> None:
        super().__init__(conn=conn, engine_url=engine_url)
        self._emitter = emitter
        self._parent_provider = parent_provider or (lambda: ABSENT)
        self._traceparent_provider = traceparent_provider or (lambda: ABSENT_TRACEPARENT)
        self._job_name = job_name
        self._failure_mode = failure_mode

    def _parent(self) -> ParentLookup:
        """Resolve caller identity, distinguishing absent from broken (RAID I29).

        A provider that *raises* is our own instrumentation failing, not the
        caller's omission — so it is counted as a dropped identity, never
        quietly folded into the normal no-identity case.
        """
        try:
            lookup = self._parent_provider()
        except Exception:  # noqa: BLE001
            logger.warning("lineage: parent identity provider raised; actor unknown", exc_info=True)
            telemetry.record_dropped(telemetry.Dropped.NO_REQUEST_CONTEXT)
            return ABSENT

        if lookup.is_malformed:
            telemetry.record_dropped(telemetry.Dropped.IDENTITY_MALFORMED)
        return lookup

    def _traceparent(self) -> TraceparentLookup:
        """Resolve an inbound trace context, distinguishing absent from broken.

        Mirrors `_parent()`'s shape exactly, for a different signal (RAID I34):
        this is OTel trace parentage, read off the reserved flat `traceparent`
        `_meta` key, not the bespoke OpenLineage parent block `_parent()` reads.
        A provider that *raises* is our own instrumentation failing, not the
        caller's omission, so it is counted the same way `_parent()` counts its
        own provider failures.
        """
        try:
            lookup = self._traceparent_provider()
        except Exception:  # noqa: BLE001
            logger.warning("lineage: traceparent provider raised; starting a fresh span", exc_info=True)
            telemetry.record_dropped(telemetry.Dropped.NO_REQUEST_CONTEXT)
            return ABSENT_TRACEPARENT

        if lookup.is_malformed:
            telemetry.record_dropped(telemetry.Dropped.TRACEPARENT_MALFORMED)
        return lookup

    async def execute_query(
        self,
        query: Any,
        params: list[Any] | None = None,
        force_readonly: bool = False,
    ) -> Any:
        tp_lookup = self._traceparent()
        span_kwargs: dict[str, Any] = {}
        if tp_lookup.status is TraceparentStatus.PRESENT:
            span_kwargs["context"] = tp_lookup.context

        with telemetry.tracer().start_as_current_span(self._job_name, **span_kwargs) as span:
            statement = parse_statement(str(query))
            lookup = self._parent()
            run_id = self._emitter.new_run_id()

            # The span carries the lineage run id so an operator who sees a
            # dropped-event count can pivot to the run that should have existed.
            # This is correlation, not identity — see RAID R09.
            span.set_attribute("lineage.run_id", run_id)
            span.set_attribute("lineage.actor_status", str(lookup.status))

            parent = lookup.identity
            actor = str(lookup.status if lookup.identity is None else ParentStatus.PRESENT)

            # START is emitted before execution, which is what makes fail-closed
            # meaningful: in CLOSED mode a failure here stops the statement from
            # running at all, so there is no unrecorded access rather than an
            # unrecorded access we then complain about.
            self._safe_emit(self._emitter.start, run_id, statement, parent, actor)

            try:
                result = await super().execute_query(query, params, force_readonly=force_readonly)
            except Exception as exc:
                # The statement already failed. Emission failure must not mask
                # the database error, so this stays fail-open in both modes —
                # the caller needs the real cause, and the drop is counted.
                self._safe_emit(
                    self._emitter.fail, run_id, statement, parent, actor, str(exc), force_open=True
                )
                raise

            # COMPLETE has already had its side effect on the database. Raising
            # here does not un-read the data, but it does stop the result being
            # returned to an agent that would then act on it with no durable
            # record — which is the point of the mode.
            self._safe_emit(self._emitter.complete, run_id, statement, parent, actor)

        # Export is made synchronous with the call because BatchSpanProcessor's
        # periodic background flush did not fire reliably in the WSL2/Docker Desktop
        # environment this was developed in, so spans queued and never exported. It
        # costs up to a second on every call, and a deployment should rely on the
        # batch processor and remove it (RAID I62).
        #
        # Guarded rather than called unconditionally: outside a configured SDK
        # (unit tests, or any deployment that never calls telemetry's setup),
        # `trace.get_tracer_provider()` returns the API's `ProxyTracerProvider`,
        # which has no `force_flush` — this crashed every unit test exercising
        # this path (6 failures tracked as "pre-existing" since 2026-08-06).
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, "force_flush"):
            tracer_provider.force_flush(timeout_millis=1000)

        return result

    def _safe_emit(self, fn: Callable[..., None], run_id: str, *args: Any, force_open: bool = False) -> None:
        """Emit, recording any failure (D12, I29) and then applying the posture (D11, R08).

        This is the one path where OpenLineage cannot report on itself: the
        event never arrived, so the collector has no record of it and no basis
        for expecting one. The counter emitted here is the *only* signal that
        the loss occurred — so it is recorded in **both** modes, before the mode
        is consulted. Fail-closed must not become a reason for the drop to go
        uncounted.
        """
        try:
            fn(run_id, self._job_name, *args)
        except Exception as exc:  # noqa: BLE001
            logger.warning("lineage: emission failed", exc_info=True)
            telemetry.record_dropped(telemetry.Dropped.EMIT_FAILED, str(exc))

            if self._failure_mode is FailureMode.CLOSED and not force_open:
                raise LineageEmissionError(
                    "lineage could not be recorded and the server is configured to fail closed; "
                    "the data interaction has been refused rather than left unrecorded"
                ) from exc

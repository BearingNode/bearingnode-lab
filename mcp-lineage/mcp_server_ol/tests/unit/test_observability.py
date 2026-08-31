"""Lineage that is lost or degraded must be *visible* — RAID I29, routed by D12.

Every test here asserts a signal exists. That is the whole point: the defect
I29 recorded was not that lineage could be lost — D11 accepts that it can — but
that four paths lost it with no signal on any plane, in the reference
implementation built to argue that silent loss is the normal failure mode.

The routing under test is D12's:

* **sent but incomplete** → declared on the event itself, as a facet
* **never sent**          → OTel counter and span event, the only plane that
                            can see it, because a lineage store has no record
                            of what never arrived
* **logs**                → operator diagnostics, never the primary signal

A test that merely asserted "the tool call still succeeded" would pass against
the broken version. These assert the signal.
"""

from __future__ import annotations

import logging
from typing import Any

import attr
import pytest
from postgres_mcp.sql import SqlDriver

from mcp_server_ol import telemetry
from mcp_server_ol.driver import (
    FailureMode,
    LineageEmissionError,
    LineageSqlDriver,
    parse_statement,
)
from mcp_server_ol.lineage import (
    ACTOR_TAG,
    COMPLETENESS_PARSE_FAILED,
    COMPLETENESS_TAG,
    TRACE_CONTEXT_FACET,
    LineageEmitter,
    TraceContextRunFacet,
)
from mcp_server_ol.meta import ABSENT, ParentLookup, ParentStatus

SELECT = "SELECT * FROM obsinsure.claim"
GARBAGE = "NOT VALID SQL AT ALL (("


@pytest.fixture
def executed(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    seen: list[str] = []

    async def fake(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        seen.append(str(query))
        return [{"id": 1}]

    monkeypatch.setattr(SqlDriver, "execute_query", fake)
    return seen


def tags(event: Any) -> dict[str, str]:
    return {t.key: t.value for t in event.run.facets["tags"].tags}


# -- Path 1: the event never reached the collector ---------------------------


async def test_a_dropped_event_is_counted(emitter, transport, executed, telemetry_counts) -> None:
    """The collector cannot report this — D12. This counter is the only signal."""

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter)

    assert await driver.execute_query(SELECT) == [{"id": 1}], "D11: the tool call still succeeds"

    counts = telemetry_counts.by_reason(telemetry.DROPPED_COUNTER)
    assert counts.get(telemetry.Dropped.EMIT_FAILED) == 2, "START and COMPLETE both dropped"
    assert "lineage.dropped" in telemetry_counts.span_events


async def test_a_dropped_event_is_logged_at_warning(emitter, transport, executed, caplog) -> None:
    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter)

    with caplog.at_level(logging.WARNING):
        await driver.execute_query(SELECT)

    assert any("emission failed" in r.message for r in caplog.records)


# -- Path 2: the event was sent, but the parse failed -------------------------


async def test_a_failed_parse_is_declared_on_the_event(emitter, transport, executed) -> None:
    """The misleading path, and the reason I29 rated it worst.

    An event with empty inputs and outputs reads in Marquez as "this statement
    touched nothing". What actually happened is "we could not tell what this
    touched". Those are opposite claims, and the event must not make the wrong
    one — so the completeness tag distinguishes them.
    """
    driver = LineageSqlDriver(conn=object(), emitter=emitter)
    await driver.execute_query(GARBAGE)

    event = transport.events[0]
    assert event.inputs == [] and event.outputs == []
    assert tags(event)[COMPLETENESS_TAG] == COMPLETENESS_PARSE_FAILED


async def test_a_successful_parse_is_not_marked_as_failed(emitter, transport, executed) -> None:
    """The tag has to discriminate, or it says nothing."""
    driver = LineageSqlDriver(conn=object(), emitter=emitter)
    await driver.execute_query(SELECT)

    assert tags(transport.events[0])[COMPLETENESS_TAG] != COMPLETENESS_PARSE_FAILED


def test_a_failed_parse_records_why_it_failed() -> None:
    statement = parse_statement(GARBAGE)

    assert statement.parse_failed
    assert statement.parse_error
    assert statement.inputs == () and statement.outputs == ()


def test_a_statement_that_touches_nothing_is_not_a_parse_failure() -> None:
    """`SELECT 1` genuinely touches no table. That is a fact, not an absence of facts."""
    statement = parse_statement("SELECT 1")

    assert not statement.parse_failed
    assert statement.inputs == () and statement.outputs == ()


async def test_a_degraded_event_is_counted(emitter, transport, executed, telemetry_counts) -> None:
    """Either degraded reason is acceptable; a *silent* degradation is not.

    `openlineage-sql` reports unparseable input through `meta.errors` rather
    than by raising, so garbage SQL normally takes the `parse-incomplete` path
    and the exception path stays a genuine last resort. Both are degradations
    and both must be counted, so this asserts the class rather than the reason.
    """
    driver = LineageSqlDriver(conn=object(), emitter=emitter)
    await driver.execute_query(GARBAGE)

    counts = telemetry_counts.by_reason(telemetry.DEGRADED_COUNTER)
    assert sum(counts.values()) >= 1, f"a degraded emission must be counted, got {counts}"
    assert set(counts) <= {telemetry.Degraded.PARSE_FAILED, telemetry.Degraded.PARSE_INCOMPLETE}


# -- Path 3: our instrumentation could not see the request --------------------


async def test_a_broken_parent_provider_is_counted_not_swallowed(
    emitter, transport, executed, telemetry_counts, caplog
) -> None:
    """This is *our* failure, not the caller's omission, and must not look like it."""

    def broken() -> ParentLookup:
        raise KeyError("no request context")

    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=broken)

    with caplog.at_level(logging.WARNING):
        assert await driver.execute_query(SELECT) == [{"id": 1}]

    counts = telemetry_counts.by_reason(telemetry.DROPPED_COUNTER)
    assert counts.get(telemetry.Dropped.NO_REQUEST_CONTEXT, 0) >= 1
    assert caplog.records


# -- Path 4: the caller supplied identity we could not read -------------------


async def test_malformed_identity_is_counted_and_marked_on_the_event(
    emitter, transport, executed, telemetry_counts
) -> None:
    """A broken integration must be distinguishable from a pre-convention client."""
    malformed = ParentLookup(identity=None, status=ParentStatus.MALFORMED)
    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=lambda: malformed)

    await driver.execute_query(SELECT)

    counts = telemetry_counts.by_reason(telemetry.DROPPED_COUNTER)
    assert counts.get(telemetry.Dropped.IDENTITY_MALFORMED, 0) >= 1
    assert tags(transport.events[0])[ACTOR_TAG] == ParentStatus.MALFORMED


async def test_absent_identity_is_marked_but_not_counted_as_a_failure(
    emitter, transport, executed, telemetry_counts
) -> None:
    """Absence is the gap the RFC describes, and the state of every client today.

    It belongs on the event, so a consumer can see the actor is unknown — but it
    is not an error, and counting it as one would bury the real failures under
    the normal case.
    """
    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=lambda: ABSENT)

    await driver.execute_query(SELECT)

    assert tags(transport.events[0])[ACTOR_TAG] == ParentStatus.ABSENT
    assert "parent" not in transport.events[0].run.facets
    counts = telemetry_counts.by_reason(telemetry.DROPPED_COUNTER)
    assert counts.get(telemetry.Dropped.IDENTITY_MALFORMED, 0) == 0


async def test_supplied_identity_is_marked_as_supplied(emitter, transport, executed) -> None:
    from mcp_server_ol.lineage import ParentIdentity

    lookup = ParentLookup(
        identity=ParentIdentity(
            run_id="3f1d2c4e-0000-4000-8000-000000000001",
            job_namespace="mcp-lineage-demo",
            job_name="agent-session",
        ),
        status=ParentStatus.PRESENT,
    )
    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=lambda: lookup)

    await driver.execute_query(SELECT)
    assert tags(transport.events[0])[ACTOR_TAG] == ParentStatus.PRESENT


# -- The plane itself ---------------------------------------------------------


async def test_the_link_between_the_two_records_is_bidirectional(
    emitter: LineageEmitter, transport, executed, _otel
) -> None:
    """RAID D15 — third line start from the lineage graph, not the tracing backend.

    The span carrying `lineage.run_id` is only half a link. Without the reverse
    pointer, an auditor who asks "which agent interactions touched this table?"
    reaches the lineage event and stops — with no route to the decisioning
    context that says what the agent asked for, chose, and did with the answer.
    """
    _, exporter = _otel
    exporter.clear()
    driver = LineageSqlDriver(conn=object(), emitter=emitter)

    await driver.execute_query(SELECT)

    span = next(s for s in exporter.get_finished_spans() if s.name == "mcp.execute_sql")
    event = transport.events[0]
    facet = event.run.facets[TRACE_CONTEXT_FACET]

    assert span.context is not None
    # lineage event -> trace
    assert facet.traceId == f"{span.context.trace_id:032x}"
    assert facet.spanId == f"{span.context.span_id:016x}"
    # trace -> lineage event
    assert span.attributes is not None
    assert span.attributes["lineage.run_id"] == event.run.runId


async def test_every_event_of_a_run_carries_the_same_trace_reference(
    emitter: LineageEmitter, transport, executed
) -> None:
    """START and COMPLETE must agree, or the reference depends on which you read."""
    driver = LineageSqlDriver(conn=object(), emitter=emitter)
    await driver.execute_query(SELECT)

    refs = {
        (e.run.facets[TRACE_CONTEXT_FACET].traceId, e.run.facets[TRACE_CONTEXT_FACET].spanId)
        for e in transport.events
    }
    assert len(refs) == 1


def test_the_trace_facet_is_a_pointer_and_carries_no_telemetry(emitter, transport) -> None:
    """The scope objection on OpenLineage #4588, answered by construction.

    A maintainer's position is that OpenLineage is not a monitoring tool. This
    facet does not make it one: it carries a trace id and a span id and nothing
    else — no durations, no counts, no per-record granularity.
    """
    fields = {f.name for f in attr.fields(TraceContextRunFacet)}
    assert fields <= {"traceId", "spanId", "_producer", "_schemaURL"}


async def test_the_query_gets_a_span_carrying_the_lineage_run_id(
    emitter: LineageEmitter, transport, executed, _otel
) -> None:
    """R09: the span carries a *correlation* reference, never identity.

    An operator who sees a dropped-event count needs a way back to the run that
    should have existed. That is all this is for — and per R09 it is only
    resolvable while the trace is retained, which sampling does not guarantee.
    """
    _, exporter = _otel
    exporter.clear()
    driver = LineageSqlDriver(conn=object(), emitter=emitter)

    await driver.execute_query(SELECT)

    spans = [s for s in exporter.get_finished_spans() if s.name == "mcp.execute_sql"]
    assert spans, "the tool call must produce a span for lineage loss to attach to"
    assert spans[-1].attributes is not None
    assert spans[-1].attributes["lineage.run_id"] == transport.events[0].run.runId


# -- RAID R08 / D11: the posture is a deployment choice, not an opinion --------


async def test_fail_open_is_the_default(emitter, transport, executed) -> None:
    """D11 — an integration that can break the tool call will not be deployed."""

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter)

    assert await driver.execute_query(SELECT) == [{"id": 1}]


async def test_fail_closed_refuses_the_call_when_lineage_cannot_be_recorded(
    emitter, transport, executed
) -> None:
    """R08 — the posture a control environment asks for by name.

    An unrecorded read of a governed table is the state a control exists to
    prevent. Neither mode is presented as correct; both are demonstrated.
    """

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter, failure_mode=FailureMode.CLOSED)

    with pytest.raises(LineageEmissionError, match="fail closed"):
        await driver.execute_query(SELECT)


async def test_fail_closed_stops_the_statement_before_it_runs(emitter, transport, monkeypatch) -> None:
    """The ordering that makes the mode worth having.

    START is emitted before execution, so a failure there means the statement
    never runs — no unrecorded access, rather than an unrecorded access we then
    complain about.
    """
    ran: list[str] = []

    async def fake(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        ran.append(str(query))
        return []

    monkeypatch.setattr(SqlDriver, "execute_query", fake)

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter, failure_mode=FailureMode.CLOSED)

    with pytest.raises(LineageEmissionError):
        await driver.execute_query(SELECT)

    assert ran == [], "the statement must not reach the database if START could not be recorded"


async def test_fail_closed_does_not_mask_a_database_error(emitter, transport, monkeypatch) -> None:
    """The caller needs the real cause.

    On the FAIL path the statement has already failed. Emission failure must not
    replace the database error with a lineage one, in either mode.
    """

    async def boom(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        raise RuntimeError("relation does not exist")

    monkeypatch.setattr(SqlDriver, "execute_query", boom)

    emitted: list[Any] = []

    def explode_on_terminal(event: Any) -> None:
        emitted.append(event)
        if len(emitted) > 1:  # let START through, break the FAIL event
            raise ConnectionError("marquez is down")

    transport.emit = explode_on_terminal  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter, failure_mode=FailureMode.CLOSED)

    with pytest.raises(RuntimeError, match="relation does not exist"):
        await driver.execute_query(SELECT)


async def test_a_drop_is_counted_in_both_modes(emitter, transport, executed, telemetry_counts) -> None:
    """Fail-closed must not become a reason the loss goes uncounted (D12)."""

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]
    driver = LineageSqlDriver(conn=object(), emitter=emitter, failure_mode=FailureMode.CLOSED)

    with pytest.raises(LineageEmissionError):
        await driver.execute_query(SELECT)

    counts = telemetry_counts.by_reason(telemetry.DROPPED_COUNTER)
    assert counts.get(telemetry.Dropped.EMIT_FAILED, 0) >= 1

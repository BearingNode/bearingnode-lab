"""The driver seam: what gets emitted around a query, and in what order.

No database. `SqlDriver.execute_query` is replaced so these stay unit tests —
the point under test is the instrumentation, not psycopg.
"""

from __future__ import annotations

from typing import Any

import pytest
from openlineage.client.event_v2 import RunState
from postgres_mcp.sql import SqlDriver

from mcp_server_ol.driver import LineageSqlDriver, parse_statement
from mcp_server_ol.lineage import LineageEmitter, ParentIdentity
from mcp_server_ol.meta import (
    ABSENT_TRACEPARENT,
    ParentLookup,
    ParentStatus,
    TraceparentLookup,
    TraceparentStatus,
    traceparent_from_meta,
)

SELECT = "SELECT * FROM obsinsure.claim"


@pytest.fixture
def driver(emitter: LineageEmitter) -> LineageSqlDriver:
    return LineageSqlDriver(conn=object(), emitter=emitter)


@pytest.fixture
def executed(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record what reached the real driver, without a database."""
    seen: list[str] = []

    async def fake(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        seen.append(str(query))
        return [{"id": 1}]

    monkeypatch.setattr(SqlDriver, "execute_query", fake)
    return seen


async def test_query_still_returns_its_rows(driver, executed) -> None:
    """Instrumentation must be invisible to the caller."""
    assert await driver.execute_query(SELECT) == [{"id": 1}]
    assert executed == [SELECT]


async def test_start_is_emitted_before_execution(driver, transport, monkeypatch) -> None:
    """A process killed mid-statement must still leave a record."""
    order: list[str] = []

    async def fake(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        order.append("executed")
        return []

    monkeypatch.setattr(SqlDriver, "execute_query", fake)
    monkeypatch.setattr(transport, "emit", lambda e: order.append(f"emit:{e.eventType.value}") or None)

    await driver.execute_query(SELECT)
    assert order == ["emit:START", "executed", "emit:COMPLETE"]


async def test_datasets_come_from_the_parsed_sql(driver, transport, executed) -> None:
    await driver.execute_query(SELECT)
    assert transport.events[0].inputs[0]["name"] == "warehouse.obsinsure.claim"


async def test_failure_emits_fail_and_re_raises(driver, transport, monkeypatch) -> None:
    async def boom(self: Any, query: Any, params: Any = None, force_readonly: bool = False) -> Any:
        raise RuntimeError("relation does not exist")

    monkeypatch.setattr(SqlDriver, "execute_query", boom)

    with pytest.raises(RuntimeError, match="relation does not exist"):
        await driver.execute_query(SELECT)

    assert [e.eventType for e in transport.events] == [RunState.START, RunState.FAIL]
    assert "does not exist" in transport.events[-1].run.facets["errorMessage"].message


async def test_emission_failure_never_breaks_the_tool_call(driver, transport, executed) -> None:
    """An observability side-channel that can break its subject gets removed."""

    def explode(event: Any) -> None:
        raise ConnectionError("marquez is down")

    transport.emit = explode  # type: ignore[method-assign]

    assert await driver.execute_query(SELECT) == [{"id": 1}]


async def test_parent_identity_is_attached_when_the_caller_supplies_it(
    emitter: LineageEmitter, transport, executed
) -> None:
    parent = ParentIdentity(
        run_id="3f1d2c4e-0000-4000-8000-000000000001",
        job_namespace="mcp-lineage-demo",
        job_name="agent-session",
    )
    lookup = ParentLookup(identity=parent, status=ParentStatus.PRESENT)
    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=lambda: lookup)

    await driver.execute_query(SELECT)
    assert transport.events[0].run.facets["parent"].run.runId == parent.run_id


async def test_a_broken_parent_provider_does_not_break_the_call(
    emitter: LineageEmitter, transport, executed
) -> None:
    def broken() -> ParentLookup:
        raise KeyError("_meta missing")

    driver = LineageSqlDriver(conn=object(), emitter=emitter, parent_provider=broken)

    assert await driver.execute_query(SELECT) == [{"id": 1}]
    assert "parent" not in transport.events[0].run.facets


class _SpyTracer:
    """Wraps the real tracer, recording the kwargs each span was started with.

    A live integration test proving parenting survives export to Jaeger is
    separate (RAID I34); this only needs to prove the driver *asks* for the
    right context, so a spy on `telemetry.tracer()` is enough.
    """

    def __init__(self, real: Any) -> None:
        self._real = real
        self.calls: list[dict[str, Any]] = []

    def start_as_current_span(self, name: str, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self._real.start_as_current_span(name, **kwargs)


@pytest.fixture
def spy_tracer(_otel: Any, monkeypatch: pytest.MonkeyPatch) -> _SpyTracer:
    """Depends on `_otel` so `telemetry.tracer()` resolves against the real
    `TracerProvider` the session fixture installs, not the SDK's default
    `ProxyTracerProvider` — `force_flush()` in `execute_query` needs the former.
    """
    from mcp_server_ol import telemetry as telemetry_module

    real = telemetry_module.tracer()
    spy = _SpyTracer(real)
    monkeypatch.setattr("mcp_server_ol.driver.telemetry.tracer", lambda: spy)
    return spy


async def test_a_present_traceparent_is_used_as_the_span_parent(
    emitter: LineageEmitter, executed, spy_tracer: _SpyTracer
) -> None:
    valid = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    lookup = traceparent_from_meta({"traceparent": valid})
    assert lookup.status is TraceparentStatus.PRESENT

    driver = LineageSqlDriver(conn=object(), emitter=emitter, traceparent_provider=lambda: lookup)
    await driver.execute_query(SELECT)

    assert spy_tracer.calls == [{"context": lookup.context}]


async def test_an_absent_traceparent_starts_a_fresh_span(
    emitter: LineageEmitter, executed, spy_tracer: _SpyTracer
) -> None:
    driver = LineageSqlDriver(conn=object(), emitter=emitter, traceparent_provider=lambda: ABSENT_TRACEPARENT)
    await driver.execute_query(SELECT)

    assert spy_tracer.calls == [{}]


async def test_a_malformed_traceparent_starts_a_fresh_span(
    emitter: LineageEmitter, executed, spy_tracer: _SpyTracer
) -> None:
    lookup = traceparent_from_meta({"traceparent": "garbage"})
    assert lookup.status is TraceparentStatus.MALFORMED

    driver = LineageSqlDriver(conn=object(), emitter=emitter, traceparent_provider=lambda: lookup)
    await driver.execute_query(SELECT)

    assert spy_tracer.calls == [{}]


async def test_a_broken_traceparent_provider_does_not_break_the_call(
    emitter: LineageEmitter, executed, spy_tracer: _SpyTracer
) -> None:
    def broken() -> TraceparentLookup:
        raise KeyError("_meta missing")

    driver = LineageSqlDriver(conn=object(), emitter=emitter, traceparent_provider=broken)

    assert await driver.execute_query(SELECT) == [{"id": 1}]
    assert spy_tracer.calls == [{}]


def test_unparseable_sql_still_produces_an_event_with_no_datasets() -> None:
    """Silence is indistinguishable from the tool never having been called."""
    statement = parse_statement("NOT VALID SQL AT ALL ((")
    assert statement.inputs == ()
    assert statement.outputs == ()
    assert statement.sql.startswith("NOT VALID")

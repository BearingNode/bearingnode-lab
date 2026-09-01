"""What the emitter puts on the wire."""

from __future__ import annotations

import pytest
from openlineage.client.event_v2 import RunState

from mcp_server_ol.lineage import (
    ACTOR_UNKNOWN,
    COMPLETENESS_TAG,
    DERIVATION_PARSED_INTENT,
    DERIVATION_TAG,
    LineageEmitter,
    ParentIdentity,
    ParsedStatement,
)

STATEMENT = ParsedStatement(
    sql="SELECT * FROM obsinsure.claim",
    inputs=("obsinsure.claim",),
    outputs=(),
)

PARENT = ParentIdentity(
    run_id="3f1d2c4e-0000-4000-8000-000000000001",
    job_namespace="mcp-lineage-demo",
    job_name="agent-session",
    root_run_id="3f1d2c4e-0000-4000-8000-000000000002",
    root_job_namespace="mcp-lineage-demo",
    root_job_name="agent-root",
)


def tags(event) -> dict[str, str]:
    return {t.key: t.value for t in event.run.facets["tags"].tags}


def test_start_then_complete_are_both_emitted(emitter: LineageEmitter, transport) -> None:
    run_id = emitter.new_run_id()
    emitter.start(run_id, "mcp.execute_sql", STATEMENT, None)
    emitter.complete(run_id, "mcp.execute_sql", STATEMENT, None)

    assert [e.eventType for e in transport.events] == [RunState.START, RunState.COMPLETE]
    assert {e.run.runId for e in transport.events} == {run_id}


def test_datasets_use_the_openlineage_naming_convention(emitter: LineageEmitter, transport) -> None:
    """RAID I16 — namespace and name must be canonical catalog identity."""
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)
    ds = transport.events[0].inputs[0]

    assert ds["namespace"] == "postgres://postgres:5432"
    assert ds["name"] == "warehouse.obsinsure.claim"


def test_every_event_declares_its_datasets_are_intent(emitter: LineageEmitter, transport) -> None:
    """RAID I17 — intent must be distinguishable from effect on the event itself."""
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)

    assert tags(transport.events[0])[DERIVATION_TAG] == DERIVATION_PARSED_INTENT
    assert COMPLETENESS_TAG in tags(transport.events[0])


def test_parent_is_linkage_only_and_carries_no_forwarded_facets(emitter: LineageEmitter, transport) -> None:
    """RAID D10/R07 — Marquez silently drops facets nested under parent.

    Forwarding identity there would lose it with no error, so we deliberately
    do not. The parent's own event is the source of truth.
    """
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, PARENT)
    parent = transport.events[0].run.facets["parent"]

    assert parent.run.runId == PARENT.run_id
    assert parent.job.name == "agent-session"
    assert parent.root is not None
    assert parent.root.run.runId == PARENT.root_run_id
    # The load-bearing assertion: nothing is nested where it would be discarded.
    assert not parent.run.facets
    assert not parent.job.facets


def test_no_parent_means_no_parent_facet(emitter: LineageEmitter, transport) -> None:
    """An unknown actor is recorded as unknown, not as a placeholder."""
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)
    assert "parent" not in transport.events[0].run.facets


def test_failure_emits_a_terminal_event_with_the_error(emitter: LineageEmitter, transport) -> None:
    """RAID R03 and the testing standard's third non-negotiable.

    Without this, a failed statement leaves no terminal event — which a
    consumer cannot tell apart from the event loss this demo is about.
    """
    run_id = emitter.new_run_id()
    emitter.start(run_id, "mcp.execute_sql", STATEMENT, None)
    emitter.fail(run_id, "mcp.execute_sql", STATEMENT, None, ACTOR_UNKNOWN, "relation does not exist")

    fail = transport.events[-1]
    assert fail.eventType == RunState.FAIL
    assert fail.run.runId == run_id
    assert "does not exist" in fail.run.facets["errorMessage"].message


def test_failed_run_still_reports_the_attempted_datasets(emitter: LineageEmitter, transport) -> None:
    """An attempted read of a governed table is itself the governance event."""
    emitter.fail(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None, ACTOR_UNKNOWN, "boom")
    assert transport.events[-1].inputs[0]["name"] == "warehouse.obsinsure.claim"


def test_sql_is_carried_on_the_job_facet(emitter: LineageEmitter, transport) -> None:
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)
    assert transport.events[0].job.facets["sql"].query == STATEMENT.sql


def test_writes_appear_as_outputs(emitter: LineageEmitter, transport) -> None:
    statement = ParsedStatement(
        sql="INSERT INTO obsinsure.agent_notes SELECT * FROM obsinsure.premium",
        inputs=("obsinsure.premium",),
        outputs=("obsinsure.agent_notes",),
    )
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", statement, None)
    event = transport.events[0]

    assert event.inputs[0]["name"] == "warehouse.obsinsure.premium"
    assert event.outputs[0]["name"] == "warehouse.obsinsure.agent_notes"


@pytest.mark.parametrize("field", ["_producer", "producer"])
def test_events_declare_a_producer(emitter: LineageEmitter, transport, field: str) -> None:
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)
    assert getattr(transport.events[0], "producer", None)

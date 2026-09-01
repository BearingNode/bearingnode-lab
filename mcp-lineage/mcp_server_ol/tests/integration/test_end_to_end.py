"""End to end against the running compose stack.

Calls the instrumented `postgres-mcp` over MCP exactly as an agent would,
supplying caller identity in `_meta`, then reads the resulting run back out of
Marquez.

This is the demonstration in one file: an agent reaches data through
`tools/call`, and a complete, correctly-named, correctly-attributed lineage
record exists at the other end.

Requires `docker compose up` in `mcp-lineage/`. Deselected by default —
`pytest -m integration` to run.
"""

from __future__ import annotations

import json
import urllib.request
import uuid
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from mcp_server_ol.lineage import (
    ACTOR_TAG,
    COMPLETENESS_PARSE_FAILED,
    COMPLETENESS_TAG,
    DERIVATION_PARSED_INTENT,
    DERIVATION_TAG,
    TRACE_CONTEXT_FACET,
)
from mcp_server_ol.meta import LINEAGE_META_KEY, ParentStatus

pytestmark = pytest.mark.integration

MCP_URL = "http://localhost:8000/mcp"
MARQUEZ = "http://localhost:5000"
NAMESPACE = "mcp-lineage-demo"


def marquez(path: str) -> Any:
    with urllib.request.urlopen(f"{MARQUEZ}{path}", timeout=10) as r:
        return json.loads(r.read())


@pytest.fixture
async def called_with_identity() -> dict[str, Any]:
    """Make one tool call carrying caller identity, return what we sent."""
    parent = {
        "parentRunId": str(uuid.uuid4()),
        "jobNamespace": NAMESPACE,
        "jobName": f"agent-session-{uuid.uuid4().hex[:6]}",
        "rootRunId": str(uuid.uuid4()),
        "rootJobNamespace": NAMESPACE,
        "rootJobName": "agent-root",
    }

    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "execute_sql",
                {"sql": "SELECT claim_id FROM obsinsure.claim LIMIT 3"},
                meta={LINEAGE_META_KEY: parent},
            )

    assert not result.isError, result.content
    return parent


async def _run_for_parent(parent_run_id: str) -> Any:
    """Find the run whose parent is the identity we sent."""
    jobs = marquez(f"/api/v1/namespaces/{NAMESPACE}/jobs?limit=100")["jobs"]
    for job in jobs:
        latest = job.get("latestRun") or {}
        facets = latest.get("facets", {})
        if facets.get("parent", {}).get("run", {}).get("runId") == parent_run_id:
            return latest
    raise AssertionError(f"no run found with parent {parent_run_id}")


async def test_a_tool_call_produces_a_lineage_run(called_with_identity) -> None:
    run = await _run_for_parent(called_with_identity["parentRunId"])
    assert run["state"] == "COMPLETED"


async def test_dataset_is_named_per_the_openlineage_convention(called_with_identity) -> None:
    """RAID I16 — canonical catalog identity, not a transport pointer."""
    run = await _run_for_parent(called_with_identity["parentRunId"])

    names = {
        (d["datasetVersionId"]["namespace"], d["datasetVersionId"]["name"])
        for d in run["inputDatasetVersions"]
    }
    assert ("postgres://postgres:5432", "warehouse.obsinsure.claim") in names


async def test_the_caller_identity_survives_the_round_trip(called_with_identity) -> None:
    """RAID D10 — the link the server could not have invented for itself."""
    run = await _run_for_parent(called_with_identity["parentRunId"])
    parent = run["facets"]["parent"]

    assert parent["job"]["name"] == called_with_identity["jobName"]
    assert parent["root"]["run"]["runId"] == called_with_identity["rootRunId"]


async def test_the_run_declares_its_datasets_are_intent(called_with_identity) -> None:
    """RAID I17 — a consumer can tell declared from observed."""
    run = await _run_for_parent(called_with_identity["parentRunId"])
    tags = {t["key"]: t["value"] for t in run["facets"]["tags"]["tags"]}

    assert tags[DERIVATION_TAG] == DERIVATION_PARSED_INTENT
    assert COMPLETENESS_TAG in tags


async def test_a_call_without_identity_records_the_actor_as_unknown() -> None:
    """The gap itself, observable: no `_meta`, no parent, no invented actor."""
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "execute_sql", {"sql": "SELECT contract_id FROM obsinsure.contract LIMIT 1"}
            )
    assert not result.isError, result.content

    jobs = marquez(f"/api/v1/namespaces/{NAMESPACE}/jobs?limit=100")["jobs"]
    runs_without_parent = [
        j for j in jobs if "parent" not in ((j.get("latestRun") or {}).get("facets") or {})
    ]
    assert runs_without_parent, "expected at least one run with no parent identity"


# -- RAID I29 / D12: degradation must be readable off the event ---------------


async def _call(sql: str, meta: dict[str, Any] | None = None) -> Any:
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool("execute_sql", {"sql": sql}, meta=meta)


def _tags_for_sql(marker: str) -> dict[str, str]:
    """Read run tags off the raw stored event whose SQL carries `marker`.

    Every call lands on the same job name (`mcp.execute_sql`), so `latestRun`
    cannot identify a particular call and the SQL lives on a *job* facet rather
    than a run facet. The raw event endpoint is the only view carrying both
    halves, and reading it back from the store — rather than asserting locally —
    is what makes this evidence rather than a restatement of our own code.
    """
    events = marquez("/api/v1/events/lineage?limit=200")["events"]
    for event in events:
        query = event.get("job", {}).get("facets", {}).get("sql", {}).get("query", "")
        if marker not in query:
            continue
        tags = event.get("run", {}).get("facets", {}).get("tags", {}).get("tags", [])
        if tags:
            return {t["key"]: t["value"] for t in tags}
    raise AssertionError(f"no stored event found whose SQL carries {marker!r}")


async def test_a_failed_parse_is_readable_off_the_event_in_marquez() -> None:
    """RAID I29's worst path, verified against the store rather than locally.

    An event with no datasets and no completeness marker reads as "this
    statement touched nothing" — the opposite of what happened, which is that we
    could not tell what it touched. The tag has to survive the round trip to
    Marquez or the distinction only exists in our own process.
    """
    marker = f"parse_probe_{uuid.uuid4().hex[:8]}"
    # Unparseable for openlineage-sql, and rejected by Postgres too. Upstream
    # reports SQL errors as ordinary text content with `isError` false, so the
    # tool result is deliberately not asserted on here — what matters is that
    # the event still reached Marquez saying it could not determine datasets.
    await _call(f"SELECT 1 AS {marker} FROM (VALUES (1)) AS t(x) WHERE ((")

    tags = _tags_for_sql(marker)
    assert tags[COMPLETENESS_TAG] == COMPLETENESS_PARSE_FAILED


async def test_the_trace_reference_survives_marquez_ingestion() -> None:
    """RAID D15, and a deliberate re-run of the R07 trap.

    R07 found Marquez silently discarding facets nested under `parent` — HTTP
    201, identity gone, no error. A custom run facet is a different code path
    and could have behaved the same way, which would make the bidirectional
    link exist in our process and nowhere else. Asserted against the stored
    event, because that is the only version third line would ever read.
    """
    marker = f"trace_probe_{uuid.uuid4().hex[:8]}"
    await _call(f"SELECT claim_id AS {marker} FROM obsinsure.claim LIMIT 1")

    events = marquez("/api/v1/events/lineage?limit=200")["events"]
    for event in events:
        if marker not in event.get("job", {}).get("facets", {}).get("sql", {}).get("query", ""):
            continue
        facet = event["run"]["facets"].get(TRACE_CONTEXT_FACET)
        assert facet is not None, "the trace reference was discarded at ingestion"
        assert len(facet["traceId"]) == 32, "W3C trace ids are 32 hex characters"
        assert len(facet["spanId"]) == 16
        assert int(facet["traceId"], 16) != 0, "an all-zero trace id is not a reference"
        return
    raise AssertionError(f"no stored event found whose SQL carries {marker!r}")


async def test_absent_identity_is_marked_as_absent_not_merely_missing() -> None:
    """A consumer must see *why* there is no actor, not just that there is none."""
    marker = f"absent_probe_{uuid.uuid4().hex[:8]}"
    result = await _call(f"SELECT contract_id AS {marker} FROM obsinsure.contract LIMIT 1")
    assert not result.isError, result.content

    tags = _tags_for_sql(marker)
    assert tags[ACTOR_TAG] == ParentStatus.ABSENT


async def test_malformed_identity_is_distinguishable_from_absent_in_marquez() -> None:
    """RAID I29 — the regression that made a broken client invisible.

    Both cases produce a run with no parent facet. Only the tag tells them
    apart, and only from the store is that claim worth anything.
    """
    marker = f"malformed_probe_{uuid.uuid4().hex[:8]}"
    result = await _call(
        f"SELECT claim_id AS {marker} FROM obsinsure.claim LIMIT 1",
        meta={LINEAGE_META_KEY: {"parentRunId": "supplied-but-incomplete"}},
    )
    assert not result.isError, result.content

    tags = _tags_for_sql(marker)
    assert tags[ACTOR_TAG] == ParentStatus.MALFORMED

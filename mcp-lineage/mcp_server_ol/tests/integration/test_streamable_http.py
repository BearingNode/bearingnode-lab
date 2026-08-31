"""Streamable HTTP, and whether caller identity survives concurrency (RAID D13, I30).

**This is the load-bearing test of the workstream, not a transport smoke test.**

D10's Claim 2b rests on MCP `_meta` being able to carry a caller's lineage
identity through a real server. That has been demonstrated over SSE — one
session, one request flow, where nothing can be confused with anything else.
A real organisational deployment is not that: it is hosted, multi-tenant
Streamable HTTP with a session manager fielding concurrent requests from
different callers.

The server reads identity through `mcp.get_context().request_context`, a
contextvar lookup. Under concurrency that is either exactly right or quietly
wrong, and quietly wrong would mean lineage events attributed to the wrong
actor — worse than no attribution, because it looks like evidence (the same
argument as RAID R12).

**If these fail, that is a finding to publish, not a bug to fix quietly.**

Requires `docker compose up` in `mcp-lineage/`. Deselected by default —
`pytest -m integration` to run.
"""

from __future__ import annotations

import asyncio
import json
import urllib.request
import uuid
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from mcp_server_ol.meta import LINEAGE_META_KEY

pytestmark = pytest.mark.integration

MCP_URL = "http://localhost:8000/mcp"
MARQUEZ = "http://localhost:5000"
NAMESPACE = "mcp-lineage-demo"

CONCURRENT_CALLERS = 8


def marquez(path: str) -> Any:
    with urllib.request.urlopen(f"{MARQUEZ}{path}", timeout=15) as r:
        return json.loads(r.read())


def _identity(tag: str) -> dict[str, str]:
    return {
        "parentRunId": str(uuid.uuid4()),
        "jobNamespace": NAMESPACE,
        "jobName": f"agent-{tag}",
    }


async def _call_as(identity: dict[str, str], sql: str) -> Any:
    """One tool call over Streamable HTTP, in its own session."""
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool("execute_sql", {"sql": sql}, meta={LINEAGE_META_KEY: identity})


async def test_the_server_serves_streamable_http() -> None:
    """D13 — the transport MCP now prefers, added by wrapping upstream's entrypoint."""
    identity = _identity(f"solo-{uuid.uuid4().hex[:6]}")
    result = await _call_as(identity, "SELECT claim_id FROM obsinsure.claim LIMIT 1")

    assert not result.isError, result.content


async def test_identity_survives_the_transport() -> None:
    """Claim 2b over Streamable HTTP rather than the deprecated transport."""
    identity = _identity(f"single-{uuid.uuid4().hex[:6]}")
    await _call_as(identity, "SELECT claim_id FROM obsinsure.claim LIMIT 1")

    run = _run_for_parent(identity["parentRunId"])
    assert run is not None, "no lineage run carried the caller's identity"


async def test_concurrent_callers_are_not_confused_with_each_other() -> None:
    """**The test that could invalidate Claim 2b's evidence.**

    Eight distinct callers, each with its own lineage identity and its own
    marker in the SQL, all in flight at once against one session manager. Every
    emitted run must pair *its own* caller's identity with *its own* statement.

    A cross-over here would not be a cosmetic bug: it would mean the mechanism
    the RFC asks the MCP community to standardise does not hold under the
    conditions organisations actually deploy in.
    """
    run_marker = uuid.uuid4().hex[:6]
    callers = [
        (_identity(f"c{i}-{run_marker}"), f"probe_{run_marker}_{i}") for i in range(CONCURRENT_CALLERS)
    ]

    results = await asyncio.gather(
        *(
            _call_as(identity, f"SELECT claim_id AS {marker} FROM obsinsure.claim LIMIT 1")
            for identity, marker in callers
        )
    )
    assert all(not r.isError for r in results), [r.content for r in results if r.isError]

    events = marquez("/api/v1/events/lineage?limit=500")["events"]

    # Map each caller's SQL marker to the parent identity recorded beside it.
    seen: dict[str, set[str]] = {}
    for event in events:
        job_facets = (event.get("job") or {}).get("facets") or {}
        query = (job_facets.get("sql") or {}).get("query", "")
        parent = ((event.get("run") or {}).get("facets") or {}).get("parent") or {}
        job_name = (parent.get("job") or {}).get("name")
        if not job_name:
            continue
        for _identity_block, marker in callers:
            if marker in query:
                seen.setdefault(marker, set()).add(job_name)

    missing = [marker for _, marker in callers if marker not in seen]
    assert not missing, f"no lineage event found for markers {missing}"

    wrong = {
        marker: sorted(names)
        for identity, marker in callers
        if (names := seen[marker]) != {identity["jobName"]}
    }
    assert not wrong, (
        "caller identity crossed between concurrent requests — "
        f"Claim 2b's evidence does not hold under Streamable HTTP: {wrong}"
    )


def _run_for_parent(parent_run_id: str) -> Any:
    events = marquez("/api/v1/events/lineage?limit=500")["events"]
    for event in events:
        parent = ((event.get("run") or {}).get("facets") or {}).get("parent") or {}
        if (parent.get("run") or {}).get("runId") == parent_run_id:
            return event
    return None


# -- RAID R08 / D11: both postures, demonstrated rather than described --------

FAILCLOSED_URL = "http://localhost:8001/mcp"


async def test_fail_closed_refuses_the_call_when_lineage_cannot_be_recorded() -> None:
    """The posture a control environment asks for, against a real server.

    `mcp-server-failclosed` in compose runs the same image pointed at a
    collector that does not exist. With lineage unrecordable, the tool call is
    refused — no unrecorded read of a governed table.

    The unit tests prove the mechanism deterministically; this proves the
    deployment story, which is what a third-line reader is actually asking
    about.
    """
    identity = _identity(f"closed-{uuid.uuid4().hex[:6]}")

    async with streamable_http_client(FAILCLOSED_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "execute_sql",
                {"sql": "SELECT claim_id FROM obsinsure.claim LIMIT 1"},
                meta={LINEAGE_META_KEY: identity},
            )

    body = str(result.content)
    assert "fail closed" in body or "refused" in body or result.isError, (
        f"fail-closed server did not refuse an unrecordable interaction: {body[:300]}"
    )


async def test_fail_open_is_the_default_deployment() -> None:
    """D11 — the default stays deployable, which is the whole reason it is default."""
    identity = _identity(f"open-{uuid.uuid4().hex[:6]}")
    result = await _call_as(identity, "SELECT claim_id FROM obsinsure.claim LIMIT 1")

    assert not result.isError, result.content

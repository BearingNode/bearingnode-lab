"""R8 — demonstrable operation, answered across *both* planes (RAID D12, R11).

**This test exists because an earlier reading of R8 was wrong.**

The evidence matrix first recorded R8 as Not met, on the grounds that a lineage
store cannot report its own absences and OpenLineage therefore needs a heartbeat
mechanism it does not have. That reasoning smuggled in exactly the error R11
warns against: it asked OpenLineage to do observability's job.

D12 already answers R8, and answers it the other way round. An event that never
arrived is invisible to the lineage plane **by definition** — so the question
*"how many data interactions were not recorded?"* is not an OpenLineage question
at all. It is a software and infrastructure observability question, and it is
answerable, because:

* every tool call that reaches the database produces a **span**, whether or not
  its lineage event was ever emitted — that is the **denominator** the lineage
  store structurally lacks;
* each span carries `lineage.run_id`, so a span can be reconciled against the
  run that should exist;
* a failure to record marks the span `lineage.dropped=true` and increments
  `mcp_lineage.events.dropped`, and the collector keeps those traces regardless
  of sampling (RAID R09, D15).

So the two planes together answer what neither answers alone. That is not a
workaround for a missing OpenLineage feature — it is the separation of concerns
working as designed, and R8 is the requirement that demonstrates it.

Requires `docker compose up` in `mcp-lineage/`, including the
`mcp-server-failclosed` sibling. Deselected by default.
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

JAEGER = "http://localhost:16686"
SERVICE = "mcp-server-ol"
SPAN = "mcp.execute_sql"

# The sibling pointed at a collector that does not exist: every call here is a
# data interaction whose lineage cannot be recorded.
UNRECORDABLE_URL = "http://localhost:8001/mcp"
UNRECORDED_CALLS = 3


def _spans() -> list[dict[str, Any]]:
    url = f"{JAEGER}/api/traces?service={SERVICE}&limit=1000&operation={SPAN}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.loads(r.read())
    return [s for t in (data.get("data") or []) for s in t["spans"] if s["operationName"] == SPAN]


def _tags(span: dict[str, Any]) -> dict[str, Any]:
    return {t["key"]: t.get("value") for t in span.get("tags", [])}


def _counts() -> tuple[int, int]:
    """`(interactions, interactions whose lineage was not recorded)`."""
    spans = _spans()
    total = sum(1 for s in spans if "lineage.run_id" in _tags(s))
    dropped = sum(1 for s in spans if _tags(s).get("lineage.dropped") == "true")
    return total, dropped


async def _call_unrecordable() -> None:
    """One data interaction against the server that cannot record lineage."""
    identity = {
        "parentRunId": str(uuid.uuid4()),
        "jobNamespace": "mcp-lineage-demo",
        "jobName": f"agent-r8-{uuid.uuid4().hex[:6]}",
    }
    async with streamable_http_client(UNRECORDABLE_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.call_tool(
                "execute_sql",
                {"sql": "SELECT claim_id FROM obsinsure.claim LIMIT 1"},
                meta={LINEAGE_META_KEY: identity},
            )


async def test_every_interaction_leaves_a_span_carrying_its_lineage_run_id() -> None:
    """The denominator. Without this, "how many were not recorded?" has no basis.

    A lineage store can only count what it received. The telemetry plane counts
    what was *attempted*, which is the half that makes absence detectable.
    """
    spans = _spans()
    assert spans, "no interaction spans found — the stack has not been exercised"

    without = [s for s in spans if "lineage.run_id" not in _tags(s)]
    assert not without, (
        f"{len(without)} interaction spans carry no lineage.run_id; "
        "the denominator is incomplete and absence cannot be reconciled"
    )


async def test_an_unrecorded_interaction_is_countable_from_telemetry_alone() -> None:
    """**R8, answered.** How many data requests were made that were not recorded?

    Three interactions are driven against a server whose lineage collector does
    not exist. Nothing about them will ever appear in Marquez. The question is
    still answerable — from spans, with no reference to the lineage store.
    """
    _, dropped_before = _counts()

    for _ in range(UNRECORDED_CALLS):
        await _call_unrecordable()

    # Batch export + the collector's tail-sampling decision window.
    deadline = 60.0
    dropped_after = dropped_before
    while deadline > 0:
        _, dropped_after = _counts()
        if dropped_after - dropped_before >= UNRECORDED_CALLS:
            break
        await asyncio.sleep(3)
        deadline -= 3

    assert dropped_after - dropped_before >= UNRECORDED_CALLS, (
        f"expected at least {UNRECORDED_CALLS} interactions marked as unrecorded, "
        f"saw {dropped_after - dropped_before}. R8 depends on this being countable."
    )


async def test_the_unrecorded_traces_survive_sampling() -> None:
    """An answer that is 10% right is not an answer (RAID R09, D15).

    The collector samples at 10%. A trace recording that lineage was lost must
    not itself be sampled away — otherwise the count above is a fraction of the
    truth and reads as though most interactions were fine.
    """
    spans = _spans()
    dropped = [s for s in spans if _tags(s).get("lineage.dropped") == "true"]

    assert dropped, "no dropped-lineage traces retained; the loss signal was sampled away"
    for span in dropped:
        assert "lineage.run_id" in _tags(span), (
            "a retained loss trace must still identify the run that should have existed"
        )

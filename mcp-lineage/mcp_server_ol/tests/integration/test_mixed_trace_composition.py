"""Scenario 2b — trace composition (RAID I34, `driver/test-strategy.md`).

Flat mode's traffic is 100% governed, so every trace it produces already
qualifies for the collector's `always-keep-data-access` policy (RAID R09)
regardless of whether that policy's *per-trace* decision actually works —
there is no non-governed traffic riding along to test the contrast (RAID
R13). `driver.py --mixed` fires sessions that mix ordinary, non-governed
spans with one governed `execute_sql` span in the same trace. This test
proves the property that traffic shape can only expose: the collector keeps
the *whole* trace once one span inside it carries `lineage.run_id`, not just
that one span.

Imports and drives the real `driver/driver.py` code path rather than
reimplementing it, so this test exercises exactly what a human running
`python driver.py N --mixed` would see, not a parallel approximation of it.

Requires `docker compose up` in `mcp-lineage/`. Deselected by default —
`pytest -m integration` to run.
"""

from __future__ import annotations

import asyncio
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.integration

JAEGER = "http://localhost:16686"
DRIVER_SERVICE = "mcp-lineage-driver"
SERVER_SERVICE = "mcp-server-ol"
SESSIONS = 3

# `driver/` is a separate deliverable with its own requirements.txt, not part
# of this package — but its opentelemetry pins match mcp_server_ol/pyproject.toml
# exactly, so importing it into this test's venv rather than shelling out to a
# subprocess is safe and lets the test call the real `run_mixed()` directly.
_DRIVER_DIR = Path(__file__).resolve().parents[3] / "driver"
if str(_DRIVER_DIR) not in sys.path:
    sys.path.insert(0, str(_DRIVER_DIR))

import driver as mixed_driver  # noqa: E402  (sys.path insert must precede this)

_ORDINARY_NAMES = {name for name, _ in mixed_driver.ORDINARY_OPERATIONS}


def _traces_for(service: str, operation: str) -> list[dict[str, Any]]:
    url = f"{JAEGER}/api/traces?service={service}&limit=1000&operation={operation}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("data") or []


def _trace(trace_id: str) -> dict[str, Any]:
    url = f"{JAEGER}/api/traces/{trace_id}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.loads(r.read())
    traces = data.get("data") or []
    assert traces, f"trace {trace_id} not found in Jaeger"
    return traces[0]


def _tags(span: dict[str, Any]) -> dict[str, Any]:
    return {t["key"]: t.get("value") for t in span.get("tags", [])}


def _services(trace: dict[str, Any]) -> set[str]:
    """Service names for every span in a trace.

    Jaeger's `/api/traces/{id}` response keys service names by `processID`
    under a top-level `processes` map, not inline on each span — a span's own
    `process` key (used by some other Jaeger API shapes) is absent here.
    """
    processes = trace.get("processes", {})
    return {
        processes[s["processID"]]["serviceName"]
        for s in trace.get("spans", [])
        if s.get("processID") in processes
    }


async def test_a_mixed_trace_is_retained_whole() -> None:
    """One trace, `ORDINARY_SPANS_PER_SESSION` ordinary spans plus one
    governed span, all kept together — read back from Jaeger by `trace_id`,
    the same evidentiary standard the rest of this suite holds itself to.
    """
    before = {t["traceID"] for t in _traces_for(DRIVER_SERVICE, "session")}

    await mixed_driver.run_mixed(SESSIONS)

    # Batch export + the collector's tail-sampling decision window.
    deadline = 60.0
    after: set[str] = set()
    while deadline > 0:
        after = {t["traceID"] for t in _traces_for(DRIVER_SERVICE, "session")}
        if len(after - before) >= SESSIONS:
            break
        await asyncio.sleep(3)
        deadline -= 3

    new_trace_ids = after - before
    assert len(new_trace_ids) >= SESSIONS, (
        f"expected {SESSIONS} new session traces in Jaeger, found {len(new_trace_ids)} "
        "— either the collector dropped a mixed trace, or export did not complete in time"
    )

    for trace_id in new_trace_ids:
        trace = _trace(trace_id)
        spans = trace["spans"]
        governed = [s for s in spans if "lineage.run_id" in _tags(s)]
        ordinary = [s for s in spans if s["operationName"] in _ORDINARY_NAMES]

        assert len(governed) == 1, (
            f"trace {trace_id}: expected exactly one governed span, found {len(governed)} "
            "— the property under test is one governed span pulling the whole trace through"
        )
        assert len(ordinary) == mixed_driver.ORDINARY_SPANS_PER_SESSION, (
            f"trace {trace_id}: expected {mixed_driver.ORDINARY_SPANS_PER_SESSION} ordinary "
            f"spans, found {len(ordinary)} — some were sampled away individually, which is "
            "exactly what always-keep-data-access is supposed to prevent for this trace"
        )

        services = _services(trace)
        assert services >= {DRIVER_SERVICE, SERVER_SERVICE}, (
            f"trace {trace_id}: expected spans from both {DRIVER_SERVICE} and {SERVER_SERVICE} "
            "— the server's span must be a child of the client's governed span via the "
            "injected traceparent, not a disjoint trace that happens to share a name"
        )


async def test_no_ordinary_sibling_carries_lineage_identity() -> None:
    """The mechanism, not just the outcome: only the governed span is governed.

    If an ordinary span picked up `lineage.run_id` by accident, retention
    would prove nothing about the policy — it would just mean everything in
    the trace happened to qualify on its own merits.
    """
    traces = _traces_for(DRIVER_SERVICE, "session")
    assert traces, "no mixed-mode traces found — run this after the composition test"

    for trace in traces[-SESSIONS:]:
        ordinary = [s for s in trace["spans"] if s["operationName"] in _ORDINARY_NAMES]
        for span in ordinary:
            assert "lineage.run_id" not in _tags(span), (
                f"ordinary span {span['operationName']!r} in trace {trace['traceID']} "
                "carries lineage.run_id — it should carry none"
            )

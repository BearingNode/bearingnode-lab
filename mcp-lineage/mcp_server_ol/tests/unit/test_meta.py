"""Reading caller identity out of `_meta` (RAID D10, Claim 2b).

The absent/malformed split is RAID I29: both once returned a bare `None`, so a
caller with a broken integration was indistinguishable from the entire installed
base of clients that predate the convention.
"""

from __future__ import annotations

import logging

import pytest
from mcp.types import RequestParams

from mcp_server_ol.meta import LINEAGE_META_KEY, ParentStatus, parent_from_meta

FULL = {
    "parentRunId": "3f1d2c4e-0000-4000-8000-000000000001",
    "jobNamespace": "mcp-lineage-demo",
    "jobName": "agent-session",
    "rootRunId": "3f1d2c4e-0000-4000-8000-000000000002",
    "rootJobNamespace": "mcp-lineage-demo",
    "rootJobName": "agent-root",
}


def test_reads_identity_from_a_plain_dict() -> None:
    lookup = parent_from_meta({LINEAGE_META_KEY: FULL})

    assert lookup.status is ParentStatus.PRESENT
    assert lookup.identity is not None
    assert lookup.identity.run_id == FULL["parentRunId"]
    assert lookup.identity.job_name == "agent-session"
    assert lookup.identity.root_run_id == FULL["rootRunId"]


def test_reads_identity_off_a_parsed_meta_object() -> None:
    """`_meta` is `extra: allow`, so our key lands in `model_extra`.

    This is the mechanism the RFC points at: MCP can already carry this, it
    simply has no agreed key for it.
    """
    meta = RequestParams.Meta.model_validate({"progressToken": "p1", LINEAGE_META_KEY: FULL})

    lookup = parent_from_meta(meta)
    assert lookup.identity is not None
    assert lookup.identity.job_namespace == "mcp-lineage-demo"


def test_root_is_optional() -> None:
    minimal = {k: FULL[k] for k in ("parentRunId", "jobNamespace", "jobName")}
    lookup = parent_from_meta({LINEAGE_META_KEY: minimal})

    assert lookup.identity is not None
    assert lookup.identity.root_run_id is None


@pytest.mark.parametrize(
    ("meta", "why"),
    [
        (None, "no _meta at all"),
        ({}, "empty _meta"),
        ({"progressToken": "p1"}, "_meta without our key — every client today"),
        ({LINEAGE_META_KEY: {}}, "key wired up but populated with nothing"),
    ],
)
def test_identity_absent_is_normal_and_quiet(meta: object, why: str) -> None:
    """An unknown actor is recorded as unknown — never guessed, never faked.

    That absence *is* the gap the RFC describes, and it is the state of every
    pre-convention client, so it must not be reported as an error.
    """
    lookup = parent_from_meta(meta)

    assert lookup.identity is None
    assert lookup.status is ParentStatus.ABSENT
    assert not lookup.is_malformed


@pytest.mark.parametrize(
    ("meta", "why"),
    [
        ({LINEAGE_META_KEY: "not-a-dict"}, "wrong type entirely"),
        ({LINEAGE_META_KEY: {"parentRunId": "abc"}}, "run id without job identity"),
        ({LINEAGE_META_KEY: {"parentRunId": "abc", "jobName": "x"}}, "half a parent is not a parent"),
        ({LINEAGE_META_KEY: {"jobNamespace": "ns", "jobName": "x"}}, "job without a run"),
    ],
)
def test_identity_malformed_is_an_error_and_is_reported(
    meta: object, why: str, caplog: pytest.LogCaptureFixture
) -> None:
    """RAID I29 — a caller that *tried* and failed must not look like one that never tried.

    `ParentRunFacet` needs run *and* job, so a partial parent is still no
    parent — but the reason differs, and only this one is somebody's bug.
    """
    with caplog.at_level(logging.WARNING):
        lookup = parent_from_meta(meta)

    assert lookup.identity is None
    assert lookup.status is ParentStatus.MALFORMED
    assert lookup.is_malformed
    assert caplog.records, "a malformed identity block must be logged at WARNING"


def test_absent_and_malformed_are_distinguishable() -> None:
    """The regression this split exists to prevent, asserted directly."""
    absent = parent_from_meta({"progressToken": "p1"})
    malformed = parent_from_meta({LINEAGE_META_KEY: "garbage"})

    assert absent.identity is malformed.identity is None
    assert absent.status is not malformed.status

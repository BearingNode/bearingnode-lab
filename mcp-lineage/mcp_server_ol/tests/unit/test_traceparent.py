"""Reading an inbound `traceparent` out of `_meta` (RAID I34).

A different mechanism from `test_meta.py`'s `parent_from_meta`, on purpose:
`traceparent` is a flat, reserved MCP `_meta` key (RAID I05), not the bespoke
nested `LINEAGE_META_KEY` block that carries OpenLineage parentage. Same
absent/malformed split as `ParentStatus` (RAID I29), cloned here for
`TraceparentStatus`.
"""

from __future__ import annotations

import logging

import pytest
from mcp.types import RequestParams

from mcp_server_ol.meta import TraceparentStatus, traceparent_from_meta

# Canonical example from the W3C Trace Context spec.
VALID = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def test_reads_traceparent_from_a_plain_dict() -> None:
    lookup = traceparent_from_meta({"traceparent": VALID})

    assert lookup.status is TraceparentStatus.PRESENT
    assert lookup.context is not None


def test_reads_traceparent_off_a_parsed_meta_object() -> None:
    """`_meta` is `extra: allow`; a reserved key not declared as a named field
    still lands in `model_extra` — same mechanism `parent_from_meta` relies on.
    """
    meta = RequestParams.Meta.model_validate({"progressToken": "p1", "traceparent": VALID})

    lookup = traceparent_from_meta(meta)
    assert lookup.status is TraceparentStatus.PRESENT
    assert lookup.context is not None


@pytest.mark.parametrize(
    ("meta", "why"),
    [
        (None, "no _meta at all"),
        ({}, "empty _meta"),
        ({"progressToken": "p1"}, "_meta without traceparent — every client today"),
    ],
)
def test_traceparent_absent_is_normal_and_quiet(
    meta: object, why: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Absence is the ordinary state of a call with no inbound trace context."""
    with caplog.at_level(logging.WARNING):
        lookup = traceparent_from_meta(meta)

    assert lookup.context is None
    assert lookup.status is TraceparentStatus.ABSENT
    assert not lookup.is_malformed
    assert not caplog.records, "absence must not be logged"


@pytest.mark.parametrize(
    ("meta", "why"),
    [
        ({"traceparent": "not-a-traceparent"}, "wrong format entirely"),
        (
            {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7"},
            "too few dash-separated fields",
        ),
        (
            {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01-extra"},
            "too many dash-separated fields",
        ),
        ({"traceparent": "00-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-00f067aa0ba902b7-01"}, "non-hex trace-id"),
        ({"traceparent": "00-00000000000000000000000000000000-00f067aa0ba902b7-01"}, "all-zero trace-id"),
        ({"traceparent": "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}, "wrong version byte"),
        ({"traceparent": ""}, "empty string"),
        ({"traceparent": 12345}, "wrong type entirely"),
    ],
)
def test_traceparent_malformed_is_an_error_and_is_reported(
    meta: object, why: str, caplog: pytest.LogCaptureFixture
) -> None:
    """RAID I29's split, cloned: a caller that tried and failed must not look
    like one that never tried."""
    with caplog.at_level(logging.WARNING):
        lookup = traceparent_from_meta(meta)

    assert lookup.context is None
    assert lookup.status is TraceparentStatus.MALFORMED
    assert lookup.is_malformed
    assert caplog.records, "a malformed traceparent must be logged at WARNING"


def test_absent_and_malformed_are_distinguishable() -> None:
    """The regression this split exists to prevent, asserted directly."""
    absent = traceparent_from_meta({"progressToken": "p1"})
    malformed = traceparent_from_meta({"traceparent": "garbage"})

    assert absent.context is malformed.context is None
    assert absent.status is not malformed.status

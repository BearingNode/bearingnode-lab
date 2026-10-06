"""Reading the caller's lineage identity out of MCP `_meta`.

**This is the gap, made concrete.** RAID D10, the `_meta` parentage ask: MCP has no convention
for propagating a caller's *lineage* run and job identity. Trace context is
settled convention — instrumentations SHOULD inject `traceparent`, `tracestate`
and `baggage` into `params._meta` (RAID I05) — but nothing carries OpenLineage
parentage, and without a parent `runId` plus job namespace and name the server
cannot populate `ParentRunFacet` at all.

So we use a bespoke, reverse-DNS-prefixed key. It works: `_meta` is declared
`extra: allow`, and arbitrary keys survive parsing into `model_extra` (verified
against `mcp` 1.28.1). That is the point — the mechanism is already there, and
the missing piece is agreement on the key, which is what the planned refiling of MCP #2638
will ask for. When a standard key exists, this module changes by one constant.

Absent the key, the server emits with no parent. The actor is then recorded as
unknown rather than guessed at — that absence *is* the gap the RFC describes,
and papering over it with a placeholder would hide the finding.

**Absent and malformed are not the same thing (RAID I29).** Both once returned
a bare `None`, so an event with no parent looked identical whether the caller
sent nothing or sent garbage — and a caller that *tried* to supply identity and
failed got no signal at all. Absence is the normal condition of every
pre-convention MCP client on earth. Malformed is an error, and it is reported
as one: on the event, so the lineage consumer sees it, and as a dropped-identity
count, so the operator does. See `ParentStatus`.

**A run id that is not a UUID is malformed, and saying so here is the whole of RAID I47.**
`ParentRunFacet` validates `runId` with `uuid.UUID()`, in code, with the constraint stated
nowhere in the specification's prose. So a block carrying all three required fields with a
session string in `parentRunId` read as *supplied* here and then raised inside
`ParentIdentity.to_facet()` — which loses the entire event rather than emitting it
unparented, and counts the loss as an emission failure rather than a broken identity. That
is I29's own failure one layer down, reachable by the mistake a caller adopting this
convention for the first time is most likely to make.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from mcp_server_ol.lineage import (
    ACTOR_MALFORMED,
    ACTOR_SUPPLIED,
    ACTOR_UNKNOWN,
    ParentIdentity,
)

logger = logging.getLogger(__name__)

# Reverse-DNS prefixed, per MCP's guidance for `_meta` keys. Deliberately
# vendor-namespaced: this is a stand-in for a convention that does not exist,
# and it should be obvious in a packet capture that it is ours, not standard.
LINEAGE_META_KEY = "io.bearingnode.lineage/parent"


class ParentStatus(StrEnum):
    """Why the event does or does not carry a parent.

    The distinction is load-bearing, not bookkeeping. `ABSENT` is the expected
    state of every client that predates the convention this workstream is asking
    for — it is the gap, and it must stay quiet enough to be the normal case.
    `MALFORMED` means a caller tried and we could not read it, which is a defect
    in somebody's integration and must be loud.

    The three values are `lineage.py`'s rather than this module's, because they
    go on the wire as `lineage.actor`: the emitter owns the vocabulary
    (`TAG_VOCABULARY`) and this enum names the semantics, so the two cannot
    drift apart (RAID D26). `TraceparentStatus` below has the same shape and is
    deliberately **not** bound to them — it describes a span attribute, not a
    lineage tag, and coupling the two would make a change to one break the
    other.
    """

    PRESENT = ACTOR_SUPPLIED
    ABSENT = ACTOR_UNKNOWN
    MALFORMED = ACTOR_MALFORMED


@dataclass(frozen=True)
class ParentLookup:
    """The outcome of looking for caller identity on a request."""

    identity: ParentIdentity | None
    status: ParentStatus

    @property
    def is_malformed(self) -> bool:
        return self.status is ParentStatus.MALFORMED


ABSENT = ParentLookup(identity=None, status=ParentStatus.ABSENT)


def parent_from_meta(meta: Any) -> ParentLookup:
    """Read caller identity from a request's `_meta`.

    Never raises. Returns a `ParentLookup` rather than a bare optional so the
    caller can tell *absent* from *malformed* — see RAID I29; conflating them
    was how a broken client got no signal at all.
    """
    if meta is None:
        return ABSENT

    block = _extract(meta)
    if block is None:
        return ABSENT
    if not isinstance(block, dict):
        logger.warning(
            "lineage: %s is %s, expected an object; emitting without parent",
            LINEAGE_META_KEY,
            type(block).__name__,
        )
        return ParentLookup(identity=None, status=ParentStatus.MALFORMED)

    run_id = block.get("parentRunId")
    namespace = block.get("jobNamespace")
    name = block.get("jobName")
    root_run_id = block.get("rootRunId")
    root_namespace = block.get("rootJobNamespace")
    root_name = block.get("rootJobName")
    if not (run_id and namespace and name):
        if not block:
            # An empty object is a client wiring the key up and populating
            # nothing — closer to absent than to broken, and not worth paging on.
            return ABSENT
        missing = [
            k for k, v in (("parentRunId", run_id), ("jobNamespace", namespace), ("jobName", name)) if not v
        ]
        logger.warning(
            "lineage: %s present but missing %s; emitting without parent",
            LINEAGE_META_KEY,
            ", ".join(missing),
        )
        return ParentLookup(identity=None, status=ParentStatus.MALFORMED)

    # RAID I47. Checked here rather than left to raise at facet construction, so a bad
    # run id is reported as what it is — a broken identity — instead of costing the whole
    # event. `rootRunId` is checked only when the root triple is complete, because that is
    # exactly when `to_facet()` constructs a `Root` and so the only time its format can
    # matter; rejecting it otherwise would refuse a parent that would have worked.
    candidates = [("parentRunId", run_id)]
    if root_run_id and root_namespace and root_name:
        candidates.append(("rootRunId", root_run_id))
    not_uuid = [key for key, value in candidates if not _is_uuid(value)]
    if not_uuid:
        logger.warning(
            "lineage: %s carries a non-UUID %s; emitting without parent",
            LINEAGE_META_KEY,
            ", ".join(not_uuid),
        )
        return ParentLookup(identity=None, status=ParentStatus.MALFORMED)

    return ParentLookup(
        identity=ParentIdentity(
            run_id=str(run_id),
            job_namespace=str(namespace),
            job_name=str(name),
            root_run_id=_opt(root_run_id),
            root_job_namespace=_opt(root_namespace),
            root_job_name=_opt(root_name),
        ),
        status=ParentStatus.PRESENT,
    )


class TraceparentStatus(StrEnum):
    """Why the event does or does not carry an inbound trace context.

    Same three-state shape as `ParentStatus`, and the same reasoning: `ABSENT`
    is the ordinary condition of a call that carries no trace context at all —
    quiet. `MALFORMED` means a caller supplied `traceparent` and it did not
    parse as a valid W3C Trace Context value, which is somebody's integration
    bug and must be loud.
    """

    PRESENT = "supplied"
    ABSENT = "absent"
    MALFORMED = "malformed"


@dataclass(frozen=True)
class TraceparentLookup:
    """The outcome of looking for an inbound `traceparent` on a request."""

    context: Context | None
    status: TraceparentStatus

    @property
    def is_malformed(self) -> bool:
        return self.status is TraceparentStatus.MALFORMED


ABSENT_TRACEPARENT = TraceparentLookup(context=None, status=TraceparentStatus.ABSENT)


def traceparent_from_meta(meta: Any) -> TraceparentLookup:
    """Read an inbound W3C `traceparent` from a request's `_meta`.

    **A different mechanism from `parent_from_meta` above, on purpose.**
    `traceparent`, `tracestate` and `baggage` are reserved keys directly in
    MCP's `params._meta` — a flat key, per the spec itself (RAID I05) — not
    the bespoke, nested `LINEAGE_META_KEY` this module uses for OpenLineage
    parentage. That key exists because MCP has no convention for lineage
    parentage; this one exists because MCP already reserves it. So this reads
    `_meta["traceparent"]` as a flat string, never nested under any namespace.

    Never raises. Returns a `TraceparentLookup` rather than a bare optional so
    the caller can tell absent from malformed, mirroring `parent_from_meta`
    and RAID I29's absent/malformed split.
    """
    if meta is None:
        return ABSENT_TRACEPARENT

    value = _extract_traceparent(meta)
    if value is None:
        return ABSENT_TRACEPARENT
    if not isinstance(value, str) or not value:
        logger.warning(
            "lineage: traceparent is %s, expected a non-empty string; starting a fresh span",
            type(value).__name__,
        )
        return TraceparentLookup(context=None, status=TraceparentStatus.MALFORMED)

    extracted = TraceContextTextMapPropagator().extract(carrier={"traceparent": value})
    if not trace.get_current_span(extracted).get_span_context().is_valid:
        logger.warning(
            "lineage: traceparent %r did not parse as valid W3C Trace Context; starting a fresh span",
            value,
        )
        return TraceparentLookup(context=None, status=TraceparentStatus.MALFORMED)

    return TraceparentLookup(context=extracted, status=TraceparentStatus.PRESENT)


def _extract_traceparent(meta: Any) -> Any:
    """Pull the flat `traceparent` key off `_meta`, whichever shape it arrives in.

    Same plain-dict-vs-`model_extra` handling as `_extract()`, for the same
    reason: `_meta` is `extra: allow`, so a reserved key not declared as a
    named field on `RequestParams.Meta` still lands in `model_extra`.
    """
    if isinstance(meta, dict):
        return meta.get("traceparent")

    extra = getattr(meta, "model_extra", None)
    if isinstance(extra, dict):
        return extra.get("traceparent")

    return getattr(meta, "traceparent", None)


def _extract(meta: Any) -> Any:
    """Pull our key off `_meta`, whichever shape it arrives in.

    A plain dict when read from the raw request; `model_extra` when it has been
    parsed into `RequestParams.Meta`, which declares only `progressToken` as a
    field and puts everything else there.
    """
    if isinstance(meta, dict):
        return meta.get(LINEAGE_META_KEY)

    extra = getattr(meta, "model_extra", None)
    if isinstance(extra, dict):
        return extra.get(LINEAGE_META_KEY)

    return getattr(meta, LINEAGE_META_KEY, None)


def _is_uuid(value: Any) -> bool:
    """Whether `openlineage-python` will accept this as a run id (RAID I47).

    Tested with `uuid.UUID()` deliberately, because that is literally what the client's
    own `runId` validator calls — so this accepts exactly what the facet accepts, no
    stricter and no looser. A 32-character hex string with no dashes passes there, and
    so must pass here.
    """
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _opt(value: Any) -> str | None:
    return str(value) if value else None

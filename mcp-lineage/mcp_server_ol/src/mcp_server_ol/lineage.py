"""OpenLineage emission for MCP tool calls.

Events are built with `openlineage-python`, never hand-rolled JSON, per
this lab's own OpenLineage standard. The scaffold this replaces POSTed
dicts to Marquez directly, which is how it drifted out of spec conformance
without anyone noticing.

Three RAID decisions shape what is emitted:

**D08 — datasets are parsed intent, not observed effect.** The tables named
here are what the statement *declared* it would touch, obtained by parsing the
SQL before execution. They are not what the database actually touched. Views,
triggers, cascades, partition routing and RLS are all invisible to a parser
(R03), and the parse can be silently incomplete even for plain SQL — see
`tests/unit/test_sql_parse_completeness.py`, which reproduces that against our
own pinned parser. Every event therefore carries a tag saying so. Emitting
intent unlabelled would make this demo an instance of the problem it describes.

**D10 — `ParentRunFacet` is used for linkage only.** The caller's identity is
*not* forwarded in `parent.run.facets`, even though the 1-2-0 schema allows it,
because the pinned Marquez silently discards facets nested there (R07, I22 —
reproduce with `probes/verify_parent_facet_forwarding.py`). The spec calls
forwarding a convenience copy and points at the parent's own event as the
source of truth, so the caller emits its own run and we carry the link.

**R02 — no PII.** Nothing here reads or constructs identity. Whatever the
caller supplies is a pseudonymous reference that is passed through untouched;
resolving it to a person is somebody else's system, behind access control.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import attr
from openlineage.client import OpenLineageClient
from openlineage.client.event_v2 import Job, Run, RunEvent, RunState
from openlineage.client.facet_v2 import RunFacet, error_message_run, parent_run, sql_job, tags_run

from mcp_server_ol.naming import PostgresTarget
from mcp_server_ol.telemetry import current_trace_context

# STAND-IN. This URL is a placeholder. It is the path of the repository this work was
# developed in, which is not public, so it returns 404 for a reader of the public
# edition. It is replaced with the public repository path, at a commit, in a later
# change after the cut (RAID I57).
PRODUCER = "https://github.com/BearingNode/DIO11y-lab/tree/main/mcp-lineage"

# How the datasets on this event were arrived at. Deliberately a standard
# TagsRunFacet rather than a bespoke facet: A04 was wrong precisely because it
# proposed something new without checking what already existed.
DERIVATION_TAG = "lineage.derivation"
DERIVATION_PARSED_INTENT = "parsed-intent"
COMPLETENESS_TAG = "lineage.completeness"
COMPLETENESS_NOT_GUARANTEED = "not-guaranteed"

# RAID I29, D12 class 1: an event that is sent but incomplete must say so *on
# itself*. Without this, a statement whose parse failed emits with empty inputs
# and outputs — a run that reads in Marquez as "this touched nothing" when what
# actually happened is "we could not tell what this touched". That is a
# confidently wrong lineage graph, which is worse than a visibly partial one.
COMPLETENESS_PARSE_FAILED = "parse-failed"

# Whether the caller supplied identity, and if not, why. Absence is the normal
# pre-convention case and the gap the RFC describes; malformed is somebody's
# broken integration. An event with no parent cannot distinguish them, so the
# event carries the reason (RAID I29).
ACTOR_TAG = "lineage.actor"
ACTOR_SUPPLIED = "supplied"
ACTOR_UNKNOWN = "absent"
ACTOR_MALFORMED = "malformed"

# The vocabulary, closed for this producer. REQ11 is the requirement these three
# keys serve and RAID D26 defines them. They are closed here, in code, rather
# than only described in prose.
#
# They stay free-form *on the wire*: `TagsRunFacet` is free-form by design,
# OpenLineage defines no key vocabulary for it, and we are not asking it to —
# the tags are deliberately not part of the ask (see `README.md` § Impact on the
# standards and their communities). Closing them here means a fourth value
# cannot arrive unnoticed: it has to be added to this mapping, which fails
# `tests/unit/test_tag_vocabulary.py` until the vocabulary is changed
# deliberately, and the register entry is updated with it.
#
# `lineage.derivation` carries one value today and so carries no information.
# That is the position, not an oversight: D08 and D26 place this implementation
# at *parsed intent* on a three-point scale, and the other two positions —
# plan-derived and observed-effect — are both out of reach for Postgres. The
# single value is what makes the scale's existence legible to a consumer.
TAG_VOCABULARY: dict[str, frozenset[str]] = {
    DERIVATION_TAG: frozenset({DERIVATION_PARSED_INTENT}),
    COMPLETENESS_TAG: frozenset({COMPLETENESS_NOT_GUARANTEED, COMPLETENESS_PARSE_FAILED}),
    ACTOR_TAG: frozenset({ACTOR_SUPPLIED, ACTOR_UNKNOWN, ACTOR_MALFORMED}),
}

# RAID D15: the trace that produced this event is part of the control record,
# not corroboration. Third line starts from the lineage graph — "which agent
# interactions touched this table?" — and must be able to reach the trace that
# supplies the decisioning context. The lineage event says the data was
# sampled; the trace says what the agent then did with it, and the control
# failure lives between the two.
#
# **There is no standard facet for this.** Verified against the OpenLineage spec
# at 1.52.0-9-g2aae49d8b, and again at 1.53.0 on 2026-10-06: no facet in
# `spec/facets/` references `traceId` or `trace_id`. `ExternalQueryRunFacet` carries
# external *query* identifiers and `ParentRunFacet` carries lineage parentage;
# neither carries trace context. So this is a bespoke facet under our own vendor
# prefix, and — exactly like the `_meta` key in `meta.py` — its being bespoke *is* the ask. The ask itself
# is not yet posted: OpenLineage #4484 asks the open question.
TRACE_CONTEXT_FACET = "bearingnode_traceContext"
# STAND-IN. This URL is a placeholder. The schema document it names has not been
# written, and it does not resolve (RAID I56). The specification requires an
# immutable, versioned pointer, so the real value is a schema committed to the
# public repository and referenced at a commit or tag. It is not specified yet.
TRACE_CONTEXT_SCHEMA = "https://bearingnode.com/schemas/traceContext.json"


@attr.define
class TraceContextRunFacet(RunFacet):
    """W3C trace context naming the span that initiated this run.

    **Bespoke, and that is the ask.** No facet in the OpenLineage spec carries
    trace context — re-verified 2026-09-30 against the shipped client at
    `1.53.0`, the current release: no run facet in
    `openlineage.client.generated` carries a trace or span, including in the
    explicit-lineage module added since `1.52.0`. `ExternalQueryRunFacet`
    carries external *query* identifiers; `ParentRunFacet` carries lineage
    parentage. Neither is this.

    **This facet carries provenance, not composition — the distinction is the
    proposal, and conflating them is what invited the cardinality objection.**
    Two separate facts want a trace reference on a run, and they have different
    cardinality by nature:

    - **Provenance** — *the span that caused this run to exist.* **Singular by
      construction**, whatever the surrounding job does. `ParentRunFacet` is the
      precedent: it names *a* parent, not every ancestor. **This facet is
      provenance**, and `emit()` implements it by capturing
      `current_trace_context()` at the point of emission.
    - **Composition** — *the spans a run consists of.* **1:N by nature.** A
      long-running job spanning many traces needs this. **This facet does not
      carry it and should not.**

    **This is a correlation reference, not telemetry.** The distinction is
    load-bearing and is the response to the scope objection an OpenLineage
    maintainer raised on
    [#4588](https://github.com/OpenLineage/OpenLineage/issues/4588) — that
    OpenLineage is not a monitoring tool. Agreed, and this does not make it one:
    it is a pointer, carrying no metrics, no per-record granularity and no
    monitoring semantics.

    **What distinguishes this ask from #4588 is the kind of claim, not
    cardinality.** An earlier version of this docstring rested it on 1:1 — one
    tool call, one run, one trace — which is true in the scoped case and was the
    wrong thing to lean on: the moment the gap claim generalises beyond MCP it
    inherits the general case's cardinality. A provenance pointer is not a work
    record, and that holds however many traces the surrounding job spans.
    #4588 was reaching for **composition**, which is why it drew a granularity
    objection; that objection does not reach provenance.

    The ask to standardise this is our proposed answer to the open question at
    OpenLineage #4484, not yet posted there (RAID D15, D22, A19). Raised at the
    OpenLineage TSC 2026-09-30 and reframed there.
    """

    traceId: str  # noqa: N815 - OpenLineage facet fields are camelCase on the wire
    spanId: str  # noqa: N815

    @staticmethod
    def _get_schema() -> str:
        return TRACE_CONTEXT_SCHEMA


@dataclass(frozen=True)
class ParentIdentity:
    """The calling agent's run and job, as supplied by the caller.

    The server does not invent this and cannot derive it — that is the whole
    of D01. Absent this, the event is emitted with no parent and the actor is
    simply unknown, which is the gap the RFC describes rather than something
    to paper over with a placeholder.
    """

    run_id: str
    job_namespace: str
    job_name: str
    root_run_id: str | None = None
    root_job_namespace: str | None = None
    root_job_name: str | None = None

    def to_facet(self) -> parent_run.ParentRunFacet:
        root = None
        if self.root_run_id and self.root_job_namespace and self.root_job_name:
            root = parent_run.Root(
                run=parent_run.RootRun(runId=self.root_run_id),
                job=parent_run.RootJob(namespace=self.root_job_namespace, name=self.root_job_name),
            )
        return parent_run.ParentRunFacet(
            run=parent_run.Run(runId=self.run_id),
            job=parent_run.Job(namespace=self.job_namespace, name=self.job_name),
            root=root,
            producer=PRODUCER,
        )


@dataclass(frozen=True)
class ParsedStatement:
    """What the parser reported about one statement, before it ran.

    `parse_error` carries the distinction that matters: empty `inputs` and
    `outputs` because the statement genuinely touched no table, versus empty
    because the parse failed. The first is a fact; the second is an absence of
    facts, and an event that cannot tell them apart misleads (RAID I29).
    """

    sql: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    parse_error: str | None = None

    @property
    def parse_failed(self) -> bool:
        return self.parse_error is not None


def _now() -> str:
    return datetime.now(UTC).isoformat()


class LineageEmitter:
    """Emits one OpenLineage run per SQL statement executed by a tool call."""

    def __init__(
        self,
        client: OpenLineageClient,
        target: PostgresTarget,
        *,
        job_namespace: str,
        default_schema: str = "public",
    ) -> None:
        self._client = client
        self._target = target
        self._job_namespace = job_namespace
        self._default_schema = default_schema

    def new_run_id(self) -> str:
        return str(uuid.uuid4())

    # -- event construction -------------------------------------------------

    def _datasets(self, names: tuple[str, ...]) -> list[dict[str, str]]:
        return [
            {
                "namespace": self._target.namespace,
                "name": self._target.dataset_name(n, default_schema=self._default_schema),
            }
            for n in names
        ]

    def _run(
        self,
        run_id: str,
        parent: ParentIdentity | None,
        *,
        statement: ParsedStatement | None = None,
        actor_status: str = ACTOR_UNKNOWN,
        error: str | None = None,
    ) -> Run:
        completeness = (
            COMPLETENESS_PARSE_FAILED
            if statement is not None and statement.parse_failed
            else COMPLETENESS_NOT_GUARANTEED
        )
        tags = [
            tags_run.TagsRunFacetFields(
                key=DERIVATION_TAG,
                value=DERIVATION_PARSED_INTENT,
                source="INTEGRATION",
            ),
            tags_run.TagsRunFacetFields(
                key=COMPLETENESS_TAG,
                value=completeness,
                source="INTEGRATION",
            ),
            tags_run.TagsRunFacetFields(
                key=ACTOR_TAG,
                value=actor_status,
                source="INTEGRATION",
            ),
        ]
        facets: dict[str, object] = {"tags": tags_run.TagsRunFacet(tags=tags, producer=PRODUCER)}

        # D15: the trace is the other half of the control record. The lineage
        # event says the data was reached; the trace says what the agent asked,
        # chose and did with it. Third line need to replay both, and they start
        # from the lineage graph — so the pointer has to be on this end too.
        trace_context = current_trace_context()
        if trace_context is not None:
            trace_id, span_id = trace_context
            facets[TRACE_CONTEXT_FACET] = TraceContextRunFacet(
                traceId=trace_id, spanId=span_id, producer=PRODUCER
            )

        if parent is not None:
            facets["parent"] = parent.to_facet()
        if error is not None:
            facets["errorMessage"] = error_message_run.ErrorMessageRunFacet(
                message=error, programmingLanguage="SQL", producer=PRODUCER
            )
        return Run(runId=run_id, facets=facets)  # type: ignore[arg-type]

    def _job(self, job_name: str, sql: str) -> Job:
        return Job(
            namespace=self._job_namespace,
            name=job_name,
            facets={"sql": sql_job.SQLJobFacet(query=sql, dialect="postgres", producer=PRODUCER)},
        )

    def _event(
        self,
        state: RunState,
        run_id: str,
        job_name: str,
        statement: ParsedStatement,
        parent: ParentIdentity | None,
        *,
        actor_status: str = ACTOR_UNKNOWN,
        error: str | None = None,
    ) -> RunEvent:
        return RunEvent(
            eventType=state,
            eventTime=_now(),
            run=self._run(run_id, parent, statement=statement, actor_status=actor_status, error=error),
            job=self._job(job_name, statement.sql),
            inputs=self._datasets(statement.inputs),  # type: ignore[arg-type]
            outputs=self._datasets(statement.outputs),  # type: ignore[arg-type]
            producer=PRODUCER,
        )

    # -- lifecycle ----------------------------------------------------------

    def start(
        self,
        run_id: str,
        job_name: str,
        statement: ParsedStatement,
        parent: ParentIdentity | None,
        actor_status: str = ACTOR_UNKNOWN,
    ) -> None:
        """Emitted *before* execution, so a crash mid-statement still leaves a record."""
        self._client.emit(
            self._event(RunState.START, run_id, job_name, statement, parent, actor_status=actor_status)
        )

    def complete(
        self,
        run_id: str,
        job_name: str,
        statement: ParsedStatement,
        parent: ParentIdentity | None,
        actor_status: str = ACTOR_UNKNOWN,
    ) -> None:
        self._client.emit(
            self._event(RunState.COMPLETE, run_id, job_name, statement, parent, actor_status=actor_status)
        )

    def fail(
        self,
        run_id: str,
        job_name: str,
        statement: ParsedStatement,
        parent: ParentIdentity | None,
        actor_status: str,
        error: str,
    ) -> None:
        """A failed statement still emits a terminal event.

        Untested, this regresses into "no terminal event", which a consumer
        cannot distinguish from the event loss this whole demonstration is
        about.
        """
        self._client.emit(
            self._event(
                RunState.FAIL, run_id, job_name, statement, parent, actor_status=actor_status, error=error
            )
        )

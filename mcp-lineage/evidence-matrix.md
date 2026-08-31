# Evidence matrix: what this implementation actually proves

<!-- build: d893ccd49cb01f28 -->

## TL;DR

**What this is.** A scorecard against the ten requirements in
[`REQUIREMENTS.md`](REQUIREMENTS.md), built on the same discipline a model
benchmark table needs to be credible: the benchmarks were **named in advance**,
the method **reproduces**, and the **failures are in the table**.

**The score: four met, six partially met, none unmet.**

| Met ✅ | Partially met 🟡 |
|---|---|
| REQ1 Durability | REQ3 Actor identity — no authority model |
| REQ2 Asset identity | REQ4 Privacy — principle, not enforcement |
| REQ6 Declared, not inferred | REQ5 Derivation — agent-side unrecorded |
| REQ7 Survives the actor | REQ8 Demonstrable operation — countable, not continuous |
| | REQ9 Fitness at decision — no consumer at decision time |
| | REQ10 Reconstructable context — link built, retention parity not |

**Not all green is the same green.** Every row carries an evidence class. Class
**A** means the claim was read back out of Marquez or Jaeger over HTTP after the
session closed, so it survives leaving our process. Class **C** means we
asserted it in-process, which proves our code does what we think and nothing
about whether a consumer can read it. Seven of the ten rows are class A.

**The finding the prose had not produced.** Read down the unmet halves and they
sort into three kinds, which is more useful than a count:

- **Missing a convention, not a mechanism** — REQ3's authority model, REQ10's
  standard trace-context facet. **No implementation can close either**, because
  what is absent is community agreement. That is this workstream's whole thesis,
  arriving from the evidence side.
- **Ours to close** — REQ4's enforcement, REQ9's decision-time consumer, REQ8's
  continuity. Ordinary engineering, needing nothing from anybody else.
- **Nobody's today** — REQ5's agent-side derivation. Nothing anywhere observes
  what an agent does with rows once they leave the server.

**One verdict was wrong and the error is left visible.** REQ8 first read Not met,
by asking OpenLineage to do observability's job — the exact confusion this
workstream argues against, made by its own authors. The row records it.

**Bounds.** Structured data reached through SQL, over MCP, against Postgres.
See § *What we deliberately do not claim* at the foot before quoting any of this.

**Naming.** **REQ1–REQ10** are requirements. RAID uses `Rnn` for **risks**; the
two are unrelated.

---

**Status:** 2026-07-28, REQ8 corrected on review. Generated against commit `43b2f2e`+.
**Companion to:** [`REQUIREMENTS.md`](REQUIREMENTS.md), holding the ten
requirements this matrix tests, and [`README.md`](README.md), the technical
statement.
**RAID:** I25.

---

## Why this document exists, and how to read it

When an open-weights model ships, it ships with a benchmark table. What makes
that table credible is not the scores. It is that somebody **named the benchmarks
in advance**, the method **reproduces**, and the **failures appear in the table**.

This applies the same discipline to a governance claim. `REQUIREMENTS.md` states
ten requirements for observability of AI interaction with data. This document
says, for each one, what we built, what test proves it, how strong that evidence
is, and, where the implementation does not meet the requirement, that it does
not meet it.

**A matrix with ten green rows would be marketing.** Four of the rows below are
Met and six are Partially met, with the unmet half named in each case.

**One row has already changed.** REQ8 first read Not met, on reasoning that turned
out to instance the very confusion this workstream argues against. It now reads
Partially met, and the row keeps the original error rather than dropping it.

### Verdicts

| | Meaning |
|---|---|
| ✅ **Met** | Satisfied within the stated scope, with evidence |
| 🟡 **Partially met** | Satisfied in part; the unmet part is named |
| ❌ **Not met** | Not satisfied. Recorded rather than reworded |
| ⬜ **Untested** | Believed to hold; nothing demonstrates it |

### Evidence classes

Not all green is the same green. Every row carries a label:

| | Meaning |
|---|---|
| **A — read back from the store** | Asserted against Marquez or Jaeger over HTTP, after the fact. The claim survives leaving our process |
| **B — live stack** | Exercised against the running compose stack end to end |
| **C — unit** | Asserted in-process against the object we constructed |
| **D — none** | No automated test |

Class A is the only class that proves a third party can use the record, which is
what every requirement here ultimately concerns. Class C proves our code does
what we think. It does not prove a consumer can read it.

### Scope, before you read any row

**Structured data reached through SQL, over MCP, against Postgres.** Non-SQL
query languages and unstructured data fall outside scope, and they are not merely
untested. See `REQUIREMENTS.md` § 11 and RAID D16/R12. That bounds every verdict
below.

### Reproducing any of it

```bash
cd mcp-lineage
docker compose up -d --build          # six services + the fail-closed sibling
cd mcp_server_ol
uv sync
uv run pytest                          # unit
uv run pytest -m integration           # requires the stack above
```

Each row gives its commands in full. **85 unit (84 pass, 1 deliberate `xfail` —
RAID A06) + 19 integration tests** pass at the commit above, verified against
the live stack 2026-08-23. Ruff and mypy are clean.

---

## The matrix

### REQ1 — Durability ✅ Met · Evidence A

> Every interaction between an actor and a governed data resource produces a
> durable record.

**Built.** A `SqlDriver` subclass emits an OpenLineage run around every
statement: START before execution, COMPLETE or FAIL after. Emitting START before
execution is deliberate. A process killed mid-statement still leaves a record
that something reached the database.

**Proven by** reading the run back out of Marquez after the MCP session closes:

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_a_tool_call_produces_a_lineage_run
uv run pytest tests/unit/test_driver.py::test_start_is_emitted_before_execution
uv run pytest tests/unit/test_lineage.py::test_failure_emits_a_terminal_event_with_the_error
```

**Bounded by:** durability of the record beyond emission is the lineage store's
property, not ours. We show the record exists and retrieves. We show no
particular retention.

---

### REQ2 — Asset identity ✅ Met · Evidence A

> The record identifies the data asset canonically, in a form that joins across
> producers and across time.

**Built.** `naming.py` derives `postgres://{host}:{port}` and
`{database}.{schema}.{table}` from the server's own DSN rather than from the SQL
text, so naming stays correct even where the parse comes back incomplete. This
replaced a non-conformant scheme in the original scaffold (RAID I16).

**Proven by** asserting the namespace and name as Marquez returns them:

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_dataset_is_named_per_the_openlineage_convention
uv run pytest tests/unit/test_naming.py
```

**Bounded by:** a dataset gets a canonical name only if the parser found it. See
REQ5.

---

### REQ3 — Actor identity and authority 🟡 Partially met · Evidence A

> The record identifies the initiating actor and the authority under which it
> acted.

**Identity: demonstrated, using a name that does not exist yet.** The caller
supplies its lineage run and job in MCP `_meta`, and the server links them via
`ParentRunFacet`. `_meta` is `extra: allow`, so arbitrary keys survive, and the
mechanism is already there. **We use a bespoke reverse-DNS key because no agreed
key exists, and that is precisely the ask** (RAID D10, Claim 2b).

**Authority model: not built.** `REQUIREMENTS.md` § 3a turns on the distinction
between an agent acting **on behalf of** a human and one acting **autonomously**.
Nothing in the emitted record carries that distinction. OpenLineage's ownership
URN vocabulary has no agent type and no authority model (RAID A03, D05, D10
Claim 2a). This is the single largest unmet part of the implementation.

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_caller_identity_survives_the_round_trip
uv run pytest -m integration tests/integration/test_streamable_http.py::test_concurrent_callers_are_not_confused_with_each_other
uv run pytest tests/unit/test_meta.py
```

**Also proven:** a call *without* identity records the actor as unknown rather
than inventing one, and a *malformed* identity stays distinguishable from an
absent one. The gap becomes observable instead of papered over (RAID I29).

---

### REQ4 — Privacy by construction 🟡 Partially met · Evidence C

> Actor identity in the record is a pseudonymous reference. Resolution to a
> person stays in a separate, access-controlled system.

**Built as a design principle.** Nothing in the emitter reads or constructs
identity. Whatever the caller supplies passes through untouched, and the server
never resolves, enriches or looks anything up.

**Not enforced, and this is an honest gap.** A caller that puts an email address
in `jobName` will see it emitted to Marquez. No validation exists, no rejection
exists, and **no test asserts that the server refuses PII**, because no such
behaviour exists. RAID R02 states the principle and the architecture makes
compliance easy. It does not make violation impossible.

```bash
uv run pytest tests/unit/test_meta.py::test_reads_identity_from_a_plain_dict
```

**To close it** needs a validation policy at the emission boundary. Not built,
and deliberately not faked for this matrix.

---

### REQ5 — Derivation 🟡 Partially met · Evidence A

> Derived data carries its derivation: the transform applied, the inputs it
> consumed, and any truncation, filtering or sampling that limits the validity
> of the result.

**Server-side: recorded.** `SQLJobFacet` carries the statement, so the record
shows a `LIMIT`. Inputs and outputs come from parsing that statement.

**Agent-side: not recorded, and not recordable from here.** Nothing observes what
the agent does with the rows after they leave the server: the aggregation, the
framing, the figure it reports. This is the failure in `REQUIREMENTS.md` § 5's
worked example, and it is why REQ10 exists.

**And the server-side half is intent, not effect.** Datasets are what the
statement *declared* it would touch. A parser cannot see views, triggers,
cascades, partition routing or row-level security (RAID R03, D08). Every event
says so with a `lineage.derivation=parsed-intent` tag, and a parse that fails
carries a `parse-failed` tag rather than emitting empty datasets that would read
as "touched nothing".

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_run_declares_its_datasets_are_intent
uv run pytest -m integration tests/integration/test_end_to_end.py::test_a_failed_parse_is_readable_off_the_event_in_marquez
uv run pytest tests/unit/test_sql_parse_completeness.py
```

**A strict xfail captures the parser's own incompleteness**, reproducing a real
upstream bug against our pinned version, so the suite fails loudly when somebody
fixes it rather than silently carrying a stale claim (RAID A06).

---

### REQ6 — Declared, not inferred ✅ Met · Evidence C

> The entity performing the action produces the record, at the time it acts.
> Provenance reconstructed after the fact from an indirect artefact is
> inference, and inference is not evidence.

**Built.** Emission happens inside the process that executes the statement. We
considered an instrumenting proxy and rejected it (RAID D02) precisely because
parsing traffic from outside makes an observer guess about someone else's action.

```bash
uv run pytest tests/unit/test_driver.py::test_start_is_emitted_before_execution
uv run pytest tests/unit/test_driver.py::test_datasets_come_from_the_parsed_sql
```

**Note the honest tension:** we parse SQL, which is itself a derivation. The
distinction D02 draws concerns *who declares*, not *how they know*. This is the
acting process declaring its own behaviour, imperfectly and labelled as such
(REQ5), rather than an outsider inferring it.

---

### REQ7 — Survives the actor ✅ Met · Evidence A

> The record outlives the agent, the session, and the deployment. Ephemeral
> actors must not produce ephemeral accountability.

**Proven structurally by how we wrote the tests.** Every integration assertion
runs *after* the MCP session closes. The client context manager exits, then the
test fetches the record from Marquez over HTTP. The test reads the record from a
system that knows nothing of the session that produced it.

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py
```

**Bounded by:** nothing demonstrates "outlives the deployment". The lineage store
persists independently, but no test tears down and rebuilds the stack to prove
it.

---

### REQ8 — Demonstrable operation 🟡 Partially met · Evidence A

> Somebody can show the control was *operating* over a period, not merely that
> it existed. Third line must be able to test it.

> **⚠️ This row was wrong in the first version of this matrix, and the correction
> stands here.** It read **Not met**, arguing that a lineage store cannot report
> its own absences and that OpenLineage therefore needs a heartbeat mechanism it
> lacks, proposed as a candidate upstream ask. That reasoning smuggled in exactly
> the error RAID R11 warns against: it asked OpenLineage to do observability's
> job. The correction stays on the record rather than quietly replacing it.

**REQ8 is not an OpenLineage question.** D12 already answers it, from the other
side. An event that never arrived is invisible to the lineage plane *by
definition*. So *"how many data interactions went unrecorded?"* belongs to
software and infrastructure observability, and it has an answer there:

- **The denominator exists.** Every tool call that reaches the database produces
  a span carrying `lineage.run_id`, whether or not anything emitted its lineage
  event. That is precisely the count a lineage store structurally cannot hold.
- **The gap counts.** A failure to record marks the span `lineage.dropped=true`
  and increments `mcp_lineage.events.dropped`.
- **The count is not a fraction.** The collector retains loss-bearing traces
  regardless of the 10% sample, so sampling cannot remove the answer
  (RAID R09, D15).

**Demonstrated** by driving interactions against a server whose collector does
not exist, and answering the question from Jaeger alone, with no reference to
Marquez:

```bash
uv run pytest -m integration tests/integration/test_demonstrable_operation.py
```

**So the two planes together answer what neither answers alone**, which is the
separation of concerns working as designed rather than a workaround for a missing
feature. REQ8 is the requirement that demonstrates D12 rather than the one that
defeats it.

**Still partial, for two reasons that concern period rather than mechanism:**

1. **Point-in-time, not continuous.** The reconciliation answers "how many
   interactions in this window went unrecorded". It does not yet show the control
   *operating over a period*: no retention policy, no scheduled assertion,
   nothing an auditor could sample across a quarter.
2. **Nothing detects a silent emitter.** If the instrumented server stops
   receiving calls entirely, or somebody deploys it without the instrumentation,
   both planes go quiet together, and quiet looks identical to healthy. Closing
   that needs a liveness signal from the emitter, an ordinary observability
   concern that sits squarely on the telemetry plane.

**To close it** takes deployment and policy work on the software-observability
side: retain the reconciliation over the audit period, alert on the drop counter,
and assert emitter liveness. None of it needs anything from OpenLineage.

### REQ9 — Fitness at the point of decision 🟡 Partially met · Evidence B

> Where an AI-produced figure informs a decision, somebody must be able **at that
> moment** to establish what produced it and whether that derivation was sound.

**The precondition holds.** The record exists *at execution time*, not on a
reporting cycle, which is the property platform audit lacks. Snowflake's
`ACCESS_HISTORY` documents a latency of up to 180 minutes (`REQUIREMENTS.md`
§ 2a). Emission is synchronous with the interaction.

**Nothing consumes it at decision time.** No interface answers "is this figure
sound?" for the person about to act on it. The evidence is available. The
*fitness judgement* is not built, and the agent itself has no way to ask.

```bash
uv run pytest -m integration tests/integration/test_streamable_http.py::test_identity_survives_the_transport
```

**This is the requirement that separates governance from forensics**, and the
implementation currently sits on the forensics side of the line.

---

### REQ10 — Reconstructable context 🟡 Partially met · Evidence A

> From the record of a data interaction, somebody can reach the context that
> produced it. The link must run in both directions and **both records must
> survive**.

**Link: built and demonstrated in both directions.** The span carries
`lineage.run_id`, and the lineage event carries a `traceContext` run facet with
W3C `traceId` and `spanId`. Verified surviving Marquez ingestion, which was not
safe to assume: the same probe found Marquez silently discarding facets nested
under `parent` (RAID R07).

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_trace_reference_survives_marquez_ingestion
uv run pytest tests/unit/test_observability.py::test_the_link_between_the_two_records_is_bidirectional
uv run pytest tests/unit/test_observability.py::test_the_trace_facet_is_a_pointer_and_carries_no_telemetry
```

**Survival: half done.** The collector keeps every trace carrying a lineage
correlation, regardless of the 10% sample: 20 of 20 data-access traces retained
where probabilistic sampling would have kept about two. **Retention parity is not
implemented.** If the lineage store holds records for years and the tracing
backend for days, every reference older than a few days dangles by expiry instead
of by sampling. That is deployment configuration, RAID D15 states it as a
recommendation, and nothing here tests or enforces it.

**And the facet is bespoke.** No OpenLineage facet carries trace context,
verified against the specification at `1.52.0-9-g2aae49d8b`. The RFC asking for
one is filed at [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484).

---

## What the suite proves that no single standard proves

The requirement rows above score one at a time. Read that way they under-state
the result, because **no one of the three standards answers the governance
question.** The joins between them answer it, and the joins are where every
remaining gap sits.

This is the `aigov != aio11y` argument in test form. Governance says what should
happen. Observability shows what is happening. And for an agent reaching governed
data, *showing what is happening* takes three standards converging:

| Plane | Standard | Contributes | Answers |
|---|---|---|---|
| **Software & infrastructure** | OpenTelemetry | Span per interaction, the decisioning context, the **denominator** | *Did it happen? What surrounded it? What went unrecorded?* |
| **Protocol** | MCP | Caller identity across the call boundary, via `_meta` | *Who asked?* |
| **Data & information** | OpenLineage | Canonical dataset identity, intent, completeness | *What did it touch?* |

Each is authoritative for its own half and silent on the others. **AI governance
that rests on any one of them is policy and hope with a dashboard attached.**

### The three joins, and the test that demonstrates each

**Join 1: protocol identity becomes lineage attribution.** The caller's run and
job travel in `_meta` and arrive as `ParentRunFacet` on the lineage event. This
makes a data interaction attributable to an actor rather than to a connection.

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_caller_identity_survives_the_round_trip
uv run pytest -m integration tests/integration/test_streamable_http.py::test_concurrent_callers_are_not_confused_with_each_other
```

*Gap it exposes:* no agreed `_meta` key exists. Ours carries a vendor prefix on
purpose. RAID D10, Claim 2b.

**Join 2: the lineage record and the decisioning context reference each other.**
The span carries `lineage.run_id`, and the event carries `traceId` and `spanId`.
Either record reaches the other, which makes replay possible. The lineage event
shows a `LIMIT` applied, and the trace shows what somebody then did with the
result.

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_trace_reference_survives_marquez_ingestion
uv run pytest tests/unit/test_observability.py::test_the_link_between_the_two_records_is_bidirectional
```

*Gap it exposes:* no OpenLineage facet carries trace context. Ours is bespoke,
and the RFC in this folder asks for a standard one.

**Join 3: telemetry supplies the denominator lineage structurally lacks.** A
lineage store can report only what it received. The span exists whether or not
anything emitted the event, so *"how many interactions went unrecorded?"* has an
answer from the telemetry plane alone.

```bash
uv run pytest -m integration tests/integration/test_demonstrable_operation.py
```

*Gap it exposes:* none in the standards. This one is a **design discipline**:
route each failure to the plane that can see it (RAID D12), and do not ask either
standard to do the other's job (R11).

### What this means for the three communities

Each of MCP, OpenTelemetry and OpenLineage has, reasonably and independently,
declined the seam from its own side. OpenTelemetry ruled lineage with context
propagation out of scope. An OpenLineage maintainer ruled that OpenLineage is not
a monitoring tool. MCP closed the question as insufficiently mapped to its
concepts (RAID A08).

Every one of those positions is defensible alone. **Together they leave the
governance question owned by nobody**, and it is the question a regulator, a CRO
and a board are all going to ask about autonomous agents.

The convergence needed is small and specific: an agreed `_meta` key, a standard
trace-context facet, and an authority model that separates an agent acting on
behalf of a person from one acting alone. Three narrow additions. This suite is
what they look like when somebody builds them anyway.

### What this suite does *not* cover: the LLM plane

Stated plainly, because readers often take "AI observability" to mean model
telemetry, and this is not that.

The suite covers **software and infrastructure observability** and **data and
information observability**, joined by the protocol. It does **not** instrument
the model: no prompts, completions, token accounting, tool-selection reasoning or
model-behaviour signals. That plane belongs to OpenTelemetry's GenAI semantic
conventions, and it is where the *caller* in Join 1 lives.

**It falls outside scope because we assume it present, and the assumption is on
the record** (RAID A09). Those conventions exist, develop alongside the MCP
conventions in the same repository, and run in production today. The join needs
no new mechanism either. A trace consists of spans, so the agent's GenAI spans
and the server's `mcp.execute_sql` span belong to **one trace** and meet without
anybody inventing anything. We expect the caller identity arriving in `_meta` to
come from that already-instrumented runtime.

Two caveats travel with the assumption, stated rather than buried. The GenAI
conventions carry stability **`development`**, so attribute names will move. What
we assume is that the plane is *instrumented and adopted*, not that its
vocabulary has settled. And if an estate has *not* instrumented its agent
runtime, the gap this workstream describes does not change, but the caller half
of the demonstration has nothing on the other end of the link.

**Three planes. This workstream evidences two of them and the seam between them,
and names its dependency on the third.**

---

## Summary

| Requirement | Verdict | Evidence |
|---|---|---|
| REQ1 Durability | ✅ Met | A |
| REQ2 Asset identity | ✅ Met | A |
| REQ3 Actor identity and authority | 🟡 Partially met — no authority model | A |
| REQ4 Privacy by construction | 🟡 Partially met — principle, not enforcement | C |
| REQ5 Derivation | 🟡 Partially met — agent-side unrecorded; server-side is intent | A |
| REQ6 Declared, not inferred | ✅ Met | C |
| REQ7 Survives the actor | ✅ Met | A |
| REQ8 Demonstrable operation | 🟡 Partially met — countable, not yet continuous | A |
| REQ9 Fitness at the point of decision | 🟡 Partially met — no consumer at decision time | B |
| REQ10 Reconstructable context | 🟡 Partially met — link built, retention parity not | A |

**Four met, six partially met, none unmet**, all within the structured and SQL
scope, and one of those verdicts corrected during review (REQ8).

### What the gaps have in common

Read down the unmet halves and they sort into three kinds, which is more useful
than a count.

**Missing a convention, not a mechanism.** REQ3's authority model and REQ10's
standard trace-context facet. No implementation can close either, because what is
absent is community agreement. That is the workstream's whole argument, arriving
from the evidence side rather than the argument side, and it is what the drafts
in this folder ask for.

**Ours to close, and not yet closed.** REQ4's enforcement, REQ9's decision-time
consumer, and REQ8's continuity. All three are ordinary engineering, and none needs
anything from anybody else.

**Nobody's today.** REQ5's agent-side derivation. Nothing anywhere observes what an
agent does with rows after they leave the server.

**And REQ8 is the instructive one.** It looked like the first kind and turned out to
be the second: a requirement met by combining the two planes, which read as a gap
only while we conflated them. The mistake stays visible above, because it is the
same mistake the argument warns readers about.

### What we deliberately do not claim

- Any platform other than Snowflake, examined (`REQUIREMENTS.md` § 2a).
- Anything outside structured SQL (§ 11).
- That fail-closed is the correct posture. We demonstrate both and argue for
  neither (RAID D11, R08).
- That parsed intent equals observed effect. It does not, and every event says
  so.

---

*Regenerate the counts before publishing: `uv run pytest -q` and
`uv run pytest -q -m integration`. A matrix that has drifted from its suite is
worse than no matrix.*

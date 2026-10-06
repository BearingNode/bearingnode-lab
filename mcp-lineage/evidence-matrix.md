# Evidence matrix: what this implementation actually proves

<!-- build: d893ccd49cb01f28 -->

## TL;DR

**What this is.** A scorecard against the eleven requirements in
[`REQUIREMENTS.md`](REQUIREMENTS.md), built on the same discipline a model
benchmark table needs to be credible: the benchmarks were **named in advance**,
the method **reproduces**, and the **failures are in the table**.

**The score: two met, nine partially met, none unmet.**

| Met ✅ | Partially met 🟡 |
|---|---|
| REQ2 Asset identity | REQ1 Durability — fail-open by default, so not every interaction |
| REQ6 Declared, not inferred | REQ3 Actor identity — no authority model |
| | REQ4 Privacy — principle, not enforcement |
| | REQ5 Derivation — agent-side unrecorded |
| | REQ7 Survives the actor — "outlives the deployment" not demonstrated |
| | REQ8 Demonstrable operation — countable, not continuous |
| | REQ9 Fitness at decision — no consumer at decision time |
| | REQ10 Reconstructable context — link built, retention parity not |
| | REQ11 Evidential basis — declared, but not interoperable |

**Not all green is the same green.** Every row carries an evidence class. Class
**A** means the claim was read back out of Marquez or Jaeger over HTTP after the
session closed, so it survives leaving our process. Class **C** means we
asserted it in-process, which proves our code does what we think and nothing
about whether a consumer can read it. Eight of the eleven rows are class A.

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

**Naming.** **REQ1–REQ11** are requirements. RAID uses `Rnn` for **risks**; the
two are unrelated.

---

**Status:** 2026-10-06. REQ8 was corrected on review, and REQ1 and REQ7 were moved
to Partially met. Every `uv run pytest` command below was last run on 2026-10-06.
**Companion to:** [`REQUIREMENTS.md`](REQUIREMENTS.md), holding the eleven
requirements this matrix tests, and [`README.md`](README.md), the technical
statement.
**RAID:** I25.

---

## Why this document exists, and how to read it

When an open-weights model ships, it ships with a benchmark table. What makes
that table credible is not the scores. It is that somebody **named the benchmarks
in advance**, the method **reproduces**, and the **failures appear in the table**.

This applies the same discipline to a governance claim. `REQUIREMENTS.md` states
eleven requirements for observability of AI interaction with data. This document
says, for each one, what we built, what test proves it, how strong that evidence
is, and, where the implementation does not meet the requirement, that it does
not meet it.

**A matrix with eleven green rows would be marketing.** Two of the rows below are
Met and nine are Partially met, with the unmet half named in each case.

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

**And this matrix scores the demonstration, not the gap claim.** The gap
generalises to any runtime actor-initiated consumption event; the evidence does
not, and the two are stated separately for that reason (RAID D24). Every verdict
below is about **MCP, over Postgres, through SQL**. None of them is evidence
about a REST call, a GraphQL query, SDK-based access or a notebook, even where
the requirement itself applies there unchanged.

**And so does run shape.** The scoped unit of work is a **single interaction** —
one tool call, one run. Every verdict below is read against that shape; a
long-running job spanning many traces is out of scope (RAID D22), and REQ10 is
the row where the difference bites rather than merely applying.

### Reproducing any of it

```bash
cd mcp-lineage
docker compose up -d --build          # six services + the fail-closed sibling
cd mcp_server_ol
uv sync
uv run pytest                          # unit
uv run pytest -m integration           # requires the stack above
```

Each row gives its commands in full. **112 unit + 20 integration tests** pass,
verified against the live stack **2026-10-06 under
`openlineage-python`/`openlineage-sql` 1.53.0**, on a stack built from scratch with
the warehouse loaded by the documented loader. Both integration runs pass all 20
(RAID I51 was fixed on 2026-10-06). Ruff is clean and mypy is clean on `src`.

**The count changed, and the reason is a result.** The suite was 85 unit with one
deliberate `xfail` (RAID A06) — the `UPDATE … SET` assignment-subquery case that
[OpenLineage PR #4767](https://github.com/OpenLineage/OpenLineage/pull/4767)
fixes. That fix shipped in 1.53.0, so the `xfail(strict=True)` **XPASSed on the
upgrade**, which is exactly what `tests/unit/test_sql_parse_completeness.py` was
written to signal. A06's specific refutation is now fixed upstream and **R03 has
narrowed**. R03 itself stands: two cases in that file still demonstrate silent
incompleteness — a read inside a function returns no inputs, no outputs and no
errors, and a read through a view reports only the view.

---

## The matrix

### REQ1 — Durability 🟡 Partially met · Evidence A

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

**Unmet part, named.** The requirement says *every* interaction. The server's
default posture is fail-open (RAID D11): when the lineage store or the collector
cannot be reached, the tool call still succeeds, and the lost event is counted and
not recorded. The fail-closed posture (`LINEAGE_FAILURE_MODE=closed`) refuses the
call instead, and the unit and integration suites test it, so the property holds in
that mode. It does not hold for every interaction under the default.

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

**Parentage: demonstrated, using a name that does not exist yet.** The caller
supplies its lineage run and job in MCP `_meta`, and the server links them via
`ParentRunFacet`. `_meta` is `extra: allow`, so arbitrary keys survive, and the
mechanism is already there. **We use a bespoke reverse-DNS key because no agreed
key exists, and that is precisely the ask** (RAID D10, the `_meta` parentage ask). The key carries
a pointer to the caller's run, not an actor. Actor identity is not demonstrated:
no client sends one, and the event records `lineage.actor` as `absent` (RAID
I29).

**Authority model: not built.** `REQUIREMENTS.md` § 3a turns on the distinction
between an agent acting **on behalf of** a human and one acting **autonomously**.
Nothing in the emitted record carries that distinction. OpenLineage's ownership
URN vocabulary has no agent type and no authority model (RAID A03, D05, D28). This is the single largest unmet part of the implementation.

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

**Built as a design principle, for the identity reference only.** Nothing in the
emitter reads or constructs identity. Whatever the caller supplies passes through
untouched, and the server never resolves, enriches or looks anything up.

**Not enforced, and this is an honest gap.** Three paths carry caller-controlled
text into the lineage store unredacted. A caller that puts an email address in
`jobName` will see it emitted to Marquez. The full statement text goes out on every
event as `job.facets.sql`, and an agent's SQL can carry literal values. On failure
the database's error text goes out as well, and it can echo those values; it is also
attached to a metric attribute (RAID I59). No validation, masking or rejection
exists on any of these paths, and **no test asserts that the server refuses or
removes PII**, because no such behaviour exists. RAID R02 states the principle and
the architecture makes compliance easy. It does not make violation impossible.

**What the requirement assumes instead (RAID A29).** That whoever operates the stack
applies appropriate anonymisation or pseudonymisation in the stores the events land
in, and treats the lineage store as holding personal data. That is the operator's
responsibility. This implementation emits the events and does not enforce it. The
data in the demonstration is synthetic.

**Evidence.** The test below shows only that the identity is read from the caller's
request and passed through as supplied, which is class C for that one claim. It
shows nothing about privacy. No test covers any privacy property, which is class D.

```bash
uv run pytest tests/unit/test_meta.py::test_reads_identity_from_a_plain_dict
```

**To close it** needs a validation or masking policy at the emission boundary. Not
built, and deliberately not faked for this matrix.

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

**The parser's own incompleteness is pinned by tests that assert today's
behaviour.** The one case with an upstream fix, a table read only in an `UPDATE`
assignment subquery, was a strict `xfail` that XPASSed when the pinned client
moved to 1.53.0, and it is now a regression pin. Two cases still show silent
incompleteness, so the suite fails loudly when somebody fixes them rather than
silently carrying a stale claim (RAID A06, R03).

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

### REQ7 — Survives the actor 🟡 Partially met · Evidence A

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

### REQ9 — Fitness at the point of decision 🟡 Partially met · Evidence C

> Where an AI-produced figure informs a decision, somebody must be able **at that
> moment** to establish what produced it and whether that derivation was sound.

**The precondition holds.** The record exists *at execution time*, not on a
reporting cycle, which is the property platform audit lacks. Snowflake's
`ACCESS_HISTORY` documents a latency of up to 180 minutes (`REQUIREMENTS.md`
§ 2a). Emission is synchronous with the interaction.

**Nothing consumes it at decision time.** No interface answers "is this figure
sound?" for the person about to act on it. The evidence is available. The
*fitness judgement* is not built, and the agent itself has no way to ask.

The test below supports only the precondition, that the start event is emitted
before the statement runs. Nothing tests timing at the point of decision or the
fitness of a figure, and the *fitness judgement* is not built.

```bash
uv run pytest tests/unit/test_driver.py::test_start_is_emitted_before_execution
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

**And the facet is bespoke.** No OpenLineage facet carries trace context.
Re-verified 2026-09-30 against the shipped client at **1.53.0**, the current
release: no run facet in `openlineage.client.generated` carries a trace or span,
including in the explicit-lineage module added since 1.52.0. A standard facet is
our proposed answer to the open question at [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484), not yet posted there.

**This verdict assumes single-interaction run shape**, which is the scoped unit
of work. The link names the span that initiated *this* run. Where one run spans
many traces the link is not degraded but ill-defined — *which span?* — and that
case is out of scope rather than unaddressed — RAID **D22**, and `REQUIREMENTS.md`
§ 11 states the adverse scenario. Raised at the OpenLineage TSC 2026-09-30.

**What the link does name is provenance**: the span that caused this run to
exist, singular by construction. Composition — the spans a run consists of — is a
different fact, 1:N by nature, and one this workstream does not ask for. That is
also what distinguishes the ask from #4588, which drew a scope objection: a
provenance pointer is not a work record (RAID A08, R11, A19).

---

### REQ11 — Evidential basis 🟡 Partially met · Evidence A

> The record declares **how it was derived**, so a reader can weigh it. Evidence
> whose derivation is unstated cannot be weighed.

**Declared: on every event, in a standard facet.** Three tags ride in
`TagsRunFacet` on every `START`, `COMPLETE` and `FAIL` this server emits. The
load-bearing one is `lineage.derivation = parsed-intent`, which states the
position this implementation occupies on the three-point derivation scale
(RAID D26): parsed from statement text, not read from an engine plan and not
observed from execution. `lineage.completeness` states what follows from that
position — `not-guaranteed` as a standing caveat, `parse-failed` where the
statement could not be read at all and empty inputs therefore mean *we could not
tell* rather than *it touched nothing*.

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_run_declares_its_datasets_are_intent
uv run pytest -m integration tests/integration/test_end_to_end.py::test_a_failed_parse_is_readable_off_the_event_in_marquez
uv run pytest tests/unit/test_sql_parse_completeness.py
uv run pytest tests/unit/test_tag_vocabulary.py
```

**The vocabulary is closed for this producer, and that is enforced rather than
described.** `TAG_VOCABULARY` in `lineage.py` declares the three keys and their
permitted values; `tests/unit/test_tag_vocabulary.py` asserts both that the
declaration is exactly what D26 records and that every tag the emitter puts on an
event is within it, so a fourth value cannot arrive unnoticed by either route.
The tags stay free-form **on the wire** — the facet is free-form by design and
OpenLineage is not being asked to define a key vocabulary.

**Closure stops at this producer's own tags, because the facet has other
writers.** The client adds `openlineage_client_version` to the same
`TagsRunFacet` on every run event, so the tags this implementation wrote are
identified by `source = INTEGRATION` rather than by key prefix. **The second
writer is not a surprise but a defect.** `OPENLINEAGE__TAGS__RUN__*`
configuration is merged into the facet with `source = USER`, and the client lets a
same-key `USER` tag replace an integration-supplied one — value *and* source —
logging at `INFO`. An operator can therefore make an event whose parse failed
declare the standing caveat instead. Reproduced and pinned at 1.53.0 by the test
above and recorded as **RAID I46**, with the mitigation left as an open decision
because it turns on whether operator or producer owns an evidential claim. It is
R14 one step earlier than R14 states it: the declaration need not even reach the
wire intact.

**Verified to survive the reference consumer.** Run-level custom facets and the
tag facet both return intact from Marquez `/api/v1/events/lineage` — checked by
the REQ10 round-trip test and again directly on 2026-09-30.

**Why it is not met: declared is not interoperable.** The mechanism is a
free-form tag facet, and **the specification places no obligation on a consumer
to preserve, return or surface a key it does not recognise** — verified by text
search of `spec/OpenLineage.md` at 1.53.0, where *consumer*, *ignore*,
*unknown*, *preserve*, *retain* and *propagate* each appear zero times (RAID
I45). So a conformant consumer may drop this declaration at ingestion, or store
it and never show it to anyone. Our own probe demonstrates the first mode in
another position — Marquez silently discards `parent.run.facets`, HTTP 201, no
warning (RAID I22) — and Marquez's tracker shows the second for *standard*
facets (#2351, #1746, #1969).

**And the vocabulary is ours.** `lineage.derivation` and its values are defined
by this producer, not by the spec, which defines no tag-key vocabulary at all.
A generic consumer reads them as unrecognised strings. That is a deliberate
position (D26): the ask to OpenLineage is two Run facets for structure that does
not exist, and this is something already expressible.

**What would close it.** Not an implementation change. Either a shared
convention across producers, which needs no spec change, or a first-class
derivation field, which does — and is not currently requested (RAID R14).

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
| **Protocol** | MCP | Lineage parentage across the call boundary, via `_meta` | *Which run asked?* |
| **Data & information** | OpenLineage | Canonical dataset identity, intent, completeness | *What did it touch?* |

Each is authoritative for its own half and silent on the others. **AI governance
that rests on any one of them is policy and hope with a dashboard attached.**

### The three joins, and the test that demonstrates each

**Join 1: protocol parentage becomes lineage attribution.** The caller's run and
job travel in `_meta` and arrive as `ParentRunFacet` on the lineage event. This
makes a data interaction attributable to the caller's run rather than to a connection.
It does not identify the actor (RAID D28).

```bash
uv run pytest -m integration tests/integration/test_end_to_end.py::test_the_caller_identity_survives_the_round_trip
uv run pytest -m integration tests/integration/test_streamable_http.py::test_concurrent_callers_are_not_confused_with_each_other
```

*Gap it exposes:* no agreed `_meta` key exists. Ours carries a vendor prefix on
purpose. RAID D10, the `_meta` parentage ask.

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
and a standard one is our proposed answer at OpenLineage #4484, not yet posted.

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
treated the seam as outside its own remit. In opentelemetry-specification#3447 a
contributor said that if lineage needs its own context propagation, so that it is
its own top-level signal, it would be out of scope for OpenTelemetry, and pointed
to Baggage as the base for a separate project. In #4588 an OpenLineage
contributor said OpenLineage is not a monitoring or observability tool. MCP
closed the question as insufficiently mapped to its concepts (RAID A08).

Every one of those positions is defensible alone. **Together they leave the
governance question owned by nobody**, and it is the question a regulator, a CRO
and a board are all going to ask about autonomous agents.

The convergence needed is small and specific: an agreed `_meta` key and a standard
trace-context facet. Two narrow additions. This suite is what they look like when
somebody builds them anyway. The authority model, which would separate an agent
acting on behalf of a person from one acting alone, is a stated gap and not an ask
(RAID D28).

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
anybody inventing anything. We expect the parent run id and trace link arriving in `_meta`
to come from that already-instrumented runtime.

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
| REQ1 Durability | 🟡 Partially met — fail-open by default, so not every interaction | A |
| REQ2 Asset identity | ✅ Met | A |
| REQ3 Actor identity and authority | 🟡 Partially met — no authority model | A |
| REQ4 Privacy by construction | 🟡 Partially met — principle, not enforcement | C |
| REQ5 Derivation | 🟡 Partially met — agent-side unrecorded; server-side is intent | A |
| REQ6 Declared, not inferred | ✅ Met | C |
| REQ7 Survives the actor | 🟡 Partially met — outlives the session, not shown to outlive the deployment | A |
| REQ8 Demonstrable operation | 🟡 Partially met — countable, not yet continuous | A |
| REQ9 Fitness at the point of decision | 🟡 Partially met — no consumer at decision time | C |
| REQ10 Reconstructable context | 🟡 Partially met — link built, retention parity not | A |
| REQ11 Evidential basis | 🟡 Partially met — declared on every event; no consumer is obliged to preserve or surface it | A |

**Two met, nine partially met, none unmet**, all within the structured and SQL
scope, and one of those verdicts corrected during review (REQ8). Two more rows, REQ1
and REQ7, were moved from Met to Partially met on 2026-10-06, after a second review
applied this matrix's own legend to them.

### What the gaps have in common

Read down the unmet halves and they sort into three kinds, which is more useful
than a count.

**Missing a convention, not a mechanism.** REQ10's standard trace-context facet.
No implementation can close it, because what is absent is community agreement, and
the standard facet is our proposed answer to OpenLineage #4484, not yet posted.
That is the workstream's whole argument, arriving from the evidence side rather
than the argument side. REQ3's authority model is a different case: a stated gap,
not an ask, which closes only if the chain in RAID A28 holds (RAID D28).

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
- Any run shape other than a single interaction (§ 11, RAID D22). The trace
  reference names the span that initiated the run; in a job spanning many traces
  there is no such span, and the link would be ill-defined rather than weaker.
- That fail-closed is the correct posture. We demonstrate both and argue for
  neither (RAID D11, R08).
- That parsed intent equals observed effect. It does not, and every event says
  so.

---

*Regenerate the counts before publishing: `uv run pytest -q` and
`uv run pytest -q -m integration`. A matrix that has drifted from its suite is
worse than no matrix.*

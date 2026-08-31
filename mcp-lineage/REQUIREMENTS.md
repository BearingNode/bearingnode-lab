# Requirements: observability of AI interaction with data

<!-- rev: 1192a9a2a7241d16 -->

> This document is written for the CDAO, CRO, Chief AI Officer, third line and
> compliance. It makes its case using the ten-requirement table below. If you'd
> rather read the same case as a short article, with no table, read
> ["From Tools to Traces: Why MCP is the Key to Agentic Data
> Lineage"][blog-leadership] instead.

## TL;DR

**The opportunity.** LLM agents now reach governed data directly through MCP —
sometimes on behalf of a human being, or acting autonomously — and currently
none of OpenTelemetry, MCP's own conventions, or OpenLineage records what data
they touched, on whose authority, or where it went. That gap is closable.

**What existing telemetry gives you, and what it doesn't?** Distributed tracing
answers *how did this perform* — it samples by design and retains for weeks,
which is right for a latency question and wrong for a record you are obliged to
keep. It can tell you a query ran. It can't tell you which customer's data fed
the decision it enabled.

**Why these ten, and not a generic AI governance checklist?** Each requirement
traces to a question a regulated function already has to answer — can
leadership trust what an agent tells it, can compliance prove it afterwards —
and to the specific way an agent-mediated interaction breaks that answer today.
None are aspirational: each is testable, and each maps to an obligation already
in force (§ 9), not invented for this workstream. Platform audit and tracing
both help; §2a and the paragraph above state why neither, on its own, answers
either question.

**The ten requirements**, each testable and checked against this workstream's
own reference implementation:

| | | |
|---|---|---|
| **REQ1** | Durability | The record answers to the obligation, not to a sampling policy |
| **REQ2** | Asset identity | Canonical, comparable across systems, column level where the obligation demands it |
| **REQ3** | Actor identity and authority | Who acted, and on whose authority — delegated or autonomous |
| **REQ4** | Privacy by construction | Pseudonymous reference; resolution stays in a separate system |
| **REQ5** | Derivation | The transform, its inputs, and any truncation that limits validity |
| **REQ6** | Declared, not inferred | The acting entity produces the record, as it acts |
| **REQ7** | Survives the actor | Outlives the agent, the session and the deployment |
| **REQ8** | Demonstrable operation | Show the control *operated* over a period, not that it existed |
| **REQ9** | Fitness at the point of decision | Reachable *when the decision is taken*, not on a reporting cycle |
| **REQ10** | Reconstructable context | Both records linked, in both directions, and both survive |

**What is proven.** Four met, six partially met, none unmet, with the unmet half
named in every case and a command to reproduce each row. See
[`evidence-matrix.md`](evidence-matrix.md), and read it before relying on any
requirement here.

**What is not.** Structured data reached through SQL, over MCP, against
Postgres. Non-SQL query languages and unstructured data fall outside scope, and
§ 11 explains why that is the harder half rather than the next increment.

**What it costs to adopt.** Carrying caller identity costs an MCP server
nothing. Emitting lineage means every server that touches governed data has to
emit it, because only the process that executed the statement can declare what
it touched. Our working assumption is that adopters refactor their servers at
the data-access seam (RAID D17, A12); we do not prescribe the route.

**Naming.** Requirements are **REQ1–REQ10** throughout this document and the
evidence matrix. RAID uses `Rnn` for **risks**, and the two are not related.

---

**Who this is for:**

- The board and executive leadership, who take decisions on AI-produced figures
- The Chief Data & Analytics Officer
- The Chief Risk Officer
- The Chief AI Officer
- Third-line internal audit
- Regulatory compliance

Two questions, one problem. Leadership asks **"can I trust what it is telling
me?"** Compliance asks **"can we prove it afterwards?"** Both need the same
missing evidence. Nothing supplies it today.

**What it is:** the obligation-side statement of the problem this workstream
addresses. [`README.md`](README.md) gives the technical statement, covering what
the signals do and do not carry. This document says why that matters to an
organisation with regulatory exposure, and what satisfying the obligation would
take. Read this first and the README second.

**Scope of the demonstration behind it:** the requirements below state the case
generally, because the obligation is general. The build proves something
narrower: **structured data reached through SQL**. This work does not address
non-SQL query languages such as SPARQL and graph traversal. It also does not
address unstructured data in any form, including documents, object stores, and
vector and embedding retrieval, which agents now both read and write. The reason
is that dataset identity for unstructured retrieval remains unsolved, not merely
unimplemented. Section 11 states this properly. We believe requirements REQ1 to
REQ10 hold for those cases. Nothing here proves they can be met there.

---

## 1. What changed

Organisations now put agents in front of governed data — sometimes on behalf
of a human being, or acting autonomously — reaching claims, policies,
customers, positions, personal data. The agent queries it, reasons over it,
and derives from it. A decision follows.

Every existing control for data access and decision provenance assumes one of
two actors:

- **A person**, who authenticates, holds a name and a role, and leaves an
  access record.
- **A scheduled pipeline**, which holds a durable job identity, an owner, a
  change record, and a run history.

An agent is neither. It has no durable job to carry ownership, often no change
record, and frequently no named human at the point of access. The control
framework does not fail loudly when an agent arrives. It stops producing
evidence, quietly, and continues to report green.

## 2. Why the existing telemetry does not cover it

Organisations that deploy agents do have telemetry. It is the wrong telemetry.

Distributed tracing answers one question: *how did this perform?* It **samples
by design**, and keeping a representative fraction is the correct engineering
choice when the question is latency. Retention typically runs to weeks. The
semantics describe operations and durations, not provenance.

Applied to a record you must keep, those same properties are fatal:

> Sampling is a cost optimisation in observability.
> Applied to an obligation, it is destruction of records.

A trace can tell you that *a* query ran and took 240ms. It cannot tell you which
customer's data fed a decision. If sampling dropped it, the trace cannot tell you
the interaction happened at all. **You cannot answer a regulator from a trace.**

## 2a. "But our data platform already audits access"

The challenge is fair and deserves a straight answer rather than a dismissal.
Regulated estates run platforms with data access auditing switched on. So why
does this problem remain?

> ### ⚠️ Scope of what has been verified
>
> **We examined one platform against primary documentation: Snowflake.** It
> appears below as a worked example, and we chose it deliberately as the
> *strongest* case rather than a convenient one.
>
> **Not verified:** Databricks / Unity Catalog, Microsoft Fabric / Purview,
> AWS (Redshift, Lake Formation, Glue, SageMaker), or any Iceberg REST catalog
> implementation including Polaris. The architectural argument about catalogs
> below reasons from the Iceberg REST catalog design. **No product's audit
> documentation confirms it.**
>
> The argument is that these are *different kinds of record*. That claim rests
> on the identity and purpose gaps, which are properties of where the record
> originates rather than of any vendor's logging quality. But **do not assert
> what a specific platform does or does not capture without checking it.** Each
> platform needs the same treatment we gave Snowflake before this section
> becomes a general published claim.

**The reason this problem remains is not that platforms log too little.** They
log a *different fact*. Readers routinely conflate three records:

| | Records | Authoritative for |
|---|---|---|
| **Platform audit** | What the engine did | Effect — which objects were touched |
| **Lineage** | What data an actor reached, and why | Attribution and purpose |
| **Traces** | The decisioning context around it | Replay — what was asked and concluded |

Take the strongest example we checked. Snowflake's `ACCESS_HISTORY` is good:
one row per statement, with objects recorded at **column** level and
resolved through views to base tables. That is observed effect, and it carries
more weight than anything derived by parsing a statement before it runs.

It still cannot answer the questions in section 4, for four reasons. The first
two are structural and hold wherever the data platform produces the audit. The
second two state Snowflake figures, and nothing verifies their equivalents
elsewhere.

**1. The agent is invisible** *(structural)*. The audit records the *session
principal*, the identity the connection authenticated as. An agent reaching data
through a tool server arrives as that server's connection identity, a service
account. The platform will faithfully report that `SVC_AGENT_PROD` read the
claims table four hundred times, which is not attribution. Every agent, and
every human behind every agent, is the same principal. **This holds wherever the
data platform produces the record**, because the platform sees the connection
and not what stands behind it.

**2. Purpose is absent** *(structural)*. No data platform knows the read served
a particular customer's question, or which decision followed. The decisioning
context exists at the point of the tool call and nowhere downstream of it.

**3. It does not cross systems.** A decision drawing on a warehouse, an
operational database and an external API has no single audit. Each platform is
authoritative for itself and for nothing else.

**4. The audit arrives too late to act as a control** *(Snowflake figures)*.
`ACCESS_HISTORY` documents a latency of **up to 180 minutes**. Three hours makes
a report, not a control. It is fatal to REQ9, which requires provenance to be
reachable *at the moment the decision is taken*.

Retention is the weaker half of this point and carries no weight. Snowflake
documents `ACCESS_HISTORY` as holding 365 days, but an estate that needs longer
can materialise it into its own tables. Retention is therefore an engineering
choice rather than a limit. **Latency is not.** It is a property of how the
platform populates the view, and no amount of configuration makes a
three-hour-old record answer a question somebody asks now. *Both figures are
Snowflake's. Nothing verifies other platforms.*

### The catalog case may be sharper: architectural reasoning, not verified

⚠️ **Reasoned from the Iceberg REST catalog design. Nothing confirms it against
the audit documentation of Polaris, Unity Catalog, Glue or any other
implementation, and credential vending is one of several access patterns rather
than the only one. Verify before publishing this as a claim about any named
product.**

Where an estate has moved to an Iceberg REST catalog, the gap looks
architectural rather than a matter of log detail. The catalog is a **metadata
service**. It can vend scoped credentials, after which the engine reads data
files **directly from object storage**. On that pattern the catalog's audit
records *authorisation*, not access. A credential vended and never used would
look identical to a full table scan.

If that holds, reconstructing what a single lineage event would have stated
means joining catalog audit, object storage access logs and engine query
history: three systems, three identity models, three retention policies, no
shared key.

**Somebody who runs the platform in question is most likely to challenge this
section, and it is the one to check first.**

### The position

**Lineage does not replace platform audit, and nobody should argue it as a
substitute.** Platform audit is the effect record and is authoritative for what
the engine did. Lineage supplies the half it structurally cannot hold: who
asked, on whose authority, for what purpose, across systems, at the moment of
the request.

The two are strongest together. An estate with both holds *intent* and *effect*
side by side. Where they diverge, that divergence is itself evidence.

## 3. The leadership question: can I trust what it is telling me?

Distinct from compliance, and upstream of it. Compliance asks *can we prove this
afterwards*. Leadership asks *should I act on this now*.

**The failure mode here is not the one everyone watches for.** Attention on AI
trustworthiness falls overwhelmingly on the model: hallucination, fabrication,
unsafe output. In the worked example in section 5, the model does nothing wrong.
It receives 5,000 rows and faithfully computes their average. The unsoundness
entered at the tool boundary, before the model reasoned at all.

That matters, because **every AI assurance technique now deployed looks at the
model, not at the data path.** Evaluations, guardrails, groundedness checks and
LLM-as-judge all assess whether the output follows from the context supplied.
None of them establish whether that context was complete, current, authorised,
or drawn from the right dataset. An agent can pass every evaluation in place and
be confidently wrong.

Nor does the presentation carry any signal. The agent reports the average with
identical fluency whether it read five thousand rows or five million. People
calibrate trust on fluency and confidence of delivery, which here has no
correlation with whether the answer is sound.

"Is this data correct?" decomposes into five questions, none of them answerable
at the point of decision:

| | |
|---|---|
| **Complete?** | Did it see all the data, or a truncated read? |
| **Current?** | How stale was what it read? |
| **Right source?** | The authoritative table, or one that looked similar? |
| **Authorised?** | Was it entitled to that data at all? |
| **Correctly derived?** | Was the transform sound, and are its limits recorded? |

A compounding problem sits behind these: **the same question may not return the
same answer twice**, and nobody can reconstruct either run. Nothing corrodes
executive confidence faster than that discovery. Not a single wrong answer, but
the realisation that the process does not repeat.

The cost is symmetric, and both sides are expensive:

- **Over-trust.** Decisions taken on figures that are not what they appear.
- **Under-trust.** The AI investment returns nothing, because nobody will act
  on its output without a basis for believing it.

Absent provenance, an organisation cannot calibrate between the two, so it
oscillates. Enthusiastic adoption until something is visibly wrong, then blanket
caution that strands the investment. Neither is a governance position.

Nor can the organisation delegate this to the AI function. It is a question
about the provenance of data, not the behaviour of a model, which is exactly why
it falls into the seam section 6 describes.

## 3a. The safety question: AI Governance is not AI Observability

Compliance asks *can we prove it afterwards*. Leadership asks *should I act on
this now*. A third question exists, and it scales worst of the three: **would
anyone know if this went wrong while nobody was watching?**

**`aigov != aio11y`.** The position appears in
["We are making the same mistake with AI that we made with data"](https://www.bearingnode.com/post/aigov-aio11y-we-are-making-the-same-mistake-with-ai-that-we-made-with-data),
and this workstream is its worked example. That post opens on precisely the
interaction instrumented here:

> Somewhere in your organisation today, an AI agent queried a data warehouse,
> joined the results, reshaped them, and injected them into a prompt. An ad-hoc
> data pipeline was created, executed and destroyed inside a chat session. Your
> governance framework has a policy about it. Your telemetry captured that a
> tool was called, and how long it took. **And nothing — anywhere — recorded what
> the data actually did.**

The distinction is not a matter of emphasis. It is categorical:

> **Governance is normative — it says what should happen. Observability is
> empirical — it shows what is happening.**

| | Says | Produces |
|---|---|---|
| **AI Governance** | Models must be risk-assessed; agents must only access authorised sources; human oversight must exist for consequential decisions | Policy, standards, controls, ownership |
| **AI Observability** | Which data sources an agent *actually* touched and what it did with them; whether the controls governance assumes are *actually firing* | Evidence |

Without AI observability, verifying AI governance is difficult. Without AI
governance, AI observability lacks context for what to measure. **Linked, but
distinct.** The failure mode is treating the existence of a controls framework
as evidence that the thing it controls is under control.

> If your organisation can't answer *"what data did this AI system access, and
> where did it go?"*, you don't have an AI governance problem. You have **an AI
> observability problem wearing a governance badge**.

**This is the same mistake, at AI speed.** Data governance arrived a decade
ahead of data observability. The industry treated policy as evidence, and
`write policy and hope` did not work. It fails worse here, for two reasons the
post states plainly. Data fails slowly, as a lineage breaks or a quality score
degrades over weeks, whereas **AI systems drift in hours**. And **agentic
systems do not just produce outputs, they take actions**. The gap between what
policy says should happen and what the system does now carries real-world
consequences rather than analytical ones.

**It also explains the two-plane problem in section 10.** While the data world
wrote policy, the software and infrastructure world instrumented: OpenTelemetry,
traces, metrics, logs, visibility as an engineering discipline rather than a
documentation exercise. One community built an evidence layer. The other built a
paper trail. That fork is why the seam this workstream addresses exists at all.
The instrumentation tradition and the governance tradition developed separately,
and the agent is the first actor that needs both at once.

**None of this argues for slowing down.** The organisations that win this decade
will deploy agentic AI aggressively *and* evidence what it does. The lesson from
data is not that governance was wrong. It is that governance without an evidence
layer cannot be verified. The standards, patterns and lessons already exist. We
have to apply them at AI speed, because nobody has another ten years to close
this gap.

### Why autonomy changes the weight of this

The distinction between the two authority models matters here more than
anywhere, and the language is deliberate (see section 7, REQ3):

**Acting on behalf of a human.** A person is in the loop. They set the task,
they see the output, and they can apply judgement before acting on it. Their
accountability stays intact, and a wrong answer meets a human check before it
reaches a consequence. Imperfect, but real.

**Acting autonomously.** No person sets the individual task, sees the
intermediate output, or checks the result before it takes effect. The check that
made the first case tolerable is gone.

**In the autonomous case the decisioning context is not supporting evidence. It
is the only record that anything happened at all.** If nothing captures it at
the moment of action, nothing remains to reconstruct from, because no human ever
existed who could later say what they intended.

This is why after-the-fact reporting cannot satisfy the requirements below, and
why REQ9 insists on provenance reachable *at the moment of decision*. An
autonomous agent's decision moment may be the only moment.

### This is a safety requirement, not only a governance one

Stated plainly, because it usually sits under compliance and loses force there.

Detecting an agent operating outside its intended remit needs a record of **what
data it touched, on whose authority, and to what end**. That covers an agent
reading data nobody scoped it to reach, acting on stale or partial information,
or drifting from its purpose across a long-running session. No such record
exists today for agent tool calls. Nor, therefore, can anyone detect the
failure, bound its blast radius, or reconstruct it afterwards.

Every serious argument for AI safety assumes somebody can observe the behaviour
of a deployed system. For agents reaching governed data through tool calls, that
assumption does not hold today. It fails silently, which is the worst property a
safety-relevant gap can have.

> **Sourcing (`mcp-lineage` RAID I18).** The quotations above come from the
> article body of
> ["aigov!=aio11y: We are making the same mistake with AI that we made with
> data"](https://www.bearingnode.com/post/aigov-aio11y-we-are-making-the-same-mistake-with-ai-that-we-made-with-data)
> (Daniel Rolles, 5 July 2026), supplied by the author. The site does not render
> a fetchable body to the usual converter, the same obstacle I18 records for the
> *Anatomy of Uncertainty* series. **Verified character-exact against the live
> post 2026-07-30** (`public-lab` RAID I14), via a different extraction path.
>
> **That post is part one of three.** The series continues in
> ["aigov!=aio11y, part 2: Three tracks, one audit
> question"](https://www.bearingnode.com/post/aigov-aio11y-part-2-three-tracks-one-audit-question)
> and
> ["aigov!=aio11y, part 3: Building Track
> 3"](https://www.bearingnode.com/post/aigov-aio11y-part-3-building-track-3),
> both 5 July 2026.

**Part two names the three tracks this document argues between.** Every AI
deployment sits on one of them with respect to *"what data did this AI system
access, and where did it go?"* — **Track 1**, capture nothing; **Track 2**,
capture everything in OpenTelemetry; **Track 3**, spans and traces in OTel,
lineage events in OpenLineage. Sections 2 and 2a are the Track 2 case in detail:
it is the sophisticated default, and the post's verdict on it is the one this
document reaches independently — *"Track 2 is a local maximum"*, whose answer to
the audit question is *"the agent called the query_warehouse tool at 14:32, and
it took 240 milliseconds"*, which is an access record and not lineage. The
correlated trail Track 3 produces instead — which datasets were read, joined
which way, landing in which prompt, shaping which output — has a published name
in part two: **decision lineage**. That is what this reference implementation
emits, and section 5's worked example is one.

**This workstream is Track 3.** Part two closes on *"Track 3 is the only track
with an answer — and today, nobody is shipping it."* That is the claim this
repository exists to make false, and part three sets out the design it does so
with — see section 8.

## 4. The questions that cannot be answered today

Concrete, and each maps to an obligation an organisation already carries:

| Question | Who asks |
|---|---|
| Which records fed the figure in this return? | Regulator, external audit |
| A data subject exercised erasure. An agent copied their data into a derived table three weeks ago — where is it now? | DPO, regulatory compliance |
| Prove this automated decision did not use a protected characteristic. | CRO, regulator, legal |
| Who authorised this agent to read the claims table, and under whose authority was it acting? | Third line, CISO |
| Reproduce this number. | Everyone |

Today, in an agent-mediated interaction, the honest answer to all five is *we
cannot tell you*.

## 5. A worked example: a control failure, not a telemetry gap

From this workstream's reference implementation. Somebody asks an agent for the
average premium for commercial-segment customers. It:

1. Reads `private_party`, capped at 5,000 rows.
2. Reads `premium`, capped at 5,000 rows.
3. Joins them and computes an average, **inside its own reasoning**.
4. Returns a number. Somebody takes a decision on that number.

What survives: two spans saying something read two tables, probably sampled
away, retained for weeks. What does not survive: that something joined the two
datasets, that it took an average, which columns fed it, and, critically,
**that the inputs were truncated, so the average covers a sample and does not
answer the question asked.**

The organisation now holds a decision it cannot explain, reproduce, or
challenge. No system failed. No alert fired. Every component did exactly what
its designers intended.

## 6. The accountability seam

This lands precisely between two roles, which is why nobody owns it.

- Where the **CDAO** owns data governance but not AI, agents look like someone
  else's system calling their data, governed at the interface rather than at the
  interaction.
- Where a **Chief AI Officer** owns model and agent governance, the focus
  typically falls on model behaviour, evaluation and safety, not on the
  provenance of the data the agent touched en route.

If neither role has explicitly claimed *observability of AI interaction with
data*, nobody owns it by construction. **The first requirement is therefore
organisational, not technical: name the owner.** Third line should test for that
ownership, not only for controls.

## 7. Requirements

Testable statements. An agent-mediated interaction meets none of them today.

**REQ1 — Durability.** Every interaction between an actor and a governed data
asset produces a record whose retention and completeness answer to the
obligation, not to an observability platform's sampling or retention policy. No
performance-driven control may discard a record.

**REQ2 — Asset identity.** The record identifies the data asset canonically, in
terms comparable across systems and stable over time, at the granularity the
obligation requires. Dataset level generally, and **column level** where the
obligation concerns personal data, protected characteristics, or financial
reporting.

**REQ3 — Actor identity and authority.** The record identifies the initiating
actor and the **authority under which it acted**, whether its own standing
identity or delegated authority on behalf of a named user. Identity alone is
insufficient: "an agent did it" does not discharge an accountability obligation.

**REQ4 — Privacy by construction.** Actor identity in the record is a pseudonymous
reference. Resolution to a natural person stays in a separate, access-controlled
system with its own retention and erasure handling. Lineage stores suit personal
data badly and must not accumulate it.

**REQ5 — Derivation.** Derived data carries its derivation: the transform applied,
the inputs it consumed, and **any truncation, filtering or sampling that limits
the validity of the result.** A derived figure whose limits nothing records is
not a governed figure.

**REQ6 — Declared, not inferred.** The entity performing the action produces the
record, at the time it acts. Provenance reconstructed after the fact from an
indirect artefact, such as query text, network traffic or performance telemetry,
is inference. Inference is not evidence.

**REQ7 — Survives the actor.** The record outlives the agent, the session, and the
deployment. Ephemeral actors must not produce ephemeral accountability.

**REQ8 — Demonstrable operation.** Somebody can show the control was *operating*
over a period, not merely that it existed. Third line must be able to test it.

**REQ9 — Fitness at the point of decision.** Where an AI-produced figure informs a
decision, somebody must be able **at that moment** to establish what produced it
and whether that derivation was sound. Provenance that exists but stays out of
reach when somebody takes the decision does not support the decision. This
requirement separates governance from forensics: REQ1 to REQ7 make the record exist,
and REQ9 makes it *usable by the person deciding*.

**REQ10 — Reconstructable context.** From the record of a data interaction,
somebody can reach the context that produced it: what was asked, what the agent
chose to do, and what followed. The record of *what data was reached* and the
record of *why* sit on different planes (section 10) and must stay distinct. But
they must be **linked, in both directions, and both must survive**. A reference
into a context that sampling removed, or that expired first, is not a link.

REQ5 requires a record of any limit applied to a result. REQ10 makes that record
answerable. It is how third line establishes not merely that something read
5,000 rows, but that the figure derived from them then reached an audience as
though it covered the whole population. **The control failure in section 5 lives
between the two records, and neither one contains it alone.**

The practical consequence is a policy one, and it is where most estates will
fail this. Telemetry carrying the context of a governed data interaction cannot
sit under the tracing backend's default sampling or retention schedule. It forms
part of the control record and needs retention to match.

> **Evidence.** [`evidence-matrix.md`](evidence-matrix.md)
> tests, scores and reproduces each requirement: four met, five partially met,
> one not met, with the unmet half named in every case and a command to
> reproduce each row. Read it before relying on any requirement above.

## 8. What this implies technically

[`README.md`](README.md) holds the technical statement, and
[`Status/RAID.md`](Status/RAID.md) holds the decisions and their rationale. In
short:

- REQ1 and REQ7 are why OpenTelemetry alone cannot satisfy this. Not because it
  falls short, but because it correctly targets a different question.
- REQ2 is why a transport-level resource pointer does not substitute for a
  canonical dataset identity (RAID A05).
- REQ3 fails on both sides today. OpenTelemetry has agent identity primitives but
  no authority model, and MCP's conventions carry no caller identity at all
  (RAID A03).
- REQ5 fails against **everything now deployed**. Nothing observes the transform
  an agent applies after data leaves the server.
- REQ6 is why this workstream rejected an inference proxy (RAID D02).
- REQ9 sits outside the AI assurance stack as deployed. Evaluations, guardrails
  and groundedness checks reason about the model's output given its context, not
  about whether that context was complete, current, authorised or correctly
  sourced.
- REQ10 has **no standard mechanism on either side**. Nothing in the OpenLineage
  specification carries a reference to the trace that produced an event, and the
  reverse pointer is convention rather than specification. The reference
  implementation emits both under a vendor prefix, deliberately, and
  the ask to standardise it is filed at
  [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) (RAID D15, R11).
- **Platform-native audit does not satisfy REQ3, REQ9 or REQ10**, for the structural
  reasons in section 2a. The platform sees the connection, not the actor behind
  it, and never sees purpose. That much holds wherever the platform produces the
  record. Claims about any *specific* platform's capture, latency or retention
  hold for Snowflake only (RAID R10).

### The published design this implements, and the two terms it turns on

The shape above is not proposed here for the first time. It is specified,
component by component, in
["aigov!=aio11y, part 3: Building Track
3"](https://www.bearingnode.com/post/aigov-aio11y-part-3-building-track-3)
(5 July 2026): an interceptor at the MCP boundary, a `RunEvent` per call with the
tool/agent pairing as Job and the invocation as Run, a runtime-actor facet on the
Run, an **interaction-derived** value on the jobless `type` field, and the OTel
trace ID of the triggering span carried as a single fact on the run event —
*"One fact crosses the boundary: the trace ID. Everything else stays home."*
REQ10 is that sentence as a requirement, and
[OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484)
is the ask that would standardise it.

Two coined terms carry the modelling argument, and this document should use them
rather than re-deriving them (`public-lab` RAID I14 — the vocabulary-consistency
rule; the internal standards document that originated it does not ship, per
`public-lab` RAID D19):

- **Declaration-based** lineage *"records a relationship that already existed
  before the event does"* — an ETL job knows its inputs and outputs before it
  runs, a view's derivation is fixed at DDL time, and jobless structural lineage
  declares something durable. OpenLineage's current model quietly assumes this.
  It is the *"durable identity"* section 10 describes and the pre-existing
  relationship section 8's REQ2 discussion relies on.
- **Interaction-derived** lineage *"creates the relationship by happening"* — no
  pipeline was configured, no job scheduled, and the initiating entity is a
  runtime actor whose identity is known only at the moment it acts. This is what
  an agent's MCP tool call produces, and it is why REQ3 and REQ10 have no
  standard mechanism to satisfy them.

**Both terms are already upstream, in our own words, in the issue this workstream
supports.** [#4484](https://github.com/OpenLineage/OpenLineage/issues/4484)'s body
states: *"In all three cases the lineage is interaction-derived rather than
declaration-based — it comes into existence through the act of the call, not
through any prior structural definition."* Its Assumption 1 is the same claim as a
question to the TSC — *"Lineage is observer-declared"*. Verified against the issue
body 2026-07-30. So using the published vocabulary here aligns this document with
the filing rather than introducing anything new to it.

⚠️ **One caveat, and it is a discrepancy in our own published text rather than in
this document.** Part three says #4484 *"proposes roughly the extension above: a
runtime-actor facet, and an interaction-derived value on the jobless `type`
field."* **The issue body does not propose either.** It says *"We're not proposing
solutions here"*, and asks instead whether the extensible `type` string is the
right hook — suggesting `AGENT` or `MCP_CLIENT` as illustrations, not
`interaction-derived` — and how a runtime actor's identity should be expressed, with
the namespace/name model floated and no facet proposed. Recorded at `public-lab`
RAID I14; do not repeat part three's characterisation of the issue in anything
this lab publishes, and cite the issue body for what the issue asks.

**Where the reference implementation stands against that five-part design,
verified against `mcp_server_ol/src/mcp_server_ol/lineage.py` on 2026-07-30:**

| Part three specifies | `mcp_server_ol` today |
|---|---|
| An interceptor at the MCP boundary | ✅ Emission sits in the server's tool path, not in the agent |
| A `RunEvent` per call — tool/agent pairing as Job, invocation as Run, tables as Dataset | ✅ |
| The OTel trace ID carried as a single fact on the run event | ✅ `TraceContextRunFacet`, bespoke under our own prefix because no standard facet carries it (RAID D15) |
| A runtime-actor facet on the Run carrying agent, model, version, session | ⬜ **Not emitted, and deliberately so.** The event carries `lineage.actor` = `absent` instead, because MCP supplies no caller identity to carry (REQ3, RAID A03, I29). The facet is what #4484 asks for; the tag records its absence honestly in the meantime |
| The `interaction-derived` value on the jobless `type` field | ⬜ **Not emitted.** No `type` value is set at all today |

The last two rows are gaps between the published design and the implementation,
not disagreements with it, and they are not equivalent. The actor facet is
**deliberately** absent — there is no caller identity to put in it, which is the
finding. The `type` value is simply **not set yet**, and it is the cheaper of the
two to close. Both are tracked in `public-lab` RAID I14 and should be closed or
consciously scoped out before the RFC drafts are filed, since #4484's open
question 3 is precisely whether that `type` field is the right hook.

## 9. Regulatory context

✅ **Verified against primary or authoritative sources, 2026-08-20** (`public-lab`
RAID A03). This lab's own standard for upstream contribution holds citations to
the same bar as code: a wrong citation in front of a compliance audience costs
more credibility than a wrong attribute name does with maintainers.

- **EU AI Act, Article 12.** Automatic event-logging and record-keeping over a
  high-risk system's lifetime, feeding post-market monitoring (Art. 72) and a
  minimum retention period (Art. 19 / 26(6)).
- **GDPR, Articles 15, 17, 22 and 30.** Right of access, including meaningful
  information on the logic of automated decisions (Art. 15); erasure (Art. 17);
  restrictions on automated individual decision-making (Art. 22); and the
  controller's own records of processing activities (Art. 30) — the last is an
  obligation on the controller, not a data-subject right, and should not be
  phrased as one.
- **BCBS 239.** Risk data aggregation and reporting: accuracy, completeness and
  traceability. Confirmed only against convergent secondary sources — the
  primary BIS text did not extract cleanly for verification — so do **not**
  cite specific principle numbers from it without a follow-up primary-text
  check. BearingNode already holds a mapping of this to the D/I O11y framework.
- **DORA.** Regulation (EU) 2022/2554. Operational resilience for EU financial
  entities and their ICT third-party providers, in force since 2023-01-16,
  applicable from 2025-01-17.
- **Model risk management: SR 26-2 (2026-04-17), which superseded SR 11-7.**
  Jointly issued by the Federal Reserve, OCC and FDIC. Citing SR 11-7 alone is
  now stale. SR 26-2 is not a renumbering — it explicitly excludes
  deterministic/rule-based systems from "model" scope and places generative
  and agentic AI under a separate framework, a materially different scope than
  SR 11-7 covered.
- **ISO/IEC 42001** and **NIST AI RMF.** AI management and risk frameworks.
  ISO/IEC 42001's text is a paywalled standard — its general scope (an AI
  management system standard for organisations that design, develop, deploy or
  use AI) is confirmed against ISO's own public page; do not cite clause
  numbers from it without purchasing the standard. NIST AI RMF (Govern / Map /
  Measure / Manage) is freely available and confirmed against NIST AI 100-1.

## 10. Relationship to the D/I O11y framework

This is not a new framework. **Data and Information Observability** — term of
art **D/I O11y** — is:

> "The body of knowledge and practices for monitoring the health, performance,
> and organisational impact of Data and Information assets, as well as the
> capabilities to steward those assets."

— [*The Rise of Data and Information
Observability*](https://www.bearingnode.com/post/the-rise-of-data-and-information-observability-moving-beyond-traditional-methods).
Quoted verbatim, and to be quoted verbatim wherever it appears: the two clauses
are the definition, not alternatives (`public-lab` RAID I01, I14).

BearingNode's existing model already positions observability as serving
**Govern**, **Comply** and **Manage** rather than existing for its own sake, as
the [Comply + Govern + Management + D/I O11y Euler
diagram](artefacts/BearingNode-AM+DIo11y-joined-mapped.png)
shows. It is vendored into `artefacts/` rather than linked from BearingNode's
private `branding` submodule, which this workstream does not ship
(`public-lab` RAID D05).

This workstream is the first proof point for that model in the agentic case: the
same capability model, applied where the actor is an agent rather than a person
or a pipeline, and where the existing capability set stops producing evidence,
as sections 3 to 5 show.

**The argument has a lineage, and it is the same argument each time.**
`gov != o11y` for data: governance and observability are linked but distinct,
and the [Euler
diagram](artefacts/BearingNode-AM+DIo11y-joined-mapped.png) places
observability as the evidence layer that overlaps Govern, Comply, Manage and
Strategy without sitting inside any of them. `aigov != aio11y` (section 3a) is
that same diagram redrawn one layer up. What this workstream adds is the third
distinction, at the technical layer: **D&I Observability and software or
infrastructure observability are orthogonal planes** that an agent now forces
into contact.

Three statements of one idea, at three altitudes: organisational, AI-programme,
and signal. The `artefacts/` brief exists because the current figure can express
only the first.

The organisational Euler diagram and the technical one in
[`artefacts/`](artefacts/) make the same argument at two altitudes.

### Two worlds, and why they now have to meet

The framework's central distinction matters more here than anywhere it has
applied before, and it is the one that goes missing most easily.

**Software and infrastructure observability** and **Data & Information
Observability** are not two halves of one discipline. They are **orthogonal**:
different units of account, different signals, different retention, different
consumers, different questions. One asks *is the system healthy and fast*. The
other asks *is this information trustworthy, governed and explainable*. A
capability model that flattens them into a single plane will under-serve both.
It will also quietly reclassify governance evidence as operational telemetry,
where sampling and short retention apply and it stops being evidence.

**That separation worked, and does not any more.**

For as long as the actor was a scheduled job, the two worlds could run
independently, and that was correct. A job holds a durable identity and a fixed
purpose, and its own definition states that purpose. If you needed to know why
something read a table overnight, you read the pipeline. The decisioning context
was static and lived outside the run. **This is what section 8 calls
declaration-based lineage: the relationship existed before the event that
recorded it.**

An agent has none of that. It has no durable job, whoever prompts it sets its
purpose per invocation, and it creates the **consumption event and the
decisioning context in the same instant, as the same act**. **That is
interaction-derived lineage — the relationship is created by the call
happening** — and it is why the two planes can no longer be kept apart.

So the record of *what data was reached* and the record of *why, and what
followed* are now inextricably linked, while remaining different kinds of fact,
on different planes, with different lifecycles and different owners.

**They must not merge. They must be able to interact.** The technical form of
that interaction is a single correlation reference between the two records and
nothing more. The implication for the operating model is that the teams owning
each plane can no longer set retention, sampling or access policy without
reference to the other. Section 5's worked example is exactly this failure: the
lineage record shows the limit applied, and only the trace shows that the answer
then reached an audience as though nothing had limited it.

This is the distinction the current Euler figure cannot express, and the reason
[`artefacts/`](artefacts/) carries a brief to replace it with a connected-cube
treatment that renders the two worlds as dimensions rather than as overlapping
regions.

## 11. What this does not cover, and why it is the harder half

The requirements above state the case generally. The demonstration behind them
covers **structured data reached through SQL**, and we draw the boundary
deliberately rather than by omission.

**Not covered:**

- **Non-SQL query languages.** SPARQL, Cypher, Gremlin and other graph
  traversals.
- **Unstructured data in all forms.** Documents, object stores, vector indexes
  and embedding retrieval, in **both directions**: agents increasingly write and
  push unstructured content back into systems of record, not only read it.
- **Data that reaches a decision without a tool call at all.** A person exports a
  spreadsheet, attaches it to a chat, and the agent reasons over the contents.
  This case differs in kind from the two above, and § 11a states why.

**We do not expect to close this gap by extending the same approach**, and
saying so matters more than claiming coverage.

The obstacle sits upstream of instrumentation: **dataset identity for
unstructured retrieval is unsolved.** When an agent retrieves three passages
from a vector index, what is the dataset? The index? The source documents the
passages came from? The passages themselves? Each answer produces a different
lineage graph and a different governance claim, and none is more obviously right
than the others. OpenLineage's naming specification, which the structured case
relies on for REQ2, has nothing to say here.

Until that question has an answer, an unstructured lineage record would carry
something whose meaning is undefined. That is worse than carrying nothing,
because it looks like evidence.

**The direction of travel runs against us.** Agent access to unstructured
information grows faster than access to warehouse tables, so a structured-only
answer addresses a shrinking share of the exposure. This is the honest position.
The structured case is the one where the mechanisms exist and the gap is a
matter of convention, so it closes now. The unstructured case needs its own
work, starting from the identity question rather than from instrumentation, and
it is the more valuable problem.

We believe requirements REQ1 to REQ10 apply unchanged to unstructured access.
Nothing establishes that anything can satisfy them there today.

## 11a. The case that bypasses the tool boundary, and what we assume about it

The two bounds above limit what this demonstration reaches. The third bound
limits what the approach itself reaches, and it deserves separate treatment.

Consider the common case. A person exports a spreadsheet from a system of
record. They attach it to a chat. The agent reads the contents, reasons over
them, and produces something a person then acts on. **The data arrives as
conversation content, and the tool boundary is never crossed.**

**What we state as verified.** The tool-call route does not observe this
interaction and cannot. Every mechanism this document proposes sits at a boundary
this path never crosses. That covers the `_meta` identity convention, the
emission seam inside the server, and the tool-call attributes alike.

**What we state as an assumption, and record as one (RAID A13).** Two other
planes plausibly hold a signal, and **we have examined neither**:

- **The content platform.** Content platforms audit access, so the
  platform may record that a file was opened, by whom, and when. Licensing,
  enablement and retention govern whether it does. We reason this from the
  product category and confirm it against no product's documentation.
- **The agent harness.** The runtime reads the artefact to place it in the
  model's context, so the runtime observes it. § 10 already assumes the runtime
  emits GenAI telemetry, which makes it a plausible carrier. What a harness emits
  when a user attaches a file is a question we can answer with the stack we run,
  and we have not answered it.

**The posture is the one § 2a takes towards platform audit: complementarity,
never insufficiency.** We do not claim these signals are absent. We claim we do
not know what they contain, and we decline to assert either coverage or a gap
that we did not verify.

**The join remains the hard part under every outcome.** Grant the most generous
reading of both planes. A platform record states that a person opened a file at a
time. It does not state that the file entered an agent's context, and it does not
state which decision the file informed. **An export is also a copy.** By the time
the spreadsheet reaches the chat window, its link to the source asset may survive
nowhere, so the two records may hold no common identifier to join on.

That is this document's own argument, one layer out. Records exist on planes
owned by different functions, and no convention joins them. For the tool-call
route we know what the two ends are and we have built the link. **For this route
we have not established what the two ends are.** We state it as a known unknown,
and treat it as a research agenda rather than a limitation to disclose and move
past.

[blog-leadership]: https://www.bearingnode.com/post/agentic-lineage-mcp-dio11y

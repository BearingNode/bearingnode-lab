# mcp-lineage
<!-- build: dc06a539fd7e89b2 -->


> **All data is synthetic. This must never touch a production system.**
> See *Data and deployment*, below, and the
> lab-level [*Status of this work*](../README.md#status-of-this-work).

## TL;DR

> **The opportunity.** LLM agents now reach governed data directly — sometimes
> on behalf of a human being, or acting autonomously — and currently none of
> OpenTelemetry, MCP's own conventions, or OpenLineage records what data they
> touched, on whose authority, or where it went. The dataset and call parts of
> that gap are closable. The authority part is a stated gap (RAID D28).
>
> **The gap is not MCP-specific; the demonstration is (RAID D24).** Nothing in
> the gap depends on the protocol. It is a mismatch in OpenLineage's model.
> Ownership hangs off a **Job**, which is declared before anything runs. The
> actor that starts an ad hoc access is known only when it acts and varies from
> one run to the next, so there is no declared Job for it to hang off. The
> mismatch holds equally for a REST call, a GraphQL query, SDK-based access or a
> notebook. MCP is the forcing function, not the scope. What is built and
> verified here is MCP, over Postgres, through SQL, and nothing below claims
> otherwise.
>
> The boundary on the general claim has two limbs: consumption events where a
> runtime actor initiates the access, and the access is ad hoc. So the claim
> does not reach static, declaration-based work. That includes a *scheduled*
> agent against a governed dataset, which has a job declared in advance, an
> actor that does not vary per run, and an existing producer model that serves
> it (RAID A26). It also does not reach all ad hoc data access with a human in a
> BI tool. The discriminator is whether the work was **declared in advance**.
> § Scope states it in full.
>
> **What we built.**
>
> - **Requirements and evidence.** Eleven testable requirements (REQ1–REQ11) for
>   what an agent-mediated interaction with governed data must produce as
>   evidence, and an evidence matrix scoring this workstream's own reference
>   implementation against every one of them: two met, nine partially met, none
>   unmet, each row reproducible from a command in the matrix itself.
> - **Synthetic data, a general insurance example.** A deterministic generator
>   produces a synthetic general-insurance dataset — parties, policies, claims,
>   premiums — realistically shaped but describing nobody real, chosen because
>   claims and personal data are exactly the class of asset REQ2 and REQ4 are
>   written for. None of it is, or derives from, a real person, account or
>   transaction.
> - **A working demo, on open standards throughout.** MCP as the interaction
>   point, an unmodified `postgres-mcp` as the demo server, OpenTelemetry and
>   Jaeger for traces, OpenLineage and Marquez for lineage, against a real
>   Postgres warehouse — third-party components wherever one already existed,
>   rather than a bespoke stack.
> - **Community engagement, already under way.** We raised this with the
>   OpenLineage and MCP communities months before this reference implementation
>   existed —
>   [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484)
>   (open, engaged) and
>   [MCP #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638)
>   (closed after four hours, citing the AI-contribution guidelines). This work goes further. Below, we break out the
>   impact on each of the three standards it depends on, and where we'll be
>   raising RFCs on the basis of it.
>
> **How we built it.** From the standing of a CDAO in a regulated industry, not
> as an engineering exercise alone. Every claim above is tracked through a
> [RAID register](Status/RAID.md) — risks, assumptions, issues, decisions —
> open alongside the code, so nothing here rests on an assertion nobody can
> trace back to its reasoning.
>
> **What we found.** Three standards are impacted, in the following ways, and
> we'll be filing or continuing RFCs against each on this basis:
>
> - **OpenLineage** needs a runtime-actor facet. Its one existing
>   identity-bearing facet — `OwnershipJobFacet` — is declaration-based: who
>   owns a job, fixed at definition time, not who is acting on a given run. We
>   don't use it for the ad hoc case, where no job is declared in advance for it
>   to attach to. A caller with a declared job is the case OpenLineage already
>   serves. Instead, the reference implementation triangulates: a bespoke
>   run facet carries the trace ID and span ID back to the OTel trace, which
>   holds the decisioning context. That trace is not an identity carrier:
>   well-run deployments strip identity from telemetry (RAID R09). Absent a runtime-actor facet, the event tags itself
>   `lineage.actor: absent`, honestly, rather than guessing.
> - **OpenTelemetry** has a specific, real gap at exactly the method this
>   depends on: `tools/call` has no defined attribute for which data resource it
>   touched. The adjacent `mcp.resource.uri` convention exists — it just stops
>   short of reaching it. Beyond that one gap, the bigger point is that OTel
>   shouldn't be asked to become something it structurally can't be: tracing is
>   correctly built to answer *how did this perform*, sampled and
>   short-retained by design — right for a performance question, wrong for a
>   record you're obliged to keep. The fix isn't more OpenTelemetry. It's
>   OpenLineage alongside it for the part tracing was never going to carry.
> - **MCP** needs a convention for carrying, across the tool-call boundary, the
>   material from which caller identity is reconstructed on read. Identity here
>   is not a field somebody stamps on an event. It is a set of facts, each
>   captured at write time by the party that holds ground truth for it, and
>   correlated at read time by explicit identifier. The `_meta` key is one of
>   those inputs and carries lineage parentage. A caller populates it only if it
>   emits its own run. A caller with a declared job has a run to point at. An ad
>   hoc caller has none, and for it the trace link does that work. We built the mechanism, a
>   server-side reader against an unmodified SDK, but no client populates it
>   yet, including our own demo driver, because the key itself is not standard.
>
> Scored against the eleven requirements above: two met, nine partially met, none
> unmet. **The missing evidence for agentic access to governed data is not an
> open research question — it is a short list of specific changes across three
> specific standards, verified against a working implementation of two of
> them.** Not one change each: OpenLineage is asked for two Run facets, MCP for
> one `_meta` key, OpenTelemetry for attributes on conventions that already
> exist. The authority model is the exception: it stays open (RAID D28). The
> breakdown is in *Impact on the standards and their communities*.
>
> **[`REQUIREMENTS.md`](REQUIREMENTS.md) states this case in full**, eleven
> requirements deep, for the CDAO, CRO, Chief AI Officer, third line and
> compliance. This README is the technical account beneath it.

This repository is a working implementation of the gap raised in
[OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) and
[MCP #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638).
When an agent calls an MCP tool that touches a data resource, OTel-based
observability and OpenLineage-based lineage are different signals, and neither
derives from the other.

There are three ways an organisation can stand with respect to *"what data did
this AI system access, and where did it go?"*: capture nothing; capture
everything in OpenTelemetry, which answers *"the agent called the
query_warehouse tool at 14:32"* and stops there; or join spans and OpenLineage
events at the point of the call, which is the only one of the three that
answers the question. **This repository builds the third.** The joined trail
it produces — which datasets were read, how, and the trace the call belongs to — we
call **decision lineage**. What the decision was, and the transform behind it, is
recorded only if the agent's own runtime is instrumented (RAID A09, REQ5).
[`REQUIREMENTS.md` § 8](REQUIREMENTS.md#8-what-this-implies-technically) records
component by component where this implementation meets that design and where it
does not.

Further reading: ["aigov!=aio11y, part 2: Three tracks, one audit
question"](https://www.bearingnode.com/post/aigov-aio11y-part-2-three-tracks-one-audit-question)
names these Track 1/2/3, and ["part 3: Building Track
3"](https://www.bearingnode.com/post/aigov-aio11y-part-3-building-track-3)
specifies the design in full.

## Implications of findings

### Prior standing

Both issues went in on 2026-04-23, months before this reference
implementation existed. Their reception is why this repository exists, so it
appears here rather than glossed.

| Issue | State | Outcome |
|---|---|---|
| [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) — *RFC: Lineage for runtime actor-initiated data interactions* | **Open, engaged** | Two responses. `jakub-moravec` asked **which gaps we see** beyond non-static jobless lineage; `mobuchowski` asked whether [PR #4480](https://github.com/OpenLineage/OpenLineage/pull/4480) is similar. The work in this repository is our answer to both, and it is not yet posted on the thread. What happened to #4480 is set out below. Verified 2026-10-06 |
| [MCP #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638) — *Tracking: Data lineage for MCP tool calls* | **Closed after 4 hours** | *"AI-generated content with no disclosure or concrete mapping to MCP concepts."* |

**PR #4480 is the closest precedent, and it did not enter the core specification.**
It proposed an `AgentAttributionRunFacet`: a Run facet carrying an agent's
identifier and a signed attestation of the policy the agent acted under. On
2026-05-07 `mobuchowski` said he was "just not sure if that's in the scope of
OpenLineage" and that he could not judge the proposal himself; `jakub-moravec` had
called it "a little bit too tailored for a specific implementation". The author
took the route the maintainers offered, a custom facet hosted by the author with a
pointer from the OpenLineage documentation, and closed the PR unmerged on
2026-06-15. The author had also told the maintainers that #4484 asks a different
question: whether runtime actor-initiated interactions should be modelled in
OpenLineage at all, and at what layer. Our ask is narrower than #4480 in the way
the scope objection cares about: a pseudonymous reference to the call, with no
attestation and no authority claim (RAID D28). It does not escape the scope
question. **OpenLineage has not said whether any runtime-actor facet belongs in
the core specification, and a community or custom facet is the route it pointed
#4480 to.** Any reply on #4484 has to start there.

**On disclosure the rule stands, and it is met at the root of this repository,
not by a footnote here.** The
[AI contribution guidelines](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/CONTRIBUTING.md#ai-contributions)
require declaration, and the original filing did not comply — corrected, and
carried forward as a filing requirement for anything refiled upstream. **The
declaration itself is [`DISCLOSURE.md`](../DISCLOSURE.md)**: this lab is built
with AI throughout, no claim is made about which words in any file are
human-written or model-written, and that applies uniformly — frontier or
open-weight, this workstream's register included. A reader who wants to know
"was this AI-generated" already has the answer, standing, for the whole
repository, before they ask.

**On substance, #2638 closed in four hours with a single closing comment and no
discussion.** It was a tracking issue asking whether a gap exists between
infrastructure observability and data observability for MCP tool calls. Nobody
requested clarification before the closure. The closing comment named what was
missing, disclosure and a concrete mapping to MCP concepts, and the issue was
closed rather than left open for either.
The same question had been raised before: on OpenTelemetry's specification
repository, where it was discussed for seventeen months and closed in 2024 for
author inactivity, and it is live on OpenLineage from the streaming side. See RAID A08. It was not a question nobody was asking.

This repository is what that mapping looks like. Not because the closure
established that the argument was wrong, but because a working implementation is
the form of the argument nobody can file away. The `_meta` extension mechanism
rather than "MCP should carry identity". `tools/call` versus `resources/read`
rather than "OTel has a gap". A `SqlDriver` subclass in a real, widely-adopted
server rather than a proposal. Where a name is bespoke, as with the `_meta` key
and the trace-context facet, it is bespoke *deliberately*, and that is the ask
made visible.

Anything refiled upstream must (a) disclose AI assistance per each project's
contribution guidelines, and (b) lead with the implementation. Not because the
argument needed changing, but because form determines whether anyone reads it.
See RAID A08; the drafts themselves are private working documents, not published here — the gap is raised at OpenLineage #4484 (see above), and the facet proposals are not yet filed.

Not a synthetic scenario. An instrumented MCP server runs over a real
warehouse holding synthetic ObsInsure data, driven by a deterministic script now
and by [OpenWebUI](https://github.com/open-webui/open-webui) later.

### What OpenTelemetry and OpenLineage each carry — and what neither does

[![What each signal carries: the OTel span and the OpenLineage run event shown as objects, then an Euler diagram of OpenTelemetry span attributes, OpenLineage facets, what both carry, and the region inside the interaction that neither covers](artefacts/bearingnode-mcp-lineage-signal-scope.png)][blog-technical]

> **[Explore the interactive version →][blog-technical]** Select any attribute or facet for
> its definition, requirement level and source file; step through the worked
> example; and watch what tail sampling removes.

One MCP tool call is the frame both signals sit inside: OpenTelemetry records
that the call happened, OpenLineage records what data it touched, joined by
`trace_id` and `span_id` but never deriving one from the other.

The **fourth region** is the finding: inside the interaction, outside both
signals. The transform an agent performs after the rows leave the server, the
dataset a `tools/call` touched, and the authority it acted under. No span, no
facet, no observer. (MCP's own gap, no convention for carrying a caller's lineage
parentage across the boundary, is a separate, third finding, covered next. The
authority gap is stated, not asked: RAID D28.) Every name in the figure was verified on 2026-10-06 against the
published conventions and the OpenLineage client's generated facets. The span box
shows what the conventions define for such a span, not what this demonstration
emits (its own span carries only `lineage.run_id` and `lineage.actor_status`). All
the GenAI and MCP attributes carry `development` stability and may still change.

### Impact on the standards and their communities

**The three gaps, stated generally — and this is the reply owed on #4484.**
`jakub-moravec` asked on
[#4484](https://github.com/OpenLineage/OpenLineage/issues/4484), 2026-04-24,
*"what are the gaps that you see?"* Answering it credibly required building the
thing and finding out; that work is this repository. None of the three is
agent-specific or MCP-specific (RAID D24):

1. **No slot for who initiated a consumption event.** The one identity-bearing
   facet OpenLineage has, `OwnershipJobFacet`, is job-level and
   declaration-based — the wrong shape for the ad hoc case, where no job is
   declared in advance and the actor varies per run. A caller with a declared
   job is already served.
2. **No standard link to the decisioning context.** Joining a lineage event to
   the trace that produced it has no facet, so the link is bespoke wherever it
   exists.
3. **No way to mark the event as a distinct class** — **narrowed 2026-09-30, and
   partly closed by someone else.** `LineageFacet` 1-0-0 (2026-08-14) now
   distinguishes *declared* from *observed* lineage through `LineageJobFacet`'s
   JobEvent/RunEvent semantics, which is part of what this gap asked for. What
   remains unaddressed is marking an event as **actor-initiated**, and that is a
   property of the run rather than a type of entity in a data flow — so it folds
   into gap 1 rather than standing on its own. See item 3 under OpenLineage
   below.

The fourth region above breaks down into concrete changes across the three
standards this depends on — not one change each, in every case, and not all
of them specification changes. The fourth row of the table is there because it
is **not** an ask: the `lineage.*` run tags are a vocabulary this producer
defines for itself, inside a facet that already exists, and they are listed so
they are not read as a request to a fourth community.

| Standard | Gap | Proposed change | Status |
|---|---|---|---|
| **MCP** | No convention for carrying, across the tool-call boundary, any of the material from which caller identity is reconstructed on read; the key below carries lineage parentage, which is one such input and is deliberately not a principal | A standard `_meta` key carrying parent run ID, job namespace and job name. A caller populates it only if it emits its own run | Mechanism built; refiling planned. Original ask ([#2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638)) closed after four hours with a single comment, on disclosure and the lack of a concrete mapping |
| **OpenTelemetry** | `tools/call` has no defined data-resource attribute; sampling and retention default to lossy for governed-data calls | **(1)** Extend `mcp.resource.uri`, or add a `tools/call`-scoped sibling. **(2)** A Collector retention policy that keeps any trace carrying a lineage marker in full | **(1)** Not yet filed. **(2)** Built and proven here — see [§ Two traffic modes, and what each proves](#two-traffic-modes-and-what-each-proves) |
| **OpenLineage** | No facet for a per-run runtime actor; no standard facet for trace correlation | **Two new Run facets: who initiated this run, and which span caused it.** `run.facets.actor`, which does not exist, and `run.facets.traceContext`, which exists here only under this producer's own vendor prefix. Facet names illustrative, not proposed spellings. The before/after run event is in [§ OpenLineage](#openlineage) below. **Corrected 2026-09-30: two asks, not three** — the third, an `interaction-derived` value on the `type` field, is withdrawn against the shipped spec. See § OpenLineage item 3 | Thread: [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) (open). It raises the gap and asks how a runtime actor's identity should be expressed. The two facets are our proposed answer and are not yet posted there |
| **None — the `lineage.*` run tags** | A consumer cannot tell whether an event's datasets were parsed from statement text, read from the engine's resolved plan, or observed in execution. Two conformant events can sit at opposite ends of that scale and render identically in the same catalogue | **Not an ask.** Three keys carried in the standard `TagsRunFacet`, in a vocabulary this producer defines and closes — `lineage.derivation`, `lineage.completeness`, `lineage.actor` (REQ11, RAID D26). No specification surface is requested: the facet is shipped and free-form by design | Emitting since summer 2026. **Expressible, not interoperable** (RAID R14) — nothing in the specification obliges a consumer to preserve or surface a tag key it does not recognise (RAID I45) |

**The authority gap: stated, not asked (RAID D28).** Whether an agent acted on
behalf of a named user or on its own standing identity is not recorded anywhere
in this implementation, and none of the three standards carries it. We do not
ask any of them to carry it.

- **MCP:** nothing to change for this. The `_meta` key carries a pointer to the
  caller's run, not a principal, and we ask MCP only to agree a carrier for a
  reference (RAID D25).
- **OpenTelemetry:** the GenAI conventions have `gen_ai.agent.id`, `.name`,
  `.description` and `.version`, and no attribute for the authority an agent
  acted under (checked 2026-10-05 against `model/gen-ai/registry.yaml` in
  `open-telemetry/semantic-conventions-genai` at `cb10b70c1`, RAID A03).
- **OpenLineage:** the runtime-actor facet names the agent, not the authority.
  `OwnershipJobFacet` cannot carry it either: it is a Job facet, its owner
  examples are `application`, `user` and `team`, and it defines no agent type and
  no authority-model distinction (checked 2026-10-05 at tag `1.53.0`, RAID D10).

The gap can be closed later only if three things hold. The agent has an identity
in a system that can be queried. That system records the authority per call. The
event can be tied to that record. None of this is tested (RAID A28). Until then
this implementation can say which run and which trace, and which agent once the
actor facet is emitted. It cannot say whether the call was delegated or
autonomous.

#### MCP

1. **Specification gap.** Nothing defines a convention for carrying a caller's
   lineage parentage (parent run id and job) across the tool-call boundary — `_meta` is typed as an open
   object in the specification, so it supports it structurally, but no key or
   payload shape is agreed.
2. **Proposed change.** A standard `_meta` key carrying parent run ID, job
   namespace and job name — the substance of a refiled #2638. A caller populates
   it only if it emits its own run, so that the link points at something that
   exists. Parentage serves a caller with a declared job. An ad hoc caller has no
   run of its own to name, and for it the trace link is the correlation
   (RAID A22).
3. **Server-side implementation impact.** Every MCP server touching governed
   data needs retooling at its own data-access seam to emit lineage. No
   protocol-level shortcut exists, and no gateway or wrapper can supply this
   on a server's behalf — see [§ Where the instrumentation
   sits](#where-the-instrumentation-sits-and-what-that-implies) and [§ What
   this means for adoption](#what-this-means-for-adoption).
4. **Client-side implementation impact.** Callers that emit their own run have
   to actually populate the key. Today even a server that can read it gets nothing — no client,
   including this workstream's own driver, sends it, because there is
   nothing standard yet to send.
5. **Community impact.** This reaches the whole MCP server ecosystem, not
   just data-access servers narrowly — any `tools/call`-based integration
   touching governed data inherits the same gap, so it is an upstream,
   protocol-level ask rather than something solvable deployment by
   deployment.

#### OpenTelemetry

1. **Specification gap.** `tools/call`, the method this entire class of
   interaction depends on, has no defined attribute naming which data
   resource it touched — the adjacent `mcp.resource.uri` names a resource on
   `resources/read`, `resources/subscribe`, `resources/unsubscribe` and
   `notifications/resources/updated`, and not on `tools/call`.
2. **Proposed change.** Extend `mcp.resource.uri`, or add a
   `tools/call`-scoped sibling, into the actively-developing GenAI/MCP
   semantic conventions. Not yet filed.
3. **Collector-level implementation impact.** Sampling and retention cannot
   apply uniformly. Any trace carrying a lineage marker has to be retained
   in full regardless of the default rate — a Collector configuration
   pattern (`always-keep-data-access`), not a spec change, but the attribute
   fix means nothing without it (REQ1). Built and proven here — see [§ Two
   traffic modes, and what each proves](#two-traffic-modes-and-what-each-proves).
4. **Correlation implementation impact.** Joining back to OpenLineage
   requires trace/span ID to be reachable at the exact point lineage is
   emitted — already native to OTel's SDK, but adopters have to structure
   their instrumentation so that context is actually available at the
   emission seam, not merely present somewhere in the call stack.
5. **Community impact.** Affects every adopter instrumenting agents with
   OTel, not just this demo. A team fully instrumented on OTel alone (Track
   2) still cannot answer the audit question no matter how completely they
   capture spans — the standard was never built to hold this fact,
   regardless of how well it is used.

#### OpenLineage

**Two new Run facets in OpenLineage: who initiated this run, and which span
caused it.** That is the entire ask. The rest of this section is why those two,
why they belong on the Run rather than the Job, and what is deliberately not
being asked for.

**The run event today, and the run event being asked for.** Below is what
`mcp_server_ol` emits, with identifiers abbreviated. The `job`, `inputs` and
`outputs` blocks are shown although nothing is asked of them, for two reasons:
they are what makes *the diff is two lines* checkable rather than asserted, and
`job.facets` has to be visible for the argument about where the actor belongs to
be read off the object instead of taken on trust.

<table>
<tr>
<th align="left">TODAY — conformant, and no actor</th>
<th align="left">THE ASK — two added keys</th>
</tr>
<tr valign="top">
<td>

```json
"run": {
  "runId": "3d9ce90f…",
  "facets": {
    "tags": { "tags": [
      { "key": "lineage.derivation",
        "value": "parsed-intent" },
      { "key": "lineage.completeness",
        "value": "not-guaranteed" },
      { "key": "lineage.actor",
        "value": "absent" }
    ] },
    "bearingnode_traceContext": {
      "traceId": "4bf92f…",
      "spanId": "00f067…"
    }
  }
},
"job": {
  "namespace": "mcp-lineage-demo",
  "name": "mcp.execute_sql",
  "facets": { "sql": { … } }
},
"inputs":  [ "warehouse.obsinsure.premium" ],
"outputs": []
```

</td>
<td>

```json
"run": {
  "runId": "3d9ce90f…",
  "facets": {
    "tags": { "tags": [
      { "key": "lineage.derivation",
        "value": "parsed-intent" },
      { "key": "lineage.completeness",
        "value": "not-guaranteed" }
    ] },
    "actor": { … },
    "traceContext": {
      "traceId": "4bf92f…",
      "spanId": "00f067…"
    }
  }
},
"job": {
  "namespace": "mcp-lineage-demo",
  "name": "mcp.execute_sql",
  "facets": { "sql": { … } }
},
"inputs":  [ "warehouse.obsinsure.premium" ],
"outputs": []
```

</td>
</tr>
</table>

**The diff is two lines**: `run.facets.actor`, which OpenLineage does not have,
and `run.facets.traceContext`, which exists here only under this producer's own
vendor prefix. Two consequences follow, and neither is itself an ask.
`lineage.actor` has nothing left to report once the facet exists, so it goes.
`lineage.derivation` and `lineage.completeness` stay, because they answer a
different question (how the record was derived, REQ11) and ask nothing of anyone.
See the fourth row of the table above.

**`actor` is not shown populated on the left, and that absence is the finding
rather than a simplification of the example.** There is nothing to put there. No
MCP client sends a caller identity, including this workstream's own driver,
because no convention exists for a client to populate (REQ3). The tag reports
the absence rather than supplying a placeholder, which is why its value is
`absent` and not a hostname or a process name.

**Both facet names are illustrative.** `actor` and `traceContext` name the
shapes, not proposed spellings. #4484's own open question asks *how* actor
identity should be expressed; writing a settled name here would answer a
maintainer's question on their behalf.

**Why these are Run facets and not Job facets.** `job.facets` carries what is declared in advance of any execution;
`run.facets` carries what varies from one execution to the next. The one
identity-bearing facet OpenLineage has, `OwnershipJobFacet`, is a Job facet, and
correctly so: who owns a job is a property of the job, fixed when the job is
defined. An actor is not. A different agent, model, session or human principal
can initiate the same job on consecutive runs, and the span that caused a run to
exist is per-run by definition. Both facts vary per execution, so both belong on
the Run, and neither has a Job-level home to be extended.

**A modelling compromise in what we built (RAID I60).** The SQL text of each
statement is emitted as a Job facet (`job.facets.sql`) under one fixed job name,
`mcp.execute_sql`, because the specification has no run-level facet for it. That
puts per-run content on the Job, which is the placement the paragraph above says is
wrong for anything that varies per execution. We did not resolve it. It is the
same gap seen from the other side, and not a point scored for the argument: a
consumer that keeps job versions by their facets may see a new version for each
distinct statement, and we have not measured whether Marquez does.

**`mcp.execute_sql` is a value, not a structure (RAID D24).** It is the job name
this demonstration happens to use. Substitute `rest.GET /claims` and the event
above is identical in shape — same absent actor, same per-run initiating span,
same two missing facets. The gap is in the model; MCP is what made it visible.

The breakdown, gap by gap:

1. **Specification gap.** No facet exists for a per-run runtime actor. The
   one identity-bearing facet OpenLineage has — `OwnershipJobFacet` — is
   job-level and declaration-based, the wrong shape for the ad hoc case, where no
   job is declared in advance and an agent's identity is per call. A caller with
   a declared job is already served.
2. **Proposed change.** A runtime-actor facet on the Run, carrying
   agent/model/version/session as a pseudonymous reference. This is the answer we
   propose to the question
   [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484)
   asks, how a runtime actor's identity should be expressed. It is not yet posted
   there. The closest precedent, PR #4480, met a scope objection and left the core
   specification; see [Prior standing](#prior-standing).
3. **Withdrawn ask, and why — the record is kept rather than deleted.** This
   read: *an `interaction-derived` value on the currently-jobless `type` field,
   so the schema itself can distinguish a relationship declared before the run
   from one the call created.* It does not stand against the shipped
   specification, **verified 2026-09-30**. `LineageFacet.json` shipped
   **2026-08-14** at facet version **1-0-0** via
   [OpenLineage PR #4804](https://github.com/OpenLineage/OpenLineage/pull/4804),
   four months after #4484 was filed. In it, `LineageEntry` is a discriminated
   union whose `type` is a **closed enum** — `["DATASET"]` or `["JOB"]` — and it
   describes the **target** of a data flow, not the initiator. Confirmed in the
   shipped client at 1.53.0 (`generated/lineage.py`, absent at 1.52.0): the
   literals are enforced in code, and no field in the module carries an actor,
   initiator, trace or span. Adding `AGENT` would be a breaking schema change
   *and* would assert that an agent is the destination of a data flow, which is
   the wrong claim.

   **The distinction the ask wanted partly exists now, by another route.**
   `LineageJobFacet` carries *"on a JobEvent it is the job's declared lineage; on
   a RunEvent it is lineage observed during that run"* — declared versus
   observed, which is what the `type` value was reaching for. It does not close
   the ask: it is a Job/Dataset facet rather than a Run facet, and it carries no
   initiator. **So the remainder folds into the runtime-actor facet in item 2**,
   because the actor is not a type of entity in a data flow — it is a property
   of the run. The asks are two, not three.
4. **Correlation implementation impact.** Joining an event to its OTel trace
   has no standard facet either. This workstream carries trace ID and span
   ID on a bespoke `TraceContextRunFacet` under its own vendor prefix —
   itself part of the ask, not a finished mechanism others can rely on
   without adopting the same convention.
5. **Community impact.** Any OpenLineage consumer wanting "who acted" for
   interaction-derived lineage hits this gap — not an MCP-specific request, but
   a request for a class of lineage OpenLineage's model has no home for yet. The
   facet names the agent, not the authority it acted under, which is a stated gap
   (RAID D28).

### Where this sits in the Data & Information Observability framework

[![Where an agent's data access enters the framework](artefacts/bearingnode-mcp-lineage-framework-entry.png)][blog-technical]

**Data and Information Observability** — term of art **D/I O11y** — is:

> "The body of knowledge and practices for monitoring the health, performance,
> and organisational impact of Data and Information assets, as well as the
> capabilities to steward those assets."

— [*The Rise of Data and Information
Observability*](https://www.bearingnode.com/post/the-rise-of-data-and-information-observability-moving-beyond-traditional-methods).
Quoted verbatim wherever it appears; the two clauses are the definition, not
alternatives.

The workstream operates in the framework's **foundational** capability layer, not
its core one. An agent's tool call produces two signals. They enter at
**Connect**, and pass up through **Collect**, **Alert**, **Store** and
**Analyse**. The five core capabilities — Value, Discover, Track, Comply,
Govern — rest on that chain.

That ordering is the argument in one picture. **Every core capability is an
assertion about data access, and no assertion can be made about an access that
was never recorded.** So a missing convention at Connect does not degrade Govern
and Comply. It removes the ground they stand on, silently, while both continue to
report on the accesses that *were* recorded.

**This is why Track 3 is a Connect-layer problem and not a governance one.**
Track 2 instruments above Connect and reports healthy while the ground is
missing; the interceptor
["part 3"](https://www.bearingnode.com/post/aigov-aio11y-part-3-building-track-3)
specifies sits *at* Connect, which is the only place the record can be made.

The figure is a subset of the BearingNode connected cube rather than a
replacement for it: the cube's capability face renders the core layer, and this
drills one level below that face. The sourcing — including where the knowledge
graph and the published framework depiction disagree — is recorded in
[`artefacts/README.md`](artefacts/README.md).

## The reference implementation

### Data and deployment

**All data is synthetic.** Every party, contract, claim, address, tax ID,
bank account, phone number and email in `warehouse/data/*.txt` was generated
by a deterministic script for the sole purpose of giving this demonstration
something realistically-shaped to run against. None of it describes, was
derived from, or is intended to represent any real person, company, account
or transaction, living, dead, or corporate. Any resemblance to an actual
person or entity is coincidental — a statistical artefact of generating data
at population scale, not a reference to anyone real.

**This is not production software, and it must not be pointed at a real
system.** The lab-level [*Status of this work*](../README.md#status-of-this-work)
already says so for the whole repository: *"Nothing here is production
software. It is reference and evidence, offered as it is."* Concretely for
this workstream: do not set `WAREHOUSE_DSN` or `DATABASE_URI` to a real
database, do not run this stack against live infrastructure, and do not
treat any output — lineage events, traces, tool responses — as authoritative
about a real system. The default local Postgres container (§ *In-source
credential default*, [`mcp_server/README.md`](mcp_server/README.md)) exists
so the demo runs with zero configuration on a throwaway container; it is not
a suggestion for where real data or a real deployment belongs.

See [§ Scope](#scope) for what this demonstration deliberately does not
cover — query languages and data forms beyond structured SQL, and the limits
of the tool-call approach itself.

### Run it

```bash
docker compose up -d

# one-off: load ObsInsure synthgen data into the warehouse
# Postgres is published on host port 5433, not 5432 — see docker-compose.yml
cd warehouse \
  && WAREHOUSE_DSN="postgresql://postgres:postgres@localhost:5433/warehouse" \
     uv run --with-requirements requirements.txt python load_obsinsure_data.py \
  && cd ..

# fire 100 deterministic tool calls at the MCP server
cd driver && uv run --with-requirements requirements.txt python driver.py 100

# or: N mixed sessions (ordinary + one governed span each) — see
# "Two traffic modes, and what each proves" below
uv run --with-requirements requirements.txt python driver.py 20 --mixed
```

**Run the stack on a machine and network you trust.** The compose file publishes
Postgres (5433), Marquez, Jaeger, the collector and both MCP endpoints (8000 and
8001) on all of the host's network interfaces, not only on `localhost`. Postgres
uses the superuser login `postgres`/`postgres`, and the two MCP endpoints take no
authentication and run arbitrary SQL as that superuser, which includes running
commands inside the Postgres container. Anyone who can reach those ports can do the
same. The credentials are the well-known defaults of a throwaway demo and the data
is synthetic, but the stack is not meant to be reachable from other machines
(RAID I61).

Then compare:

- **Jaeger**, http://localhost:16686. Expect **every trace retained**, whatever
  the driver produced — not a 10% sample, and not a fixed count.
  `otel-collector-config.yaml`'s `always-keep-data-access` policy runs first
  and keeps an entire trace the moment any span in it carries
  `lineage.run_id`; the probabilistic 10% policy only ever gets a turn on
  traces that policy skips. Every call this driver fires is a governed
  `execute_sql` call, so every trace already qualifies before sampling is
  reached. See *Two traffic modes, and what each proves* below.
- **Marquez**, http://localhost:3033. Expect a run for every call the driver
  made, every one `COMPLETED`, under a single stable job name
  (`mcp.execute_sql`) — and the same count Jaeger shows, because that parity
  is the point. (More than N: `driver.py` fires one `CREATE TABLE` call up
  front, plus one `INSERT` on every tenth iteration, on top of the N `SELECT`
  queries — for the `driver.py 100` example above, that's 111.) **This is the
  opposite of the frozen `mcp_server/` exhibit's behaviour** — that server's
  job identity is intentionally synthetic-per-invocation, degrading the
  Marquez job list into one-run-per-job noise, documented in its own
  docstring (`mcp_server/server.py`) as a finding about a from-scratch server
  with no durable job concept. `mcp_server_ol` wraps `postgres-mcp`, which
  does not have that problem — one job name, many runs against it, the
  ordinary shape Marquez expects. Both behaviours are real; they describe
  different servers, not the same one at different times.

Verified end to end on **2026-09-30 under `openlineage-python` and
`openlineage-sql` 1.53.0**, on a stack recreated from empty volumes: flat mode at
N=100 produced **111 runs in Marquez, all `COMPLETED`, under the single job name
`mcp.execute_sql`, and 111 traces retained in Jaeger** — exact parity. Counts
must be read off a clean stack: the integration suite fires its own traffic under
`agent-*` job names, so running it first inflates both sides.

Previously verified on 2026-09-27: flat mode at N=37 produced 42 traces in
Jaeger and 42 runs in Marquez, all `COMPLETED` — exact parity, at a volume
that isn't 100 or 111, because the claim is about retention holding at any
volume, not about a specific count. The same run's mixed mode (N=9) confirmed
the trace-scoped mechanism directly: exactly one span per trace carries
`lineage.run_id`, and all six spans in all nine traces were retained anyway.
Also verified 2026-08-23 (111 of 111, at N=100) and 2026-08-06, on earlier
builds of the same stack.

#### Two traffic modes, and what each proves

**Flat** (`driver.py N`) is 100% governed — every call is `execute_sql`,
every span carries `lineage.run_id`, and every trace is kept by
`always-keep-data-access` ahead of the 10% probabilistic policy. That's
correct, but it doesn't demonstrate anything interesting about the policy,
because there's no ungoverned traffic for it to discriminate against.

**Mixed** (`driver.py N --mixed`) is the real proof. Each session rides three
ordinary, non-governed spans alongside one governed `execute_sql` call, all
in the same trace. Exactly one span per trace carries `lineage.run_id` — the
other five are retained purely as a side effect of riding alongside it. That
is the policy actually working: trace-scoped, not span-scoped, keeping a
whole trace the moment any part of it touches governed data.

**The cost is real.** In a deployment where governed calls are a minority of
volume, one governed span makes its entire trace durable for as long as
retention holds — `trace_id` stops being just an observability pointer the
moment a governed span rides in it (RAID R13).

### Beyond the reference implementation

This isn't only a server with a finding attached. It's a package,
deliberately: the reference implementation, the synthetic dataset that drives
it, and a test framework proving the traffic behaves as the requirements
demand — because a claim this specific needed something a reader could run and
check, not a diagram to take on faith.

| Path | What it is |
|---|---|
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | The eleven testable requirements and the obligation-side case, for CDAO/CRO/CAIO/third-line/compliance |
| [`evidence-matrix.md`](evidence-matrix.md) | Scores this reference implementation against every requirement — two met, nine partially met, none unmet — each row reproducible from a command |
| [`Status/RAID.md`](Status/RAID.md) | The risk/assumption/issue/decision register. Every claim in this README and REQUIREMENTS.md traces back to an entry here |
| [`mcp_server_ol/`](mcp_server_ol/) | The active reference implementation — the instrumented `postgres-mcp` server this demo actually runs |
| [`mcp_server/`](mcp_server/) | A frozen, unrepaired exhibit — an earlier, from-scratch server design, kept as a documented finding rather than deleted |
| [`driver/`](driver/) | The test client that fires tool calls at the server, flat and mixed traffic modes |
| [`warehouse/`](warehouse/) | The synthetic ObsInsure dataset and its loader (the generator is private) |
| [`artefacts/`](artefacts/) | The published figures (Euler diagram, framework-entry, call-chain, event-lifecycle) and their source |

## Architecture

### Topology and call chain

Jaeger (traces) and Marquez (lineage) are independent write paths with
independent completeness guarantees, which is why they stay visible as two
separate UIs rather than one merged view. The Postgres *instance* underneath
both is shared purely for infrastructure convenience: Marquez gets its own
database (`marquez`), and the ObsInsure data lives in a separate database
(`warehouse`, schema `obsinsure`).

```
                 ┌──────────────┐  OTLP (tail-sampled)   ┌────────┐
                 │ OTel Collector│───────────────────────▶│ Jaeger │
                 └──────▲───────┘                         └────────┘
                        │ spans
┌────────────┐   MCP    │
│ driver.py  │─────────▶│  mcp-server (execute_sql)
│ (or OWUI)  │          │
└────────────┘          └──────────────────────────────▶ Marquez (every event)
                                     │
                                     ▼
                              Postgres: warehouse.obsinsure.*
```

[![The call chain of one agent tool call: OTel spans and OpenLineage events for a single tools/call, with the MCP _meta key and the two proposed OpenLineage Run facets marked as asks against the standard facets around them, ending in a two-column before/after of the run event itself — the same object as § OpenLineage above, with the two added keys and everything else unchanged](artefacts/bearingnode-mcp-lineage-call-chain.png)][blog-technical]

The diagram above is the topology; this is the same call chain traced end to
end for one real `tools/call`, spans and lineage events both shown, with each
ask marked at the point in the chain it is made: **part one**, the `_meta`
lineage-parentage key MCP has not named yet, and **part two**, the two Run facets
proposed to OpenLineage — trace context and runtime actor — shown alongside the
standard facets the implementation uses, and marked as proposed rather than
mixed in with them. The runtime-actor facet is not emitted, and the figure shows
why: `lineage.actor = absent` is the stand-in that records the gap, not the ask.

A companion to that figure is
[`artefacts/bearingnode-mcp-lineage-event-lifecycle.png`](artefacts/bearingnode-mcp-lineage-event-lifecycle.png)
(RAID D27). It draws the same chain as a bow tie. The left side is what is
captured as the producer's call goes out, the middle is where it lands, and the
right side mirrors the left: the steps an auditor, SRE or governance analyst takes
to recreate the event. It marks what is an ask and what is assumed.

![Capture an event, recreate it on read: on the left, what is captured as the producer's call goes out; on the right, the three steps an auditor, SRE or governance analyst takes to recreate the event from it](artefacts/bearingnode-mcp-lineage-event-lifecycle.png)

**The read scenario.** An auditor, SRE or governance analyst asks who acted on a
dataset, and why. They recreate the event in three steps. Each step is a separate
query by an explicit identifier. Nothing is inferred, and nothing in the event
carries identity itself.

1. **Query Marquez, by dataset and time.** The run comes back as it was received:
   its parent run id and job, its tags and the trace reference. Once the
   runtime-actor facet exists (an ask, not yet emitted), it adds a pseudonym.
2. **Follow the trace in Jaeger, by `traceContext`.** This gives the reasoning
   trace: what was asked and what the agent decided. It resolves only if the
   client injected `traceparent` and the trace is still held. Both are
   assumptions.
3. **Resolve the pseudonym, authorised access only.** This is a separate query to
   a separate system, with its own access control and retention (REQ4). It sits
   outside this implementation and is a deliberate second step.

**What the event carries that we do not redact, and what we assume about the
store.** The caller reference is a pseudonym (REQ4), and nothing here reads or
constructs identity. The event also carries the statement text (`job.facets.sql`)
and, when a statement fails, the database's own error text, and both are passed
through as they arrive. An agent that writes a literal into a statement, or a
database error that echoes one, puts that value into Marquez, and the error text is
also attached to a metric attribute. This implementation does not mask, hash or
reject any of it. It assumes that whoever runs the stack applies appropriate
anonymisation or pseudonymisation in the stores the events land in, and treats them
as holding personal data. That is the operator's responsibility and not the
emitter's (RAID A29, I59). The data in this demonstration is synthetic.

Each fact captured on the left of the figure has a step on the right that
recreates it, with one limit. The `_meta` key does not carry identity. It carries
the parent run id and the trace link, and from them the run and its reasoning
trace can be rebuilt. Who acted can be rebuilt only if the runtime-actor facet is
emitted and the chain in RAID A28 holds. Delegated versus autonomous cannot be
recovered from the event (RAID D28).

**Two departures from the rules in `AGENTS.md`, stated here and left open.** Neither
changes what the demonstration shows. The span attributes this implementation adds, `lineage.run_id`, `lineage.dropped`,
`lineage.actor_status` and `lineage.governed`, are not vendor-prefixed, although
the facet and the `_meta` key are, and no conformant MCP attribute sits beside
them (the demonstration emits none). A deployment should rename them to a prefix it
owns, and that is best settled together with the placeholder `_schemaURL` and
`producer` URL (RAID I63, I56, I57). And the server emits lineage synchronously inside an `async`
method, adds a one-second span flush to every call, emits an event for every
statement including the catalogue queries behind the schema-listing tools, and
counts a missing request context twice per call (RAID I62).

### Where the instrumentation sits, and what that implies

The deployment topology above says nothing about *where in the stack* lineage
gets emitted, and that is the question an estate will ask first. Two things in
this repository carry the name "driver", which does not help:

- `driver/driver.py` is the **test client**. It fires tool calls at the server.
  It is a load generator and has nothing to do with lineage.
- `mcp_server_ol/src/mcp_server_ol/driver.py` is the **instrumentation**. It
  subclasses postgres-mcp's own `SqlDriver`. We did not write a database driver.

```
  Agent / LLM
      │
      │  MCP protocol   ── tools/call  {name, arguments}
      │                    _meta carries lineage parentage  ← our MCP ask
      ▼
  postgres-mcp server          9 tools
      │                        execute_sql(sql=...)      ← SQL is an argument
      │                        get_object_details(...)   ← SQL is NOT
      ▼
  SqlDriver.execute_query(query)     ◄── WE INSTRUMENT HERE
      │                                  every tool funnels through it
      ▼
  psycopg / psycopg_pool
      │
      ▼
  Postgres
```

**Why not higher up.** Of postgres-mcp's nine tools, only three take SQL as an
argument. `list_schemas`, `list_objects`, `get_object_details`,
`analyze_workload_indexes`, `analyze_db_health` and `get_top_queries` build and
execute SQL internally, and the protocol never sees it.

A gateway, proxy or SDK middleware reading `tools/call` therefore captures a
generic run-this-SQL tool and misses every purpose-built one. That is the worse
failure, because it fails silently on exactly the tools an organisation writes.
RAID D02 rejects the proxy on a second ground: a component that parses somebody
else's traffic infers, and inference is not evidence.

`SqlDriver.execute_query` is the choke point. All nine tools funnel through it,
which is why one subclass covered the whole server.

### What this means for adoption

> **The finding, stated plainly: MCP servers that call out to data will need
> refactoring to emit lineage.** There is no protocol-level shortcut and no
> wrapper anybody can ship on your behalf. This is our **working assumption**,
> not a prescription — the route belongs to the community and to adopting
> organisations. Recorded as **RAID D17** (why the location is structural) and
> **RAID A12** (what we assume adopters do, and why we do not decide it).

**Two separate things, and only one of them costs anybody anything.**

**Carrying lineage parentage costs servers nothing.** The MCP specification
types `_meta` as an open object (the Python SDK sets `extra: allow`), so a bespoke
key travels today against an unmodified SDK. A server that has never heard of the key ignores it. The gap is
agreement on the key name and payload shape, a convention rather than a protocol
change. That is the whole of our MCP ask, and its size is the point: the
protocol can carry lineage parentage forward, and here it can do nothing else.

**Emitting lineage means every MCP server that touches data has to emit it.** No
protocol-level shortcut exists, because only the process that executed the
statement can declare what it touched. We do not propose a wrapper per server,
and no product could supply one. Our position is that this is what observable
MCP tool calling costs, in the same way somebody had to instrument every HTTP
framework for OpenTelemetry before distributed tracing became ordinary.

**The cost varies more than this demonstration shows.** postgres-mcp was cheap
because it already had a `SqlDriver` abstraction behind a module-level factory,
so a subclass and a factory swap sufficed. A server that calls its database
library inline has no such seam, and the work there is a restructure rather than
a subclass. This repository shows the good case, and says so here rather than
letting a reader generalise from it.

**And the wrapper here is a demonstration device, not the proposal.** We
subclassed to instrument a real server without forking it, which makes the
evidence about deployed ecosystem tooling rather than about a server invented for
the purpose (RAID D03). Read it as a measurement of how small the seam is, not as
a distribution model.

## Scope

**The unit of work under test is a single interaction: an LLM or agent calls an
MCP tool, and that tool touches a data resource.** Everything here serves that
one path.

**Which MCP protocol revision was exercised.** The reference implementation and
its tests run on MCP SDK 1.28.1, whose latest protocol revision is 2025-11-25, and
the demonstration driver uses SDK 1.9.0. They use the `initialize` handshake and
server-side sessions. The 2026-07-28 revision removes both, and nothing here has
been run against it. Where this README says what the 2026-07-28 specification
defines (RAID D04), that is a reading of the specification text, not something the
demonstration exercised.

**And the interaction is ad hoc.** The discriminator is whether the work was
declared in advance. That is the **declaration-based** versus
**interaction-derived** distinction that [`REQUIREMENTS.md`
§ 8](REQUIREMENTS.md#8-what-this-implies-technically) defines, and it is a
property of the *work*, not of the caller. This work does not address static,
declaration-based work, including a *scheduled* agent doing nightly work against
a governed dataset. That work is a job declared before it runs, which the
existing producer model already serves. In scope is ad hoc access by a human, by
an MCP call on behalf of a human, or by an agent acting on its own authority. In
none of these was a job declared before the access happened, so there is nothing
to hang parentage from.

> ### This is scoped to structured data reached through SQL
>
> Stated up front because it bounds every claim below, and because the omission
> carries consequences (RAID D16, R12).
>
> **Not addressed here:** non-SQL query languages, covering SPARQL, Cypher,
> Gremlin and other graph traversals. Also **unstructured data entirely**:
> documents, object stores, vector stores and embedding retrieval, in both
> directions. Agents now read unstructured sources *and increasingly write and
> push them*, and that is where agent data access grows fastest.
>
> **Why this is not simply the next step.** Dataset identity for unstructured
> retrieval is an unsolved problem in its own right. When an agent retrieves
> three chunks from a vector index, what is the dataset? The index, the source
> document, or the chunk? OpenLineage's naming specification answers none of
> these. Extending the demonstration would not extend the argument. It would
> replace the argument with a harder, prior question.
>
> The design does not assume SQL. The emission seam is a driver subclass at the
> point of execution, which is language-agnostic by construction, and only the
> parser is SQL-specific. But nothing here reaches beyond SQL, and this document
> claims nothing further.
>
> **A third case sits outside the approach, not only outside this
> demonstration.** A person exports a spreadsheet, attaches it to a chat, and the
> agent reasons over the contents. The data arrives as conversation content, so
> the tool boundary is never crossed. **Verified: the tool-call route cannot
> observe this, structurally.** Beyond that we make an explicit assumption rather
> than a claim (RAID A13): a content platform's access auditing and the agent
> harness's own telemetry may each hold a signal, **we have examined neither**,
> and we do not assert that the interaction is unobservable by any means. The
> posture matches the one taken towards platform audit throughout: complementarity,
> never insufficiency. What holds under every outcome is that **no convention
> joins those records to a decision**, and that an export is a copy which may
> retain no link to its source asset. See `REQUIREMENTS.md` § 11a.

**In scope**

- The **MCP client**: the agent, or the deterministic driver standing in for
  one. Source of actor and job identity, per RAID D01.
- The **MCP server**: a real, unmodified `postgres-mcp` instrumented for
  OpenLineage. Source of dataset identity, because it executes the statement.
- The **data resource**: Postgres, the ObsInsure warehouse.
- The two signals that interaction produces, and their different completeness
  guarantees: OTel spans to Jaeger, OpenLineage events to Marquez.
- Direct client-to-server transport (`stdio`, SSE, streamable HTTP).

**Out of scope**

- **Static, declaration-based work, which we hold that OpenLineage already
  serves (RAID A26).** A scheduled pipeline, and equally a **scheduled agent**
  doing a nightly piece of work against a governed dataset, has job identity,
  parent job identity and a producer definition today, and those mechanisms
  work. The gap this workstream describes is not in that case, and nothing here
  asks for anything on its behalf.

  **This scope decision rests on an assumption, so both appear here, and we
  invite the challenge.** We have not surveyed scheduled-agent deployments. If
  that case breaks somewhere the existing producer model does not reach, the
  boundary is drawn in the wrong place and we would want to know. A26 records it
  as an assumption rather than a finding for exactly that reason.

  **The two scopes touch at one seam, and it is a complement rather than a
  counter-example.** A scheduled agent that reaches a governed dataset *through
  MCP* has a parent run id that its orchestrator already minted, and nothing
  carries it across the tool-call boundary. The chain is intact up to the MCP
  seam and breaks across it. The MCP `_meta` ask above closes that wire gap for
  any caller that has a run id to carry. That is a noted consequence, not a
  claim made on the static case's behalf: nothing here is asked for on behalf of
  scheduled work, and the gap claim does not reach it. Parentage serves that
  case. The trace reference serves the ad hoc one, where no parent run exists to
  point at.

- **MCP gateways, proxies and federation**, including
  [Context Forge](https://github.com/IBM/mcp-context-forge) and BearingNode's
  fork of it. Gateway topologies raise real and related questions (RAID R06,
  I24), and we *defer them rather than dismiss them*: nothing here should make
  them harder to add later. But they are not what this demonstration is about,
  and the gap exists without a gateway.
- Multi-hop or agent-to-agent chains beyond one client and one server.
- **Non-SQL query languages and unstructured data.** See the boxed statement
  above. This is the most consequential boundary here and the one a reader is
  most likely to raise (RAID D16, R12).
- **Data reaching a decision without a tool call**, such as a spreadsheet
  attached to a chat. Out of scope for the approach rather than for this build,
  and what other planes record about it is a stated assumption we have not tested
  (RAID A13).
- Non-Postgres data resources.
- **The LLM plane, assumed present rather than absent (RAID A09).** Nothing here
  instruments the model: no prompts, completions, token accounting or
  tool-selection reasoning. That belongs to OpenTelemetry's GenAI semantic
  conventions, which exist, develop alongside the MCP conventions in
  `open-telemetry/semantic-conventions-genai`, and run in production today. Our
  own OpenWebUI instance emits them.

  **This scope decision rests on an assumption, so both appear here.** The join
  needs no new mechanism. A trace consists of spans, so the agent's GenAI spans
  and the server's `mcp.execute_sql` span belong to **one trace** and meet
  without anyone inventing a correlation. We expect the parent run id and trace link
  that arrive in `_meta` to originate from that already-instrumented runtime.

  *If the assumption fails for a given estate*, the gap this workstream
  describes does not change, but the caller half of the demonstration has
  nothing on the other end of the link. See A09 for the stability caveat: those
  conventions carry `development` stability, so names will move.
- Production concerns: auth, multi-tenancy, retention, scale.

- **Run shapes other than a single interaction.** One tool call, one run, is the
  unit of work. A long-running job spanning many traces and many spans is out of
  scope (RAID D22), and **this is a bound on the claim, not only on the build** —
  see the note below. Added 2026-09-30 after the case was raised at the
  OpenLineage TSC. `REQUIREMENTS.md` § 11 states the adverse scenario.

**This work is tightly scoped, and we think the findings reach further than we
are claiming.** The cases above are new and deliberately narrow. We believe
several of the findings here, and several of the specification changes they
imply, would generalise to other areas, and we are not alone in thinking so. At
the OpenLineage TSC a maintainer proposed a **generic** trace-context foundation
rather than an MCP-specific one, so the community is already arguing the
generalisation as well as we are (RAID D24). The run-shape bound in the list
above is the other example: it is there because a maintainer raised it, not
because we thought of it. We do not claim those wider cases here, and the
boundary above is where the claim stops, but we think they are real.

**If one of them is yours, we would rather have a test than agreement.** Fork
this repository, write new tests against the reference implementation that
exercise the case you think generalises, and raise
[issues and pull requests](https://github.com/BearingNode/bearingnode-lab/issues).
We will work through the implications in the open, against the register. A
reference implementation exists so that a question about scope can be settled
by running something.

**Why the boundary sits here, and what it does and does not bound.** The simplest
possible interaction shows the whole gap. One agent, one tool call, one table.
Anything that enlarges the *topology* — a gateway, a second hop, another data
resource — enlarges the demonstration without strengthening the argument, and
invites the reply that the architecture caused the problem rather than the
protocol. **Run shape is different, and the distinction matters.** Changing it
does not merely enlarge the demonstration: the trace reference this design rests
on names the span that initiated the run, which is singular by construction here
and has no single answer in a job spanning many traces. So a multi-trace job is
excluded from the **claim**, not just absent from the build, and the mechanism
that would serve it is a different one (RAID D22). Stating which of these two
kinds a boundary is, is the thing that was missing: the bound existed, but it
read as *we kept the build small*.

<!-- The two posts this workstream cites — the leadership pre-read and the
     technical deep dive behind these figures. Interactive figures are
     published on the blog, deliberately not on GitHub: see artefacts/README.md
     § "Why the interactive figures aren't embedded on GitHub". -->
[blog-leadership]: https://www.bearingnode.com/post/agentic-lineage-mcp-dio11y
[blog-technical]: https://www.bearingnode.com/post/mcp-agent-data-dio11y

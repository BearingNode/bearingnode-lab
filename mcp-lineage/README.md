# mcp-lineage

<!-- build: dc06a539fd7e89b2 -->

> **All data is synthetic. This must never touch a production system.**
> See *Data and deployment*, below, and the
> lab-level [*Status of this work*](../README.md#status-of-this-work).

## TL;DR

> **The opportunity.** LLM agents now reach governed data directly through MCP —
> sometimes on behalf of a human being, or acting autonomously — and currently
> none of OpenTelemetry, MCP's own conventions, or OpenLineage records what data
> they touched, on whose authority, or where it went. That gap is closable.
>
> **What we built.**
>
> - **Requirements and evidence.** Ten testable requirements (REQ1–REQ10) for
>   what an agent-mediated interaction with governed data must produce as
>   evidence, and an evidence matrix scoring this workstream's own reference
>   implementation against every one of them: four met, six partially met, none
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
>   Postgres warehouse — open-source components wherever one already existed,
>   rather than a bespoke stack.
> - **Community engagement, already under way.** We raised this with the
>   OpenLineage and MCP communities months before this reference implementation
>   existed —
>   [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484)
>   (open, engaged) and
>   [MCP #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638)
>   (closed without engagement). This work goes further. Below, we break out the
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
>   don't use it. Instead, the reference implementation triangulates: a bespoke
>   run facet carries the trace ID and span ID back to the OTel trace, and
>   identity, where it exists at all, lives there rather than on the lineage
>   event itself. Absent that join, the event just tags itself
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
> - **MCP** needs a convention for carrying caller identity at the tool-call
>   boundary. We built the mechanism — a server-side reader against an
>   unmodified SDK — but no client, including our own demo driver, populates it
>   yet, because the key itself isn't standard.
>
> Scored against the ten requirements above: four met, six partially met, none
> unmet. **The missing evidence for agentic access to governed data is not an
> open research question — it is three specific changes to three specific
> standards, verified against a working implementation of two of them.**
>
> **[`REQUIREMENTS.md`](REQUIREMENTS.md) states this case in full**, ten
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
it produces — which datasets were read, how, and what decision they fed — we
call **decision lineage**.
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
| [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) — *RFC: Lineage for runtime actor-initiated data interactions* | **Open, engaged** | Two maintainer responses. `jakub-moravec` asked **which gaps we see** beyond non-static jobless lineage; `mobuchowski` pointed at [PR #4480](https://github.com/OpenLineage/OpenLineage/pull/4480). **Neither answered yet — the work that answers them is this repository.** Verified 2026-07-29 |
| [MCP #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638) — *Tracking: Data lineage for MCP tool calls* | **Closed after 4 hours** | *"AI-generated content with no disclosure or concrete mapping to MCP concepts."* |

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

**On substance, #2638 closed in four hours with no engagement.** It was a
tracking issue asking whether a gap exists between infrastructure observability
and data observability for MCP tool calls. Nobody requested clarification, and
nobody ever asked for the "concrete mapping" the closing comment called for.
Meanwhile the same question was already open on OpenTelemetry's specification
repository, a seventeen-month discussion, and is live on OpenLineage from the
streaming side. See RAID A08. It was not a question nobody was asking.

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
See RAID A08; the drafts themselves are private working documents, not published here — the ask itself is filed at OpenLineage #4484 (see above).

Not a synthetic scenario. An instrumented MCP server runs over a real
warehouse holding synthetic ObsInsure data, driven by a deterministic script now
and by [OpenWebUI](https://github.com/open-webui/open-webui) later.

### What OpenTelemetry and OpenLineage each carry — and what neither does

[![What each signal carries: an Euler diagram of OpenTelemetry span attributes, OpenLineage facets, what both carry, and the region inside the interaction that neither covers](artefacts/bearingnode-mcp-lineage-signal-scope.png)][blog-technical]

> **[Explore the interactive version →][blog-technical]** Select any attribute or facet for
> its definition, requirement level and source file; step through the worked
> example; and watch what tail sampling removes.

One MCP tool call is the frame both signals sit inside: OpenTelemetry records
that the call happened, OpenLineage records what data it touched, joined by
`trace_id` and `span_id` but never deriving one from the other.

The **fourth region** is the finding: inside the interaction, outside both
signals. The transform an agent performs after the rows leave the server, the
dataset a `tools/call` touched, and the authority it acted under. No span, no
facet, no observer. (MCP's own gap — no convention yet for carrying that
authority across the boundary at all — is a separate, third finding, covered
next.) Every name in the figure was verified on 2026-07-27 against the
published conventions and the OpenLineage client's generated facets; all the
GenAI and MCP attributes carry `development` stability and may still change.

### Impact on the standards and their communities

The fourth region above breaks down into concrete changes across the three
standards this depends on — not one change each, in every case, and not all
of them specification changes:

| Standard | Gap | Proposed change | Status |
|---|---|---|---|
| **MCP** | No convention for carrying caller identity across the tool-call boundary | A standard `_meta` key carrying parent run ID, job namespace and job name | Mechanism built; refiling planned — original ask ([#2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638)) closed without engagement |
| **OpenTelemetry** | `tools/call` has no defined data-resource attribute; sampling and retention default to lossy for governed-data calls | **(1)** Extend `mcp.resource.uri`, or add a `tools/call`-scoped sibling. **(2)** A Collector retention policy that keeps any trace carrying a lineage marker in full | **(1)** Not yet filed. **(2)** Built and proven here — see [§ Two traffic modes, and what each proves](#two-traffic-modes-and-what-each-proves) |
| **OpenLineage** | No facet for a per-run runtime actor; no standard facet for trace correlation | A runtime-actor facet on the Run, an `interaction-derived` value on the `type` field, and standardising the trace-correlation facet this reference implementation carries under its own prefix | Filed as [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484) (open, engaged) |

#### MCP

1. **Specification gap.** Nothing defines a convention for carrying a caller's
   lineage identity across the tool-call boundary — `_meta` supports it
   structurally (`extra: allow`), but no key or payload shape is agreed.
2. **Proposed change.** A standard `_meta` key carrying parent run ID, job
   namespace and job name — the substance of a refiled #2638.
3. **Server-side implementation impact.** Every MCP server touching governed
   data needs retooling at its own data-access seam to emit lineage. No
   protocol-level shortcut exists, and no gateway or wrapper can supply this
   on a server's behalf — see [§ Where the instrumentation
   sits](#where-the-instrumentation-sits-and-what-that-implies) and [§ What
   this means for adoption](#what-this-means-for-adoption).
4. **Client-side implementation impact.** Callers have to actually populate
   the key. Today even a server that can read it gets nothing — no client,
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
   resource it touched — the adjacent `mcp.resource.uri` exists but scopes
   only to `resources/read`.
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

1. **Specification gap.** No facet exists for a per-run runtime actor. The
   one identity-bearing facet OpenLineage has — `OwnershipJobFacet` — is
   job-level and declaration-based, the wrong shape for an agent's per-call
   identity.
2. **Proposed change.** A runtime-actor facet on the Run, carrying
   agent/model/version/session as a pseudonymous reference — filed as
   [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484),
   open and engaged.
3. **Schema-level companion change.** An `interaction-derived` value on the
   currently-jobless `type` field, so the schema itself can distinguish a
   relationship declared before the run from one the call created — also
   part of #4484's ask. See [`REQUIREMENTS.md` §
   8](REQUIREMENTS.md#8-what-this-implies-technically).
4. **Correlation implementation impact.** Joining an event to its OTel trace
   has no standard facet either. This workstream carries trace ID and span
   ID on a bespoke `TraceContextRunFacet` under its own vendor prefix —
   itself part of the ask, not a finished mechanism others can rely on
   without adopting the same convention.
5. **Community impact.** Any OpenLineage consumer wanting "who acted, under
   what authority" for interaction-derived lineage hits this gap — not an
   MCP-specific request, but a request for a class of lineage OpenLineage's
   model has no home for yet.

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
python driver.py 20 --mixed
```

Then compare:

- **Jaeger**, http://localhost:16686. Expect **all 111 traces retained**, not
  a 10% sample. `otel-collector-config.yaml`'s `always-keep-data-access`
  policy runs first and keeps an entire trace the moment any span in it
  carries `lineage.run_id`; the probabilistic 10% policy only ever gets a
  turn on traces that policy skips. Every call this driver fires is a
  governed `execute_sql` call, so every trace already qualifies before
  sampling is reached. See *Two traffic modes, and what each proves* below.
- **Marquez**, http://localhost:3033. Expect all 111 runs, every one
  `COMPLETED`, under a single stable job name (`mcp.execute_sql`). (111, not
  100: `driver.py` fires one `CREATE TABLE` call up front, plus one `INSERT`
  on every tenth iteration, on top of the 100 `SELECT` queries.) **This is
  the opposite of the frozen `mcp_server/` exhibit's behaviour** — that
  server's job identity is intentionally synthetic-per-invocation, degrading
  the Marquez job list into one-run-per-job noise, documented in its own
  docstring (`mcp_server/server.py`) as a finding about a from-scratch
  server with no durable job concept. `mcp_server_ol` wraps `postgres-mcp`,
  which does not have that problem — one job name, many runs against it, the
  ordinary shape Marquez expects. Both behaviours are real; they describe
  different servers, not the same one at different times.

Verified end to end on 2026-08-23: 111 of 111 runs in Marquez, 111 of 111
traces retained in Jaeger, against the live stack, not asserted from an
earlier run. (Also verified 2026-08-06, on an earlier build of the same
stack.)

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
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | The ten testable requirements and the obligation-side case, for CDAO/CRO/CAIO/third-line/compliance |
| [`evidence-matrix.md`](evidence-matrix.md) | Scores this reference implementation against every requirement — four met, six partially met, none unmet — each row reproducible from a command |
| [`Status/RAID.md`](Status/RAID.md) | The risk/assumption/issue/decision register. Every claim in this README and REQUIREMENTS.md traces back to an entry here |
| [`mcp_server_ol/`](mcp_server_ol/) | The active reference implementation — the instrumented `postgres-mcp` server this demo actually runs |
| [`mcp_server/`](mcp_server/) | A frozen, unrepaired exhibit — an earlier, from-scratch server design, kept as a documented finding rather than deleted |
| [`driver/`](driver/) | The test client that fires tool calls at the server, flat and mixed traffic modes |
| [`warehouse/`](warehouse/) | The synthetic ObsInsure dataset and its generator |
| [`artefacts/`](artefacts/) | The published figures (Euler diagram, framework-entry, call-chain) and their source |

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

[![The call chain of one agent tool call: OTel spans and OpenLineage events for a single tools/call, and the two upstream RFC asks this repository makes visible](artefacts/bearingnode-mcp-lineage-call-chain.png)][blog-technical]

The diagram above is the topology; this is the same call chain traced end to
end for one real `tools/call`, spans and lineage events both shown, with the
two bespoke asks — the `_meta` caller-identity key and the trace-context
facet — marked at the point in the chain each one is made.

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
      │                    _meta carries caller identity  ← our MCP ask
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
`analyze_db_health` and `get_top_queries` build and execute SQL internally, and
the protocol never sees it.

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

**Carrying caller identity costs servers nothing.** The MCP specification
declares `_meta` `extra: allow`, so a bespoke key travels today against an
unmodified SDK. A server that has never heard of the key ignores it. The gap is
agreement on the key name and payload shape, a convention rather than a protocol
change. That is the whole of our MCP ask, and its size is the point: the
protocol can carry identity forward, and here it can do nothing else.

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
  without anyone inventing a correlation. We expect the caller identity that
  arrives in `_meta` to originate from that already-instrumented runtime.

  *If the assumption fails for a given estate*, the gap this workstream
  describes does not change, but the caller half of the demonstration has
  nothing on the other end of the link. See A09 for the stability caveat: those
  conventions carry `development` stability, so names will move.
- Production concerns: auth, multi-tenancy, retention, scale.

**Why the boundary sits here:** the simplest possible interaction shows the
whole gap. One agent, one tool call, one table. Anything that enlarges the
topology enlarges the *demonstration* without strengthening the *argument*, and
invites the reply that the architecture caused the problem rather than the
protocol.

<!-- The two posts this workstream cites — the leadership pre-read and the
     technical deep dive behind these figures. Interactive figures are
     published on the blog, deliberately not on GitHub: see artefacts/README.md
     § "Why the interactive figures aren't embedded on GitHub". -->
[blog-leadership]: https://www.bearingnode.com/post/agentic-lineage-mcp-dio11y
[blog-technical]: https://www.bearingnode.com/post/mcp-agent-data-dio11y

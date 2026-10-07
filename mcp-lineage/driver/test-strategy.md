# `driver/` — scenario specification and test strategy

## TL;DR

**Two scenarios.** **Scenario 2** (flat mode: N deterministic `execute_sql`
calls) has no automated test — only a manual walkthrough in `README.md` §
*Run it*. **Scenario 2b** (`--mixed` mode) mixes non-governed spans into a
trace alongside a governed one, to show the collector's
`always-keep-data-access` policy retains the *whole trace*, not just the
governed span.

**The rule that matters most:** Scenario 2b's non-governed spans describe an
**operation**, never imply an **actor**. Naming them after a "chat" or any
other persona would imply a speaker, which is REQ3's unresolved authority
model (human / on-behalf-of / autonomous — `evidence-matrix.md`'s largest
unmet requirement) and out of scope for what this scenario tests. See §
*Scenario 2b: explicit scope boundary*.

**Status.** Scenario 2 is built; Scenario 2b is not. See RAID I34 for the
build decision and estimate.

---

## What this component is, and is not

`driver/` is the **test client**. It fires MCP tool calls at the instrumented
`postgres-mcp` server (`mcp_server_ol/`) so a human can watch what lands in
Jaeger and Marquez. It is a load generator, not part of the instrumentation
under test, and has no lineage logic of its own — see `README.md` §
*"Where the instrumentation sits, and what that implies"* for why the two
components sharing the word "driver" is confusing and deliberate scope, not
an accident.

## Scenarios this driver drives

This workstream names three scenarios; this driver covers one and gains a
variant of it:

- **Scenario 1 — correlation** (pivot Marquez to Jaeger on `trace_id`). Not
  built by this driver. Covered instead by `mcp_server_ol`'s own integration
  suite (`test_end_to_end.py::test_the_trace_reference_survives_marquez_ingestion`).
- **Scenario 2 — completeness** (sampling versus no-sampling), **built**.
  N deterministic `execute_sql` calls, no LLM in the loop, reproducible and
  screenshotable: 1 `CREATE TABLE IF NOT EXISTS` + 100 `SELECT` + 10 `INSERT`
  = 111 statements at `N=100`, all `execute_sql`.
- **Scenario 2b — trace composition.** Every call Scenario 2 fires is a
  governed `execute_sql` call, so every span it produces already carries
  `lineage.run_id`, and the collector's `always-keep-data-access` policy
  (RAID R09) retains all of them. That is not a defect in the policy; it is
  a property of Scenario 2's traffic being 100% governed. What Scenario 2
  cannot show is what happens to a trace that **mixes** governed and
  non-governed spans — whether the policy's per-trace (not per-span)
  decision actually pulls an entire mixed trace through when only one span
  inside it is governed. Scenario 2b adds a `--mixed` mode to answer that,
  without replacing Scenario 2's existing flat mode.
- **Scenario 3 — identity degeneration.** Not built by this driver; out of
  scope here.

## Scenario 2b: explicit scope boundary — read this before writing any code

**The non-governed spans this driver adds under `--mixed` make no claim
about what generated them — human, an agent acting on behalf of a human, or
an autonomous agent.** That three-way distinction is `REQUIREMENTS.md` § 7's
**REQ3 — Actor identity and authority**, and `evidence-matrix.md` records it
in terms that must not be contradicted by anything this driver does:

> **Authority model: not built.** ... Nothing in the emitted record carries
> that distinction. OpenLineage's ownership URN vocabulary has no agent type
> and no authority model (RAID A03, D05, D28). **This is the single
> largest unmet part of the implementation.**

**Span names in this mode must describe an operation, not imply an actor**:
`ordinary_span`, `session_step`, `context_read` — no `chat`, `note`,
`review`, or anything else that reads as a persona acting.

The property under test is purely mechanical: **does the collector retain an
entire trace when exactly one span inside it carries `lineage.run_id`,
regardless of what the other spans in that trace are.** Nothing about origin,
authority, or intent is exercised, asserted, or implied. If this scenario is
later extended to say something about REQ3, that is new, separately-scoped
work — most likely upstream RFC-shaped, since the authority-model gap this
would need to fill does not currently exist in OpenLineage's vocabulary
(RAID A03/D05, D28) — not a driver flag.

## Design (Scenario 2b)

- **One driver, a mode switch** — `driver.py` gains `--mixed`, not a second
  script. Same client, same server, same collector config; only the traffic
  shape changes, keeping the two scenarios from drifting apart the way a
  parallel script would risk.
- **Client-side tracer**, new — `driver.py` has zero span/trace code today.
  Mirrors the ~30-line `TracerProvider` + `BatchSpanProcessor` +
  `OTLPSpanExporter` pattern already in `mcp_server_ol/telemetry.py`. New
  dependencies in `requirements.txt`: `opentelemetry-sdk` and an OTLP
  exporter package, pinned to match `mcp_server_ol/pyproject.toml`.
- **A weighted task list** of non-governed operations (see naming rule
  above), each opening and closing a plain child span with a few attributes
  and no MCP call involved. Shape borrowed as an *idea only* from
  OpenTelemetry's own demo load generator's weighted dispatcher
  (`opentelemetry-demo/src/load-generator/script.js:236-253`) —
  not copied; that demo has no MCP-relevant code to lift, and no manual
  `traceparent` extraction exists anywhere in that repository either, which
  is the one piece we still have to write ourselves.
- **One parent "session" span** wrapping several ordinary child spans plus
  one child span that wraps a real governed `execute_sql` call — the
  "one parent, several downstream calls" shape, same source, `script.js:165-182`.
- **`traceparent` injection into `_meta`** immediately before the governed
  call: `TraceContextTextMapPropagator().inject(carrier)`, then
  `carrier["traceparent"]` placed in that call's `_meta`. Standard SDK
  pattern, independent of transport.
- **Server-side extraction** — the half of this that touches the actual
  instrumented server, not just the demo client. `mcp_server_ol/meta.py`
  needs a `traceparent` reader; `mcp_server_ol/driver.py`'s
  `start_as_current_span` call (always roots a fresh span today — no
  inbound context is ever read) needs to use the extracted context as
  parent. Two build options — see RAID I34 for the sizing:
  - **Option A — test scaffolding only**: accept `traceparent` if present,
    no malformed-input handling, no dedicated test, undocumented as a
    feature.
  - **Option B — real capability**: `TraceparentStatus`/`TraceparentLookup`
    mirroring the existing `ParentStatus`/`ParentLookup` pattern already in
    `meta.py:46-73`, a unit test cloning `test_meta.py:58-104`'s
    absent/malformed table shape, and documentation framing it as the first
    working implementation of the "settled convention" RAID I05/D10
    currently only cite as researched but unimplemented. **Both options
    edit the same two production files** (`meta.py`, `mcp_server_ol/driver.py`);
    A does not avoid that edit, it ships it untested.

## Test strategy

`driver/` has no test infrastructure today — no `driver/tests/`, no pytest
wiring — for either scenario below.

### Scenario 2 (existing, flat mode) — currently unautomated

Verification today is manual: run `driver.py N`, look at Jaeger and Marquez
by eye, record the observed counts as prose in `README.md` § *Run it*.
Closing this needs:

- An integration test that runs the flat driver, then asserts against
  Marquez that all N-plus-setup statements landed and `COMPLETED`.
- An integration test that asserts the Jaeger-side retention sits inside a
  statistically sound band rather than eyeballing a couple of runs. Since
  Scenario 2's own traffic is 100% governed, the correct assertion for
  Scenario 2 alone is **100% retained** (RAID R09) — a ~10% sampled-away
  band is only a meaningful assertion once Scenario 2b's non-governed
  traffic exists to sample.

### Scenario 2b (new)

- **Unit-level** (wherever Option B's server-side extraction lands): clone
  the absent/malformed table shape from
  `mcp_server_ol/tests/unit/test_meta.py:58-104`, asserting
  `TraceparentStatus` distinguishes absent from malformed the same way
  `ParentStatus` already does.
- **Integration-level**: a live check against the Jaeger HTTP API, same
  pattern as `mcp_server_ol/tests/integration/test_demonstrable_operation.py`'s
  `_spans()`/`_tags()` helpers — but those are service+operation scoped, so
  a fetch-by-`trace_id` helper is new, not reused. Assert: one `trace_id`
  contains N ordinary spans + 1 governed span, all retained together, none
  of the ordinary siblings individually carrying `lineage.run_id`.
- **Manual/visual**: a Jaeger screenshot showing the mixed trace, for
  `README.md` and/or the blog draft, the same evidentiary role the existing
  Scenario 2 walkthrough plays in `README.md` § *Run it*.

## Links back to `evidence-matrix.md` and `REQUIREMENTS.md`

- **REQ3 — Actor identity and authority**: explicitly **not** touched by
  Scenario 2b. Verdict stays 🟡 Partially met, unchanged. See the scope
  boundary above — this is the row most at risk of accidental overreach and
  needs re-checking against whatever ships, not just against this spec.
- **REQ10 — Reconstructable context**: strengthened. Currently evidenced by
  a single-call trace (`test_end_to_end.py`). Scenario 2b adds a second,
  more realistic data point for the "survival" half of this row — a trace
  that looks like a real mixed session, not a single isolated call — without
  changing the verdict language, which already correctly states retention
  parity (store-vs-backend, not sampling) is separately unimplemented.
- **REQ8 — Demonstrable operation**: not expected to change. REQ8 is about
  detecting *absence* (a call that never reached the database at all); it
  does not turn on trace composition. Re-check this expectation once
  Scenario 2b actually exists, rather than assuming it holds.
- **RAID cross-references**: R13, I34.

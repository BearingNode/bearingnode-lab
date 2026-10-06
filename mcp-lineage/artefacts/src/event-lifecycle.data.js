/**
 * Content for the event-lifecycle figure: a bow tie. The left side is event
 * capture, what is captured as the producer's call goes out. The middle is
 * where it lands. The right side mirrors the left: what an auditor, SRE or
 * governance analyst does to recreate the event from what was captured.
 *
 * It shows the intended design, so each item that is not built today carries a
 * `tag`: "ask" (proposed, not yet standard), "assumed" (relied on, not shown by
 * this implementation) or "outside" (a separate system, out of scope).
 *
 * `pair` links a captured fact on the left to the step that recreates it on the
 * right: 1 the parent run id, 2 the trace and span ids, 3 the pseudonym.
 * Stage numbers match the call-chain figure. A string wrapped in backticks
 * renders as monospace. The template builds the DOM with textContent, so
 * nothing here is parsed as HTML.
 */
export const TAGS = {
    ask:     "Ask",
    assumed: "Assumed",
    outside: "Outside this implementation"
  };

export const CAPTURE = [
    { kind: "node", num: "2", h: "MCP `tools/call` + `_meta`",
      body: "The caller's request crosses into MCP." },
    { kind: "data", label: "edge 2 → 6: captured at the seam",
      lines: [
        { pair: "1", text: "from `_meta`: `parentRunId`, `jobNamespace`, `jobName`",
          note: "The parent run id. It names the caller's run, not a person.", tag: "ask" },
        { pair: "2", text: "from `_meta`: `traceparent`",
          note: "The caller's trace context, so the server's span joins the caller's trace.", tag: "assumed" }
      ],
      foot: "The `_meta` key does not carry identity. It carries the parent run id and the trace link, and the run and its reasoning trace are rebuilt from them. Who acted needs the actor reference, an ask not yet emitted." },
    { kind: "node", num: "6", h: "The event is built",
      body: "The server assembles the `RunEvent` from everything captured so far." },
    { kind: "data", label: "edge 6 → 7: assembled into `RunEvent.facets`",
      lines: [
        { pair: "1", text: "`parent: {runId, namespace, name}`", note: "from `_meta`, the edge above", tag: "ask" },
        { pair: "2", text: "`traceContext: {traceId, spanId}`", note: "the server span's own ids, not MCP's", tag: "ask" },
        { text: "`tags: {derivation, completeness, actor}`", note: "the producer's own vocabulary, not the caller's" },
        { pair: "3", text: "`actor`: a pseudonymous reference", note: "issued by the resolution service", tag: "ask" }
      ],
      foot: "This is the object now, not a description of one." },
    { kind: "node", num: "7", h: "Two write paths",
      body: "The complete object. The fan-out point." },
    { kind: "data", label: "edge 7 → stores: the split",
      lines: [
        { text: "The span's own attributes (`mcp.*`, `gen_ai.*`, duration) stay on the span.",
          note: "They come from the caller's and MCP's own instrumentation.", tag: "assumed" },
        { text: "The whole assembled `RunEvent` goes to Marquez." }
      ],
      foot: "Same interaction, two different slices of it." }
  ];

export const STORES = [
    { id: "marquez", h: "Marquez: OpenLineage store",
      nodes: [ { h: "`RunEvent`", body: "stored as received" },
               { h: "`Dataset`", body: "`namespace`, `name`" } ] },
    { id: "jaeger", h: "Jaeger: OTel trace store",
      nodes: [ { h: "`Span / Trace`", body: "`traceId`, `spanId`, `mcp.*`, `gen_ai.*`, duration" } ] },
    { id: "identity", h: "Identity resolution", tag: "outside", gated: true,
      nodes: [ { h: "pseudonym to real identity", body: "its own retention and access control (REQ4)" } ] }
  ];

export const PERSONA = { label: "Persona", h: "Auditor, SRE or governance analyst", body: "The question: who acted here, and why?" };

export const RECREATE = [
    { pair: "1", label: "query", h: "Query Marquez, by dataset and time",
      body: "Returns the run: its parent run id and job, its tags and the trace reference. The actor facet adds a pseudonym once it exists.",
      tag: "ask" },
    { pair: "2", label: "follow", h: "Follow the trace in Jaeger, by `traceContext`",
      body: "The reasoning trace: what was asked, what the agent decided. It resolves only if the client injected `traceparent` and the trace is still held.",
      tag: "assumed" },
    { pair: "3", label: "authorised only", h: "Resolve the pseudonym", gated: true,
      body: "A separate query, a separate system, separate access control. A deliberate second step." }
  ];

export const CLOSING = "**Recreated on read.** The parent run id and the trace link are captured at write time. They let the analyst rebuild the run and bind the event to its reasoning trace. Who acted needs the actor reference, an ask not yet emitted, and a resolution system outside this implementation. Whether the call was delegated or autonomous cannot be recovered from the event (REQ3). Each step is a separate query by explicit identifier. Nothing is inferred, and nothing in the event carries identity itself.";

/**
 * Content for the event-lifecycle figure: a bow tie. The left side is event
 * capture, what is captured as the producer's call goes out. The middle is
 * where it lands. The right side mirrors the left: what an auditor, SRE or
 * governance analyst does to recreate the event from what was captured.
 *
 * It shows the intended design, so each item that is not built today carries a
 * `tag`: "ask" (proposed, not yet standard), "assumed" (relied on, not shown by
 * this implementation on the SDK 1.x it runs on), "probed" (measured once against
 * SDK 2.x by a probe outside the gates) or "outside" (a separate system, out of
 * scope). A `tag` may be an array when an item differs by SDK version.
 *
 * `pair` links a captured fact on the left to the step that recreates it on the
 * right: 1 the parent run id, 2 the trace and span ids, 3 the pseudonym.
 * Stage numbers match the call-chain figure. A string wrapped in backticks
 * renders as monospace. The template builds the DOM with textContent, so
 * nothing here is parsed as HTML.
 */
export const TAGS = {
    ask:     "Ask",
    assumed: "Assumed · SDK 1.x",
    probed:  "Probed · SDK 2.x",
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
          note: "The caller's trace context, so the server's span joins the caller's trace. On SDK 1.x the caller must inject it: the lab's driver does so by hand on one call, and a real client is assumed to. On SDK 2.x the client SDK injects it when the caller has OpenTelemetry configured.", tag: ["assumed", "probed"] }
      ],
      foot: "The `_meta` key does not carry identity. It carries the parent run id and the trace link, and the run and its reasoning trace are rebuilt from them. Who acted needs the actor reference, an ask not yet emitted." },
    { kind: "node", num: "6", h: "The event is built",
      body: "The server assembles the `RunEvent` from everything captured so far." },
    { kind: "data", label: "edge 6 → 7: assembled into `RunEvent.facets`",
      lines: [
        { pair: "1", text: "`parent: {runId, namespace, name}`", note: "the standard `ParentRunFacet`, filled from `_meta`, the edge above" },
        { pair: "2", text: "`traceContext: {traceId, spanId}`", note: "the server span's own ids, not MCP's", tag: "ask" },
        { text: "`tags: {derivation, completeness, actor}`", note: "the producer's own vocabulary, not the caller's" },
        { pair: "3", text: "`actor`: a pseudonymous reference", note: "issued by the resolution service", tag: "ask" }
      ],
      foot: "This is the object now, not a description of one." },
    { kind: "node", num: "7", h: "Two write paths",
      body: "The complete object. The fan-out point." },
    { kind: "data", label: "edge 7 → stores: the split",
      lines: [
        { pair: "2", text: "On the span: `lineage.run_id` and `lineage.actor_status`",
          note: "Our own attribute names, set by this server's span. They point from the span back to its run. `lineage.dropped` is added when the event is lost.", },
        { text: "`mcp.*` and `gen_ai.*` are not set by this server's own span.",
          note: "On SDK 1.x nothing sets them, so the caller's or MCP's instrumentation is assumed to. On SDK 2.x the SDK's server span sets `mcp.method.name`, `mcp.protocol.version`, `gen_ai.operation.name` and `gen_ai.tool.name`.", tag: ["assumed", "probed"] },
        { text: "The whole assembled `RunEvent` goes to Marquez." }
      ],
      foot: "Same interaction, two different slices of it." }
  ];

export const STORES = [
    { id: "marquez", h: "Marquez: OpenLineage store",
      nodes: [ { h: "`RunEvent`", body: "stored as received" },
               { h: "`Dataset`", body: "`namespace`, `name`" } ] },
    { id: "jaeger", h: "Jaeger: OTel trace store",
      nodes: [ { h: "`Span / Trace`", body: "One span per SQL statement. `traceId`, `spanId`, `lineage.run_id`, `lineage.actor_status`, duration, and `lineage.dropped` when an event is lost" } ] },
    { id: "identity", h: "Identity resolution", tag: "outside", gated: true,
      nodes: [ { h: "pseudonym to real identity", body: "its own retention and access control (REQ4)" } ] }
  ];

export const PERSONA = { label: "Persona", h: "Auditor, SRE or governance analyst", body: "The question: who acted here, and why?" };

export const RECREATE = [
    { pair: "1", label: "query", h: "Query Marquez, by dataset and time",
      body: "Returns the run: its parent run id and job, its tags and the trace reference. The actor facet adds a pseudonym once it exists.",
      tag: "ask" },
    { pair: "2", label: "cross", h: "Cross between the run and its trace in Jaeger",
      body: "From the run, `traceContext` names the trace and span. From a span, `lineage.run_id` names the run, so a run id with no run in Marquez is an event that should exist and does not. A span marked `lineage.dropped` lost its event. The reasoning trace, what was asked and what the agent decided, resolves only if `traceparent` reached the server and the trace is still held. On SDK 1.x the client has to inject it. On SDK 2.x the SDK does, when the caller has OpenTelemetry configured. That the trace is still held is assumed on both.",
      tag: ["assumed", "probed"] },
    { pair: "3", label: "authorised only", h: "Resolve the pseudonym", gated: true,
      body: "A separate query, a separate system, separate access control. A deliberate second step." }
  ];

export const CLOSING = "**Recreated on read.** The parent run id and the trace link are captured at write time. They let the analyst rebuild the run and bind the event to its reasoning trace. Who acted needs the actor reference, an ask not yet emitted, and a resolution system outside this implementation. Whether the call was delegated or autonomous cannot be recovered from the event (REQ3). Each step is a separate query by explicit identifier. Nothing is inferred, and nothing in the event carries identity itself.";

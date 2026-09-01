/**
 * Content for the signal-scope figure, extracted verbatim from the 2026-07-27
 * build. Every entry's meta is transcribed from the source file named in `src`,
 * and was verified against those files on that date — so this data is edited
 * only against primary sources, never from memory.
 *
 * `col` places an item in one of the four regions: otel | both | ol | gap.
 * The desktop Euler geometry and the stacked mobile view are both rendered from
 * this one array, so they cannot diverge.
 */
export const ITEMS = [
    { id: "method",   col: "otel", mono: true,  label: "mcp.method.name",
      set: "OpenTelemetry span · MCP convention", req: "Required", stability: "development",
      src: "model/mcp/registry.yaml",
      body: "The name of the request or notification method. An enum — members include tools/call, resources/read, tools/list, prompts/get, sampling/createMessage." },
    { id: "session",  col: "otel", mono: true,  label: "mcp.session.id",
      set: "OpenTelemetry span · MCP convention", req: "Recommended", stability: "development",
      src: "model/mcp/registry.yaml",
      body: "Identifies the MCP session. The closest thing MCP has to a durable, job-shaped anchor — worth considering as the OpenLineage run or parent-run anchor, since it is already emitted." },
    { id: "protocol", col: "otel", mono: true,  label: "mcp.protocol.version",
      set: "OpenTelemetry span · MCP convention", req: "Recommended", stability: "development",
      src: "model/mcp/registry.yaml",
      body: "The version of the Model Context Protocol in use, e.g. 2025-06-18. Matters here because pre- and post-stateless-rewrite deployments propagate identity differently." },
    { id: "rpc",      col: "otel", mono: true,  label: "rpc.response.status_code",
      set: "OpenTelemetry span · MCP convention", req: "Conditionally required", stability: "development",
      src: "model/mcp/common.yaml",
      body: "Set if the response carries an error code. Alongside error.type, which should be the string representation of the JSON-RPC error code." },
    { id: "args",     col: "otel", mono: true,  label: "gen_ai.tool.call.arguments",
      set: "OpenTelemetry span · GenAI convention", req: "Opt-in", stability: "development",
      src: "model/gen-ai/registry.yaml",
      body: "Parameters passed to the tool call. Opt-in because it is a payload — in this scenario it is where limit: 5000 appears, which is the only trace of the read being truncated." },
    { id: "duration", col: "otel", mono: false, label: "duration + causal span tree",
      set: "OpenTelemetry span · intrinsic", req: "Intrinsic to the span model", stability: "stable",
      src: "OTel trace data model",
      body: "How long it took and what called what. This is what tracing is for, and OpenLineage has no equivalent — nor should it." },

    { id: "join",     col: "both", mono: false, label: "trace_id + span_id — the join key",
      set: "Carried by both", req: "The correlation, not a derivation", stability: "—",
      src: "W3C Trace Context · custom OL run facet",
      body: "MCP conventions say instrumentations SHOULD inject the configured propagators — traceparent, tracestate, baggage — into the request params._meta bag. A lineage event may carry those IDs so a reader can pivot between the two stores. It is a link. No OpenLineage event in this design is ever generated from a span." },
    { id: "resource", col: "both", mono: false, label: "the data resource touched *",
      set: "Carried by both — but not the same identifier", req: "Conditionally required (OTel)", stability: "development",
      src: "model/mcp/registry.yaml",
      body: "OTel's mcp.resource.uri is a transport pointer — it need only be meaningful to the server about to dereference it. Its own example is postgres://database/customers/schema. OpenLineage's namespace + name is a catalog identity that must be canonical to join a graph. Neither derives from the other without a naming authority — which is the real reason lineage cannot be reconstructed from spans." },
    { id: "rw",       col: "both", mono: false, label: "read / write intent",
      set: "Carried by both", req: "—", stability: "—",
      src: "—",
      body: "OTel infers it from the method and the DB span; OpenLineage states it structurally, as inputs versus outputs." },
    { id: "fail",     col: "both", mono: false, label: "success or failure",
      set: "Carried by both", req: "Conditionally required (OTel)", stability: "development",
      src: "model/mcp/common.yaml · ErrorMessageRunFacet",
      body: "error.type on the span; RunState.FAIL plus an errorMessage run facet on the lineage side. A run that starts and never terminates is indistinguishable from a dropped event — which is precisely the confusion this figure exists to prevent." },
    { id: "time",     col: "both", mono: false, label: "when, and how long",
      set: "Carried by both", req: "—", stability: "—",
      src: "—",
      body: "Both timestamp the interaction. Only the span meaningfully measures it." },
    { id: "who",      col: "both", mono: false, label: "caller pseudo-id — app convention",
      set: "Possible on both — required by neither", req: "Not in the MCP attribute set", stability: "development",
      src: "model/enduser/registry.yaml",
      body: "enduser.pseudo.id exists in core OTel: a pseudonymous identifier not directly linked to the end user's actual identity. It can reach the server through baggage in params._meta. But it is absent from mcp.common.attributes, so a fully conformant MCP instrumentation carries no caller identity at all — any that is present is an application convention a lineage consumer cannot rely on. On the OpenLineage side, TagsRunFacet could carry the same pseudonymous reference today, using an existing facet rather than a new one." },

    { id: "dsid",     col: "ol", mono: false, label: "dataset: namespace + name",
      set: "OpenLineage event", req: "Core to the event", stability: "stable",
      src: "openlineage/client/generated/base.py",
      body: "Canonical dataset identity. OpenLineage has a dataset naming specification precisely because these identifiers must be comparable across producers and across time to form a graph." },
    { id: "schema",   col: "ol", mono: true,  label: "SchemaDatasetFacet",
      set: "OpenLineage event · dataset facet", req: "Optional facet", stability: "stable",
      src: "openlineage/client/generated/schema_dataset.py",
      body: "The fields of the dataset. No OTel span carries the shape of what was read." },
    { id: "collin",   col: "ol", mono: true,  label: "ColumnLineageDatasetFacet",
      sub: "↳ Transformation · DIRECT / INDIRECT",
      set: "OpenLineage event · dataset facet", req: "Optional facet", stability: "stable (1-2-0)",
      src: "openlineage/client/generated/column_lineage_dataset.py",
      body: "Maps each output field to the input fields used to evaluate it. Each InputField carries Transformation entries: type DIRECT or INDIRECT, a subtype, a description, and a masking flag. The facet's dataset property is documented for lineage affecting the whole dataset — filtering, sorting, grouping (aggregates), joining, window functions. That is a purpose-built slot for exactly the join-and-group-by in this scenario. OpenLineage can express the transform perfectly. Nothing in this architecture can observe it." },
    { id: "owner",    col: "ol", mono: true,  label: "OwnershipJobFacet",
      set: "OpenLineage event · job facet", req: "Optional facet", stability: "stable",
      src: "openlineage/client/generated/ownership_job.py",
      body: "Job-level ownership, in OpenLineage since 2022 and populated from Airflow's owner field. It attaches to a job — which is why it does not solve the ad hoc case: there is no durable job to attach it to." },
    { id: "tags",     col: "ol", mono: true,  label: "TagsRunFacet",
      set: "OpenLineage event · run facet", req: "Optional facet", stability: "development",
      src: "openlineage/client/generated/tags_run.py",
      body: "Run-level tags, with active work syncing tag and ownership config across the Python and Java clients. The most conservative candidate carrier for a pseudonymous actor reference: an existing facet, no new spec surface, and pseudonymous by construction." },
    { id: "graph",    col: "ol", mono: false, label: "the graph, across time",
      set: "OpenLineage event · emergent", req: "—", stability: "—",
      src: "—",
      body: "The accumulated result. Worthless if incomplete: dropping 90% of spans costs you resolution, dropping 90% of lineage events costs you correctness. That asymmetry of consequence is why one signal may be sampled and the other may not." },

    { id: "g-transform", col: "gap", mono: false,
      label: "The transform the agent performed after the rows left the server — AVG over the returned rows. No span. No facet. No observer.",
      set: "Neither", req: "No mechanism exists", stability: "—", src: "—",
      body: "The MCP server has ground truth for the reads — it ran the SELECTs — and no idea the agent then averaged anything. The caller knows it computed an average but cannot assert dataset identity. The transform falls in the hole between them: outside both parties' ground truth, not missing through a defect. This lands on the RFC's first assumption — lineage must be declared by the entity enacting it. Only the agent can declare this one." },
    { id: "g-dataset", col: "gap", mono: false,
      label: "Which dataset a tools/call touched — mcp.resource.uri is scoped to resources/read, which takes a URI parameter. A tool call does not.",
      set: "Neither", req: "No mechanism exists", stability: "—", src: "model/mcp/registry.yaml",
      body: "mcp.resource.uri is conditionally required only when the client executes a request type that includes a resource URI parameter — documented as resources/read, resources/subscribe, resources/unsubscribe and notifications/resources/updated. A tools/call has no such parameter. This is the narrow, closeable gap: a concrete proposal to open-telemetry/semantic-conventions-genai. Claiming OTel cannot identify an MCP data resource at all would be wrong, and would be corrected in review." },
    { id: "g-authority", col: "gap", mono: false,
      label: "The authority the agent acted under — autonomously, or on behalf of a named user.",
      set: "Neither", req: "No mechanism exists", stability: "—", src: "model/gen-ai/registry.yaml",
      body: "gen_ai.agent.id, .name, .description and .version all exist — the identity primitive is there. Nothing anywhere expresses the authority model: whether the agent holds its own standing identity or acts under a user's delegated permissions. This one stays deliberately open in the RFC: it is a question posed to both communities, not a demand." }
  ];

export const NARRATION = {
    0: "",
    1: "tools/call query_dataset(table=private_party). The server span records the method, the tool, the session and the duration. The lineage event records the dataset by its canonical name. Both are emitted; both are complete.",
    2: "tools/call query_dataset(table=premium, limit=5000). Same again — but note the limit only appears inside gen_ai.tool.call.arguments, which is opt-in. If it is off, nothing records that the read was truncated.",
    3: "The agent joins the two result sets and computes AVG(premium.amount) GROUP BY segment. Both circles go quiet: there is no span for this and no facet observing it. A decision will be taken on that average — computed over a truncated read — and nothing anywhere records how it was derived."
  };

export const STEP_ITEMS = {
    1: ["method", "session", "protocol", "duration", "join", "resource", "rw", "time", "dsid", "schema", "graph"],
    2: ["method", "session", "protocol", "rpc", "args", "duration", "join", "resource", "rw", "time", "dsid", "schema", "graph"],
    3: []
  };

/** Items a 10% tail sampler discards. The OpenLineage side has no equivalent knob. */
export const SAMPLED_AWAY = ["method", "session", "protocol", "rpc", "args", "duration", "join", "time", "who"];

"""
FROZEN EXHIBIT — not run, not tested, not repaired. See ./README.md
(RAID D09/I13, mcp-lineage register) before reading further. Replaced by
../mcp_server_ol/, which docker-compose.yml actually runs.

Instrumented MCP server over the ObsInsure warehouse.

Every tool call that touches the warehouse emits TWO independent signals:

  1. An OTel span, sent to the collector (which tail-samples at 10% —
     see ../otel-collector-config.yaml). This is the "how did it perform"
     signal, and it is *designed* to be lossy.

  2. An OpenLineage RunEvent, sent directly to Marquez. This is the
     "what did it touch" signal, and nothing here drops it.

The span carries a candidate attribute pair identifying the data resource
touched (DATA_RESOURCE_NAMESPACE_ATTR / DATA_RESOURCE_NAME_ATTR). SUPERSEDED:
this was floated as the reference implementation of a semconv attribute for
the GenAI/MCP tool-call conventions, but `mcp-lineage` RAID A04 invalidated
that framing — `mcp.resource.uri` already exists for the adjacent
`resources/read`-family case. See RAID I09 and the SUPERSEDED comment at the
constants' definition below. Do not read this as a current proposal.

The OpenLineage event carries the span's trace_id/span_id as a custom run
facet, so a viewer can pivot from Marquez to Jaeger for any run that
happened to survive sampling — this is deliberately a correlation, not a
derivation: the OL event is never generated from the span.

Job identity is intentionally synthetic-per-invocation
(`agent-{query,write}-<8 hex>`), not a stable job name. This is the
"initiating entity is an agent, not a durable job" case the RFC describes.
Running the driver script many times is meant to make the Marquez job list
degenerate into noise — that degeneration is a finding, not a bug.
"""
import os
import uuid
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import psycopg2.sql
import requests
from mcp.server.fastmcp import FastMCP
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

MARQUEZ_URL = os.environ.get("MARQUEZ_URL", "http://localhost:5000")
OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
# KNOWN AND DELIBERATE — an in-source credential default, left in place on
# purpose. `05-repo-hygiene.md` makes credentials in source a non-negotiable, and
# this is a conscious, marked exception rather than an oversight:
#   1. There is no secret here. `postgres:postgres@localhost` is the well-known
#      default loopback DSN for a throwaway container. It grants nothing, to
#      nobody, anywhere but the machine running the demo.
#   2. Its presence is the point. A reader clones the repository, starts the
#      compose stack and the demo runs — no configuration step, nothing to
#      obtain, nothing to guess. Being able to *see and run* the thing is what
#      makes this an exhibit rather than an assertion.
#   3. It is overridable by `WAREHOUSE_DSN`, so no deployment is obliged to use
#      it, and nothing here reads a real credential from source.
# This file is a frozen exhibit (RAID D09) and obligation 4 of the frozen-exhibit
# exception forbids repairing it. Documented at `mcp_server/README.md`. Do not
# "fix" this by removing the default — that breaks the clone-and-run property
# without removing any exposure, because there is none.
WAREHOUSE_DSN = os.environ.get(
    "WAREHOUSE_DSN", "postgresql://postgres:postgres@localhost:5432/warehouse"
)
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

OL_NAMESPACE = "warehouse"
OL_JOB_NAMESPACE = "mcp-lineage-demo"
OL_PRODUCER = "https://github.com/BearingNode/DIO11y-lab/tree/main/mcp-lineage"

# SUPERSEDED — retired pre-A04 framing. Do not read the attribute names below
# as a current claim.
#
# This directory is a frozen exhibit (RAID D09, mcp-lineage/mcp_server/README.md).
# `data.resource.*` was this workstream's original candidate attribute pair.
# `mcp-lineage` RAID A04 invalidated the premise it was built on: OTel's
# GenAI/MCP semconv already defines `mcp.resource.uri` for this purpose
# (scoped to `resources/read`-family calls; `tools/call`, which is what this
# server uses, has no defined attribute at all — narrower than "nothing
# exists"). Tracked as `mcp-lineage` RAID I09. The current, non-superseded
# reference implementation is `../mcp_server_ol/`, which does not emit these
# attributes. Left in place, unfixed, because fixing it would falsify the
# as-is state this exhibit exists to show — see the folder README's
# "Not repaired" section.
DATA_RESOURCE_NAMESPACE_ATTR = "data.resource.namespace"
DATA_RESOURCE_NAME_ATTR = "data.resource.name"
DATA_RESOURCE_OPERATION_ATTR = "data.resource.operation"  # "read" | "write"

provider = TracerProvider(resource=Resource.create({"service.name": "mcp-lineage-server"}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("mcp-lineage.warehouse")

mcp = FastMCP("obsinsure-warehouse", host="0.0.0.0", port=MCP_PORT)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit_ol_event(event_type, job_name, run_id, inputs, outputs, trace_id, span_id):
    """POST a minimal OpenLineage RunEvent straight to Marquez. No batching,
    no sampling, no drop path — every call gets an event, on purpose."""
    event = {
        "eventType": event_type,
        "eventTime": _now(),
        "producer": OL_PRODUCER,
        "run": {
            "runId": run_id,
            "facets": {
                "bearingnode_traceContext": {
                    "_producer": OL_PRODUCER,
                    "_schemaURL": "https://bearingnode.com/schemas/traceContext.json",
                    "traceId": trace_id,
                    "spanId": span_id,
                }
            },
        },
        "job": {"namespace": OL_JOB_NAMESPACE, "name": job_name},
        "inputs": inputs,
        "outputs": outputs,
    }
    resp = requests.post(f"{MARQUEZ_URL}/api/v1/lineage", json=event, timeout=5)
    resp.raise_for_status()


def _dataset(table: str) -> dict:
    return {"namespace": OL_NAMESPACE, "name": f"obsinsure.{table}"}


@mcp.tool()
def query_dataset(table: str, limit: int = 10) -> list[dict]:
    """Read up to `limit` rows from an ObsInsure warehouse table
    (e.g. 'claim', 'contract', 'private_party', 'catalog', 'premium')."""
    run_id = str(uuid.uuid4())
    job_name = f"agent-query-{uuid.uuid4().hex[:8]}"

    with tracer.start_as_current_span("mcp.tool.query_dataset") as span:
        # SUPERSEDED emission — retired pre-A04 framing, see the constants'
        # definition above and mcp-lineage RAID I09. Not fixed (RAID D09
        # frozen-exhibit obligation 4).
        span.set_attribute(DATA_RESOURCE_NAMESPACE_ATTR, OL_NAMESPACE)
        span.set_attribute(DATA_RESOURCE_NAME_ATTR, f"obsinsure.{table}")
        span.set_attribute(DATA_RESOURCE_OPERATION_ATTR, "read")
        ctx = span.get_span_context()
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        _emit_ol_event("START", job_name, run_id, [_dataset(table)], [], trace_id, span_id)

        conn = psycopg2.connect(WAREHOUSE_DSN)
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    psycopg2.sql.SQL("SELECT * FROM obsinsure.{} LIMIT %s").format(
                        psycopg2.sql.Identifier(table)
                    ),
                    (limit,),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        _emit_ol_event("COMPLETE", job_name, run_id, [_dataset(table)], [], trace_id, span_id)
        return [dict(r) for r in rows]


@mcp.tool()
def write_dataset(table: str, rows: list[dict]) -> dict:
    """Write derived rows into an ObsInsure warehouse table, creating it if
    it doesn't already exist. `rows` is a list of flat dicts, all with the
    same keys."""
    if not rows:
        return {"written": 0}

    run_id = str(uuid.uuid4())
    job_name = f"agent-write-{uuid.uuid4().hex[:8]}"
    columns = list(rows[0].keys())

    with tracer.start_as_current_span("mcp.tool.write_dataset") as span:
        # SUPERSEDED emission — retired pre-A04 framing, see the constants'
        # definition above and mcp-lineage RAID I09. Not fixed (RAID D09
        # frozen-exhibit obligation 4).
        span.set_attribute(DATA_RESOURCE_NAMESPACE_ATTR, OL_NAMESPACE)
        span.set_attribute(DATA_RESOURCE_NAME_ATTR, f"obsinsure.{table}")
        span.set_attribute(DATA_RESOURCE_OPERATION_ATTR, "write")
        ctx = span.get_span_context()
        trace_id = format(ctx.trace_id, "032x")
        span_id = format(ctx.span_id, "016x")

        _emit_ol_event("START", job_name, run_id, [], [_dataset(table)], trace_id, span_id)

        conn = psycopg2.connect(WAREHOUSE_DSN)
        try:
            with conn.cursor() as cur:
                col_defs = psycopg2.sql.SQL(", ").join(
                    psycopg2.sql.SQL("{} text").format(psycopg2.sql.Identifier(c)) for c in columns
                )
                cur.execute(
                    psycopg2.sql.SQL("CREATE TABLE IF NOT EXISTS obsinsure.{} ({})").format(
                        psycopg2.sql.Identifier(table), col_defs
                    )
                )
                insert_cols = psycopg2.sql.SQL(", ").join(map(psycopg2.sql.Identifier, columns))
                placeholders = psycopg2.sql.SQL(", ").join(psycopg2.sql.Placeholder() * len(columns))
                insert_stmt = psycopg2.sql.SQL("INSERT INTO obsinsure.{} ({}) VALUES ({})").format(
                    psycopg2.sql.Identifier(table), insert_cols, placeholders
                )
                for row in rows:
                    cur.execute(insert_stmt, [str(row[c]) for c in columns])
            conn.commit()
        finally:
            conn.close()

        _emit_ol_event("COMPLETE", job_name, run_id, [], [_dataset(table)], trace_id, span_id)
        return {"written": len(rows)}


if __name__ == "__main__":
    mcp.run(transport="sse")

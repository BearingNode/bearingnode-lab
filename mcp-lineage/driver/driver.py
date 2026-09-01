"""
Deterministic driver — Scenario 2 (completeness) and Scenario 2b (composition).

Two modes, one client, one server, one collector config (test-strategy.md
§ "Design (Scenario 2b)" — a second script would let the two scenarios drift
apart):

- **Flat mode (default, Scenario 2).** Fires N `execute_sql` tool calls at
  the MCP server directly (no LLM in the loop, so this is reproducible and
  screenshotable). Every call is governed, so every span it produces already
  carries `lineage.run_id` and the collector's `always-keep-data-access`
  policy retains all of it (RAID R09). Each call produces one OTel span and
  one OpenLineage RunEvent pair (START/COMPLETE).

  After running, compare:
    - Jaeger  (http://localhost:16686) — expect roughly 10% of N traces.
      The collector tail-samples at 10%; the rest were dropped by design.
    - Marquez (http://localhost:3033)  — expect all N runs. Nothing here
      samples. This is the argument: same interactions, same collector,
      one trail intact, one full of holes.

- **`--mixed` mode (Scenario 2b, composition).** Flat mode alone can't show
  what the `always-keep-data-access` policy does to a trace that *isn't*
  100% governed, because it never produces one. `--mixed` fires N "sessions"
  instead of N bare calls: each session is one parent span wrapping a
  handful of ordinary, non-governed child spans (no MCP call, no lineage)
  plus one child span that wraps a real governed `execute_sql` call. The
  question this answers: does the collector retain the *whole* trace once
  one span inside it carries `lineage.run_id`, or only that one span? See
  test-strategy.md § "Scenario 2b: explicit scope boundary" for why the
  ordinary span names below describe operations, never actors — this mode
  makes no claim about who or what generated the traffic (REQ3 stays out of
  scope here).

  This mode is the one part of the two that emits its own OTel spans
  client-side (flat mode has none — every span today comes from the
  server). It talks to the collector's OTLP endpoint directly, mirroring
  `mcp_server_ol/telemetry.py`'s `configure_telemetry()` shape, scaled down
  to tracing only (no metrics pipeline needed here).

Usage:
    pip install -r requirements.txt
    python driver.py [N]           # flat mode (Scenario 2, unchanged)
    python driver.py [N] --mixed   # mixed mode (Scenario 2b)
"""
import asyncio
import random
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import (
    CallToolRequest,
    CallToolRequestParams,
    CallToolResult,
    ClientRequest,
    RequestParams,
)
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.propagate import inject
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

MCP_URL = "http://localhost:8000/mcp"
# The collector's OTLP gRPC receiver, published on the host per
# docker-compose.yml (`otel-collector` service, "4317:4317"). This driver
# runs on the host via `uv run`/`python`, not inside the compose network, so
# it targets `localhost`, unlike `mcp-server`'s in-cluster
# `http://otel-collector:4317`.
COLLECTOR_URL = "http://localhost:4317"
TRACER_SERVICE = "mcp-lineage-driver"

TABLES = ["claim", "contract", "private_party", "catalog", "premium"]

# Weighted, non-governed, operation-shaped spans for `--mixed` mode's
# ordinary traffic. Deliberately no persona in any of these names — see the
# module docstring and test-strategy.md's scope boundary. Idea only (a
# weighted list, one picked per step) borrowed from OpenTelemetry's own demo
# load generator's dispatcher shape (RAID A14); nothing here is copied from
# it, and no traceparent-injection precedent exists there either.
ORDINARY_OPERATIONS = [
    ("ordinary_span", 3),
    ("session_step", 3),
    ("context_read", 2),
    ("cache_lookup", 2),
]
ORDINARY_SPANS_PER_SESSION = 3

# Fixed seed so `--mixed` picks the same sequence of ordinary operations on
# every run — deterministic and screenshotable, same requirement flat mode
# already meets by having no randomness at all.
MIXED_SEED = 2026


def configure_tracing() -> trace.Tracer:
    """Client-side tracer for `--mixed` mode, mirroring `configure_telemetry()`.

    Scoped down from the server's version (`mcp_server_ol/telemetry.py`):
    tracing only, no metrics pipeline, no no-op fallback for a missing
    endpoint — `--mixed` exists specifically to produce a trace the
    collector acts on, so a reachable collector is a precondition of the
    mode, not an optional extra. Flat mode never calls this, so its
    behavior is untouched whether or not a collector is even running.
    """
    resource = Resource.create({SERVICE_NAME: TRACER_SERVICE})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=COLLECTOR_URL, insecure=True)))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(TRACER_SERVICE)


async def call(session: ClientSession, sql: str, *, meta: dict[str, str] | None = None) -> None:
    """Call the real `execute_sql` tool and raise loudly on failure.

    `query_dataset`/`write_dataset` never existed on the instrumented
    `postgres-mcp` server — they were the old, superseded scaffold's tool
    names (RAID D03). The MCP client SDK does not raise on `isError`, so a
    call to a nonexistent tool looked identical to success here for months;
    this driver was silently hitting "Unknown tool" the whole time.

    `meta`, when given, becomes the request's flat `_meta` — see
    `governed_call()` below for the one case that uses it (`traceparent`
    propagation).

    Built with `send_request` directly rather than `ClientSession.call_tool`
    because this repo pins `mcp==1.9.0` (unchanged since the workstream's
    first commit), whose `call_tool` predates the `meta=` convenience kwarg
    added in later SDK releases — `CallToolRequestParams` has always carried
    `_meta` (`RequestParams.Meta`, `extra="allow"`), so the underlying
    protocol support was never missing, only the shortcut. `meta=None`
    produces `_meta=None`, identical to today's flat-mode calls, which never
    pass it.
    """
    request_meta = RequestParams.Meta(**meta) if meta else None
    result = await session.send_request(
        ClientRequest(
            CallToolRequest(
                method="tools/call",
                params=CallToolRequestParams(name="execute_sql", arguments={"sql": sql}, _meta=request_meta),
            )
        ),
        CallToolResult,
    )
    if result.isError:
        text = "; ".join(getattr(c, "text", str(c)) for c in result.content)
        raise RuntimeError(f"execute_sql failed: {text}")


def ordinary_operation(tracer: trace.Tracer, name: str, index: int) -> None:
    """One plain child span: no MCP call, no lineage, nothing governed.

    Exists purely to give a `--mixed` trace non-governed siblings for the
    governed span to be retained alongside. Attributes describe the
    operation's position in the session, not who performed it.
    """
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("operation.index", index)
        span.set_attribute("lineage.governed", False)


async def governed_call(tracer: trace.Tracer, session: ClientSession, sql: str) -> None:
    """The one governed span in a mixed session — wraps a real `execute_sql` call.

    The wire contract: inject the current span's W3C trace context into a
    carrier via `opentelemetry.propagate.inject(carrier)`, which populates
    `carrier["traceparent"]`, then attach that as a *flat* `_meta` key —
    `{"traceparent": "..."}`, not nested under any namespace. This is
    deliberately not the same `_meta` key `mcp_server_ol/meta.py` already
    uses for OpenLineage caller-identity parentage: the MCP spec reserves
    `traceparent`/`tracestate`/`baggage` directly under `params._meta`
    (RAID I05), so it gets its own flat key rather than sharing the
    bespoke, reverse-DNS-prefixed one.
    """
    with tracer.start_as_current_span("governed_execute_sql") as span:
        span.set_attribute("lineage.governed", True)
        carrier: dict[str, str] = {}
        inject(carrier)
        await call(session, sql, meta={"traceparent": carrier["traceparent"]})


async def run(n: int) -> None:
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await call(
                session,
                "CREATE TABLE IF NOT EXISTS obsinsure.agent_notes "
                "(source_table text, call_index text)",
            )

            for i in range(n):
                table = TABLES[i % len(TABLES)]
                await call(session, f"SELECT * FROM obsinsure.{table} LIMIT 5")

                if i % 10 == 0:
                    await call(
                        session,
                        "INSERT INTO obsinsure.agent_notes (source_table, call_index) "
                        f"VALUES ('{table}', '{i}')",
                    )

                print(f"[{i + 1}/{n}] execute_sql(table={table})")

    print(f"\nDone: {n} query calls fired.")
    print("Compare http://localhost:16686 (Jaeger, ~10% expected) against")
    print("        http://localhost:3033  (Marquez, 100% expected).")


async def run_mixed(n: int) -> None:
    """Scenario 2b: N mixed sessions, one trace per session.

    Each session is one parent span wrapping `ORDINARY_SPANS_PER_SESSION`
    ordinary child spans plus one child span wrapping a real governed
    `execute_sql` call. Check the resulting traces in Jaeger: each should
    show `ORDINARY_SPANS_PER_SESSION + 1` spans total (plus the parent),
    all retained together even though only one of them carries
    `lineage.run_id`.
    """
    tracer = configure_tracing()
    rng = random.Random(MIXED_SEED)
    names = [name for name, _ in ORDINARY_OPERATIONS]
    weights = [weight for _, weight in ORDINARY_OPERATIONS]

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            await call(
                session,
                "CREATE TABLE IF NOT EXISTS obsinsure.agent_notes "
                "(source_table text, call_index text)",
            )

            for i in range(n):
                table = TABLES[i % len(TABLES)]
                with tracer.start_as_current_span("session") as parent:
                    parent.set_attribute("session.index", i)

                    for j, op_name in enumerate(rng.choices(names, weights=weights, k=ORDINARY_SPANS_PER_SESSION)):
                        ordinary_operation(tracer, op_name, j)

                    await governed_call(tracer, session, f"SELECT * FROM obsinsure.{table} LIMIT 5")

                print(f"[{i + 1}/{n}] mixed session (table={table})")

    # The exporter batches asynchronously; without an explicit flush a
    # short-lived script like this one can exit before the last batch is
    # sent. `mcp_server_ol`'s server process never needs this — it just
    # keeps running.
    trace.get_tracer_provider().shutdown()

    print(f"\nDone: {n} mixed sessions fired ({ORDINARY_SPANS_PER_SESSION} ordinary + 1 governed span each).")
    print("Compare http://localhost:16686 (Jaeger) — each session's trace should")
    print("        show every span retained together, not just the governed one.")


def parse_args(argv: list[str]) -> tuple[int, bool]:
    """Manual, minimal parsing — `[N] [--mixed]` in either order.

    Not argparse: flat mode's existing behavior (including how it fails on
    a bad N) must not change when `--mixed` is absent, and the previous
    `int(sys.argv[1])` gave a plain traceback rather than argparse's usage
    message. Keeping the same shape keeps that identical.
    """
    mixed = "--mixed" in argv
    positional = [arg for arg in argv if arg != "--mixed"]
    n = int(positional[0]) if positional else 100
    return n, mixed


if __name__ == "__main__":
    count, mixed = parse_args(sys.argv[1:])
    asyncio.run(run_mixed(count) if mixed else run(count))

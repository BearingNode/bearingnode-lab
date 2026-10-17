"""
I64 / I66 probe — what MCP SDK 2.x does with `_meta` and trace context, set against our asks.

The lab's server cannot run on SDK 2.x: `postgres-mcp` 0.3.0 imports `FastMCP`, which
2.x renamed, and `main.py` calls `mcp.get_context()`, which 2.x does not have (I64).
This probe does not try to. It stands up a small 2.x `MCPServer` with one tool, and
reuses the lab's own `meta.py` readers and `LineageEmitter` unchanged, so the
questions that do not depend on `postgres-mcp` can still be answered on 2.x:

  1. Does our `_meta` key arrive at a 2.x handler intact, and does `parent_from_meta`
     read it, so that a `ParentRunFacet` is built from it?
  2. Does the 2.x client inject `traceparent` into `_meta` by itself, and does the 2.x
     server parent its own span from it? What if the caller sends its own `traceparent`?
     What if the caller has no OpenTelemetry SDK?
  3. What is the span shape for one tool call that runs one statement, and for one that
     runs three? Where does a statement span sit when it is started the ambient way, and
     where when it takes the parent from `_meta` by hand, as `driver.py` does today?
  4. What happens to a single run reference set on the SDK's tool-call span when the call
     runs several statements (the cardinality point in I66)?
  5. Can a 2.x `ServerMiddleware` hand `ctx.meta` to code that has no `Context`, which is
     the seam `main.py` would use in place of `mcp.get_context()`?

What it mirrors, so it can be checked against the source: the statement span and its
attributes follow `mcp_server_ol/driver.py` (`execute_query`), and the two readers are
the ones `main.py` wires in. What it does not do: run SQL, reach Postgres or Marquez, or
exercise `postgres-mcp`. Events go to an in-memory transport.

Not a test: it states facts and does not grade them. Read the output.

    cd mcp-lineage
    uv run --no-project --python 3.12 --with mcp==2.3.0 \
        --with-editable mcp_server_ol python probes/verify_sdk2_meta_and_spans.py

Needs no running stack. Uses an isolated environment, so the lab's lock stays on SDK 1.x.
"""

from __future__ import annotations

import json
import logging
import socket
import subprocess
import sys
import textwrap
import threading
import time
from contextvars import ContextVar
from importlib.metadata import version
from typing import Any

import anyio
import uvicorn
from mcp.client.client import Client
from mcp.server.mcpserver import Context, MCPServer
from openlineage.client import OpenLineageClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from mcp_server_ol.lineage import LineageEmitter, ParsedStatement
from mcp_server_ol.meta import LINEAGE_META_KEY, parent_from_meta, traceparent_from_meta
from mcp_server_ol.naming import target_from_dsn

CALLER_RUN = "0198c1e2-aaaa-7bbb-8ccc-0123456789ab"
CALLER_JOB = ("probe-caller", "agent-session")

# -- telemetry: one in-process provider for client and server spans -------------------------------

EXPORTER = InMemorySpanExporter()
PROVIDER = TracerProvider()
PROVIDER.add_span_processor(SimpleSpanProcessor(EXPORTER))
trace.set_tracer_provider(PROVIDER)
TRACER = trace.get_tracer("sdk2-probe")

# -- lineage: the lab's own emitter, events kept in memory ----------------------------------------


class _Capture:
    kind = "capturing"

    def __init__(self) -> None:
        self.events: list[Any] = []

    def emit(self, event: Any) -> None:
        self.events.append(event)


CAPTURE = _Capture()
EMITTER = LineageEmitter(
    OpenLineageClient(transport=CAPTURE),  # type: ignore[arg-type]
    target_from_dsn("postgresql://postgres:postgres@postgres:5432/warehouse"),
    job_namespace="mcp-lineage-probe",
    default_schema="obsinsure",
)
STATEMENT = ParsedStatement(sql="SELECT 1 FROM obsinsure.premium", inputs=("obsinsure.premium",), outputs=())

# -- the server: a 2.x MCPServer with one tool and a meta-stashing middleware ---------------------

STASH: ContextVar[Any] = ContextVar("probe_meta", default=None)
OBSERVED: list[dict[str, Any]] = []


class StashMeta:
    """The seam `main.py` would use in place of `mcp.get_context().request_context.meta`."""

    async def __call__(self, ctx: Any, call_next: Any) -> Any:
        token = STASH.set(ctx.meta)
        try:
            return await call_next(ctx)
        finally:
            STASH.reset(token)


server = MCPServer("sdk2-probe", middleware=[StashMeta()])


def _lineage_provider_without_context() -> Any:
    """What a driver factory sees: no `Context` argument, only the contextvar."""
    return STASH.get()


@server.tool()
async def execute_sql(statements: int, parenting: str, ctx: Context) -> str:
    request_context = ctx.request_context
    meta = request_context.meta
    via_middleware = _lineage_provider_without_context()
    parent = parent_from_meta(meta)
    tp = traceparent_from_meta(meta)
    sdk_span = trace.get_current_span()

    run_ids: list[str] = []
    for _ in range(statements):
        kwargs: dict[str, Any] = {}
        if parenting == "manual" and tp.context is not None:
            kwargs["context"] = tp.context  # what driver.py's execute_query does today
        with TRACER.start_as_current_span("mcp.execute_sql", **kwargs) as span:
            run_id = EMITTER.new_run_id()
            run_ids.append(run_id)
            span.set_attribute("lineage.run_id", run_id)
            span.set_attribute("lineage.actor_status", str(parent.status))
            EMITTER.start(run_id, "mcp.execute_sql", STATEMENT, parent.identity, str(parent.status))
            EMITTER.complete(run_id, "mcp.execute_sql", STATEMENT, parent.identity, str(parent.status))
        # Probe only: a single-valued reference on the SDK's tool-call span, once per statement.
        sdk_span.set_attribute("lineage.run_id", run_id)

    OBSERVED.append(
        {
            "protocol_version": request_context.protocol_version,
            "meta_type": type(meta).__name__,
            "meta_keys": sorted(meta.keys()) if meta else [],
            "meta_from_context_equals_meta_from_middleware": meta == via_middleware,
            "parent_status": str(parent.status),
            "parent_run_id": parent.identity.run_id if parent.identity else None,
            "traceparent_status": str(tp.status),
            "meta_traceparent": meta.get("traceparent") if meta else None,
            "run_ids": run_ids,
        }
    )
    return json.dumps({"statements": statements})


# -- run the server over real HTTP, in a thread with its own event loop ---------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def start_server() -> tuple[uvicorn.Server, str]:
    port = _free_port()
    config = uvicorn.Config(server.streamable_http_app(), host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    threading.Thread(target=srv.run, daemon=True).start()
    deadline = time.time() + 15
    while not srv.started and time.time() < deadline:
        time.sleep(0.05)
    if not srv.started:
        raise SystemExit("probe server did not start")
    return srv, f"http://127.0.0.1:{port}/mcp"


# -- clients ----------------------------------------------------------------------------------------


async def call_with_sdk(url: str, arguments: dict[str, Any], meta: dict[str, Any]) -> None:
    """A caller that has an OpenTelemetry SDK configured, wrapped in its own agent span."""
    with TRACER.start_as_current_span("caller.agent_turn"):
        async with Client(url) as client:
            await client.call_tool("execute_sql", arguments, meta=meta)  # type: ignore[arg-type]


NO_SDK_CLIENT = textwrap.dedent(
    """
    import anyio, json, sys
    from mcp.client.client import Client
    url, arguments, meta = sys.argv[1], json.loads(sys.argv[2]), json.loads(sys.argv[3])
    async def main():
        async with Client(url) as client:
            await client.call_tool("execute_sql", arguments, meta=meta)
    anyio.run(main)
    """
)


def call_without_sdk(url: str, arguments: dict[str, Any], meta: dict[str, Any]) -> None:
    """A caller process with no OpenTelemetry SDK: only the API, so a no-op tracer."""
    subprocess.run(
        [sys.executable, "-c", NO_SDK_CLIENT, url, json.dumps(arguments), json.dumps(meta)],
        check=True,
        timeout=60,
    )


# -- reporting --------------------------------------------------------------------------------------


def _short(n: int | None, width: int) -> str:
    return "-" if n is None else format(n, f"0{width}x")[-6:]


def spans_report() -> dict[str, Any]:
    time.sleep(0.3)
    spans = list(EXPORTER.get_finished_spans())
    rows = []
    for s in spans:
        if not (
            s.name.startswith("MCP send tools/call")
            or s.name.startswith("tools/call")
            or s.name in ("mcp.execute_sql", "caller.agent_turn")
        ):
            continue
        rows.append(
            {
                "name": s.name,
                "kind": s.kind.name,
                "trace": _short(s.context.trace_id, 32),
                "span": _short(s.context.span_id, 16),
                "parent": _short(s.parent.span_id if s.parent else None, 16),
                "attrs": {
                    k: v for k, v in s.attributes.items() if k.startswith(("mcp.", "gen_ai.", "lineage."))
                },
            }
        )

    def by_name(prefix: str) -> list[dict[str, Any]]:
        return [r for r in rows if r["name"].startswith(prefix)]

    agent = by_name("caller.agent_turn")
    client = by_name("MCP send tools/call")
    sdk_server = by_name("tools/call")
    stmts = by_name("mcp.execute_sql")
    return {"rows": rows, "agent": agent, "client": client, "sdk_server": sdk_server, "stmts": stmts}


def facts(label: str, observed: dict[str, Any], rep: dict[str, Any]) -> None:
    print(f"\n=== {label}")
    print(
        f"  server saw: protocol {observed['protocol_version']}, _meta is a {observed['meta_type']} "
        f"with keys {observed['meta_keys']}"
    )
    print(
        f"  our key read by parent_from_meta: {observed['parent_status']}, "
        f"run id matches the caller's: {observed['parent_run_id'] == CALLER_RUN}"
    )
    print(f"  traceparent_from_meta: {observed['traceparent_status']}")
    print(
        f"  ctx.request_context.meta equals what the middleware stashed: "
        f"{observed['meta_from_context_equals_meta_from_middleware']}"
    )
    for r in rep["rows"]:
        a = " ".join(f"{k}={v}" for k, v in r["attrs"].items())
        ids = f"trace …{r['trace']} span …{r['span']} parent …{r['parent']}"
        print(f"    {r['name']:<34} {r['kind']:<8} {ids}  {a}")
    client, sdk_server, stmts, agent = rep["client"], rep["sdk_server"], rep["stmts"], rep["agent"]
    if sdk_server:
        s = sdk_server[0]
        if client:
            print(f"  SDK server span is a child of the SDK client span: {s['parent'] == client[0]['span']}")
            print(f"  same trace as the SDK client span: {s['trace'] == client[0]['trace']}")
        elif agent:
            print(f"  SDK server span is in the caller's trace: {s['trace'] == agent[0]['trace']}")
        else:
            print(
                f"  the caller sent no span: the SDK server span starts a new trace (parent …{s['parent']})"
            )
        print(f"  statement spans: {len(stmts)}; distinct run ids: {len(set(observed['run_ids']))}")
        for st in stmts:
            where = (
                "child of the SDK server span"
                if st["parent"] == s["span"]
                else "child of the SDK client span"
                if client and st["parent"] == client[0]["span"]
                else f"parent …{st['parent']}"
            )
            print(f"    a statement span is a {where}; in the SDK span's trace: {st['trace'] == s['trace']}")
        held = s["attrs"].get("lineage.run_id")
        print(
            f"  lineage.run_id on the SDK server span after {len(observed['run_ids'])} statement(s): "
            f"{held!r}; run ids it could have held: {len(observed['run_ids'])}"
        )
    events = list(CAPTURE.events)
    parent_ids = {getattr(getattr(e.run.facets.get("parent"), "run", None), "runId", None) for e in events}
    print(
        f"  OpenLineage events: {len(events)}; ParentRunFacet run id on them: {sorted(map(str, parent_ids))}"
    )


def reset() -> None:
    EXPORTER.clear()
    CAPTURE.events.clear()
    OBSERVED.clear()


def main() -> int:
    logging.disable(logging.INFO)  # the SDK logs every HTTP request; the facts are below
    srv, url = start_server()
    meta_ours = {
        LINEAGE_META_KEY: {"parentRunId": CALLER_RUN, "jobNamespace": CALLER_JOB[0], "jobName": CALLER_JOB[1]}
    }
    print(
        f"MCP SDK under probe: mcp {version('mcp')}; opentelemetry-sdk {version('opentelemetry-sdk')}; "
        f"openlineage-python {version('openlineage-python')}"
    )

    scenarios: list[tuple[str, dict[str, Any], dict[str, Any], str]] = [
        (
            "S1  one statement, ambient parenting, caller with an OTel SDK, our key in _meta",
            {"statements": 1, "parenting": "ambient"},
            meta_ours,
            "sdk",
        ),
        (
            "S2  three statements, ambient parenting (the statement span starts inside the SDK's span)",
            {"statements": 3, "parenting": "ambient"},
            meta_ours,
            "sdk",
        ),
        (
            "S3  three statements, manual parenting from _meta (what driver.py does today)",
            {"statements": 3, "parenting": "manual"},
            meta_ours,
            "sdk",
        ),
        (
            "S4  the caller also supplies its own flat traceparent, as the lab's driver does",
            {"statements": 1, "parenting": "ambient"},
            {**meta_ours, "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"},
            "sdk",
        ),
        (
            "S5  a caller process with no OpenTelemetry SDK, our key in _meta",
            {"statements": 1, "parenting": "ambient"},
            meta_ours,
            "nosdk",
        ),
    ]
    for label, args, meta, who in scenarios:
        reset()
        if who == "sdk":
            anyio.run(call_with_sdk, url, args, meta)
        else:
            call_without_sdk(url, args, meta)
        if not OBSERVED:
            print(f"\n=== {label}\n  the server handler did not run")
            continue
        facts(label, OBSERVED[-1], spans_report())
        if label.startswith("S4"):
            print(f"  traceparent the handler read from _meta: {OBSERVED[-1]['meta_traceparent']}")
            print("  the caller supplied: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")

    srv.should_exit = True
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

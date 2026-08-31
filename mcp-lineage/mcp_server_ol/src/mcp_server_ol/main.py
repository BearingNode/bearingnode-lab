"""Entrypoint: run `postgres-mcp` with lineage emission attached.

The entire integration is `install()` below — replace the module-level
`get_sql_driver` factory with one that returns an instrumented driver, then
hand off to upstream's own `main()`. Nothing in `postgres_mcp` is modified,
forked or vendored; it stays pinned at the version in `pyproject.toml`.

That brevity is the evidence for RAID D03. Adding OpenLineage to a real,
widely-adopted MCP server is a subclass and a factory swap. The ecosystem is
not short of a mechanism.
"""

from __future__ import annotations

import logging
import os
import sys

from openlineage.client import OpenLineageClient
from openlineage.client.transport.http import HttpConfig, HttpTransport

from mcp_server_ol import telemetry
from mcp_server_ol.driver import FailureMode, LineageSqlDriver
from mcp_server_ol.lineage import LineageEmitter
from mcp_server_ol.meta import (
    ABSENT,
    ABSENT_TRACEPARENT,
    ParentLookup,
    TraceparentLookup,
    parent_from_meta,
    traceparent_from_meta,
)
from mcp_server_ol.naming import target_from_dsn

logger = logging.getLogger(__name__)

DEFAULT_JOB_NAMESPACE = "mcp-lineage-demo"


def _current_parent() -> ParentLookup:
    """Read the caller's lineage identity off the in-flight MCP request.

    Imported lazily and defended heavily: there is no request context outside a
    tool call, and lineage must never be the reason a tool call fails (D11).

    **The failure is reported, not swallowed (RAID I29).** This was `debug` in a
    process where nothing configured logging, so a missing request context —
    our instrumentation failing to see the call at all — produced no output
    anywhere. It now warns and counts. Note this is *our* failure, distinct from
    a caller legitimately not supplying identity, which is `ABSENT` and quiet.
    """
    try:
        from postgres_mcp.server import mcp

        return parent_from_meta(mcp.get_context().request_context.meta)
    except Exception:  # noqa: BLE001
        logger.warning("lineage: no MCP request context; actor recorded as unknown", exc_info=True)
        telemetry.record_dropped(telemetry.Dropped.NO_REQUEST_CONTEXT)
        return ABSENT


def _current_traceparent() -> TraceparentLookup:
    """Read an inbound `traceparent` off the in-flight MCP request (RAID I34).

    Mirrors `_current_parent()` exactly — same lazy import, same defensive
    wrapping, same reasoning: there is no request context outside a tool call,
    and this must never be the reason a tool call fails (D11). The failure is
    reported, not swallowed, for the same RAID I29 reason `_current_parent()`
    states: a missing request context is *our* instrumentation failing to see
    the call, distinct from a caller legitimately sending no `traceparent`,
    which is `ABSENT_TRACEPARENT` and quiet.
    """
    try:
        from postgres_mcp.server import mcp

        return traceparent_from_meta(mcp.get_context().request_context.meta)
    except Exception:  # noqa: BLE001
        logger.warning("lineage: no MCP request context; starting a fresh span", exc_info=True)
        telemetry.record_dropped(telemetry.Dropped.NO_REQUEST_CONTEXT)
        return ABSENT_TRACEPARENT


def _failure_mode() -> FailureMode:
    """Read the fail-open/fail-closed posture from the environment (RAID R08).

    Defaults to **open** per D11 — an integration that can break the tool call
    will not be deployed, and adoption is the binding constraint on every ask in
    D10. `LINEAGE_FAILURE_MODE=closed` selects the posture a control environment
    is likely to require, where an unrecorded read of a governed table is the
    state the control exists to prevent.

    An unrecognised value is refused rather than defaulted. Silently falling back
    to fail-open would mean a deployment that believes it is failing closed and
    is not — which is worse than either mode chosen deliberately.
    """
    raw = os.environ.get("LINEAGE_FAILURE_MODE", FailureMode.OPEN).strip().lower()
    try:
        mode = FailureMode(raw)
    except ValueError:
        raise SystemExit(
            f"LINEAGE_FAILURE_MODE must be 'open' or 'closed', got {raw!r}. "
            "Refusing to start rather than silently failing open."
        ) from None

    if mode is FailureMode.CLOSED:
        logger.warning("lineage: FAIL-CLOSED — a tool call will be refused if its lineage cannot be recorded")
    return mode


def install() -> None:
    """Point `postgres_mcp`'s driver factory at the instrumented driver."""
    from postgres_mcp import server as upstream

    # Both before anything else can fail: RAID I29's root cause was that the
    # failure paths had nowhere to report to.
    telemetry.configure_logging()
    telemetry.configure_telemetry()

    dsn = os.environ.get("DATABASE_URI") or os.environ.get("WAREHOUSE_DSN")
    if not dsn:
        raise SystemExit("DATABASE_URI is required to build OpenLineage dataset names")

    emitter = LineageEmitter(
        OpenLineageClient(
            transport=HttpTransport(HttpConfig(url=os.environ.get("MARQUEZ_URL", "http://marquez:5000")))
        ),
        target_from_dsn(dsn),
        job_namespace=os.environ.get("OL_JOB_NAMESPACE", DEFAULT_JOB_NAMESPACE),
        default_schema=os.environ.get("OL_DEFAULT_SCHEMA", "public"),
    )

    failure_mode = _failure_mode()
    original = upstream.get_sql_driver

    async def get_sql_driver():  # type: ignore[no-untyped-def]
        driver = await original()
        # RESTRICTED mode wraps the base driver in a SafeSqlDriver; instrument
        # whichever object actually reaches the database.
        base = getattr(driver, "sql_driver", driver)
        instrumented = LineageSqlDriver(
            conn=base.conn,
            emitter=emitter,
            parent_provider=_current_parent,
            traceparent_provider=_current_traceparent,
            failure_mode=failure_mode,
        )
        if base is driver:
            return instrumented
        driver.sql_driver = instrumented
        return driver

    upstream.get_sql_driver = get_sql_driver
    logger.info("lineage: instrumented postgres-mcp; emitting to %s", os.environ.get("MARQUEZ_URL"))


STREAMABLE_HTTP = "streamable-http"


def install_streamable_http() -> None:
    """Serve MCP over Streamable HTTP instead of the deprecated SSE transport.

    **The same trick as `install()`, for the same reason (RAID D13).** Upstream
    hardcodes `choices=["stdio", "sse"]` and branches to `mcp.run_sse_async()`;
    0.3.0 is the latest release, so this is not a stale pin (I30). The `mcp` SDK
    *does* support Streamable HTTP, and `run_streamable_http_async()` reads the
    same `settings.host`/`settings.port` that upstream has already populated
    from `--sse-host`/`--sse-port` — so replacing the bound method is the whole
    change. Everything else upstream does on the way there, the connection pool,
    the access mode, the signal handlers, runs exactly as it intends.

    That it is again a one-line swap is the point: adding the transport the MCP
    specification now prefers, to the ecosystem's most-adopted Postgres MCP
    server, is a few lines nobody has written.
    """
    from postgres_mcp.server import mcp

    async def run_streamable_http_instead() -> None:
        logger.info(
            "transport: serving Streamable HTTP on %s:%s (upstream offers stdio/sse only)",
            mcp.settings.host,
            mcp.settings.port,
        )
        await mcp.run_streamable_http_async()

    mcp.run_sse_async = run_streamable_http_instead


def _select_transport(argv: list[str]) -> bool:
    """Consume our own `--transport streamable-http`, leaving upstream's args valid.

    Upstream's argparse rejects any value outside `stdio`/`sse`, so the flag is
    rewritten to `sse` before it ever reaches it. `MCP_TRANSPORT` is honoured
    too, because the container sets transport by environment.
    """
    wanted = os.environ.get("MCP_TRANSPORT", "").strip().lower() == STREAMABLE_HTTP
    for i, arg in enumerate(argv):
        if arg == "--transport" and i + 1 < len(argv) and argv[i + 1] == STREAMABLE_HTTP:
            argv[i + 1] = "sse"
            wanted = True
        elif arg == f"--transport={STREAMABLE_HTTP}":
            argv[i] = "--transport=sse"
            wanted = True
    return wanted


def main() -> None:
    if _select_transport(sys.argv):
        install()
        install_streamable_http()
    else:
        install()

    # The package-level `main` is the sync wrapper that calls `asyncio.run` on
    # `server.main()`; the one in `server` is a coroutine. Take upstream's own
    # entrypoint so argument parsing and the rest of startup stay theirs.
    from postgres_mcp import main as upstream_main

    sys.exit(upstream_main())


if __name__ == "__main__":
    main()

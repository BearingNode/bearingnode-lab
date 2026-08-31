# Instrumented postgres-mcp. Upstream is installed from PyPI at a pinned
# version — not forked, not vendored (RAID D03).
FROM python:3.12-slim

# uv, pinned, per this lab's own tooling standard: uv, never bare pip.
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# --frozen: install exactly what the lock says, and fail if it has drifted.
# --no-binary is deliberately NOT used, but a source build of openlineage-sql
# would mean no wheel matched — the failure RAID D09 declined to engage with
# and R05 tracks. If this step ever starts compiling Rust, stop and read R05.
RUN uv sync --frozen --no-dev --no-editable

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Upstream's own argument parsing and transport selection; we only swap the
# SQL driver factory before handing off.
ENTRYPOINT ["python", "-m", "mcp_server_ol.main"]
# Streamable HTTP, not SSE: MCP deprecated SSE, and hosted enterprise MCP is
# what this workstream's requirements address (RAID D13, I30). Upstream accepts
# only stdio/sse; `--sse-host`/`--sse-port` still carry host and port because
# that is where upstream reads them from. Endpoint is /mcp.
CMD ["--transport", "streamable-http", "--sse-host", "0.0.0.0", "--sse-port", "8000"]

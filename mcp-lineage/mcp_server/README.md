# `mcp_server/` — frozen exhibit, not a live component

**This directory is frozen.** It is kept under the **frozen exhibit** exception
to this lab's own repo-hygiene rule against empty or dead files, per RAID
`D09` (`public-lab` register). It is not
run by `docker-compose.yml` (see the comment above the `mcp-server` service
there), it is not tested, and it is not to be repaired. Read this file before
touching anything in this folder.

## Why it is kept instead of deleted

The delta between this hand-rolled scaffold and its replacement,
[`../mcp_server_ol/`](../mcp_server_ol/), is itself the deliverable: the
workstream's central claim is that instrumenting a real MCP server for
OpenLineage costs *very little* (RAID `D03`) — a driver subclass and a factory
swap, not a fork. That claim is evidenced by **how small the working
integration turned out to be**, and a reader can only see that by comparing
this from-scratch scaffold against the real thing it was replaced with. An
undocumented old version, or a sentence asserting the same thing, is weaker
evidence than the diff.

## Frozen at

`bd5777183558e38bc480c8239f30c01ceb0d4e4b` — *"Fix mcp-lineage stack; verified
running end to end"*, 2026-07-27. No commit has touched `server.py`,
`Dockerfile`, or `requirements.txt` since. `D09` (2026-07-29) decided to keep
this directory's contents exactly as they stood at that commit.

## What replaced it

[`../mcp_server_ol/`](../mcp_server_ol/) — RAID `D03`: instruments the real,
deployed, open-source [`crystaldba/postgres-mcp`](https://github.com/crystaldba/postgres-mcp)
("Postgres MCP Pro", pinned `postgres-mcp==0.3.0`) by subclassing its
`SqlDriver` and swapping a module-level factory, rather than building a bespoke
server from scratch as this directory does. `docker-compose.yml`'s `mcp-server`
service builds `../mcp_server_ol`, not this directory.

## Known defects

Every defect below is **left in place**. Fixing any of them would falsify the
as-is state this exhibit exists to demonstrate (obligation 4 of the frozen-exhibit
exception).

1. **Emits the retired pre-A04 attribute framing.** `server.py` sets
   `data.resource.namespace` / `data.resource.name` / `data.resource.operation`
   on every span (constants at lines 58–60; set on the span in
   `query_dataset` at lines 112–114 and in `write_dataset` at lines 151–153).
   `mcp-lineage` RAID **A04** invalidated this framing: OTel's GenAI/MCP
   semantic conventions already define `mcp.resource.uri` for this purpose,
   scoped to `resources/read`-family calls (`tools/call`, which is what this
   server uses, has no defined attribute at all — a narrower and sharper gap
   than "nothing exists"). `mcp-lineage` RAID **I09** tracks that this
   reference implementation still argues the retired claim. **Marked at the
   emission site in `server.py` itself** — see the comments there — so a
   reader of the code, not just of this README, cannot mistake it for a
   current claim.
2. **Non-conformant OpenLineage dataset naming.** `_dataset()` (lines 100–101)
   and `OL_NAMESPACE` (line 52) emit namespace `warehouse`, name
   `obsinsure.{table}`. The spec (`website/docs/spec/naming.md`) requires
   namespace `postgres://{host}:{port}`, name `{database}.{schema}.{table}`.
   Tracked as `mcp-lineage` RAID **I16**, fixed in the replacement
   (`../mcp_server_ol/src/mcp_server_ol/naming.py`).
3. **No intent/effect distinction.** Both the `START` and `COMPLETE` events
   list the same declared dataset; nothing on the event, in this file, or in
   the Marquez view states that what is recorded is *declared* (parsed intent)
   rather than *observed* (actual effect) — a failed or rolled-back statement
   would still report its datasets as touched, though nothing in this
   particular server exercises that path today. Tracked as `mcp-lineage` RAID
   **I17**, addressed in the replacement.
4. **In-source credential default — known, deliberate, and not a defect.**
   `WAREHOUSE_DSN` defaults to
   `postgresql://postgres:postgres@localhost:5432/warehouse`. On its face this is
   the anti-pattern this lab's own repo-hygiene rule against credentials in
   source names as a non-negotiable, so it is called out
   here rather than left for a reader to find and draw their own conclusion
   about our standards. **It stays, on three grounds.** There is no secret:
   `postgres:postgres@localhost` is the well-known default loopback DSN for a
   throwaway container and grants nothing to anyone off the machine running the
   demo. Its presence is load-bearing for what this exhibit is *for* — clone the
   repository, start the compose stack, and it runs, with no configuration step
   and nothing to obtain; being able to see and run the thing is what makes it an
   exhibit rather than an assertion. And it is overridable by the environment
   variable, so nothing is obliged to use it. Marked in full at the definition
   site in `server.py`. **Do not "fix" this** — removing the default breaks the
   clone-and-run property without removing an exposure, because there is none.
   Confirmed by the principal 2026-07-30.
5. **No failure-path emission.** Neither tool function emits an OpenLineage
   `FAIL` event nor sets OTel span error status when the database call raises
   — the `_emit_ol_event("COMPLETE", ...)` call is simply never reached, and
   the exception propagates with no lineage or trace record of the failure.
   This lab's own testing standard names an untested failure path as
   indistinguishable from event loss, which is the thing this whole workstream
   argues against. Not currently tracked under a RAID ID; flagged for the
   register.
6. **`requirements.txt`, not `pyproject.toml` + `uv.lock`.** Predates this
   lab's dependency-management rule. Kept as-is: it is part of what makes this
   exhibit the *pre-standards* state, in contrast with
   `../mcp_server_ol/pyproject.toml`.

### Two claims about this file elsewhere are stale, not currently true

RAID `D09`'s own rationale (`public-lab` register, 2026-07-29) lists "no
OpenTelemetry" and "a known import bug" among this exhibit's defects. Verified
directly against the file in this directory (2026-07-30), **neither currently
applies here**:

- **OpenTelemetry is present.** `server.py` sets up a `TracerProvider`, an
  `OTLPSpanExporter`, and wraps both tools in spans (lines 62–65, 111, 150).
  `mcp-lineage` RAID **I29** itself confirms this the other way round: it was
  `mcp_server_ol` that briefly had **no** OpenTelemetry after the `D03`
  rework — "the old `mcp_server/` had it and the D03 rework silently dropped
  it" — since fixed in the replacement. The "no OpenTelemetry" defect
  description in `D09` describes the replacement's transitional state, not
  this exhibit.
- **The import bug was real, and was already fixed before `D09` was written.**
  The private lab's session record for 2026-07-27 notes that
  `psycopg2.sql` was used but never imported, so both tools raised on first
  call. Commit `bd5777183558e38bc480c8239f30c01ceb0d4e4b` (2026-07-27) added
  the missing `import psycopg2.sql` — two days before `D09` (2026-07-29) cited
  the bug as a reason a CI run against this file would go red. Confirmed
  2026-07-30: the file's imports resolve and `ruff check` on it passes clean.

Both corrections are written up for the register rather than silently folded
into `D09`'s text; the full note is kept in the private working register — ask the relevant maintainer for it.

## Not repaired

None of the defects above are fixed here, including the ones that would take
one line. That is the point of the exception this directory relies on.

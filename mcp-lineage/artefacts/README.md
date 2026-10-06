# artefacts

Published-output assets for the mcp-lineage workstream — figures that
accompany the reference implementation, not part of it.

## What lives here

| File | What it is |
|---|---|
| `bearingnode-mcp-lineage-signal-scope.html` / `.png` | What an OTel span carries, what an OpenLineage event carries, what both carry, and what neither does — at field level, with a worked example, anchored on the two records shown as objects |
| `bearingnode-mcp-lineage-framework-entry.html` / `.png` | Where an agent's data access enters the D&I Observability framework, and why the core layer can't be claimed without the foundational one |
| `bearingnode-mcp-lineage-call-chain.html` / `.png` | The call chain of events from an agent's MCP tool call through to OpenLineage emission, the two divergent write paths, and — as stage 6's climax — the run event before and after the two Run facets this workstream asks OpenLineage for |
| `BearingNode-AM+DIo11y-joined-mapped.png` | BearingNode's existing Comply/Govern/Manage + D&I Observability diagram, cited from `REQUIREMENTS.md` §10 |
| `logos/` | Vendored BearingNode, OpenTelemetry and OpenLineage marks — see [`logos/README.md`](logos/README.md) for provenance and trademark terms |
| `build.py`, `src/` | Build source for the four published figures above |
| `bearingnode-mcp-lineage-event-lifecycle.html` / `.png` | The metadata data model (RAID D27), drawn as a bow tie. The left side is event capture, what is captured as the producer's call goes out. The middle is where it lands. The right side mirrors the left: what an auditor, SRE or governance analyst does to recreate the event. It shows the intended design, and marks what is an ask and what is assumed. Source is `src/event-lifecycle.template.html` and `src/event-lifecycle.data.js`, registered in `build.py`'s `BUILDS`. Verified against the code on 2026-10-05, and against `checks.js` at 375, 740, 940 and 1180 px and in static mode |

**Naming.** Every published figure carries the `bearingnode-mcp-lineage-`
prefix, so it stays attributable once it has left this repository and is
sitting in a downloads folder, a slide deck or an issue thread.

**HTML is the source, PNG is the export.** Each figure is authored as HTML and
CSS (`src/*.template.html`), rendered in a real browser so layout is correct
by construction, and exported to PNG at 2x device pixel ratio for anywhere
static rendering is needed (this README, the paper). Don't hand-edit a PNG —
edit the template and rebuild.

## Rebuilding a figure

The brand typeface and the render-check script are maintainer-only tooling
and aren't part of this published snapshot — the built `.html` and `.png`
files ship complete and don't need rebuilding to view. To make a change:
edit the relevant `src/*.template.html`, then run `python3 artefacts/build.py`,
which inlines the font and logo assets as base64 (the only reason a build
step exists at all — everything else is plain HTML/CSS).

## Why the interactive figures aren't embedded on GitHub

GitHub's markdown sanitises `<script>`, `<iframe>` and `<style>`, so the
interactive HTML versions can't render inline in this README. The canonical,
interactive versions are published on bearingnode.com; this repository carries
the static PNG export of each, linking back to the post.

## Branding

The BearingNode mark, and the OpenTelemetry / OpenLineage project marks, are
vendored into [`logos/`](logos/README.md) — see that file for provenance and
trademark terms. `BearingNode-AM+DIo11y-joined-mapped.png` is an existing
BearingNode diagram, reproduced here the same way, following the palette and
typography of BearingNode's brand guidelines.

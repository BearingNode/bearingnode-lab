# Logos

Marks vendored into this folder for two different reasons — read the two
sections separately, since only one of them is BearingNode's own.

## Third-party project logos — not BearingNode's

`opentelemetry-horizontal-color.svg` and `openlineage-horizontal-color.svg` are
the official, unmodified marks of the OpenTelemetry project (CNCF) and the
OpenLineage project (LF AI & Data). **They are not BearingNode's property.**
They are reproduced here solely to identify each project accurately in a figure
describing what its standard carries — nominative use to name the thing, not an
endorsement or affiliation claim.

| File | Project | Source | Steward |
|---|---|---|---|
| `opentelemetry-horizontal-color.svg` | OpenTelemetry | [cncf/artwork](https://github.com/cncf/artwork/tree/main/projects/opentelemetry) | CNCF |
| `openlineage-horizontal-color.svg` | OpenLineage | [lfai/artwork](https://github.com/lfai/artwork/tree/main/projects/openlineage) | LF AI & Data |

Geometry and colour are untouched. The only change at build time is that each
file's inlined `<style>` block is promoted to `fill` attributes on its paths —
an inlined stylesheet otherwise leaks into the host document (OpenTelemetry's
contains a bare `svg { … }` selector that would apply to every other SVG on the
page).

Do not recolour, restretch, or place either mark on a ground that breaks its
contrast. If either foundation's trademark policy conflicts with this usage,
the mark comes out and the plain project name goes back in its place.
OpenLineage publishes no icon-only variant, so both projects use their
horizontal lockup here, for visual consistency rather than one having a mark
and the other a wordmark.

## BearingNode's own mark

`Logomark_horisontal_dark.svg` is BearingNode's own logo. It's included here,
rather than pulled from BearingNode's private brand-asset repository at build
time, so that cloning this repository alone is enough to rebuild the figures
that use it — no dependency on a repository this one doesn't ship.

# AGENTS.md — `mcp-lineage`

Workstream instructions. **Read the lab's root `AGENTS.md` first** — this file
holds only what is specific to `mcp-lineage`, and assumes the standards, the
`Status/` discipline and the non-negotiables stated there.

## What this workstream is

A reference implementation supporting two upstream filings:

- [OpenLineage #4484](https://github.com/OpenLineage/OpenLineage/issues/4484)
- [Model Context Protocol #2638](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2638)

**The claim: OpenTelemetry-based observability and OpenLineage-based lineage are
distinct signals, and neither can be derived from the other.** A trace does not
contain lineage; a lineage event does not contain a trace. Correlating them is a
design decision that has to be made deliberately.

It addresses the OpenLineage, OpenTelemetry and Model Context Protocol
communities. Code here is read by their maintainers.

## Non-negotiables

- **Correlate, never derive.** OpenLineage events are never generated from OTel
  spans, nor spans from lineage events. This is the workstream's central claim
  (RAID **D02**); code that blurs it refutes the thesis rather than implementing
  it.
- **No PII in the identity reference.** Pseudonymous references only (RAID
  **R02**). We are proposing actor identity in lineage — a reference
  implementation that leaks identity argues against its own RFC. Statement text
  and database error text are passed through unredacted, and anonymising or
  pseudonymising the stores is the operator's responsibility (RAID **A29**,
  **I59**). Do not describe the implementation as PII-free.
- **Mark stand-ins in both directions.** Attributes and facets we propose but
  which are not yet standardised must be unmistakably labelled in code and in the
  README, and must sit alongside conformant attributes rather than replacing
  them. A reader must never be left to infer that a stand-in is specified
  behaviour.
- **Specification behaviour is quoted at a stated version.** Not from summaries,
  not from recall. The register entries this rule exists because of are in
  [`Status/RAID.md`](Status/RAID.md) — grep it rather than relying on a list
  here, which goes stale silently.

## `mcp_server/` is a frozen exhibit

`mcp-lineage` **D03** records why `mcp_server/` is superseded rather than
extendable. It ships anyway, as a deliberately frozen as-is exhibit, because the
delta between what it did and what the workstream now does is part of the
evidence. The obligations that come with shipping it are stated in full in
`mcp_server/README.md`.

**Repair nothing in it.** The delta between
as-is and to-be is the deliverable, so a fix destroys the evidence.
`mcp_server/README.md` states its frozen state and every known defect.

## Before anything is filed upstream

- **The lab's own filing procedure is an internal document and is not
  published.** `PRINCIPLES.md` carries the reasoning in its place, and this file
  states the substance an outside reader needs directly, rather than pointing at
  a file they cannot open.
- **Check each project's own AI-disclosure requirements and follow them.** They
  differ, and the lab's `DISCLOSURE.md` does not substitute for theirs. MCP #2638
  was closed in part for filing without disclosure; refiling without checking
  repeats it.
- **Keep any reference to the #2638 closure factual and courteous.** State the
  date, the closing comment in its own words, and what was and was not asked.
  Say nothing about the person. The closing comment's criticism on disclosure
  was fair, and the register says so (RAID A08).

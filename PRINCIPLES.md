# Principles of approach

How this lab is built, and what we hold ourselves to.

## TL;DR

These are the aims this lab is built to, stated as targets we're trying to meet rather than warranties we're making.

- Portable over clever: Python and declarative config over shell, and the ecosystem's own clients over a hand-rolled payload.
- Tests assert and results are reproducible — a script that prints ✅, or a number without the command that produced it, is not evidence.
- Specification claims are checked against the specification itself, at a stated version — never a summary, never memory.
- The record ships with its own corrections, and a rejected option is written down so it isn't re-proposed by someone who couldn't see it was already considered.
- No credentials, ever; whether personal or identifying data appears at all is a workstream's own explicit design decision, stated plainly rather than left to infer; anything proposed but not yet standardised is labelled a stand-in rather than presented as settled.

**These are aims, not warranties.** We try to meet them and we will not always
succeed. Where we have missed, the status registers that ship with each
workstream are where it should be recorded — that is why they ship unpolished.
See [`DISCLOSURE.md`](DISCLOSURE.md) for how this applies to the lab's own
authorship, and [`CURATION.md`](CURATION.md) for what is edited on the way out.

## The principles

**Portable, not clever.** Python, not shell. Shell binds you to a platform, and
a reference implementation that only runs on its author's machine is not
evidence of anything. Declarative config before code — less code is less to
verify.

**Use the ecosystem's own clients.** We never hand-build another project's
payload. Hand-rolling their format demonstrates our reading of it, which is the
thing under discussion.

**Tests assert.** A script that prints ✅ and exits zero is a demo. A suite that
cannot fail tells you nothing.

**Show the working.** A number ships with the command that produced it. An
unreproduced result is marked unverified, not presented as a finding.

**Primary sources, at a stated version.** Specifications are read from the
specification — not from summaries, not from memory. We argue about what specs
do and do not carry; an argument built on a paraphrase is not an argument.

**The record ships, corrections included.** Assumptions, risks, issues and
decisions are written down as we go and published without tidying. Where we were
wrong, the invalidation stays beside the original wording. A register showing
only the decisions that survived would be a marketing document.

**Negative decisions are decisions.** What we rejected, and why — or it gets
re-proposed by someone who cannot see it was already considered.

**Mark what is not settled.** Anything we propose but which is not standardised
is labelled a stand-in, in code and in documentation, and sits alongside
conformant attributes rather than replacing them. You should never have to infer
whether you are looking at a specification or at our proposal.

**No credentials, ever.** Including as function defaults in a local lab.

**Personal or identifying data is a workstream's own explicit design
decision, not a lab-wide ban.** Some workstreams' own claims may require
carrying real or pseudonymous identity in emitted telemetry or lineage
metadata; others may need to exclude it entirely. Either is legitimate. What
is not legitimate is leaving a reader to infer the position — state it
plainly, in that workstream's own `AGENTS.md`, alongside how it is protected
if it is carried at all.

**Nothing generated is committed.** No reports, event dumps, coverage output or
virtual environments.

## Hold us to these

Our fuller engineering standards are not published here — most of it is internal
procedure, or rules aimed at a particular workstream's target communities rather
than at the lab. That is a scope judgement and it may be revisited. The
principles above are the part that generalises.

If the code looks like it follows a rule not stated here, ask. If it breaks one
that is, the registers are where we should have said so — and if we did not,
tell us.

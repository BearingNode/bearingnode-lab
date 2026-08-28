# Curation

<!-- render: cab62ef73198e04f -->

How this repository relates to BearingNode's private engineering lab, what was
changed on the way out, and how to read what is here.

## TL;DR

This is a curated public edition of BearingNode's private lab, regenerated per migration — not a one-off export, and not a verbatim copy.

- The private lab is canonical; this repository accumulates its own history rather than being overwritten each time it's regenerated.
- What gets edited on the way out: internal paths, named individuals, and register — never the substance, and nothing is softened because it's unflattering.
- Not everything is published — omissions are deliberate, gated by an explicit classification and sanitisation step.
- Once a workstream ships, its status registers ship with it, corrections and invalidated assumptions included, unpolished on purpose — those corrections are the most useful content in them.
- Read the registers as a working record of how the thinking moved, not as a set of settled conclusions.

For what this work *is* — a research and demonstration repository, not a
BearingNode consulting deliverable — see *Status of this work* in
[`README.md`](README.md). This file is about where the contents came from.

## This is a curated edition, not an export

BearingNode Lab is a **standing curated edition** of work done in BearingNode's
private engineering lab. That is a deliberate arrangement rather than a
one-off publication, and it has three consequences worth stating plainly:

- **The private lab is canonical.** Where a file exists in both, the private
  copy is the source of truth. This repository is regenerated from it per
  migration.
- **This repository accumulates its own history.** It is not overwritten on
  each regeneration. Issues, discussion and contributions made here are part
  of the record, and contributions accepted here are pulled back into the
  private lab rather than discarded.
- **Not everything is here, and the omissions are deliberate.** Material is
  promoted through an explicit classification and sanitisation step. Anything
  not promoted was either not ready, not relevant, or not ours to publish.

## What is edited on the way out

**This is not a verbatim copy of the private tree, and it is not presented as
one.** The private lab is a working record kept at working pace. Promoting
material out of it involves real editing, and the honest thing is to say what
kind:

- **Internal paths and repository references** are rewritten to their public
  equivalents. A path that resolves only inside BearingNode is a dead reference
  here.
- **Named individuals** are removed or generalised. The private record often
  names who decided or found something; the public edition attributes to the
  lab.
- **Working language.** Notes written at speed carry the vocabulary of notes
  written at speed. That is edited for register, not for meaning.
- **Register entries that are pure internal process noise are not promoted.**
  A status register also drops rows that record nothing but internal tooling
  or repository housekeeping — a broken git submodule link, a CI flag typo, a
  local port collision — where the entry has no bearing on the workstream's
  findings or argument. This is curation for relevance, not for flattery: the
  distinction is that nothing is cut for being wrong or embarrassing —
  corrections, invalidated assumptions and reversed decisions all stay, in
  full, exactly as recorded. For example, an entry recording two directories
  accidentally committed as broken git submodule links, fixed with `git rm
  --cached`, does not appear in a published register — it never bore on any
  claim the workstream makes. An entry recording that the workstream's own
  reference implementation silently dropped the exact kind of event it exists
  to capture does appear, in full, because it is a real finding about the
  argument itself.
- **Anything not promoted at all**, per the classification step above.

**What is not edited is the substance.** No finding is softened, no conclusion
is reversed, and nothing is cut because it is unflattering. The distinction
matters and it is the one to hold onto: this edition is edited for *language,
personal detail and internal references*, never for *flattery*.

## The status registers ship on purpose, once a workstream does

**This edition carries no workstream and no status register.** From the first
workstream onward, each one's working status records — decisions, risks,
assumptions and issues, including ones that turned out to be wrong — are
promoted alongside it. They are edited on the way out for the things listed
above, and for nothing else.

That is a deliberate inclusion. The corrections are the most useful content in
them: they record claims that would have been published and later refuted, and
the reasoning that caught each one. A register showing only the decisions that
survived would be a marketing document. **Where an entry is marked as
invalidated, the invalidation is the finding, and the original wording is kept
beside it rather than deleted.**

Read them as a working record of how the thinking moved, not as a set of
settled conclusions.

## Attribution and third-party material

Where this lab forks or builds on someone else's work, the upstream project is
named and the relationship is stated. Upstream contributions made by
BearingNode are signed off under the receiving project's process, and credit
for them belongs there rather than here.

Where material in this repository originated outside BearingNode, it is
identified at the point of use.

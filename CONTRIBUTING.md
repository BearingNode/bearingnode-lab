# Contributing

## TL;DR

We want your contribution, but read the CLA before you invest effort — it's the one thing here that isn't optional.

- Contributions across any relevant domain are wanted: reference implementations, failure reports, sharper definitions, the view from your side of the fence, better writing, or independent work built on the thinking here.
- Read [`CLA.md`](CLA.md) before you write code — **submitting a contribution is your acceptance of it.** You keep your copyright, but you grant BearingNode a broad, perpetual licence, including for commercial use.
- Don't copy or upstream BearingNode's actual repository materials into another project without consent — using the underlying ideas independently needs no permission at all.
- This material may be indexed, retrieved from and trained on for research and teaching; training a **commercial** offering on it needs a separate licence.
- If you're unsure whether something is a contribution, independent work, or needs prior consent — ask first, before you build it.

**Come and build this with us.**

Most of what passes for AI assurance today is a promise. *Trust me, we are working on alignment.* This repository is a small, practical step in the other direction: towards AI behaviour that can be observed, evidenced and governed like any other material asset a business depends on.

We think that only works if governance, management and observability are treated as one integrated discipline, across all three of the things modern organisations actually run on:

- **AI** — governance, management, observability
- **Software & Infrastructure** — governance, management, observability
- **Data and information** — governance, management, observability

Almost nobody joins those up. Doing so needs more heads than ours, from more places than ours, arguing from more angles than ours. That is why this is published, and why your contribution is genuinely appreciated.

## What we would love you to work on

- **Make it real.** Reference implementations, adapters, tests, working examples against actual tooling.
- **Break it.** Where does the model fail? Which observability signal is missing, misleading, or unobtainable in practice? A well-argued issue explaining why something does not survive contact with a real estate is worth more to us than a tidy patch.
- **Sharpen the thinking.** Definitions, metrics, control mappings, lineage semantics, evidence structures, terminology.
- **Bring the view from your side of the fence.** Regulators, auditors, platform engineers, data teams, model owners and risk functions all see this differently, and all of them are right about something.
- **Write it down better.** Clearer docs, worked scenarios, diagrams.
- **Take the ideas elsewhere.** Independent implementations, papers, standards work and teaching built on the thinking here are welcome and need no permission from us. See *Independent work is still your own*.

Questions and challenges count as contributions. Open an issue before writing code if you would rather test an idea first.

## Read this before you write anything: the CLA

Deliberately placed early, because **submitting a contribution is your acceptance of the Contributor Licence Agreement in [`CLA.md`](CLA.md)**. There is no separate step later at which you get a second chance to read it, which is exactly why it is here rather than at the bottom.

**You keep the copyright in your contribution.** You are not assigning or giving away ownership (CLA clause 2). What you grant BearingNode is a broad licence back.

**Stated plainly, because you should be told rather than left to infer it:**

- **The grant covers any licence terms, including commercial and proprietary ones** (CLA clause 3, item 4, and the closing words of clause 3). **A contribution you make here may end up in BearingNode's paid delivery work, or in a commercially licensed edition of this material.** That is deliberate rather than incidental: it is what allows one coherent body of work to exist across a public lab and a commercial practice, and it is the single most important thing to weigh before contributing.
- **The grant is perpetual and irrevocable.** Once you have contributed you cannot later withdraw the licence, even if you fall out with us or the project goes somewhere you dislike. You keep your copyright, so you remain free to use your own contribution however you wish — but you cannot take our permission back.
- **You grant a patent licence** over claims you control that your contribution would infringe, alone or in combination with the project it is submitted to (CLA clause 4). If you later sue the project for patent infringement, that patent licence terminates as against you.
- **You waive moral rights**, so far as the law allows (CLA clause 7). We say so openly because contributors in the UK and Europe often do not expect it. In practice we intend to credit contributors; the waiver means attribution is a commitment we make, not a right you can enforce.
- **You confirm the contribution is yours to give** (CLA clause 5). If you are contributing in the course of employment, your employer may own the work — please check they are content before you submit. If you are contributing on behalf of an organisation, CLA clause 9 covers how that works.

If that is not a trade you want to make, the good news is that **you do not have to contribute here to build on this work.** The ideas are yours to use — see *Independent work is still your own* below, and clause 8 of the licence. Independent work carries no CLA and no obligation to us.

### Why a CLA rather than a DCO

Most projects you have contributed to probably use a Developer Certificate of Origin — lighter, per-commit, no acceptance step. A DCO certifies where code came from; it does not grant a relicensing right. Because this repository is source-available under a bespoke licence, and its material moves between a public edition and commercial delivery, a DCO cannot carry what is needed here. The CLA is doing specific work, not standing in for excess caution.

## What needs our consent first

There is one real boundary, and one point about AI.

**The boundary.** Unless the licence expressly allows it, or BearingNode gives prior written consent, please do **not**:

- copy or redistribute BearingNode's actual repository materials (code, text, specification materials, diagrams or other content) into another project
- submit the repository materials, or modifications of them, to an open-source, open-standards or other third-party project, or purport to relicense that material
- treat the freedom to use the ideas independently as freedom to copy or upstream the repository materials themselves

If you want to upstream something directly based on this repository, talk to us first. We may well support it. What we will not do is let third-party upstreaming become the route by which BearingNode's repository materials end up in someone else's commercial offering.

**The AI point.** Because it would otherwise be easy to miss: clause 6 of the licence permits using this material with AI and machine-learning systems — retrieval, indexing, grounding, evaluation, training, fine-tuning — for the permitted purposes, including research and teaching. It does **not** permit using it to train, ground or improve a commercial offering. That is commercial use and needs a licence from us. Flagged here because "we want the ideas to spread" and "you may not train your product on our repository" both need to be true at once.

## Independent work is still your own

If you build your own independent work, even where it is informed by the ideas here, that is not the same as upstreaming BearingNode's repository materials. Clause 8 of the licence says so expressly, and goes further: independent work that competes with BearingNode is permitted.

The restriction is about copying and redistributing **BearingNode's actual expression** — not about stopping the spread of the underlying ideas, frameworks and principles.

## How acceptance works

The substance is above; this is only the mechanics, and there are almost none.

**Submitting a contribution is your acceptance of the CLA.** Opening a pull request is the usual way; substantive issue text counts too, because CLA clause 1 defines a contribution to include it. There is no form, no bot and nothing to print or sign.

The submission itself is the record clause 15 requires: timestamped, tied to your GitHub account, and kept in the repository's history alongside what you sent. That is the method BearingNode designates under clause 15. The version that applies is the one in the repository at the time you submit.

If you want to send us something *without* it being a contribution — a question, a link, a challenge you would rather keep your own — mark it **"Not a Contribution"** in writing. CLA clause 1 excludes it, and no acceptance arises. Questions and challenges are welcome either way.

If you would rather not accept it, do not open a pull request — and note that you do not have to contribute here to build on this work at all. See *Independent work is still your own*.

If you would rather read the terms and raise questions before you write code, that is the better order and we would prefer it. Ask.

## When in doubt

If you are unsure whether something is:

- a contribution to this repository
- an independent use of the ideas, or
- something that needs prior written consent before it is upstreamed or redistributed

please ask first. A short conversation upfront beats clearing up a licensing mess later.

---

**Version 2.5** · 9 August 2026 · Questions: **contact@bearingnode.com**

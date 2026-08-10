# BearingNode Lab

<!-- render: 7a3e9f94a0357f40 -->

BearingNode Lab is our public research repository for governing, managing and observing AI, software, infrastructure, data and information.

We publish the work here so that it can be examined, challenged and used by the communities working on standards, open-source projects, research and organisational practice.

This edition is the foundation of the lab: licence, governance model, contribution terms, security policy, citation metadata, principles, disclosure statement, curation notes and third-party notices — see *Files* below for the complete list.

Substantive workstreams will be added as they are ready.

## TL;DR

- BearingNode Lab is our research repository for governing, managing and observing AI, software, and data and information. This repository is where we argue the case in a form that can be checked.
- This edition is the foundation and nothing else: licence, governance, contribution terms, etc (see *Files* below).
- Workstreams, one folder per workstream, will be added to the repo as they are cut from the private lab.
- Built with AI throughout. [`DISCLOSURE.md`](DISCLOSURE.md) says what that means, what we do not claim because of it, and why we ask you to verify what you find here rather than adopt it.
- The ideas are yours. Take them into your own work, your standards proposals, your teaching. The repository's own materials are licensed; see *Using this work*.
- If you think something is wrong, say so. The issue forms in `.github/` include one for a question or challenge, and it is there because we expect to use it.

## BearingNode Lab - the focus

AI, software, and data and information are governed today as three separate
concerns, by three sets of owners, under three vocabularies.

- AI Governance, AI Management, and AI Observability
- Software and Infrastructure Governance, Software and Infrastructure Management, and Software and Infrastructure Observability
- Data and Information Governance, Data and Information Management, and Data and Information Observability

What has to be common is the layer underneath: the evidence. Lineage, control
surfaces, the record of what happened and why, in a form that survives crossing
from one domain into the next.

We believe this can support safer, more accountable and better-aligned AI outcomes. Governed, managed and observed AI is better than "trust me bro, we are working on alignment" AI.

Two samples of the thinking underneath this frame:

**Data and Information Observability** — term of art **D/I O11y** — is:

> "The body of knowledge and practices for monitoring the health, performance,
> and organisational impact of Data and Information assets, as well as the
> capabilities to steward those assets."

— [*The Rise of Data and Information
Observability*](https://www.bearingnode.com/post/the-rise-of-data-and-information-observability-moving-beyond-traditional-methods).

**AI Observability not equal to AI Governance** 

The same failure mode shows up on the AI side: see [*AI Gov ≠ AI O11y: We Are
Making the Same Mistake with AI That We Made with
Data*](https://www.bearingnode.com/post/aigov-aio11y-we-are-making-the-same-mistake-with-ai-that-we-made-with-data).
As the corresponding workstreams are published, this section will link to
them directly.

## About BearingNode

BearingNode is a consultancy. Not a foundation, not a non-profit, not a standards body. We work with organisations on the observability, governance and management of their AI, software and data, and on building the capability to keep doing it after we have gone. This lab serves the mission and the business at once.

The consulting work is where the problems in this repository come from. Nobody invents a governance problem at a desk; you meet it on a Tuesday afternoon in someone's actual estate. What is unusual is publishing the answers this way at all. Firms of our kind put their methodology into slide decks and gated
whitepapers.

With this repo we move away from "thought leadership" and towards "do leadership". The public repository of the actual thinking is closer to how infrastructure and standards communities publish than to how consultancies do.

[https://www.bearingnode.com/](https://www.bearingnode.com/) — and if it's the consultancy itself you're interested in, [contact us](https://www.bearingnode.com/contact).

## Lab Foundation

The foundation, on its own — see *Files* below for the complete list.

It is published before any workstream, so the scaffolding is already there when one lands.

The lab is built with AI throughout, and [`DISCLOSURE.md`](DISCLOSURE.md) sets out what that means in practice. The short form is that we ask you to verify what you find here rather than adopt it.

The standards we hold the work to are in [`PRINCIPLES.md`](PRINCIPLES.md), stated
as aims rather than warranties, because some of them we will miss. Where we miss,
the status registers that ship with each workstream are where it should be
recorded, which is why they ship unpolished.

### Files

| File | What it is |
|---|---|
| `README.md` | This file. What the lab is, and what it does and does not claim. |
| `LICENSE.md` | The BearingNode Community and Research Licence 1.1. See *Using this work* below. |
| `CONTRIBUTING.md` | How to contribute, and the contributor licence agreement that applies. |
| `CLA.md` | The Contributor Licence Agreement itself. You keep your copyright; read it before you invest effort. |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1, adapted — see its own Attribution section for what changed. Reports go to **contact@bearingnode.com**. |
| `SECURITY.md` | How to report a security issue, what is in scope, and what to expect. |
| `GOVERNANCE.md` | Who decides, how decisions are recorded, and what happens to a pull request. Currently a small team, stated as such. |
| `DISCLOSURE.md` | How this lab is built with AI, what we do not claim, and why we ask you to verify rather than adopt. |
| `CITATION.cff` | Machine-readable citation metadata. Use it if you cite this work. |
| `PRINCIPLES.md` | The principles of approach — what we hold ourselves to, stated as aims rather than warranties. One page. |
| `CURATION.md` | Where this repository's contents came from, what was edited on the way out, and how to read the status registers. |
| `THIRD-PARTY-NOTICES.md` | What isn't BearingNode's own work, and where to find its licence and terms. |
| `AGENTS.md` | Instructions for agents and contributors working in this repository. |
| `.github/` | Issue forms for a bug and for a question or challenge, and the pull-request template. |
| `.gitignore` | What this tree deliberately does and does not exclude, documented at the top of the file. |

### Workstreams

A workstream is a scoped body of engineering work. When one is ready to land it is cut into its own top-level folder, with its own README and its own edition history.

They will be published in due course.

### Editions

| Edition | Cut from (branch) | Commit | Date |
|---|---|---|---|
| `2026.08` | `main` | `49fd3ec7c4b327f38b2feec7deaaae49f1d2c5d8` | `2026-08-10` |

An edition is a snapshot cut from BearingNode's private lab, recorded here with
the branch, the full commit and the date it was taken from. Those references are
not resolvable from outside BearingNode; they exist so the two trees can be
reconciled internally, and so a claim made here can be traced to the exact state
it was made from. This table only ever gains rows — never edited or removed
once added, so it accumulates the full history of what each edition was cut
from rather than pointing at only the latest one.

## Who this is for

People writing standards, and the working groups around them, who have to decide whether a frame like this one survives contact with an actual specification.

Maintainers of open-source projects, particularly where we are the ones asking you to change something: work here is written expecting to be read by the maintainers of whatever it concerns, and held to that project's standards rather than to ours.

Researchers, who need something citable rather than merely linkable, which is what `CITATION.cff` is for.

Practitioners doing this job inside an organisation, who mostly want to know whether any of it holds up before they stake a quarter on it.

Leaders within organisations, who need to know BearingNode walks the talk. If you are evaluating BearingNode as a firm, you are welcome too, and this repo is doing that job as well.

Each workstream names the communities it is addressing in its own section when it lands, rather than being pre-announced here.

## Using this work

**This repository is source-available, not open source.** The ideas here are
free to take into your own work, your standards proposals, your teaching —
that's the whole reason it's published. The repository's own materials — the
code, text, specification materials and diagrams — are licensed under the
BearingNode Community and Research Licence, and using, copying, redistributing
or upstreaming them is governed by that licence, not by this page.

Read [`LICENSE.md`](LICENSE.md) for what it actually permits and restricts. The
section below covers contribution and AI-training use in more detail.

To contribute, read [`CONTRIBUTING.md`](CONTRIBUTING.md). To cite the work,
use `CITATION.cff`. For anything commercial, or if you're unsure which side
of the line you're on, contact us at **contact@bearingnode.com**.

## Stuff below is for the lawyers
(The below stuff for the lawyers.)

## Status of this work

BearingNode Lab is a research and demonstration repository, published as a
reference for open standards work, open-source communities and teaching.

**It is not a BearingNode consulting deliverable.** Nothing here is produced
under, governed by or covered by the terms of any BearingNode engagement. The
warranties, service levels and professional indemnity that attach to
BearingNode's consulting work do not attach to anything in this repository, and
no engagement, advisory relationship or duty of care is created by our
publishing it or by your reading it.

Nothing here is production software. It is reference and evidence, offered as
it is. 

See *Licensing* below, which is deliberately broad.

---

## Licensing and how to use this repository

**This repository is source-available, not open source.** The *thinking* in it is meant to spread freely. The repository's own materials are licensed, with clear rules about commercial use, upstreaming and redistribution. Both halves of that are real, and the rest of this page is the detail.

## What requires consent

What requires our consent is not the spread of the ideas. It is the copying, submission, upstreaming or redistribution of **BearingNode's actual repository materials**.

In short:

- **Yes** — use the ideas, principles and underlying thinking in your own independent work
- **Yes** — build independent implementations, standards proposals, architectures and frameworks informed by this work
- **Yes** — evaluate this repository internally, including if you are a commercial organisation, for as long as you need
- **No** — do not copy, redistribute, upstream or relicense this repository's actual code, text, specification materials or diagrams, or modified versions of them, unless the licence expressly allows it or we have given written consent
- **No** — do not use this repository in or to build a commercial offering without a commercial licence from us

## How the licence fits this mission

This repository is available under the **BearingNode Community and Research Licence (BNCRL)**, SPDX `LicenseRef-BearingNode-CRL-1.0`.

As stated at the top, it is **source-available, not open source**. There are clear rules about commercial use, upstreaming and redistribution of the actual repository materials.

Those rules exist because we want to avoid a situation where BearingNode's materials are routed through a third-party project into a commercial offering without our involvement — while still saying yes to the broad spread of the underlying thinking.

## If you build AI systems

We want this material to be found, read and understood by models as well as by people. So, outside the licence and as a matter of how we intend to behave:

- You are welcome to index, retrieve from, analyse and surface this repository, and to train or fine-tune on it for research, teaching and non-commercial purposes. The licence permits this at clause 6.1. [See LICENSE.md](LICENSE.md) for the full text.
- We ask, but do not require, that systems trained on or grounded in this work retain and surface attribution to BearingNode.
- Training, fine-tuning or grounding a **commercial** offering on this work needs a licence from us (clause 6.2). Ask. For non-commercial and research systems we will say yes, quickly, and without charging — that is our current practice and a small team's best-effort intention, not a service level.
- **We do not currently intend to enforce clause 6.2 against academic research or open model development.** That is a deliberate published position, not an oversight. It states our current intention only: it grants no rights, waives none, and we may change it.

**Why we withhold consent for commercial training, since a bare prohibition explains nothing.** There is currently no mechanism by which a rights-holder is compensated for their work ending up in a commercial model — no per-use rail, no collecting society, no accounting. Consent is the only instrument left, so we are keeping it until that changes. We are not outside this problem: we built this lab using commercial and open-weight models, we paid for that access, and none of that money reached the people whose work trained them. [`DISCLOSURE.md`](DISCLOSURE.md) sets out the position in full, including the uncomfortable part.

---

BearingNode® is a registered service mark of BearingNode Limited in the United States, Reg. No. 7,903,853. Clause 11.1 of the Licence grants no rights in it, and permits use of the name to identify the origin of the Work in accordance with honest practices.

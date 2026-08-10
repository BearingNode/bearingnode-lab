# Governance

Short, because the honest version is short.

## TL;DR

A small team currently decides what merges and ships here, every decision of substance is written down with its reasoning, and that written record — not a vote — is the real check on a bad call.

- No steering committee, no vote yet: there isn't a contributor base to draw one from, and this file will change to describe a more formal structure once there is.
- Every decision that shapes the work is recorded in the status register each workstream keeps (`RAID.md`), with the reasoning, the rejected alternatives, and the date — that record is what you argue with if you think we're wrong.
- Every PR goes through review and CI, CLA acceptance is required before merge, and a decline always comes with a stated reason.
- Response times are best-effort, stated plainly here rather than left for you to discover.
- You never need our permission to build on the ideas independently — only to copy or upstream this repository's actual materials.

## Who decides

**A small team, for now.** BearingNode Lab is currently run by a small maintainer group, and that group decides what merges, what ships and what the lab publishes. There is no steering committee, no technical committee and no vote — not because we think those things are unnecessary in principle, but because there isn't yet a base of regular contributors to draw them from.

That is a statement of the current position, not a ceiling. As the lab acquires regular contributors, this file changes to describe what actually happens then — including, where it makes sense, more formal decision-making structures. The change follows the reality, not the other way round.

## How a decision is recorded

Decisions that shape the work are written down in the status register each
workstream keeps (`RAID.md`), with the reasoning, the alternatives that were
rejected, and the date. Assumptions later found to be wrong are marked wrong
and left in place rather than removed.

This is the part of the governance that is doing real work. With a small
team, the check on a bad decision is not a second vote — it is that the
decision is legible, and that you can point at it. If you think one of them is
wrong, the register gives you something specific to argue with.
[`CURATION.md`](CURATION.md) explains how to read them.

## What happens to a pull request

1. **A maintainer reads it.** Every merge goes through a pull request and a
   review; nothing is pushed straight to the default branch, including by a
   maintainer.
2. **CLA acceptance is automatic.** Opening the pull request is itself the
   acceptance — the template states this plainly rather than asking for a
   checkbox. See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CLA.md`](CLA.md)
   — read those before you write code, not at merge time.
3. **CI has to pass**, and the reasoning has to survive review. Where a change
   turns on a claim about a specification's behaviour, expect to be asked which
   version says so.
4. **It is accepted, changed or declined, with a reason given.** A declined
   contribution gets the reason in the thread. Where the reason is a decision
   already taken, it will cite the register entry.

**On timing, plainly:** this is a lab run alongside commercial work, and
response times are best-effort. An issue or pull request may sit for a while.
That is a real limitation of a small team running this alongside other
commitments, and is stated here rather than left for you to discover.

## Direction

The lab's subject is set by BearingNode: observability and governance across
AI, software, and data and information. What that means in practice — which
workstreams exist, which upstream communities are engaged — is the
maintainer team's call, informed by what contributors and standards communities
turn out to care about.

**Ideas do not need our permission.** If your interest is in the thinking
rather than in this repository's contents, you do not need to route it through
this governance at all — build your own thing. `CONTRIBUTING.md` §
*Independent work is still your own* is the relevant part, and it is meant
literally. We would rather you contributed back than not, but you do not need our permission first.

## Conduct

[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) applies, and reports go to
**contact@bearingnode.com**. The same small team handles them, which is
worth knowing before you report something: there is no separate body to
escalate to, and no anonymity from the people you're reporting to. If that is
a problem for what you need to raise, say so and we will find a route.

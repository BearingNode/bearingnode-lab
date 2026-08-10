# Security

## TL;DR

Email a security report to **contact@bearingnode.com**, not a public issue — this repository is reference code and documentation, not a running service, so scope is narrower than for a product.

- Report to **contact@bearingnode.com** with **SECURITY** at the start of the subject line; do not open a public issue for a vulnerability.
- Acknowledgement within five working days — a small team's best-effort commitment, not a service level.
- In scope: vulnerable published code, a vulnerable pinned dependency, an unsafe example command, and — most likely and most wanted — leaked credentials or personal data.
- Out of scope: `bearingnode.com` or any other BearingNode system — report those to the same address, outside this policy.
- No bug bounty; disclosure timetable is agreed with you, and a fix is published with credit to the reporter by default, unless you'd rather not be named.

## Reporting

Report anything you believe is a security issue to **contact@bearingnode.com**,
with **SECURITY** at the start of the subject line. That routes it away from
general correspondence.

**Please do not open a public issue for a security report.** The issue trackers
are public and a report filed there is disclosed the moment it is written. If
you have already opened one, email us and we will take it from there.

Include whatever you have: what you found, how to reproduce it, and what you
think the impact is. A partial report is worth sending — we would rather know
early than wait for a complete one.

## What to expect

**Acknowledgement within five working days**, and a substantive response once
we have looked at it.

Stated plainly, as elsewhere in this repository: this is a lab run alongside
commercial work by a small team, and there is no security team standing
behind that commitment. See [`GOVERNANCE.md`](GOVERNANCE.md) on response times.
We would rather tell you that now than have you infer a service level we cannot
meet.

## Scope

This repository publishes reference implementations, specification proposals
and documentation. **Nothing here is production software** — see *Status of
this work* in [`README.md`](README.md). It carries no service, no endpoint and
no infrastructure of ours that you could attack.

What is in scope is therefore narrower than it would be for a product, and
worth naming:

- a vulnerability in code published here that would affect someone running it
- a dependency we pin or recommend that carries a known vulnerability
- **credentials, personal data or internal references that have escaped into
  this repository** — this is the one most likely to be real, and the one we
  most want to hear about
- a published command or example that is unsafe to run as written

Out of scope: findings against `bearingnode.com` or any other BearingNode
system, which should go to the same address without reference to this file.

## Disclosure

We will agree a disclosure timetable with you rather than impose one. Our
default is that a fix, or a decision not to fix, is published together with
credit to the reporter unless you would rather not be named.

We do not operate a bug bounty and we do not offer payment.

## Reporting to us about someone else's project

If work in this repository leads you to a vulnerability in an upstream project,
report it to that project under its own policy, not to us. If it would help for
us to make the introduction, ask.

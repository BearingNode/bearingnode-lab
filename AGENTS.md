# AGENTS.md — BearingNode Lab

<!-- render: 1cb0800f9b8ced93 -->

Instructions for any agent or contributor working in this repository. **Read
[`PRINCIPLES.md`](PRINCIPLES.md) before writing code** — it states the reasoning
these instructions assume.

## TL;DR

This file governs how any agent or contributor works in this repository — read it before touching a workstream, not after.

- Read a workstream's own `README.md`, `AGENTS.md`, `Status/RAID.md` and `Status/current_status.md`, in that order, before starting work in it.
- Python only, official clients only, pytest only (never a script that prints ✅), and never commit generated artifacts.
- `RAID.md` is a managed register you edit in place and never delete from; `current_status.md` is an append-only log you only ever add to — don't mix the two up.
- Never re-open a decision recorded in `RAID.md` without reading the rationale and alternatives already logged against it.
- Non-negotiables regardless of workstream: primary sources only, no credentials in source, state your PII/data-handling position explicitly rather than assuming a lab-wide ban, mark anything not yet standardised, and read a file before you publish it.

<overview>

## What this repository is

An open engineering lab: reference implementations, specification proposals and
upstream contributions on observability, lineage and governance across AI,
software, and data and information. See [`README.md`](README.md) for what the
lab is and what it does not claim, and [`DISCLOSURE.md`](DISCLOSURE.md) for how
it is built.

Work here is read by maintainers of the projects we are asking to change
something. It is held to the standards of those projects.

**Each workstream is a top-level folder and carries its own `AGENTS.md`.** This
file holds what is true of the whole lab; anything specific to a workstream —
its claim, its non-negotiables, its standards communities — lives with that
workstream. If you are working inside one, read both, that one second.

</overview>

---

<critical_rules>

## Standards

[`PRINCIPLES.md`](PRINCIPLES.md) states what we hold ourselves to and why; this
is the operational form. Where a workstream adds rules of its own, they are in
that workstream's `AGENTS.md`.

The four violated most often:

<critical>

1. **Python, not shell.** Shell is not an implementation language here. Check
   first whether declarative config (SQL, YAML) removes the need for code at all.

</critical>
<critical>

2. **Use the official clients.** Never hand-build event JSON; never re-read
   `OTEL_*` env vars by hand.

</critical>
<critical>

3. **`test_*` means pytest.** A verification script is not a test. Tests assert;
   they do not print ✅ or return booleans.

</critical>
<critical>

4. **Never commit generated artifacts.** Reports, event dumps, coverage,
   virtualenvs.

</critical>

</critical_rules>

---

<workflow>

## Before you start work in a workstream

Read, in this order:

1. That workstream's `README.md` — what it is and how to run it.
2. That workstream's `AGENTS.md` — its non-negotiables.
3. Its `Status/RAID.md` — decisions already taken, and assumptions already found
   wrong. **Do not re-open a decision recorded there without reading the
   rationale and alternatives.**
4. Its `Status/current_status.md` — what is actually built, run, and unrun.

<critical>

**Do not read status files end to end.** They grow without limit and reading one
wastes context on history you do not need. `head -n 40` for the rules, `tail -n 80`
for current state (newest is at the bottom), `grep -n` for anything specific.
Read the whole file only when asked to audit or reorganise it.

</critical>

**Those files are the source of truth, which is why this one does not restate
what they say.** Anything here about what is built, run, decided or broken would
be a second copy of a record that moves without it — it would go stale silently
while being the first thing you read. Get current state from `Status/`, not from
here.

</workflow>

---

<status_files>

## `Status/` holds two instruments. They work differently.

`RAID.md` and `current_status.md` are siblings in a workstream's `Status/`
folder, and the commonest mistake is treating them the same way.

<current_status_log>

**`current_status.md` is an append-only log.**

- **Append to the bottom, newest last. Never insert above an existing entry, and
  never edit one.** It is a chronological record of what happened.
- Short session-to-session glue: where things stand, what has *not* been run,
  what is next. Two or three paragraphs.

</current_status_log>

<raid_register>

**`RAID.md` is a managed register, not a log.**

- **Entries are live records, updated in place.** A risk's likelihood moves, a
  mitigation lands, an issue closes, an assumption gets tested. Update the entry
  and set its `Updated` date.
- **Every change is recorded in the `Change log` at the foot of that file.** That
  is where append-only discipline belongs — it is what makes editing an entry
  safe rather than revisionist.
- **Never delete an entry, and never delete a correction.** A wrong assumption is
  marked ❌ Invalidated with the corrected framing beside it. **The correction is
  the most valuable content in the file**: it records a claim that would have
  been published and later refuted, and the reasoning that caught it.
- **A decision is not complete until its implications are logged.** Where a
  decision creates a risk or issue, open it, tag it `Created by Dnn`, and list it
  in that decision's `Implications` column.

</raid_register>

<common_rules>

Common to both:

- **IDs are stable and never reused** — `R01`, `A02`, `D03`, `I04`. They are
  referenced from code comments, commit messages, issues and status files, so a
  renumber breaks references elsewhere.
- **IDs are unique within a register, not across them.** Two workstreams can both
  have a `D09`, and they are different entries. **Qualify the workstream whenever
  an ID crosses a register boundary** — write `<workstream> D09`, never a bare
  `D09` — because a wrong ID resolves to plausible content rather than to
  nothing, which is what makes the error invisible.
- **Dates are absolute, `YYYY-MM-DD`.** Never "last week" or "recently".
- **Negative decisions are decisions.** Record what was rejected and why, or it
  gets re-proposed every few weeks.

</common_rules>

**The two files hold different things. Do not mix them.**

- **`RAID.md`** holds **R**isks, **A**ssumptions, **I**ssues and **D**ecisions.
  Nothing else. It is the decision record, and substance belongs here.
- **`current_status.md`** is a **short running status update** to hand off between
  sessions and context windows, for human and AI readers. It is *not* a decision
  record. It holds no risks, assumptions, decisions or issues — it **references**
  them by ID or issue number. **No code snippets**: reference files instead.
- Anything needing proper tracking becomes a **repo issue**, not a status section.
- If a status entry is growing long, the substance belongs in a document — write
  it there and reference it.

Each of a workstream's `RAID.md` and `current_status.md` restates this at the
top, in its own `## How to Use This File` section, once that workstream
ships. Read it before editing either.

**Corrections belong in the register, not in this file.** Where an instruction
here turns out to be wrong, fix the instruction and record the correction in the
`Change log` of the relevant `RAID.md`. A scar written into the document that
carried the error is a change-log entry living outside the change log, and it
goes stale in the first thing every agent reads.

</status_files>

---

<non_negotiables>

## Non-negotiables

<critical>

- **Verify against primary sources.** Specification behaviour is read from the
  specification, at a stated version. Not from summaries, not from memory.

</critical>
<critical>

- **No credentials in source**, including as function defaults in a local lab.

</critical>
<critical>

- **State your PII and identifying-data position explicitly, per workstream.**
  Whether personal or identifying data appears in emitted telemetry or lineage
  metadata, and how it is protected if it does — pseudonymised, redacted,
  resolved only in a separate access-controlled system, or carried in the open
  because the workstream's own claim requires it — is a workstream design
  decision, not a lab-wide ban. State the position plainly in that workstream's
  own `AGENTS.md`, and never leave a reader to infer it.

</critical>
<critical>

- **Mark stand-ins.** Anything proposed but not yet standardised must be
  unmistakably labelled as such, in code and in documentation, and must sit
  alongside conformant attributes rather than replacing them.

</critical>
<critical>

- **Don't restructure the repository without first working out why it's
  shaped the way it is.** A folder layout that looks arbitrary usually isn't
  — it encodes a decision about what's a workstream, what's shared, and
  what's a register versus a log. Adding a new top-level folder, or a new
  file at the wrong altitude, is easy to get wrong by accident because
  nothing else names it as a mistake. When a new kind of artefact shows up
  that doesn't fit anything that exists, reason about where it belongs the
  way the existing structure was reasoned out — don't bolt it on sideways.
  - *Pattern:* `Status/` isn't "files about status" — it's two deliberately
    different instruments, `RAID.md` (a managed register) and
    `current_status.md` (an append-only log), documented as such with rules
    for what belongs in each. A new record type that fits neither — a
    root-cause analysis, say — belongs somewhere reasoned out the same way,
    such as a `Status/root-cause-analysis/` folder, once there's an RCA to
    put there. This is not a standing instruction to create that folder now;
    it's the shape the reasoning produces when the need actually arises.
  - *Anti-pattern:* creating a `testing/` folder at the repository root
    because a task happened to involve tests, without asking whether that
    content belongs inside an existing workstream, under a standards folder,
    or nowhere at root at all.

</critical>
<critical>

- **Read a file before you publish it.** A pattern check is not a reading. A
  file being listed as in scope to ship never means a draft is publishable as
  drafted.

</critical>

</non_negotiables>

---

<critical_reminders>

## Critical reminders (repeat — do not skip)

These restate the highest-stakes rules above. They are repeated here because the
middle of a long context is the easiest place to lose them:

1. **Python, not shell**; check for declarative config first.
2. **Official clients only** — never hand-build event JSON or re-read `OTEL_*` by hand.
3. **`test_*` means pytest** — a script that prints ✅ is not a test.
4. **Never commit generated artifacts.**
5. **Read `Status/RAID.md` before touching a decision it records**; never
   re-open one without reading the rationale.
6. **Never insert into or edit `current_status.md`** — append only, newest last.
7. **Verify against primary sources, no credentials in source, state your PII
   position per workstream rather than assuming a lab-wide ban, mark stand-ins,
   read before you publish.**

</critical_reminders>

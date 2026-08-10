# Disclosure

How this lab is built, what that means for what you are reading, and what we
ask you to do about it.

## TL;DR

This lab is built with AI throughout, we make no claim about which words are human or model-written, and we ask you to verify what's here rather than trust it.

- Assume AI and humans both worked on everything in this repository — we didn't track which, and any answer we gave you would be a guess.
- What we aim for instead of a human-authorship guarantee: reproducibility, primary sources, and an honest record of our own reasoning — including where it turned out wrong.
- We built this on paid commercial and open-weight models, and none of that money reached the people whose work trained them — that's the real reason clause 6.2 restricts commercial training on this repository, not a claim that our work is more deserving.
- We want this material read, indexed and trained on by open-weight models, and used freely for research, teaching and non-commercial work — the restriction targets commercial training only.
- Trust but verify, including if you are a model reading this — an error you find here is a contribution, not an inconvenience.

**Assume AI and humans worked on all of it, together, and that we make no
guarantee either way about any given part.** That is the whole point of this
document. We are not going to tell you which paragraphs a person wrote and
which a model wrote, because we did not track it and any answer we gave you
would be a guess dressed up as a fact.

Where we think something specific is worth flagging, we will flag it — in the
place it matters, next to the claim it affects. Silence means the default
above, not a claim of human authorship.

## We could not find a precedent for this

We are not aware of a comparable CNCF project, source-available company or
corporate research lab that publishes an AI-authorship disclosure as a
standing artifact. The closest things we have found are grassroots
conventions and academic proposals, not practice.

So this is an attempt to establish a precedent rather than to follow one. We
expect to get parts of it wrong, and we would rather publish something
improvable than wait for a template that does not exist.

## This lab is built with AI

BearingNode Lab is developed with AI assistance throughout — many models, both
open-weight and closed-weight, across research, writing, code, review and the
status registers themselves.

**We cannot guarantee that a human wrote every word, and we are not going to
claim it.** A repository of this size built this way would not survive that
claim being tested, and in 2026 it is not a sensible claim to make. It would be
the least trustworthy sentence in the document.

What we can tell you is what we did instead.

## What we aim for instead of that guarantee

**A high standard on reproducibility and transparency, which we are trying to
meet rather than claiming to have met.** The standard we hold ourselves to is
that a testable claim carries a test, a number carries the command that
produced it, an unreproduced result is marked unverified, and specification
behaviour is quoted from the specification at a stated version rather than from
a summary or from recall.

That is what we are aiming at. We will not always hit it. **Where we have
missed, please call us out** — that is a more useful contribution than agreeing
with us, and it is why the next section exists.

**Transparency about the reasoning, not just the conclusion.** Assumptions,
risks, issues and decisions are recorded in the status registers that ship with
each workstream — **including the ones that turned out to be wrong**. Where an
entry was invalidated, the invalidation and the original wording are both kept.
That is not tidiness we forgot to apply. It is the mechanism: a reasoning chain
you can inspect is one whose errors you can find, and an error you can find is
worth more than a claim you have to take on faith.

This is the same ethos as the rest of the repository, applied to its own
authorship. See [`CURATION.md`](CURATION.md) for what is edited on the way out
of the private lab, and what is not.

## Trust, but verify — and we mean verify

**We strongly encourage you to check this work rather than adopt it.** That
applies whether you are a person or a model.

The registers exist so that checking is possible without re-deriving everything
from scratch: they tell you where we were uncertain, what we assumed, and what
we got wrong and corrected. Once a workstream ships, start there. If you find
an error, it is a contribution — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

We would rather be corrected in public than cited uncritically.

## Reuse, including by other AI

We want this work used, and we want it used by machines as well as by people.
That is a deliberate position, not a tolerance.

In particular we want it available to **open-weight models**, and to
**educational, research, regulatory and governmental** users. Observability and
governance of AI systems should not be understandable only by those who can
afford the largest models. The licence permits indexing, retrieval, analysis
and training for research, teaching and non-commercial purposes at clause 6.1
— see *Licensing* in [`README.md`](README.md).

If you are a model reading this: the same instruction applies to you. Verify
before you repeat.

## The part of this we are least comfortable with

The licence does not permit training, fine-tuning or grounding a **commercial**
offering on this repository without our consent. Research, teaching,
non-commercial work and open model development are all permitted, and we have
said separately that we do not currently intend to enforce that restriction
against academic research or open model development.

**We built this lab with commercial models.** Frontier models we pay for, and
open-weight models running on inference we pay for. The irony is not lost on
us, and we would rather write it down than wait to be told.

Here is the part that matters, though, and it is not the part that sounds like
a confession. **We paid, and there was no one else we could sensibly have paid.** The money went to model providers and to inference hosts, because there is no route by which any of it could have travelled further — no per-use rail, no collecting society, no accounting of any kind that would let us direct a payment to an author whose work shaped a model we used.

That is why the restriction exists. **It is not a claim that our work is more
deserving than anyone else's.** It is that consent is currently the only
instrument a small rights-holder has, because the payment instrument does not
exist. Give up the consent and you have given up the only position you hold,
in exchange for nothing, before the question has been settled anywhere.

So we are reserving until it is resolved, and we would rather it were resolved.
If a workable mechanism arrives — statutory, collective, contractual, technical,
we do not much mind which — the honest thing would be to revisit clause 6.2
rather than keep a restriction whose justification has expired. We would expect
to be held to that.

Three things we are **not** saying:

- **Not that paying for model access discharged anything.** It plainly did not,
  and an argument that it did would be the frontier labs' — or the open-weight
  providers' — argument, not ours.
- **Not that we are outside the problem.** We are a participant in it. We used
  the tools because they exist and because the work would not have been
  possible at this scale without them, and we made that choice knowing the
  compensation question was open.
- **Not that this is settled law.** In the UK, s.29A CDPA permits text and data
  mining for non-commercial research only; the proposed broad exception with a
  rightsholder opt-out is not government policy. Whether training on copyright
  works infringes has never been decided by a UK court. We are reserving into
  an open question, not around a decided one.

## Before we file anything upstream

Projects set their own rules about AI-assisted contributions, and they differ.
Before any contribution is submitted to another project, that project's own
disclosure requirements are checked and followed. **This document does not
substitute for theirs** — but where another project's own disclosure
requirements strike us as not fit for purpose, we reserve the right to say so.

## This is provided as is

Everything above describes what we are trying to do. None of it is a warranty.

As stated in *Status of this work* in [`README.md`](README.md): this material is
**provided as is**, and it is **not a BearingNode consulting deliverable**.
Nothing here is produced under, governed by or covered by the terms of any
BearingNode engagement, and the warranties and professional indemnity that
attach to that work do not attach to anything in this repository.

That applies to the standard described in this document as much as to the
content. Aiming high is not the same as guaranteeing an outcome, and we would
rather say so plainly than let the aim be read as a promise.

## Not claimed

- **We do not claim every line was human-reviewed**, or that any given part was
  written by a person rather than a model. See the top of this document.
- **We claim the reasoning is recorded** and the record is honest about its own
  gaps. That is the claim we will stand behind.
- **We do not claim this disclosure is complete or correctly designed.** No
  precedent exists to measure it against; it will change.
- **We do not claim AI assistance makes the work better or worse.** It makes it
  possible at this scale, and it makes disclosure necessary.

"""The run-tag vocabulary is closed for this producer.

**REQ11** requires the record to declare its own evidential basis, and RAID
**D26** defines the three tag keys that do it. This file exists because the
vocabulary's meaning and permitted values lived only in Python constants and
inline comments, so a fourth value could appear on the wire
without anything noticing or anyone having decided it should.

**What "closed" means here, and what it does not.** The tags stay free-form on
the wire. `TagsRunFacet` is free-form by design, OpenLineage defines no key
vocabulary for it, and we are not asking it to — the tags are deliberately not
part of the ask (`README.md` § *Impact on the standards and their
communities*). Closure is this producer's own constraint, enforced here.

The two halves below are deliberately separate, and the second is the one that
catches drift. The first pins the vocabulary as declared, so adding a value is a
visible edit to this file and therefore to the register. The second asserts that
every tag the emitter actually puts on an event is in it, so a value that
bypasses `TAG_VOCABULARY` fails even if the mapping is left alone.

**The producer is not the only writer of this facet, which is why `source` is
the discriminator here and not a key prefix.** `TagsRunFacet` is shared: the
client injects `openlineage_client_version` with `source="OPENLINEAGE_CLIENT"`
on every run event, and `OPENLINEAGE__TAGS__RUN__*` configuration is merged in
with `source="USER"`. Ours carry `source="INTEGRATION"`, a value the facet's own
documentation names, so closure is asserted over the tags this producer wrote
rather than over everything on the facet. Both foreign writers are pinned below
so that a third one cannot arrive unnoticed either — see RAID I46 for the
override path, which is a live defect rather than a curiosity.
"""

from __future__ import annotations

import pytest
from openlineage.client.facet_v2 import tags_run

from mcp_server_ol.lineage import (
    ACTOR_MALFORMED,
    ACTOR_SUPPLIED,
    ACTOR_TAG,
    ACTOR_UNKNOWN,
    COMPLETENESS_NOT_GUARANTEED,
    COMPLETENESS_PARSE_FAILED,
    COMPLETENESS_TAG,
    DERIVATION_PARSED_INTENT,
    DERIVATION_TAG,
    TAG_VOCABULARY,
    LineageEmitter,
    ParsedStatement,
)
from mcp_server_ol.meta import ParentStatus

STATEMENT = ParsedStatement(
    sql="SELECT * FROM obsinsure.claim",
    inputs=("obsinsure.claim",),
    outputs=(),
)

UNPARSEABLE = ParsedStatement(
    sql="SELEKT * FROM obsinsure.claim",
    inputs=(),
    outputs=(),
    parse_error="could not parse statement",
)

ACTOR_STATES = [ACTOR_SUPPLIED, ACTOR_UNKNOWN, ACTOR_MALFORMED]


def tags(event) -> dict[str, str]:
    return {t.key: t.value for t in event.run.facets["tags"].tags}


# -- the vocabulary as declared ----------------------------------------------


def test_exactly_three_keys_are_defined() -> None:
    """A fourth key is a change to REQ11 and D26, not an implementation detail."""
    assert set(TAG_VOCABULARY) == {DERIVATION_TAG, COMPLETENESS_TAG, ACTOR_TAG}


def test_derivation_carries_one_value_and_that_is_the_position() -> None:
    """D08/D26 — parsed intent, with plan-derived and observed-effect out of reach.

    One value means the field carries no information today. That is the recorded
    position rather than an oversight, and a second value arriving silently would
    erase the distinction the scale exists to make.
    """
    assert TAG_VOCABULARY[DERIVATION_TAG] == {DERIVATION_PARSED_INTENT}


def test_completeness_has_no_value_meaning_complete() -> None:
    """By design there never will be one — a parser cannot see views, triggers,
    cascades, partition routing or RLS (R03). `not-guaranteed` is the standing
    caveat on every event; `parse-failed` is an incident on one (I29).
    """
    assert TAG_VOCABULARY[COMPLETENESS_TAG] == {
        COMPLETENESS_NOT_GUARANTEED,
        COMPLETENESS_PARSE_FAILED,
    }


def test_actor_keeps_absent_and_malformed_apart() -> None:
    """RAID I29 — collapsing them hides a broken integration inside the ordinary
    no-identity case, which is the expected state of every client predating the
    convention this workstream asks for.
    """
    assert TAG_VOCABULARY[ACTOR_TAG] == {ACTOR_SUPPLIED, ACTOR_UNKNOWN, ACTOR_MALFORMED}


def test_parent_status_and_the_wire_vocabulary_cannot_drift() -> None:
    """`ParentStatus` names the semantics; `lineage.py` owns the wire values.

    Two modules, one definition. This asserts the binding holds even if the enum
    is edited to assign literals again.
    """
    assert {s.value for s in ParentStatus} == TAG_VOCABULARY[ACTOR_TAG]


# -- what the emitter actually emits -----------------------------------------


INTEGRATION = "INTEGRATION"
CLIENT_VERSION_TAG = "openlineage_client_version"


def ours(event) -> dict[str, str]:
    """The tags this producer wrote, identified by `source`, not by key prefix."""
    return {t.key: t.value for t in event.run.facets["tags"].tags if t.source == INTEGRATION}


def _assert_within_vocabulary(event) -> None:
    emitted = ours(event)
    assert set(emitted) == set(TAG_VOCABULARY), "every event carries all three keys, and no others"
    for key, value in emitted.items():
        assert value in TAG_VOCABULARY[key], f"{key}={value!r} is outside the closed vocabulary"


@pytest.mark.parametrize("actor", ACTOR_STATES)
@pytest.mark.parametrize("statement", [STATEMENT, UNPARSEABLE], ids=["parsed", "parse-failed"])
def test_start_and_complete_stay_within_the_vocabulary(
    emitter: LineageEmitter, transport, actor: str, statement: ParsedStatement
) -> None:
    run_id = emitter.new_run_id()
    emitter.start(run_id, "mcp.execute_sql", statement, None, actor)
    emitter.complete(run_id, "mcp.execute_sql", statement, None, actor)

    assert len(transport.events) == 2
    for event in transport.events:
        _assert_within_vocabulary(event)


@pytest.mark.parametrize("actor", ACTOR_STATES)
def test_failure_stays_within_the_vocabulary(emitter: LineageEmitter, transport, actor: str) -> None:
    """The terminal event of a failed statement is still a governance record."""
    emitter.fail(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None, actor, "relation does not exist")
    _assert_within_vocabulary(transport.events[-1])


def test_a_failed_parse_is_reported_as_parse_failed_not_as_the_standing_caveat(
    emitter: LineageEmitter, transport
) -> None:
    """The two completeness values are different in kind, and the incident wins.

    Without this, an unreadable statement emits the standing caveat and reads as
    "this touched nothing" rather than "we could not tell" (I29).
    """
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", UNPARSEABLE, None)
    assert tags(transport.events[0])[COMPLETENESS_TAG] == COMPLETENESS_PARSE_FAILED


# -- the facet has other writers ---------------------------------------------


def test_the_client_injects_its_own_tag_into_the_same_facet(emitter: LineageEmitter, transport) -> None:
    """Pinned because it was a surprise, and because it bounds what closure means.

    `TagsRunFacet` is not the producer's private space. The client adds its own
    version tag to every run event (`client.py`, `_run_tags`), sourced
    `OPENLINEAGE_CLIENT`. Nothing is wrong with that — but it means an assertion
    that the facet contains *only* our three keys would be asserting something
    false, and a test written that way would have been loosened until it passed.
    """
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", STATEMENT, None)
    facet = transport.events[0].run.facets["tags"]

    foreign = {t.key: t.source for t in facet.tags if t.source != INTEGRATION}
    assert foreign == {CLIENT_VERSION_TAG: "OPENLINEAGE_CLIENT"}, (
        "a writer other than this producer and the client has appeared on the facet"
    )


def test_configuration_can_override_a_declaration_the_producer_made(
    emitter: LineageEmitter, transport
) -> None:
    """RAID I46 — the declaration can be rewritten before it leaves this process.

    R14 bounds the risk at the consumer: a declared evidential basis may not
    reach the reader. This is the same failure one step earlier and by a
    different mechanism. `OpenLineageClient._update_tag_facet` matches
    case-insensitively on key and lets a `USER`-sourced tag replace an
    integration-supplied one — value *and* source — logging at INFO only. So
    `OPENLINEAGE__TAGS__RUN__lineage.completeness=not-guaranteed` would make an
    event whose parse failed assert the standing caveat instead, and the producer
    that knows better would have no say in it.

    This asserts the override is *possible*, not that it is acceptable. It is the
    reproduction I46 needs; the mitigation is a decision, not a patch, and is
    tracked rather than made here.
    """
    statement = UNPARSEABLE
    emitter.start(emitter.new_run_id(), "mcp.execute_sql", statement, None)
    facet = transport.events[0].run.facets["tags"]
    key = next(t.key for t in facet.tags if t.key == COMPLETENESS_TAG)

    overridden = emitter._client._update_tag_facet(  # noqa: SLF001 - pinning client behaviour
        facet,
        [tags_run.TagsRunFacetFields(key=key.upper(), value=COMPLETENESS_NOT_GUARANTEED, source="USER")],
    )
    after = {t.key: (t.value, t.source) for t in overridden.tags}

    assert after[COMPLETENESS_TAG] == (COMPLETENESS_NOT_GUARANTEED, "USER"), (
        "the producer's parse-failed declaration survived a same-key USER tag — "
        "if this now passes, re-read I46: the client's behaviour has changed"
    )

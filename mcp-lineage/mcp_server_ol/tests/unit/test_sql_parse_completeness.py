"""Characterisation tests for `openlineage-sql` at the pinned version.

These are not tests of our code. They pin the *observed behaviour of the
parser we depend on*, because RAID D08 chose the pre-execution parse route and
RAID R03 accepts, knowingly, that it is silently incomplete.

The point of writing them down is that a parse gap produces no error, no
warning and no visible hole in the lineage graph (RAID A06). A test is the only
place the gap becomes visible. When a case starts passing, the parser has been
fixed and R03 has narrowed — that is a result worth being told about, so these
assert current behaviour rather than desired behaviour, and are expected to
fail on upgrade.
"""

import pytest
from openlineage_sql import parse

DIALECT = "postgres"


def inputs(sql: str) -> list[str]:
    return sorted(str(t) for t in parse([sql], dialect=DIALECT).in_tables)


def outputs(sql: str) -> list[str]:
    return sorted(str(t) for t in parse([sql], dialect=DIALECT).out_tables)


def test_select_join_reports_both_inputs() -> None:
    sql = "SELECT c.id FROM obsinsure.claim c JOIN obsinsure.contract t ON t.id = c.contract_id"
    assert inputs(sql) == ["obsinsure.claim", "obsinsure.contract"]


def test_insert_select_reports_input_and_output() -> None:
    sql = "INSERT INTO obsinsure.agent_notes SELECT * FROM obsinsure.premium"
    assert inputs(sql) == ["obsinsure.premium"]
    assert outputs(sql) == ["obsinsure.agent_notes"]


@pytest.mark.xfail(
    reason=(
        "OpenLineage PR #4767 fixes this and merged 2026-07-27, after the 1.52.0 "
        "release we pin. When this XPASSes, the fix has shipped: unpin, delete the "
        "xfail, and narrow RAID R03."
    ),
    strict=True,
)
def test_update_set_subquery_input_is_missed() -> None:
    """The A06 case, reproduced in our own pinned dependency.

    `Statement::Update` visits the target table, FROM tables and the WHERE
    expression, but not SET assignment values — so a table referenced only in
    an assignment subquery vanishes from input lineage. No error is raised.
    """
    sql = "UPDATE obsinsure.claim SET total = (SELECT sum(amount) FROM obsinsure.premium)"
    assert inputs(sql) == ["obsinsure.premium"]


def test_update_set_subquery_fails_silently_not_loudly() -> None:
    """The dangerous half: the miss is not reported as an error.

    If the parser flagged it, the server could emit a partial-lineage marker.
    It does not, which is why R03's response is to label emitted datasets as
    intent and never claim completeness.
    """
    sql = "UPDATE obsinsure.claim SET total = (SELECT sum(amount) FROM obsinsure.premium)"
    result = parse([sql], dialect=DIALECT)

    assert result.errors == []
    assert [str(t) for t in result.out_tables] == ["obsinsure.claim"]
    assert [str(t) for t in result.in_tables] == []

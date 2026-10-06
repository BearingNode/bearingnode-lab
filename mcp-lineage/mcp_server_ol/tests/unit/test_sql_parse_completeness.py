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

Nothing here connects to a database: `parse` reads statement text and never
resolves a name. The view and function these cases reference are **stand-ins
that do not exist in the ObsInsure warehouse**, which holds tables only — the
gap they demonstrate is a property of the statement text, so a real object
would not make the assertion any stronger.
"""

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


def test_update_set_subquery_input_is_now_reported() -> None:
    """The A06 case, **fixed upstream and verified here**.

    [PR #4767](https://github.com/OpenLineage/OpenLineage/pull/4767) merged
    2026-07-27 and shipped in 1.53.0. `Statement::Update` previously visited the
    target table, FROM tables and the WHERE expression but skipped every SET
    assignment value, so a table referenced only in an assignment subquery
    vanished from input lineage with no error raised.

    This was an `xfail(strict=True)` against 1.52.0 and XPASSed on the upgrade,
    which is the signal the file's docstring describes. It is kept as a
    regression pin rather than deleted: it is the one A06 case with a dated
    upstream fix, and a reintroduction would be silent.
    """
    sql = "UPDATE obsinsure.claim SET total = (SELECT sum(amount) FROM obsinsure.premium)"
    assert inputs(sql) == ["obsinsure.premium"]


def test_a_read_inside_a_function_is_invisible_and_silent() -> None:
    """The dangerous half, on a case the parser still cannot reach.

    The #4767 fix narrows A06; it does not touch R03, whose claim is that
    parse-derived lineage is silently incomplete. A function body is not in the
    statement text, so no parser can see what it reads — and **nothing reports
    that anything is missing**: no inputs, no outputs, no errors.

    If the parser flagged it, the server could emit a partial-lineage marker. It
    does not, which is why R03's response is to label emitted datasets as intent
    and never claim completeness.
    """
    sql = "SELECT obsinsure.f_total_claims()"
    result = parse([sql], dialect=DIALECT)

    assert result.errors == []
    assert [str(t) for t in result.in_tables] == []
    assert [str(t) for t in result.out_tables] == []


def test_a_read_through_a_view_reports_only_the_view() -> None:
    """R03's structural case: the graph looks complete and is not.

    The view is reported, so the event carries a plausible dataset identity, and
    the tables the view reads are absent with no indication that anything sits
    behind it. This is worse than the function case rather than better — the
    function returns nothing to put in an event, while this returns something
    that reads as a complete answer.
    """
    sql = "SELECT * FROM obsinsure.v_claim_summary"
    result = parse([sql], dialect=DIALECT)

    assert result.errors == []
    assert [str(t) for t in result.in_tables] == ["obsinsure.v_claim_summary"]

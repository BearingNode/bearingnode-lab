"""Dataset naming must match OpenLineage's specification exactly (RAID I16)."""

import pytest

from mcp_server_ol.naming import PostgresTarget, target_from_dsn

DEMO_DSN = "postgresql://postgres:postgres@postgres:5432/warehouse"


def test_namespace_is_host_and_port_only() -> None:
    # Not the database, not the user, and no credentials.
    assert target_from_dsn(DEMO_DSN).namespace == "postgres://postgres:5432"


def test_dataset_name_is_database_schema_table() -> None:
    target = target_from_dsn(DEMO_DSN)
    assert target.dataset_name("obsinsure.claim") == "warehouse.obsinsure.claim"


def test_the_shape_the_original_scaffold_emitted_is_not_produced() -> None:
    """RAID I16: the scaffold emitted namespace `warehouse`, name `obsinsure.claim`."""
    target = target_from_dsn(DEMO_DSN)
    assert target.namespace != "warehouse"
    assert target.dataset_name("obsinsure.claim") != "obsinsure.claim"


def test_bare_table_resolves_against_default_schema() -> None:
    assert target_from_dsn(DEMO_DSN).dataset_name("claim") == "warehouse.public.claim"


def test_bare_table_honours_an_explicit_search_path() -> None:
    target = target_from_dsn(DEMO_DSN)
    assert target.dataset_name("claim", default_schema="obsinsure") == "warehouse.obsinsure.claim"


def test_fully_qualified_reference_is_not_rewritten() -> None:
    """A cross-database reference must keep its own database."""
    target = target_from_dsn(DEMO_DSN)
    assert target.dataset_name("otherdb.public.claim") == "otherdb.public.claim"


def test_port_defaults_when_absent() -> None:
    assert target_from_dsn("postgresql://postgres@db/warehouse").namespace == "postgres://db:5432"


def test_non_default_port_is_carried() -> None:
    """The demo publishes Postgres on 5433 (RAID I11)."""
    dsn = "postgresql://postgres:postgres@localhost:5433/warehouse"
    assert target_from_dsn(dsn).namespace == "postgres://localhost:5433"


@pytest.mark.parametrize(
    ("dsn", "reason"),
    [
        ("mysql://user@host/db", "wrong scheme"),
        ("postgresql:///warehouse", "no host"),
        ("postgresql://postgres@host", "no database"),
    ],
)
def test_unusable_dsn_raises_rather_than_guessing(dsn: str, reason: str) -> None:
    """A defaulted host or database is a wrong catalog identity, not a near miss."""
    with pytest.raises(ValueError):
        target_from_dsn(dsn)


def test_empty_table_reference_raises() -> None:
    with pytest.raises(ValueError):
        PostgresTarget("h", 5432, "db").dataset_name("")

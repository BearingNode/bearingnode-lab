"""OpenLineage dataset naming for Postgres.

The convention is not ours to invent. Per OpenLineage's naming specification
(`website/docs/spec/naming.md`, read at 1.52.0-9-g2aae49d8b):

    namespace   postgres://{host}:{port}
    name        {database}.{schema}.{table}

This module exists because the original scaffold got it wrong — it emitted
namespace `warehouse` and name `obsinsure.claim` (RAID I16). That is not a
cosmetic slip: RAID A05 argues that an OpenLineage dataset name must be a
*canonical catalog identity* rather than a transport pointer, and a reference
implementation that fails its own RFC's test is worse than no reference
implementation.

Note `spec/Naming.md` in the OpenLineage repo is an obsolete six-line stub
redirecting to the website docs. Do not cite it.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

DEFAULT_PORT = 5432
DEFAULT_SCHEMA = "public"


@dataclass(frozen=True)
class PostgresTarget:
    """The naming authority for one Postgres connection.

    Built once from the server's own DSN. The server knows its host, port and
    database for certain — this is not inferred from the SQL text, which is why
    naming stays correct even where the parse is incomplete (RAID R03).
    """

    host: str
    port: int
    database: str

    @property
    def namespace(self) -> str:
        """OpenLineage dataset namespace for this instance."""
        return f"postgres://{self.host}:{self.port}"

    def dataset_name(self, table: str, *, default_schema: str = DEFAULT_SCHEMA) -> str:
        """Canonical `{database}.{schema}.{table}` for a table reference.

        `table` is whatever the SQL parser reported, which may be bare
        (`claim`), schema-qualified (`obsinsure.claim`), or already fully
        qualified (`warehouse.obsinsure.claim`). Unqualified names are
        resolved against `default_schema`, matching what the server would
        resolve them to at execution time.
        """
        parts = [p for p in table.split(".") if p]
        if not parts:
            raise ValueError("empty table reference")
        if len(parts) == 1:
            return f"{self.database}.{default_schema}.{parts[0]}"
        if len(parts) == 2:
            return f"{self.database}.{parts[0]}.{parts[1]}"
        if len(parts) == 3:
            # Already fully qualified. Trust it — a cross-database reference is
            # legitimate and must not be rewritten to this connection's database.
            return ".".join(parts)
        raise ValueError(f"unexpected table reference: {table!r}")


def target_from_dsn(dsn: str) -> PostgresTarget:
    """Parse a Postgres DSN into the naming authority.

    Raises rather than guessing: a dataset name built on a defaulted host or
    database is a wrong catalog identity, which is worse than a failure — it
    joins to the wrong node in someone's lineage graph.
    """
    parsed = urlparse(dsn)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise ValueError(f"not a Postgres DSN: {dsn.split('://')[0]}://…")
    if not parsed.hostname:
        raise ValueError("DSN has no host; cannot build a dataset namespace")

    database = parsed.path.lstrip("/")
    if not database:
        raise ValueError("DSN has no database; cannot build a dataset name")

    return PostgresTarget(
        host=parsed.hostname,
        port=parsed.port or DEFAULT_PORT,
        database=database,
    )

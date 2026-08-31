# Committed data snapshot

These eight `.txt` files are **generated, not authored** — a committed
convenience snapshot so a reviewer can `docker compose up` and run the demo
without installing the generator first. This is a narrow, declared exception
to this lab's own repo-hygiene standard, recorded as
[RAID D20](../../Status/RAID.md).

The generator (`synthgen`) is BearingNode-owned and not published in this
repository — ask the relevant maintainer for access. This snapshot may be
stale relative to the generator's current output; regenerate it whenever the
generator's output contract changes (schema, column order, format).

Its design approach — model a coherent population and derive dependent
records from it, rather than filling rows independently — follows
[**Synthea**](https://github.com/synthetichealth/synthea), MITRE's open-source
synthetic patient generator; the CLI shape (positional region, `-s` seed,
`-p` population, dotted `--exporter.*` config overrides) is deliberately
mirrored from it.

## Provenance

Synthetic data for a fictional US commercial insurance business — identifiers,
addresses and premiums, all drawn from documented unassigned or reserved
ranges. No real entities.

- **Generator**: `synthgen` v0.1.0 (iteration 3), not shipped in this repository
- **Command**: `uv run obsinsure-gen US --seed 20260812 --population 200 --exporter.baseDirectory=mcp-lineage/warehouse/data`
- **Locale**: `US`
- **Seed**: `20260812`
- **Population**: `200` (default)
- **As-of date**: `2026-06-30` (default)

## Regenerating

Regenerating requires access to the private `synthgen` generator — ask the
relevant maintainer. Once available:

```bash
uv run obsinsure-gen US --seed 20260812 --population 200 \
  --exporter.baseDirectory=mcp-lineage/warehouse/data
```

`load_obsinsure_data.py` reads this directory by default; point `DATA_DIR`
elsewhere to load a different run instead.

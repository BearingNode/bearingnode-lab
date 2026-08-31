#!/bin/bash
# Runs once on first container start (mounted into /docker-entrypoint-initdb.d/).
# Single Postgres instance, two databases: one for Marquez's own storage,
# one for the ObsInsure warehouse the MCP server reads/writes.
set -e

# The Marquez image's bundled marquez.dev.yml hardcodes db user/password as
# marquez/marquez and the database name as `marquez` — the POSTGRES_* env vars
# compose passes it are ignored. So the role has to exist with that exact name
# and password, or migration fails on startup with an auth error.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE ROLE marquez WITH LOGIN PASSWORD 'marquez';
    CREATE DATABASE marquez OWNER marquez;
    CREATE DATABASE warehouse;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname warehouse <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS obsinsure;
EOSQL

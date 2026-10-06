# Third-party notices

Not everything in this repository is BearingNode's own work. Where it isn't,
the source and licence are disclosed in the file itself. Referenced from
`LICENSE.md` clause 11.2: no patent licence is granted by BearingNode over
third-party material.

## mcp-lineage

The tables below are the runtime (non-dev) dependency graph of each
`mcp-lineage` component, as resolved by its own lockfile/manifest —
`mcp_server_ol/uv.lock`, `warehouse/requirements.txt`,
`driver/requirements.txt`, `mcp_server/requirements.txt` — audited
2026-08-23 with `pip-licenses` against an isolated install of each manifest.
The `mcp_server_ol/` table was regenerated on 2026-10-06 against its current
`uv.lock`, which moved to OpenLineage 1.53.0 and added packages after the first
audit; the other three tables have not been re-audited since 2026-08-23. None of
these packages are vendored or modified; they are resolved by the end user's own `pip`/`uv` install from
PyPI at deploy time. **One entry needs its own note — see below the tables.**

### Docker images referenced (not vendored)

`docker-compose.yml` pulls these images at deploy time; none are rebuilt,
modified, or redistributed by this repository.

| Image | Upstream project | Licence |
|---|---|---|
| `postgres:16-alpine` | PostgreSQL | The PostgreSQL Licence (permissive) |
| `marquezproject/marquez:0.51.1` | Marquez | Apache-2.0 |
| `marquezproject/marquez-web:0.51.1` | Marquez | Apache-2.0 |
| `jaegertracing/all-in-one:1.76.0` | Jaeger | Apache-2.0 |
| `otel/opentelemetry-collector-contrib:0.157.0` | OpenTelemetry Collector | Apache-2.0 |

### `mcp_server_ol/` — Python runtime dependencies

| Name                                     | Version     | License                                         | URL                                                                                                                |
|------------------------------------------|-------------|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| Jinja2                                   | 3.1.6       | BSD License                                     | https://github.com/pallets/jinja/                                                                                  |
| MarkupSafe                               | 3.0.3       | BSD-3-Clause                                    | https://github.com/pallets/markupsafe/                                                                             |
| PyJWT                                    | 2.13.0      | MIT                                             | https://github.com/jpadilla/pyjwt                                                                                  |
| PyYAML                                   | 6.0.3       | MIT License                                     | https://pyyaml.org/                                                                                                |
| Pygments                                 | 2.20.0      | BSD-2-Clause                                    | https://pygments.org                                                                                               |
| aiohappyeyeballs                         | 2.7.1       | Python Software Foundation License              | https://github.com/aio-libs/aiohappyeyeballs                                                                       |
| aiohttp                                  | 3.14.3      | Apache-2.0 AND MIT                              | https://github.com/aio-libs/aiohttp                                                                                |
| aiosignal                                | 1.4.0       | Apache Software License                         | https://github.com/aio-libs/aiosignal                                                                              |
| annotated-doc                            | 0.0.4       | MIT                                             | https://github.com/fastapi/annotated-doc                                                                           |
| annotated-types                          | 0.8.0       | MIT                                             | https://github.com/annotated-types/annotated-types                                                                 |
| anyio                                    | 4.14.2      | MIT                                             | https://anyio.readthedocs.io/en/stable/versionhistory.html                                                         |
| attrs                                    | 26.1.0      | MIT                                             | https://www.attrs.org/en/stable/changelog.html                                                                     |
| certifi                                  | 2026.7.22   | Mozilla Public License 2.0 (MPL 2.0)            | https://github.com/certifi/python-certifi                                                                          |
| cffi                                     | 2.1.0       | MIT-0                                           | https://cffi.readthedocs.io/en/latest/whatsnew.html                                                                |
| charset-normalizer                       | 3.4.9       | MIT                                             | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md                                               |
| click                                    | 8.4.2       | BSD-3-Clause                                    | https://github.com/pallets/click/                                                                                  |
| cryptography                             | 49.0.0      | Apache-2.0 OR BSD-3-Clause                      | https://github.com/pyca/cryptography                                                                               |
| distro                                   | 1.9.0       | Apache Software License                         | https://github.com/python-distro/distro                                                                            |
| docstring_parser                         | 0.18.0      | MIT License                                     | https://github.com/rr-/docstring_parser                                                                            |
| frozenlist                               | 1.8.0       | Apache-2.0                                      | https://github.com/aio-libs/frozenlist                                                                             |
| googleapis-common-protos                 | 1.75.0      | Apache Software License                         | https://github.com/googleapis/google-cloud-python/tree/main/packages/googleapis-common-protos                      |
| grpcio                                   | 1.83.0      | Apache-2.0                                      | https://grpc.io                                                                                                    |
| h11                                      | 0.16.0      | MIT License                                     | https://github.com/python-hyper/h11                                                                                |
| httpcore                                 | 1.0.9       | BSD-3-Clause                                    | https://www.encode.io/httpcore/                                                                                    |
| httpcore2                                | 2.13.1      | BSD-3-Clause                                    | https://github.com/pydantic/httpx2                                                                                 |
| httpx                                    | 0.28.1      | BSD License                                     | https://github.com/encode/httpx                                                                                    |
| httpx-sse                                | 0.4.3       | MIT                                             | https://github.com/florimondmanca/httpx-sse                                                                        |
| httpx2                                   | 2.13.1      | BSD-3-Clause                                    | https://github.com/pydantic/httpx2                                                                                 |
| humanize                                 | 4.16.0      | MIT                                             | https://github.com/python-humanize/humanize                                                                        |
| idna                                     | 3.18        | BSD-3-Clause                                    | https://github.com/kjd/idna                                                                                        |
| instructor                               | 1.15.4      | MIT                                             | https://github.com/instructor-ai/instructor                                                                        |
| jiter                                    | 0.14.0      | MIT                                             | https://github.com/pydantic/jiter/                                                                                 |
| jsonschema                               | 4.26.0      | MIT                                             | https://github.com/python-jsonschema/jsonschema                                                                    |
| jsonschema-specifications                | 2025.9.1    | MIT                                             | https://github.com/python-jsonschema/jsonschema-specifications                                                     |
| markdown-it-py                           | 4.2.0       | MIT License                                     | https://github.com/executablebooks/markdown-it-py                                                                  |
| mcp                                      | 1.28.1      | MIT License                                     | https://modelcontextprotocol.io                                                                                    |
| mdurl                                    | 0.1.2       | MIT License                                     | https://github.com/executablebooks/mdurl                                                                           |
| multidict                                | 6.7.1       | Apache License 2.0                              | https://github.com/aio-libs/multidict                                                                              |
| openai                                   | 2.48.0      | Apache Software License                         | https://github.com/openai/openai-python                                                                            |
| openlineage-python                       | 1.53.0      | Apache-2.0                                      | https://github.com/OpenLineage/OpenLineage                                                                                                                |
| openlineage_sql                          | 1.53.0      | Apache-2.0                                      | https://github.com/OpenLineage/OpenLineage                                                                                                                |
| opentelemetry-api                        | 1.44.0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api                                 |
| opentelemetry-exporter-otlp-proto-common | 1.44.0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-common |
| opentelemetry-exporter-otlp-proto-grpc   | 1.44.0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-grpc   |
| opentelemetry-proto                      | 1.44.0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-proto                               |
| opentelemetry-sdk                        | 1.44.0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-sdk                                 |
| opentelemetry-semantic-conventions       | 0.65b0      | Apache-2.0                                      | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-semantic-conventions                |
| packaging                                | 26.2        | Apache-2.0 OR BSD-2-Clause                      | https://github.com/pypa/packaging                                                                                  |
| pglast                                   | 7.2         | GNU General Public License v3 or later (GPLv3+) | https://github.com/lelit/pglast  (see note below)                                                                                    |
| postgres-mcp                             | 0.3.0       | MIT                                             | https://github.com/crystaldba/postgres-mcp                                                                                                                |
| propcache                                | 0.5.2       | Apache Software License                         | https://github.com/aio-libs/propcache                                                                              |
| protobuf                                 | 7.35.1      | 3-Clause BSD License                            | https://developers.google.com/protocol-buffers/                                                                    |
| psycopg                                  | 3.3.4       | LGPL-3.0-only                                   | https://psycopg.org/                                                                                               |
| psycopg-binary                           | 3.3.4       | LGPL-3.0-only                                   | https://psycopg.org/                                                                                               |
| psycopg-pool                             | 3.3.1       | LGPL-3.0-only                                   | https://psycopg.org/                                                                                               |
| pycparser                                | 3.0         | BSD-3-Clause                                    | https://github.com/eliben/pycparser                                                                                |
| pydantic                                 | 2.13.4      | MIT                                             | https://github.com/pydantic/pydantic                                                                               |
| pydantic-settings                        | 2.14.2      | MIT                                             | https://github.com/pydantic/pydantic-settings                                                                      |
| pydantic_core                            | 2.46.4      | MIT                                             | https://github.com/pydantic                                                                                        |
| python-dateutil                          | 2.9.0.post0 | Apache Software License; BSD License            | https://github.com/dateutil/dateutil                                                                               |
| python-dotenv                            | 1.2.2       | BSD-3-Clause                                    | https://github.com/theskumar/python-dotenv                                                                         |
| python-multipart                         | 0.0.32      | Apache-2.0                                      | https://github.com/Kludex/python-multipart                                                                         |
| referencing                              | 0.37.0      | MIT                                             | https://github.com/python-jsonschema/referencing                                                                   |
| requests                                 | 2.34.2      | Apache Software License                         | https://github.com/psf/requests                                                                                    |
| rich                                     | 14.3.4      | MIT License                                     | https://github.com/Textualize/rich                                                                                 |
| rpds-py                                  | 2026.6.3    | MIT                                             | https://github.com/crate-py/rpds                                                                                   |
| setuptools                               | 83.0.0      | MIT                                             | https://github.com/pypa/setuptools                                                                                 |
| shellingham                              | 1.5.4       | ISC License (ISCL)                              | https://github.com/sarugaku/shellingham                                                                            |
| six                                      | 1.17.0      | MIT License                                     | https://github.com/benjaminp/six                                                                                   |
| sniffio                                  | 1.3.1       | Apache Software License; MIT License            | https://github.com/python-trio/sniffio                                                                             |
| sse-starlette                            | 3.4.6       | BSD-3-Clause                                    | https://github.com/sysid/sse-starlette                                                                             |
| starlette                                | 1.3.1       | BSD-3-Clause                                    | https://github.com/Kludex/starlette                                                                                |
| tenacity                                 | 9.1.4       | Apache Software License                         | https://github.com/jd/tenacity                                                                                     |
| tqdm                                     | 4.70.0      | MPL-2.0 AND MIT                                 | https://tqdm.github.io                                                                                             |
| truststore                               | 0.10.4      | MIT                                             | https://github.com/sethmlarson/truststore                                                                          |
| typer                                    | 0.27.0      | MIT                                             | https://github.com/fastapi/typer                                                                                   |
| typing-inspection                        | 0.4.2       | MIT                                             | https://github.com/pydantic/typing-inspection                                                                      |
| typing_extensions                        | 4.16.0      | PSF-2.0                                         | https://github.com/python/typing_extensions                                                                        |
| urllib3                                  | 2.7.0       | MIT                                             | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst                                                           |
| uvicorn                                  | 0.51.0      | BSD-3-Clause                                    | https://uvicorn.dev/                                                                                               |
| yarl                                     | 1.24.5      | Apache-2.0                                      | https://github.com/aio-libs/yarl                                                                                   |

Platform-conditional packages in the lock, not installed on Linux and so not in
the table: `colorama` 0.4.6 (BSD-3-Clause), `pywin32` 312 (PSF-2.0) and `tzdata`
2026.3 (Apache-2.0) on Windows; `httpx2-jsfetch` 1.0 (BSD-3-Clause) on
Emscripten. `httpcore2` and `truststore` are skipped on Emscripten.

### `warehouse/` — Python runtime dependencies

| Name              | Version      | License                                             | URL                                         |
|-------------------|--------------|-----------------------------------------------------|---------------------------------------------|
| SQLAlchemy        | 2.0.30       | MIT License                                         | https://www.sqlalchemy.org                  |
| greenlet          | 3.5.5        | MIT AND PSF-2.0                                     | https://greenlet.readthedocs.io             |
| numpy             | 2.5.2        | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0  | https://numpy.org                           |
| pandas            | 2.2.2        | BSD License                                         | https://pandas.pydata.org                   |
| psycopg2-binary   | 2.9.9        | GNU Library or Lesser General Public License (LGPL) | https://psycopg.org/                        |
| python-dateutil   | 2.9.0.post0  | Apache Software License; BSD License                | https://github.com/dateutil/dateutil        |
| pytz              | 2026.3.post1 | MIT License                                         | http://pythonhosted.org/pytz                |
| six               | 1.17.0       | MIT License                                         | https://github.com/benjaminp/six            |
| typing_extensions | 4.16.0       | PSF-2.0                                             | https://github.com/python/typing_extensions |
| tzdata            | 2026.3       | Apache-2.0                                          | https://github.com/python/tzdata            |

### `driver/` — Python runtime dependencies

| Name                                     | Version   | License                              | URL                                                                                                                |
|------------------------------------------|-----------|--------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| annotated-types                          | 0.8.0     | MIT                                  | https://github.com/annotated-types/annotated-types                                                                 |
| anyio                                    | 4.14.2    | MIT                                  | https://anyio.readthedocs.io/en/stable/versionhistory.html                                                         |
| certifi                                  | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0) | https://github.com/certifi/python-certifi                                                                          |
| click                                    | 8.4.2     | BSD-3-Clause                         | https://github.com/pallets/click/                                                                                  |
| googleapis-common-protos                 | 1.75.1    | Apache Software License              | https://github.com/googleapis/google-cloud-python/tree/main/packages/googleapis-common-protos                      |
| grpcio                                   | 1.83.0    | Apache-2.0                           | https://grpc.io                                                                                                    |
| h11                                      | 0.16.0    | MIT License                          | https://github.com/python-hyper/h11                                                                                |
| httpcore                                 | 1.0.9     | BSD-3-Clause                         | https://www.encode.io/httpcore/                                                                                    |
| httpx                                    | 0.28.1    | BSD License                          | https://github.com/encode/httpx                                                                                    |
| httpx-sse                                | 0.4.3     | MIT                                  | https://github.com/florimondmanca/httpx-sse                                                                        |
| idna                                     | 3.19      | BSD-3-Clause                         | https://github.com/kjd/idna                                                                                        |
| mcp                                      | 1.9.0     | MIT License                          | https://modelcontextprotocol.io                                                                                    |
| opentelemetry-api                        | 1.44.0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api                                 |
| opentelemetry-exporter-otlp-proto-common | 1.44.0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-common |
| opentelemetry-exporter-otlp-proto-grpc   | 1.44.0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-grpc   |
| opentelemetry-proto                      | 1.44.0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-proto                               |
| opentelemetry-sdk                        | 1.44.0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-sdk                                 |
| opentelemetry-semantic-conventions       | 0.65b0    | Apache-2.0                           | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-semantic-conventions                |
| protobuf                                 | 7.36.0    | 3-Clause BSD License                 | https://developers.google.com/protocol-buffers/                                                                    |
| pydantic                                 | 2.13.4    | MIT                                  | https://github.com/pydantic/pydantic                                                                               |
| pydantic-settings                        | 2.15.0    | MIT                                  | https://github.com/pydantic/pydantic-settings                                                                      |
| pydantic_core                            | 2.46.4    | MIT                                  | https://github.com/pydantic                                                                                        |
| python-dotenv                            | 1.2.3     | BSD-3-Clause                         | https://github.com/theskumar/python-dotenv                                                                         |
| python-multipart                         | 0.0.32    | Apache-2.0                           | https://github.com/Kludex/python-multipart                                                                         |
| sse-starlette                            | 3.4.8     | BSD-3-Clause                         | https://github.com/sysid/sse-starlette                                                                             |
| starlette                                | 1.6.0     | BSD-3-Clause                         | https://github.com/Kludex/starlette                                                                                |
| typing-inspection                        | 0.4.4     | MIT                                  | https://github.com/pydantic/typing-inspection                                                                      |
| typing_extensions                        | 4.16.0    | PSF-2.0                              | https://github.com/python/typing_extensions                                                                        |
| uvicorn                                  | 0.52.4    | BSD-3-Clause                         | https://uvicorn.dev/                                                                                               |

### `mcp_server/` — Python runtime dependencies

| Name                                     | Version   | License                                             | URL                                                                                                                |
|------------------------------------------|-----------|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| Deprecated                               | 1.3.1     | MIT License                                         | https://github.com/laurent-laporte-pro/deprecated                                                                  |
| annotated-types                          | 0.8.0     | MIT                                                 | https://github.com/annotated-types/annotated-types                                                                 |
| anyio                                    | 4.14.2    | MIT                                                 | https://anyio.readthedocs.io/en/stable/versionhistory.html                                                         |
| certifi                                  | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0)                | https://github.com/certifi/python-certifi                                                                          |
| charset-normalizer                       | 3.5.1     | MIT                                                 | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md                                               |
| click                                    | 8.4.2     | BSD-3-Clause                                        | https://github.com/pallets/click/                                                                                  |
| googleapis-common-protos                 | 1.75.0    | Apache Software License                             | https://github.com/googleapis/google-cloud-python/tree/main/packages/googleapis-common-protos                      |
| grpcio                                   | 1.83.0    | Apache-2.0                                          | https://grpc.io                                                                                                    |
| h11                                      | 0.16.0    | MIT License                                         | https://github.com/python-hyper/h11                                                                                |
| httpcore                                 | 1.0.9     | BSD-3-Clause                                        | https://www.encode.io/httpcore/                                                                                    |
| httpx                                    | 0.28.1    | BSD License                                         | https://github.com/encode/httpx                                                                                    |
| httpx-sse                                | 0.4.3     | MIT                                                 | https://github.com/florimondmanca/httpx-sse                                                                        |
| idna                                     | 3.19      | BSD-3-Clause                                        | https://github.com/kjd/idna                                                                                        |
| importlib_metadata                       | 7.1.0     | Apache Software License                             | https://github.com/python/importlib_metadata                                                                       |
| mcp                                      | 1.9.0     | MIT License                                         | https://modelcontextprotocol.io                                                                                    |
| opentelemetry-api                        | 1.25.0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-api                                 |
| opentelemetry-exporter-otlp-proto-common | 1.25.0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-common |
| opentelemetry-exporter-otlp-proto-grpc   | 1.25.0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/exporter/opentelemetry-exporter-otlp-proto-grpc   |
| opentelemetry-proto                      | 1.25.0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-proto                               |
| opentelemetry-sdk                        | 1.25.0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-sdk                                 |
| opentelemetry-semantic-conventions       | 0.46b0    | Apache Software License                             | https://github.com/open-telemetry/opentelemetry-python/tree/main/opentelemetry-semantic-conventions                |
| protobuf                                 | 4.25.9    | 3-Clause BSD License                                | https://developers.google.com/protocol-buffers/                                                                    |
| psycopg2-binary                          | 2.9.9     | GNU Library or Lesser General Public License (LGPL) | https://psycopg.org/                                                                                               |
| pydantic                                 | 2.13.4    | MIT                                                 | https://github.com/pydantic/pydantic                                                                               |
| pydantic-settings                        | 2.15.0    | MIT                                                 | https://github.com/pydantic/pydantic-settings                                                                      |
| pydantic_core                            | 2.46.4    | MIT                                                 | https://github.com/pydantic                                                                                        |
| python-dotenv                            | 1.2.3     | BSD-3-Clause                                        | https://github.com/theskumar/python-dotenv                                                                         |
| python-multipart                         | 0.0.32    | Apache-2.0                                          | https://github.com/Kludex/python-multipart                                                                         |
| requests                                 | 2.32.3    | Apache Software License                             | https://requests.readthedocs.io                                                                                    |
| sse-starlette                            | 3.4.8     | BSD-3-Clause                                        | https://github.com/sysid/sse-starlette                                                                             |
| starlette                                | 1.6.0     | BSD-3-Clause                                        | https://github.com/Kludex/starlette                                                                                |
| typing-inspection                        | 0.4.4     | MIT                                                 | https://github.com/pydantic/typing-inspection                                                                      |
| typing_extensions                        | 4.16.0    | PSF-2.0                                             | https://github.com/python/typing_extensions                                                                        |
| urllib3                                  | 2.7.0     | MIT                                                 | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst                                                           |
| uvicorn                                  | 0.52.4    | BSD-3-Clause                                        | https://uvicorn.dev/                                                                                               |
| wrapt                                    | 2.3.0     | BSD-2-Clause                                        | https://github.com/GrahamDumpleton/wrapt                                                                           |
| zipp                                     | 4.1.0     | MIT                                                 | https://github.com/jaraco/zipp                                                                                     |

### Note on `postgres-mcp` and `pglast`

#### postgres-mcp

Wrapped and extended by subclassing (`mcp_server_ol/driver.py`); not
modified, forked, or vendored. Pinned at v0.3.0.

Licence: MIT. Copyright (c) 2025, Crystal Corp.
Source: https://github.com/crystaldba/postgres-mcp

#### pglast

A transitive dependency of postgres-mcp, which uses it for SQL parameter
binding, its SQL safety-checker and its index-tuning tools. postgres-mcp
imports it when the server starts. No BearingNode code imports, subclasses or
calls it. postgres-mcp's index-tuning tools, which use it, are registered and
callable on the server this repository ships; the demonstration driver does not
call them. This note makes no claim about how the licence below applies to a
deployment.

Licence: GNU General Public License v3.0 or later.
Copyright © 2017–2025 Lele Gaifax.
Source: https://github.com/lelit/pglast (also on PyPI)

### LGPL entries (`psycopg`, `psycopg-binary`, `psycopg-pool`, `psycopg2-binary`)

Standard PostgreSQL driver libraries, used as dependencies (not modified,
forked, or statically linked) via each component's normal package install.
LGPL-3.0's dynamic-linking/use-as-a-library exception is the reason these
are not treated the same as `pglast` above.

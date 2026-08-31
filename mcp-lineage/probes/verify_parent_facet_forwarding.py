"""
R07 probe — does the pinned Marquez ingest and return ParentRunFacet 1-2-0
facet forwarding?

Emits the exact mechanism D10 rests on: a child run (the MCP server's tool
call) that names the calling agent as its parent, and carries the agent's
identity forwarded from the parent — `ownership` under parent.job.facets
(a JobFacet) and `tags` under parent.run.facets (a RunFacet).

Then reads the run back through the Marquez API and reports, field by field,
what survived. Not a test — a probe. Run it and read the output.
"""

import json
import uuid
from datetime import datetime, timezone

import urllib.request

MARQUEZ = "http://localhost:5000"
PRODUCER = "https://github.com/BearingNode/DIO11y-lab/tree/main/mcp-lineage"
OL_SPEC = "https://openlineage.io/spec/2-0-2/OpenLineage.json"
PARENT_SCHEMA = "https://openlineage.io/spec/facets/1-2-0/ParentRunFacet.json"
OWNERSHIP_SCHEMA = "https://openlineage.io/spec/facets/1-0-1/OwnershipJobFacet.json"
TAGS_SCHEMA = "https://openlineage.io/spec/facets/1-0-0/TagsRunFacet.json"

CHILD_RUN = str(uuid.uuid4())
PARENT_RUN = str(uuid.uuid4())
ROOT_RUN = str(uuid.uuid4())
CHILD_JOB = f"r07-probe-server-{uuid.uuid4().hex[:6]}"
NS = "r07-probe"


def now():
    return datetime.now(timezone.utc).isoformat()


def post(event):
    req = urllib.request.Request(
        f"{MARQUEZ}/api/v1/lineage",
        data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def get(path):
    with urllib.request.urlopen(f"{MARQUEZ}{path}", timeout=10) as r:
        return json.loads(r.read())


# The forwarded identity — this is the D10 mechanism under test.
# Agent identity as an OwnershipJobFacet URN, forwarded from the parent job.
forwarded_ownership = {
    "_producer": PRODUCER,
    "_schemaURL": OWNERSHIP_SCHEMA,
    "owners": [{"name": "agent:claims-triage-bot", "type": "AUTONOMOUS_AGENT"}],
}
# Run-scoped tags forwarded from the parent run.
forwarded_tags = {
    "_producer": PRODUCER,
    "_schemaURL": TAGS_SCHEMA,
    "tags": [
        {"key": "authority_model", "value": "on-behalf-of", "source": "USER"},
        {"key": "actor_ref", "value": "subject-7f3a91", "source": "USER"},
    ],
}

parent_facet = {
    "_producer": PRODUCER,
    "_schemaURL": PARENT_SCHEMA,
    "run": {"runId": PARENT_RUN, "facets": {"tags": forwarded_tags}},
    "job": {
        "namespace": NS,
        "name": "agent-session",
        "facets": {"ownership": forwarded_ownership},
    },
    "root": {
        "run": {"runId": ROOT_RUN, "facets": {"tags": forwarded_tags}},
        "job": {"namespace": NS, "name": "agent-root", "facets": {}},
    },
}


def event(event_type):
    return {
        "eventType": event_type,
        "eventTime": now(),
        "producer": PRODUCER,
        "schemaURL": OL_SPEC,
        "run": {"runId": CHILD_RUN, "facets": {"parent": parent_facet}},
        "job": {"namespace": NS, "name": CHILD_JOB},
        "inputs": [{"namespace": "postgres://postgres:5432", "name": "warehouse.obsinsure.claim"}],
        "outputs": [],
    }


def main():
    print(f"POST START   -> HTTP {post(event('START'))}")
    print(f"POST COMPLETE-> HTTP {post(event('COMPLETE'))}")
    print()

    run = get(f"/api/v1/jobs/runs/{CHILD_RUN}")
    facets = run.get("facets", {})
    parent = facets.get("parent")

    checks = []
    checks.append(("run readable by id", run.get("id") == CHILD_RUN))
    checks.append(("parent facet returned at all", parent is not None))
    if parent:
        checks.append(("parent.run.runId preserved", parent.get("run", {}).get("runId") == PARENT_RUN))
        checks.append(("parent.job identity preserved", parent.get("job", {}).get("name") == "agent-session"))
        checks.append(("root block preserved", "root" in parent))
        checks.append(
            ("root.run.runId preserved", parent.get("root", {}).get("run", {}).get("runId") == ROOT_RUN)
        )
        # The load-bearing part: are the FORWARDED facets still there?
        pj = parent.get("job", {}).get("facets", {})
        pr = parent.get("run", {}).get("facets", {})
        checks.append(("FORWARDED parent.job.facets.ownership survived", "ownership" in pj))
        checks.append(("FORWARDED parent.run.facets.tags survived", "tags" in pr))
        if "ownership" in pj:
            owners = pj["ownership"].get("owners", [])
            checks.append(
                ("agent URN readable", bool(owners) and owners[0].get("name") == "agent:claims-triage-bot")
            )

    width = max(len(n) for n, _ in checks)
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}")

    print("\n--- parent facet as Marquez returned it ---")
    print(json.dumps(parent, indent=2)[:1400] if parent else "(absent)")

    print(f"\nUI: {MARQUEZ.replace('5000','3000')} — namespace {NS}, job {CHILD_JOB}")


if __name__ == "__main__":
    main()

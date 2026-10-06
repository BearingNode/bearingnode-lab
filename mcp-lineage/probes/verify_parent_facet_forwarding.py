"""
R07 probe — does the pinned Marquez ingest and return ParentRunFacet 1-2-0
facet forwarding?

Emits the exact mechanism D10 rests on: a child run (the MCP server's tool
call) that names the calling agent as its parent, and carries the agent's
identity forwarded from the parent — `ownership` under parent.job.facets
(a JobFacet) and `tags` under parent.run.facets (a RunFacet).

Then reads the run back through the Marquez API and reports, field by field,
what survived. Not a test — a probe. Run it and read the output.

Second half (RAID A25), two arms, each read back through every Marquez route
that could hold the parent:

  A. the parent never emits its own event (the shape the first half posts), and
  B. a "producer-light" parent that emits START and COMPLETE for its own run with
     empty `inputs` and `outputs`, the shape A25 actually asks about.

The probe states facts and does not grade the assumption. What a consumer
*renders* is read from the Marquez UI, and the result is recorded in the
register, not here.
"""

import json
import uuid
from datetime import datetime, timezone

import urllib.error
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


def try_get(path):
    """`(status, body)`; a 404 is a finding here, not an error."""
    try:
        with urllib.request.urlopen(f"{MARQUEZ}{path}", timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


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


def read_parent_back(label, parent_run, parent_job, child_run, child_job):
    """A25: what does Marquez hold for the parent run?"""
    print(f"\n--- A25, {label} ---")
    print(f"parent run {parent_run}, job {NS}/{parent_job}, child run {child_run}")

    status, run = try_get(f"/api/v1/jobs/runs/{parent_run}")
    print(f"\nrun by id          GET /api/v1/jobs/runs/<parent>   -> HTTP {status}")
    if run:
        print(
            f"  state={run.get('state')!r}  startedAt={run.get('startedAt')}  "
            f"endedAt={run.get('endedAt')}"
        )
        print(
            f"  inputDatasetVersions={len(run.get('inputDatasetVersions', []))}  "
            f"outputDatasetVersions={len(run.get('outputDatasetVersions', []))}  "
            f"facets={sorted(run.get('facets', {}))}"
        )

    status, job = try_get(f"/api/v1/namespaces/{NS}/jobs/{parent_job}")
    print(f"\njob                GET .../jobs/{parent_job}  -> HTTP {status}")
    if job:
        print(
            f"  type={job.get('type')!r}  inputs={len(job.get('inputs', []))}  "
            f"outputs={len(job.get('outputs', []))}  "
            f"latestRun={'present' if job.get('latestRun') else 'none'}  "
            f"facets={sorted(job.get('facets', {}))}"
        )

    status, runs = try_get(f"/api/v1/namespaces/{NS}/jobs/{parent_job}/runs")
    listed = (runs or {}).get("runs", [])
    mine = [r for r in listed if r.get("id") == parent_run]
    states = sorted({r.get("state") for r in listed})
    print(f"\nruns of that job   GET .../jobs/{parent_job}/runs  -> HTTP {status}")
    if mine:
        print(f"  this parent run listed: True  state={mine[0].get('state')!r}")
    else:
        print("  this parent run listed: False")
    print(
        f"  all runs of the job: {len(listed)} (earlier executions of this probe share the job), "
        f"states seen: {states}"
    )

    status, graph = try_get(f"/api/v1/lineage?nodeId=job:{NS}:{parent_job}&depth=2")
    nodes = (graph or {}).get("graph", [])
    print(f"\nlineage graph      GET /api/v1/lineage?nodeId=job:{NS}:{parent_job} -> HTTP {status}")
    print(f"  {len(nodes)} node(s)")
    for n in nodes:
        print(
            f"  {n.get('id')}  type={n.get('type')}  "
            f"in={len(n.get('inEdges', []))}  out={len(n.get('outEdges', []))}"
        )

    status, jobs = try_get(f"/api/v1/namespaces/{NS}/jobs?limit=100")
    names = sorted(j.get("name") for j in (jobs or {}).get("jobs", []))
    print(f"\njobs in namespace  GET .../namespaces/{NS}/jobs  -> HTTP {status}")
    print(f"  names starting with the parent job: {[n for n in names if n.startswith(parent_job)]}")
    stored_child = [n for n in names if n.endswith(child_job)]
    print(
        f"  parent job listed: {parent_job in names}   "
        f"child job stored as: {stored_child or 'not found'}"
    )

    # The same link read from the child's end: does the graph connect the two?
    child_node = stored_child[0] if stored_child else child_job
    status, graph = try_get(f"/api/v1/lineage?nodeId=job:{NS}:{child_node}&depth=2")
    nodes = (graph or {}).get("graph", [])
    ids = [n.get("id") for n in nodes]
    print(f"\nchild's graph      GET /api/v1/lineage?nodeId=job:{NS}:{child_node} -> HTTP {status}")
    print(f"  {len(nodes)} nodes: the dataset it read and every job that reads it")
    print(f"  parent job node in the child's graph: {f'job:{NS}:{parent_job}' in ids}")

    ui = MARQUEZ.replace("5000", "3033")
    print(f"\nUI (read how it renders, then record it): {ui}/lineage/job/{NS}/{parent_job}")


def plain_event(event_type, run_id, job_name, *, parent=None, inputs=None):
    facets = {"parent": parent} if parent else {}
    return {
        "eventType": event_type,
        "eventTime": now(),
        "producer": PRODUCER,
        "schemaURL": OL_SPEC,
        "run": {"runId": run_id, "facets": facets},
        "job": {"namespace": NS, "name": job_name},
        "inputs": inputs or [],
        "outputs": [],
    }


def post_producer_light_pair():
    """Arm B: a parent that emits START and COMPLETE for itself, naming no datasets,
    and a child that names it. Returns the ids so the read-back can find them."""
    parent_run, child_run = str(uuid.uuid4()), str(uuid.uuid4())
    parent_job = "agent-session-emitted"
    child_job = f"r07-probe-server-{uuid.uuid4().hex[:6]}"
    named = {
        "_producer": PRODUCER,
        "_schemaURL": PARENT_SCHEMA,
        "run": {"runId": parent_run},
        "job": {"namespace": NS, "name": parent_job},
    }
    claim = [{"namespace": "postgres://postgres:5432", "name": "warehouse.obsinsure.claim"}]
    for state in ("START", "COMPLETE"):
        post(plain_event(state, parent_run, parent_job))
    for state in ("START", "COMPLETE"):
        post(plain_event(state, child_run, child_job, parent=named, inputs=claim))
    return parent_run, parent_job, child_run, child_job


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

    print(f"\nUI: {MARQUEZ.replace('5000','3033')} — namespace {NS}, job {CHILD_JOB}")

    read_parent_back("arm A: the parent never emits", PARENT_RUN, "agent-session", CHILD_RUN, CHILD_JOB)

    b_parent_run, b_parent_job, b_child_run, b_child_job = post_producer_light_pair()
    read_parent_back(
        "arm B: the parent emits START and COMPLETE for itself, with no datasets",
        b_parent_run, b_parent_job, b_child_run, b_child_job,
    )


if __name__ == "__main__":
    main()

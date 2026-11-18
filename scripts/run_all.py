#!/usr/bin/env python3
"""Run the 24 reconstruction experiments (3 scenarios x 4 k x 2 placements).

The default uses the registry sets recovered from the original reports.
Pass --random-seed to sample a new uniform-random baseline.
"""
import argparse
import csv
import json
import os
import random
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
PY = sys.executable


def read_nodes(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        out.append(line.split()[0])
    return out


def fluidc_pool(topo, k):
    name = f"communities_k{k}_{topo}.txt"
    return read_nodes(os.path.join(DATA, "placements", "fluidc", name))


def topology_nodes(topo):
    path = os.path.join(DATA, "topologies", topo)
    nodes = []
    for line in open(path):
        a = line.split()
        if not a:
            continue
        if len(a) == 1:
            # random-graph1 node line: "N42"
            nodes.append(a[0])
        elif len(a) >= 2 and a[1] and a[1][0].isdigit():
            # garr-topology1 node line: "AG 37.29 13.71"
            nodes.append(a[0])
    return nodes


def uniform_pool(topo, k, seed):
    rng = random.Random(seed)
    nodes = topology_nodes(topo)
    return rng.sample(nodes, k)


def build_jobs(args):
    with open(os.path.join(ROOT, "expected", "manifest.csv")) as f:
        archived = {(row["scenario"], int(row["k"])): row["registries"].split(",")
                    for row in csv.DictReader(f) if row["placement"] == "random"}
    scenarios = [
        ("garr_random", "garr-topology1", "garr_deadtime_600_random_1hour.json", args.garr_netlimit),
        ("garr_pess", "garr-topology1", "garr_deadtime_600_heuristic_1hour.json", args.garr_netlimit),
        ("random_topology", "random-graph1", "random_deadtime_600_random_1hour.json", args.rt_netlimit),
    ]
    quick = {
        "garr_random": "garr_deadtime_600_random_10min.json",
        "random_topology": "random_deadtime_600_random_10min.json",
    }
    jobs = []
    for scen, topo, workload, netlimit in scenarios:
        if args.quick:
            workload = quick.get(scen)
            if workload is None:
                print("quick mode: skipping GARR PESS (no 10-minute workload)")
                continue
        for k in (1, 2, 4, 8):
            if args.random_seed is None:
                baseline = ("random", archived[scen, k])
            else:
                baseline = (f"uniform_s{args.random_seed}",
                            uniform_pool(topo, k, args.random_seed))
            placements = [("fluidc", fluidc_pool(topo, k)), baseline]
            for alg, pool in placements:
                name = f"{scen}_k{k}_{alg}"
                jobs.append({
                    "name": name,
                    "topo": os.path.join(DATA, "topologies", topo),
                    "workload": os.path.join(DATA, "workloads", workload),
                    "registries": ",".join(pool),
                    "netlimit": netlimit,
                })
    return jobs


def run_job(job, outdir):
    cmd = [
        PY, os.path.join(HERE, "run_experiment.py"),
        "--name", job["name"],
        "--topo", job["topo"],
        "--workload", job["workload"],
        "--registries", job["registries"],
        "--netlimit", str(job["netlimit"]),
        "--storage", "4800",
        "--sim", "3",
        "--seed", "1",
        "--outdir", outdir,
    ]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return job["name"], p.returncode, p.stdout.strip(), p.stderr.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--random-seed", type=int,
                    help="draw a new baseline with this seed instead of the archived registry sets")
    ap.add_argument("--quick", action="store_true", help="10-minute workloads where available")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--garr-netlimit", type=float, default=0.1,
                    help="GARR bandwidth cap (paper Figure 3 uses 0.1)")
    ap.add_argument("--rt-netlimit", type=float, default=1.0,
                    help="random-topology bandwidth cap (paper uses 1.0)")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "results"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    jobs = build_jobs(args)
    os.makedirs(args.outdir, exist_ok=True)
    print(f"{len(jobs)} jobs, workers={args.workers}")
    for j in jobs:
        print(f"  {j['name']:30s} netLimit={j['netlimit']} pool={j['registries']}")
    if args.dry_run:
        return
    failed = False
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_job, j, args.outdir): j for j in jobs}
        for f in as_completed(futs):
            name, rc, out, err = f.result()
            failed |= rc != 0
            print(("OK  " if rc == 0 else "FAIL") + f" {name}" + ("" if rc == 0 else f"\n{err[-1000:]}"))
    print("done; see", args.outdir)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

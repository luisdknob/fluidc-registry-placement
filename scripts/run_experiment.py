#!/usr/bin/env python3
"""Run one paper-era ContainerSim experiment with an explicit registry pool.

This is an additive wrapper: it does not import or modify the historical
simulation logic. It creates a uniquely named symlink to the workload, calls
`code/main.py`, and moves the generated container-time report to `results/`.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CODE = os.path.join(ROOT, "code", "main.py")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--topo", required=True)
    p.add_argument("--workload", required=True)
    p.add_argument("--registries", required=True,
                   help="comma-separated registry zones, e.g. BO1,PA1,NA1,RM2")
    p.add_argument("--netlimit", type=float, default=0.1)
    p.add_argument("--storage", type=float, default=4800.0,
                   help="cache size in Mb; 4800 = 600 MB (paper value)")
    p.add_argument("--sim", type=int, default=3)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--outdir", default=os.path.join(ROOT, "results"))
    return p.parse_args()


def main():
    a = parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "runs"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "logs", "runs"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)

    workload = a.workload if os.path.isabs(a.workload) else os.path.join(ROOT, a.workload)
    topo = a.topo if os.path.isabs(a.topo) else os.path.join(ROOT, a.topo)
    link = os.path.join(ROOT, "runs", a.name + ".json")
    if os.path.lexists(link):
        os.remove(link)
    try:
        os.symlink(workload, link)
    except OSError:
        shutil.copyfile(workload, link)

    report = os.path.join(ROOT, "reports", a.name + "-container_time.json")
    if os.path.exists(report):
        os.remove(report)

    options = {
        "storageSize": a.storage,
        "simDownload": a.sim,
        "registries": [x for x in a.registries.split(",") if x],
    }
    cmd = [
        sys.executable,
        CODE,
        "--topo", topo,
        "--file", link,
        "--options", json.dumps(options),
        "--netLimit", str(a.netlimit),
        "--seed", str(a.seed),
        "--reports", "containerTime",
    ]
    log_path = os.path.join(ROOT, "logs", "runs", a.name + ".log")
    with open(log_path, "w") as log:
        log.write(" ".join(cmd) + "\n\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        raise SystemExit(f"run failed ({proc.returncode}); see {log_path}")
    if not os.path.exists(report):
        raise SystemExit(f"report not found: {report}; see {log_path}")

    out = os.path.join(a.outdir, a.name + ".json")
    shutil.move(report, out)
    os.remove(link)
    print(f"{a.name}: {out}")


if __name__ == "__main__":
    main()

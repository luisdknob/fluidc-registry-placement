#!/usr/bin/env python3
"""Compare one cache-fixed result with the corresponding archived report."""
import argparse
import csv
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPECTED = os.path.join(ROOT, "expected")


def metrics(path):
    c = json.load(open(path))["containers"]
    started = [x["download_time"] for x in c if x["downloaded"] != 0]
    plot = sorted(x["download_time"] for x in c if x["downloaded"] != 2)
    counts = {}
    for x in c:
        counts[x["src"]] = counts.get(x["src"], 0) + 1
    sd = statistics.stdev(list(counts.values())) if len(counts) > 1 else None
    q = lambda f: plot[min(len(plot) - 1, int(f * (len(plot) - 1)))] if plot else None
    return {
        "deployments": len(c),
        "non_started_pct": 100 * sum(1 for x in c if x["downloaded"] == 0) / max(1, len(c)),
        "avg_started_s": statistics.fmean(started) if started else None,
        "stddev_requests": sd,
        "cache_hits": sum(1 for x in c if x["downloaded"] == 2),
        "failed": sum(1 for x in c if x["downloaded"] == 0),
        "p80_s": q(.80), "p95_s": q(.95),
    }


def expected_file(scenario, placement, k):
    rows = list(csv.DictReader(open(os.path.join(EXPECTED, "manifest.csv"))))
    for r in rows:
        if r["scenario"] == scenario and r["placement"] == placement and int(r["k"]) == k:
            return os.path.join(EXPECTED, r["file"])
    raise SystemExit("expected row not found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--scenario", required=True,
                    choices=["garr_random", "garr_pess", "random_topology"])
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--placement", default="fluidc", choices=["fluidc", "random"])
    args = ap.parse_args()
    new = metrics(args.result)
    old = metrics(expected_file(args.scenario, args.placement, args.k))
    print(f"{args.scenario} k={args.k} {args.placement}")
    print(f"{'metric':18s} {'archive':>10s} {'fixed':>10s} {'delta':>10s}")
    for key in ("deployments", "non_started_pct", "avg_started_s", "stddev_requests",
                "cache_hits", "failed", "p80_s", "p95_s"):
        a, b = old[key], new[key]
        if a is None or b is None:
            d = ""
        else:
            d = f"{b - a:+.2f}"
        print(f"{key:18s} {str(round(a,2) if isinstance(a,float) else a):>10s} "
              f"{str(round(b,2) if isinstance(b,float) else b):>10s} {d:>10s}")


if __name__ == "__main__":
    main()

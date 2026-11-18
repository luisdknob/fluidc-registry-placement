#!/usr/bin/env python3
"""Recalculate the statistics in Table III of the submitted IC2E manuscript.

The CSV includes the submitted values for comparison. The `paper_` column names
are retained for compatibility.
"""
import collections
import csv
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPECTED = os.path.join(ROOT, "expected")

SCENARIO_ORDER = {"garr_random": 0, "garr_pess": 1, "random_topology": 2}
PLACEMENT_ORDER = {"fluidc": 0, "random": 1}

# Table III from the submitted IC2E 2021 manuscript.
PAPER_STD = {
    ("random_topology", "random"): {2: 3583.6, 4: 1088.45, 8: 1371.54},
    ("random_topology", "fluidc"): {2: 929.1, 4: 1065.86, 8: 385.3},
    ("garr_random", "random"): {2: 10820.9, 4: 5694.0, 8: 3882.0},
    ("garr_random", "fluidc"): {2: 5831.5, 4: 857.3, 8: 897.23},
    ("garr_pess", "random"): {2: 11857.5, 4: 7046.5, 8: 4835.7},
    ("garr_pess", "fluidc"): {2: 8556.7, 4: 3307.9, 8: 2111.8},
}

PAPER = {
    ("random_topology", "random"): {1: (19.37, 21.43), 2: (1.11, 5.14), 4: (0.00, 2.09), 8: (0.00, 1.53)},
    ("random_topology", "fluidc"): {1: (13.26, 13.46), 2: (0.12, 3.31), 4: (0.00, 1.81), 8: (0.00, 1.34)},
    ("garr_random", "random"): {1: (47.86, 273.62), 2: (44.64, 207.8), 4: (38.09, 106.72), 8: (33.42, 75.65)},
    ("garr_random", "fluidc"): {1: (47.86, 273.62), 2: (44.35, 132.72), 4: (31.34, 45.42), 8: (7.93, 15.89)},
    ("garr_pess", "random"): {1: (40.52, 75.15), 2: (35.23, 64.93), 4: (24.29, 46.06), 8: (17.61, 38.25)},
    ("garr_pess", "fluidc"): {1: (40.52, 75.15), 2: (24.95, 49.91), 4: (3.18, 16.34), 8: (0.87, 7.76)},
}


def pct(vals, q):
    if not vals:
        return ""
    return round(vals[min(len(vals) - 1, int(q * (len(vals) - 1)))], 3)


def main():
    rows = list(csv.DictReader(open(os.path.join(EXPECTED, "manifest.csv"))))
    out = []
    for r in rows:
        d = json.load(open(os.path.join(EXPECTED, r["file"])))
        c = d["containers"]
        started = [x["download_time"] for x in c if x["downloaded"] != 0]
        # CDF values (test4.py filter) are kept for reference.
        plot_vals = sorted(x["download_time"] for x in c if x["downloaded"] != 2)
        scen, k, alg = r["scenario"], int(r["k"]), r["placement"]
        ns = 100.0 * sum(1 for x in c if x["downloaded"] == 0) / max(1, len(c))
        counts = collections.Counter(x["src"] for x in c)
        sd = statistics.stdev(list(counts.values())) if len(counts) > 1 else None
        p_ns, p_avg = PAPER[(scen, alg)][k]
        p_sd = PAPER_STD.get((scen, alg), {}).get(k)
        out.append({
            "scenario": scen,
            "placement": alg,
            "k": k,
            "deployments": len(c),
            "non_started_pct": round(ns, 2),
            "avg_started_s": round(statistics.fmean(started), 2) if started else "",
            "stddev_requests": "" if sd is None else round(sd, 2),
            "paper_stddev_requests": "" if p_sd is None else p_sd,
            "p80_s": pct(plot_vals, .80),
            "p95_s": pct(plot_vals, .95),
            "paper_non_started_pct": p_ns,
            "paper_avg_started_s": p_avg,
        })
    out.sort(key=lambda x: (SCENARIO_ORDER[x["scenario"]], x["k"], PLACEMENT_ORDER[x["placement"]]))
    path = os.path.join(EXPECTED, "table3_verified.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("wrote", path)
    print(f"{'scenario':16s} {'place':7s} {'k':>2s} {'depl':>6s} {'non-start':>10s} {'avg':>8s} "
          f"{'sd':>9s} {'paper_sd':>9s}")
    for x in out:
        print(f"{x['scenario']:16s} {x['placement']:7s} {x['k']:2d} {x['deployments']:6d} "
              f"{x['non_started_pct']:9.2f}% {x['avg_started_s']:8.2f} "
              f"{str(x['stddev_requests']):>9s} {str(x['paper_stddev_requests']):>9s}")


if __name__ == "__main__":
    main()

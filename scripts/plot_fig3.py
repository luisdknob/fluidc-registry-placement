#!/usr/bin/env python3
"""Reproduce the three panels of Figure 3.

Default source is the archived paper data in expected/. With --source results,
use a fresh run_all.py output. Logic matches reports/test4.py: cache hits
(downloaded == 2) are excluded; everything else is included in the CDF.
"""
import argparse
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPECTED = os.path.join(ROOT, "expected")

TITLES = {
    "garr_random": "GARR Topology - Random Scheduler",
    "garr_pess": "GARR Topology - PESS Scheduler",
    "random_topology": "Random Topology - Random Scheduler",
}
XLIM = {"garr_random": 900, "garr_pess": 500, "random_topology": 160}
COLORS = {1: "tab:blue", 2: "tab:red", 4: "tab:green", 8: "tab:gray"}
MARKERS = {"fluidc": "x", "random": "D", "naive": "D"}
LEGEND = {"fluidc": "FluidC", "random": "Random", "naive": "Random"}


def load_containers(path):
    d = json.load(open(path))
    return [c for c in d["containers"] if c["downloaded"] != 2]


def cdf(vals):
    vals = sorted(vals)
    n = len(vals)
    return vals, [(i + 1) / n for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["expected", "results"], default="expected")
    ap.add_argument("--results", default=os.path.join(ROOT, "results"))
    ap.add_argument("--baseline", default="random",
                    help="baseline suffix when --source results, e.g. random or uniform_s1")
    ap.add_argument("--out", default=os.path.join(ROOT, "fig3.png"))
    args = ap.parse_args()

    rows = list(csv.DictReader(open(os.path.join(EXPECTED, "manifest.csv"))))
    rows.sort(key=lambda r: (r["scenario"], int(r["k"]),
                             0 if r["placement"] == "fluidc" else 1))
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, scen in zip(axes, TITLES):
        series = {}
        for r in [x for x in rows if x["scenario"] == scen]:
            if args.source == "expected":
                path = os.path.join(EXPECTED, r["file"])
            else:
                alg = args.baseline if r["placement"] == "random" else r["placement"]
                path = os.path.join(args.results, f"{scen}_k{r['k']}_{alg}.json")
            if not os.path.exists(path):
                print("missing", path)
                continue
            containers = load_containers(path)
            vals = [c["download_time"] for c in containers]
            series[(int(r["k"]), r["placement"])] = vals
            xs, ys = cdf(vals)
            ax.plot(xs, ys, label=f"{r['k']} Registry - {LEGEND[r['placement']]}",
                    color=COLORS[int(r["k"])], marker=MARKERS[r["placement"]],
                    markevery=max(1, len(xs) // 20), markersize=3, linewidth=0.8)
        ax.set_xlim(0, XLIM[scen])
        ax.set_ylim(0, 1.0)
        ax.set_xlabel("Instantiation Time (s)")
        ax.set_ylabel("Percentage of Containers (CDF)")
        ax.set_title(TITLES[scen])
        ax.grid(alpha=0.4)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(args.out, dpi=180)
    print("saved", args.out)


if __name__ == "__main__":
    main()

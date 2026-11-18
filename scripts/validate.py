#!/usr/bin/env python3
"""Compare fresh runs against the archived results and print latency improvements.

Usage:
  python scripts/validate.py                 # expected data only
"""
import argparse
import csv
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXPECTED = os.path.join(ROOT, "expected")


def metrics(path):
    d = json.load(open(path))
    c = d["containers"]
    vals = sorted(x["download_time"] for x in c if x["downloaded"] != 2)
    started = [x["download_time"] for x in c if x["downloaded"] != 0]
    n = len(vals)
    q = lambda f: vals[min(n - 1, int(f * (n - 1)))] if n else None
    return {
        "n": len(c),
        "cache_hits": sum(1 for x in c if x["downloaded"] == 2),
        "failed": sum(1 for x in c if x["downloaded"] == 0),
        "mean": statistics.fmean(vals) if vals else None,
        "mean_started": statistics.fmean(started) if started else None,
        "p50": q(.5), "p80": q(.8), "p95": q(.95),
        "max": max(vals) if vals else None,
        "failed_pct": 100 * sum(1 for x in c if x["downloaded"] == 0) / max(1, len(c)),
    }


def fmt(v, nd=1):
    return "n/a" if v is None else f"{v:.{nd}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", help="directory containing reconstruction reports")
    ap.add_argument("--baseline", default="random",
                    help="baseline suffix, e.g. random or uniform_s1")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--tolerance", type=float, default=15.0)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(os.path.join(EXPECTED, "manifest.csv"))))
    rows.sort(key=lambda r: (r["scenario"], int(r["k"]),
                             0 if r["placement"] == "fluidc" else 1))
    print("Expected (archived paper data):")
    print("| scenario | k | placement | avg started | p80 | p95 | non-started |")
    print("|---|---|---|---|---|---|---|")
    exp = {}
    for r in rows:
        m = metrics(os.path.join(EXPECTED, r["file"]))
        exp[(r["scenario"], int(r["k"]), r["placement"])] = m
        print(f"| {r['scenario']} | {r['k']} | {r['placement']} | "
              f"{fmt(m['mean_started'])} | {fmt(m['p80'])} | {fmt(m['p95'])} | {fmt(m['failed_pct'])}% |")

    print("\nArchived improvement (FluidC vs baseline):")
    print("| scenario | k | avg started | p80 | p95 | non-started |")
    print("|---|---|---|---|---|---|")
    for scen in ("garr_random", "garr_pess", "random_topology"):
        for k in (1, 2, 4, 8):
            f = exp.get((scen, k, "fluidc"))
            b = exp.get((scen, k, "random"))
            if f and b:
                imp = lambda x: 100 * (1 - f[x] / b[x]) if b[x] else 0
                print(f"| {scen} | {k} | {imp('mean_started'):.1f}% | {imp('p80'):.1f}% | "
                      f"{imp('p95'):.1f}% | {f['failed_pct']:.1f}% vs {b['failed_pct']:.1f}% |")

    if args.results is None and not args.strict:
        return
    results = args.results or os.path.join(ROOT, "results")
    print("\nFresh runs vs expected:")
    print("| scenario | k | placement | avg started exp/new | p80 exp/new | non-started exp/new | status |")
    print("|---|---|---|---|---|---|---|")
    bad = 0
    compared = 0
    for r in rows:
        scen, k = r["scenario"], int(r["k"])
        alg = args.baseline if r["placement"] == "random" else r["placement"]
        path = os.path.join(results, f"{scen}_k{k}_{alg}.json")
        if not os.path.exists(path):
            continue
        compared += 1
        e = exp[(scen, k, r["placement"])]
        a = metrics(path)
        ok = all(a[key] is not None and
                 abs(a[key] - e[key]) <= args.tolerance / 100 * max(1, e[key])
                 for key in ("mean_started", "p80"))
        bad += 0 if ok else 1
        print(f"| {scen} | {k} | {r['placement']} | {fmt(e['mean_started'])}/{fmt(a['mean_started'])} | "
              f"{fmt(e['p80'])}/{fmt(a['p80'])} | {fmt(e['failed_pct'])}/{fmt(a['failed_pct'])} | "
              f"{'OK' if ok else 'DIFF'} |")
    missing = len(rows) - compared
    print(f"\n{compared}/{len(rows)} runs compared; {missing} missing; "
          f"{bad} outside ±{args.tolerance:.0f}% on mean/p80")
    if args.strict and (missing or bad):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

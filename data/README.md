# Data

## Topologies

| File | Nodes | Unique links | Edge entries | Units | Role |
|---|---|---|---|---|---|
| `data/topologies/garr-topology1` | 70 | 111 | 126 | bits/sec | **paper GARR topology** |
| `data/topologies/random-graph1` | 100 | 243 | 243 | 1 Gbps per link | **paper random topology** |

The GARR capacities are stored in bits per second and converted to Mbps by the simulator. The Figure 3 GARR runs apply `netLimit=0.1`, which gives each link 10% of its listed capacity. The random topology uses the full listed capacity.

## Workloads

- `garr_deadtime_600_random_1hour.json` — GARR, random baseline, 1 h.
- `garr_deadtime_600_heuristic_1hour.json` — GARR, PESS schedule, 1 h.
- `random_deadtime_600_random_1hour.json` — random topology, 1 h.
- `garr_deadtime_600_random_10min.json` — GARR, 10-min smoke test.
- `random_deadtime_600_random_10min.json` — random topology, 10-min smoke test.
- `garr_deadtime_600_heuristic_1hour_k8_100g.json` — the original `garr_deadtime_600_heuristic_10min.json`; it is a 1-hour k=8 scenario with explicit 100 Gbps registries, not a 10-minute workload.

Cold-cache effects can make the smoke-test results differ from the one-hour runs.

## Placements

`placements/fluidc/communities_k{1,2,4,8}_{garr-topology1,random-graph1}.txt` contains the stored FluidC registry sets, one node per line.

The paper's random baseline was a uniform draw. The [report manifest](../expected/manifest.csv) records the sets recovered from the archived `src` values for both placements. The original order and seed remain unknown. By default, `run_all.py` uses the recovered sets. Pass `--random-seed` to draw a fresh baseline.

## Runnable Copy

The runnable copy defers the Basemap import and accepts explicit registry lists. It also restores the solver's one-registry result and provides a convergence fallback.

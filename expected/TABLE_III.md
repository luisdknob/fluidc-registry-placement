# Submission-only statistics

Table III appeared in the submitted IC2E manuscript. This comparison uses the available `container_time` reports from the archive.

Mean deployment time is calculated over started containers, including cache hits. The request standard deviation is the sample standard deviation of the per-registry request counts from `src`.

See the [CSV](table3_verified.csv). To regenerate it, run `python scripts/make_table3.py` from the repository root.

## Recalculated values

| Scenario | Placement | k | Deployments | Non-started | Avg started (s) | StdDev req. |
|---|---|---|---|---|---|---|
| GARR Random | Random | 1 | 19649 | 47.86% | 273.62 | — |
| GARR Random | Random | 2 | 19649 | 44.64% | 207.80 | 10820.86 |
| GARR Random | Random | 4 | 19649 | 38.09% | 106.39 | 5694.05 |
| GARR Random | Random | 8 | 19649 | 33.42% | 75.65 | 3882.00 |
| GARR Random | FluidC | 1 | 19649 | 47.86% | 273.62 | — |
| GARR Random | FluidC | 2 | 19649 | 44.35% | 132.72 | 5831.51 |
| GARR Random | FluidC | 4 | 19649 | 31.34% | 45.42 | 857.27 |
| GARR Random | FluidC | 8 | 19649 | 7.93% | 15.89 | 897.23 |
| GARR PESS | Random | 1 | 19129 | 41.62% | 75.15 | — |
| GARR PESS | Random | 2 | 19129 | 36.19% | 64.93 | 11857.47 |
| GARR PESS | Random | 4 | 19129 | 24.95% | 46.06 | 7046.50 |
| GARR PESS | Random | 8 | 19129 | 18.09% | 38.25 | 4835.66 |
| GARR PESS | FluidC | 1 | 19129 | 41.62% | 75.15 | — |
| GARR PESS | FluidC | 2 | 19129 | 25.63% | 49.91 | 8556.70 |
| GARR PESS | FluidC | 4 | 19129 | 3.26% | 16.34 | 3307.90 |
| GARR PESS | FluidC | 8 | 19129 | 0.89% | 7.76 | 2111.78 |
| Random Topology | Random | 1 | 19790 | 19.37% | 21.43 | — |
| Random Topology | Random | 2 | 19790 | 1.12% | 5.14 | 3583.62 |
| Random Topology | Random | 4 | 19790 | 0.00% | 2.09 | 1088.45 |
| Random Topology | Random | 8 | 19790 | 0.00% | 1.53 | 1371.55 |
| Random Topology | FluidC | 1 | 19790 | 13.26% | 13.46 | — |
| Random Topology | FluidC | 2 | 19790 | 0.13% | 3.31 | 929.14 |
| Random Topology | FluidC | 4 | 19790 | 0.00% | 1.81 | 1065.87 |
| Random Topology | FluidC | 8 | 19790 | 0.00% | 1.34 | 385.30 |

`—` = one registry, so the StdDev is undefined.

## Comparison with the submission

- The largest difference in mean deployment time is 0.33 s for GARR Random with four randomly placed registries, at 106.39 s from the archive and 106.72 s in the submission.
- The largest difference in the non-started rate is 1.1 percentage points in the GARR PESS workload.
- The recalculated standard deviations are within 0.05 of the submission values.

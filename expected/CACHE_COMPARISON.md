# IC2E 2021 cache and simulator comparison

The experiment compares the paper-era FIFO simulator on `main` with the LRU variant and simulator fixes on `cache-fixed`. Both branches ran the 24 Figure 3 configurations with the same recovered registry sets, one-hour workloads, topology, bandwidth cap, 600 MB cache, three concurrent downloads, and simulator seed 1. Each configuration was run once per branch using Python 3.9.6 on macOS arm64.

Each cell shows the result on **main / cache-fixed**. The mean includes started containers. The percentiles use the Figure 3 filter, which excludes cache hits and includes missed deadlines. Requests per registry SD is the sample standard deviation of request counts. The [submission comparison](TABLE_III.md) lists the corresponding archived measurements.

## Findings

- FluidC had a lower mean deployment time and p80 in ten of the twelve placement comparisons. The two GARR cases with one registry tied.
- The placement ordering was also the same across both branches for non-started rates, p95, and request standard deviation. The random baseline had a lower p95 with one registry on the random topology, as it did in the archive.
- The largest relative change in a mean deployment time was 5.98% (GARR PESS, random placement, eight registries, 38.54 s to 36.23 s). The largest absolute p80 change was 14.38 s in GARR Random with one registry.
- On the random topology, all containers started with four and eight registries in both branches. On GARR with two FluidC registries, the corrected non-started rates were 44.47% with the random scheduler and 24.16% with PESS.

## Rerun the comparison

Run this command in a checkout of `main` with the README environment.

```bash
python scripts/run_all.py --workers 4 --outdir results/main-fifo
```

Run this command in a checkout of `cache-fixed`.

```bash
python scripts/run_all.py --workers 4 --cache-policy LRU --outdir results/fixed-lru
```

The batch records the report name, registry pool, and bandwidth cap. To inspect the metrics for one case, pass its report to `scripts/compare_cache.py` with the corresponding scenario, placement, and registry count.

## GARR Random

| Registries | Placement | Mean started (s) | Non-started (%) | p80 (s) | p95 (s) | Requests per registry SD |
| :---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | FluidC | 273.62 / 272.49 | 47.86 / 47.63 | 338.22 / 352.61 | 773.48 / 772.37 | — / — |
| 1 | Random | 273.62 / 272.49 | 47.86 / 47.63 | 338.22 / 352.61 | 773.48 / 772.37 | — / — |
| 2 | FluidC | 131.71 / 132.03 | 44.38 / 44.47 | 122.85 / 123.40 | 447.64 / 446.83 | 5881.01 / 5881.01 |
| 2 | Random | 208.82 / 207.75 | 44.43 / 44.57 | 287.37 / 274.76 | 670.76 / 671.10 | 10836.41 / 10836.41 |
| 4 | FluidC | 45.54 / 45.38 | 31.60 / 31.41 | 82.93 / 83.03 | 119.36 / 119.13 | 855.44 / 855.44 |
| 4 | Random | 106.16 / 105.64 | 38.09 / 38.02 | 99.09 / 99.11 | 411.48 / 410.92 | 5700.94 / 5700.94 |
| 8 | FluidC | 15.98 / 16.06 | 7.99 / 7.83 | 33.11 / 33.89 | 71.24 / 71.16 | 887.19 / 887.19 |
| 8 | Random | 75.28 / 76.38 | 33.49 / 33.41 | 96.41 / 96.49 | 329.50 / 335.09 | 3872.67 / 3872.67 |

## GARR PESS

| Registries | Placement | Mean started (s) | Non-started (%) | p80 (s) | p95 (s) | Requests per registry SD |
| :---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | FluidC | 75.15 / 72.63 | 41.62 / 41.11 | 177.81 / 177.02 | 275.05 / 270.39 | — / — |
| 1 | Random | 75.15 / 72.63 | 41.62 / 41.11 | 177.81 / 177.02 | 275.05 / 270.39 | — / — |
| 2 | FluidC | 49.26 / 47.98 | 24.96 / 24.16 | 124.07 / 123.44 | 194.15 / 193.39 | 8546.80 / 8546.80 |
| 2 | Random | 64.98 / 63.91 | 36.31 / 35.65 | 166.69 / 167.49 | 250.35 / 254.43 | 11826.36 / 11826.36 |
| 4 | FluidC | 16.36 / 16.00 | 3.24 / 3.08 | 37.96 / 37.21 | 58.86 / 57.59 | 3317.93 / 3317.93 |
| 4 | Random | 46.64 / 45.65 | 25.15 / 24.63 | 126.54 / 126.86 | 197.24 / 196.77 | 7048.82 / 7048.82 |
| 8 | FluidC | 7.69 / 7.67 | 0.91 / 0.83 | 15.95 / 16.00 | 33.46 / 33.57 | 2098.14 / 2098.14 |
| 8 | Random | 38.54 / 36.23 | 18.41 / 17.16 | 102.36 / 100.93 | 163.76 / 160.86 | 4838.81 / 4838.81 |

## Random topology

| Registries | Placement | Mean started (s) | Non-started (%) | p80 (s) | p95 (s) | Requests per registry SD |
| :---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | FluidC | 13.46 / 13.53 | 13.26 / 13.30 | 45.93 / 46.44 | 113.05 / 114.25 | — / — |
| 1 | Random | 21.43 / 21.67 | 19.37 / 19.29 | 75.61 / 75.71 | 95.64 / 95.92 | — / — |
| 2 | FluidC | 3.25 / 3.28 | 0.07 / 0.10 | 5.96 / 5.95 | 12.77 / 13.03 | 931.97 / 931.97 |
| 2 | Random | 4.56 / 4.66 | 0.73 / 0.67 | 7.63 / 7.68 | 23.61 / 24.09 | 3553.92 / 3553.92 |
| 4 | FluidC | 1.82 / 1.81 | 0.00 / 0.00 | 3.20 / 3.20 | 5.11 / 5.08 | 1075.06 / 1075.06 |
| 4 | Random | 2.00 / 1.99 | 0.00 / 0.00 | 3.52 / 3.51 | 5.76 / 5.73 | 1566.56 / 1566.56 |
| 8 | FluidC | 1.33 / 1.33 | 0.00 / 0.00 | 1.77 / 1.78 | 3.20 / 3.20 | 378.93 / 378.93 |
| 8 | Random | 1.54 / 1.54 | 0.00 / 0.00 | 2.58 / 2.59 | 4.22 / 4.23 | 1448.65 / 1448.65 |

## FIFO and LRU Control

The one-hour GARR Random FluidC control with four registries and 600 MB compares FIFO and LRU on `cache-fixed`.

| Metric | Archived run (FIFO) | FIFO control | LRU |
| --- | ---: | ---: | ---: |
| Mean deployment time | 45.42 s | 45.50 s | 45.38 s |
| Non-started | 31.34% | 31.60% | 31.41% |
| Cache hits | 6,726 | 6,680 | 6,740 |
| Failed | 6,158 | 6,210 | 6,171 |
| Request standard deviation | 857.27 | 855.44 | 855.44 |
| p80 | 82.84 s | 82.96 s | 83.03 s |
| p95 | 118.48 s | 119.66 s | 119.13 s |

In this control, LRU reduced the mean by 0.12 s and the non-started rate by 0.20 percentage points. It added 60 cache hits and reduced failures by 39.

## Additional Simulator Fixes

| Location | Paper version | Fixed version |
| --- | --- | --- |
| `topology.py::__control_cache` | Evicts one entry | Evicts until there is capacity |
| `topology.py::running_messages` | Removes entries from the list during iteration | Iterates over a copy |
| `topology.py::calculate_network_traffic` | Can advance by a non-positive time step | Guards the step |
| `json.py` | Ignores seed 0 | Accepts seed 0 |
| `json.py::create_interfaces` | Adds a reverse edge when `bidirectional` is present and false | Checks the boolean value |
| `solver.py` | Uses an implicit seed | Accepts an optional seed |
| `report.py::registry_usage` | Starts the count at zero on the first request | Counts the first request |
| `report.py::host_occupation` | Divides by zero on some cache hits | Reports zero bandwidth for zero duration |
| `json.py::scheduling_app` | Resets a local list and can loop indefinitely | Clears the caller's list |

In the paper version, `finish_messages` leaves the success status at 0. Figure 3 uses the `downloaded` field to identify completed downloads.

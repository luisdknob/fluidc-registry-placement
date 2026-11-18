# Archived Figure 3 data

The archived `container_time` reports are the original inputs used to draw Figure 3.

| Folder | Figure | Source prefix |
|---|---|---|
| `fig3a_garr_random` | 3a, GARR random baseline | `garr_deadtime_600_random_1hour-container_time_*` |
| `fig3b_garr_pess` | 3b, GARR PESS | `garr_deadtime_600_heuristic_1hour-container_time_*` |
| `fig3c_random_topology` | 3c, random topology | `random_deadtime_600_random_1hour-container_time_*` |

File index mapping:

| Index | Registries | Placement |
|---|---|---|
| 9 | 1 | FluidC |
| 10 | 1 | random baseline |
| 1 | 2 | FluidC |
| 2 | 2 | random baseline |
| 3 | 4 | FluidC |
| 4 | 4 | random baseline |
| 6 | 8 | FluidC |
| 8 | 8 | random baseline |

Each JSON has a `containers` list with `name, src, dst, downloaded, download_time`.

`downloaded`: 0 = deadline missed, 1 = downloaded, 2 = cache hit.

The CDF excludes cache hits and includes deadline misses at their recorded failure time.

[`manifest.csv`](manifest.csv) records the scenario, registry count, placement, and CDF metrics. Its mean includes deadline misses and follows the CDF filter.

## Submission-only statistics

The submitted manuscript included a separate table of mean deployment time for started containers, non-started counts, and registry request variation. The [submission comparison](TABLE_III.md) and [CSV](table3_verified.csv) preserve that analysis. The CSV columns prefixed with `paper_` refer to that submitted table. To regenerate the CSV, run `python scripts/make_table3.py` from the repository root.

## Archived Replay

On `main`, all six one-registry configurations reproduced the archived report records. For GARR Random with two FluidC registries, the archived set is `PA1,RM2`. Seed 1 gives a Figure 3 p80 of 122.85 s, compared with 122.35 s in the archive.

Registry order affects tie-breaking in the multi-registry runs. The recovered registry sets are in the report manifest. The original order and random seed remain unknown, so the batch uses the recovered sets and a fixed seed for fresh runs.

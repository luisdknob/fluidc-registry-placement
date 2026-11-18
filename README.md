# Community-based Placement of Registries to Speed Up Application Deployment on Edge Computing

This repository contains the ContainerSim experiments for IC2E 2021. The study uses FluidC to partition an edge network and place a container registry in each community. It compares that placement with a uniform random baseline.

Luis Augusto Dias Knob, Francescomaria Faticanti, Tiago Ferreto, and Domenico Siracusa (2021). *Community-based Placement of Registries to Speed Up Application Deployment on Edge Computing*. IEEE International Conference on Cloud Engineering. [Paper](https://doi.org/10.1109/IC2E52221.2021.00029)

## Release Note

> [!NOTE]
> This post-publication release is part of an ongoing effort to improve the reproducibility and verifiability of my research. For this paper, I am making the source code and experimental configurations publicly available. I plan to gradually release artifacts from more of my research projects over time.
>
> I used GPT-6.2 Sol and DeepSeek V4.1 Flash 1017 to help prepare this repository, fix minor execution issues, and review the code and results against the published paper. I kept the code here as close as possible to the implementation used in the original experiments.
>
> I used a random function to break ties between registries. I didn’t set a seed for the original runs, so the simulator used the current time. If you run the experiments again, the overall results can be similar even if some requests go to different registries and take a different amount of time. See [Archived Replay](#archived-replay) for how the new runs compare with the originals.
>
> I documented minor corrections and clarifications in the [errata](ERRATA.md). The results still support the paper’s main conclusions.

## Simulation Scenario

The experiments use 13 container images of 200 MB each and evaluate both placements with 1, 2, 4, and 8 registries.

| Figure | Topology | Application schedule | Link bandwidth used |
| --- | --- | --- | --- |
| 3a | GARR | Random | 10% |
| 3b | GARR | PESS | 10% |
| 3c | Random topology | Random | 100% |

The PESS experiment uses a precomputed schedule from *Progressive Embedding of Security Services* on the 70-node GARR topology. The schedule is included. For details on the scheduling algorithm, see the [PESS paper](https://doi.org/10.1109/TNSM.2019.2941128).

### Dataset

- The [original source archive](archive/ic2e-original-source.zip) includes the paper-era simulator, the recovered solver copies, and the original Figure 3 plotting script.
- The [archived Figure 3 reports](expected/README.md) contain the original container timing data. The [manifest](expected/manifest.csv) identifies the report and recovered registry set for each configuration.
- The [original simulator logs](archive/ic2e-original-logs.zip) include the 13 detailed logs matched to Figure 3 reports and an index of the matches.
- The runnable copy uses the included [topologies, workloads, and FluidC placements](data/README.md). The [data notes](data/README.md#runnable-copy) describe its compatibility adjustments.

### Settings and Execution

From the repository root, install the dependencies with Python 3.9. Python 3.10 is also supported by the pinned stack.

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run a ten-minute GARR Random smoke test with four FluidC registries. The run uses a 600 MB cache (`--storage 4800` in Mb) and the default of three concurrent downloads.

```bash
python scripts/run_experiment.py \
  --name smoke_garr_random_k4 \
  --topo data/topologies/garr-topology1 \
  --workload data/workloads/garr_deadtime_600_random_10min.json \
  --registries BO1,PA1,NA1,RM2 \
  --netlimit 0.1 \
  --storage 4800
```

The report is written to `results/` and the run log to `logs/runs/`. Run the 24 one-hour configurations using the recovered registry sets and simulator seed 1.

```bash
python scripts/run_all.py --workers 4
python scripts/plot_fig3.py --source results
python scripts/validate.py --results results --strict
```

A one-hour GARR run can take 15–20 minutes on one core. The `--quick` option uses the shorter workloads and skips GARR PESS. To sample a new baseline, pass `--random-seed 1` to the runner and `--baseline uniform_s1` to the plotter and validator. Strict validation requires all 24 reports and checks the mean and p80 against the archive.

### Results

Rebuild the published Figure 3 from the archived reports.

```bash
python scripts/plot_fig3.py
python scripts/validate.py
```

The [Figure 3 data and replay notes](expected/README.md) explain the plot filter and how fresh runs compare with the archive.

The paper version on `main` uses FIFO. The `cache-fixed` branch defaults to LRU and provides `--cache-policy FIFO` for a control within that branch. The branch comparison is in `expected/CACHE_COMPARISON.md` on `cache-fixed`.

### Archived Replay

All six one-registry configurations reproduced the archived report records on `main`. The order of the registries also affects how ties are broken. See the [replay notes](expected/README.md#archived-replay) for the comparison with the archived results.

## Citation

```bibtex
@inproceedings{knob2021registries,
  author    = {Dias Knob, Luis Augusto and Faticanti, Francescomaria and Ferreto, Tiago and Siracusa, Domenico},
  title     = {Community-based Placement of Registries to Speed Up Application Deployment on Edge Computing},
  booktitle = {2021 IEEE International Conference on Cloud Engineering (IC2E)},
  year      = {2021},
  doi       = {10.1109/IC2E52221.2021.00029}
}
```

## License

The code is released under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE).

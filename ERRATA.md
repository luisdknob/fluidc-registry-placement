# IC2E 2021 Errata

These corrections refer to the published version of [Community-based Placement of Registries to Speed Up Application Deployment on Edge Computing](https://doi.org/10.1109/IC2E52221.2021.00029).

## Algorithm 1

- In lines 11–13, update `sd` to the new best bandwidth standard deviation before resetting the counter.
- In line 20, include only edges with both endpoints in `V_k`.
- In lines 21–24, compute eigenvector centrality once for the community and select the node with the highest score.

## Simulation Setup

- Section V-B describes the random topology as “fully connected”. The intended term is “connected”. The archived inputs contain 243 unique undirected links for the random topology and 111 for GARR. Section V-B reports 242 and 112, respectively. [Topology files](data/README.md#topologies)
- The 1 Gbps worker link setting in Table II applies to the random topology. The GARR runs use the link-specific capacities in the topology file, scaled to 10% as described in Section V-B. [Topology files](data/README.md#topologies)
- Section V-B and Table II describe an LRU cache. In the paper version, hits leave the insertion timestamp unchanged, so eviction follows FIFO. [Cache implementation in the paper version](code/classes/topology.py)
- Section V-C gives 25 s as the minimum deadline. The archived workloads include shorter intervals from arrival to deadline, down to about 15 s in the two random schedules and 2.53 s in the PESS schedule. [Workload files](data/README.md#workloads)

## Figure 3 and Section V-D

- Figure 3 excludes cache hits and includes deadline misses at the time the simulator recorded the failure. This defines which records contribute to the deployment-time CDF. [Archived Figure 3 reports](expected/README.md)
- For the GARR random scheduler in Figure 3a, both placements reach 80% below 100 s at four registries. At one and two registries, the 80th percentile exceeds 100 s for both placements. [Figure 3 data](expected/manifest.csv)
- Section V-D.2 reports that 67% of the PESS deployments were scheduled on six workers. The six busiest workers in the archived schedule receive 63.0% of the deployments. [Archived PESS schedule](data/workloads/garr_deadtime_600_heuristic_1hour.json)
- In the PESS comparison in Section V-D.2, “than in the random scheduler” should read “than with random registry placement”. Both curves in each comparison in Figure 3b use the PESS scheduler.
- Section V-D.2 reports average gains of 32% and 71% at four and eight registries. The arithmetic means of the individual deployment-time reductions printed in that section are 68% for the random scheduler and 72.5% for PESS.

## Conclusion

The statement in Section VI about few non-started containers with two FluidC registries applies to the random topology. Both GARR workloads still have substantial numbers of non-started containers at that registry count. [Archived Figure 3 reports](expected/manifest.csv)

These corrections leave the paper’s main conclusion intact. FluidC reduced deployment time compared with random registry placement in the evaluated scenarios with two, four, and eight registries. [Figure 3 data](expected/manifest.csv)

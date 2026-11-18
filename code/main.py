#import simpy as sim
import networkx as nx
import matplotlib.pyplot as plt 
import time
import sys
import json
import logging as log
import pathlib
import argparse
import time
import statistics
import operator

import classes.topology as ct
import classes.application as ca
import classes.json as js
import classes.draw as dr
import classes.report as rp

def __maxmin_fairness(sP, sA, C, links):
    # sP - list of transfers
    # sA - list of arcs
    # C - dictionary with capacities of each arc
    # links - list of tuples, each tuple (i,j) indicates that transfer i uses arc j

    # k -> step
    k = 1 # initiated at 1

    # A[k] -> set of non saturated arcs at the beginning of step k
    A = dict([(k,sA)])

    # P[k] -> set of sessions not passing through any saturated arc at the beginning of step k
    P = dict([(k,sP)])

    # n[k][a] -> number of sessions using arc a that are in P[k]
    n = dict()

    # rt[k] -> increment of rate added to all session in P[k]
    rt = dict()

    # r[k][p] -> allocated rate on session p at step k
    r = dict([ ((0,p),0) for p in sP])

    # F[k][a] = allocated flow on arc a at step k
    F = dict([ ((0,a),0) for a in sA])

    # delta[p][a] = matrix where [p][a] = 1 if arc is in path p, 0 otherwise
    delta = dict([ ((p,a),0) for p in sP for a in sA ])
    delta.update( dict([ (l,1) for l in links ]) )

    while(len(P[k]) != 0) :

        # 1. n[k][a] := number of paths p in P[k] with delta[p][a] = 1
        n.update( dict([ ((k,a),len([ p for p in P[k] if delta[p,a] == 1 ])) for a in sA ]) )

        # 2. rt[k] := min( (C[a]-F[k-1][a])/n[k][a] forall a in A[k] and n[k][a] > 0)
        rt[k] = min([ float(C[a]-F[k-1,a])/n[k,a] for a in A[k] if n[k,a] > 0 ])

        # 3. r[k][p] := if p in P[k], then r[k-1][p] + rt[k] else r[k-1][p]
        r.update( dict([ ((k,p), r[k-1,p]+(lambda x: (x in P[k] and rt[k]) or 0)(p)) for p in sP]))

        # 4. F[k][a] := sum{p in P} delta[p][a] * r[k][p]
        F.update( dict([ ((k,a),sum([ delta[p,a]*r[k,p] for p in sP ])) for a in sA ]) )
        
        # 5. A[k+1] := {a|C[a]-F[k][a] > 0}
        A[k+1] = [ a for a in sA if C[a]-F[k,a] > 0 ]

        # 6. P[k+1] := {p|delta[p][a] = 0, forall a notin A[k+1]}
        saturated_links = [ (p,all( [delta[p,a] == 0 for a in sA if a not in A[k+1]] )) for p in sP]
        P[k+1] = [ p for (p,cond) in saturated_links if cond ]

        # 7. k := k+1
        k = k+1

        # 8. if P[k] is empty, then stop, else goto 1
    
    return dict([ (p,r[k-1,p]) for p in sP ])

def parse_args(parser):
    parser.epilog = "ContainerSim v0.01"
    parser.add_argument("--debug", help="enable DEBUG log", action="store_true")
    parser.add_argument("--seed", type=int, default=None, help="set the random seed")
    parser.add_argument("--netLimit", type=float, default=1.0, help="set the limit to network bandwidth")
    parser.add_argument("--topo", help="import a topology file")
    parser.add_argument("--options", type=json.loads, default={}, help="Complimentary options to deploy the topology")
    parser.add_argument("--file", help="import a configuration file")
    parser.add_argument("--draws", nargs="+", help="list of graphics that want to be generate after the simulation")
    parser.add_argument("--reports", nargs="+", help="list of logs that want to be generate after the simulation")
    parser.add_argument("--psch", help="list of logs that want to be generate after the simulation")

    return parser.parse_args()

def main():

    start_time = time.time()

    log.basicConfig(filename="logs/log_"+str(int(time.time()))+".log",
                            filemode='a', format='%(levelname)s - %(message)s', level=log.INFO)
    
    args = parse_args(argparse.ArgumentParser())
    messages = []

    if args.debug:
        logHandler = log.getLogger()
        logHandler.setLevel(log.DEBUG)

    if args.topo:
        filename = pathlib.Path(args.topo)
    
        with open(filename, "r") as file:
            nodes, edges = js.import_topology(file, args.options)
    
    if args.file:
        filename = pathlib.Path(args.file)
        with open(filename, "r") as file:
                json_file = json.load(file)
                if args.topo:
                    nodes_json, edges_json, messages = js.import_config(json_file, nodes, args.seed)
                    nodes.extend(nodes_json)
                    edges.extend(edges_json)
                else:
                    nodes, edges, messages = js.import_config(json_file)
        
    if not (nodes and messages and edges):
        print(messages)
        #return False


    # Create infrastructure graph
    infra = ct.Topology(nodes, edges)

    # final_alg = None
    # iter_round = 0
    # pstdev = sys.maxsize
    # while(True):
    #     alg = nx.algorithms.community.asyn_fluidc(infra.topo.to_undirected(reciprocal=True), 3, max_iter=100)
    #     band = []
    #     round_alg = list(alg)
    #     error = False
    #     for b in round_alg:
    #         band_round = 0
    #         h = infra.topo.subgraph(b)
    #         if not nx.is_strongly_connected(h):
    #             print("error")
    #             error = True
    #             break
    #         for edge in h.edges(data=True):
    #             band_round += edge[2]["bandwidth"]
    #         band.append(band_round)
    #     if error:
    #         iter_round+=1
    #         continue
    #     round_stdev = statistics.stdev(band)
        
    #     #print(nx.average_node_connectivity(h))
    #     if round_stdev < pstdev:
    #         #print(round_stdev)
    #         pstdev = round_stdev
    #         final_alg = round_alg
    #         iter_round = 0
    #     else:
    #         iter_round+=1
    #     if iter_round >= 100:
    #         break    
    
    # for community_index, community_members in enumerate(final_alg):
    #     sub_g = infra.topo.subgraph(community_members)
    #     centrality_sub = nx.eigenvector_centrality(sub_g)
    #     cen_sorted = sorted(centrality_sub.items(), key=operator.itemgetter(1), reverse=True)
    #     print([(infra.topo.nodes[element[0]]["name"], element[1]) for element in cen_sorted])
    
    # #print(final_alg)
    # for group, b in enumerate(final_alg):
    #     h = infra.topo.subgraph(b)
    # #print(infra.topo.nodes(data=True))
    #     sources = []
    #     for node in h.nodes(data=True):
    #             n = node[1].copy()
    #             n["id"] = node[0]
    #             sources.append(n)
    #     #print(sources)

    #     result = []
    #     for source in sources:
    #         sA = []
    #         C = {}
    #         sP = []
    #         links = []

    #         all_nodes = nx.single_source_dijkstra(h, source["id"], weight="inverse_bandwidth")
    #         if not all_nodes:
    #             continue

    #         for id, path in all_nodes[1].items():
    #             #if infra.topo.nodes[id]["type"] == "registry":
    #             #    continue
    #             if id == source["id"]:
    #                 continue
    #             sP.append(id)
    #             for index, node in enumerate(path[:-1]):
    #                 arc = h[node][path[index+1]]
    #                 links.append((id,arc["id"]))
    #                 if arc["id"] not in sA:
    #                     sA.append(arc["id"])
    #                     C[arc["id"]] = arc["bandwidth"]*args.netLimit
    #         #print(sA, C, sP, links)
    #         a = __maxmin_fairness(sP, sA, C, links)
    #         sum_val = sum([b for b in a.values()])/len(a)
                    
    #         result.append((source["name"], sum_val))
        
    #     print("group %d"%(group+1))
    #     group = []
    #     for c in sorted(result,key=lambda item: item[1], reverse=True):
    #         group.append(c[0])
    #         #print(c[0],c[1])
    #     print(group)
    # # #print(all_nodes)
    
    # #dr.map(infra.topo, filename.stem)

    #return False

    #mst = infra.mst()
    #cent = 0
    #nd = None
    #for node,value in nx.degree_centrality(infra.topo).items():
    #    if cent < value:
    #        cent=value
    #        nd = node
    #infra.topo.nodes[nd]["type"] = "registry"
    #print(infra.topo.nodes[nd])
    #dr.map(infra.topo, filename.stem)

    #Insert messages on the infrastructure
    infra.add_messages(messages)
    #infra.scheduling_messages(args.psch)

    # Start simulation time
    sec = 0.0

    log.info("Start Simulation")

    infra.run_simulation(sec, args.netLimit)

    #print("Error Messages: %d\nInstalled Messages:%d " % (len(infra.error_messages),len(infra.installed_messages)))

    log.info("Finish Simulation")
    log.info("Total Time: %.2f" % sec)

    if args.draws:
        if "map" in args.draws:
            dr.map(infra.topo, filename.stem)
        if "containerInstTime" in args.draws:
            dr.container_instantiantion_time(infra.installed_messages, filename.stem)
        if "containerMaxMinInstTime" in args.draws:
            dr.container_instantiantion_maxmin_time(infra.installed_messages, filename.stem)
    
    if args.reports:
        if "hostOccupation" in args.reports:
            rp.host_occupation(infra.installed_messages, infra.topo, filename.stem)
        if "timePerApp" in args.reports:
            rp.time_per_app(infra.installed_messages, infra.topo, filename.stem)
        if "cacheStatus" in args.reports:
            rp.cache_status(infra.topo, filename.stem)
        if "chainTime" in args.reports:
            rp.chain_time(infra.installed_messages+infra.error_messages, filename.stem)
        if "networkLog" in args.reports:
            rp.network_log(infra.netstat, infra.topo, filename.stem)
        if "registryUsage" in args.reports:
            rp.registry_usage(infra.installed_messages+infra.error_messages, infra.topo, filename.stem)
        if "containerTime" in args.reports:
            rp.container_instantiation_time(infra.installed_messages+infra.error_messages, infra.topo, filename.stem)

    print(time.time()-start_time)

if __name__ == "__main__":
    main() 

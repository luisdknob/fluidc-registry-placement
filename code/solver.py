# to run the solver ".\solver.py folder\topology_file n_comm"

import networkx as nx
import operator
import random
import sys
import pathlib
import statistics

#@s: file directory
def net_init(s):
	
    g = nx.DiGraph()

    with open(s, 'r') as f:
        
        for line in f:
            lineArray = line.rstrip().split(" ")

            # try add line as node
            try:
                if len(lineArray) > 1:
                    pos = (float(lineArray[2]), float(lineArray[1]))
                else:
                    pos = (0,0)

                # add node to graph 
                g.add_node(lineArray[0], pos=pos)
            
            # if second value can't be convert to float, line is edge
            except ValueError:
                
                # convert bandwidth to megabits
                band = float(lineArray[2])/1000000

                # add edge to graph
                g.add_edge(lineArray[0], lineArray[1], band=band)
                g.add_edge(lineArray[1], lineArray[0], band=band)
    
    return g

#@n: number of communities
#@g: networkx graph
def fluid_communities(g,n):
    final_communities = None
    iter_round = 0
    stdev = sys.maxsize
    
    while(True):
        #run the fluid communities algorithm
        round_communities = list(nx.algorithms.community.asyn_fluidc(g.to_undirected(reciprocal=True), n, max_iter=100))
        band_round = []
        error = False
        for community in round_communities:
            band_community = 0
            sub_g = g.subgraph(community)

            #test if the subgraph is connected, if not rerun the algorithm
            if not nx.is_strongly_connected(sub_g):
                error = True
                break

            # create an array with all communities total available bandwidth
            for edge in sub_g.edges(data=True):
                band_community += edge[2]["band"]
            band_round.append(band_community)

        if error:
            continue

        # COMPATIBILITY PATCH (IC2E-2021 snapshot): a single community has
        # no standard deviation; the paper-era solver returned it directly.
        if n == 1:
            final_communities = round_communities
            break

        # test if the standard deviation from the round communities are smaller than the previous save
        round_stdev = statistics.stdev(band_round)
        if round_stdev < stdev:
            stdev = round_stdev
            #if smaller, change the final communities and reset iterations count
            final_communities = round_communities
            iter_round = 0
        else:
            iter_round += 1
        if iter_round >= 100:
            break

    return final_communities

#read topology file
filename = pathlib.Path(sys.argv[1])
#read n number of communities
n = int(sys.argv[2])
#optional seed: python solver.py topology k [seed]
if len(sys.argv) > 3:
    random.seed(int(sys.argv[3]))
#start the graph
g = net_init(filename)

with open("communities_k%d_%s.txt" % (n,filename.stem),"w") as f:
    for community_members in fluid_communities(g, n):
            sub_g = g.subgraph(community_members)
            #run the centrality to each community
            # COMPATIBILITY PATCH (IC2E-2021 snapshot): power iteration can
            # fail to converge on periodic community subgraphs. Retry with a
            # larger budget, then fall back to the NumPy eigensolver.
            try:
                centrality_sub = nx.eigenvector_centrality(sub_g, max_iter=10000)
            except nx.PowerIterationFailedConvergence:
                centrality_sub = nx.eigenvector_centrality_numpy(sub_g)
            cen_sorted = sorted(centrality_sub.items(), key=operator.itemgetter(1), reverse=True)
            #save on file only the first element of each community
            f.write("%s\n" % (cen_sorted[0][0]))
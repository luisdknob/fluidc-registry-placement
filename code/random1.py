import networkx as nx
import matplotlib.pyplot as plt
import random

#l = [1000,10000,100000]
l = [1000]

random.seed(11)

a = nx.gnm_random_graph(100,245,11,directed=True)

#print(nx.is_connected(a))

for edge in a.edges(data=True):
    #print(edge)

    link = random.choice(l)
    edge[2]["bandwidth"] = link
    if a.has_edge(edge[1], edge[0]):
        a[edge[1]][edge[0]]["bandwidth"] = link
    else:
        a.add_edge(edge[1],edge[0], bandwidth=link)


for node in a.nodes():
    print("N"+str(node))

edges = []
for edge in a.edges(data=True):
    if (edge[1],edge[0],edge[2]) in edges:
        continue
    else:
        edges.append(edge)
for edge in edges:
    print("N"+str(edge[0]),"N"+str(edge[1]),edge[2]["bandwidth"]*1000000)
#nx.write_yaml(a, "test.yaml")

#nx.draw(a)
#plt.plot()
#plt.savefig("a.jpg")
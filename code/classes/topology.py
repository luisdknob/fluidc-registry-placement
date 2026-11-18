from uuid import uuid1 as uuid
import networkx as nx
import logging as log
import json
import time
import sys
import random

class LCOperationsSchedule:

    @staticmethod
    def max_bandwidth_schedule(messages, topo):
        ordered_messages = messages.copy()
        for message in ordered_messages:
            path_max_bandwidth = 0
            for num, node in enumerate(message.path[:-1]):
                path_max_bandwidth = max(path_max_bandwidth, topo[node][message.path[num+1]]["bandwidth"])
            message.max_bandwidth = path_max_bandwidth
        return sorted(ordered_messages, key=lambda item: item.max_bandwidth, reverse=True)

    @staticmethod
    def common_path_schedule(messages):
        nodes = {}
        ordered_messages = messages.copy()

        for message in ordered_messages:
            for node in message.path:
                if node in nodes.keys():
                    for dep in nodes[node]:
                        if dep not in message.dependencies:
                            message.dependencies.append(dep)
                    nodes[node].append(message.name+"-"+str(message.id))
                else:
                    nodes[node] = []
            print(message.name,message.dependencies)
                    
        return ordered_messages

class Message:

    def __init__(self, **attr):
        self.id = uuid().int
        self.src = None
        self.dst = None
        self.name = ""
        self.arrival_time = 0
        self.deadline_time = sys.maxsize
        self.size = 0
        self.layer = ""
        self.transmitted = 0
        self.chain = 0
        self.dependencies = []
        
        """ 
        message status

        0 - schedule message
        1 - cached message
        2 - error message
        3 - active message
        4 - contained message
        5 - downloaded message 
        """

        self.status = 0
        self.type = "host"
        for var, value in attr.items():
            if var in self.__dict__:
                self.__setattr__(var, value)
        if self.size > 0:
            self.size *= 8
        if attr.get("topo"):
            self.calculate_path(attr.get("topo"))

    def data_to_transmit(self):
        return self.size - self.transmitted

    def transfer_data(self, value):
        if self.transmitted + value > self.size:
            self.transmitted = self.size
        else:
            self.transmitted += value

    def calculate_path(self, topo):
        try:
            if len(self.src) == 1:
                self.src = self.src[0]
            else:
                smaller = (sys.maxsize,None)
                for node in self.src:
                    val = nx.shortest_path_length(topo.topo, source=node, target=self.dst, weight="inverse_bandwidth")
                    if val < smaller[0]:
                        smaller = (val, node)
                    if val == smaller[0]:
                        smaller = random.choice([(val, node),smaller])
                self.src = smaller[1]
            self.path = topo.connection_path(self.src,self.dst)
            if not self.path:
                return False
            return True

        except:
            return False

class Topology:

    def __init__(self, nodes, edges):
        self.topo = nx.DiGraph()
        self.schedule_messages = []
        self.active_messages = []
        self.retained_messages = []
        self.installed_messages = []
        self.error_messages = []
        self.netstat = []
        self.recalculate_network = False
        for node in nodes:
            id = node["id"]
            node.pop("id")
            self.topo.add_node(id,**node)
        
        for src,dst,data in edges:
            self.topo.add_edge(src,dst,**data)

    def mst(self, netLimit=1):
        return nx.minimum_spanning_tree(self.topo, weight="inverse_bandwidth")

    def run_simulation(self, sec, netLimit=1):
        while len(self.schedule_messages):
            self.running_messages(sec)

            sec += self.calculate_network_traffic(netLimit, sec)

            self.finish_messages(sec)

    def connection_path(self, src, dst):
        return nx.shortest_path(self.topo,src,dst,weight="inverse_bandwidth")

    def add_messages(self, messages):
        self.schedule_messages = sorted(messages, key=lambda x: x.arrival_time)

        for message in self.schedule_messages:
            message.calculate_path(self)

    def scheduling_messages(self, policy):
        if policy == "smallfirst":
            self.schedule_messages = sorted(self.schedule_messages, key=lambda item: item.size)
        elif policy == "largefirst":
            self.schedule_messages = sorted(self.schedule_messages, key=lambda item: item.size, reverse=True)
        elif policy == "largebandwidth":
            self.schedule_messages = LCOperationsSchedule.max_bandwidth_schedule(self.schedule_messages, self.topo)
        elif policy == "commonpath":
            self.schedule_messages = LCOperationsSchedule.common_path_schedule(self.schedule_messages)
        
    def running_messages(self, sec):
        # for each new sim time, run on each message that not be installed or failed

        for message in self.schedule_messages:
    
            # if message arrival time bigger than the actual sim time, break the loop

            if message.arrival_time <= sec:

            
                #if message deadline smaller than the sim time, message failed and removed from the schedule list

                if message.deadline_time <= sec:
                    message.status = 2
                    message.start_time = sec
                    message.finish_time = sec
                    self.error_messages.append(message)
                    self.schedule_messages.remove(message)
                    log.info("ST: %.2f - Message %s-%d can't be installed because the deadline is smaller than the current time"% (sec, message.name, message.id%100000000))
                    continue

                # if the same image to the same host are already active put the message on retained and continue

                if any(message.layer == i.layer and message.dst == i.dst for i in self.active_messages):
                    if not message in self.retained_messages:
                        self.retained_messages.append(message)
                    continue

                # if message is already installed on the node, set as installed

                if any(message.layer in i for i in self.topo.nodes[message.dst]["layers"]):
                    message.start_time = sec                    
                    message.finish_time = sec
                    self.installed_messages.append(message)
                    self.schedule_messages.remove(message)
                    self.__control_cache(message.dst, message.layer, message.size, sec)
                    message.status = 1
                    log.debug("ST: %.2f - Message %s-%d download already made, so auto-start"% (sec, message.name, message.id%100000000))
                    if message in self.retained_messages:
                        self.retained_messages.remove(message)
                    continue

                # calculate the number of active messages to a given host

                retained_simultaneous_download = len([True for m in self.active_messages if m.dst == message.dst])

                # if number of active messages on node less than the simultaneousDownload test if message has dependencies, if not, start
                # TO-DO Improve dependencies implementation

                if retained_simultaneous_download < self.topo.nodes(data="simultaneousDownload", default=1)[message.dst]:
                    if len(message.dependencies) > 0:
                        if not all([True if m.name == dep or m.name+"-"+str(m.id) == dep else False for m in self.schedule_messages for dep in message.dependencies]):
                            if not message in self.retained_messages:
                                self.retained_messages.append(message)
                            continue
                    self.recalculate_network = True
                    if message in self.retained_messages:
                        self.retained_messages.remove(message)
                    log.info("ST: %.2f - Message %s-%d started transfer from %s to %s (schedule waiting time - %.2f)" % (sec, message.name, message.id%100000000, self.topo.nodes[message.src]["name"], self.topo.nodes[message.dst]["name"], sec-message.arrival_time))
                    message.start_time = sec
                    self.active_messages.append(message)
                else:
                    if not message in self.retained_messages:
                        self.retained_messages.append(message)
            else:
                break    

    def calculate_network_traffic(self, basetime, sec):

        # calculate minimal arrival time from schedule messages.

        min_arrival_time_waiting = sorted(list(set(self.schedule_messages)-set(self.retained_messages)-set(self.active_messages)), key=lambda x: x.arrival_time)

        # if no active messages, add minimal arrival time or 0.0 to time

        if len(self.active_messages) == 0:
            if len(min_arrival_time_waiting) > 0:
                return min_arrival_time_waiting[0].arrival_time-sec
            else:
                return 0.0

        # if necessary recalculate Maxmin Fairness

        if self.recalculate_network:

            sA = []
            C = {}
            sP = []
            links = []

            for message in self.active_messages:
                for index, node in enumerate(message.path[:-1]):
                        arc = self.topo[node][message.path[index+1]]
                        links.append((message.id, arc["id"]))
                        if arc["id"] not in sA:
                            sA.append(arc["id"])
                            C[arc["id"]] = arc["bandwidth"]*basetime
                sP.append(message.id)

            self.rates = self.__maxmin_fairness(sP, sA, C, links)

            self.recalculate_network = False
            self.netstat.append({"sec":sec, "rates":self.rates, "messages":[ { "id":m.id, "name":m.name, "path":m.path } for m in self.active_messages ]})


        # calculate who is the first flow will finish the transmition with a given rates

        times = { message.id:message.data_to_transmit()/self.rates[message.id] for message in self.active_messages }

        # set the minimum deadline time to active messages

        min_deadline_time = sorted(self.active_messages, key=lambda x: x.deadline_time)

        # discover which value is small between minimum deadline, minimal arrival time and finish flow

        if len(min_arrival_time_waiting):
            time_spend_cycle = min(min(times.values()), min_arrival_time_waiting[0].arrival_time-sec, min_deadline_time[0].deadline_time-sec)
        else:
            if len(min_deadline_time):
                if min_deadline_time[0].deadline_time is not sys.maxsize:
                    time_spend_cycle = min(min(times.values()), min_deadline_time[0].deadline_time-sec)
                else:
                    time_spend_cycle = min(times.values())
            else:
                time_spend_cycle = min(times.values())
  
        # after discover the minimum time spend on cycle, update all flows with the data transmitted

        for id, value in self.rates.items():
            for message in self.active_messages:
                if message.id == id:
                    message.transfer_data(value*time_spend_cycle)
                    break
        
        return time_spend_cycle

    def finish_messages(self, sec):
        new_active = []
        for message in self.active_messages:     
            if message.transmitted >= message.size:
                self.__control_cache(message.dst, message.layer, message.size, sec)
                self.recalculate_network = True
                message.finish_time = sec
                log.info("ST: %02.2f - Message %s-%d transfer %.2f Mbytes from %s to %s and last %.2f seconds" 
                        % (sec, message.name, message.id%100000000, message.size/8, self.topo.nodes[message.src]["name"], self.topo.nodes[message.dst]["name"], sec-message.start_time))
                self.installed_messages.append(message)
                self.schedule_messages.remove(message) 

            elif message.deadline_time <= sec:
                self.recalculate_network = True
                message.finish_time = sec
                log.info("ST: %02.2f - Message %s-%d transfer %.2f Mbytes from %s to %s and last %.2f seconds but don't finish the installation because deadline was smaller than simulation time" 
                        % (sec, message.name, message.id%100000000, message.transmitted/8, self.topo.nodes[message.src]["name"], self.topo.nodes[message.dst]["name"], sec-message.start_time))
                message.status = 2
                self.error_messages.append(message)
                self.schedule_messages.remove(message)                
            else:
                new_active.append(message)
        self.active_messages = new_active
        
    def __control_cache(self, node, layer, size, time):
        node = self.topo.nodes[node]

        if node["storageSize"] == 0.0:
            node["cache"][1] += 1
            return

        if sum([layer[1] for layer in node["layers"]])+size > node["storageSize"] or any(layer in i for i in node["layers"]):
            old = ("", 0, time)
            for cont in node["layers"]:
                if cont[0] == layer:
                    cont = (layer, size, time)
                    node["cache"][0] += 1
                    return
                if old[2] > cont[2]:
                    old = (cont[0], cont[1], cont[2])
            
            log.debug("ST: %02.2f - Remove layer %s from node %s because the cache is full" % (time, old[0], node["name"]))
            try:
                node["layers"].remove(old)
            except:
                print(node["layers"], old, any(layer in i for i in node["layers"]), sum([layer[1] for layer in node["layers"]])+size, node["storageSize"])
        
        log.debug("ST: %02.2f - Add layer %s on node %s cache" % (time, layer, node["name"]))
        node["layers"].append((layer, size, time))
        node["cache"][1] += 1
             

    def __maxmin_fairness(self, sP, sA, C, links):
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

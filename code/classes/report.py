import json
from networkx.readwrite import json_graph
import sys

def time_per_app(messages, topo, filename):
    if not filename:
        filename="simulation"

    messages_plot = {}

    for message in messages:
        if not message.name in messages_plot.keys():
            messages_plot[message.name] = []

        messages_plot[message.name].append(
            {"downloadTime":round(message.finish_time-message.start_time, 2),
            "waitingTime":round(message.start_time-message.arrival_time, 2), 
            "node":topo.nodes[message.path[-1]]["name"],
            "id":message.id})

    jsonFile = {"apps":[]}

    for id, values in messages_plot.items():
        jsonFile["apps"].append({"name":id, "containers":values})
    
    with open("reports/"+filename+'-time_per_app.json', 'w') as fp:
        json.dump(jsonFile, fp)

def host_occupation(messages, hosts, filename):
    messages_per_host = {}
    file = open('reports/'+filename+"-host_occupation.csv", 'w')

    for message in messages:
        if message.path[-1] in messages_per_host.keys():
            messages_per_host[message.path[-1]].append(message)
        else:
            messages_per_host[message.path[-1]] = [message]

    times_per_host = []
    for host, messages in messages_per_host.items():
        entry = {"name":hosts.nodes[host]['name'], "id":host, "messages":[]}
        for message in messages:
            #print(message.__dict__)
            if message.transmitted == 0:
                bandwidth = 0.0
                continue
            elif message.finish_time == message.start_time:
                bandwidth = 0.0
            else:
                bandwidth = message.size/(message.finish_time-message.start_time)
            entry['messages'].append({"name":message.name, "id":message.id, "start_time":message.start_time, "finish_time":message.finish_time, "bandwidth_mean":bandwidth, "size":message.size})
        entry['messages'] = sorted(entry['messages'], key=lambda x: x['start_time'])
        times_per_host.append(entry)

    file.write("host;name;start_time;finish_time;bw;size\n")
    for host in times_per_host:
        #file.write("Host: "+host['name']+"\n")
        for message in host['messages']:
            file.write("%s;%s;%.2f;%.2f;%.2f;%.2f\n"%(host["name"],message['name'], message['start_time'],message['finish_time'],message['bandwidth_mean'],message["size"]))
        #file.write("-------------------\n")
     
    file.close()

def cache_status(topo, filename):

    file = open('reports/'+filename+"-cache_status.csv", 'w')


    file.write("host;hit;miss;total\n")
    for host in topo.nodes(data=True):
        host = host[1]
        if host["type"] == "chost":
            if host["cache"][0] > 0 or host["cache"][1] > 0:
                file.write("%s;%d;%d;%d\n" %(host['name'],host["cache"][0],(host["cache"][1]),host["cache"][0]+host["cache"][1]))
                #file.write("Host: "+host['name']+"\n")
                #file.write("Cache Hit: %d/%d = %.3f\n" %(host["cache"][0], host["cache"][0]+host["cache"][1], (host["cache"][0]/(host["cache"][0]+host["cache"][1]))*100))
                #file.write("Cache Miss: %d/%d = %.3f\n\n" %(host["cache"][1], host["cache"][0]+host["cache"][1], (host["cache"][1]/(host["cache"][0]+host["cache"][1]))*100))

    file.close()

def container_instantiation_time(messages, topo, filename):
    file = open('reports/'+filename+"-container_time.json", 'w')
    file.write("{\n\"containers\":\n")
    containers = []
    for message in messages:
        downloaded = int(message.transmitted/message.size)
        if message.status == 1:
            downloaded = 2
        containers.append({"name":message.name, "src":topo.nodes[message.src]["name"], "dst":topo.nodes[message.dst]["name"], "downloaded":downloaded, "download_time": message.finish_time-message.arrival_time})
    json.dump(containers, file)
    file.write("}")
    file.close()

def chain_time(messages, filename):

    file = open('reports/'+filename+"-chain_time.json", 'w')
    messages = sorted(messages, key=lambda x: x.chain)

    chains = {} 

    for message in messages:

        downloaded = int(message.transmitted/message.size)
        if message.status == 1:
            downloaded = 2
        appended_message = {"name":message.name, "schedule":message.arrival_time, "deadline":message.deadline_time ,"start":message.start_time ,"finish":message.finish_time, "downloaded":downloaded}

        if message.chain not in chains.keys():
            chains[message.chain] = {"finish_time": message.finish_time, "expected_lifetime": message.deadline_time-message.arrival_time, "real_lifetime":message.deadline_time-message.finish_time, "messages":[appended_message], "status":message.status}
        else:
            if message.finish_time > chains[message.chain]["finish_time"]:
                 chains[message.chain]["finish_time"] = message.finish_time
                 chains[message.chain]["real_lifetime"] = message.deadline_time-message.finish_time
            #print(message.__dict__)
            chains[message.chain]["messages"].append(appended_message)
            if message.status > chains[message.chain]["status"] :
                chains[message.chain]["status"] = message.status

    file.write("{\n\"chains\":\n")
    tmp = []
    for id, chain in chains.items():
         tmp.append({"id":id,"status":chain["status"],"expected":chain["expected_lifetime"],"real":chain["real_lifetime"],"percentage":chain["real_lifetime"]/chain["expected_lifetime"]})
         #tmp = ""
         #for message in chain["messages"]:
         #    tmp += str(message)+", "
         #file.write(json.dumps(chain["messages"]))
    file.write(json.dumps(tmp))
    file.write("}")
    file.close()

def network_log(logs, topo, filename):

    file = open('reports/'+filename+"-network_log.json", 'w')

    file.write("{\n\"rates\":\n")

    json.dump(logs, file)

    file.write(",\n\"graph\":\n")

    file.write(json.dumps(json_graph.node_link_data(topo)))
    file.write("}")
    file.close()

def registry_usage(messages, topo, filename):
    file = open('reports/'+filename+"-registry_usage.json", 'w')
    file.write("{\n\"registries\":\n")
    registries = {}
    for message in messages:
        if topo.nodes[message.src]["name"] in registries.keys():
            registries[topo.nodes[message.src]["name"]] += 1
        else:
            registries[topo.nodes[message.src]["name"]] = 1
    jsonRegistry = []
    for name,number in registries.items():
        jsonRegistry.append({"name":name, "numberOfRequests":number})
    
    file.write(json.dumps(jsonRegistry))

    file.write("}")
    file.close()

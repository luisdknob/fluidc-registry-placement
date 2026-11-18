import logging as log
import random
import sys
from uuid import uuid1 as uuid
from datetime import datetime

import classes.topology as ct

def create_node(template):
    node = template.copy()
    if "netint" in node.keys():
        node.pop("netint")

    node["id"] = uuid().int
    node["layers"] = []

    if "pos" in template.keys():
        node["pos"] = (node["pos"][0],node["pos"][1])
    if "storageSize" in template.keys():
        node["storageSize"] = template["storageSize"]
    else:
        node["storageSize"] = 0
    if "simultaneousDownload" in template.keys():
        node["simultaneousDownload"] = template["simultaneousDownload"]
    node["cachePolicy"] = template.get("cachePolicy", "FIFO")
    node["cache"] = [0,0]
    if template["type"] == "chost":
        node["scheduledLayers"] = 0

    return node

def create_interfaces(template):
    interfaces = []
    interfaces.append((template["hostId"],
                       template['connectedto'],
                       {"id":uuid().int, "bandwidth":template['bandwidth'], "inverse_bandwidth":1/template["bandwidth"], "activeMessages":[]}))
    if template.get("bidirectional"):
        interfaces.append((template['connectedto'],
                           template["hostId"],
                           {"id":uuid().int, "bandwidth":template['bandwidth'], "inverse_bandwidth":1/template["bandwidth"], "activeMessages":[]}))
    return interfaces

def scheduling_app(policy, chosts, **options):
    if policy == "fixed":

        dst = chosts.get(options['dst']) 
        
        dst["scheduledLayers"]+=1

        src = []
        for node in options['src']:
            src.append(chosts.get(node)["id"])

        return src, dst["id"]

    elif policy == "random":
        rCh = options["rCh"]
        rHost = random.choice(list(chosts.keys()))
        while(rHost in rCh):
            rHost = random.choice(list(chosts.keys()))
        rCh.append(rHost)
        if len(rCh) == len(chosts):
            rCh.clear()
        
        src = chosts[rHost]

        reg = []
        for node in src["registry"]:
            reg.append(options["registries"].get(node)["id"])

        src["scheduledLayers"]+=1
        
        return reg, src["id"]

    elif policy == "default":
        
        chosts = {k: v for k, v in sorted(chosts.items(), key=lambda item: item[1]["scheduledLayers"])}

        src = list(chosts.items())[0][1]
        src["scheduledLayers"]+=1

        reg = []
        for node in src["registry"]:
            reg.append(options["registries"].get(node)["id"])

        return reg, src["id"]

    return False, False

def create_message(template):

    message = ct.Message(size=template['size'], name=template['name'])
    if "src" in template:
        message.src = template['src']
    if "dst" in template:
        message.dst = template['dst']
    if "start" in template:
        message.arrival_time = template['start']
    if "dependencies" in template:
        message.dependencies = template['dependencies']
    if "deadline" in template:
        message.deadline_time = template['deadline']
    if "layer" in template:
        message.layer = template['layer']
    if "chain" in template:
        message.chain = template['chain']

    return message

def import_config(JSONFile, preNodes=None,seed=None):
    nodes = []
    jointNameObject = {}
    edges = []
    
    if seed is not None:
        random.seed(seed)
    else:
        random.seed(datetime.now())
        
    if preNodes:
        for node in preNodes:
            jointNameObject[node["name"]] = node

    netAbs = { key:value for key, value in jointNameObject.items() if value["type"] == "netabs" }

    if "nodes" in JSONFile:
        for nodeJSON in JSONFile['nodes']:
            node = create_node(nodeJSON)
            nodes.append(node)
            jointNameObject[node["name"]] = node

            if len(nodeJSON["netint"]) == 1:
                if nodeJSON["netint"][0]["connectedto"] == "random" :
                    dst = jointNameObject[random.choice(list(netAbs.keys()))]["name"]
                    log.debug("Connect node %s to %s" % (nodeJSON["name"], dst))
                    nodeJSON["netint"][0]["connectedto"] = dst
                    nodeJSON["netint"][0]["bidirectional"] = True
            
            for interface in nodeJSON["netint"]:
                interface["hostId"] = node["id"]
                interface["connectedto"] = jointNameObject[interface["connectedto"]]["id"]
                edges.extend(create_interfaces(interface))

    layers = {}
    if "layers" in JSONFile:
        for layer in JSONFile["layers"]:
            layers[layer["name"]] = layer

    #containers = {}
    #if "containers" in JSONFile:
    #    for container in JSONFile["containers"]:
    #        containers[container["name"]] = container

    chost = { key:value for key, value in jointNameObject.items() if value["type"] == "chost" }

    if "generators" in JSONFile:

        for generator in JSONFile["generators"]:
            
            if generator["type"] == "nodes":
                
                template = generator["template"]
                #template["type"] = "chost"
                
                if generator["number"] == "foreach":
                    generator["number"] = len(chost)

                for _ in range(0,generator["number"]):

                    dst = jointNameObject[random.choice(list(chost.keys()))]
                    
                    chost.pop(dst['name'])
                    if not netAbs:
                        netAbs = { key:value for key, value in jointNameObject.items() if value["type"] == "chost" }
                    
                    template["name"] = generator["name"]+"-"+dst["name"]
                    node = create_node(template)
                    jointNameObject[node["name"]] = node
                    nodes.append(node)

                    log.debug("Connect node %s to %s" % (node["name"], dst["name"]))
                    template["netint"]["connectedto"] = dst["id"]
                    template["netint"]["bidirectional"] = True
                    template["netint"]["hostId"] = node["id"]
                    intf = create_interfaces(template["netint"])
                    #print(intf)
                    edges.extend(intf)          

    messages = []

    if "messages" in JSONFile:
        for messageJSON in JSONFile['messages']:

            messageJSON["src"] = jointNameObject.get(messageJSON['src'])["id"]
            messageJSON["dst"] = jointNameObject.get(messageJSON['dst'])["id"]
            messageJSON["name"] = "noapp"
            messages.append(create_message(messageJSON))
    
    if "applications" in JSONFile:

        log.debug("Start scheduling applications")

        chosts = { key:value for key, value in jointNameObject.items() if value["type"] == "chost" }      
        registries = { key:value for key, value in jointNameObject.items() if value["type"] == "registry" }    

        #remove this in the future
        #if "RM1" in chosts.keys():
        #    chosts.pop("RM1")
        if "SP" in chosts.keys():
            chosts.pop("SP")

        apps = {}

        for appJSON in JSONFile['applications']:
            if appJSON['type'] == "image":

                if appJSON['scheduling'] == "fixed":
                    for node in appJSON["hosts"]:
                        
                        appJSON['src'], appJSON["dst"] = scheduling_app(appJSON['scheduling'], jointNameObject, src=jointNameObject.get(node)["registry"], dst=node)
                        message = create_message(appJSON)
                        messages.append(message)
                        log.debug("Add message %s-%d on %s using fixed schedule" % (message.name,message.id%100000000, jointNameObject.get(node)["name"]))

                elif appJSON['scheduling'] == "random":
                    
                    rCh = []
                    
                    for _ in range(0,appJSON['numReplicas']):
                        appJSON['src'], appJSON["dst"] = scheduling_app(appJSON['scheduling'], chosts, rCh=rCh, registries=registries)
                        message = create_message(appJSON)
                        messages.append(message)
                        host = next(filter(lambda x: x['id'] == appJSON["dst"], chosts.values()))
                        log.debug("Add message %s-%d on %s using random schedule" % (message.name,message.id%100000000, host["name"]))

                elif appJSON['scheduling'] == "default":
                    
                    for _ in range(0,appJSON['numReplicas']):

                        chostsOrdered = {k: v for k, v in sorted(chosts.items(), key=lambda item: item[1]["scheduledLayers"])}
                        appJSON['src'], appJSON["dst"] = scheduling_app(appJSON['scheduling'], chostsOrdered, registries=registries)
                        message = create_message(appJSON)
                        messages.append(message)
                        host = next(filter(lambda x: x['id'] == appJSON["dst"], chosts.values()))
                        log.debug("Add message %s-%d on %s using default (worst fit) schedule" % (message.name,message.id%100000000, host["name"]))
            
            elif appJSON['type'] == "layers":

                if appJSON['scheduling'] == "random":
                    
                    rCh = []
                    
                    for _ in range(0,appJSON['numReplicas']):
                        
                        appJSON['src'], appJSON["dst"] = scheduling_app(appJSON['scheduling'], chosts, rCh=rCh, registries=registries)
                        
                        for layer in appJSON["layers"]:
                            appJSON["name"] = appJSON["name"].split("-")[0]+"-"+layers[layer]["name"]
                            appJSON["size"] = layers[layer]["size"]
                            appJSON["layer"] = layer
                            message = create_message(appJSON)
                            messages.append(message)
                            host = next(filter(lambda x: x['id'] == appJSON["dst"], chosts.values()))
                            log.debug("Add message %s-%d on %s using random schedule" % (message.name,message.id%100000000, host["name"]))

                if appJSON['scheduling'] == "fixed":

                    for node in appJSON["hosts"]:
                        
                        appJSON['src'], appJSON["dst"] = scheduling_app(appJSON['scheduling'], jointNameObject, src=jointNameObject.get(node)["registry"], dst=node)
                        
                        for layer in appJSON["layers"]:
                            appJSON["name"] = appJSON["name"].split("-")[0]+"-"+layers[layer]["name"]
                            appJSON["size"] = layers[layer]["size"]
                            appJSON["layer"] = layer
                            message = create_message(appJSON)
                            messages.append(message)
                            host = next(filter(lambda x: x['id'] == appJSON["dst"], chosts.values()))
                            log.debug("Add message %s-%d on %s using fixed schedule" % (message.name,message.id%100000000, host["name"]))

                if appJSON['scheduling'] == "json" or appJSON['scheduling'] == "generator":

                    apps[appJSON["name"]] = appJSON

    if "generators" in JSONFile:

        for generator in JSONFile["generators"]:

             if generator["type"] == "schedules":

                sec = generator["start_time"]
                appJSON = apps[generator["app"]]
                
                while sec < generator["stop_time"]:
                    msg = {}
                    
                    msg['src'], msg["dst"] = scheduling_app("fixed", {**chosts,**registries}, src=jointNameObject.get(generator["node"])["registry"], dst=generator["node"])                    

                    for layer in appJSON["layers"]:
                            msg["name"] = appJSON["name"].split("-")[0]+"-"+layers[layer]["name"]
                            msg["size"] = layers[layer]["size"]
                            msg["layer"] = layers[layer]["name"]
                            msg["start"] = sec
                            message = create_message(msg)
                            #print(message)
                            messages.append(message)
                            host = next(filter(lambda x: x['id'] == msg["dst"], chosts.values()))
                            log.debug("Add message %s-%d on %s using generator schedule" % (message.name,message.id%100000000, host["name"]))
                    
                    sec += generator["frequency"]

    if "schedules" in JSONFile:

            for schedule in JSONFile["schedules"]:

                #print(apps[schedule["name"]])
                #print(jointNameObject.get(schedule["node"]), schedule["node"])

                appJSON = apps[schedule["name"]]
                msg = {}

                
                try:
                    msg['src'], msg["dst"] = scheduling_app("fixed", {**chosts,**registries}, src=jointNameObject.get(schedule["node"])["registry"], dst=schedule["node"])
                except:
                    print(schedule)
                    continue

                for layer in appJSON["layers"]:
                    #print (schedule)
                    msg["name"] = appJSON["name"].split("-")[0]+"-"+layers[layer]["name"]
                    msg["size"] = layers[layer]["size"]
                    msg["layer"] = layers[layer]["name"]
                    msg["chain"] = schedule["chain"]
                    msg["start"] = schedule["arrival_time"]
                    if "deadline" in schedule.keys():
                        msg["deadline"] = schedule["deadline"]
                    if "dependencies" in schedule.keys():
                        msg["dependencies"] = schedule["dependencies"]
                    message = create_message(msg)
                    #print(message)
                    messages.append(message)
                    host = next(filter(lambda x: x['id'] == msg["dst"], chosts.values()))
                    log.debug("Add message %s-%d on %s using json schedule" % (message.name,message.id%100000000, host["name"]))
                            
    return nodes, edges, messages

def import_topology(file, options):

    nodes = []
    edges = []
    jointNameObject = {}

    if not "type" in options:
        options["type"] = "chost"
    if not "simDownload" in options:
        options["simDownload"] = 3
    if not "storageSize" in options:
        options["storageSize"] = 4800.0
    if not "cachePolicy" in options:
        options["cachePolicy"] = "LRU"

    registry = []
    #pool = random.choices(["N%d" % (b) for b in range(0,100)], k=4)
    # REPRODUCIBILITY PATCH (IC2E-2021 snapshot): the original source
    # hard-coded the k=4 FluidC set. The default keeps the original behavior;
    # the CLI option --options '{"registries": [...]}' enables other k values.
    pool = options.get("registries", ["PA1", "RM2", "BO1", "NA1"])
    
    for i in pool:
        registry.append("registry-%s" % (i))
    print(registry)

    for line in file:
        lineArray = line.rstrip().split(" ")
        
        try:
            if len(lineArray) > 1:
                pos = (float(lineArray[2]), float(lineArray[1]))
            else:
                pos = (0,0)

            #registry = ["registry-N8","registry-N59","registry-N66","registry-N47"]
            template = {"type": options["type"], 
                    "name": lineArray[0], "registry":registry, "simultaneousDownload":options["simDownload"], "storageSize":options["storageSize"], "cachePolicy":options["cachePolicy"], "cache":[0,0],
                    "pos":pos}
            node = create_node(template)
            jointNameObject[node["name"]] = node
            nodes.append(node)
        except ValueError:
            netint_template = {"hostId": jointNameObject.get(lineArray[0])["id"], 
                    "connectedto": jointNameObject[lineArray[1]]["id"], "bidirectional": True, 
                    "bandwidth": int(lineArray[2])/1000000}
            edges.extend(create_interfaces(netint_template))

    return nodes, edges
            


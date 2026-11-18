import random
from uuid import uuid1 as uuid

random.seed(12)

vnfs = ["vnf00", "vnf01", "vnf02", "vnf03", "vnf04", "vnf05", "vnf06", "vnf07", "vnf08", "vnf09", "vnf10", "vnf11", "vnf12"]

node = ['TN1', 'ME', 'PV', 'BS', 'NA1', 'VE', 'PD1', 'CT1', 'MT', 'MC', 'MAZ', 'TO1', 'AN', 'NA6', 'TS1', 'RM2', 'TP', 'MAR', 'FI3', 'GE2', 'FI2', 'SS', 'RG', 'BO3', 'MI3', 'PI1', 'FUC', 'BN', 'RM5', 'SA', 'SR', 'CZ', 'MI2', 'MI5', 'UR', 'TN', 'MI1', 'FRA', 'MI4', 'BA1', 'AND', 'RC', 'GE1', 'PA1', 'MI6', 'LE', 'FE', 'FI1', 'CE', 'PZ', 'FI4', 'FI5', 'ME2', 'TA1', 'RM4', 'SA1', 'BR', 'FG', 'PG', 'AG', 'BO1', 'CA1', 'AV', 'NA2', 'SOV', 'PD2', 'CS', 'AQ1', 'GE3', 'RM1']

time = 0
mean = 0.18
z = 0

while z<20000:
    chain = uuid().int
    time += round(random.uniform(mean,mean*5), 8)
    deadline = 0
    if random.randint(0,10) < 7:
        deadline = time+round(random.uniform(15,100), 8)

    for i in range(0,random.randint(1,5)):
        temp = {"name":random.choice(vnfs), "arrival_time":time,"node":str(random.choice(node)),"chain":chain}
        if deadline != 0:
            temp["deadline"] = deadline
        print(temp)
        z+=1
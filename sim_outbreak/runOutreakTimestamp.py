import operator
import csv
from run_outbreak import infectNode
import math
import datetime
import snap

# e-mails can have multiple timestamps
def orderTimestamps(filename):
    
    timestampsDict = dict()

    with open(filename,'rb') as tsvin:
        tsvin = csv.reader(tsvin, delimiter='\t')
        next(tsvin)
        
        for row in tsvin:
            srcID = int(row[0])
            dstID = int(row[1])
            timestamp = int(row[3])
            edge = (srcID, dstID, timestamp)
            if edge in timestampsDict:
                timestampsDict[edge] += 1
            else:
                timestampsDict[edge] = 1
    
    sorted_timestampsDict = sorted( (key[2], key[0], key[1], value) for (key, value) in timestampsDict.items() )
    
    
    return sorted_timestampsDict



# TODO (maybe): Track cascasdes? add recovery time? take some nodes offline?
def runOutBreakTimestamp2(Network, p_initial_infect, num_detectors, graph_file, debug=False):
    print 'running timestamp model 2 by Andrew'

    # Creates different output for different executions
    Rnd = snap.TRnd(42)
    Rnd.Randomize()
    
    timestampsOrdered = orderTimestamps(graph_file)
    
    # Mark initial nodes infected
    num_nodes_infect = math.floor(Network.GetNodes() * p_initial_infect)
    cur_infected_ids = []
    detectors_alerted = []
    
    for i in range(int(num_nodes_infect)):
        nID = Network.GetRndNId(Rnd) # TODO: make this return different values on every run
        if nID not in cur_infected_ids:
            cur_infected_ids.append(nID)
            Network.AddStrAttrDatN(nID, 'infected', 'state') # resets state
        if Network.GetStrAttrDatN(nID, 'type') == 'detector' and nID not in detectors_alerted:
            detectors_alerted.append(nID)

    print 'INITIAL SET OF INFECTED NODES Size: ' + str(num_nodes_infect)
    
    if debug:
        print cur_infected_ids

    num_nodes_infected = len(cur_infected_ids)
    steps = 0
    found_earliest_infection = False
    time_first_infection = 0
    
    for timestamp in timestampsOrdered: # cycle thru the timestamps in the e-mails
        
        if len(detectors_alerted) == num_detectors: # outbreak detected!
            print "Outbreak detected!"
            print "Detectors Alerted: "
            if debug:
                print detectors_alerted
            print "STEP: " + str(steps)
            print "TIME INITIAL INFECTION: " + str(time_first_infection) + " TIME DETECTION: " + str(cur_time)
            time_to_detection = datetime.datetime.fromtimestamp(cur_time) - datetime.datetime.fromtimestamp(time_first_infection)
            print "TIME TO DETECTION: " + str(time_to_detection)
            print "NUM INFECTED: " + str(len(cur_infected_ids))
            return detectors_alerted, time_to_detection, cur_infected_ids
        
        if debug:
            if steps % 1000 == 0:
                print 'STEP: ' + str(steps)
                print 'CURRENTLY INFECTED: ' + str(cur_infected_ids)
                print 'DETECTORS ALERTED: ' + str(detectors_alerted)
        
        cur_time = timestamp[0]
        sourceNode = timestamp[1]
        destNode = timestamp[2]
        
        eid = Network.GetEI(sourceNode, destNode)
        
        if Network.GetStrAttrDatN(destNode, 'type') == 'detector':
            if destNode not in detectors_alerted:
                detectors_alerted.append(destNode)
                                              
        infected = False
        for _ in range(timestamp[3]): # since an edge w/ the same timestamp can occur multiple times
            if sourceNode in cur_infected_ids:
                if not found_earliest_infection:
                    time_first_infection = cur_time
                    found_earliest_infection = True
                if infectNode(Network, eid):
                    infected = True
                    break # b/c we do have an infection
        
        if infected: # let's add another infected node
            if destNode not in cur_infected_ids:
                cur_infected_ids.append(destNode)
                Network.AddStrAttrDatN(destNode, 'infected', 'state')
        steps += 1

    print 'NO OUTBREAK DETECTED'

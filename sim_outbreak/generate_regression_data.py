import operator
import csv
from run_outbreak import infectNode
import math
import datetime
import snap
import argparse, sys
from run_outbreak import loadDNCNetwork
import copy

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

    # Creates different output for different executions
    Rnd = snap.TRnd(42)
    Rnd.Randomize()
    
    timestampsOrdered = orderTimestamps(graph_file)
    
    # Mark initial nodes infected
    num_nodes_infect = math.floor(Network.GetNodes() * p_initial_infect)
    cur_infected_ids = []
    detectors_alerted = []
    
    while len(cur_infected_ids) < num_nodes_infect:
        nID = Network.GetRndNId(Rnd) # TODO: make this return different values on every run
        if nID not in cur_infected_ids:
            cur_infected_ids.append(nID)
            Network.AddStrAttrDatN(nID, 'infected', 'state') # resets state
            if Network.GetStrAttrDatN(nID, 'type') == 'detector' and nID not in detectors_alerted:
                detectors_alerted.append(nID)

    initial_infected_ids = copy.deepcopy(cur_infected_ids)
    print 'INITIAL SET OF INFECTED NODES Size: ' + str( len(cur_infected_ids) )
    
    if debug:
        print cur_infected_ids

    num_nodes_infected = len(cur_infected_ids)
    steps = 0
    found_earliest_infection = False
    time_first_infection = timestampsOrdered[0][0] # first infection is at least from the first e-mail's time
    cur_time = timestampsOrdered[0][0]
    
    for timestamp in timestampsOrdered: # cycle thru the timestamps in the e-mails
        
        if len(detectors_alerted) >= num_detectors: # outbreak detected!
            print "Outbreak detected!" # needs to be >= since we may start already detecting the outbreak
            
            if debug:
                print "Detectors Alerted: "
                print detectors_alerted
            print "STEP: " + str(steps)
            print "TIME INITIAL INFECTION: " + str(time_first_infection) + " TIME DETECTION: " + str(cur_time)
            time_to_detection = datetime.datetime.fromtimestamp(cur_time) - datetime.datetime.fromtimestamp(time_first_infection)
            print "TIME TO DETECTION: " + str(time_to_detection)
            print "NUM INFECTED: " + str(len(cur_infected_ids))
            return detectors_alerted, time_to_detection, cur_infected_ids, initial_infected_ids
        
        if debug:
            if steps % 1000 == 0:
                print 'STEP: ' + str(steps)
                print 'CURRENTLY INFECTED: ' + str(cur_infected_ids)
                print 'DETECTORS ALERTED: ' + str(detectors_alerted) + '\n\n'
        
        cur_time = timestamp[0]
        sourceNode = timestamp[1]
        destNode = timestamp[2]
        
        eid = Network.GetEI(sourceNode, destNode)
        
        if sourceNode in cur_infected_ids: # need to chekc if our source node is infected before setting off detector
            if Network.GetStrAttrDatN(destNode, 'type') == 'detector':
                if destNode not in detectors_alerted:
                    detectors_alerted.append(destNode)
                                              
        infected = False
        for _ in range(timestamp[3]): # since an edge w/ the same timestamp can occur multiple times
            if sourceNode in cur_infected_ids:
                if not found_earliest_infection: # use the first infected e-mail transmission to track the start of the infection
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
    return detectors_alerted, str( datetime.datetime.fromtimestamp(cur_time) - datetime.datetime.fromtimestamp(time_first_infection) ), cur_infected_ids, initial_infected_ids




if __name__== "__main__":
    print 'Running Outbreak with Timestamps'
    parser=argparse.ArgumentParser()

    parser.add_argument('--graph_filename', help='graph to load', default='../dnc-temporalGraph/out.dnc-temporalGraph')
    parser.add_argument('--debug', help='True to print verbose outputs', default=False)
    parser.add_argument('--write_output_to_file', help='True to save results and inputs in text file', default=False)
    args = parser.parse_args()
    
    print 'ARGS: '
    print args

    graph_filename = args.graph_filename
    p_initial_infect = 0.001
    p_infect = 0.3
    t_recover = 0
    p_infect_hardened = p_infect # No hardened nodes for now
    total_detectors = 50
    debug = args.debug
    write_output_to_file = args.write_output_to_file

    # Malformed input defaults to false
    debug_flag = False
    write_output = False

    if debug == 'True':
        debug_flag = True
    if write_output_to_file == 'True':
        write_output = True


    num_detectors_alerted =50
    
    detector_ids = [1874,1669,453,1706,1159,1144,1287,1258,895,278,999,993,1274,511,246,412,1377,1,465,203,1151,713,1768,350,1876,1440,1839,691,1906,547,1369,1792,1278,411,1254,390,419,869,1952,329,1510,1586,1998,1500,829,852,1198,841,24,1963]
    hardened_ids = detector_ids # For now, no hardened IDs

    if debug:
        print 'NUM DETECTORS ALERTED' + str(num_detectors_alerted)
        print detector_ids

    output_filename = 'regression_data_50_detectors.txt'
    with open(output_filename, 'a') as f:
        f.write('Trigger Order of Detector IDs|initial_infected_ids\n')
        for i in range(1000):
            print 'RUN ' + str(i) + ' \n'
            N = loadDNCNetwork(graph_filename, p_infect, p_infect_hardened, t_recover, detector_ids, hardened_ids)
            detectors_alerted, time_to_detection, cur_infected_ids, initial_infected_ids = runOutBreakTimestamp2(N, p_initial_infect, num_detectors_alerted, graph_filename, debug)

            print detectors_alerted, len(detectors_alerted), len(cur_infected_ids), initial_infected_ids
            f.write(str(detectors_alerted) + '|' + str(initial_infected_ids) + '\n')


#TODO: 1) learn order with social score feature 2) Include data from initial infected set 3) Node2Vec



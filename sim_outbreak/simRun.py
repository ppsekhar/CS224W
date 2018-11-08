import argparse
import sys
import json
import random
import csv
import operator
import math
import datetime
import snap

import numpy as np

from run_outbreak import infectNode
from run_outbreak import loadDetectorIds, loadDNCNetwork
from pprint import pprint

def GetSimConfig():
    with open('simulation.json', 'r') as fd:
        config = json.load(fd)
    return config

def GetDetectorAlertThreshold(config):
    numDetectors = config.get("triggeredDetectors", {})
    minDetectors = numDetectors.get("min", 1.0)
    maxDetectors = numDetectors.get("max", 1.0)
    return minDetectors


def GetDetectors(config):

    detectors = config.get("detectors", {})
    detectorSelection =  detectors.get("detectorSelection", "file")
    detectorNodes = detectors.get("detectorNodes", "../socialScore/socialScore.txt")


    if detectorSelection == 'file': 
        print "Selecting social hierarchy nodes as detectors ..."
        detector_ids = []
	with open(detectorNodes, 'rb') as tsvin:
	    tsvin = csv.reader(tsvin, delimiter='\t')
	    for row in tsvin:
		nID = int(row[0])
		detector_ids.append(nID)
    else:
        graphFile = config.get("GraphFile", '../dnc-temporalGraph/out.dnc-temporalGraph')
        detector_ids = []
	with open(graphFile,'rb') as tsvin:
            tsvin = csv.reader(tsvin, delimiter='\t')
            firstLine = True 
	    for row in tsvin:
                if firstLine:
                    firstLine = False
                    continue
	        srcID = int(row[0])
                dstID = int(row[1])
                if srcID not in detector_ids:
                    detector_ids.append(srcID)
                if dstID not in detector_ids:
                    detector_ids.append(dstID)

    numDetectors = config.get("NumDetectors", {})
    minDetectors = numDetectors.get("min", 50)
    maxDetectors = numDetectors.get("max", 500)
    step = numDetectors.get("increment", 50)

    for d in range(minDetectors, maxDetectors, step):
        if detectorSelection == "file":
            yield detector_ids[0:d]
        else:
            yield random.sample(detector_ids, d)

def GetInfectConfig(config):
    infectProb = config.get("infectProbability", {}) 
    p_infect_min = infectProb.get("min", 0.1)
    p_infect_max = infectProb.get("max", 0.1)

    initialInfect = config.get("InitialInfected", {})
    p_initial_infect_min = initialInfect.get("min", 0.005)
    p_initial_infect_max = initialInfect.get("min", 0.005)

    return (p_infect_min, p_infect_max, p_initial_infect_min, p_initial_infect_max)
    

def GetGraphFile(config):
    return config.get("GraphFile", '../dnc-temporalGraph/out.dnc-temporalGraph')

def GetOutputFile(config):
    return config.get("output", "simulationOutput.txt")


# e-mails can have multiple timestamps
def orderTimestamps(filename):
    
    timestampsDict = dict()
    nodeIdList = list()

    with open(filename,'rb') as tsvin:
        tsvin = csv.reader(tsvin, delimiter='\t')
        next(tsvin)
        
        for row in tsvin:
            srcID = int(row[0])
            dstID = int(row[1])

            if srcID not in nodeIdList:
                nodeIdList.append(srcID)

            if dstID not in nodeIdList:
                nodeIdList.append(dstID)

            timestamp = int(row[3])

            edge = (srcID, dstID, timestamp)

            if edge in timestampsDict:
                timestampsDict[edge] += 1
            else:
                timestampsDict[edge] = 1
    
    sorted_timestampsDict = sorted( (key[2], key[0], key[1], value) for (key, value) in timestampsDict.items() )
    
    print "Total timeStamps: %d" % len(sorted_timestampsDict)
    print "Start time : %r, End time: %r" % (sorted_timestampsDict[0], sorted_timestampsDict[-1])
    print "nodeIdList: %d" % len(nodeIdList)

    return (sorted_timestampsDict, nodeIdList)


def GetBaselineInfection(graph_filename, nodeIdList, orderedTimestamps, 
                          numInitialInfected, p_infect, TotalRun, outputFile):
    numInfectedNodeList = []

    for r in range(0, TotalRunCount):
        random.seed(r)
        Network = loadDNCNetwork(graph_filename, p_infect,\
                                 p_infect, 30, [], [])
        
        cur_infected_ids = random.sample(nodeIdList, int(numInitialInfected))

        for timestamp in orderedTimestamps: 
            cur_time = timestamp[0]
            sourceNode = timestamp[1]
            destNode = timestamp[2]
        
            eid = Network.GetEI(sourceNode, destNode)

            #
            # Infect destination node
            #
            infected = False

            # since an edge w/ the same timestamp can occur multiple times
            for _ in range(timestamp[3]): 
                if sourceNode in cur_infected_ids:
                    if infectNode(Network, eid):
                        infected = True
                        # b/c we do have an infection 
                        break

            #
            # Add infected node to the list 
            #
            if infected: 
                if destNode not in cur_infected_ids:
                    cur_infected_ids.append(destNode)
                    Network.AddStrAttrDatN(destNode, 'infected', 'state')

        numInfectedNodes = len(cur_infected_ids)
        numInfectedNodeList.append(numInfectedNodes)

    infectedNode = np.array(numInfectedNodeList)
    avgInfectedNode = np.mean(infectedNode)
    stdInfectedNode = np.std(infectedNode)
    maxInfectedNode = max(numInfectedNodeList)
    minInfectedNode = min(numInfectedNodeList)

    with open(outputFile, "a") as fd:
        fd.write("%r %r %r %r\n" % (avgInfectedNode, minInfectedNode,\
                maxInfectedNode, stdInfectedNode))


def runModifiedOutbreak(Network, initialInfectedNodes, numDetectors, orderedTimestamps, debug=False):
    print 'Running modified timestamp model 2 ...'
    
    # 
    # Mark initial nodes infected
    #
    cur_infected_ids = [ node for node in initialInfectedNodes]

    #
    # Set detectors alerted to empty
    #
    detectors_alerted = []
    
    #
    # totalNodes Infected count 
    #
    num_nodes_infected = len(cur_infected_ids)

    
    #
    # first infection is at least from the first e-mail's time
    #
    found_earliest_infection = False
    cur_time = orderedTimestamps[0][0]
    time_first_infection = orderedTimestamps[0][0] 
    steps = 0

    for timestamp in orderedTimestamps: # cycle thru the timestamps in the e-mails
        
        
        cur_time = timestamp[0]
        sourceNode = timestamp[1]
        destNode = timestamp[2]
        
        eid = Network.GetEI(sourceNode, destNode)

        #
        # Check if source node is infected 
        #
        if sourceNode in cur_infected_ids: 
            if Network.GetStrAttrDatN(destNode, 'type') == 'detector':
                if destNode not in detectors_alerted:
                    detectors_alerted.append(destNode)
                                              
        #
        # Infect destination node
        #
        infected = False

        # since an edge w/ the same timestamp can occur multiple times
        for _ in range(timestamp[3]): 
            if sourceNode in cur_infected_ids:
                #
                # use the first infected e-mail transmission 
                # to track the start of the infection
                #
                if not found_earliest_infection: 
                    time_first_infection = cur_time
                    found_earliest_infection = True

                if infectNode(Network, eid):
                    infected = True
                    # b/c we do have an infection 
                    break

        #
        # Add infected node to the list 
        #
        if infected: 
            if destNode not in cur_infected_ids:
                cur_infected_ids.append(destNode)
                Network.AddStrAttrDatN(destNode, 'infected', 'state')

        steps += 1

        if len(detectors_alerted) >= numDetectors: # outbreak detected!
            print "Outbreak detected!" # needs to be >= since we may start already detecting the outbreak
            
            if debug:
                print "Detectors Alerted: "
                print detectors_alerted
            print "STEP: " + str(steps)
            print "TIME INITIAL INFECTION: " + str(time_first_infection) + " TIME DETECTION: " + str(cur_time)
            time_to_detection = datetime.datetime.fromtimestamp(cur_time) - datetime.datetime.fromtimestamp(time_first_infection)
            print "TIME TO DETECTION: " + str(time_to_detection)
            print "NUM INFECTED: " + str(len(cur_infected_ids))
            return (detectors_alerted, time_to_detection, cur_infected_ids)
        
        if debug:
            if steps % 1000 == 0:
                print 'STEP: ' + str(steps)
                print 'CURRENTLY INFECTED: ' + str(cur_infected_ids)
                print 'DETECTORS ALERTED: ' + str(detectors_alerted) + '\n\n'

    print 'NO OUTBREAK DETECTED'
    return detectors_alerted, \
           str( datetime.datetime.fromtimestamp(cur_time) - datetime.datetime.fromtimestamp(time_first_infection) ), cur_infected_ids


def simulationRun(config, graph_filename, nodeList,  orderedTimeStamps,\
                  p_infect, numInitialInfected, TotalRunCount,\
                  outputFile):

    random.seed(137)
    for detector_ids in GetDetectors(config):
        numDetectors = len(detector_ids)
        print "Num Detectors: %r..." % numDetectors

        numInfectedNodeList = []

        for r in range(0, TotalRunCount):
            random.seed(r)
            Network = loadDNCNetwork(graph_filename, p_infect, \
                                     p_infect, 30, detector_ids,\
                                     detector_ids)

            initialInfectedNodes = random.sample(nodeList, int(numInitialInfected))

            detectors_alerted, time_to_detection, cur_infected_ids = \
                runModifiedOutbreak(Network, initialInfectedNodes, 20, \
                                    orderedTimeStamps, debug_flag)

            numInfectedNodes = len(cur_infected_ids)
            numInfectedNodeList.append(numInfectedNodes)

        infectedNode = np.array(numInfectedNodeList)
        avgInfectedNode = np.mean(infectedNode)
        stdInfectedNode = np.std(infectedNode)
        maxInfectedNode = max(numInfectedNodeList)
        minInfectedNode = min(numInfectedNodeList)

        with open(outputFile, "a") as fd:
            fd.write("%r %r %r %r %r\n" % (numDetectors, avgInfectedNode, \
                    minInfectedNode, maxInfectedNode, stdInfectedNode))

if __name__ == '__main__':

    config = GetSimConfig()

    debug = config.get("debug", None)
    if debug:
        debug_flag = True
    else:
        debug_flag = False

    graph_filename = GetGraphFile(config)
    outputFile = GetOutputFile(config)

    (p_infect, _, p_initial_infect, _) = GetInfectConfig(config)


    TotalRunCount = config.get("TotalRunCount",  100)

    orderedTimestamps, nodeIdList = orderTimestamps(graph_filename)

    #
    # Fix Num Detectors 
    # 
    num_detectors_alerted = 10

    #
    # Number of nodes infected at t0 
    #
    numInitialInfected = math.ceil(len(nodeIdList) * p_initial_infect)
    print p_initial_infect, numInitialInfected, len(nodeIdList)

    '''
    random.seed(137)
    for detector_ids in GetDetectors(config):
        numDetectors = len(detector_ids)
        print "Num Detectors: %r..." % numDetectors
        GetBaselineInfection(graph_filename, nodeIdList, orderedTimestamps, 
                             numInitialInfected, p_infect, TotalRunCount, "baseline.txt")
    '''

    simulationRun(config, graph_filename, nodeIdList,  orderedTimestamps,\
                  p_infect, numInitialInfected, TotalRunCount,\
                  outputFile)

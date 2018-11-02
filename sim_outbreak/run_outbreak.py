import snap
import csv
import math
import random

# Currently runs an outbreak on the DNC email network

def getLastTimestep(Network, eidMap):
	max_timestamp = 0
	for k in eidMap:
		eidList = eidMap[k]
		for eid in eidList:
			timestamp = Network.GetIntAttrDatE(eid, 'timestamp')
			if timestamp > max_timestamp:
				max_timestamp = timestamp

	return max_timestamp

def buildOutgoingEdgeIDMap(Network):
	eidMap = dict()
	for edge in Network.Edges():
		srcID = edge.GetSrcNId()
		if srcID not in eidMap:
			outgoing_edges = [edge.GetId()]
			eidMap[srcID] = outgoing_edges
		else:
			outgoing_edges = eidMap[srcID]
			outgoing_edges.append(edge.GetId())
			eidMap[srcID] = outgoing_edges

	return eidMap

def getEarliestEmailTimestamp(Network, nID, eidMap):
	min_timestamp = float('inf')

	if nID in eidMap:
		outgoing_edges = eidMap[nID]
		for eid in outgoing_edges:
			timestamp = Network.GetIntAttrDatE(eid, 'timestamp')
			if timestamp < min_timestamp:
				min_timestamp = timestamp

	return min_timestamp

def findEdgeWithTimestamp(Network, nID, eidMap, cur_timestamp):
	eids = []
	if nID in eidMap:
		outgoing_edges = eidMap[nID]
		for eid in outgoing_edges:
			timestamp = Network.GetIntAttrDatE(eid, 'timestamp')
			if timestamp == cur_timestamp:
				eids.append(eid)
			if timestamp < cur_timestamp:
				outgoing_edges.remove(eid)

	return eids

# Randomly determine if the node should be infected based on edge infect probability
def infectNode(Network, eid):
	p_infect = Network.GetFltAttrDatE(eid, 'p_infect')
	rndInt = random.uniform(0, 1)
	
	if rndInt < p_infect:
		return True

	return False

def runOutBreakTimestamp(Network, p_initial_infect, num_detectors):
	print 'running timestamp model'
	# TODO: Extend to include recovery time
	eidMap = buildOutgoingEdgeIDMap(Network)
	max_timestamp = getLastTimestep(Network, eidMap)

	# Mark initial nodes infected
	num_nodes_infect = math.floor(Network.GetNodes() * p_initial_infect)
	cur_infected_ids = []
	detectors_alerted = []

	for i in range(int(num_nodes_infect)):
		nID = Network.GetRndNId()
		if nID not in cur_infected_ids:
			cur_infected_ids.append(nID)
			Network.AddStrAttrDatN(nID, 'infected', 'state') # resets state
		if Network.GetStrAttrDatN(nID, 'type') == 'detector' and nID not in detectors_alerted:
			detectors_alerted.append(nID)

	print 'INITIAL SET OF INFECTED NODES Size: ' + str(num_nodes_infect)
	print cur_infected_ids

	# Get earliest timestamp from these infected nodes - set to current timestamp (infection start time)
	cur_timestamp = float('inf')
	for nID in cur_infected_ids:
		earliest = getEarliestEmailTimestamp(Network, nID, eidMap)
		if earliest < cur_timestamp:
			cur_timestamp = earliest

	num_nodes_infected = len(cur_infected_ids)
	steps = 0

	print 'RUNNING FROM TIMESTEP ' + str(cur_timestamp) + ' TO ' + str(max_timestamp)
	# Run outbreak until num_detectors are alerted (or we send the last email)
	while len(detectors_alerted) < num_detectors and cur_timestamp <= max_timestamp:
		if steps % 10000 == 0:
			print 'STEP: ' + str(steps)
			print 'TIMESTAMP: ' + str(cur_timestamp)
			print 'CURRENTLY INFECTED: ' + str(cur_infected_ids)
			print 'DETECTORS ALERTED: ' + str(detectors_alerted)
		
		for nID in cur_infected_ids:
			eids = findEdgeWithTimestamp(Network, nID, eidMap, cur_timestamp)
			for eid in eids:
				edge = Network.GetEI(eid)
				next_node = edge.GetDstNId()
				if Network.GetStrAttrDatN(next_node, 'type') == 'detector':
					if next_node not in detectors_alerted:
						detectors_alerted.append(next_node)
				if infectNode(Network, eid):
					if next_node not in cur_infected_ids:
						cur_infected_ids.append(next_node)
						Network.AddStrAttrDatN(next_node, 'infected', 'state')

		cur_timestamp+=1
		steps+=1


def loadDNCNetwork(filename, p_infect, p_infect_hardened, t_recover, detector_ids, hardened_ids):
	print 'Loading DNC Network'
	added = 0

	Network = snap.GenFull(snap.PNEANet, 0)
	print Network.GetNodes(), Network.GetEdges()
	with open(filename,'rb') as tsvin:
		tsvin = csv.reader(tsvin, delimiter='\t')
		i = 0 # Ignore header
		maxID = 0
		for row in tsvin:
			if i > 0:
				srcID = int(row[0])
				dstID = int(row[1])
				timestamp = int(row[3])
				if srcID > maxID:
					maxID = srcID
				if dstID > maxID:
					maxID = dstID
				
				# Add nodes to network if not already there
				if not Network.IsNode(srcID):
					added+=1
					Network.AddNode(srcID)
					# normal user or detector
					if srcID in detector_ids:
						Network.AddStrAttrDatN(srcID, 'detector', 'type')
					else:
						Network.AddStrAttrDatN(srcID, 'user', 'type')

				if not Network.IsNode(dstID):
					Network.AddNode(dstID)
					# normal user or detector
					if dstID in detector_ids:
						Network.AddStrAttrDatN(dstID, 'detector', 'type')
					else:
						Network.AddStrAttrDatN(dstID, 'user', 'type')

				# Add edge attributes (Note, multi edges allowed)
				eid = Network.AddEdge(srcID, dstID)
				Network.AddIntAttrDatE(eid, timestamp, 'timestamp')
				Network.AddIntAttrDatE(eid, t_recover, 't_recover')
				if dstID in hardened_ids:
					Network.AddFltAttrDatE(eid, p_infect_hardened, 'p_infect') #TODO: Do we need to distinguish between hardened/de
				else:
					Network.AddFltAttrDatE(eid, p_infect, 'p_infect')

				# state: infected or susceptible
				Network.AddStrAttrDatN(srcID, 'susceptible', 'state')
				Network.AddStrAttrDatN(dstID, 'susceptible', 'state')

			i+=1

	# Add any disjoint nodes (nodes without entries in the tsv file)
	for nID in range(maxID):
		if nID > 0 and not Network.IsNode(nID):
			Network.AddNode(nID)
			Network.AddStrAttrDatN(nID, 'susceptible', 'state')
			if nID in detector_ids:
				Network.AddStrAttrDatN(nID, 'detector', 'type')
			else:
				Network.AddStrAttrDatN(nID, 'user', 'type')


	print 'NUM NODES: ' + str(Network.GetNodes())
	print 'NUM EDGES: ' + str(Network.GetEdges())
	print 'NODES WITH OUTGOING EDGES: ' + str(added)
	return Network

# When testing out runs on a small network, it is easier to build test cases using this function
def loadTestNetwork():
	print 'Loading test Network'
	Network = snap.GenRndGnm(snap.PNEANet, 10, 6)
	print Network.GetEdges()
	# attr = snap.AddSAttrDat(1, "timestamp", 104)
	# attr2 = snap.AddSAttrDat(1, "timestamp", 107)
	for edge in Network.Edges():
		# Network.AddIntAttrDatE(edge, 107, 'timestamp')
		src = edge.GetSrcNId()
		dst = edge.GetDstNId()
		print src, dst
		# if Network.IsNode(src) and Network.IsNode(dst):
		# 	Network.AddEdge(src, dst)
		Network.AddIntAttrDatE(edge.GetId(), 107, 'timestamp')
		Network.AddIntAttrDatE(edge.GetId(), 35, 'infect')

	for edge in Network.Edges():
		print edge.GetId(), Network.GetIntAttrDatE(edge.GetId(), 'timestamp'), Network.GetIntAttrDatE(edge.GetId(), 'infect')
		# print edge.GetId(), Network.GetIntAttrDatE(edge.GetId(), 'timestamp')

	for edge2 in Network.Edges():
		# Network.AddIntAttrDatE(edge, 107, 'timestamp')
		src2 = edge2.GetSrcNId()
		dst2 = edge2.GetDstNId()
		print src, dst
		# if Network.IsNode(src) and Network.IsNode(dst):
		eid = Network.AddEdge(src2, dst2)
		Network.AddIntAttrDatE(eid, 407, 'timestamp')
		# Network.AddIntAttrDatE(edge.GetId(), 35, 'infect')

	for edge in Network.Edges():
		print edge.GetId(), Network.GetIntAttrDatE(edge.GetId(), 'timestamp'), Network.GetIntAttrDatE(edge.GetId(), 'infect')
	# Load TSV DNC file
	# For each row, add node, edge, timestamp, probability of infection

# Marks k top nodes as detectors
def loadDetectorIds(rankingFilename, k):
	print 'Choosing ' + str(k) + ' detector ids'
	detector_ids = []
	with open(filename,'rb') as tsvin:
		tsvin = csv.reader(tsvin, delimiter='\t')
		i = 0
		for row in tsvin:
			if i != 0: # Ignore header
				if i >= (k + 1):
					break
				nID = int(row[0])
				detector_ids.append(nID)
			i+=1

	return detector_ids

if __name__== "__main__":
	print 'Running Outbreak with Timestamps'
	
	# Define parameters (TODO: make command line flags)
	filename = '../dnc-temporalGraph/out.dnc-temporalGraph'
	p_infect = 0.8
	p_infect_hardened = 0.3
	t_recover = 30 # time in days to recovery

	hardened_ids = [5, 419503, 1897, 503, 1874]
	detector_ids = loadDetectorIds('pageRank.txt', 100)
	print detector_ids

	N = loadDNCNetwork(filename, p_infect, p_infect_hardened, t_recover, detector_ids, hardened_ids)

	p_initial_infect = 0.02 # Range 0-1 proportion of nodes to infect initially
	num_detectors = 4 # number of detectors that must be alerted for simulation to end
	runOutBreakTimestamp(N, p_initial_infect, num_detectors)



import snap
import csv

def runOutBreakSteadyState():
	print 'running outbreak with steady state'

def runOutBreakTimestamp():
	print 'running according to timestamps'

def loadDNCNetwork(filename, p_infect, p_infect_hardened, t_recover, hardened_ids):
	print 'Loading DNC Network'

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
					Network.AddNode(srcID)
				if not Network.IsNode(dstID):
					Network.AddNode(dstID)

				# Add edge attributes (Note, multi edges allowed)
				eid = Network.AddEdge(srcID, dstID)
				Network.AddIntAttrDatE(eid, timestamp, 'timestamp')
				Network.AddIntAttrDatE(eid, t_recover, 't_recover')
				if dstID in hardened_ids:
					Network.AddIntAttrDatE(eid, p_infect_hardened, 'p_infect_hardened')
				else:
					Network.AddIntAttrDatE(eid, p_infect, 'p_infect')

				# Infected = 1, Susceptible (not infected) = 0
				Network.AddIntAttrDatE(eid, 0, 'infected')
			
			i+=1

	# Add any disjoint nodes (nodes without entries in the tsv file)
	for nID in range(maxID):
		if nID > 0 and not Network.IsNode(nID):
			Network.AddNode(nID)


	print 'NUM NODES: ' + str(Network.GetNodes())
	print 'NUM EDGES: ' + str(Network.GetEdges())
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

if __name__== "__main__":
	print 'Running Outbreak with Timestamps'
	
	# Define parameters (TODO: make command line flags)
	filename = '../dnc-temporalGraph/out.dnc-temporalGraph'
	p_infect = 0.8
	p_infect_hardened = 0.3
	t_recover = 30 # time in days to recovery
	hardened_ids = [5, 419]

	loadDNCNetwork(filename, p_infect, p_infect_hardened, t_recover, hardened_ids)



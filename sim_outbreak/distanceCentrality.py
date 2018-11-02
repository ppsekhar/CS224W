

def distanceCentrality(network):
    
    n = network.GetNodes()
    Components = snap.TCnComV() # holds the connected components in a network
    snap.GetSccs(network, Components)
    
    nodeCloseness = dict() # dictionary {node: degree}
    for NI in network.Nodes():
        NId = NI.GetId()
        
        farness = snap.GetFarnessCentr( network, NId, True, True) # this call gives us the farness (un-normalized) sum to the nodes in this node's connected component
        
        if farness == 0: # this node has an out-degree of 0 and can't reach other nodes
            nodeCloseness[ NI.GetId() ] = n-1 # normalized avg distance to other nodes
            continue
        
        disconnected_nodes = 0 # how many nodes are disconnected from current node
        
        for CnCom in Components:
            if NId in CnCom: # we found the CnCom
                disconnected_nodes = n - CnCom.Len() # subtract away the size of our connected component
                break
        
        
        nodeCloseness[ NI.GetId() ] = farness 
        #+ disconnected_nodes * n
        
    sorted_nodeCloseness = sorted( ((value, key) for (key,value) in nodeCloseness.items()), reverse = False) # sort, ascending
    
    with open("distanceCentrality.txt", "w") as f3:
        for pair in sorted_nodeCloseness: # (value, node) format
            f3.write( str(pair[1]) + "\t" + str(pair[0]) + "\n" )

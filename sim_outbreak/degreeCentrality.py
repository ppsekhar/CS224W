# returns a list of node IDs, ranked by their degree centrality
# descending order, so the first node in the list has the highest degree centrality

def outDegreeCentrality(network):
    
    
    nodeDegree = dict() # dictionary {node: degree}
    for NI in network.Nodes():
        nodeDegree[ NI.GetId() ] = NI.GetOutDeg()
        
    sorted_nodeDegree = sorted( ((value, key) for (key,value) in nodeDegree.items()), reverse = True) # sort
    sorted_nodes = [item[1] for item in sorted_nodeDegree] # extract the node IDs only
    
    return sorted_nodes
    


# returns a list of node IDs, ranked by their degree centrality
# descending order, so the first node in the list has the highest degree centrality

def inDegreeCentrality(network):
    
    
    nodeDegree = dict() # dictionary {node: degree}
    for NI in network.Nodes():
        nodeDegree[ NI.GetId() ] = NI.GetInDeg()
        
    sorted_nodeDegree = sorted( ((value, key) for (key,value) in nodeDegree.items()), reverse = True) # sort
    sorted_nodes = [item[1] for item in sorted_nodeDegree] # extract the node IDs only
    
    return sorted_nodeDegree, sorted_nodes

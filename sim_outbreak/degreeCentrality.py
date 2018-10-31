def degreeCentrality(network):
    
    outDegreeDict = dict()
    inDegreeDict = dict()
    
    for NI in network.Nodes():
        outDegreeDict[ NI.GetId() ] = NI.GetOutDeg()
        inDegreeDict[ NI.GetId() ] = NI.GetInDeg()
    
    sorted_out = sorted( ((value, key) for (key,value) in outDegreeDict.items()), reverse = True) # sort
    sorted_in = sorted( ((value, key) for (key,value) in inDegreeDict.items()), reverse = True)
    
    with open("outDegree.txt", "w") as f1:
        for pair in sorted_out: # (value, node) format
            f1.write( str(pair[1]) + "\t" + str(pair[0]) + "\n" )
    
    with open("inDegree.txt", "w") as f2:
        for pair in sorted_in: # (value, node) format
            f2.write( str(pair[1]) + "\t" + str(pair[0]) + "\n" )

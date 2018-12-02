#!/usr/bin/env python
# coding: utf-8

# In[1]:


import snap 
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt 
import networkx as nx
from datetime import datetime
from matplotlib.pyplot import loglog 

#get_ipython().magic(u'matplotlib inline')


# In[2]:


def ProcessEdgeRow(row, Graph):
    src = row['src']
    dst = row['dst']
    timestamp = row['timestamp']
    
    if not Graph.IsNode(src):
        Graph.AddNode(src)
    
    if not Graph.IsNode(dst):
        Graph.AddNode(dst)
        
    if not Graph.IsEdge(src, dst):
        EId = Graph.AddEdge(src, dst)   
    else:
        EId = Graph.GetEI(src, dst) 
    
    Graph.AddIntAttrDatE(EId, timestamp, 'timestamp')
        
    return
        


# In[3]:


def GenerateDirectedGraph(df):
    '''
    Returns a TNEANet Graph object 
    '''
    Graph = snap.TNEANet.New()
    df.apply(ProcessEdgeRow, axis=1, Graph=Graph)

    return Graph


# In[4]:


def GenerateGraph(filename='/home/merchantsameer2014/project/dnc-temporalGraph/out.dnc-temporalGraph'):
    ''' read a list of edges 
        and return a snap multigraph
    '''
    df = pd.read_csv(filename, sep='\t', header=None)
    df.columns = ['src', 'dst', 'weight', 'timestamp']
    G = GenerateDirectedGraph(df)
    #print "Nodes: ", G.GetNodes()
    #print "Edges: ", G.GetEdges()
    return (df, G)


# In[5]:


def plotDegreeDistribution(G):
    #
    # Get Degree Distribution 
    # 
    OutDegToCntV = snap.TIntPrV()
    snap.GetOutDegCnt(G, OutDegToCntV)
    count = 0
    nodeList = []
    degreeList = []
    for item in OutDegToCntV:
        (n, d) = (item.GetVal2(), item.GetVal1())
        nodeList.append(n)
        degreeList.append(d)
    x = np.array( [ np.log10(item.GetVal1()) for itemm in OutDegToCntV if item.GetVal1() > 0 ] )
    y = np.array( [ np.log10(item.GetVal2()) for item in OutDegToCntV if item.GetVal2() > 0 ] )
    #
    # Plot Degree Distribution
    #
    plt.figure(figsize=(15,15))
    loglog(degreeList, nodeList, 'bo')
    #plt.plot(x_plot, 10**b*x_plot**a, 'r-')
    plt.title("LogLog plot of out-degree distribution")
    plt.show()
    return 


# ### 1. Compute Degree Centrality

# In[6]:


def computeDegreeCentrality(G, NodeAttributes):
    #
    # 1. Degree Centrality 
    #    Get In Degree and Out Degree for each node 
    #
    InDegV = snap.TIntPrV()
    OutDegV = snap.TIntPrV()

    snap.GetNodeOutDegV(G, OutDegV)
    snap.GetNodeInDegV(G, InDegV)

    InDegreeList = [ (item.GetVal1(), item.GetVal2()) for item in InDegV ]
    OutDegreeList = [ (item.GetVal1(), item.GetVal2()) for item in OutDegV ]
    
    InDegreeList.sort(key=lambda x: x[1], reverse=True)
    OutDegreeList.sort(key=lambda x: x[1], reverse=True)

    minOutDegree = min(OutDegreeList, key = lambda x: x[1])[1]
    maxOutDegree = max(OutDegreeList, key = lambda x: x[1])[1]
    minInDegree = min(InDegreeList, key = lambda x: x[1])[1]
    maxInDegree = max(InDegreeList, key = lambda x: x[1])[1]
    
    #
    # Sanity Check 
    #print maxOutDegree, minOutDegree, maxInDegree, minInDegree
    #print InDegreeList[0], InDegreeList[-1]
    
    for (nodeId, Degree) in InDegreeList:
        if not NodeAttributes.get(nodeId, None):
            NodeAttributes[nodeId] = dict()
        NodeAttributes[nodeId]['InDegree'] = Degree
        normalizedDegree = (float(Degree) - float(minInDegree))/(float(maxInDegree - float(minInDegree)))
        NodeAttributes[nodeId]['NormInDegree'] = normalizedDegree

    for (nodeId, Degree) in OutDegreeList: 
        NodeAttributes[nodeId]['OutDegree'] = Degree
        normalizedDegree = (float(Degree) - float(minOutDegree))/(float(maxOutDegree - float(minOutDegree)))
        NodeAttributes[nodeId]['NormOutDegree'] = normalizedDegree
        
    #
    # Sanity Check 
    #
    #print NodeAttributes[1874]
    #print NodeAttributes[893]
    
    return NodeAttributes


# ### 2. Compute Clustering Coefficient

# In[7]:


def computeClusteringCoeff(G, NodeAttributes):
    NIdCCfH = snap.TIntFltH()
    snap.GetNodeClustCf(G, NIdCCfH)
    
    ClusterCoeffList = list()
    for nodeId in NIdCCfH:
        NodeAttributes[nodeId]['ClusterCoeff'] = NIdCCfH[nodeId]
        ClusterCoeffList.append((nodeId, NIdCCfH[nodeId]))
        
    ClusterCoeffList.sort(key=lambda x: x[1], reverse=True)
    minClusterCoeff = min(ClusterCoeffList, key=lambda x: x[1])[1]
    maxClusterCoeff = max(ClusterCoeffList, key=lambda x: x[1])[1]
    
    #
    # Sanity Check 
    #
    print ClusterCoeffList[1], maxClusterCoeff, ClusterCoeffList[-1], minClusterCoeff
    
    NIdCCfH = snap.TIntFltH()
    snap.GetNodeClustCf(G, NIdCCfH)
    ClusterCoeffList = list()
    for nodeId in NIdCCfH:
        clusterCoeff = NIdCCfH[nodeId]
        normClusterCoeff = (clusterCoeff - minClusterCoeff)/(maxClusterCoeff - minClusterCoeff)
        NodeAttributes[nodeId]['NormClusterCoeff'] = normClusterCoeff
        
    #print NodeAttributes[2012]
    return NodeAttributes


# ### 3. Compute Avergate shortest path length

# In[8]:


def computeAvgShortestPath(G, NodeAttributes):
    nodeCount = float(G.GetNodes() - 1)
    avgShortPathLenList = list()
    for src in G.Nodes():
        srcId = src.GetId()
        totalShortPathLength = 0 
    
        for dst in G.Nodes():
            dstId = dst.GetId()
            #
            # Skip Self Edges
            #
            if srcId == dstId:
                continue
            
            #
            # Compute Shortest Path 
            #
            l = snap.GetShortPath(G, srcId, dstId, True)
        
            #
            # Skip nodes that cannot be reached 
            #
            if l < 0:
                continue
            
            totalShortPathLength += float(l) 
        NodeAttributes[srcId]['AvgShortPathLen'] = totalShortPathLength/nodeCount
        avgShortPathLenList.append((srcId, totalShortPathLength/nodeCount))
        
    minAvgShortPathLength = min(avgShortPathLenList, key=lambda x: x[1])[1]
    maxAvgShortPathLength = max(avgShortPathLenList, key=lambda x: x[1])[1]
    
    for (node, spLen) in avgShortPathLenList:
        normAvgShortPath = (spLen - minAvgShortPathLength)/(maxAvgShortPathLength - minAvgShortPathLength)
        NodeAttributes[node]['normAvgShortPathLen'] = normAvgShortPath
    
    #print NodeAttributes[480]
    
    return NodeAttributes


# ### 4. Compute Betweeness Centrality

# In[9]:


def computeBetweenessCentrality(G, NodeAttributes):
    Nodes = snap.TIntFltH()
    Edges = snap.TIntPrFltH()
    BetweenessNodeList = list()
    BetweenessEdgeList = list()

    snap.GetBetweennessCentr(G, Nodes, Edges, 1.0)
    for node in Nodes:
        NodeAttributes[node]['Betweeness'] = Nodes[node]
        BetweenessNodeList.append((node, Nodes[node]))

    for edge in Edges:
        #print "edge: (%d, %d) centrality: %f" % (edge.GetVal1(), edge.GetVal2(), Edges[edge])
        BetweenessEdgeList.append((edge.GetVal1(), edge.GetVal2(), Edges[edge]))

    BetweenessNodeList.sort(key=lambda x: x[1], reverse=True) 
    BetweenessEdgeList.sort(key=lambda x: x[2], reverse=True)
    
    #print BetweenessNodeList[0], BetweenessNodeList[-1]
    
    minBetweeness = BetweenessNodeList[-1][1]
    maxBetweeness = BetweenessNodeList[0][1]
    for (node, betweeness) in BetweenessNodeList:
        normBetweeness = (betweeness - minBetweeness)/(maxBetweeness - minBetweeness)
        NodeAttributes[node]['normBetweeness'] = normBetweeness
        
    #print NodeAttributes[1669]
    #print NodeAttributes[884]
    
    return NodeAttributes


# ### 5.  Compute Auth and Hub Score

# In[10]:


def computeAuthHubScore(G, NodeAttributes):
    NIdHubH = snap.TIntFltH()
    NIdAuthH = snap.TIntFltH()
    snap.GetHits(G, NIdHubH, NIdAuthH)
    HubNodes = []
    for nodeId in  NIdHubH:
        HubNodes.append((nodeId,  NIdHubH[nodeId]))
        NodeAttributes[nodeId]['HubScore'] = NIdHubH[nodeId]
    
    HubNodes.sort(key = lambda x: x[1], reverse=True)

    AuthNodes = []
    for nodeId in  NIdAuthH:
        AuthNodes.append((nodeId,  NIdAuthH[nodeId])) 
        NodeAttributes[nodeId]['AuthScore'] = NIdAuthH[nodeId]
        
    AuthNodes.sort(key = lambda x: x[1], reverse=True)

    #print AuthNodes[0], AuthNodes[-1]
    #print HubNodes[0], HubNodes[-1]
    
    minAuthNodes = AuthNodes[-1][1]
    maxAuthNodes = AuthNodes[0][1]
    minHubNodes = HubNodes[-1][1]
    maxHubNodes = HubNodes[0][1]
    
    for (node, hubScore) in HubNodes:
        normHubScore = (hubScore - minHubNodes)/(maxHubNodes - minHubNodes)
        NodeAttributes[node]['normHubScore'] = normHubScore
    
    for (node, authScore) in AuthNodes:
        normAuthScore = (authScore - minAuthNodes)/(maxAuthNodes - minAuthNodes)
        NodeAttributes[node]['normAuthScore'] = normAuthScore
    
    #print NodeAttributes[1874]
    #print NodeAttributes[893]
    return NodeAttributes


# ## Get Raw Statistics 
# 
#     1. Degree Centrality 
#     2. Clustering Coefficient 
#     3. Mean shortest path from each node 
#     4. Betweeness Centralitily 
#     5. Hub and Authority Score 

# In[11]:


def GetRawStatistics(G, NodeAttributes):
    
    #
    # Step 1: Compute Degree Centrality
    #
    print "Computing Degree Centrality... "
    computeDegreeCentrality(G, NodeAttributes)
    
    #
    # Step 2: Compute Clustering Coefficients 
    #
    print "Computing Clustering coefficient..."
    computeClusteringCoeff(G, NodeAttributes)
    
    #
    # Step 3: Avg. Shortest path length 
    #
    print "Computing Average Shortest path length ... "
    computeAvgShortestPath(G, NodeAttributes)
    
    # 
    # Step 4: Betweeness Centrality
    #
    print "Computing Betweeness centrality... "
    computeBetweenessCentrality(G, NodeAttributes)
    
    #
    # Step 5: Hub and Auth Score 
    #
    print "Computing Hub and Auth Score ... "
    computeAuthHubScore(G, NodeAttributes)
    
    return 


# ## Automatic Social Hierarchy Detection From Email Network 
# 
# ### Steps 
# 
#     1. Compute node's importance on response time for email  
#     2. Get all Cliques (Algorithm 457)
#     3. Number of clique each node is part of 
#     4. Raw Clique Score computed using 
#     
#  $$R*2^{n-1}$$
#  
#     5. Weighted Clique Score (Based on importance of a person) 
#     
#  $$W = t*2^{n-1}$$
#  

# ### Use networkx library for Clique analysis 
# 
#     1. Build a multigraph with edges for each (src, dst, timestamp) entry in the email data set 
#     2. Build undirected graph with edges between nodes only when email count exceeds N=4 between two those nodes 
#     

# In[12]:


def ProcessNxEdgeRow(row, Graph):
    src = row['src']
    dst = row['dst']
    timestamp = row['timestamp']
    
    Graph.add_node(src)
    Graph.add_node(dst)
    Graph.add_edge(src, dst, timestamp=timestamp)
        
    return
        


# In[13]:


def GenerateDirectedNxGraph(df):
    '''
    Returns a TNEANet Graph object 
    '''
    Graph = nx.MultiDiGraph(name="DNC Email Network")
    df.apply(ProcessNxEdgeRow, axis=1, Graph=Graph)

    #print "Networkx Nodes: ", Graph.number_of_nodes()
    #print "Networkx Edges: ", Graph.number_of_edges()
    
    return Graph


# ### Generate undirected graph with edges between nodes with email count > N
# 
# #### Prune all edges with N <=4 emails exchanged
# As per the paper - consider edges between nodes only if the nodes have exchanged > N messages
# N is a tunable parameter 
# 
# DNC email has a median of message exchanged = 2 

# In[14]:


def GeneratePrunedDirectedGraph(GNx,  N = 4):
    
    edgeCount = dict()
    for edge in GNx.edges():
        if not edgeCount.get(edge, None):
            edgeCount[edge] = 0
        edgeCount[edge] += 1 
        
    emailDist= [ v for k, v in edgeCount.iteritems() ]
    emailDist.sort(reverse=True)
    #print emailDist[0], emailDist[-1], np.median(emailDist), len(emailDist)
    
   
    pruneList = [ k for k, v in edgeCount.iteritems() if v <= N ]
    prunedEdgeList = [ k for k, v in edgeCount.iteritems() if v > N ]
    
    uGNx = nx.Graph()

    for edge in prunedEdgeList:
        (src, dst) = edge
        uGNx.add_edge(int(src), int(dst))
    
    #print "Networkx Nodes: ", uGNx.number_of_nodes()
    #print "Networkx Edges: ", uGNx.number_of_edges() 
    
    return uGNx


# ### Step 1: Compute Nodes importance on email response time 

# ### Approach 1: Based on Rowe et. al. paper 
# 
# Use response time to measure importance of a node 
# 
#     1. For each node get all the out bound email timestamps 
#     2. For each email sent - check the response time from the receiver 
#     3. Consider responses within a day for computing time score. 
#     4. Consider response time for nodes that have exchanged at least 100 emails 
#        (fewer emails with high response time can falsely promote node based on time score)
#  

# In[15]:


def getEmailSentByNode(GNx):
    temporalMap = dict()
    for n, nbrs in GNx.adjacency():
        temporalMap[n] = dict()
        for nbr, edict in nbrs.items():
            t1 = [ d['timestamp'] for d in edict.values() ]
            t1.sort()
            temporalMap[n][nbr] = t1 
            
    return temporalMap


# In[16]:


def getAvgResponseTime(temporalMap):
    avgNodeResponse = list()

    for src, destinations in temporalMap.iteritems():
        totalRequestResp = 0
        totalResponseTime = 0.0
    
        for dst, reqTimestamps in destinations.iteritems():
            responseTime = None
            #
            # Walk through ALl requests sent to a destination
            #
            for req in reqTimestamps:
                reqTime = datetime.fromtimestamp(req)
        
                #
                # Look for response time from the destinaton to ths source
                #
                for resp in temporalMap[dst].get(src, list()):
                    respTime = datetime.fromtimestamp(resp)
            
                    if resp < req:
                        #
                        # Look for first response after the request time 
                        #
                        continue
            
                    deltaTime = respTime - reqTime
            
                    if deltaTime.total_seconds() > 86400:
                        #
                        # If response time exceeds a day don't 
                        # consider it as a response
                        break
                    
                    #print "Found Response time: src: %d, dst: %d req: %s, resp: %s" % (src, dst, reqTime, respTime)
                
                    totalRequestResp += 1
                    totalResponseTime += deltaTime.total_seconds()
                    break
        #
        # Compute average across all dst response times 
        #
        if totalRequestResp > 0 and totalResponseTime > 0:
            avgResponse = totalResponseTime/totalRequestResp
        else:
            #
            # Set default response to 7 day 
            #
            avgResponse = float(7*86400)
        #
        # Lower response Higher the timeScore 
        # 
        timeScore = 1/avgResponse
        avgNodeResponse.append((src, timeScore, totalResponseTime, totalRequestResp ))
        
    avgNodeTimeScore = list()

    #
    # Ignore response time for email exchanges fewer than 10
    #
    for x in avgNodeResponse:
        (src, timeScore, totalResponseTime, totalRequestResp) = x
    
        if totalRequestResp <= 200:
            timeScore = 1.0/float(7*86400)
        
        avgNodeTimeScore.append((src, timeScore, totalResponseTime, totalRequestResp))
        
    avgNodeTimeScore.sort(key=lambda x: x[1], reverse=True)

    #print "\nLast Node avg response time: ", avgNodeTimeScore[-1]
    #print "\nTop top two nodes avg response time:", avgNodeTimeScore[:2] 
    
    normTimeScore = dict()
    minAvgTimeScore = avgNodeTimeScore[-1][1]
    maxAvgTimeScore = avgNodeTimeScore[0][1]

    for (node, timeScore, _, _) in avgNodeTimeScore:
        normTimeScore[node] = (timeScore - minAvgTimeScore)/(maxAvgTimeScore - minAvgTimeScore)
    
    #print "Node 1625 normTimeScore: ", normTimeScore[1625]
    
    return normTimeScore


# In[17]:


def GetSocialAttributes(df, NodeAttributes, threshold=0):
    
    # Generate NetworkX graph
    #
    GNx = GenerateDirectedNxGraph(df)
    
    #
    # Prune graph based on number of emails exchanged 
    # Keep edges with edge weight > 4 (exchanged > 4 emails)
    #

    uGNx = GeneratePrunedDirectedGraph(GNx, N=threshold)
    
    temporalMap = getEmailSentByNode(GNx)
    normTimeScore = getAvgResponseTime(temporalMap)
    
    nodeCliqueCount = dict()
    rawCliqueScore = dict()
    weightedCliqueScore = dict()

    #
    # Find all maximal cliques 
    # 
    for clique in nx.find_cliques(uGNx):
        for node in clique:
        
            if not nodeCliqueCount.get(node, None):
                nodeCliqueCount[node] = 0
            
            if not rawCliqueScore.get(node, None):
                rawCliqueScore[node] = 0
        
            if not weightedCliqueScore.get(node, None):
                weightedCliqueScore[node] = 0
            
            nodeCliqueCount[node] += 1 
        
            n = len(clique)
        
            rawCliqueScore[node] += 2**n
        
            weightedCliqueScore[node] += (2**n)*normTimeScore[node]
    #
    # Get a sorted list of nodes based on their clique count 
    #
    nodeCliqueList = [ (k, v) for k, v in nodeCliqueCount.iteritems() ]
    nodeCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    rawCliqueList = [ (k, v) for k, v in rawCliqueScore.iteritems() ]
    rawCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    weightedCliqueList = [ (k, v) for k, v in weightedCliqueScore.iteritems() ]
    weightedCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    #print "\n Top 10 nodes based on Cliques count: " , nodeCliqueList[:10]
    #print "\n Top 10 nodes based on Raw Clique size: ",  rawCliqueList[:10]
    #print "\n Top 10 nodes based on weighted Clique size: " , weightedCliqueList[:10]
    
    minNodeCliqueCount = nodeCliqueList[-1][1]
    maxNodeCliqueCount = nodeCliqueList[0][1]

    minRawCliqueScore = rawCliqueList[-1][1]
    maxRawCliqueScore = rawCliqueList[0][1]

    minWeightedCliqueScore = weightedCliqueList[-1][1]
    maxWeightedCliqueScore = weightedCliqueList[0][1]
    
    for node, score in nodeCliqueList:
        NodeAttributes[node]['nodeClique'] = score
        NodeAttributes[node]['normNodeClique'] = float(score - minNodeCliqueCount)/float(maxNodeCliqueCount - minNodeCliqueCount)
        
    for node, score in rawCliqueList:
        NodeAttributes[node]['rawClique'] = score
        NodeAttributes[node]['normRawClique'] = float(score - minRawCliqueScore)/float(maxRawCliqueScore - minRawCliqueScore)
    
    for node, score in weightedCliqueList:
        NodeAttributes[node]['weightedClique'] = score
        NodeAttributes[node]['normWeightedClique'] = float(score - minWeightedCliqueScore)/float(maxWeightedCliqueScore - minWeightedCliqueScore)
     
    #print "\nNode 1874 features: ", NodeAttributes[1874]
    
    return 


# ## Modified version of Social Score
# 
# Social hierarchy can be determined by how often a person receives a response to their mail within first 10 mails sent by the receipient. Instead of using time as a measure which can be skewed due to different time zones or working hours, a priority of mails can be a better indicator of a persons importance in the organization 
# 

# In[25]:


def getNodeResponseList(GNx):
    nodeResponseTuple = dict()
    nodeAdj = dict()
    
    for n, nbrs in GNx.adjacency():
        nodeAdj[n] = dict()
        nodeResponseTuple[n] = list()
        for nbr, edict in nbrs.items():
            t1 = [ d['timestamp'] for d in edict.values() ]
            t2 = [nbr]*len(t1)
            response = zip(t1,t2)
            response.sort(key=lambda x: x[0])
            nodeResponseTuple[n].extend(response)
            
            if nbr not in nodeAdj[n]:
                nodeAdj[n][nbr] = list()
            nodeAdj[n][nbr].extend(t1)
            
    return nodeAdj, nodeResponseTuple


# In[26]:


def getAvgResponseScore(nodeAdj, nodeResponseTuple):
    avgNodeResponse = list()

    for src, destinations in nodeAdj.iteritems():
        totalRequests = 0.0
        totalPriorityResponse = 0.0
        #print "Processing %r" % src
        for dst, reqTimestamps in destinations.iteritems():
            #
            # Walk through ALl requests sent to a destination
            #         
            for req in reqTimestamps:
                totalRequests += 1        
                #
                # check if destination responded to src within next 5 mails 
                #
                count = 0
                found_response = False
                for resp, node in nodeResponseTuple[dst]:            
                    if resp < req:
                        #
                        # Look for first response after the request time 
                        #
                        continue
                    
                    count += 1
                    found_response = True
                    if node == src:
                        #print "Found a response in top 5.."
                        break
                    
                    if count > 5:
                        break
                
                if found_response and (count <= 5):
                    totalPriorityResponse += 1
                    break
        #
        # Compute average across all dst response times 
        # 
        #
        #print "src: %r, total mails sent %r, priority: %r" % (src, totalRequests, totalPriorityResponse)
        if totalRequests > 0 and totalPriorityResponse > 0:
            avgResponse = totalPriorityResponse/totalRequests
        else:
            #
            # Set default priority respone to zero
            #
            avgResponse = 0

        avgNodeResponse.append((src, avgResponse, totalRequests, totalPriorityResponse ))
        
    avgNodeResponseScore = list()

    #
    # Ignore response time for email exchanges fewer than 200
    #
    for x in avgNodeResponse:
        (src, avgResponse, totalRequests, totalPriorityResponse) = x
    
        if totalRequests <= 200:
            avgResponse = 0
        
        avgNodeResponseScore.append((src, avgResponse, totalRequests, totalPriorityResponse))
        
    avgNodeResponseScore.sort(key=lambda x: x[1], reverse=True)

    #print "\nLast Node avg response score: ", avgNodeResponseScore[-1]
    print "\nTop top nodes avg response score:", avgNodeResponseScore[:10] 
    
    
    normResponseScore = dict()
    minAvgResponseScore = avgNodeResponseScore[-1][1]
    maxAvgResponseScore = avgNodeResponseScore[0][1]

    for (node, responseScore, _, _) in avgNodeResponseScore:
        normResponseScore[node] = (responseScore - minAvgResponseScore)/(maxAvgResponseScore - minAvgResponseScore)
    
    #print "\nNode 1625 normTimeScore: ", normResponseScore[1625]
    
    return normResponseScore


# In[27]:


def GetModifiedSocialAttributes(df, NodeAttributes, threshold=0):
    
    # Generate NetworkX graph
    #
    GNx = GenerateDirectedNxGraph(df)
    
    #
    # Prune graph based on number of emails exchanged 
    # Keep edges with edge weight > 4 (exchanged > 4 emails)
    #

    uGNx = GeneratePrunedDirectedGraph(GNx, N=threshold)
    
    nodeAdj, nodeResponseTuple = getNodeResponseList(GNx)
    normResponseScore = getAvgResponseScore(nodeAdj, nodeResponseTuple)
    
    nodeCliqueCount = dict()
    rawCliqueScore = dict()
    weightedCliqueScore = dict()

    #
    # Find all maximal cliques 
    # 
    for clique in nx.find_cliques(uGNx):
        for node in clique:
        
            if not nodeCliqueCount.get(node, None):
                nodeCliqueCount[node] = 0
            
            if not rawCliqueScore.get(node, None):
                rawCliqueScore[node] = 0
        
            if not weightedCliqueScore.get(node, None):
                weightedCliqueScore[node] = 0
            
            nodeCliqueCount[node] += 1 
        
            n = len(clique)
        
            rawCliqueScore[node] += 2**n
        
            weightedCliqueScore[node] += (2**n)*normResponseScore[node]
    #
    # Get a sorted list of nodes based on their clique count 
    #
    nodeCliqueList = [ (k, v) for k, v in nodeCliqueCount.iteritems() ]
    nodeCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    rawCliqueList = [ (k, v) for k, v in rawCliqueScore.iteritems() ]
    rawCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    weightedCliqueList = [ (k, v) for k, v in weightedCliqueScore.iteritems() ]
    weightedCliqueList.sort(key=lambda x: x[1], reverse=True )
    
    #print "\n Top 10 nodes based on Cliques count: " , nodeCliqueList[:10]
    #print "\n Top 10 nodes based on Raw Clique size: ",  rawCliqueList[:10]
    print "\n Top 10 nodes based on weighted Clique size: " , weightedCliqueList[:10]
    
    minNodeCliqueCount = nodeCliqueList[-1][1]
    maxNodeCliqueCount = nodeCliqueList[0][1]

    minRawCliqueScore = rawCliqueList[-1][1]
    maxRawCliqueScore = rawCliqueList[0][1]

    minWeightedCliqueScore = weightedCliqueList[-1][1]
    maxWeightedCliqueScore = weightedCliqueList[0][1]
    
    for node, score in nodeCliqueList:
        if not NodeAttributes.get(node, None):
            NodeAttributes[node] = dict()
        NodeAttributes[node]['nodeClique'] = score
        NodeAttributes[node]['normNodeClique'] = float(score - minNodeCliqueCount)/float(maxNodeCliqueCount - minNodeCliqueCount)
        
    for node, score in rawCliqueList:
        NodeAttributes[node]['rawClique'] = score
        NodeAttributes[node]['normRawClique'] = float(score - minRawCliqueScore)/float(maxRawCliqueScore - minRawCliqueScore)
    
    for node, score in weightedCliqueList:
        NodeAttributes[node]['weightedClique'] = score
        NodeAttributes[node]['normWeightedClique'] = float(score - minWeightedCliqueScore)/float(maxWeightedCliqueScore - minWeightedCliqueScore)
    
    #print "\nNode 1874 features: ", NodeAttributes[1874]
    
    return 


# ## Compute Weighted Social Score 

# ### Social Score is computed as follows 
# 
# \begin{align}
# w_x * C_x & = w_x * 100 * \left[ \frac{x_i - infx}{sup\ x - inf\ x} \right] \\
# \\
# score & = \frac{\Sigma_{all\ x} w * C_x}{\Sigma_{all\ x} w}
# \end{align}

# In[28]:


def ComputeSocialScore(NodeAttributes):
    
    socialScore = list()
    
    #
    # Weights:
    #
    # W = [ Weighted Clique, RawClique, NumClique, OutDegree, InDegree, Cluster Coeff, Betweeness, Avg ShortPath, Auth, Hub]
    #
    w_weightedClique = 0.9
    w_rawClique = 0.8
    w_numClique = 0.7
    w_outDegree = 0.6
    w_inDegree = 0.6
    w_clusterCoeff = 0.3 
    w_betweeness = 0.3 
    w_shortpath = 0.5 
    w_auth = 0.2 
    w_hub = 0.1 

    w = np.array([w_weightedClique,                 w_rawClique,                  w_numClique,                  w_outDegree,                  w_inDegree,                  w_clusterCoeff,                  w_betweeness,                  w_shortpath,                  w_auth,                  w_hub])

    w_sum = np.sum(w)

    for node, attributes in NodeAttributes.iteritems():
        weightedClique = attributes.get('normWeightedClique', 0.0)
        rawClique = attributes.get('normRawClique', 0.0)
        numClique = attributes.get('normNodeClique', 0.0)
        outDeg =  attributes.get('NormOutDegree', 0.0)
        inDeg =  attributes.get('NormInDegree', 0.0)
        clusterCoeff =  attributes.get('NormClusterCoeff', 0.0)
        betweeness = attributes.get('normBetweeness', 0.0)
        shortestPath = attributes.get('normAvgShortPathLen', 0.0)
        authScore = attributes.get('normAuthScore', 0.0)
        hubSccore = attributes.get('normHubScore', 0.0)
    
        C_x = np.array([weightedClique,                        rawClique,                        numClique,                        outDeg,                        inDeg,                        clusterCoeff,                        betweeness,                        shortestPath,                        authScore,                        hubSccore])
    
        score = 100.0 * np.dot(w, C_x)/w_sum
        socialScore.append((node, score))
        
    socialScore.sort(key=lambda x: x[1], reverse=True)
    print socialScore[:10]
    
    return socialScore


# In[31]:


def ComputeNodeScore(df, G, modified=False, threshold=0):
    #
    # Create a Node Attribute Dictionary
    #
    NodeAttributes = dict()
    
    #
    # Get Node Statistics and Graph attributes
    #
    GetRawStatistics(G, NodeAttributes)
    
    #
    # Get Social Attributes for nodes 
    #
    if modified:
        print "Get Modified Social Score Attributes... "
        GetModifiedSocialAttributes(df, NodeAttributes, threshold=threshold) 
    else:
        print "Get Social Score Attributes... "
        GetSocialAttributes(df, NodeAttributes, threshold=threshold)
    
    print "Compute Social Score... "
    socialScore = ComputeSocialScore(NodeAttributes)

    return socialScore, NodeAttributes 
    


# In[32]:


if __name__ == '__main__':
    
    df, G = GenerateGraph(filename='/home/merchantsameer2014/project/dnc-temporalGraph/out.dnc-temporalGraph')
    
    start_time = datetime.now()
    socialScore, NodeAttributes = ComputeNodeScore(df, G, modified=True, threshold=0)
    end_time = datetime.now()
    print('Total time to compute Social Score: {}'.format(end_time - start_time))

    
    with open('socialScoreModifed_all_test.txt', 'w') as fd:
        for (node, score) in socialScore:
            fd.write("%r\t%r\n" % (node, score))
    
    '''
    with open('../results/nodeSocialScoreFeature.txt', 'w') as fd:
        fd.write("node,normNodeClique,normRawClique,normWeightedClique,nodeClique,rawClique,weightedClique\n")
        for (node, attributes) in NodeAttributes.iteritems():
            fd.write("%r,%r,%r,%r,%r,%r,%r\n" % (node,\
                                        attributes.get('normNodeClique', 0.0),\
                                        attributes.get('normRawClique', 0.0),\
                                        attributes.get('normWeightedClique', 0.0),\
                                        attributes.get('nodeClique', 0.0),\
                                        attributes.get('rawClique', 0.0),\
                                        attributes.get('weigthedClique', 0.0),\
                                       ))
          
    '''


# In[ ]:





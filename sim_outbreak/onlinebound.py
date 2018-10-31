def GetBound(network, hardened_ids, outbreak, budget):
    current_reward = outbreak(hardened_ids)
    
    networkAllNodes = [node.GetId() for node in network.GetNodes()] # list of all the nodes in the network
    explorationNodes = list(set(networkAllNodes) - set(hardened_ids)) # V\A
    explorationPayoffs = []
    
    for s in explorationNodes:
        explorationSet = list(hardened_ids).append(s)
        payoff = outbreak(explorationSet) - current_reward
        explorationPayoffs.append(payoff)
    
    sortedPayoffs = explorationPayoffs.sort(reverse=True) # descending payoffs
    
    bound = current_reward
    for payoff in sortedPayoffs[:budget]: # grab the payoffs within budget
        bound = bound + payoff
    
    return bound
    
    

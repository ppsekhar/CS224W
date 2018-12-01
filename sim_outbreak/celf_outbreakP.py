# creates historic record of deterministic infections, live edges
# given how many runs, p_initial, p_infect
# returns a list of lists. each sublist contains the nodes that are infected in an outbreak in chronological order
# this function is used to create live edges for CELF in maximizing outbreak detection and minimizing population affected

def createLiveEdges(runs, p_initial_infect, p_infect, n=2029, seed=0, debug=False):
    random.seed(seed)
    timestampsOrdered = orderTimestamps('out.dnc-temporalGraph')
    
    
    num_nodes_infect = math.floor(n * p_initial_infect)
    lists_infected_nodes = [] # list of lists of infected nodes from every run
    
    
    for run in range(runs): # go thru runs
        cur_infected_ids = []
        
        # Mark patient zeros
        while len(cur_infected_ids) < num_nodes_infect:
            nID = random.randint(1,n) 
            if nID not in cur_infected_ids:
                cur_infected_ids.append(nID)
        
        for timestamp in timestampsOrdered: # cycle thru the timestamps in the e-mails
            
            sourceNode = timestamp[1]
            destNode = timestamp[2]
            
            # this logic is used to infect neighbors
            if sourceNode in cur_infected_ids: # source node is infected, so we can try to infect
                if destNode not in cur_infected_ids: # destination node isn't infected, so we can try to infect
                    infected = False # flag to track whether infection successfully transmits
                    for _ in range(timestamp[3]): # since an edge w/ the same timestamp can occur multiple times
                        if random.uniform(0, 1) < p_infect: # flip a coin to infect neighbor
                            infected = True
                            cur_infected_ids.append(destNode)
                            break # b/c we do have an infection, so no need to try to keep infecting
            
        lists_infected_nodes.append(cur_infected_ids)
        
    return lists_infected_nodes

def celf_outbreakP_live_edges(p_initial_infect, p_infect, runs_per_marginal_node, seed=0, n=2029, debug=False):
    
    print 'Running CELF to optimize detection probability w/ live edges'
    results = open("CELF_outbreak_detection_probability_live_edge.txt", "w")
    results.write("P_infect = " + str(p_infect) + " P_initial_infect = " + str(p_initial_infect) + " Runs per marginal node = " + str(runs_per_marginal_node))
    results.write("\nNode ID\tReward so Far\tMarginal gain\n")
    
    lists_infected_nodes = createLiveEdges(runs_per_marginal_node, p_initial_infect, p_infect, debug=debug) # can modify seed, n, debug default parameters here
    
    marginals = np.zeros(n)
    
    # select the first node by exhuastively computing all marginal benefits
    for potential_detector in range(1,n+1): # calculate marginals for each node
        runs = [1 if potential_detector in cur_infected_ids else 0 for cur_infected_ids in lists_infected_nodes]
        marginals[potential_detector - 1] = sum(runs) / float(runs_per_marginal_node)
        if debug:
            print "Straight up gain for node " + str(potential_detector) + " is: " + str(marginals[potential_detector - 1])
    
    sorted_marginals_indices = np.argsort(marginals) # ascending order, sorted by which nodes have the best metric
    best_marginal_node = sorted_marginals_indices[-1] + 1 
    rewards_so_far = np.max(marginals) # used to track current best reward
    marginals[best_marginal_node - 1] = -99 # since we already selected it
    
    selected_detectors = [best_marginal_node] # we have found our first best node
    
    print "We have our first best node: "
    print selected_detectors
    
    results.write(str(best_marginal_node) + '\t' + str(rewards_so_far) + '\t' + str(rewards_so_far) + '\n' )
    
    for i in range(1, 20): # select the next 19 detectors
        
        if debug:
            print "Trying to find the " + str(i+1) + "th detector"
        
        # need to re-evaluate the top node once, at least
        sorted_marginals_indices = np.argsort(marginals)
        old_top_node = sorted_marginals_indices[-1] + 1 # the top node from the previous iteration
        new_detectors = list(selected_detectors)
        new_detectors.append(old_top_node)

        runs = [bool(set(new_detectors) & set(infected_ids)) for infected_ids in lists_infected_nodes] # check if any detectors are in the list of infected nodes
        marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far
        
        sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
        new_top_node = sorted_marginals_indices[-1] + 1
        
        while new_top_node != old_top_node: # this is where we need to re-evaluate the next top node
            old_top_node = sorted_marginals_indices[-1] + 1 # the top node from the previous iteration
            new_detectors = list(selected_detectors)
            new_detectors.append(old_top_node)
            runs = [bool(set(new_detectors) & set(infected_ids)) for infected_ids in lists_infected_nodes] # check if any detectors are in the list of infected nodes
            marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far

            sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
            new_top_node = sorted_marginals_indices[-1] + 1
        
        
        
        best_node = new_top_node
        
        print "After doing CELF, we have found the " + str (i+1) + "th detector w/ best marginal gain = " + str(best_node)
        selected_detectors.append(best_node)
        rewards_so_far = rewards_so_far + marginals[best_node - 1] # update the rewards w/ the marginals gained by the current node
        results.write(str(best_node) + '\t' + str(rewards_so_far) + '\t' + str(marginals[best_node - 1]) + '\n')
        marginals[best_node - 1] = -99
        print "Outbreak detection probability so far: " + str(rewards_so_far)
        
        
            
    results.close()

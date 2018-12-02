def celf_population_live_edges(p_initial_infect, p_infect, runs_per_marginal_node, seed=0, n=2029, debug=False):
    
    print 'Running CELF to minimize population affected w/ live edges'
    results = open("CELF_population_live_edge.txt", "w")
    results.write("P_infect = " + str(p_infect) + " P_initial_infect = " + str(p_initial_infect) + " Runs per marginal node = " + str(runs_per_marginal_node))
    results.write("\nNode ID\tReward so Far\tMarginal gain\n")
    
    lists_infected_nodes = createLiveEdges(runs_per_marginal_node, p_initial_infect, p_infect, n=n, seed=seed, debug=debug) # can modify seed, n, debug default parameters here
    
    marginals = np.zeros(n)
    
    # how to calculate population affected: if the detector is in the infected nodes, we take the index of the detector b/c the infected nodes are in chronological order
    # if not, we just take the length
    # select the first node by exhuastively computing all marginal benefits
    for potential_detector in range(1,n+1): # calculate marginals for each node
        runs = [infected_ids.index(potential_detector)+1 if potential_detector in infected_ids else len(infected_ids) for infected_ids in lists_infected_nodes]
        marginals[potential_detector - 1] = sum(runs) / float(runs_per_marginal_node)
        if debug:
            print "Straight up gain for node " + str(potential_detector) + " is: " + str(marginals[potential_detector - 1])
    
    sorted_marginals_indices = np.argsort(marginals) # ascending order, sorted by which nodes have the best metric
    best_marginal_node = sorted_marginals_indices[0] + 1 
    rewards_so_far = np.min(marginals) # used to track current best reward
    marginals[best_marginal_node - 1] = 9999 # since we already selected it
    
    selected_detectors = [best_marginal_node] # we have found our first best node
    
    print "We have our first best node: "
    print selected_detectors
    
    results.write(str(best_marginal_node) + '\t' + str(rewards_so_far) + '\t' + str(rewards_so_far) + '\n' )
    
    for i in range(1, 20): # select the next 19 detectors
        
        if debug:
            print "Trying to find the " + str(i+1) + "th detector"
        
        # need to re-evaluate the top node once, at least
        sorted_marginals_indices = np.argsort(marginals)
        old_top_node = sorted_marginals_indices[0] + 1 # the top node from the previous iteration
        new_detectors = list(selected_detectors)
        new_detectors.append(old_top_node)

        # lazily evaluate for the top node
        runs = [] # records the results for each run
        for run in range(runs_per_marginal_node): # go thru the runs
            infected_ids = lists_infected_nodes[run]
            if bool(set(new_detectors) & set(infected_ids)): # detector is in the set of infected ids
                for infected_node in infected_ids: # let's go thru the infected IDs to see which one is affected
                    if infected_node in new_detectors:
                        runs.append(infected_ids.index(infected_node) + 1)
                        break # since we found the earliest detection
            else: # outbreak not detected, so everyone got affected
                runs.append(len(infected_ids))
            
        marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far
        
        sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
        new_top_node = sorted_marginals_indices[0] + 1
        
        while new_top_node != old_top_node: # this is where we need to re-evaluate the next top node
            old_top_node = sorted_marginals_indices[0] + 1 # the top node from the previous iteration
            new_detectors = list(selected_detectors)
            new_detectors.append(old_top_node)
            
            runs = [] # records number of runs
            for run in range(runs_per_marginal_node): # go thru the runs
                infected_ids = lists_infected_nodes[run]
                if bool(set(new_detectors) & set(infected_ids)): # detector is in the set of infected ids
                    for infected_node in infected_ids: # let's go thru the infected IDs to see which one is affected
                        if infected_node in new_detectors:
                            runs.append(infected_ids.index(infected_node) + 1)
                            break
                else: # outbreak not detected, so everyone got affected
                    runs.append(len(infected_ids))            
            
            marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far

            sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
            new_top_node = sorted_marginals_indices[0] + 1
        
        
        
        best_node = new_top_node
        
        print "After doing CELF, we have found the " + str (i+1) + "th detector w/ best marginal gain = " + str(best_node)
        selected_detectors.append(best_node)
        rewards_so_far = rewards_so_far + marginals[best_node - 1] # update the rewards w/ the marginals gained by the current node
        results.write(str(best_node) + '\t' + str(rewards_so_far) + '\t' + str(marginals[best_node - 1]) + '\n')
        marginals[best_node - 1] = 9999
        print "Population affected so far: " + str(rewards_so_far)
        
        
            
    results.close()
    

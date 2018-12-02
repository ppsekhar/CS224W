# creates historic record of deterministic infections, live edges
# given how many runs, p_initial, p_infect
# returns a list of dictionaries. each dictionary represents an outbreak, mapping an infected node to its time of infection
# this function is used to create live edges for CELF in minimizing time to detection

def createLiveEdges_steps(runs, p_initial_infect, p_infect, n=2029, seed=0, debug=False):
    random.seed(seed)
    timestampsOrdered = orderTimestamps('out.dnc-temporalGraph')
    
    
    num_nodes_infect = math.floor(n * p_initial_infect)
    lists_infected_nodes = [] # list of lists of infected nodes from every run
    
    
    for run in range(runs): # go thru runs
        if run % 10000 == 0:
            print "Creating Live Edge #" + str(run)
        
        cur_infected_ids = {}
        
        # Mark patient zeros
        while len(cur_infected_ids) < num_nodes_infect:
            nID = random.randint(1,n) 
            if nID not in cur_infected_ids:
                cur_infected_ids[nID] = 0
        
        step = 0 
        
        for timestamp in timestampsOrdered: # cycle thru the timestamps in the e-mails
            
            sourceNode = timestamp[1]
            destNode = timestamp[2]
            
            # this logic is used to infect neighbors
            if sourceNode in cur_infected_ids: # source node is infected, so we can try to infect
                if destNode not in cur_infected_ids: # destination node isn't infected, so we can try to infect
                    infected = False # flag to track whether infection successfully transmits
                    for email in range(timestamp[3]): # since an edge w/ the same timestamp can occur multiple times
                        if random.uniform(0, 1) < p_infect: # flip a coin to infect neighbor
                            infected = True
                            cur_infected_ids[destNode] = step + email # timestamp of infection
                            break # b/c we do have an infection, so no need to try to keep infecting
            step = step + timestamp[3] # increment the step
        
        lists_infected_nodes.append(cur_infected_ids)
        
    return lists_infected_nodes
    
 def celf_steps_live_edges(p_initial_infect, p_infect, runs_per_marginal_node, seed=0, n=2029, debug=False):
    
    print 'Running CELF to minimize simulation steps w/ live edges'
    results = open("CELF_population_steps.txt", "w")
    results.write("P_infect = " + str(p_infect) + " P_initial_infect = " + str(p_initial_infect) + " Runs per marginal node = " + str(runs_per_marginal_node))
    results.write("\nNode ID\tReward so Far\tMarginal gain\n")
    
    lists_infected_dicts = createLiveEdges_steps(runs_per_marginal_node, p_initial_infect, p_infect, n=n, seed=seed, debug=debug) # can modify seed, n, debug default parameters here
    
    marginals = np.zeros(n)
    
    # how to calculate simulation steps: look thru the keys in the dictionary, if it is not in the keys, then we automatically fill it w/ the max number of simulation steps
    for potential_detector in range(1,n+1): # calculate marginals for each node
        runs = [infected_dict[potential_detector] if potential_detector in infected_dict.keys() else 39265 for infected_dict in lists_infected_dicts]
        marginals[potential_detector - 1] = sum(runs) / float(runs_per_marginal_node)
        if debug:  # select the first node by exhuastively computing all marginal benefits
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
            infected_dict = lists_infected_dicts[run]
            if bool(set(new_detectors) & set(infected_dict.keys() )): # detector is in the set of infected ids
                alerted_detectors = set(new_detectors) & set(infected_dict.keys() )  # grab the set of detectors that was alerted
                alert_times = [infected_dict[detector] for detector in alerted_detectors]
                runs.append(min(alert_times)) # get the first time of alert
            else: # outbreak not detected, so last simulation step
                runs.append(39265)
            
        marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far
        
        sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
        new_top_node = sorted_marginals_indices[0] + 1
        
        while new_top_node != old_top_node: # this is where we need to re-evaluate the next top node
            old_top_node = sorted_marginals_indices[0] + 1 # the top node from the previous iteration
            new_detectors = list(selected_detectors)
            new_detectors.append(old_top_node)
            
            runs = [] # records number of runs
            for run in range(runs_per_marginal_node): # go thru the runs
                infected_dict = lists_infected_dicts[run]
                if bool(set(new_detectors) & set(infected_ids)): # detector is in the set of infected ids
                    alerted_detectors = set(new_detectors) & set(infected_dict.keys() ) # grab the set of detectors that was alerted
                    alert_times = [infected_dict[detector] for detector in alerted_detectors]
                    runs.append(min(alert_times)) # get the first time of alert
                else: # outbreak not detected, so last simulation step
                    runs.append(39265)            
            
            marginals[old_top_node - 1] = sum(runs) / float(runs_per_marginal_node) - rewards_so_far

            sorted_marginals_indices = np.argsort(marginals) # sort now that we have re-evaluted for top node
            new_top_node = sorted_marginals_indices[0] + 1
        
        
        
        best_node = new_top_node
        
        print "After doing CELF, we have found the " + str (i+1) + "th detector w/ best marginal gain = " + str(best_node)
        selected_detectors.append(best_node)
        rewards_so_far = rewards_so_far + marginals[best_node - 1] # update the rewards w/ the marginals gained by the current node
        results.write(str(best_node) + '\t' + str(rewards_so_far) + '\t' + str(marginals[best_node - 1]) + '\n')
        marginals[best_node - 1] = 9999
        print "Simulation steps so far: " + str(rewards_so_far)
        
        
            
    results.close()
    

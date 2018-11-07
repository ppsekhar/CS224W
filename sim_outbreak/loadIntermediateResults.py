def loadIntermediateResults(filename): 

    grid_search_intermediate = []
    with open(filename) as f3:
        line = f3.readline()
        while line:
            line = line.strip()
            result = []
            line = line.split('\t')
            for i in range(7):
                if i == 3: # processing the timedelta, which is in the format of "305 days, 3:26:52"
                    if "days" not in line[3]: # took less than a day
                        result.append(1) # round up to one day
                    else: # normal format "xx days"
                        result.append( int( line[3].split(' ', 1)[0] ) )
                else:
                    result.append( float(line[i]) )
            grid_search_intermediate.append( result )
            line = f3.readline()
    return grid_search_intermediate
    
## sample code to load the file that varies p initial infect while holding p_infect = 0.25 and total detectors to 200
grid_search_25pinfect_200detectors = loadIntermediateResults("gridSearch_results_pInitialInfect_0.25pInfect_200detectors.txt")

p_initial_infect_BY_outbreakP = []
for p_initial_infect in p_initial_infect_params:
    outbreakP = [ result[6] for result in grid_search_25pinfect_200detectors if result[0] == p_initial_infect ]
    p_initial_infect_BY_outbreakP.append( outbreakP )
p_initial_infect_BY_outbreakP_avg = np.array( [ np.mean( np.array(a) ) for a in p_initial_infect_BY_outbreakP])
p_initial_infect_BY_outbreakP_std = np.array( [ np.std( np.array(a) ) for a in p_initial_infect_BY_outbreakP])
plt.figure(1, figsize=(12,12))
plt.subplot(4, 1, 1)
plt.errorbar(p_initial_infect_params, p_initial_infect_BY_outbreakP_avg, yerr=p_initial_infect_BY_outbreakP_std)
plt.xlabel("P initial infection")
plt.ylabel("outbreakP")
plt.title("outbreakP over p initial infect")
plt.xscale('log')

p_initial_infect_BY_steps = []
for p_initial_infect in p_initial_infect_params:
    steps = [ result[5] for result in grid_search_25pinfect_200detectors if result[0] == p_initial_infect ]
    p_initial_infect_BY_steps.append( steps )
p_initial_infect_BY_steps_avg = np.array( [ np.mean( np.array(a) ) for a in p_initial_infect_BY_steps])
#p_initial_infect_BY_steps_std = np.array( [ np.std( np.array(a) ) for a in p_initial_infect_BY_steps])
plt.figure(2, figsize=(12,12))
plt.subplot(4, 1, 2)
#plt.errorbar(p_initial_infect_params, p_initial_infect_BY_steps_avg, yerr=p_initial_infect_BY_steps_std)
plt.plot([1,2,3,4,5], p_initial_infect_BY_steps_avg)
plt.boxplot(p_initial_infect_BY_steps)
plt.xticks([1,2,3,4,5], p_initial_infect_params)
plt.xlabel("P initial infection")
plt.ylabel("Steps")
plt.title("Simulation steps over p initial infect")

p_initial_infect_BY_num_nodes_infected = []
for p_initial_infect in p_initial_infect_params:
    num_nodes_infected = [ result[4] for result in grid_search_25pinfect_200detectors if result[0] == p_initial_infect ]
    p_initial_infect_BY_num_nodes_infected.append( num_nodes_infected )
p_initial_infect_BY_num_nodes_infected_avg = np.array( [ np.mean( np.array(a) ) for a in p_initial_infect_BY_num_nodes_infected])
p_initial_infect_BY_num_nodes_infected_std = np.array( [ np.std( np.array(a) ) for a in p_initial_infect_BY_num_nodes_infected])
plt.figure(3, figsize=(12,12))
plt.subplot(4, 1, 3)
#plt.errorbar(p_initial_infect_params, p_initial_infect_BY_num_nodes_infected_avg, yerr=p_initial_infect_BY_num_nodes_infected_std)
plt.plot( [1,2,3,4,5], p_initial_infect_BY_num_nodes_infected_avg)
plt.boxplot(p_initial_infect_BY_num_nodes_infected)
plt.xticks([1,2,3,4,5], p_initial_infect_params)
plt.xlabel("P initial infection")
plt.ylabel("Number of nodes infected")
plt.title("Number of nodes infected over p initial infect")
#plt.xscale('log')

p_initial_infect_BY_time_to_detection = []
for p_initial_infect in p_initial_infect_params:
    time_to_detect = [ result[3] for result in grid_search_25pinfect_200detectors if result[0] == p_initial_infect ]
    p_initial_infect_BY_time_to_detection.append( time_to_detect )
p_initial_infect_BY_time_to_detection_avg = np.array( [ np.mean( np.array(a) ) for a in p_initial_infect_BY_time_to_detection])
p_initial_infect_BY_time_to_detection_std = np.array( [ np.std( np.array(a) ) for a in p_initial_infect_BY_time_to_detection])
plt.figure(4, figsize=(12,12))
plt.subplot(4, 1, 4)
plt.plot( [1,2,3,4,5], p_initial_infect_BY_time_to_detection_avg)
plt.boxplot(p_initial_infect_BY_time_to_detection)
plt.xticks([1,2,3,4,5], p_initial_infect_params)
#plt.errorbar(p_initial_infect_params, p_initial_infect_BY_time_to_detection_avg, yerr=p_initial_infect_BY_time_to_detection_std)

plt.xlabel("P initial infection")
plt.ylabel("Days to detection")
plt.title("Time to detection over p initial infect")

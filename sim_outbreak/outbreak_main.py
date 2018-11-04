import argparse, sys
from run_outbreak import loadDetectorIds, loadDNCNetwork
from runOutreakTimestamp import runOutBreakTimestamp2
import datetime

if __name__== "__main__":
	print 'Running Outbreak with Timestamps'
	parser=argparse.ArgumentParser()

	parser.add_argument('--graph_filename', help='graph to load', default='../dnc-temporalGraph/out.dnc-temporalGraph')
	parser.add_argument('--score_filename', help='scores to load as detectors', default='../socialScore/socialScore.txt')
	parser.add_argument('--p_infect', help='probability a node gets infected through edge if neighbor is infected')
	parser.add_argument('--total_detectors', help='number of nodes to select as detectors')
	parser.add_argument('--p_initial_infect', help='number of nodes to mark as infected initially')
	parser.add_argument('--p_detectors_alerted', help='number of detectors that must be alerted for simulation to end')
	parser.add_argument('--debug', help='True to print verbose outputs', default=False)
	parser.add_argument('--write_output_to_file', help='True to save results and inputs in text file', default=False)
	args = parser.parse_args()
	
	print 'ARGS: '
	print args

	graph_filename = args.graph_filename
	score_filename = args.score_filename
	p_initial_infect = float(args.p_initial_infect)
	p_infect = float(args.p_infect)
	p_infect_hardened = p_infect # No hardened nodes for now
	total_detectors = int(args.total_detectors)
	p_detectors_alerted = float(args.p_detectors_alerted)
	debug = args.debug
	write_output_to_file = args.write_output_to_file

	# Malformed input defaults to false
	debug_flag = False
	write_output = False

	if debug == 'True':
		debug_flag = True
	if write_output_to_file == 'True':
		write_output = True


	num_detectors_alerted = int(p_detectors_alerted * total_detectors) # Calculate raw number of detectors that must be alerted to end simulation
	
	t_recover = 30 # unused TODO: Include in SIS model
	detector_ids = loadDetectorIds(score_filename, total_detectors)
	hardened_ids = detector_ids # For now, no hardened IDs

	if debug:
		print 'NUM DETECTORS ALERTED' + str(num_detectors_alerted)
		print detector_ids

	N = loadDNCNetwork(graph_filename, p_infect, p_infect_hardened, t_recover, detector_ids, hardened_ids)
	detectors_alerted, time_to_detection, cur_infected_ids = runOutBreakTimestamp2(N, p_initial_infect, num_detectors_alerted, graph_filename, debug)
	

	if write_output:
		output_filename = str(datetime.datetime.now()) + '_outbreak_run.txt'
		with open(output_filename, 'a') as f:
			f.write('PARAMETERS:\n')
			f.write(str(args) + '\n')
			f.write('Detector IDs: ' + str(detector_ids) + '\n\n')
			f.write('RESULTS:\n')
			f.write('alerted detectors: ' + str(detectors_alerted) + '\n')
			f.write('infected id list: ' + str(cur_infected_ids) + '\n')
			f.write('time to detection: ' + str(time_to_detection) + '\n')
			f.write('number of infected nodes ' + str(len(cur_infected_ids)) + '\n')



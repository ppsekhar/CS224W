import csv
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
from ast import literal_eval
from sklearn import svm
from sklearn.linear_model import LogisticRegression

# TODO: 1) Run CELF on full data set (then 80/20) 2) Train logistic regression to find detectors 3) Train linear regression to rank the subset (today)
# Monday - see results, maybe try rank svm and regular svm
# Train full linear regression/rankSVM

# Load Graph using networkx
def loadGraph():
	G = "TODO"
	return G

def loadSocialScoreFeatures():
	features = [] # Load from file (order by node id)
	features_dict = {}
	with open('../results/nodeSocialScoreFeature.txt') as featureFile: #change
		# skip header 
		i = 0
		for line in featureFile:
			if i != 0:
				values = line.split(',')
				featureList = [float(value) for value in values]
				nID = int(featureList.pop(0))
				features.append(featureList)
				features_dict[nID] = featureList
			i+=1

	#print len(features)
	return features, features_dict



def loadGreedyLabels():
	numNodes = 1891 # (excludes disconnected nodes with no edges)
	labels = [] # Load from file (order by node id)
	nodeOrder = {}
	order = 1
	filename = '../results/CELF_outbreak_detection_probability)live_edge.txt'
	with open(filename) as labelFile:
		i = 0
		for line in labelFile:
			if i > 3:
				nid = 0
				values = line.split('	')
				nodeOrder[int(values[0])] = order
				order+=1  
			i+=1
	
	for nID in range(numNodes):
		if nID in nodeOrder:
			labels.append(nodeOrder[nID])
		else:
			labels.append(-1)

	return labels


# Split data (80/20)
def splitData():
	train = []
	test = []
	# Generate node IDs to put in train/test (train = first 80% of edges for now)

# Fit with scikit learn linear regression model (whole dataset)
def trainLinear(trainData, labels):
	regr = linear_model.LinearRegression()
	regr.fit(trainData, labels)
	predictions = regr.predict(trainData)
	print predictions
	print("Mean squared error: %.2f" % mean_squared_error(labels, predictions))
	print('Variance score: %.2f' % r2_score(labels, predictions))
	
	# Plot
	# plt.scatter(trainData, labels,  color='black')
	# plt.plot(trainData, predictions, color='blue', linewidth=3)

	# plt.xticks(())
	# plt.yticks(())

	# plt.show()

def trainRankSVM():
	# Rebuild dataset
	print 'rank svm'

def splitDataForTwoModels(labels):
	is_detector_labels = [] # 0 or 1
	rank_labels_linear = [] # Order (option 1)
	rank_labels_svm = [] # Pairwise (option 2)


def trainTwoModels():
	print 'Logistic regression to split models and then linear to rank'
	# Predict detectors using logistic regression (OR SVM)
	# Predict rank using linear regression (OR RANK SVM)

# Predict social scores on test data -> select top k (later)
def predict(testData, labels):
	predictions = []
	return predictions

# Run outbreak - report results (time to detection, etc)
def runOutbreak():
	print 'Running outbreak'
	# label top k test data nodes as detectors
	# run outbreak on this smaller Graph 1000

def loadTrainingData(features_dict):
	filename = "../sim_outbreak/regression_data_50_detectors.txt"
	train_X = []
	train_Y = []
	with open(filename) as dataFile:
		for line in dataFile:
			if line.find("Trigger") == -1:
				values = line.split('|')
				order = values[0]
				start_infected_nodes = values[1]

				orderList = list(literal_eval(order))
				infectedList = list(literal_eval(start_infected_nodes))
				if len(orderList) > 0:
					for i in range(len(orderList)):
						rank = i + 1
						nID = orderList[i]
						feature_vec = features_dict[nID]
						for infectedID in infectedList: # Append social scores of initial infected nodes
							if infectedID in features_dict:
								feature_vec = feature_vec + features_dict[infectedID]
							else:
								newList = [0 for i in range(len(features_dict[nID]))]
								feature_vec = feature_vec + newList
						train_X.append(feature_vec)
						train_Y.append(rank)

	return train_X, train_Y

def trainSVM(train_X, train_Y):
	clf = svm.SVC(gamma='scale')
	clf.fit(train_X, train_Y)
	predictions = clf.predict(train_X)
	print predictions
	print("Mean squared error: %.2f" % mean_squared_error(train_Y, predictions))
	print('Variance score: %.2f' % r2_score(train_Y, predictions))

def buildRankData(features_dict):
	filename = "../sim_outbreak/regression_data_50_detectors.txt"
	train_X = []
	train_Y = []
	with open(filename) as dataFile:
		for line in dataFile:
			if line.find("Trigger") == -1:
				values = line.split('|')
				order = values[0]
				start_infected_nodes = values[1]

				orderList = list(literal_eval(order))
				infectedList = list(literal_eval(start_infected_nodes))
				for i in range(len(orderList)):
					for j in range(len(orderList)):
						if j > i:
							nID1 = orderList[i]
							nID2 = orderList[j]
							feature_vec = features_dict[nID1] + features_dict[nID2]
							reverse_feature_vec = features_dict[nID2] + features_dict[nID1]
							for infectedID in infectedList: # Append social scores of initial infected nodes
								if infectedID in features_dict:
									feature_vec = feature_vec + features_dict[infectedID]
									reverse_feature_vec = reverse_feature_vec + features_dict[infectedID]
								else:
									newList = [0 for i in range(len(features_dict[nID1]))]
									feature_vec = feature_vec + newList
									reverse_feature_vec = reverse_feature_vec + newList

							train_X.append(feature_vec)
							train_Y.append(1)
							train_X.append(reverse_feature_vec)
							train_Y.append(-1)

	return train_X, train_Y

def trainLogisticReg(train_X, train_Y):
	clf = LogisticRegression(random_state=0, solver='lbfgs', multi_class='multinomial').fit(train_X, train_Y)
	clf.predict(train_X)
	print 'MEAN ACCURACY'
	print clf.score(train_X, train_Y)

if __name__ == "__main__":
	features, features_dict = loadSocialScoreFeatures()
	print 'Loaded features'
	train_X, train_Y = loadTrainingData(features_dict)
	print 'Loaded training data'
	#labels = loadGreedyLabels()
	trainLinear(train_X, train_Y)
	#trainSVM(train_X, train_Y)
	ranked_X, ranked_Y = buildRankData(features_dict)
	#trainLogisticReg(ranked_X, ranked_Y)
	#trainSVM(ranked_X, ranked_Y)




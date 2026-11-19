import numpy as np
from scipy.spatial.distance import cdist

def nearest_neighbor(weights, train, test, labels):
    distances = cdist((weights.T @ test).T, (weights.T @ train).T, metric='euclidean')
    return labels[distances.argmin(axis=1)]

def accuracy(truth, prediction):
    return float(np.mean(np.asarray(truth) == np.asarray(prediction)))

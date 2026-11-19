import numpy as np

class TrainingTransform:
    """Statistics are fitted on training columns only."""
    def __init__(self, standardize=True):
        self.standardize = standardize

    def fit(self, x):
        self.mean = x.mean(axis=1, keepdims=True)
        self.scale = x.std(axis=1, ddof=1, keepdims=True) if self.standardize else np.ones_like(self.mean)
        self.scale[self.scale < 1e-12] = 1.0
        return self

    def transform(self, x):
        return (x - self.mean) / self.scale

    def inverse(self, x):
        return x * self.scale + self.mean

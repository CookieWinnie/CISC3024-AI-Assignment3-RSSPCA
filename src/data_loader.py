"""Load the authors' already resized ORL resource without changing pixel order."""
from pathlib import Path
import hashlib
import numpy as np
from scipy.io import loadmat

ORL_SHA256 = 'f59adc3a173cca9685cafc13645f6af4e05e62a16190049c63ebedfeeece1fcd'

def load_orl(path='data/ORL.mat'):
    path = Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != ORL_SHA256:
        raise ValueError('ORL file differs from the verified author resource')
    data = loadmat(path)
    images, labels = data['x'], data['label'].ravel().astype(int)
    assert images.shape == (56, 46, 400)
    classes, counts = np.unique(labels, return_counts=True)
    assert np.array_equal(classes, np.arange(1, 41)) and np.all(counts == 10)
    assert np.isfinite(images).all() and images.min() >= 0 and images.max() <= 255
    # Each column is one image; MATLAB reshape and ind2sub use column order.
    return images.reshape((56 * 46, 400), order='F') / 255.0, labels, (56, 46)

def stratified_split(labels, n_train, seed, available=None):
    rng = np.random.default_rng(seed)
    available = np.arange(len(labels)) if available is None else np.asarray(available)
    train, test = [], []
    for label in np.unique(labels):
        indices = rng.permutation(available[labels[available] == label])
        if len(indices) <= n_train:
            raise ValueError('Each class needs both training and held-out observations')
        train.extend(indices[:n_train]); test.extend(indices[n_train:])
    return np.array(train), np.array(test)

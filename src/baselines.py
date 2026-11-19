import time
from scipy.linalg import svd
from .rss_pca import fit_components

def fit_pca(x, n_components):
    start = time.perf_counter()
    weights = svd(x, full_matrices=False, check_finite=False)[0][:, :n_components]
    return weights, [], {'seconds': time.perf_counter() - start, 'components': []}

def fit_pcal1(x, n_components):
    return fit_components(x, n_components)

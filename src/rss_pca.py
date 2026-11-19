"""Python translation derived from yuzhounh/RSSPCA, commit 58ef723.

Wang et al., PLOS ONE 20(5), e0323281 (2025). GPL-3.0-only.
Retains upstream initialization, L2 stopping monitor and cumulative deflation.
"""
import time
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.linalg import svd

def spatial_laplacian(height, width):
    """Unweighted four-neighbor graph, MATLAB column-major image indexing."""
    index = np.arange(height * width).reshape((height, width), order='F')
    a = np.concatenate([index[:-1, :].ravel(), index[:, :-1].ravel()])
    b = np.concatenate([index[1:, :].ravel(), index[:, 1:].ravel()])
    rows, cols = np.r_[a, b], np.r_[b, a]
    adjacency = sparse.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(height * width,) * 2).tocsc()
    return sparse.diags(np.asarray(adjacency.sum(axis=1)).ravel(), format='csc') - adjacency

def normalize(w):
    norm = np.linalg.norm(w)
    if not np.isfinite(w).all() or not np.isfinite(norm) or norm < 1e-14:
        raise FloatingPointError('Degenerate or nonfinite projection; no arbitrary substitute returned')
    return w / norm

def rss_update(x, w, laplacian, eta1, eta2):
    """Exact sparse equivalent of U*((U+eta1*I+eta2*L*U)\v).

    (U+eta1 I+eta2 U L) U = U (U+eta1 I+eta2 L U),
    so this also equals paper Eq. (32), including zero diagonal entries.
    """
    if eta1 < 0 or eta2 < 0:
        raise ValueError('Parameters must be nonnegative')
    v = x @ np.sign(x.T @ w)
    if eta1 == 0 and eta2 == 0:
        return normalize(v)
    u = np.abs(w)
    if eta1 == 0:
        # Exact continuous extension of Eq. (30) for the smooth-only case.
        system = sparse.eye(len(w), format='csc') + eta2 * laplacian
        return normalize(spsolve(system, v))
    system = sparse.diags(u + eta1, format='csc') + eta2 * laplacian @ sparse.diags(u, format='csc')
    return normalize(u * spsolve(system, v))

def fit_components(x, n_components, laplacian=None, eta1=0.0, eta2=0.0, tol=1e-4, max_iter=100):
    """Shared upstream iteration for RSSPCA and its PCA-L1 special case."""
    start = time.perf_counter()
    x = np.array(x, dtype=float, copy=True)
    if not np.isfinite(x).all() or np.linalg.norm(x) < 1e-14:
        raise ValueError('Training data must be finite and nonzero')
    if not 1 <= n_components <= min(x.shape):
        raise ValueError('Invalid component count')
    if laplacian is None:
        laplacian = sparse.csc_matrix((x.shape[0], x.shape[0]))
    initial = svd(x, full_matrices=False, check_finite=False)[0][:, :n_components]
    weights = np.zeros((x.shape[0], n_components))
    traces, status = [], []
    for component in range(n_components):
        w = initial[:, component].copy()
        previous = np.linalg.norm(x.T @ w)
        for iteration in range(1, max_iter + 1):
            updated = rss_update(x, w, laplacian, eta1, eta2)
            projected = x.T @ updated
            l2_monitor = np.linalg.norm(projected)
            relative = abs(l2_monitor - previous) / max(previous, 1e-14)
            traces.append({'component': component + 1, 'iteration': iteration,
                           'l1_projection': float(np.abs(projected).sum()), 'l2_monitor': float(l2_monitor),
                           'relative_l2_change': float(relative),
                           'direction_change': float(min(np.linalg.norm(updated - w), np.linalg.norm(updated + w))),
                           'l1_weight': float(np.abs(updated).sum()), 'smoothness': float(updated @ (laplacian @ updated))})
            w = updated
            if relative <= tol:
                break
            previous = l2_monitor
        weights[:, component] = w
        status.append({'component': component + 1, 'iterations': iteration,
                       'converged_monitor': bool(relative <= tol), 'relative_l2_change': float(relative)})
        # Faithful to upstream: cumulative W on the already deflated X.
        # This is not assumed to be an orthogonal projector for RSSPCA.
        current = weights[:, :component + 1]
        x -= current @ (current.T @ x)
    return weights, traces, {'seconds': time.perf_counter() - start, 'components': status,
                            'gram_off_identity_fro': float(np.linalg.norm(weights.T @ weights - np.eye(n_components)))}

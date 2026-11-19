"""Controlled numerical checks independent of the sparse implementation."""
import numpy as np
import pytest
from scipy.linalg import svd
from src.rss_pca import spatial_laplacian, rss_update, fit_components
from src.preprocessing import TrainingTransform
from src.data_loader import load_orl, stratified_split
from src.reconstruction import reconstruct, reconstruction_metrics, corrupt_blocks
from src.recognition import nearest_neighbor, accuracy

def test_laplacian_against_coordinate_distances():
    h, w = 3, 4
    coords = np.array([(r, c) for c in range(w) for r in range(h)])
    distances = np.linalg.norm(coords[:, None] - coords[None, :], axis=2)
    a = (distances == 1).astype(float)
    expected = np.diag(a.sum(axis=1)) - a
    lap = spatial_laplacian(h, w).toarray()
    np.testing.assert_array_equal(lap, expected)
    np.testing.assert_array_equal(lap @ np.ones(h*w), 0)
    assert np.linalg.eigvalsh(lap).min() > -1e-12
    assert lap[2, 3] == 0  # Do not join consecutive columns at their boundaries.

@pytest.mark.parametrize('zeros', [False, True])
def test_sparse_update_matches_both_official_formulas(zeros):
    rng = np.random.default_rng(18)
    x, w = rng.normal(size=(12, 8)), rng.normal(size=12)
    if zeros: w[::3] = 0
    w /= np.linalg.norm(w)
    u, lap = np.diag(np.abs(w)), spatial_laplacian(3, 4)
    v = x @ np.sign(x.T @ w)
    e1, e2 = .03, 2.1
    matlab = u @ np.linalg.solve(u + e1*np.eye(12) + e2*lap.toarray()@u, v)
    paper = np.linalg.solve(u + e1*np.eye(12) + e2*u@lap.toarray(), u@v)
    actual = rss_update(x, w, lap, e1, e2)
    np.testing.assert_allclose(actual, matlab/np.linalg.norm(matlab), atol=2e-13)
    np.testing.assert_allclose(actual, paper/np.linalg.norm(paper), atol=2e-13)

def test_multiple_components_against_literal_dense_matlab_translation():
    rng = np.random.default_rng(91)
    original = rng.normal(size=(12, 20)); x = original.copy()
    lap = spatial_laplacian(3, 4)
    initial = svd(x, full_matrices=False)[0]
    weights = np.zeros((12, 3))
    for i in range(3):
        w = initial[:, i]; f = np.linalg.norm(x.T @ w)
        for iteration in range(100):
            v = x @ np.sign(x.T @ w); u = np.diag(np.abs(w))
            w = u @ np.linalg.solve(u + .01*np.eye(12) + .5*lap.toarray()@u, v)
            w /= np.linalg.norm(w)
            previous, f = f, np.linalg.norm(x.T @ w)
            if abs(f-previous)/previous <= 1e-4: break
        weights[:, i] = w
        x = (np.eye(12) - weights@weights.T) @ x
    actual, trace, info = fit_components(original, 3, lap, .01, .5)
    np.testing.assert_allclose(actual, weights, atol=1e-10)
    np.testing.assert_allclose(np.linalg.norm(actual, axis=0), 1)
    assert trace and np.isfinite(actual).all()

def test_pcal1_limit_and_reproducibility():
    x = np.random.default_rng(7).normal(size=(12, 16))
    w = np.ones(12)/np.sqrt(12)
    expected = x @ np.sign(x.T @ w); expected /= np.linalg.norm(expected)
    np.testing.assert_allclose(rss_update(x, w, spatial_laplacian(3, 4), 0, 0), expected)
    a = fit_components(x, 3)[0]; b = fit_components(x, 3)[0]
    np.testing.assert_array_equal(a, b)

def test_zero_and_nonfinite_are_controlled():
    with pytest.raises(ValueError): fit_components(np.zeros((12, 8)), 3)
    with pytest.raises(FloatingPointError): rss_update(np.zeros((12, 8)), np.ones(12), spatial_laplacian(3, 4), .1, 1)

def test_training_only_statistics():
    train = np.array([[1., 2., 3.], [4., 4., 4.]])
    transform = TrainingTransform().fit(train)
    np.testing.assert_allclose(transform.mean.ravel(), [2, 4])
    before = transform.mean.copy()
    transform.transform(np.full((2, 10), 1000.))
    np.testing.assert_array_equal(transform.mean, before)
    np.testing.assert_allclose(transform.inverse(transform.transform(train)), train)

def test_nonorthogonal_reconstruction_and_metrics():
    weights = np.array([[1., 1.], [0., 1.], [1., 0.]])
    x = np.array([[2., 3.], [1., 0.], [0., 2.]])
    reconstructed = reconstruct(weights, x)
    np.testing.assert_allclose(weights.T@(x-reconstructed), 0, atol=1e-13)
    np.testing.assert_allclose(reconstruct(weights, reconstructed), reconstructed, atol=1e-13)
    mse, psnr = reconstruction_metrics(np.zeros((3, 2)), np.full((3, 2), .1))
    assert mse == pytest.approx(.01) and psnr == pytest.approx(20)

def test_orl_splits_and_noise():
    x, y, shape = load_orl()
    train, test = stratified_split(y, 7, 2026)
    inner, val = stratified_split(y, 5, 2027, train)
    assert x.shape == (2576, 400) and len(train) == 280 and len(test) == 120
    assert not set(train)&set(test) and not set(inner)&set(val)
    assert set(inner)|set(val) == set(train)
    assert np.all(np.unique(y[test], return_counts=True)[1] == 3)
    corrupted, coordinates = corrupt_blocks(x[:, train], shape, 5, .2)
    assert len(coordinates) == 56
    np.testing.assert_array_equal(corrupted, corrupt_blocks(x[:, train], shape, 5, .2)[0])
    assert np.count_nonzero(corrupted != x[:, train]) == 56*14*12

def test_nearest_neighbor():
    train = np.array([[0., 5.], [0., 5.]])
    prediction = nearest_neighbor(np.eye(2), train, np.array([[.1, 4.9], [0., 5.]]), np.array([1, 2]))
    assert accuracy([1, 2], prediction) == 1.

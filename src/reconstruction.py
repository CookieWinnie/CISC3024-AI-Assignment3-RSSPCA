import numpy as np

def corrupt_blocks(x, shape, seed, fraction=1.0, block=(14, 12)):
    """Select floor(fraction*n) images; overwrite a uniformly positioned block."""
    rng = np.random.default_rng(seed)
    result = x.copy()
    chosen = np.sort(rng.choice(x.shape[1], int(np.floor(fraction*x.shape[1])), replace=False))
    coordinates = []
    for i in chosen:
        top = int(rng.integers(shape[0] - block[0] + 1))
        left = int(rng.integers(shape[1] - block[1] + 1))
        image = result[:, i].reshape(shape, order='F')
        image[top:top+block[0], left:left+block[1]] = rng.integers(0, 2, size=block)
        coordinates.append({'column': int(i), 'top': top, 'left': left})
    return result, coordinates

def reconstruct(weights, centered):
    # Euclidean projection onto span(W); W W^T is generally wrong here.
    return weights @ (np.linalg.pinv(weights, rcond=1e-10) @ centered)

def reconstruction_metrics(truth, reconstructed):
    mse_per_image = np.mean((truth - reconstructed)**2, axis=0)
    psnr_per_image = 10 * np.log10(1.0 / np.maximum(mse_per_image, 1e-30))
    return float(mse_per_image.mean()), float(psnr_per_image.mean())

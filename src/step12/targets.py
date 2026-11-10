"""Step 12 non-IQP target families (specs/step12_nonIQP_targets.md). Scales are guesses except beta."""
from __future__ import annotations

from itertools import combinations

import numpy as np

from src.step1.bits import parity_matrix

K_LCM = 4       # guess: latent classes
N_W4 = 6        # mirrors iqp4's 6 weight-4 generators


def _bits(n: int) -> np.ndarray:
    i = np.arange(2**n, dtype=np.int64)
    return ((i[:, None] >> np.arange(n)[None, :]) & 1).astype(np.float64)


def lcm_params(seed: int, n: int):
    rng = np.random.default_rng(12000 + seed)
    w = rng.dirichlet(np.ones(K_LCM))
    z = rng.normal(0.0, 1.0, (K_LCM, n))
    return w, z


def lcm_target(beta: float, seed: int, n: int) -> np.ndarray:
    """p(x) = sum_k w_k prod_j q_kj^x_j (1 - q_kj)^(1 - x_j), q = sigmoid(beta z)."""
    w, z = lcm_params(seed, n)
    a = beta * z
    log_q, log_1q = -np.logaddexp(0.0, -a), -np.logaddexp(0.0, a)
    X = _bits(n)
    logp = X @ log_q.T + (1.0 - X) @ log_1q.T + np.log(w)[None, :]
    m = logp.max()
    p = np.exp(logp - m).sum(axis=1)
    return p / p.sum()


def mask(idx) -> int:
    return int(sum(1 << j for j in idx))


def ising4_params(seed: int, n: int):
    """(masks, coefficients) of E: fields, all pairs, n random triples, 6 random quadruples."""
    rng = np.random.default_rng(13000 + seed)
    h = rng.normal(0.0, 0.5, n)                                  # N(0, 0.25)
    pairs = list(combinations(range(n), 2))
    J = rng.normal(0.0, 1.0 / np.sqrt(n), len(pairs))
    trip_all = list(combinations(range(n), 3))
    trips = [trip_all[i] for i in sorted(rng.choice(len(trip_all), n, replace=False))]
    Kt = rng.normal(0.0, 1.0 / np.sqrt(n), n)
    quad_all = list(combinations(range(n), 4))
    quads = [quad_all[i] for i in sorted(rng.choice(len(quad_all), N_W4, replace=False))]
    L = rng.normal(0.0, 1.0, N_W4)
    masks = [mask((j,)) for j in range(n)] + [mask(t) for t in pairs] + [mask(t) for t in trips] + [mask(t) for t in quads]
    return np.array(masks, dtype=np.int64), np.concatenate([h, J, Kt, L])


def ising4_target(beta: float, seed: int, n: int) -> np.ndarray:
    masks, c = ising4_params(seed, n)
    E = parity_matrix(n, masks) @ c
    e = beta * E
    p = np.exp(e - e.max())
    return p / p.sum()


FAMILIES = {"lcm": lcm_target, "ising4": ising4_target}

"""Step 12 tests (specs/step12_nonIQP_targets.md), written before the grid."""
import numpy as np

from src.step1.bits import popcount
from src.step12 import targets as T


def test_lcm_explicit():
    n, beta, seed = 6, 1.3, 3
    w, z = T.lcm_params(seed, n)
    q = 1 / (1 + np.exp(-beta * z))
    p = np.zeros(2**n)
    for x in range(2**n):
        b = [(x >> j) & 1 for j in range(n)]
        p[x] = sum(w[k] * np.prod([q[k, j] if b[j] else 1 - q[k, j] for j in range(n)]) for k in range(T.K_LCM))
    assert np.max(np.abs(T.lcm_target(beta, seed, n) - p / p.sum())) < 1e-14


def test_ising4_explicit():
    n, beta, seed = 6, 0.8, 4
    masks, c = T.ising4_params(seed, n)
    p = np.zeros(2**n)
    for x in range(2**n):
        p[x] = np.exp(beta * sum(ci * (-1) ** bin(x & int(m)).count("1") for m, ci in zip(masks, c)))
    assert np.max(np.abs(T.ising4_target(beta, seed, n) - p / p.sum())) < 1e-14


def test_deterministic_and_layout():
    for f in T.FAMILIES.values():
        assert np.array_equal(f(1.0, 11, 8), f(1.0, 11, 8))
    n = 10
    masks, _ = T.ising4_params(5, n)
    w = popcount(masks)
    assert (w == 4).sum() == 6 and (w == 3).sum() == n and (w == 2).sum() == n * (n - 1) // 2 and (w == 1).sum() == n

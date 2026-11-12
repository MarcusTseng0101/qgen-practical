"""Step 23 (specs/step23_local_iqp.md §2): the 4x4 device graph, its targets and the graph-restricted models."""
from __future__ import annotations

from itertools import combinations

import numpy as np

from src.step1.bits import all_bitstrings, parity_matrix
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import iqp_distribution
from src.step14.run import SIGMA

N_BITS, L = 16, 4
ISING_H, ISING_J = 0.2, 0.3   # guesses (spec §2): safety-target field and coupling scales


def _q(r, c):
    return r * L + c


def _mask(s):
    return int(sum(1 << j for j in s))


SINGLES = [(j,) for j in range(N_BITS)]
EDGES = [(_q(r, c), _q(r, c + 1)) for r in range(L) for c in range(L - 1)] + \
        [(_q(r, c), _q(r + 1, c)) for r in range(L - 1) for c in range(L)]
PLAQS = [(_q(r, c), _q(r, c + 1), _q(r + 1, c), _q(r + 1, c + 1)) for r in range(L - 1) for c in range(L - 1)]
TRIPLES = [t for P in PLAQS for t in combinations(P, 3)]

TARGET_GENS = np.array([_mask(s) for s in SINGLES + EDGES + PLAQS], dtype=np.int64)          # 49
LOCAL_GENS = np.array(sorted({_mask(s) for s in SINGLES + EDGES + TRIPLES + PLAQS}), dtype=np.int64)  # 85
LOCAL_ME = np.array(sorted({_mask(s) for s in SINGLES + EDGES + TRIPLES}), dtype=np.int64)    # 76


def grid_iqp_theta(seed: int) -> np.ndarray:
    return SIGMA * np.random.default_rng(seed).normal(size=len(TARGET_GENS))


def grid_iqp(seed: int) -> np.ndarray:
    p = iqp_distribution(N_BITS, TARGET_GENS, grid_iqp_theta(seed))
    return p / p.sum()


def grid_ising(seed: int) -> np.ndarray:
    rng = np.random.default_rng(10_000 + seed)
    h = ISING_H * rng.normal(size=N_BITS)
    J = ISING_J * rng.normal(size=len(EDGES))
    s = 1.0 - 2.0 * all_bitstrings(N_BITS).astype(np.float64)   # bit 0 -> +1, bit 1 -> -1
    e = s @ h + sum(J[k] * s[:, i] * s[:, j] for k, (i, j) in enumerate(EDGES))
    p = np.exp(e - e.max())
    return p / p.sum()


class MaxEntOn(MaxEntModel):
    """MaxEnt restricted to a given mask set (the fairness arm: the classical model gets the same graph)."""

    def __init__(self, n: int, masks):
        super().__init__(n, 1)
        self.k = 3
        self.name = self.key = "maxent_local"
        self.masks = np.asarray(masks, dtype=np.int64)
        self.n_params = len(self.masks)
        self.F = parity_matrix(n, self.masks)

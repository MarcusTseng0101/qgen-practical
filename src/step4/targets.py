"""Step 4 targets (specs/step4_misspec_finite_n.md): iqp4 and mix.

- iqp4(sigma, s): iqp(sigma, s) of step 2/3 (imported) plus 6 weight-4 generators. The 6
  distinct weight-4 supports and z' ~ N(0, 1) are drawn from default_rng(4000 + s), supports
  first; the angles are sigma * z', so z' is reused across sigma. Outside the generic IQP's
  weight-<=3 family.
- mix(s, delta, K): a latent-class mixture of K product-Bernoulli components (K = 3 in the
  original spec; a parameter since amendment 1, specs/step4_amendment1.md). From
  default_rng(5000 + s): weights ~ Dirichlet(1, ..., 1), then u ~ U(-0.5, 0.5) of shape (K, n);
  the draw order is unchanged, so K = 3 is bit-identical to the original construction;
  P(x_j = 1 | k) = 0.5 + delta * u[k, j]. The same (weights, u) are used for every delta, so the
  delta calibration varies only the scale.

src/step1..3 are imported, never edited.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np

from src.step1.bits import all_bitstrings, subset_mask
from src.step1.targets import iqp_distribution
from src.step2.sweep import sigma_target

N_BITS = 12
N_W4 = 6            # spec: 6 weight-4 generators
K_MIX = 3           # original spec: 3 latent classes (default; amendment 1 makes K a parameter)
KS_AMEND1 = (3, 6, 12, 24, 48)
DELTAS_AMEND1 = (0.8, 0.9, 0.99)
DELTAS = (0.2, 0.4, 0.6, 0.8)


def iqp4_layout(seed: int, n: int = N_BITS):
    """(weight-4 supports, z') from default_rng(4000 + seed)."""
    rng = np.random.default_rng(4000 + seed)
    quads = list(combinations(range(n), 4))
    pick = rng.choice(len(quads), size=N_W4, replace=False)
    supports = [quads[i] for i in sorted(pick)]
    z4 = rng.normal(0.0, 1.0, N_W4)
    return supports, z4


def iqp4_target(sigma: float, seed: int, n: int = N_BITS):
    """(p, masks, theta, layout): the iqp(sigma, seed) generators followed by the 6 weight-4 ones."""
    _, masks3, theta3, _, layout3 = sigma_target(sigma, seed, n)
    supports, z4 = iqp4_layout(seed, n)
    masks = np.concatenate([masks3, np.array([subset_mask(g) for g in supports], dtype=np.int64)])
    theta = np.concatenate([theta3, sigma * z4])
    p = iqp_distribution(n, masks, theta)
    return p / p.sum(), masks, theta, list(layout3) + supports


def mix_params(seed: int, n: int = N_BITS, K: int = K_MIX):
    rng = np.random.default_rng(5000 + seed)
    w = rng.dirichlet(np.ones(K))
    u = rng.uniform(-0.5, 0.5, (K, n))
    return w, u


def mix_target(seed: int, delta: float, n: int = N_BITS, K: int = K_MIX) -> np.ndarray:
    """p(x) = sum_k w_k prod_j q_kj^x_j (1 - q_kj)^(1 - x_j), q = 0.5 + delta * u."""
    w, u = mix_params(seed, n, K)
    q = 0.5 + delta * u                                    # P(x_j = 1 | k)
    X = all_bitstrings(n).astype(np.float64)               # (2^n, n), x_j = (i >> j) & 1
    logp = X @ np.log(q).T + (1.0 - X) @ np.log(1.0 - q).T  # (2^n, K)
    p = np.exp(logp) @ w
    return p / p.sum()


def fit_mixture_moments(*_, **__):
    """Out of scope (spec, fairness caveat): a latent-class fit would be well-specified on mix."""
    raise NotImplementedError("latent-class mixture baseline is out of scope for step 4")

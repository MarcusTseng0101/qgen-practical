"""Synthetic targets at n = 12 (n is a guess, chosen so everything is exact).

make_target(kind, n, seed) -> (p, meta), with p the exact probability vector.
The layout and angles come from np.random.default_rng(100 + seed): layout first, angles
second, so `random` shares the generator layout of `biased` for the same seed.

The target code computes its own distributions from bits.py; it deliberately does not use
the model classes, so a bug in a model cannot also be baked into the target.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.special import logsumexp

from .bits import fwht, parity_matrix, subset_mask

KINDS = ("biased", "ising", "random")
N_PAIRS = 18        # spec
N_TRIPLES = 8       # spec
ANGLE_SCALE = 0.4   # guess (spec): theta, h, J ~ N(0, 0.4^2)


def _pick(rng, items, k):
    idx = rng.choice(len(items), size=k, replace=False)
    return [items[i] for i in sorted(idx)]


def _iqp_layout(n, rng):
    pairs = _pick(rng, list(combinations(range(n), 2)), N_PAIRS)
    triples = _pick(rng, list(combinations(range(n), 3)), N_TRIPLES)
    return [(j,) for j in range(n)] + pairs + triples


def iqp_distribution(n, gens_masks, theta) -> np.ndarray:
    """p(x) = |2^-n sum_z (-1)^{x.z} e^{i phi(z)}|^2, phi = sum_g theta_g s_g."""
    a = fwht(np.exp(1j * (parity_matrix(n, gens_masks) @ theta))) / 2**n
    return a.real**2 + a.imag**2


def make_target(kind: str, n: int = 12, seed: int = 0):
    rng = np.random.default_rng(100 + seed)
    if kind in ("biased", "random"):
        layout = _iqp_layout(n, rng)
        masks = np.array([subset_mask(g) for g in layout], dtype=np.int64)
        if kind == "biased":
            theta = rng.normal(0.0, ANGLE_SCALE, len(layout))
        else:
            theta = rng.uniform(0.0, 2 * np.pi, len(layout))
        p = iqp_distribution(n, masks, theta)
        meta = {"kind": kind, "n": n, "seed": seed, "generators": [list(g) for g in layout],
                "angles": theta.tolist()}
    elif kind == "ising":
        pairs = _pick(rng, list(combinations(range(n), 2)), N_PAIRS)
        h = rng.normal(0.0, ANGLE_SCALE, n)
        J = rng.normal(0.0, ANGLE_SCALE, N_PAIRS)
        masks = np.array([subset_mask((j,)) for j in range(n)] + [subset_mask(pr) for pr in pairs])
        e = parity_matrix(n, masks) @ np.concatenate([h, J])
        p = np.exp(e - logsumexp(e))
        meta = {"kind": kind, "n": n, "seed": seed, "pairs": [list(pr) for pr in pairs],
                "h": h.tolist(), "J": J.tolist()}
    else:
        raise ValueError(f"unknown target kind {kind!r}; expected one of {KINDS}")
    p = p / p.sum()
    return p, meta


def sample_indices(p: np.ndarray, N: int, seed: int) -> np.ndarray:
    """N data samples (bitstring indices) from default_rng(1000 + seed)."""
    return np.random.default_rng(1000 + seed).choice(len(p), size=N, p=p)

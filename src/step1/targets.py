"""Synthetic targets at n = 12 (n is a guess, chosen so everything is exact).

make_target(kind, n, seed) -> (p, meta), with p the exact probability vector.
The layout and angles come from np.random.default_rng(100 + seed): layout first, angles
second, so `random` shares the generator layout of `biased` for the same seed.

`maxent_proj` (amendment 1, post-hoc): the exact MaxEnt(3) distribution with the exact
order-<=3 moments of `biased` (same seed). Same training statistics, max-ent completion.

The target code computes its own distributions from bits.py; it deliberately does not use
the model classes, so a bug in a model cannot also be baked into the target.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.special import logsumexp

from scipy.optimize import minimize

from .bits import fwht, masks_up_to, parity_matrix, subset_mask

KINDS = ("biased", "maxent_proj", "random", "ising")
PROJ_LBFGS = {"maxiter": 50000, "maxfun": 100000, "ftol": 1e-17, "gtol": 1e-14, "maxcor": 30}
# ^ guesses: the projection must match the order-<=3 moments to <= 1e-10 (amendment 1).
PROJ_TOL = 1e-10
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


def maxent_projection(p: np.ndarray, n: int, k: int = 3):
    """argmax entropy subject to the order-1..k parity moments of p, by the unregularized
    convex dual (an independent implementation; does not use models/maxent.py)."""
    masks = masks_up_to(n, k)
    F = parity_matrix(n, masks)
    f = fwht(p)[masks]

    def dual(lam):
        e = F @ lam
        lz = logsumexp(e)
        q = np.exp(e - lz)
        return lz - lam @ f, F.T @ q - f

    res = minimize(dual, np.zeros(len(masks)), jac=True, method="L-BFGS-B", options=PROJ_LBFGS)
    e = F @ res.x
    q = np.exp(e - logsumexp(e))
    resid = float(np.sum((fwht(q)[masks] - f) ** 2))
    return q, res.x, resid, str(res.message)


def make_target(kind: str, n: int = 12, seed: int = 0):
    if kind == "maxent_proj":
        p_b, meta_b = make_target("biased", n, seed)
        q, lam, resid, msg = maxent_projection(p_b, n, 3)
        if resid > PROJ_TOL:
            raise RuntimeError(f"maxent_proj moment residual {resid:.3e} > {PROJ_TOL:g} ({msg})")
        meta = {"kind": kind, "n": n, "seed": seed, "projected_from": "biased",
                "moment_residual_vs_biased": resid, "lambda": lam.tolist(),
                "biased_generators": meta_b["generators"]}
        return q / q.sum(), meta
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

"""Metrics on probability vectors and angle arrays only.

Hard rule (spec): this module never depends on the model package; it must not know
which model produced a distribution. It sees probability vectors and angle arrays.
"""
from __future__ import annotations

import numpy as np

from .walsh import coefficients_by_order

LEVELS = (4, 5, 6)      # guess (spec): the "high-order" parity levels
PI4 = np.pi / 4


def completion_gap(p_model: np.ndarray, p_true: np.ndarray, n: int, levels=LEVELS) -> dict:
    """G = mean over levels l of mean_{|A| = l} (f_A(model) - f_A(true))^2, against the
    exact target. Returns {"G": G, "per_level": {l: error}}."""
    fm = coefficients_by_order(p_model, n, levels)
    ft = coefficients_by_order(p_true, n, levels)
    per = {int(l): float(np.mean((fm[l] - ft[l]) ** 2)) for l in levels}
    return {"G": float(np.mean(list(per.values()))), "per_level": per}


def tv(p: np.ndarray, q: np.ndarray) -> float:
    return float(0.5 * np.sum(np.abs(np.asarray(p) - np.asarray(q))))


def lattice_dist(theta) -> np.ndarray:
    """|theta - (pi/4) round(4 theta / pi)| elementwise, in [0, pi/8] (line-A definition)."""
    th = np.asarray(theta, dtype=np.float64)
    return np.abs(th - PI4 * np.round(th / PI4))


def clifford_distance(theta, orders=None) -> dict:
    """max / mean / median distance of the angles to (pi/4)Z; with orders (the generator
    weight of each angle), also the max and mean per weight."""
    d = lattice_dist(theta)
    out = {"clifford_dist_max": float(d.max()), "clifford_dist_mean": float(d.mean()),
           "clifford_dist_median": float(np.median(d))}
    if orders is not None:
        orders = np.asarray(orders)
        for k in np.unique(orders):
            out[f"clifford_dist_max_w{int(k)}"] = float(d[orders == k].max())
            out[f"clifford_dist_mean_w{int(k)}"] = float(d[orders == k].mean())
    return out


def collision_ratio(p: np.ndarray) -> float:
    """2^n sum p^2 (1 for uniform)."""
    p = np.asarray(p, dtype=np.float64)
    return float(len(p) * np.sum(p**2))


def expected_sampling_residual(f: np.ndarray, N: float) -> float:
    """sum_A (1 - f_A^2) / N: the expected squared error of N-sample moment estimates.
    0 at N = inf."""
    if not np.isfinite(N):
        return 0.0
    f = np.asarray(f, dtype=np.float64)
    return float(np.sum(1.0 - f**2) / N)


def gap_tau(f_hat: np.ndarray, N: float) -> float:
    """tau = 1e-10 at N = inf; 3 * expected sampling residual at finite N (spec, FM2)."""
    return 1e-10 if not np.isfinite(N) else 3.0 * expected_sampling_residual(f_hat, N)


def gap_valid(train_residual_iqp: float, train_residual_maxent: float, tau: float) -> bool:
    """False whenever train_residual_iqp > max(10 * train_residual_maxent, tau)."""
    return bool(train_residual_iqp <= max(10.0 * train_residual_maxent, tau))

"""Parity (Walsh) coefficients f_A = E_p[(-1)^{A.x}] of a probability vector."""
from __future__ import annotations

import numpy as np

from .bits import fwht, subsets_by_order


def parity_coefficients(p: np.ndarray) -> np.ndarray:
    """f[A] for every mask A (f[0] = sum p = 1), via one FWHT."""
    return fwht(np.asarray(p, dtype=np.float64))


def coefficients_at(p: np.ndarray, masks: np.ndarray) -> np.ndarray:
    return parity_coefficients(p)[np.asarray(masks, dtype=np.int64)]


def coefficients_by_order(p: np.ndarray, n: int, orders) -> dict[int, np.ndarray]:
    """{k: f_A for all |A| = k, in subsets_by_order order}."""
    f = parity_coefficients(p)
    orders = list(orders)
    by = subsets_by_order(n, max(orders), min(orders))
    return {k: f[by[k]] for k in orders}


def empirical_distribution(idx: np.ndarray, n: int) -> np.ndarray:
    """Probability vector of N samples given as bitstring indices."""
    return np.bincount(np.asarray(idx, dtype=np.int64), minlength=2**n) / len(idx)

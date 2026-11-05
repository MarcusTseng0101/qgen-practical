"""Bitstrings, spins, the fast Walsh-Hadamard transform, and parity subsets.

Conventions used everywhere in step 1:
- A bitstring x in {0,1}^n is stored as the integer index i with x_j = (i >> j) & 1.
- A subset A of {0..n-1} is stored as the integer mask sum_{j in A} 2^j.
- s = 1 - 2x in {+1,-1}^n, and s_A = prod_{j in A} s_j = (-1)^{A.x} = (-1)^{popcount(A & i)}.
- fwht(v)[a] = sum_x (-1)^{popcount(a & x)} v[x]  (unnormalized; fwht(fwht(v)) = 2^n v).
"""
from __future__ import annotations

from itertools import combinations

import numpy as np


def all_bitstrings(n: int) -> np.ndarray:
    """(2^n, n) uint8 array; row i is x with x_j = (i >> j) & 1."""
    idx = np.arange(2**n, dtype=np.int64)
    return ((idx[:, None] >> np.arange(n)) & 1).astype(np.uint8)


def spins(n: int) -> np.ndarray:
    """(2^n, n) float array s = 1 - 2x."""
    return 1.0 - 2.0 * all_bitstrings(n).astype(np.float64)


def fwht(v: np.ndarray) -> np.ndarray:
    """Unnormalized Walsh-Hadamard transform of a length-2^n real or complex vector."""
    v = np.array(v, copy=True)
    N = v.shape[0]
    if N & (N - 1):
        raise ValueError("length must be a power of 2")
    h = 1
    while h < N:
        v = v.reshape(-1, 2, h)
        v = np.stack([v[:, 0] + v[:, 1], v[:, 0] - v[:, 1]], axis=1).reshape(N)
        h *= 2
    return v


def popcount(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.int64)
    c = np.zeros_like(a)
    while np.any(a):
        c += a & 1
        a = a >> 1
    return c


def subset_mask(A) -> int:
    return int(sum(1 << int(j) for j in A))


def mask_to_subset(m: int) -> tuple:
    return tuple(j for j in range(int(m).bit_length()) if (int(m) >> j) & 1)


def subsets_by_order(n: int, kmax: int, kmin: int = 1) -> dict[int, np.ndarray]:
    """{k: int64 array of masks of all k-subsets of {0..n-1}}, k = kmin..kmax, in
    lexicographic order of the subsets (itertools.combinations)."""
    return {k: np.array([subset_mask(c) for c in combinations(range(n), k)], dtype=np.int64)
            for k in range(kmin, kmax + 1)}


def masks_up_to(n: int, kmax: int, kmin: int = 1) -> np.ndarray:
    """All masks of order kmin..kmax, concatenated by increasing order."""
    return np.concatenate(list(subsets_by_order(n, kmax, kmin).values()))


def parity_matrix(n: int, masks: np.ndarray) -> np.ndarray:
    """(2^n, len(masks)) float matrix with entries s_A(x) = (-1)^{popcount(A & x)}.
    For IQP generators this is the matrix S of products prod_{j in g} s_j."""
    idx = np.arange(2**n, dtype=np.int64)
    return 1.0 - 2.0 * (popcount(idx[:, None] & np.asarray(masks, dtype=np.int64)[None, :]) & 1)

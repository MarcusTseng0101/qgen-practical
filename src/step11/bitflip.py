"""Decohered ("bitflip") twin of the generic IQP (specs/step11_bitflip_control.md).

Each gate exp(i theta_g X_g) is replaced by a random flip of the bits in g with probability
sin^2 theta_g (Recio-Armengol et al., arXiv 2503.02934). Starting from 0...0, x is the XOR of the
independently flipped masks, so

    <Z_a> = prod_{g : |g & a| odd} cos(2 theta_g),      p = FWHT(f) / 2^n.

The coherent IQP has <Z_a> = E_s[cos(2 sum_{g odd} theta_g s_g)] with s_g parities of one sign
vector; this model is the same expression with the s_g independent.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from src.step1.bits import fwht, masks_up_to, popcount
from src.step1.models.iqp import LBFGS_OPTS


def _excl_prod(A: np.ndarray) -> np.ndarray:
    """E[i, j] = prod_{k != j} A[i, k], without division (safe at A = 0)."""
    m = A.shape[1]
    left = np.ones_like(A)
    right = np.ones_like(A)
    if m > 1:
        left[:, 1:] = np.cumprod(A[:, :-1], axis=1)
        right[:, :-1] = np.cumprod(A[:, :0:-1], axis=1)[:, ::-1]
    return left * right


class BitflipModel:
    def __init__(self, n: int, gens: np.ndarray | None = None):
        self.n = n
        self.gens = masks_up_to(n, 3) if gens is None else np.asarray(gens, dtype=np.int64)
        self.n_params = len(self.gens)
        self._ops_key, self._Mops = None, None

    def odd(self, ops) -> np.ndarray:
        """Boolean (len(ops), n_params): |g & a| odd."""
        ops = np.asarray(ops, dtype=np.int64)
        return (popcount(ops[:, None] & self.gens[None, :]) & 1).astype(bool)

    def _M(self, ops):
        key = (len(ops), int(np.asarray(ops).sum()))
        if key != self._ops_key:
            self._ops_key, self._Mops = key, self.odd(ops)
        return self._Mops

    def moments(self, theta, ops) -> np.ndarray:
        c = np.cos(2.0 * np.asarray(theta, dtype=np.float64))
        return np.prod(np.where(self._M(ops), c[None, :], 1.0), axis=1)

    def loss_and_grad(self, theta, fhat, ops):
        theta = np.asarray(theta, dtype=np.float64)
        M = self._M(ops)
        c, s = np.cos(2.0 * theta), np.sin(2.0 * theta)
        A = np.where(M, c[None, :], 1.0)
        f = np.prod(A, axis=1)
        r = f - fhat
        dA = np.where(M, -2.0 * s[None, :], 0.0)          # d A[a, g] / d theta_g
        J = _excl_prod(A) * dA                            # d f_a / d theta_g
        return float(r @ r), 2.0 * (r @ J)

    def all_moments(self, theta) -> np.ndarray:
        """f_a for every a in 0..2^n-1, in chunks (logs + signs + zero counts)."""
        c = np.cos(2.0 * np.asarray(theta, dtype=np.float64))
        zero = c == 0.0
        lc = np.log(np.abs(np.where(zero, 1.0, c)))
        neg = (c < 0).astype(np.float64)
        zf = zero.astype(np.float64)
        N = 2**self.n
        f = np.empty(N)
        step = 4096
        for i in range(0, N, step):
            idx = np.arange(i, min(i + step, N), dtype=np.int64)
            Mo = (popcount(idx[:, None] & self.gens[None, :]) & 1).astype(np.float64)
            mag = np.exp(Mo @ lc)
            sign = 1.0 - 2.0 * (np.rint(Mo @ neg).astype(np.int64) & 1)
            f[i:i + len(idx)] = np.where(Mo @ zf > 0.5, 0.0, sign * mag)
        return f

    def prob(self, theta) -> np.ndarray:
        return fwht(self.all_moments(theta)) / 2**self.n

    def fit_one(self, theta0, fhat, ops, options: dict | None = None) -> dict:
        opts = dict(LBFGS_OPTS, **(options or {}))
        fhat = np.asarray(fhat, dtype=np.float64)
        res = minimize(self.loss_and_grad, np.asarray(theta0, dtype=np.float64), args=(fhat, ops),
                       jac=True, method="L-BFGS-B", options=opts)
        L = self.loss_and_grad(res.x, fhat, ops)[0]
        return {"params": res.x, "residual": float(L), "nit": int(res.nit), "message": str(res.message)}

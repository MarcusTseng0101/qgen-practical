"""MaxEnt(k): the log-linear model on parities of order <= k, enumerated exactly.

p(x) = exp(sum_{1<=|A|<=k} lambda_A (-1)^{A.x}) / Z(lambda).
Fit by minimizing the convex dual log Z(lambda) - lambda . fhat + RIDGE |lambda|^2.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from ..bits import fwht, masks_up_to, parity_matrix
from .base import FitResult

RIDGE = 1e-8        # guess: purely for numerical safety at N = inf
LBFGS_OPTS = {"maxiter": 20000, "maxfun": 40000, "ftol": 1e-16, "gtol": 1e-12, "maxcor": 20}
# ^ guesses, not tuned


def build(n: int):
    """Entry point for run.py's model discovery: the order-3 max-ent comparator."""
    return MaxEntModel(n, k=3)


class MaxEntModel:
    def __init__(self, n: int, k: int = 3):
        self.n, self.k = n, k
        self.name = f"maxent{k}"
        self.key = "maxent" if k == 3 else f"maxent{k}"   # metrics.json key suffix
        self.masks = masks_up_to(n, k)
        self.n_params = len(self.masks)
        self.F = parity_matrix(n, self.masks)   # (2^n, n_params)
        self.params = None

    def prob(self, lam=None) -> np.ndarray:
        lam = self.params if lam is None else lam
        e = self.F @ np.asarray(lam, dtype=np.float64)
        return np.exp(e - logsumexp(e))

    def dual_and_grad(self, lam, fhat_own):
        e = self.F @ lam
        logZ = logsumexp(e)
        p = np.exp(e - logZ)
        val = logZ - lam @ fhat_own + RIDGE * (lam @ lam)
        return float(val), self.F.T @ p - fhat_own + 2.0 * RIDGE * lam

    def fit_moments(self, fhat, ops, seed: int = 0, options: dict | None = None) -> FitResult:
        """fhat[i] = target f_{ops[i]}; ops must contain every parity of order <= k.
        The dual is convex: a single start at lambda = 0 (seed unused, kept for the interface)."""
        fhat = np.asarray(fhat, dtype=np.float64)
        ops = np.asarray(ops, dtype=np.int64)
        pos = {int(m): i for i, m in enumerate(ops)}
        missing = [int(m) for m in self.masks if int(m) not in pos]
        if missing:
            raise ValueError(f"fhat lacks {len(missing)} of the order-<={self.k} parities")
        fhat_own = fhat[[pos[int(m)] for m in self.masks]]
        trace = []
        res = minimize(self.dual_and_grad, np.zeros(self.n_params), args=(fhat_own,), jac=True,
                       method="L-BFGS-B", options=dict(LBFGS_OPTS, **(options or {})),
                       callback=lambda xk: trace.append(self._residual(xk, fhat, ops)))
        self.params = res.x
        L = self._residual(res.x, fhat, ops)
        return FitResult(params=res.x, train_residual=L, restart_residuals=[L], trace=trace,
                         nit=int(res.nit), message=str(res.message))

    def _residual(self, lam, fhat, ops) -> float:
        r = fwht(self.prob(lam))[ops] - fhat
        return float(r @ r)

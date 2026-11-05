"""IQP model with generators of weight <= 3, fitted to parity moments.

Convention (the same phase_np convention as the line-A IQP code; read, never imported):
  phi(s) = sum_g theta_g prod_{j in g} s_j,  s = 1 - 2x,
  p(x)   = |2^-n sum_z (-1)^{x.z} e^{i phi(s(z))}|^2.
(Line A writes e^{-i phi}; p is the same, because conjugating the amplitude does not
change |.|^2 and the transform is real.)

Production path (spec, "load-bearing detail"): moments come from FWHTs, never from the cos
closed form:
  u = e^{i phi};  a = fwht(u) / 2^n;  p = |a|^2;  f = fwht(p).
The gradient is the adjoint of those four steps (see loss_and_grad). The cos closed form
<Z_a> = E_s[cos(2 sum_{g: |g & a| odd} theta_g s_g)] exists only in tests/test_core.py.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from ..bits import fwht, masks_up_to, parity_matrix
from .base import FitResult

INIT_STD = 0.05     # guess: theta ~ N(0, 0.05^2). Small angles avoid the anticoncentrated,
                    # vanishing-gradient regime of random angles (Herbst, arXiv 2512.24801).
                    # Do not replace with uniform-random angles to unstick a fit.
N_RESTARTS = 10     # spec (FM2): keep the restart with the lowest training residual
LBFGS_OPTS = {"maxiter": 20000, "maxfun": 40000, "ftol": 1e-16, "gtol": 1e-13, "maxcor": 20}
# ^ guesses: tolerances tight enough for a 1e-10 residual (scipy's ftol is effectively
#   absolute once L < 1); maxiter/maxcor not tuned.


class IQPModel:
    name = "iqp"

    def __init__(self, n: int, kmax: int = 3, gens: np.ndarray | None = None):
        self.n = n
        # Generic generator set: all subsets of size 1..kmax (298 at n = 12, kmax = 3).
        # Never the target's own generators (that would be an oracle, not a test).
        self.gens = masks_up_to(n, kmax) if gens is None else np.asarray(gens, dtype=np.int64)
        self.n_params = len(self.gens)
        self.S = parity_matrix(n, self.gens)   # (2^n, n_params), S[z, g] = prod_{j in g} s_j(z)
        self.params = None

    # ---------------- forward ----------------
    def phase(self, theta) -> np.ndarray:
        return self.S @ np.asarray(theta, dtype=np.float64)

    def amplitudes(self, theta) -> np.ndarray:
        return fwht(np.exp(1j * self.phase(theta))) / 2**self.n

    def prob(self, theta=None) -> np.ndarray:
        theta = self.params if theta is None else theta
        a = self.amplitudes(theta)
        return a.real**2 + a.imag**2

    def moments(self, theta, ops) -> np.ndarray:
        """f_A for each mask A in ops."""
        return fwht(self.prob(theta))[np.asarray(ops, dtype=np.int64)]

    # ---------------- loss and adjoint gradient ----------------
    def loss_and_grad(self, theta, fhat, ops):
        """L = sum_i (f_{ops[i]} - fhat[i])^2 and dL/dtheta, by the adjoint of the 4 FWHT steps."""
        ops = np.asarray(ops, dtype=np.int64)
        N = 2**self.n
        u = np.exp(1j * self.phase(theta))
        a = fwht(u) / N
        p = a.real**2 + a.imag**2
        r = fwht(p)[ops] - fhat
        L = float(r @ r)
        gf = np.zeros(N)
        np.add.at(gf, ops, 2.0 * r)                 # dL/df (zero off ops)
        gp = fwht(gf)                               # f = W p, W symmetric -> dL/dp = W dL/df
        ga = 2.0 * a * gp                           # dL/dRe(a) + i dL/dIm(a), p = |a|^2
        gu = fwht(ga) / N                           # a = W u / N, W real symmetric
        gphi = np.real(np.conj(1j * u) * gu)        # u = e^{i phi}, du = i u dphi
        return L, self.S.T @ gphi                   # phi = S theta

    def moment_jacobian(self, theta, ops) -> np.ndarray:
        """d f_{ops} / d theta, shape (len(ops), n_params), one adjoint pass per op."""
        ops = np.asarray(ops, dtype=np.int64)
        N = 2**self.n
        u = np.exp(1j * self.phase(theta))
        a = fwht(u) / N
        J = np.empty((len(ops), self.n_params))
        for i, A in enumerate(ops):
            gf = np.zeros(N)
            gf[A] = 1.0
            gu = fwht(2.0 * a * fwht(gf)) / N
            J[i] = self.S.T @ np.real(np.conj(1j * u) * gu)
        return J

    # ---------------- fit ----------------
    def fit_moments(self, fhat, ops, seed: int = 0, n_restarts: int = N_RESTARTS,
                    init_std: float = INIT_STD, options: dict | None = None,
                    theta0: np.ndarray | None = None) -> FitResult:
        """L-BFGS-B from n_restarts small-angle inits; keep the lowest training residual.
        theta0 (tests only) replaces the first restart's init."""
        fhat = np.asarray(fhat, dtype=np.float64)
        rng = np.random.default_rng(seed)
        opts = dict(LBFGS_OPTS, **(options or {}))
        best, residuals = None, []
        for r in range(n_restarts):
            init = rng.normal(0.0, init_std, self.n_params)
            theta0_r = np.asarray(theta0, dtype=np.float64) if (r == 0 and theta0 is not None) else init
            trace = []
            res = minimize(self.loss_and_grad, theta0_r, args=(fhat, ops), jac=True,
                           method="L-BFGS-B", options=opts,
                           callback=lambda xk: trace.append(self.loss_and_grad(xk, fhat, ops)[0]))
            L = self.loss_and_grad(res.x, fhat, ops)[0]
            residuals.append(L)
            if best is None or L < best.train_residual:
                best = FitResult(params=res.x, train_residual=L, trace=trace,
                                 nit=int(res.nit), message=str(res.message))
        best.restart_residuals = residuals
        self.params = best.params
        return best


def iqp_moments_mc(theta, gens, ops, n_samples, rng):
    """Van den Nest Monte Carlo estimator of <Z_a> for n > 20: the hook for step 3.

    Estimates E_s[cos(2 sum_{g: |g & a| odd} theta_g s_g)] by sampling s uniformly.
    Deliberately not implemented in step 1 (n = 12 is enumerable)."""
    raise NotImplementedError("iqp_moments_mc is the step-3 hook; step 1 is exact at n = 12")

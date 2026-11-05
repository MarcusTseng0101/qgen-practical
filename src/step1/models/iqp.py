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
from scipy.optimize import minimize, nnls

from ..bits import fwht, masks_up_to, parity_matrix, popcount
from .base import FitResult

INIT_STD = 0.05     # guess: theta ~ N(0, 0.05^2). Small angles avoid the anticoncentrated,
                    # vanishing-gradient regime of random angles (Herbst, arXiv 2512.24801).
                    # Do not replace with uniform-random angles to unstick a fit.
N_RESTARTS = 10     # spec (FM2): keep the restart with the lowest training residual
LBFGS_OPTS = {"maxiter": 20000, "maxfun": 40000, "ftol": 1e-16, "gtol": 1e-13, "maxcor": 20}
# ^ guesses: tolerances tight enough for a 1e-10 residual (scipy's ftol is effectively
#   absolute once L < 1); maxiter/maxcor not tuned.


# Amendment 1 (post-hoc, triggered by the FM2 diagnostics): sparse generator selection.
SPARSE_REL_THRESHOLD = 1e-3   # guess (amendment 1): keep g with theta_g^2 >= 1e-3 * max theta^2
K_MAX = 60                    # guess (amendment 1): at most 60 generators, the largest theta^2
CANDIDATE_KMAX = 3            # candidates: all generators of weight 1..3 (298 at n = 12)


def build(n: int, gens: str = "sparse", **_):
    """Entry point for run.py's model discovery. gens: "sparse" (amendment 1, default) or
    "generic" (the original 298-generator model, kept so FM2 can be reproduced)."""
    return IQPModel(n, gens_mode=gens)


def select_sparse_generators(fhat, ops) -> dict:
    """Small-angle NNLS selector (amendment 1). Sees ONLY the training moments (fhat, ops);
    never the target's layout.

    To second order, m_a := (1 - fhat_a) / 2 ~= sum_g M_ag theta_g^2, with
    M_ag = 1[|g & a| odd], over all weight-<=3 candidates g. Solve for theta^2 >= 0 with
    scipy.optimize.nnls, keep theta^2 >= SPARSE_REL_THRESHOLD * max, capped at K_MAX by size.
    n is the number of bits spanned by ops (the order-1 ops cover every bit)."""
    fhat = np.asarray(fhat, dtype=np.float64)
    ops = np.asarray(ops, dtype=np.int64)
    n = int(max(int(o).bit_length() for o in ops))
    cand = masks_up_to(n, CANDIDATE_KMAX)
    M = (popcount(ops[:, None] & cand[None, :]) % 2).astype(np.float64)
    m = (1.0 - fhat) / 2.0
    theta2, rnorm = nnls(M, m, maxiter=50 * M.shape[1])
    keep = np.flatnonzero(theta2 >= SPARSE_REL_THRESHOLD * theta2.max()) if theta2.max() > 0         else np.array([], dtype=np.int64)
    keep = keep[np.argsort(-theta2[keep], kind="stable")][:K_MAX]
    keep = np.sort(keep)                       # candidate order (by weight, then lexicographic)
    return {"gens": cand[keep], "theta2": theta2[keep], "theta2_all": theta2,
            "candidates": cand, "nnls_rnorm": float(rnorm), "K": int(len(keep))}


class IQPModel:
    name = "iqp"
    key = "iqp"   # metrics.json key suffix

    def angles(self):
        """(angles, generator weights) of the fitted model, for clifford_distance."""
        return self.params, popcount(self.gens)

    def __init__(self, n: int, kmax: int = 3, gens: np.ndarray | None = None,
                 gens_mode: str = "generic"):
        if gens_mode not in ("generic", "sparse"):
            raise ValueError(gens_mode)
        self.n = n
        self.gens_mode = gens_mode
        self.selection = None
        # Generic generator set: all subsets of size 1..kmax (298 at n = 12, kmax = 3).
        # Never the target's own generators (that would be an oracle, not a test).
        # In sparse mode this is replaced in fit_moments by the selector's output.
        self._set_gens(masks_up_to(n, kmax) if gens is None else np.asarray(gens, dtype=np.int64))
        self.params = None

    def _set_gens(self, gens):
        self.gens = np.asarray(gens, dtype=np.int64)
        self.n_params = len(self.gens)
        self.S = parity_matrix(self.n, self.gens)   # (2^n, n_params), S[z, g] = prod_{j in g} s_j(z)

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
        """L-BFGS-B from n_restarts inits; keep the lowest training residual.
        generic: theta ~ N(0, init_std^2). sparse (amendment 1): first select the generators
        from (fhat, ops) only, then |theta_g| = sqrt(NNLS theta_g^2) with random signs from
        default_rng(seed*100 + r); restart 0 is all-positive.
        theta0 (tests only) replaces the first restart's init."""
        fhat = np.asarray(fhat, dtype=np.float64)
        rng = np.random.default_rng(seed)
        opts = dict(LBFGS_OPTS, **(options or {}))
        if self.gens_mode == "sparse":
            self.selection = select_sparse_generators(fhat, ops)
            self._set_gens(self.selection["gens"])
            mag = np.sqrt(self.selection["theta2"])
        best, residuals, info = None, [], []
        for r in range(n_restarts):
            if self.gens_mode == "sparse":
                signs = np.ones(self.n_params) if r == 0 else                     np.random.default_rng(seed * 100 + r).choice([-1.0, 1.0], self.n_params)
                init = signs * mag
            else:
                init = rng.normal(0.0, init_std, self.n_params)
            theta0_r = np.asarray(theta0, dtype=np.float64) if (r == 0 and theta0 is not None) else init
            trace = []
            cb = _trace_callback(trace)

            res = minimize(self.loss_and_grad, theta0_r, args=(fhat, ops), jac=True,
                           method="L-BFGS-B", options=opts, callback=cb)
            L = self.loss_and_grad(res.x, fhat, ops)[0]
            residuals.append(L)
            info.append({"residual": L, "nit": int(res.nit), "message": str(res.message)})
            if best is None or L < best.train_residual:
                best = FitResult(params=res.x, train_residual=L, trace=trace,
                                 nit=int(res.nit), message=str(res.message))
        best.restart_residuals = residuals
        best.restarts = info
        self.params = best.params
        return best


def _trace_callback(trace: list):
    """scipy passes an OptimizeResult (with .fun, the current loss) only when the callback's
    single parameter is named intermediate_result."""
    def cb(intermediate_result):
        trace.append(float(intermediate_result.fun))
    return cb


def iqp_moments_mc(theta, gens, ops, n_samples, rng):
    """Van den Nest Monte Carlo estimator of <Z_a> for n > 20: the hook for step 3.

    Estimates E_s[cos(2 sum_{g: |g & a| odd} theta_g s_g)] by sampling s uniformly.
    Deliberately not implemented in step 1 (n = 12 is enumerable)."""
    raise NotImplementedError("iqp_moments_mc is the step-3 hook; step 1 is exact at n = 12")

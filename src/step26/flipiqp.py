"""IQP + learned per-qubit bit-flip damping: model moments f_S = prod_{j in S} lam_j * f_S^IQP(theta).
An effective local noise model: exact for independent output bit flips (readout, Z errors after the last gate),
approximate for mid-circuit X/Y errors. lam_j in [LAM_LO, 1], fitted jointly with theta by L-BFGS-B."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from src.step1.bits import fwht
from src.step1.models.iqp import IQPModel, LBFGS_OPTS

LAM_LO = 0.5     # guess: lower bound on the damping (flip prob <= 25%)


def _bits(masks, n):
    masks = np.asarray(masks, dtype=np.int64)
    return ((masks[:, None] >> np.arange(n)[None, :]) & 1).astype(np.float64)


class FlipIQP:
    def __init__(self, n, gens):
        self.n = n
        self.iqp = IQPModel(n, gens=gens)
        self.K = self.iqp.n_params
        self.Ball = None

    def _split(self, x):
        return x[: self.K], x[self.K:]

    def loss_and_grad(self, x, fhat, ops):
        th, lam = self._split(x)
        m = self.iqp
        ops = np.asarray(ops, dtype=np.int64)
        N = 2**self.n
        B = self._B
        w = np.exp(B @ np.log(lam))                         # prod_{j in S} lam_j, per op
        u = np.exp(1j * m.phase(th))
        a = fwht(u) / N
        p = a.real**2 + a.imag**2
        f = fwht(p)[ops]
        r = w * f - fhat
        L = float(r @ r)
        gf = np.zeros(N)
        np.add.at(gf, ops, 2.0 * r * w)
        gp = fwht(gf)
        gu = fwht(2.0 * a * gp) / N
        gth = m.S.T @ np.real(np.conj(1j * u) * gu)
        glam = (B * (2.0 * r * w * f)[:, None]).sum(0) / lam   # d w / d lam_j = w * B_j / lam_j
        return L, np.concatenate([gth, glam])

    def fit(self, fhat, ops, seed=0, n_restarts=20, init_std=0.3, lam0=1.0):
        self._B = _bits(ops, self.n)
        rng = np.random.default_rng(seed)
        bounds = [(None, None)] * self.K + [(LAM_LO, 1.0)] * self.n
        best = None
        for _ in range(n_restarts):
            x0 = np.concatenate([rng.normal(0, init_std, self.K), np.full(self.n, lam0)])
            r = minimize(self.loss_and_grad, x0, args=(fhat, ops), jac=True, method="L-BFGS-B",
                         bounds=bounds, options=LBFGS_OPTS)
            if best is None or r.fun < best.fun:
                best = r
        self.x = best.x
        self.resid = float(best.fun)
        return self

    def prob(self):
        th, lam = self._split(self.x)
        p = self.iqp.prob(th)
        Nn = 2**self.n
        f = fwht(p) * np.exp(_bits(np.arange(Nn), self.n) @ np.log(lam))
        q = np.clip(fwht(f) / Nn, 0, None)
        return q / q.sum()

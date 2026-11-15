"""Step 30: coherent-aware IQP. Layered IQP with learned per-qubit RX over-rotations between layers, plus FlipIQP's
per-qubit damping lam for readout:

    u = 1;  for each layer l (gates grouped by weight: 1, 2, >=3):
              u *= exp(i S_l theta_l);   if l is not the last layer: u <- prod_j RX(e_{l,j}) u
    a = H u;  f_S = prod_{j in S} lam_j * f_S(|a|^2).

A layer of RX on all qubits is diagonal in the X basis: prod_j RX(e_j) = H diag(exp(-i/2 sum_j e_j s_j)) H, so it
costs two fast Walsh-Hadamard transforms. An RX after the last layer acts as a Z after the final H and leaves p
unchanged, so it is omitted (its gradient is identically zero).

Assumed gate order (a guess, the price of a coherent model): all 1-body gates, then 2-body, then higher. The RX after
a layer stands in for the over-rotations accumulated inside it: exact for the 1-body layer, approximate otherwise."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from src.step1.bits import fwht, parity_matrix
from src.step1.models.iqp import LBFGS_OPTS
from src.step26.flipiqp import LAM_LO, _bits

EPS_MAX = 1.5    # guess: bound on a layer's total over-rotation
COH_OPTS = {**LBFGS_OPTS, "maxiter": 3000}   # guess: the tail after ~3000 iterations moves the ratio by < 2% (probe, seed 1067)


def _weight(m):
    return bin(int(m)).count("1")


class CohIQP:
    """tied=False: a free angle per qubit per RX layer. tied=True: one angle e_j per qubit (one per-touch
    miscalibration), and the RX after layer l turns by c_{l,j} e_j, c_{l,j} = number of layer-l gates touching j."""

    def __init__(self, n, gens, tied=False):
        self.n = n
        self.tied = tied
        gens = np.asarray(gens, dtype=np.int64)
        w = np.array([_weight(g) for g in gens])
        self.layers = [g for g in (gens[w == 1], gens[w == 2], gens[w >= 3]) if len(g)]
        self.Sl = [parity_matrix(n, g).astype(np.float64) for g in self.layers]
        self.Kl = [len(g) for g in self.layers]
        self.K = sum(self.Kl)
        self.L = len(self.layers)
        self.E = self.L - 1                                   # RX layers
        self.S1 = parity_matrix(n, 1 << np.arange(n)).astype(np.float64)   # s_j(x), (2^n, n)
        self.C = np.array([[sum((int(g) >> j) & 1 for g in lay) for j in range(n)] for lay in self.layers[: self.E]],
                          dtype=np.float64)                    # touches, (E, n)
        self.n_eps = n if tied else self.E * n

    def _split(self, x):
        th = x[: self.K]
        e = x[self.K: self.K + self.n_eps]
        eps = self.C * e[None, :] if self.tied else e.reshape(self.E, self.n)
        lam = x[self.K + self.n_eps:]
        return th, eps, lam

    def _forward(self, th, eps, keep=False):
        N = 2**self.n
        u = np.ones(N, dtype=np.complex128)
        tape = []
        o = 0
        for l in range(self.L):
            u = u * np.exp(1j * (self.Sl[l] @ th[o: o + self.Kl[l]]))
            o += self.Kl[l]
            if l < self.E:
                y = fwht(u) * np.exp(-0.5j * (self.S1 @ eps[l]))
                if keep:
                    tape.append((u, y))
                u = fwht(y) / N
            elif keep:
                tape.append((u, None))
        return u, tape

    def loss_and_grad(self, x, fhat, ops):
        th, eps, lam = self._split(x)
        N = 2**self.n
        B = self._B
        w = np.exp(B @ np.log(lam))
        u, tape = self._forward(th, eps, keep=True)
        a = fwht(u) / N
        p = a.real**2 + a.imag**2
        f = fwht(p)[ops]
        r = w * f - fhat
        L = float(r @ r)
        gf = np.zeros(N)
        np.add.at(gf, ops, 2.0 * r * w)
        gp = fwht(gf)
        G = fwht(2.0 * a * gp) / N                  # 2 dL/d conj(u) at the circuit output
        gth = np.zeros(self.K)
        geps = np.zeros((self.E, self.n))
        o = self.K
        for l in reversed(range(self.L)):
            uph, y = tape[l]
            if y is not None:                       # back through u_out = F(d * F u_ph) / N
                Gy = fwht(G) / N
                geps[l] = self.S1.T @ np.real(np.conj(-0.5j * y) * Gy)
                G = fwht(Gy * np.exp(0.5j * (self.S1 @ eps[l])))
            o -= self.Kl[l]
            gth[o: o + self.Kl[l]] = self.Sl[l].T @ np.real(np.conj(1j * uph) * G)
            G = G * np.exp(-1j * (self.Sl[l] @ th[o: o + self.Kl[l]]))
        glam = (B * (2.0 * r * w * f)[:, None]).sum(0) / lam
        ge = (self.C * geps).sum(0) if self.tied else geps.ravel()
        return L, np.concatenate([gth, ge, glam])

    def fit(self, fhat, ops, seed=0, n_restarts=5, init_std=0.3, eps_std0=0.05, opts=None):
        ops = np.asarray(ops, dtype=np.int64)
        self._B = _bits(ops, self.n)
        rng = np.random.default_rng(seed)
        bounds = [(None, None)] * self.K + [(-EPS_MAX, EPS_MAX)] * self.n_eps + [(LAM_LO, 1.0)] * self.n
        best = None
        for _ in range(n_restarts):
            x0 = np.concatenate([rng.normal(0, init_std, self.K), rng.normal(0, eps_std0, self.n_eps),
                                 np.ones(self.n)])
            r = minimize(self.loss_and_grad, x0, args=(fhat, ops), jac=True, method="L-BFGS-B",
                         bounds=bounds, options=opts or COH_OPTS)
            if best is None or r.fun < best.fun:
                best = r
        self.x = best.x
        self.resid = float(best.fun)
        return self

    def prob(self, x=None):
        th, eps, lam = self._split(self.x if x is None else x)
        Nn = 2**self.n
        a = fwht(self._forward(th, eps)[0]) / Nn
        p = a.real**2 + a.imag**2
        f = fwht(p) * np.exp(_bits(np.arange(Nn), self.n) @ np.log(lam))
        q = np.clip(fwht(f) / Nn, 0, None)
        return q / q.sum()

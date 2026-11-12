"""Pilot (dev seeds only): L1-IQP over weight<=4 candidates, debiased refit, lambda by validation.
phase = WHT(theta placed at generator masks), so no 2^n x K matrix is needed."""
import sys, time, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.walsh import empirical_distribution, parity_coefficients, fwht
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA

n = 16; NN = 2**n; ops = masks_up_to(n, 3)
LB = {"maxiter": 5000, "maxfun": 10000, "ftol": 1e-14, "gtol": 1e-10, "maxcor": 20}
LAMS = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2]  # guess grid
TOL = 1e-3                              # guess: support threshold on |theta|


def lg(theta, gens, fhat):
    full = np.zeros(NN); full[gens] = theta
    u = np.exp(1j * fwht(full))
    a = fwht(u) / NN
    p = a.real**2 + a.imag**2
    r = fwht(p)[ops] - fhat
    gf = np.zeros(NN); gf[ops] = 2 * r
    gu = fwht(2.0 * a * fwht(gf)) / NN
    gphi = np.real(np.conj(1j * u) * gu)
    return float(r @ r), fwht(gphi)[gens], p


def fit_l1(gens, fhat, lam, x0):
    K = len(gens)
    def obj(z):
        th = z[:K] - z[K:]
        L, g, _ = lg(th, gens, fhat)
        return L + lam * z.sum(), np.concatenate([g + lam, -g + lam])
    z0 = np.concatenate([np.maximum(x0, 0), np.maximum(-x0, 0)])
    res = minimize(obj, z0, jac=True, method="L-BFGS-B", bounds=[(0, None)] * (2 * K), options=LB)
    return res.x[:K] - res.x[K:]


def refit(gens, fhat, x0):
    res = minimize(lambda t: lg(t, gens, fhat)[:2], x0, jac=True, method="L-BFGS-B", options=LB)
    return res.x


seed = int(sys.argv[1]); N = int(sys.argv[2])
p = iqp4_target(SIGMA, seed, n)[0]
idx = sample_indices(p, N, seed)
nf = int(0.8 * N)
f_all = parity_coefficients(empirical_distribution(idx, n))[ops]
f_fit = parity_coefficients(empirical_distribution(idx[:nf], n))[ops]
f_val = parity_coefficients(empirical_distribution(idx[nf:], n))[ops]
me = MaxEntModel(n, 3); qme = me.prob(me.fit_moments(f_all, ops).params)
Gme = M1.completion_gap(qme, p, n)["G"]

cand = masks_up_to(n, 4)
rng = np.random.default_rng(seed)
x = rng.normal(0, 0.01, len(cand))
rows = []
t = time.time()
for lam in sorted(LAMS, reverse=True):      # warm start from strong to weak penalty
    x = fit_l1(cand, f_fit, lam, x)
    sup = np.abs(x) > TOL
    g = cand[sup]
    th = refit(g, f_fit, x[sup])
    _, _, q = lg(th, g, f_fit)
    pf = fwht(q)[ops]
    val = float(((pf - f_val) ** 2).sum())
    # refit on all training shots for the reported model
    th_all = refit(g, f_all, th)
    _, _, q_all = lg(th_all, g, f_all)
    R = M1.completion_gap(q_all, p, n)["G"] / Gme
    w4 = int((np.array([bin(m).count("1") for m in g]) == 4).sum())
    rows.append((lam, int(sup.sum()), w4, val, R))
best = min(rows, key=lambda r: r[3])
for lam, k, w4, val, R in rows:
    print(f"seed {seed} N {N} lam {lam:.0e} k {k} w4 {w4} val {val:.4e} R {R:.3f}{'  <- val' if (lam, k) == best[:2] else ''}", flush=True)
print(f"seed {seed} N {N} VAL-CHOSEN R={best[4]:.3f}  {time.time()-t:.0f}s", flush=True)

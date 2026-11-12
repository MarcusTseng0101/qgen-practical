"""Exploration (spent step 14 seeds): identifiability of the generic IQP and a min-norm (ridge) IQP.
1) effective rank of J_lo at the N = inf fit, and how much the near-null directions move f_hi;
2) ridge IQP: min sum (f - fhat)^2 + lam ||theta||^2 on step 14's N-shot moments, lam grid.
theta = 0 is the uniform distribution, so the lam -> 0+ limit is a min-norm, 'max-entropy-like' IQP."""
import sys, json, time, numpy as np
from scipy.optimize import minimize
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import IQPModel, LBFGS_OPTS, INIT_STD
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import parity_coefficients, fwht
from src.step4.run import training_moments
from src.step4.targets import iqp4_target
from src.step14.run import SIGMA

n = 16; NN = 2**n
lo = masks_up_to(n, 3); allm = np.arange(NN); w = popcount(allm); hi = allm[(w >= 4) & (w <= 6)]
LAMS = [0.0, 1e-6, 1e-5, 1e-4, 1e-3]  # guess grid
seed = int(sys.argv[1]); N = int(sys.argv[2])
t = time.time()
p = iqp4_target(SIGMA, seed, n)[0]
fhat, ops = training_moments(p, N, seed, n)
me = MaxEntModel(n, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, n)["G"]
m = IQPModel(n)
rng = np.random.default_rng(seed)
inits = [rng.normal(0, INIT_STD, m.n_params) for _ in range(3)]
out = {"seed": seed, "N": N, "G_me": Gme, "rows": []}
for lam in LAMS:
    best = None
    for x0 in inits:
        def f(th, lam=lam):
            L, g = m.loss_and_grad(th, fhat, ops)
            return L + lam * float(th @ th), g + 2 * lam * th
        r = minimize(f, x0, jac=True, method="L-BFGS-B", options=LBFGS_OPTS)
        if best is None or r.fun < best.fun:
            best = r
    th = best.x
    resid = m.loss_and_grad(th, fhat, ops)[0]
    G = M1.completion_gap(m.prob(th), p, n)["G"]
    row = {"lam": lam, "R": G / Gme, "resid": resid, "norm": float(np.linalg.norm(th))}
    if lam == 0.0:   # Jacobian spectrum at the unregularised fit
        u = np.exp(1j * m.phase(th)); a = fwht(u) / NN
        J = np.empty((len(lo), m.n_params)); Jh = np.empty((len(hi), m.n_params))
        for g in range(m.n_params):
            ff = fwht(2.0 * np.real(np.conj(a) * (fwht(1j * m.S[:, g] * u) / NN)))
            J[:, g] = ff[lo]; Jh[:, g] = ff[hi]
        U, s, Vt = np.linalg.svd(J)
        row["sv"] = s.tolist()
        row["rank_1e-3"] = int((s > 1e-3 * s[0]).sum()); row["rank_1e-6"] = int((s > 1e-6 * s[0]).sum())
        # leverage of the weakest 100 directions on the high orders vs low orders
        V = Vt[-100:].T
        row["hi_over_lo_weak100"] = float(np.linalg.norm(Jh @ V) / np.linalg.norm(J @ V))
        row["hi_over_lo_strong100"] = float(np.linalg.norm(Jh @ Vt[:100].T) / np.linalg.norm(J @ Vt[:100].T))
    out["rows"].append(row)
    print(json.dumps({k: v for k, v in row.items() if k != "sv"}), flush=True)
out["secs"] = time.time() - t
print("RESULT " + json.dumps(out), flush=True)

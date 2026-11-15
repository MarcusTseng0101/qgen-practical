"""One CohIQP restart on spent seed 1067 (full graph, eps 0.2): iterations, time, loss trajectory."""
import sys, time; sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np
from scipy.optimize import minimize
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step29 import noise as N29
from src.step30.cohiqp import CohIQP, EPS_MAX, LAM_LO, LBFGS_OPTS
from src.step26.flipiqp import _bits
from src.step27 import run as R27
p = N29.coherent_grid_iqp(1067, 0.2, 0.02); fhat, ops = training_moments(p, 10_000, 1067, 16)
F = R27.raw_floor(fhat, 10_000)
m = CohIQP(16, Gd.LOCAL_GENS); m._B = _bits(np.asarray(ops), 16)
rng = np.random.default_rng(0)
x0 = np.concatenate([rng.normal(0, .3, m.K), rng.normal(0, .05, m.E*16), np.ones(16)])
bounds = [(None, None)] * m.K + [(-EPS_MAX, EPS_MAX)] * (m.E * 16) + [(LAM_LO, 1.0)] * 16
t0 = time.time(); it = [0]
def cb(xk):
    it[0] += 1
    if it[0] % 250 == 0: print(it[0], round(time.time()-t0), m.loss_and_grad(xk, fhat, ops)[0] / F, flush=True)
r = minimize(m.loss_and_grad, x0, args=(fhat, ops), jac=True, method="L-BFGS-B", bounds=bounds, options=LBFGS_OPTS, callback=cb)
print("done", r.nit, r.nfev, round(time.time()-t0), r.fun / F, r.message, flush=True)

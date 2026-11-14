"""Exploration (spent seeds 980-983): IQP + learned per-qubit flip damping on gate-noise + 2% readout data.
No calibrated eta is used: the damping is learned from the same order<=3 moments."""
import sys, json, time
import numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step26 import noise as Nz
from src.step26.flipiqp import FlipIQP

seed, pg = int(sys.argv[1]), float(sys.argv[2]); NB = 16; N = 10_000; t0 = time.time()
p = Nz.noisy_grid_iqp(seed, pg, 0.02)
fhat, ops = training_moments(p, N, seed, NB)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
m = FlipIQP(NB, Gd.LOCAL_GENS).fit(fhat, ops, seed=seed)
G = M1.completion_gap(m.prob(), p, NB)["G"]
lam = m.x[m.K:]
print(json.dumps({"seed": seed, "p_gate": pg, "R_flip_me3": G / Gme, "resid_over_floor": m.resid / float(np.sum(1 - fhat**2) / N),
                  "lam_min": float(lam.min()), "lam_med": float(np.median(lam)), "secs": round(time.time() - t0)}), flush=True)

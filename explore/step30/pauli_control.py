"""Exploration (spent seeds 1000-1013, step 26 g01 data: independent Pauli 1%, correct graph): does CohIQP hurt under
Pauli noise? Compares with the stored step 26 FlipIQP arm on the same moments."""
import sys, json, time
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np
from src.step1 import metrics as M1
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step26 import noise as N26
from src.step30.cohiqp import CohIQP
seed = int(sys.argv[1]); which = sys.argv[2] if len(sys.argv) > 2 else "given"; t0 = time.time()
old = json.load(open(rf"C:\Users\tseng\qgen-practical-step1\results\step26\g01\seed_{seed}\metrics.json"))
p = N26.noisy_grid_iqp(seed, 0.01, 0.02)
fhat, ops = training_moments(p, 10_000, seed, 16)
F = float(np.sum(1 - fhat**2) / 10_000)
m = CohIQP(16, Gd.LOCAL_GENS, tied=(which == "tied")).fit(fhat, ops, seed=seed)
G = M1.completion_gap(m.prob(), p, 16)["G"]
out = {"seed": seed, "cond": "g01", "which": which, "R_coh": round(G / old["G_me3"], 3), "ratio_coh": round(m.resid / F, 3),
       "R_given29": round(old["R_flip_me3"], 3), "ratio_given29": round(old["flip_resid_over_floor"], 3),
       "R_flow29": None, "R_enl29": None, "lam_min": round(float(m._split(m.x)[2].min()), 3),
       "eps_fit": np.round(m._split(m.x)[1], 2).tolist(), "secs": round(time.time() - t0)}
open(rf"C:\Users\tseng\qgen-practical-step1\explore\step30\out\g01_{which}_{seed}.json", "w").write(json.dumps(out))

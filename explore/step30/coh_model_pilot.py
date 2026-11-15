"""Exploration (spent seeds 1060-1073, the step 29 xf02/xm02 data): CohIQP on the given graph vs the stored step 29 arms.
2% readout, N = 1e4, same moments as step 29 (training_moments(p, 1e4, seed)). Prints one JSON line."""
import sys, json, time
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np
from src.step1 import metrics as M1
from src.step4.run import training_moments
from src.step25.run import ENLARGED
from src.step27 import run as R27
from src.step29 import noise as N29
from src.step30.cohiqp import CohIQP
seed, cond = int(sys.argv[1]), sys.argv[2]; which = sys.argv[3] if len(sys.argv) > 3 else "given"
t0 = time.time()
old = json.load(open(rf"C:\Users\tseng\qgen-practical-step1\results\step29\{cond}\seed_{seed}\metrics.json"))
kind = "full" if cond.startswith("xf") else "miss"
p = N29.coherent_grid_iqp(seed, old["eps_std"], 0.02)
fhat, ops = training_moments(p, 10_000, seed, 16)
F = R27.raw_floor(fhat, 10_000)

m = CohIQP(16, R27.given_graph(kind, seed)[0], tied=(which == "tied")).fit(fhat, ops, seed=seed)
G = M1.completion_gap(m.prob(), p, 16)["G"]
out = {"seed": seed, "cond": cond, "which": which, "R_coh": round(G / old["G_me3"], 3), "ratio_coh": round(m.resid / F, 3),
       "R_given29": round(old["R_given_me3"], 3), "ratio_given29": round(old["ratio_given"], 3),
       "R_flow29": round(old["R_flow_me3"], 3), "R_enl29": round(old["R_enl_me3"], 3),
       "eps_true": np.round(N29.eps_of(seed, old["eps_std"]), 2).tolist(),
       "eps_fit": np.round(m._split(m.x)[1], 2).tolist(), "lam_min": round(float(m._split(m.x)[2].min()), 3),
       "secs": round(time.time() - t0)}
print(json.dumps(out), flush=True)
open(rf"C:\Users\tseng\qgen-practical-step1\explore\step30\out\{cond}_{which}_{seed}.json", "w").write(json.dumps(out))

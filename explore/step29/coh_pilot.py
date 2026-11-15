"""Exploration (spent seeds 980-985): step 27 recipe on COHERENT RX over-rotation errors + 2% readout.
Per-gate infidelity per qubit is about eps^2/4: eps_std 0.1 ~ 0.25%, 0.2 ~ 1%."""
import sys, json, time
import numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step25.run import ENLARGED
from src.step26.flipiqp import FlipIQP
from src.step27 import run as R27
from src.step29 import noise as N29

seed, es, kind = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]; NB = 16; N = 10_000; t0 = time.time()
p = N29.coherent_grid_iqp(seed, es, 0.02)
fhat, ops = training_moments(p, N, seed, NB)
F = R27.raw_floor(fhat, N)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
out = {"seed": seed, "eps_std": es, "kind": kind}
for name, gens in (("given", R27.given_graph(kind, seed)[0]), ("enl", ENLARGED)):
    m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
    out[f"R_{name}"] = M1.completion_gap(m.prob(), p, NB)["G"] / Gme
    out[f"ratio_{name}"] = m.resid / F
    out[f"lam_min_{name}"] = float(m.x[m.K:].min())
out["R_flow"] = out["R_enl"] if out["ratio_given"] > R27.THRESH else out["R_given"]
out["secs"] = round(time.time() - t0)
print(json.dumps(out), flush=True)

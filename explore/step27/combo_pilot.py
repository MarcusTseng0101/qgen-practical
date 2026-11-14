"""Exploration (spent seeds): missing couplers + gate noise + 2% readout. FlipIQP on the given (missing) graph,
on the 103-gen enlarged graph, and on the true full graph. Reports resid/raw floor and R vs me3."""
import sys, json, time
import numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step24 import conds as C24
from src.step25.run import ENLARGED
from src.step26 import noise as Nz
from src.step26.flipiqp import FlipIQP

seed, pg = int(sys.argv[1]), float(sys.argv[2]); NB = 16; N = 10_000; t0 = time.time()
p = Nz.noisy_grid_iqp(seed, pg, 0.02)
fhat, ops = training_moments(p, N, seed, NB)
F = float(np.sum(1 - fhat**2) / N)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
out = {"seed": seed, "p_gate": pg}
for name, gens in (("given", C24.model_masks("miss", seed)[0]), ("enl", ENLARGED), ("true", Gd.LOCAL_GENS)):
    m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
    out[f"R_{name}"] = M1.completion_gap(m.prob(), p, NB)["G"] / Gme
    out[f"ratio_{name}"] = m.resid / F
out["secs"] = round(time.time() - t0)
print(json.dumps(out), flush=True)

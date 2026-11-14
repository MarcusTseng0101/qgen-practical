"""Exploration (spent seeds 980-985): step 27 recipe on CORRELATED gate noise + 2% readout.
kind = full | miss. Reports ratio, R of given / enlarged / flow vs me3, and how far the data are from step 26's
independent-noise data at the same marginal rate (TV distance)."""
import sys, json, time
import numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step25.run import ENLARGED
from src.step26 import noise as N26
from src.step26.flipiqp import FlipIQP
from src.step27 import run as R27
from src.step28 import noise as N28

seed, pg, kind = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]; NB = 16; N = 10_000; t0 = time.time()
p = N28.correlated_grid_iqp(seed, pg, 0.02)
tv = 0.5 * float(np.abs(p - N26.noisy_grid_iqp(seed, pg, 0.02)).sum())
fhat, ops = training_moments(p, N, seed, NB)
F = R27.raw_floor(fhat, N)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
out = {"seed": seed, "p_gate": pg, "kind": kind, "tv_vs_indep": tv}
for name, gens in (("given", R27.given_graph(kind, seed)[0]), ("enl", ENLARGED)):
    m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
    out[f"R_{name}"] = M1.completion_gap(m.prob(), p, NB)["G"] / Gme
    out[f"ratio_{name}"] = m.resid / F
out["R_flow"] = out["R_enl"] if out["ratio_given"] > R27.THRESH else out["R_given"]
out["secs"] = round(time.time() - t0)
print(json.dumps(out), flush=True)

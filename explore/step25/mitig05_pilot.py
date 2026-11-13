"""Exploration (spent step 24 noise05 seeds): readout-mitigated local IQP at eta = 5%."""
import sys, json, time, numpy as np
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step24 import conds as C

seed = int(sys.argv[1]); NB = 16; eta = 0.05; t0 = time.time()
p = C.data_dist("noise05", seed)
fhat, ops = training_moments(p, 10_000, seed, NB)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
m = IQPModel(NB, gens=Gd.LOCAL_GENS)
f = m.fit_moments(C.mitigate(fhat, ops, eta), ops, seed=seed, n_restarts=20, init_std=0.3)
G = M1.completion_gap(C.readout_channel(m.prob(f.params), eta), p, NB)["G"]
print(json.dumps({"seed": seed, "R_mitig_me3": G / Gme, "secs": round(time.time() - t0)}), flush=True)

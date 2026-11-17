"""Step 34 exploration (SPENT seeds 1080-1086, the step 31 data at N = 1e5, 2% readout).
Question: at N = 1e5, which statistics separate (correct vs missing-coupler graph) x (Pauli vs coherent noise), so that
one recipe can choose enlargement and/or CohIQP?

Data are step 31's (src.step31.run.data): cf = coherent eps 0.2, pf = Pauli 1%. The model graph is either the correct
('full') graph or the step 24 'miss' graph (2 couplers missing); the data do not change.

python explore/step34/pilot.py COND GRAPH ARM SEED     COND in {cf, pf}; GRAPH in {full, miss, enl}; ARM in {flip, coh}
Writes explore/step34/out/COND_GRAPH_ARM_SEED.json (skips if it exists, so the batch is resumable)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np

from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step25.run import ENLARGED
from src.step26.flipiqp import FlipIQP
from src.step27.run import given_graph, raw_floor
from src.step30.cohiqp import CohIQP
from src.step31 import run as R31

cond, graph, arm, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
OUT = Path(r"C:\Users\tseng\qgen-practical-step1\explore\step34\out") / f"{cond}_{graph}_{arm}_{seed}.json"
if OUT.exists():
    sys.exit(0)
t0 = time.time()
NB, N = 16, R31.N_SHOTS
p = R31.data(cond, seed)
fhat, ops = training_moments(p, N, seed, NB)
F = raw_floor(fhat, N)
gens = ENLARGED if graph == "enl" else given_graph(graph, seed)[0]
G = lambda q: M1.completion_gap(q, p, NB)["G"]
me = MaxEntModel(NB, 3)
out = {"cond": cond, "graph": graph, "arm": arm, "seed": seed, "N": N, "n_gens": len(gens),
       "G_me3": G(me.prob(me.fit_moments(fhat, ops).params))}
m = (FlipIQP(NB, gens) if arm == "flip" else CohIQP(NB, gens, tied=False)).fit(fhat, ops, seed=seed)
out["G"] = G(m.prob())
out["ratio"] = m.resid / F
out["R_me3"] = out["G"] / out["G_me3"]
out["secs"] = time.time() - t0
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(out))
print(json.dumps(out), flush=True)

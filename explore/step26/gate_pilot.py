"""Exploration (spent seeds 980-983): step 25 pipeline on data with gate-level depolarizing noise + 2% readout."""
import sys, json, time
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step25 import run as P
from src.step26 import noise as Nz

seed, pg = int(sys.argv[1]), float(sys.argv[2]); eta = 0.02; NB = 16; N = 10_000; t0 = time.time()
p = Nz.noisy_grid_iqp(seed, pg, eta)
fhat, ops = training_moments(p, N, seed, NB)
G = {}
for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, Gd.LOCAL_ME))):
    G[name] = M1.completion_gap(mdl.prob(mdl.fit_moments(fhat, ops).params), p, NB)["G"]
r = P.pipeline(fhat, ops, eta, N, Gd.LOCAL_GENS, seed)
G["pipe"] = M1.completion_gap(r["q"], p, NB)["G"]
G["stage1"] = M1.completion_gap(r["q1"], p, NB)["G"]
print(json.dumps({"seed": seed, "p_gate": pg, "R_me3": G["pipe"] / G["me3"], "R_stage1": G["stage1"] / G["me3"],
                  "R_me_local": G["pipe"] / G["me_local"], "ratio1": r["ratio1"], "flag": r["flag"],
                  "ratio2": r.get("ratio2"), "secs": round(time.time() - t0)}), flush=True)

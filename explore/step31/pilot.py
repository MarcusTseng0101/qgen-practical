"""Step 31 exploration (SPENT seeds 1060-1073, step 29 xf02 data: coherent eps_std 0.2, correct graph, 2% readout).
Question: does more shots (N = 1e5) or exact moments (N = inf) let the unchanged step 27 recipe, or step 30's
untied CohIQP, beat MaxEnt(3) on the correct graph where step 29 got 10/14 at N = 1e4?

python explore/step31/pilot.py SEED ARM   with ARM in {recipe5, coh5, given_inf}
Writes explore/step31/out/ARM_SEED.json."""
import json
import sys
import time

sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
import numpy as np

from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step25.run import ENLARGED
from src.step26.flipiqp import FlipIQP
from src.step27.run import flow_choice, given_graph, raw_floor
from src.step29 import noise as N29
from src.step30.cohiqp import CohIQP

seed, arm = int(sys.argv[1]), sys.argv[2]
NB = Gd.N_BITS
N = None if arm.endswith("inf") else 100_000
t0 = time.time()
p = N29.coherent_grid_iqp(seed, 0.2, 0.02)
fhat, ops = training_moments(p, N, seed, NB)
gens, me_masks = given_graph("full", seed)
G = lambda q: M1.completion_gap(q, p, NB)["G"]
out = {"seed": seed, "arm": arm, "N": N}
me = MaxEntModel(NB, 3)
out["G_me3"] = G(me.prob(me.fit_moments(fhat, ops).params))
if arm == "recipe5":
    F = raw_floor(fhat, N)
    ml = Gd.MaxEntOn(NB, me_masks)
    out["G_me_local"] = G(ml.prob(ml.fit_moments(fhat, ops).params))
    for name, g in (("given", gens), ("enl", ENLARGED)):
        m = FlipIQP(NB, g).fit(fhat, ops, seed=seed)
        out[f"G_{name}"] = G(m.prob())
        out[f"ratio_{name}"] = m.resid / F
        out[f"lam_med_{name}"] = float(np.median(m.x[m.K:]))
    out["flow_pick"] = flow_choice(out["ratio_given"])
    out["G_flow"] = out[f"G_{out['flow_pick']}"]
elif arm == "coh5":
    F = raw_floor(fhat, N)
    m = CohIQP(NB, gens, tied=False).fit(fhat, ops, seed=seed)
    out["G_coh"] = G(m.prob())
    out["ratio_coh"] = m.resid / F
elif arm == "given_inf":
    m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
    out["G_given"] = G(m.prob())
    out["resid_given"] = float(m.resid)
out["secs"] = time.time() - t0
open(rf"C:\Users\tseng\qgen-practical-step1\explore\step31\out\{arm}_{seed}.json", "w").write(json.dumps(out))
print(json.dumps(out), flush=True)

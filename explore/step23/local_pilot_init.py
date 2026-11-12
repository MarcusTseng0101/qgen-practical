"""Exploration (new dev seeds 900+): does a device-connectivity prior make the IQP identifiable?
Device: 4x4 grid. Target: IQP on singles + NN edges + plaquettes (16 + 24 + 9 = 49 gens), theta = SIGMA * N(0,1).
Models (all fitted to order<=3 moments only):
  iqp_local : candidates = all grid-local gens of weight <= 4 (singles, edges, plaquette corner triples,
              plaquettes; 85) -- the device graph is known, which gens are active is not
  iqp_generic: 696 gens (the existing model)
  me3       : MaxEnt(3), 696 params
  me_local  : MaxEnt on the 76 grid-local parities of weight <= 3 (fair: same graph prior)
"""
import sys, json, time, numpy as np
from itertools import combinations
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, parity_matrix
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import iqp_distribution
from src.step4.run import training_moments
from src.step14.run import SIGMA

n, L = 16, 4
q = lambda r, c: r * L + c
mk = lambda s: int(sum(1 << j for j in s))
singles = [(j,) for j in range(n)]
edges = [(q(r, c), q(r, c + 1)) for r in range(L) for c in range(L - 1)] + \
        [(q(r, c), q(r + 1, c)) for r in range(L - 1) for c in range(L)]
plaqs = [(q(r, c), q(r, c + 1), q(r + 1, c), q(r + 1, c + 1)) for r in range(L - 1) for c in range(L - 1)]
tris = [t for P in plaqs for t in combinations(P, 3)]
T_GENS = np.array([mk(s) for s in singles + edges + plaqs])
C_GENS = np.array(sorted({mk(s) for s in singles + edges + tris + plaqs}))
ME_LOCAL = np.array(sorted({mk(s) for s in singles + edges + tris}))


class MaxEntOn(MaxEntModel):
    def __init__(self, n, masks):
        super().__init__(n, 1)
        self.k = 3
        self.masks = np.asarray(masks, np.int64); self.n_params = len(self.masks)
        self.F = parity_matrix(n, self.masks)


seed = int(sys.argv[1]); N = None if sys.argv[2] == "inf" else int(sys.argv[2])
sig = SIGMA
RESTARTS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
INIT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.05  # guess
t = time.time()
th = sig * np.random.default_rng(seed).normal(size=len(T_GENS))
p = iqp_distribution(n, T_GENS, th); p /= p.sum()
fhat, ops = training_moments(p, N, seed, n)
G = {}
for name, mdl in (("me3", MaxEntModel(n, 3)), ("me_local", MaxEntOn(n, ME_LOCAL))):
    G[name] = M1.completion_gap(mdl.prob(mdl.fit_moments(fhat, ops).params), p, n)["G"]
for name, gens in (("iqp_local", C_GENS),) + ((("iqp_generic", None),) if RESTARTS == 3 else ()):
    m = IQPModel(n, gens=gens)
    f = m.fit_moments(fhat, ops, seed=seed, n_restarts=RESTARTS, init_std=INIT)
    G[name + "_all_resid"] = sorted(f.restart_residuals)[:5]
    G[name] = M1.completion_gap(m.prob(f.params), p, n)["G"]
    G[name + "_resid"] = f.train_residual
out = {"seed": seed, "N": N, "sigma": sig, **G,
       "R_local_vs_me3": G["iqp_local"] / G["me3"], "R_local_vs_melocal": G["iqp_local"] / G["me_local"],
       "R_generic_vs_me3": G.get("iqp_generic", float("nan")) / G["me3"], "restarts": RESTARTS, "init_std": INIT, "secs": round(time.time() - t)}
print(json.dumps(out), flush=True)

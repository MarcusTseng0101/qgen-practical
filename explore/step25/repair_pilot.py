"""Exploration (spent step 24 `miss` seeds): residual-triggered graph repair.
Start from the step 24 `miss` graph (2 true couplers absent). Fit iqp_local. While resid/floor > THRESH and rounds < MAX:
score every weight-2 pair not yet a candidate by |dL/dtheta| at theta_new = 0 (gradient screening), add the top pair
together with any grid triples/plaquettes containing both its endpoints, refit (warm start + random restarts).
Report: which pairs were added (true dropped edges?), resid/floor per round, final R vs me3."""
import sys, json, time, numpy as np
from itertools import combinations
sys.path.insert(0, r"C:\Users\tseng\qgen-practical-step1")
from src.step1 import metrics as M1
from src.step1.bits import popcount
from src.step1.models.iqp import IQPModel, LBFGS_OPTS
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step24 import conds as C
from scipy.optimize import minimize

THRESH, MAX_ROUNDS, RESTARTS, REFIT_RANDOM = 1.0, 4, 20, 4   # guesses
seed = int(sys.argv[1]); NB = 16; N = 10_000
t0 = time.time()
p = C.data_dist("miss", seed)
fhat, ops = training_moments(p, N, seed, NB)
floor = float(np.sum(1 - fhat**2) / N)
me = MaxEntModel(NB, 3); Gme = M1.completion_gap(me.prob(me.fit_moments(fhat, ops).params), p, NB)["G"]
gens, _ = C.model_masks("miss", seed)
dropped = [(1 << a) | (1 << b) for a, b in C.dropped_edges(seed)]
m = IQPModel(NB, gens=gens)
f = m.fit_moments(fhat, ops, seed=seed, n_restarts=RESTARTS, init_std=0.3)
th, L = f.params, f.train_residual
rows = [{"round": 0, "n_gens": len(gens), "resid_over_floor": L / floor,
         "R": M1.completion_gap(m.prob(th), p, NB)["G"] / Gme}]
print(json.dumps(rows[-1]), flush=True)
pairs = np.array([(1 << a) | (1 << b) for a, b in combinations(range(NB), 2)], dtype=np.int64)
rng = np.random.default_rng(seed + 777)
for rd in range(1, MAX_ROUNDS + 1):
    if L / floor <= THRESH:
        break
    cur = set(gens.tolist())
    pool = np.array([x for x in pairs.tolist() if x not in cur], dtype=np.int64)
    mm = IQPModel(NB, gens=np.concatenate([gens, pool]))
    g = mm.loss_and_grad(np.concatenate([th, np.zeros(len(pool))]), fhat, ops)[1][len(gens):]
    order = np.argsort(-np.abs(g))
    pick = int(pool[order[0]])
    add = [pick] + [x for x in Gd.LOCAL_GENS.tolist() if popcount(np.array([x]))[0] >= 3 and (x & pick) == pick
                    and x not in cur]
    gens = np.concatenate([gens, np.array(add, dtype=np.int64)])
    m = IQPModel(NB, gens=gens)
    inits = [np.concatenate([th, np.zeros(len(add))])] + [rng.normal(0, 0.3, len(gens)) for _ in range(REFIT_RANDOM)]
    best = None
    for x0 in inits:
        r = minimize(m.loss_and_grad, x0, args=(fhat, ops), jac=True, method="L-BFGS-B", options=LBFGS_OPTS)
        if best is None or r.fun < best.fun:
            best = r
    th, L = best.x, float(best.fun)
    top5 = [(int(pool[i]) in dropped) for i in order[:5]]
    rows.append({"round": rd, "pick": pick, "pick_is_dropped": pick in dropped, "top5_dropped": top5,
                 "added": len(add), "n_gens": len(gens), "resid_over_floor": L / floor,
                 "R": M1.completion_gap(m.prob(th), p, NB)["G"] / Gme})
    print(json.dumps(rows[-1]), flush=True)
print("RESULT " + json.dumps({"seed": seed, "dropped": dropped, "rows": rows, "secs": round(time.time() - t0)}), flush=True)

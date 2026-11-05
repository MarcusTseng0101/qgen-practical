"""H1 verdict and completion spread for the oracle-support IQP at sigma = 0.05, seeds 0-4.

Diagnostic only: imports src/step1 and src/step2, changes nothing, writes only here.
fit_moments keeps only the best restart's parameters, so the 10 restarts are replayed here
with exactly its generic-path init draws (default_rng(seed), N(0, 0.05^2) per restart) and
LBFGS_OPTS. The replayed best residual is checked against fit_moments itself.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, popcount
from src.step1.models.iqp import INIT_STD, LBFGS_OPTS, N_RESTARTS, IQPModel
from src.step1.walsh import parity_coefficients
from src.step2.sweep import SUCCESS_TOL, d3, sigma_target

n, SIGMA = 12, 0.05
HERE = Path(__file__).resolve().parent


def gauge_mismatch(th, theta, masks):
    """Sign mismatches after a canonical gauge fixing. The exact symmetries of p are
    theta_g -> (-1)^{|g&B|} theta_g (any bit set B) and theta -> -theta. One-body signs are
    pure gauge, so for each global sign choose the unique B that makes all 12 one-body signs
    match theta*, then count pair and triple mismatches; keep the global sign with fewer.
    (The min-over-all-gauges count used first for seed 0 has ties between gauges with
    different pair/one-body composition; this fixing has none, and it reproduces the seed-0
    result: 8 mismatches, all pairs.)
    Returns (total, pair, triple mismatches, B, global sign)."""
    w = popcount(masks)
    one = np.flatnonzero(w == 1)
    best = None
    for gs in (1.0, -1.0):
        B = 0
        for i in one:
            j = int(masks[i]).bit_length() - 1
            if np.sign(gs * th[i]) != np.sign(theta[i]):
                B |= 1 << j
        S = 1.0 - 2.0 * (popcount(masks & B) % 2)
        mism = np.sign(gs * S * th) != np.sign(theta)
        res = (int(mism.sum()), int((mism & (w == 2)).sum()), int((mism & (w == 3)).sum()), B, gs)
        if best is None or res[0] < best[0]:
            best = res
    return best


rows, seeds_out = [], []
for seed in range(5):
    p, masks, theta, z, layout = sigma_target(SIGMA, seed, n)
    ops = masks_up_to(n, 3)
    fhat = parity_coefficients(p)[ops]
    model = IQPModel(n, gens=masks)
    rng = np.random.default_rng(seed)
    sols = []
    for r in range(N_RESTARTS):
        theta0 = rng.normal(0.0, INIT_STD, model.n_params)
        res = minimize(model.loss_and_grad, theta0, args=(fhat, ops), jac=True,
                       method="L-BFGS-B", options=LBFGS_OPTS)
        L = model.loss_and_grad(res.x, fhat, ops)[0]
        G = M1.completion_gap(model.prob(res.x), p, n)
        tot, pair_m, tri_m, b, gs = gauge_mismatch(res.x, theta, masks)
        sols.append({"seed": seed, "restart": r, "residual": float(L), "G_iqp": G["G"],
                     "per_level": G["per_level"], "sign_mismatch_total": tot,
                     "sign_mismatch_pairs": pair_m, "sign_mismatch_triples": tri_m, "gauge_B": b, "global_sign": gs,
                     "nit": int(res.nit), "message": str(res.message)})
    check = model.fit_moments(fhat, ops, seed=seed).train_residual
    best = min(sols, key=lambda s: s["residual"])
    assert abs(check - best["residual"]) <= 1e-12 * max(1.0, check), (check, best["residual"])
    D3, q_me, _ = d3(p, n)
    G_me = M1.completion_gap(q_me, p, n)["G"]
    G_true = M1.completion_gap(p, p, n)["G"]
    G_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p, n)["G"]
    n_ok = sum(s["residual"] <= SUCCESS_TOL for s in sols)
    seeds_out.append({"seed": seed, "best_residual": best["residual"], "n_success_restarts": n_ok,
                      "success": n_ok > 0, "best_sign_mismatch_pairs": best["sign_mismatch_pairs"],
                      "best_sign_mismatch_total": best["sign_mismatch_total"],
                      "best_sign_mismatch_triples": best["sign_mismatch_triples"],
                      "G_true": G_true, "G_maxent": G_me, "G_uniform": G_uni, "D3": D3,
                      "fit_moments_best_residual": check})
    rows += sols
    print(f"seed {seed}: best {best['residual']:.3e}  success {n_ok}/10  best mism pairs "
          f"{best['sign_mismatch_pairs']}, triples {best['sign_mismatch_triples']} (total {best['sign_mismatch_total']})  G_maxent {G_me:.3e}  "
          f"G_true {G_true:.1e}", flush=True)

(HERE / "h1_all_seeds.json").write_text(json.dumps({"sigma": SIGMA, "seeds": seeds_out,
                                                    "solutions": rows}, indent=1))

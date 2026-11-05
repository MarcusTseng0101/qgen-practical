"""FM2 diagnostics for step 1 (biased, N = inf, seed 0, n = 12). Not part of the pipeline;
nothing here writes to results/. Imports the production code, does not modify it.

  python -m diagnostics.step1_fm2.diag near    # (1) start near the embedded true angles
  python -m diagnostics.step1_fm2.diag lbfgs   # (2) 50 small-angle restarts, L-BFGS-B
  python -m diagnostics.step1_fm2.diag lsq     # (3) first 10 of (2)'s inits, least_squares trf

Each part writes diagnostics/step1_fm2/<part>.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares, minimize

from src.step1.bits import masks_up_to, subset_mask
from src.step1.models.iqp import INIT_STD, LBFGS_OPTS, IQPModel
from src.step1.targets import make_target
from src.step1.walsh import parity_coefficients

OUT = Path(__file__).resolve().parent
N_BITS, SEED = 12, 0


def setup():
    p, meta = make_target("biased", N_BITS, SEED)
    model = IQPModel(N_BITS)
    ops = masks_up_to(N_BITS, 3)
    fhat = parity_coefficients(p)[ops]
    pos = {int(m): i for i, m in enumerate(model.gens)}
    theta_true = np.zeros(model.n_params)
    for g, a in zip(meta["generators"], meta["angles"]):
        theta_true[pos[subset_mask(g)]] += a
    return model, ops, fhat, theta_true


def sv_min_max(model, theta, ops):
    sv = np.linalg.svd(model.moment_jacobian(theta, ops), compute_uv=False)
    return float(sv[-1]), float(sv[0]), int(np.sum(sv > 1e-8 * sv[0]))


def lbfgs(model, theta0, fhat, ops):
    t0 = time.time()
    res = minimize(model.loss_and_grad, theta0, args=(fhat, ops), jac=True,
                   method="L-BFGS-B", options=LBFGS_OPTS)
    L = model.loss_and_grad(res.x, fhat, ops)[0]
    return res, L, time.time() - t0


def part_near():
    model, ops, fhat, theta_true = setup()
    L0 = model.loss_and_grad(theta_true, fhat, ops)[0]
    rows = []
    for sigma in (0.01, 0.1, 0.3):
        for k in range(5):
            rng = np.random.default_rng(10_000 + 100 * int(sigma * 100) + k)
            theta0 = theta_true + rng.normal(0.0, sigma, model.n_params)
            res, L, sec = lbfgs(model, theta0, fhat, ops)
            smin, smax, rank = sv_min_max(model, res.x, ops)
            rows.append({"sigma": sigma, "rep": k, "init_residual": model.loss_and_grad(theta0, fhat, ops)[0],
                         "residual": L, "nit": int(res.nit), "message": str(res.message),
                         "dist_to_true": float(np.linalg.norm(res.x - theta_true)),
                         "sv_min": smin, "sv_max": smax, "rank": rank, "seconds": sec})
            print(f"sigma {sigma:<5} rep {k}: residual {L:.3e}  nit {res.nit:5d}  sv_min {smin:.2e}  "
                  f"|theta-theta*| {rows[-1]['dist_to_true']:.3f}", flush=True)
    smin_true, smax_true, rank_true = sv_min_max(model, theta_true, ops)
    return {"residual_at_true": L0, "sv_min_at_true": smin_true, "sv_max_at_true": smax_true,
            "rank_at_true": rank_true, "runs": rows}


def small_inits(n):
    """The same draws as fit_moments(seed=0): rng = default_rng(0), one N(0, INIT_STD^2) vector
    per restart, so the first 10 are exactly the production restarts."""
    rng = np.random.default_rng(SEED)
    return [rng.normal(0.0, INIT_STD, 298) for _ in range(n)]


def part_lbfgs():
    model, ops, fhat, _ = setup()
    rows = []
    for r, theta0 in enumerate(small_inits(50)):
        res, L, sec = lbfgs(model, theta0, fhat, ops)
        smin, smax, rank = sv_min_max(model, res.x, ops)
        rows.append({"restart": r, "residual": L, "nit": int(res.nit), "message": str(res.message),
                     "sv_min": smin, "rank": rank, "seconds": sec})
        print(f"restart {r:2d}: residual {L:.3e}  nit {res.nit:5d}  sv_min {smin:.2e}", flush=True)
    res_sorted = sorted(x["residual"] for x in rows)
    return {"runs": rows, "sorted_residuals": res_sorted, "median": float(np.median(res_sorted)),
            "min": res_sorted[0], "max": res_sorted[-1]}


def part_lsq():
    model, ops, fhat, _ = setup()
    fun = lambda th: model.moments(th, ops) - fhat
    jac = lambda th: model.moment_jacobian(th, ops)
    rows = []
    for r, theta0 in enumerate(small_inits(10)):
        t0 = time.time()
        res = least_squares(fun, theta0, jac=jac, method="trf", xtol=1e-15, ftol=1e-15, gtol=1e-15)
        sec = time.time() - t0
        L = float(np.sum(fun(res.x) ** 2))
        smin, smax, rank = sv_min_max(model, res.x, ops)
        rows.append({"restart": r, "residual": L, "nfev": int(res.nfev), "njev": int(res.njev or 0),
                     "status": int(res.status), "message": str(res.message), "sv_min": smin,
                     "rank": rank, "seconds": sec})
        print(f"restart {r}: residual {L:.3e}  nfev {res.nfev}  njev {res.njev}  status {res.status}  "
              f"sv_min {smin:.2e}  ({sec:.0f} s)  {res.message}", flush=True)
    return {"runs": rows, "sorted_residuals": sorted(x["residual"] for x in rows)}


if __name__ == "__main__":
    part = sys.argv[1]
    out = {"near": part_near, "lbfgs": part_lbfgs, "lsq": part_lsq}[part]()
    out["config"] = {"target": "biased", "N": "inf", "seed": SEED, "n": N_BITS,
                     "lbfgs_options": LBFGS_OPTS, "init_std": INIT_STD}
    (OUT / f"{part}.json").write_text(json.dumps(out, indent=1))

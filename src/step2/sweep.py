"""Step 2: the recoverability / completion-room boundary in the angle scale sigma.

specs/step2_sigma_boundary.md. One (sigma, seed) -> results/step2/sigma_<sigma>/seed_<s>/metrics.json.

  python -m src.step2.sweep --sigma 0.05 --seed 0 [--fits O,G] [--out DIR]
  python -m src.step2.sweep --all          (refuses to start without BUDGET_OK)

Targets: the step-1 `biased` layout of seed s (12 one-body, 18 pairs, 8 triples) with
theta = sigma * z, where z ~ N(0, 1) is drawn ONCE per seed and reused across sigma, so each
seed traces a path in sigma. At sigma = 0.4 this is exactly step 1's `biased` target, because
step 1 drew N(0, 0.4^2) = 0.4 * z from the same rng state.

Fits (N = inf only), each with 10 restarts, init N(0, 0.05^2), and step-1 L-BFGS-B settings:
- O (oracle support): the IQP restricted to the target's own 38 generators. A DIAGNOSTIC of
  the landscape only, never a practical method.
- G (generic): step 1's 298-generator IQP.
- MaxEnt(3): gives D3 = KL(p || MaxEnt3(p)) and the R denominators.

Everything model- and metric-related is imported from src/step1 (a closed record, never
edited); only this file is new.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.bits import fwht, masks_up_to, popcount, subset_mask
from src.step1.models.iqp import IQPModel, N_RESTARTS
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import _iqp_layout, iqp_distribution
from src.step1.versions import versions
from src.step1.walsh import parity_coefficients

N_BITS = 12
SIGMAS = (0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.6)
SEEDS = (0, 1, 2, 3, 4)
SUCCESS_TOL = 1e-10     # spec: a restart succeeds if its training residual is <= 1e-10
ROOT = Path(__file__).resolve().parents[2]


# ---------------- targets ----------------
def sigma_target(sigma: float, seed: int, n: int = N_BITS):
    """(p, gens_masks, theta, z, layout) for theta = sigma * z on the step-1 `biased` layout.
    The rng sequence is the same as step 1's biased target: layout first, then z."""
    rng = np.random.default_rng(100 + seed)
    layout = _iqp_layout(n, rng)
    z = rng.normal(0.0, 1.0, len(layout))
    masks = np.array([subset_mask(g) for g in layout], dtype=np.int64)
    theta = sigma * z
    p = iqp_distribution(n, masks, theta)
    return p / p.sum(), masks, theta, z, layout


# ---------------- target statistics ----------------
def kl(p: np.ndarray, q: np.ndarray) -> float:
    """KL(p || q) in nats; terms with p = 0 contribute 0."""
    p, q = np.asarray(p, dtype=np.float64), np.asarray(q, dtype=np.float64)
    m = p > 0
    return float(np.sum(p[m] * (np.log(p[m]) - np.log(q[m]))))


def hi_order_frac(p: np.ndarray, kmin: int = 4) -> float:
    """sum_{|A| >= kmin} f_A^2 / sum_{|A| >= 1} f_A^2."""
    f = parity_coefficients(p)
    w = popcount(np.arange(len(p)))
    f2 = f**2
    return float(f2[w >= kmin].sum() / f2[w >= 1].sum())


def d3(p: np.ndarray, n: int = N_BITS):
    """D3 = KL(p || MaxEnt3(p)), MaxEnt(3) fitted to the exact order-<=3 moments of p.
    Returns (D3, the MaxEnt distribution, its fit residual)."""
    ops = masks_up_to(n, 3)
    me = MaxEntModel(n, 3)
    fit = me.fit_moments(parity_coefficients(p)[ops], ops)
    q = me.prob(fit.params)
    return kl(p, q), q, fit.train_residual


# ---------------- fits ----------------
def fit_iqp(model: IQPModel, fhat, ops, seed: int, n_restarts: int = N_RESTARTS) -> dict:
    t0 = time.time()
    fit = model.fit_moments(fhat, ops, seed=seed, n_restarts=n_restarts)
    res = [float(r) for r in fit.restart_residuals]
    n_ok = int(sum(r <= SUCCESS_TOL for r in res))
    return {"fit": fit, "best_residual": float(fit.train_residual), "n_success_restarts": n_ok,
            "success": n_ok > 0, "restart_residuals": res, "restarts": fit.restarts,
            "trace": [float(x) for x in fit.trace], "n_params": int(model.n_params),
            "seconds": time.time() - t0}


def run_one(sigma: float, seed: int, n: int = N_BITS, fits=("O", "G"),
            restarts: dict | None = None) -> dict:
    restarts = restarts or {}
    t_start = time.time()
    p, masks, theta, z, layout = sigma_target(sigma, seed, n)
    ops = masks_up_to(n, 3)
    fhat = parity_coefficients(p)[ops]

    D3, q_me, me_resid = d3(p, n)
    gap_me = M1.completion_gap(q_me, p, n)
    gap_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p, n)
    out = {"sigma": sigma, "seed": seed, "n": n, "N": "inf", "versions": versions(),
           "target_layout": [list(g) for g in layout], "target_theta": theta.tolist(),
           "z": z.tolist(),
           "D3": D3, "maxent_train_residual": me_resid,
           "hi_order_frac": hi_order_frac(p),
           "collision_ratio_target": M1.collision_ratio(p),
           "clifford_dist_median_target": M1.clifford_distance(theta)["clifford_dist_median"],
           "gap_maxent": gap_me["G"], "gap_uniform": gap_uni["G"],
           "per_level": {"maxent": gap_me["per_level"], "uniform": gap_uni["per_level"]},
           "fits_run": list(fits)}

    for name in fits:
        model = IQPModel(n, gens=masks) if name == "O" else IQPModel(n)
        r = fit_iqp(model, fhat, ops, seed, restarts.get(name, N_RESTARTS))
        out[f"{name}_best_residual"] = r["best_residual"]
        out[f"{name}_n_success_restarts"] = r["n_success_restarts"]
        out[f"{name}_success"] = r["success"]
        out[f"{name}_n_restarts"] = len(r["restart_residuals"])
        out[f"{name}_restart_residuals"] = r["restart_residuals"]
        out[f"{name}_restarts"] = r["restarts"]
        out[f"{name}_trace"] = r["trace"]
        out[f"{name}_n_params"] = r["n_params"]
        out[f"{name}_fit_seconds"] = r["seconds"]
        p_m = model.prob(r["fit"].params)
        gap = M1.completion_gap(p_m, p, n)
        out[f"{name}_gap"] = gap["G"]
        out["per_level"][name] = gap["per_level"]
        # R only when the fit succeeds (spec); otherwise the gap compares an underfit model.
        out[f"{name}_R"] = gap["G"] / gap_me["G"] if r["success"] else None
    out["total_seconds"] = time.time() - t_start
    return out


# ---------------- stub for a later step ----------------
def pauli_path_tv(theta, gens, max_weight):
    """Classical low-weight Pauli-path sampler proxy: TV between the IQP distribution and
    its Pauli-path truncation at max_weight. Hook for a later step; deliberately not
    implemented in step 2."""
    raise NotImplementedError("pauli_path_tv is a hook for a later step (spec: do not implement)")


# ---------------- CLI ----------------
def default_out(sigma: float, seed: int) -> Path:
    return ROOT / "results" / "step2" / f"sigma_{sigma:g}" / f"seed_{seed}"


def write(out: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / "metrics.json"
    f.write_text(json.dumps(out, indent=1))
    return f


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fits", default="O,G")
    ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    fits = tuple(x.strip() for x in a.fits.split(",") if x.strip())
    if any(f not in ("O", "G") for f in fits):
        ap.error("--fits takes O and/or G")

    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the sweep: BUDGET_OK does not exist (only the user creates it)")
        for sg in SIGMAS:
            for s in SEEDS:
                print(write(run_one(sg, s, fits=fits), default_out(sg, s)), flush=True)
        return

    if a.sigma is None:
        ap.error("--sigma is required unless --all")
    out = run_one(a.sigma, a.seed, fits=fits)
    f = write(out, Path(a.out) if a.out else default_out(a.sigma, a.seed))
    print(f)
    print(f"  D3 = {out['D3']:.3e}  hi_order_frac = {out['hi_order_frac']:.3e}  "
          f"collision = {out['collision_ratio_target']:.3f}  ({out['total_seconds']:.1f} s)")
    for name in fits:
        print(f"  {name}: best residual {out[f'{name}_best_residual']:.3e}  "
              f"success restarts {out[f'{name}_n_success_restarts']}/{out[f'{name}_n_restarts']}  "
              f"R = {out[f'{name}_R']}  ({out[f'{name}_fit_seconds']:.1f} s)")


if __name__ == "__main__":
    main()

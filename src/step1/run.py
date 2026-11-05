"""One config -> results/step1/<target>/N<N>/seed_<s>/metrics.json; --all runs the grid.

  python -m src.step1.run --target ising --N inf --seed 0 [--out DIR]
  python -m src.step1.run --all          (refuses to start without BUDGET_OK)

Every model in src/step1/models/ (any module with build(n)) is fitted to the same
order-<=3 parity moments. R = G(iqp) / G(maxent) by the spec; other models just get
their own G_<key>, per_level, tv_<key> and train_residual_<key> entries.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from . import metrics as M
from .bits import masks_up_to
from .models import discover
from .targets import KINDS, make_target, sample_indices
from .versions import versions
from .walsh import empirical_distribution, parity_coefficients

N_BITS = 12                      # guess (spec): small enough that everything is exact
GRID_N = (float("inf"), 1000, 10000, 100000)
GRID_SEEDS = (0, 1, 2, 3, 4)
ROOT = Path(__file__).resolve().parents[2]


def n_label(N: float) -> str:
    return "Ninf" if not np.isfinite(N) else f"N{int(N)}"


def default_out(target: str, N: float, seed: int) -> Path:
    return ROOT / "results" / "step1" / target / n_label(N) / f"seed_{seed}"


def run_one(target: str, N: float, seed: int, n: int = N_BITS) -> dict:
    t_start = time.time()
    p_true, meta = make_target(target, n, seed)
    ops = masks_up_to(n, 3)
    if np.isfinite(N):
        p_data = empirical_distribution(sample_indices(p_true, int(N), seed), n)
    else:
        p_data = p_true
    fhat = parity_coefficients(p_data)[ops]

    out = {"target": target, "N": "inf" if not np.isfinite(N) else int(N), "seed": seed, "n": n,
           "levels": list(M.LEVELS), "per_level": {}, "versions": versions(),
           "target_meta": meta, "collision_ratio_target": M.collision_ratio(p_true)}

    uni = M.completion_gap(np.full(2**n, 2.0**-n), p_true, n)
    out["G_uniform"], out["per_level"]["uniform"] = uni["G"], uni["per_level"]

    for model in discover(n):
        k = model.key
        t0 = time.time()
        fit = model.fit_moments(fhat, ops, seed=seed)
        out[f"fit_seconds_{k}"] = time.time() - t0
        p_m = model.prob(fit.params)
        gap = M.completion_gap(p_m, p_true, n)
        out[f"G_{k}"], out["per_level"][k] = gap["G"], gap["per_level"]
        out[f"tv_{k}"] = M.tv(p_m, p_true)
        out[f"train_residual_{k}"] = fit.train_residual
        out[f"n_params_{k}"] = int(model.n_params)
        out[f"restart_residuals_{k}"] = [float(x) for x in fit.restart_residuals]
        out[f"restarts_{k}"] = fit.restarts
        out[f"nit_{k}"] = fit.nit
        out[f"trace_{k}"] = [float(x) for x in fit.trace]
        prefix = "" if k == "iqp" else f"{k}_"
        if hasattr(model, "angles"):
            theta, weights = model.angles()
            for name, v in M.clifford_distance(theta, weights).items():
                out[prefix + name] = v
            out[prefix + "angles"] = [float(x) for x in theta]
        if hasattr(model, "moment_jacobian"):
            sv = np.linalg.svd(model.moment_jacobian(fit.params, ops), compute_uv=False)
            out[prefix + "jacobian_rank"] = int(np.sum(sv > 1e-8 * sv[0]))
            out[prefix + "jacobian_sv_max"] = float(sv[0])
            out[prefix + "jacobian_sv_min"] = float(sv[-1])

    out["R"] = out["G_iqp"] / out["G_maxent"]
    out["expected_sampling_residual"] = M.expected_sampling_residual(fhat, N)
    out["tau"] = M.gap_tau(fhat, N)
    out["gap_valid"] = M.gap_valid(out["train_residual_iqp"], out["train_residual_maxent"], out["tau"])
    out["total_seconds"] = time.time() - t_start
    return out


def write(out: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / "metrics.json"
    f.write_text(json.dumps(out, indent=1))
    return f


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=KINDS)
    ap.add_argument("--N", default="inf")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)

    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the grid: BUDGET_OK does not exist (only the user creates it)")
        for t in KINDS:
            for N in GRID_N:
                for s in GRID_SEEDS:
                    f = write(run_one(t, N, s), default_out(t, N, s))
                    print(f, flush=True)
        return

    if a.target is None:
        ap.error("--target is required unless --all")
    N = float("inf") if a.N.lower() == "inf" else int(a.N)
    out = run_one(a.target, N, a.seed)
    f = write(out, Path(a.out) if a.out else default_out(a.target, N, a.seed))
    print(f"{f}\n  R = {out['R']:.4g}  G_iqp = {out['G_iqp']:.3e}  G_maxent = {out['G_maxent']:.3e}  "
          f"G_uniform = {out['G_uniform']:.3e}\n  train_residual iqp = {out['train_residual_iqp']:.3e}  "
          f"maxent = {out['train_residual_maxent']:.3e}  gap_valid = {out['gap_valid']}  "
          f"jacobian_rank = {out.get('jacobian_rank')}  ({out['total_seconds']:.1f} s)")


if __name__ == "__main__":
    main()

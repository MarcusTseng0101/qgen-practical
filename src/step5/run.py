"""Step 5: where does the iqp4 advantage reverse, and why? (specs/step5_iqp4_sigma_scan.md)

Designed after step 4 (notes/2026-11-07_step4_findings.md).

  python -m src.step5.run --target iqp4 --sigma 0.2 --N inf --seed 0
  python -m src.step5.run --projection      (results/step5/PROJECTION.json from the timed pair)
  python -m src.step5.run --all             (refuses to start without BUDGET_OK)

Both targets go through ONE code path (fit_instance), which mirrors step 4's run_instance and
reuses its pieces by import: training_moments, noise_floor (src/step4/run), fit_restarts
(src/step3/run, G = generic 298-generator IQP, 3 restarts), MaxEntModel (ridge 1e-8),
completion_gap, d3. The reproduction check (iqp4 at sigma 0.1/0.2, N = inf vs results/step4)
therefore also validates the path used for iqp4f. src/step1..4 are never edited.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.versions import versions
from src.step2.sweep import d3, hi_order_frac
from src.step3.run import fit_restarts
from src.step4.run import G_RESTARTS, N_BITS, noise_floor, parse_N, training_moments
from src.step5.targets import TAU, iqp4_target, iqp4f_target

TARGETS = ("iqp4", "iqp4f")
SIGMAS = (0.1, 0.125, 0.15, 0.175, 0.2, 0.25)
NS = (None, 10000)                      # None = N = inf
SEEDS = (0, 1, 2, 3, 4)
ROOT = Path(__file__).resolve().parents[2]
STEP4_RESULTS = ROOT / "results" / "step4"


# ---------------- one instance ----------------
def target_p(target: str, sigma: float, seed: int, n: int = N_BITS):
    if target == "iqp4":
        return iqp4_target(sigma, seed, n)
    if target == "iqp4f":
        return iqp4f_target(sigma, seed, n)
    raise ValueError(target)


def fit_instance(target: str, sigma: float, N, seed: int, n: int = N_BITS,
                 g_restarts: int = G_RESTARTS) -> dict:
    """The step-4 instance recipe (src/step4/run.run_instance), for iqp4 and iqp4f."""
    t0 = time.time()
    p, masks, theta, _ = target_p(target, sigma, seed, n)
    fhat, ops = training_moments(p, N, seed, n)

    me = MaxEntModel(n, 3)
    me_fit = me.fit_moments(fhat, ops)
    G_me = M1.completion_gap(me.prob(me_fit.params), p, n)
    G_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p, n)
    r = fit_restarts(IQPModel(n), fhat, ops, seed, p, n, g_restarts)
    b = r["rows"][r["best"]]
    out = {"target": target, "sigma": sigma, "N": "inf" if N is None else int(N), "seed": seed,
           "n": n, "versions": versions(),
           "designed_after": "step 4 (notes/2026-11-07_step4_findings.md)",
           "training_input": "exact order-<=3 moments" if N is None else
                             f"order-<=3 moments of sample_indices(p, {int(N)}, {seed})",
           "G_iqp": b["G"], "G_maxent": G_me["G"], "G_uniform": G_uni["G"], "R": b["G"] / G_me["G"],
           "G_train_residual": b["residual"], "G_best_restart": r["best"],
           "G_restart_residuals": [x["residual"] for x in r["rows"]],
           "G_restart_G": [x["G"] for x in r["rows"]],
           "G_restart_nit": [x["nit"] for x in r["rows"]],
           "G_restart_message": [x["message"] for x in r["rows"]],
           "G_n_restarts": len(r["rows"]), "G_fit_seconds": r["seconds"],
           "G_best_params": [float(v) for v in b["params"]],
           "maxent_train_residual": me_fit.train_residual, "maxent_nit": me_fit.nit,
           "maxent_message": me_fit.message,
           "D3": d3(p, n)[0], "noise_floor": noise_floor(p, N, n),
           "hi_order_frac": hi_order_frac(p), "collision_ratio_target": M1.collision_ratio(p),
           "per_level": {"G": b["per_level"], "maxent": G_me["per_level"], "uniform": G_uni["per_level"]},
           "target_masks": [int(m) for m in masks], "target_theta": theta.tolist(),
           "clifford_dist_median_target": M1.clifford_distance(theta)["clifford_dist_median"]}
    if target == "iqp4f":
        out["tau"] = TAU
    out["total_seconds"] = time.time() - t0
    return out


# ---------------- crossing sigma* and the Q5 rule ----------------
def sign_changes(meds) -> int:
    above = [m >= 1 for m in meds]
    return int(sum(a != b for a, b in zip(above, above[1:])))


def sigma_star(sigmas, meds):
    """Spec section 2: scan sigma upward; first adjacent pair with median R >= 1 at sigma_i and
    < 1 at sigma_{i+1}; interpolate log R linearly in log sigma to log R = 0. None if no pair."""
    for (s0, r0), (s1, r1) in zip(zip(sigmas, meds), zip(sigmas[1:], meds[1:])):
        if r0 >= 1 and r1 < 1:
            l0, l1 = math.log(r0), math.log(r1)
            return math.exp(math.log(s0) + (0.0 - l0) * (math.log(s1) - math.log(s0)) / (l1 - l0))
    return None


AMEND1 = "specs/step5_amendment1.md"


def q5_verdict(star_inf, star_1e4, meds_1e4) -> dict:
    """Q5: sigma*(iqp4, N = 1e4) >= sigma*(iqp4, N = inf). Spec section 3 plus
    specs/step5_amendment1.md (approved before the grid ran), in this order:
      1. sigma*(N = inf) undefined -> FAIL, whatever sigma*(1e4) is (amendment 1, case 1);
      2. sigma*(1e4) undefined, R >= 1 everywhere at 1e4 -> PASS (spec);
      3. sigma*(1e4) undefined, R < 1 everywhere at 1e4 -> FAIL (spec);
      4. sigma*(1e4) undefined, median R - 1 changes sign on the grid -> FAIL (amendment 1, case 2);
      5. both defined -> PASS iff sigma*(1e4) >= sigma*(inf) (spec)."""
    if star_inf is None:
        return {"PASS": False, "rule": f"{AMEND1}, case 1",
                "reason": "sigma*(N = inf) undefined: no reference for the comparison"}
    if star_1e4 is None:
        if all(m >= 1 for m in meds_1e4):
            return {"PASS": True, "rule": "spec section 3", "reason": "sigma*(1e4) undefined: R >= 1 everywhere"}
        if all(m < 1 for m in meds_1e4):
            return {"PASS": False, "rule": "spec section 3", "reason": "sigma*(1e4) undefined: R < 1 everywhere"}
        return {"PASS": False, "rule": f"{AMEND1}, case 2",
                "reason": "sigma*(1e4) undefined but median R - 1 changes sign on the grid"}
    return {"PASS": star_1e4 >= star_inf, "rule": "spec section 3",
            "reason": f"sigma*(1e4) = {star_1e4:.4g} vs sigma*(inf) = {star_inf:.4g}"}


# ---------------- CLI / IO ----------------
def default_out(target: str, sigma: float, N, seed: int) -> Path:
    return (ROOT / "results" / "step5" / target / f"sigma_{sigma:g}" /
            f"N_{'inf' if N is None else int(N)}" / f"seed_{seed}")


def write(out: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / "metrics.json"
    f.write_text(json.dumps(out, indent=1))
    return f


def grid():
    for t in TARGETS:
        for N in NS:
            for sg in SIGMAS:
                for s in SEEDS:
                    yield t, sg, N, s


TIMED = {"iqp4": ("iqp4", 0.25, 10000, 0), "iqp4f": ("iqp4f", 0.25, 10000, 0)}
BUDGET_HOURS = 1.0


def projection() -> dict:
    per, sec = {}, {}
    for t, (tt, sg, N, s) in TIMED.items():
        d = json.loads((default_out(tt, sg, N, s) / "metrics.json").read_text())
        per[f"{tt}/sigma_{sg:g}/N_{N}/seed_{s}"] = {"total_seconds": d["total_seconds"],
                                                    "G_fit_seconds": d["G_fit_seconds"],
                                                    "G_train_residual": d["G_train_residual"]}
        sec[t] = d["total_seconds"]
    count = {t: sum(1 for c in grid() if c[0] == t) for t in TARGETS}
    hours = sum(count[t] * sec[t] for t in TARGETS) / 3600.0
    out = {"projected_hours": hours, "instances": sum(count.values()),
           "basis": "spec section 6: per-target time of the timed instance (sigma = 0.25, N = 1e4, "
                    "seed 0) x its 60 instances",
           "seconds_by_target": sec, "instances_by_target": count, "per_instance": per,
           "budget_hours": BUDGET_HOURS, "over_budget": hours > BUDGET_HOURS,
           "note": "one timed instance per target; N = inf and smaller sigma may be slower or faster. "
                   "Steps 3-4 ran 1.4x-2x slower than projected on a shared machine.",
           "projected_hours_x2_shared_machine": 2 * hours}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--N", type=parse_N, default=None, help="10000 or inf")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--projection", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
    if a.projection:
        pr = projection()
        f = ROOT / "results" / "step5" / "PROJECTION.json"
        f.write_text(json.dumps(pr, indent=1))
        print(f)
        print(json.dumps(pr, indent=1))
        return
    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the grid: BUDGET_OK does not exist (only the user creates it)")
        for t, sg, N, s in grid():
            print(write(fit_instance(t, sg, N, s), default_out(t, sg, N, s)), flush=True)
        return
    if a.target is None or a.sigma is None:
        ap.error("--target and --sigma are required")
    out = fit_instance(a.target, a.sigma, a.N, a.seed)
    f = write(out, Path(a.out) if a.out else default_out(a.target, a.sigma, a.N, a.seed))
    print(f)
    print(f"  total {out['total_seconds']:.1f} s  G fit {out['G_fit_seconds']:.1f} s  "
          f"G residual {out['G_train_residual']:.3e}  restarts "
          f"{['%.2e' % x for x in out['G_restart_residuals']]}  maxent residual "
          f"{out['maxent_train_residual']:.2e} (nit {out['maxent_nit']})")


if __name__ == "__main__":
    main()

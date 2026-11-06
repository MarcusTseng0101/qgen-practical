"""Step 4: does R_G < 1 survive misspecification and finite N?

specs/step4_misspec_finite_n.md (designed after step 3, notes/2026-11-06_step3_findings.md).

  python -m src.step4.run --calibrate                       (original delta rule; D3 only)
  python -m src.step4.run --calibrate-amend1                (amendment 1: K x delta; D3 only)
  python -m src.step4.run --target iqp4 --sigma 0.2 --N 10000 --seed 0
  python -m src.step4.run --target mix --N inf --seed 0
  python -m src.step4.run --all        (refuses to start without the budget-approval file)

Targets: iqp, iqp4, mix, maxent_proj (src/step4/targets.py; iqp from src/step2, maxent_proj
from src/step3.make_pair). Training input: the order-<=3 parity moments of the target, exact
at N = inf, else of the empirical distribution of src/step1/targets.sample_indices(p, N, seed).
Both models see the same vector. Fits: G = the generic 298-generator IQP, 3 restarts (as in
step 3; src/step3.run.fit_restarts), and MaxEnt(3) with step 1's frozen ridge. R = G_iqp /
G_maxent at G's lowest-training-residual restart, both against the exact target.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.versions import versions
from src.step1.walsh import empirical_distribution, parity_coefficients
from src.step2.sweep import d3, hi_order_frac, sigma_target
from src.step3.run import fit_restarts, make_pair
from src.step4.targets import DELTAS, DELTAS_AMEND1, KS_AMEND1, iqp4_target, mix_target

N_BITS = 12
TARGETS = ("iqp", "iqp4", "mix", "maxent_proj")
SIGMAS = (0.1, 0.2)
NS = (1000, 10000, 100000, None)        # None = N = inf
SEEDS = (0, 1, 2, 3, 4)
G_RESTARTS = 3                          # spec: as in step 3; never fewer
ROOT = Path(__file__).resolve().parents[2]
CALIB_SIGMA = 0.2                       # spec: match mix's median D3 to iqp at sigma = 0.2


# ---------------- targets and training input ----------------
def target_p(target: str, sigma, seed: int, delta=None, n: int = N_BITS) -> dict:
    """{'p': exact target, plus target-specific info}."""
    if target == "iqp":
        p, masks, theta, _, _ = sigma_target(sigma, seed, n)
        return {"p": p, "masks": masks, "theta": theta}
    if target == "iqp4":
        p, masks, theta, _ = iqp4_target(sigma, seed, n)
        return {"p": p, "masks": masks, "theta": theta}
    if target == "mix":   # amendment 1: (K, delta) from calibration_amend1.json
        K, dl = chosen_mix_params()
        if delta is not None:
            dl = delta
        return {"p": mix_target(seed, dl, n, K), "delta": dl, "K": K}
    if target == "maxent_proj":
        pair = make_pair(sigma, seed, n)
        return {"p": pair["p"]["maxent_proj"], "paired_iqp_D3": pair["D3"],
                "pair_moment_max_abs": pair["pair_moment_max_abs"]}
    raise ValueError(target)


def training_moments(p: np.ndarray, N, seed: int, n: int = N_BITS):
    """(fhat over masks_up_to(n, 3), ops). Exact at N = None, else from sample_indices(p, N, seed)."""
    ops = masks_up_to(n, 3)
    if N is None:
        return parity_coefficients(p)[ops], ops
    q = empirical_distribution(sample_indices(p, N, seed), n)
    return parity_coefficients(q)[ops], ops


def noise_floor(p: np.ndarray, N, n: int = N_BITS) -> float:
    """Mean over the order-1..3 parities of (1 - f_a^2) / N (0 at N = inf)."""
    if N is None:
        return 0.0
    f = parity_coefficients(p)[masks_up_to(n, 3)]
    return float(np.mean((1.0 - f**2) / N))


# ---------------- delta calibration (D3 only; no fits of G, no R) ----------------
CALIB_FILE = ROOT / "results" / "step4" / "calibration.json"


def calibrate(n: int = N_BITS) -> dict:
    ref = [d3(sigma_target(CALIB_SIGMA, s, n)[0], n)[0] for s in SEEDS]
    ref_med = float(np.median(ref))
    by = {}
    for dl in DELTAS:
        by[dl] = [d3(mix_target(s, dl, n), n)[0] for s in SEEDS]
    med = {dl: float(np.median(v)) for dl, v in by.items()}
    chosen = min(DELTAS, key=lambda dl: abs(med[dl] - ref_med))
    return {"chosen_delta": chosen,
            "D3_by_delta": {f"{dl:g}": med[dl] for dl in DELTAS},
            "D3_by_delta_per_seed": {f"{dl:g}": by[dl] for dl in DELTAS},
            "iqp_sigma_0.2_D3_median": ref_med, "iqp_sigma_0.2_D3_per_seed": ref,
            "rule": "delta in {0.2,0.4,0.6,0.8} whose median D3 of mix over seeds 0-4 is closest "
                    "(absolute difference) to the median D3 of iqp at sigma = 0.2",
            "D3_definition": "KL(p || MaxEnt3(p)), src/step2/sweep.d3 (MaxEnt(3) with step 1's ridge)",
            "seeds": list(SEEDS), "versions": versions()}


def chosen_delta() -> float:
    """The ORIGINAL rule's delta (calibration.json); superseded for the grid by amendment 1."""
    if not CALIB_FILE.exists():
        raise RuntimeError("run the delta calibration first (results/step4/calibration.json)")
    return float(json.loads(CALIB_FILE.read_text())["chosen_delta"])


# ---------------- amendment 1 calibration: K x delta (D3 only; no fits of G, no R) ----------------
# specs/step4_amendment1.md, section 2.1. calibration.json stays as the record of the original rule.
CALIB_AMEND1_FILE = ROOT / "results" / "step4" / "calibration_amend1.json"
STEP3_TABLE = ROOT / "results" / "step3" / "table.csv"
REF_SIGMA_AMEND1 = 0.1


def reference_D3_amend1() -> tuple:
    """Median D3 of iqp at sigma = 0.1 over seeds 0-4, from the step-3 table (as the amendment says)."""
    lines = STEP3_TABLE.read_text().strip().splitlines()
    cols = lines[0].split(",")
    rows = [dict(zip(cols, l.split(","))) for l in lines[1:]]
    v = [float(r["D3"]) for r in rows if r["target"] == "iqp" and float(r["sigma"]) == REF_SIGMA_AMEND1]
    assert len(v) == len(SEEDS), v
    return float(np.median(v)), v


def calibrate_amend1(n: int = N_BITS) -> dict:
    ref, ref_per = reference_D3_amend1()
    per, med = {}, {}
    for K in KS_AMEND1:
        per[f"{K}"], med[f"{K}"] = {}, {}
        for dl in DELTAS_AMEND1:
            v = [d3(mix_target(s, dl, n, K), n)[0] for s in SEEDS]
            per[f"{K}"][f"{dl:g}"] = v
            med[f"{K}"][f"{dl:g}"] = float(np.median(v))
    K, dl = min(((K, dl) for K in KS_AMEND1 for dl in DELTAS_AMEND1),
                key=lambda c: abs(np.log(med[f"{c[0]}"][f"{c[1]:g}"]) - np.log(ref)))
    return {"chosen_K": K, "chosen_delta": dl, "D3_by_K_delta": med, "D3_by_K_delta_per_seed": per,
            "reference_D3": ref, "reference_D3_per_seed": ref_per,
            "reference_source": "median D3 of iqp at sigma = 0.1, seeds 0-4, results/step3/table.csv",
            "rule": "(K, delta) in {3,6,12,24,48} x {0.8,0.9,0.99} whose median D3 of mix over seeds "
                    "0-4 is closest to reference_D3 on a log scale (specs/step4_amendment1.md)",
            "D3_definition": "KL(p || MaxEnt3(p)), src/step2/sweep.d3 (MaxEnt(3) with step 1's ridge)",
            "seeds": list(SEEDS), "versions": versions()}


def chosen_mix_params() -> tuple:
    """(K, delta) for the grid's mix, from calibration_amend1.json."""
    if not CALIB_AMEND1_FILE.exists():
        raise RuntimeError("run the amendment-1 calibration first (results/step4/calibration_amend1.json)")
    c = json.loads(CALIB_AMEND1_FILE.read_text())
    return int(c["chosen_K"]), float(c["chosen_delta"])


# ---------------- one instance ----------------
def run_instance(target: str, sigma, N, seed: int, n: int = N_BITS, delta=None,
                 g_restarts: int = G_RESTARTS) -> dict:
    t0 = time.time()
    if target == "mix":
        sigma = None
    tp = target_p(target, sigma, seed, delta, n)
    p = tp["p"]
    fhat, ops = training_moments(p, N, seed, n)

    me = MaxEntModel(n, 3)
    me_fit = me.fit_moments(fhat, ops)
    G_me = M1.completion_gap(me.prob(me_fit.params), p, n)
    G_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p, n)
    r = fit_restarts(IQPModel(n), fhat, ops, seed, p, n, g_restarts)
    b = r["rows"][r["best"]]
    out = {"target": target, "sigma": sigma, "N": "inf" if N is None else int(N), "seed": seed,
           "n": n, "versions": versions(),
           "designed_after": "step 3 (notes/2026-11-06_step3_findings.md)",
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
           "per_level": {"G": b["per_level"], "maxent": G_me["per_level"], "uniform": G_uni["per_level"]}}
    if target == "mix":
        out["delta"] = tp["delta"]
        out["mix_K"] = tp["K"]
        out["mix_params_source"] = "results/step4/calibration_amend1.json (specs/step4_amendment1.md)"
    if target == "maxent_proj":
        out["paired_iqp_D3"] = tp["paired_iqp_D3"]
        out["pair_moment_max_abs"] = tp["pair_moment_max_abs"]
    if "theta" in tp:
        out["target_masks"] = [int(m) for m in tp["masks"]]
        out["target_theta"] = tp["theta"].tolist()
        out["clifford_dist_median_target"] = M1.clifford_distance(tp["theta"])["clifford_dist_median"]
    out["total_seconds"] = time.time() - t0
    return out


# ---------------- budget projection (build order item 3) ----------------
TIMED = (("iqp4", 0.2, 10000, 0), ("mix", None, 10000, 0))
STEP3_SLOWDOWN = 118.0 / (1.38 * 60)    # step 3: 118 min actual vs 1.38 h projected (~1.4x)


def projection() -> dict:
    per = {}
    for t, sg, N, s in TIMED:
        d = json.loads((default_out(t, sg, N, s) / "metrics.json").read_text())
        per[f"{t}/{'none' if sg is None else f'sigma_{sg:g}'}/N_{N}/seed_{s}"] = {
            "total_seconds": d["total_seconds"], "G_fit_seconds": d["G_fit_seconds"],
            "G_train_residual": d["G_train_residual"]}
    slow = max(v["total_seconds"] for v in per.values())
    n_inst = sum(1 for _ in grid())
    out = {"projected_hours": n_inst * slow / 3600.0, "instances": n_inst,
           "basis": "spec rule: the slower of the two timed instances (iqp4 sigma=0.2 N=1e4 seed 0; "
                    "mix amend-1 parameters N=1e4 seed 0) x 140",
           "slowest_instance_seconds": slow, "per_instance": per,
           "step3_underestimate": f"step 3 ran {STEP3_SLOWDOWN:.2f}x slower than its projection "
                                  "(118 min actual vs 1.38 h projected)",
           "projected_hours_x_step3_slowdown": n_inst * slow / 3600.0 * STEP3_SLOWDOWN}
    # Not the spec's basis (a caution): the two timed instances are fast (moments with a high
    # residual floor). In step 3 the same G (3 restarts) on iqp / maxent_proj at sigma = 0.1-0.2,
    # N = inf, took ~145 s per instance (median total, results/step3/table.csv). If the 80
    # iqp / maxent_proj instances cost that and the other 60 cost the slower timed instance:
    s3 = STEP3_TABLE.read_text().strip().splitlines()
    cols = s3[0].split(",")
    rows = [dict(zip(cols, l.split(","))) for l in s3[1:]]
    t3 = [float(r["total_seconds"]) for r in rows if float(r["sigma"]) in SIGMAS]
    med3 = float(np.median(t3))
    n_like3 = sum(1 for t, *_ in grid() if t in ("iqp", "maxent_proj"))
    out["caution_step3_based_hours"] = (n_like3 * med3 + (n_inst - n_like3) * slow) / 3600.0
    out["caution_basis"] = (f"{n_like3} iqp/maxent_proj instances x {med3:.0f} s (median step-3 instance "
                            f"time at sigma 0.1/0.2, which also includes 10 O restarts) + the rest x {slow:.1f} s; "
                            "untimed in step 4, an assumption")
    return out


# ---------------- CLI ----------------
def default_out(target: str, sigma, N, seed: int) -> Path:
    cell = "none" if target == "mix" else f"sigma_{sigma:g}"
    return ROOT / "results" / "step4" / target / cell / f"N_{'inf' if N is None else int(N)}" / f"seed_{seed}"


def write(out: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / "metrics.json"
    f.write_text(json.dumps(out, indent=1))
    return f


def grid():
    for t in TARGETS:
        for sg in ((None,) if t == "mix" else SIGMAS):
            for N in NS:
                for s in SEEDS:
                    yield t, sg, N, s


def parse_N(x: str):
    return None if x.lower() in ("inf", "none") else int(float(x))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--N", type=parse_N, default=None, help="1000, 10000, 100000 or inf")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--calibrate", action="store_true", help="original delta rule (calibration.json)")
    ap.add_argument("--calibrate-amend1", action="store_true", help="K x delta (calibration_amend1.json)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--projection", action="store_true", help="results/step4/PROJECTION.json from the timed pair")
    a = ap.parse_args(argv)

    if a.calibrate_amend1:
        c = calibrate_amend1()
        CALIB_AMEND1_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIB_AMEND1_FILE.write_text(json.dumps(c, indent=1))
        print(CALIB_AMEND1_FILE)
        print(json.dumps({k: c[k] for k in ("chosen_K", "chosen_delta", "reference_D3", "D3_by_K_delta")}, indent=1))
        return
    if a.projection:
        pr = projection()
        f = ROOT / "results" / "step4" / "PROJECTION.json"
        f.write_text(json.dumps(pr, indent=1))
        print(f)
        print(json.dumps(pr, indent=1))
        return
    if a.calibrate:
        c = calibrate()
        CALIB_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIB_FILE.write_text(json.dumps(c, indent=1))
        print(CALIB_FILE)
        print(json.dumps({k: c[k] for k in ("chosen_delta", "D3_by_delta", "iqp_sigma_0.2_D3_median")}, indent=1))
        return
    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the grid: the budget-approval file does not exist (only the user creates it)")
        for t, sg, N, s in grid():
            print(write(run_instance(t, sg, N, s), default_out(t, sg, N, s)), flush=True)
        return
    if a.target is None or (a.target != "mix" and a.sigma is None):
        ap.error("--target (and --sigma unless mix) are required")
    out = run_instance(a.target, a.sigma, a.N, a.seed)
    f = write(out, Path(a.out) if a.out else default_out(a.target, a.sigma, a.N, a.seed))
    print(f)
    print(f"  R = {out['R']:.4g}  G_iqp = {out['G_iqp']:.3e}  G_maxent = {out['G_maxent']:.3e}  "
          f"G residual = {out['G_train_residual']:.3e}  noise floor = {out['noise_floor']:.2e}  "
          f"({out['total_seconds']:.1f} s)")


if __name__ == "__main__":
    main()

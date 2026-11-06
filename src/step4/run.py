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
# One timed instance per target (user decision A, 2026-11-06): iqp4 and mix as the spec says,
# plus iqp and maxent_proj, each by the production run_instance.
TIMED = {"iqp4": ("iqp4", 0.2, 10000, 0), "mix": ("mix", None, 10000, 0),
         "iqp": ("iqp", 0.1, None, 0), "maxent_proj": ("maxent_proj", 0.1, 10000, 0)}
SPEC_RULE_TIMED = ("iqp4", "mix")
STEP3_SLOWDOWN = 118.0 / (1.38 * 60)    # step 3: 118 min actual vs 1.38 h projected (~1.4x)
STEP3_CUTS = ("drop N = 1e3", "drop sigma = 0.1")


def _cell(t, sg, N, s):
    return f"{t}/{'none' if sg is None else f'sigma_{sg:g}'}/N_{'inf' if N is None else N}/seed_{s}"


def projection() -> dict:
    per, sec = {}, {}
    for t, (tt, sg, N, s) in TIMED.items():
        d = json.loads((default_out(tt, sg, N, s) / "metrics.json").read_text())
        per[_cell(tt, sg, N, s)] = {"total_seconds": d["total_seconds"], "G_fit_seconds": d["G_fit_seconds"],
                                    "G_train_residual": d["G_train_residual"]}
        sec[t] = d["total_seconds"]
    cells = list(grid())
    count = {t: sum(1 for c in cells if c[0] == t) for t in TARGETS}
    hours = sum(count[t] * sec[t] for t in TARGETS) / 3600.0
    slow = max(sec[t] for t in SPEC_RULE_TIMED)
    out = {"projected_hours": hours, "instances": len(cells),
           "basis": "per target: its own timed instance's total_seconds x its instance count "
                    "(user decision A, 2026-11-06)",
           "seconds_by_target": sec, "instances_by_target": count,
           "hours_by_target": {t: count[t] * sec[t] / 3600.0 for t in TARGETS},
           "per_instance": per,
           "projected_hours_spec_rule": len(cells) * slow / 3600.0,
           "spec_rule_basis": "the slower of iqp4 (sigma=0.2, N=1e4) and mix (N=1e4), x 140",
           "step3_underestimate": f"step 3 ran {STEP3_SLOWDOWN:.2f}x slower than its projection "
                                  "(118 min actual vs 1.38 h projected)",
           "projected_hours_x_step3_slowdown": hours * STEP3_SLOWDOWN,
           "note": "one seed per target, one (sigma, N) per target; fit times vary with sigma and N. "
                   "The step-3 grid's per-instance times are not used: the identical iqp sigma=0.1 seed-0 "
                   "G fit took 193 s there and 23.5 s here (same residuals)."}
    # what the spec's cut order would leave (reported, not applied)
    after = []
    keep = cells
    for name in STEP3_CUTS:
        keep = [c for c in keep if not (c[2] == 1000 if "1e3" in name else c[1] == 0.1)]
        after.append({"cut": name, "instances": len(keep),
                      "hours": sum(sec[c[0]] for c in keep) / 3600.0})
    out["if_cut_in_spec_order"] = after
    return out


# ---------------- report (build order item 4) ----------------
N_PLOT_INF = 1e6        # where N = inf is drawn (right edge), labelled "inf"
FLOOR = 1e-30


def cell_key(t, sg):
    return "mix" if t == "mix" else f"{t}/sigma_{sg:g}"


def load_grid() -> dict:
    out = {}
    for t, sg, N, s in grid():
        f = default_out(t, sg, N, s) / "metrics.json"
        if f.exists():
            out[(t, sg, N, s)] = json.loads(f.read_text())
    return out


def iqr(x):
    q1, med, q3 = np.percentile(np.asarray(x, dtype=np.float64), [25, 50, 75])
    return float(q1), float(med), float(q3)


def verdict_at(x) -> str:
    """Spec Statistics: "<1" = IQR entirely below 1; ">=1" = entirely at or above 1."""
    q1, _, q3 = iqr(x)
    return "<1" if q3 < 1 else (">=1" if q1 >= 1 else "undecided")


def cells():
    for t in TARGETS:
        for sg in ((None,) if t == "mix" else SIGMAS):
            yield t, sg


def stats(grid_: dict) -> dict:
    st = {}
    for t, sg in cells():
        for N in NS:
            ds = [grid_[(t, sg, N, s)] for s in SEEDS if (t, sg, N, s) in grid_]
            if not ds:
                continue
            k = f"{cell_key(t, sg)}/N_{'inf' if N is None else N}"
            R = [d["R"] for d in ds]
            st[k] = {"n": len(ds), "R": R, "R_iqr": iqr(R), "R_verdict": verdict_at(R),
                     "G_train_residual": [d["G_train_residual"] for d in ds],
                     "G_train_residual_iqr": iqr([d["G_train_residual"] for d in ds]),
                     "G_iqp_iqr": iqr([d["G_iqp"] for d in ds]),
                     "G_maxent_iqr": iqr([d["G_maxent"] for d in ds]),
                     "maxent_train_residual_iqr": iqr([d["maxent_train_residual"] for d in ds]),
                     "maxent_nit_max": max(d["maxent_nit"] for d in ds),
                     "maxent_messages": sorted({d["maxent_message"] for d in ds}),
                     "noise_floor_iqr": iqr([d["noise_floor"] for d in ds]),
                     "D3_iqr": iqr([d["D3"] for d in ds])}
    return st


def verdicts(st: dict) -> dict:
    v = {}
    k = [f"maxent_proj/sigma_{sg:g}/N_{N}" for sg in SIGMAS for N in NS if N is not None]
    v["K"] = {"PASS": all(st[x]["R_verdict"] != "<1" for x in k), "cells": {x: st[x]["R_verdict"] for x in k}}
    r1 = [f"iqp/sigma_{sg:g}/N_inf" for sg in SIGMAS]
    v["R1"] = {"PASS": all(st[x]["R_verdict"] == "<1" for x in r1), "cells": {x: st[x]["R_verdict"] for x in r1}}
    v["P1"] = {"PASS": st["iqp4/sigma_0.2/N_inf"]["R_verdict"] == "<1"}
    v["P2"] = {"PASS": st["mix/N_inf"]["R_verdict"] != "<1"}
    v["F1"] = {"PASS": st["iqp/sigma_0.2/N_100000"]["R_verdict"] == "<1"
                       and st["iqp/sigma_0.2/N_1000"]["R_verdict"] != "<1"}
    v["F2"] = {"PASS": st["iqp4/sigma_0.2/N_100000"]["R_verdict"] == "<1"}
    return v


def write_table(grid_: dict, path: Path):
    cols = ["target", "sigma", "N", "seed", "R", "G_iqp", "G_maxent", "G_uniform", "G_train_residual",
            "G_best_restart", "G_n_restarts", "maxent_train_residual", "maxent_nit", "noise_floor", "D3",
            "hi_order_frac", "collision_ratio_target", "clifford_dist_median_target", "mix_K", "delta",
            "total_seconds"]
    lines = [",".join(cols)]
    for key in grid():
        if key in grid_:
            d = grid_[key]
            lines.append(",".join("" if d.get(c) is None else str(d.get(c)) for c in cols))
    path.write_text("\n".join(lines) + "\n")


def make_figures(grid_: dict, st: dict, fig_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
    fig_dir.mkdir(parents=True, exist_ok=True)
    xs = [1e3, 1e4, 1e5, N_PLOT_INF]
    xlab = ["1e3", "1e4", "1e5", "∞"]
    style = {"iqp": ("o", "-", "k"), "iqp4": ("s", "--", "0.3"), "maxent_proj": ("^", ":", "k"),
             "mix": ("D", "-.", "0.45")}

    def nax(ax):
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(FixedLocator(xs))
        ax.xaxis.set_major_formatter(FixedFormatter(xlab))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xlabel("N (samples)")

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(fig_dir / f"{name}.png", dpi=150)
        fig.savefig(fig_dir / f"{name}.pdf")
        plt.close(fig)

    def series(t, sg, key):
        return np.array([st[f"{cell_key(t, sg)}/N_{'inf' if N is None else N}"][key] for N in NS])

    # 1. ratio_vs_N
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
    for ax, sg in zip(axs, SIGMAS):
        for t in ("iqp", "iqp4", "maxent_proj", "mix"):
            mk, ls, c = style[t]
            q = series(t, None if t == "mix" else sg, "R_iqr")
            lab = "mix (K=48, δ=0.99; no σ)" if t == "mix" else t
            ax.plot(xs, q[:, 1], marker=mk, ls=ls, color=c, label=lab)
            ax.fill_between(xs, q[:, 0], q[:, 2], color=c, alpha=0.15, lw=0)
        ax.axhline(1.0, color="k", lw=0.8)
        ax.set_yscale("log"); nax(ax)
        ax.set_title(f"σ = {sg:g} (median R, IQR band; 5 seeds)", fontsize=9)
    axs[0].set_ylabel("R = G_iqp / G_maxent3")
    axs[0].legend(fontsize=8)
    save(fig, "ratio_vs_N")

    # 2. ratio_at_inf
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    labels, markers = [], ["o", "s", "^", "v", "D", "P", "X"]
    for i, (t, sg) in enumerate(cells()):
        key = f"{cell_key(t, sg)}/N_inf"
        R = st[key]["R"]
        ax.scatter(np.full(len(R), i) + np.linspace(-0.15, 0.15, len(R)), R, marker=markers[i],
                   edgecolors="k", facecolors="none" if i % 2 else "k", s=30)
        ax.plot([i - 0.25, i + 0.25], [st[key]["R_iqr"][1]] * 2, color="0.4", lw=2)
        labels.append(cell_key(t, sg).replace("/sigma_", "\nσ=") + ("\nK=48, δ=0.99" if t == "mix" else ""))
    ax.axhline(1.0, color="k", lw=0.8)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=8)
    ax.set_yscale("log"); ax.set_ylabel("R per seed at N = ∞ (bar = median)")
    ax.set_title("R at N = ∞ (maxent_proj at N = ∞ is vacuous by construction, step 3)", fontsize=9)
    save(fig, "ratio_at_inf")

    # 3. noise_floor
    fig, axs = plt.subplots(2, 4, figsize=(13, 6.2))
    for ax, (t, sg) in zip(axs.flat, list(cells())):
        gi, gm, nf = series(t, sg, "G_iqp_iqr"), series(t, sg, "G_maxent_iqr"), series(t, sg, "noise_floor_iqr")
        ax.plot(xs, np.maximum(gi[:, 1], FLOOR), marker="o", ls="-", color="k", label="G_iqp")
        ax.plot(xs, np.maximum(gm[:, 1], FLOOR), marker="s", ls="--", color="0.4", label="G_maxent3")
        ax.plot(xs[:3], nf[:3, 1], marker="x", ls=":", color="k", label="noise floor (orders 1-3)")
        ax.set_yscale("log"); nax(ax)
        ax.set_title(cell_key(t, sg) + (" (K=48, δ=0.99)" if t == "mix" else ""), fontsize=9)
    axs.flat[-1].axis("off")
    axs.flat[0].legend(fontsize=7)
    for ax in axs[:, 0]:
        ax.set_ylabel("median over 5 seeds")
    save(fig, "noise_floor")


def report():
    g = load_grid()
    write_table(g, ROOT / "results" / "step4" / "table.csv")
    st = stats(g)
    v = verdicts(st)
    out = {"n_instances": len(g), "verdicts": v, "stats": st}
    (ROOT / "results" / "step4" / "verdicts.json").write_text(json.dumps(out, indent=1))
    make_figures(g, st, ROOT / "figures" / "step4")
    print(json.dumps(v, indent=1))


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
    ap.add_argument("--report", action="store_true", help="table.csv, verdicts.json, figures/step4/*")
    a = ap.parse_args(argv)

    if a.calibrate_amend1:
        c = calibrate_amend1()
        CALIB_AMEND1_FILE.parent.mkdir(parents=True, exist_ok=True)
        CALIB_AMEND1_FILE.write_text(json.dumps(c, indent=1))
        print(CALIB_AMEND1_FILE)
        print(json.dumps({k: c[k] for k in ("chosen_K", "chosen_delta", "reference_D3", "D3_by_K_delta")}, indent=1))
        return
    if a.report:
        report()
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

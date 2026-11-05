"""Step 3: completion ratio R as a function of the angle scale sigma.

specs/step3_completion_vs_sigma.md (designed after the step 1-2 diagnostics).

  python -m src.step3.run --target iqp --sigma 0.05 --seed 0 [--fits O,G] [--out DIR]
  python -m src.step3.run --all          (refuses to start without BUDGET_OK)
  python -m src.step3.run --report       (table.csv, verdicts.json, figures/step3/*)

Targets (n = 12, N = inf):
- iqp(sigma, s): the step-2 construction (step-1 biased layout, z reused across sigma),
  imported from src/step2/sweep.py.
- maxent_proj(sigma, s): MaxEnt3 of iqp(sigma, s), via step 1's unregularized projection
  (src/step1/targets.maxent_projection), polished by Newton steps on the same convex dual
  (refine_projection), so its order-<=3 moments equal iqp's to max |error| < 1e-10.

Training input. The pair shares ONE training vector: the exact order-<=3 moments of
iqp(sigma, s). maxent_proj's own moments agree with it to <= 1e-10 (tested, and recorded
here as pair_moment_*); sharing the vector makes "identical inputs on the pair" exact, so
the fits are bit-identical and only the truth above order 3 differs.

Fits, each with 10 restarts from N(0, 0.05^2) and step 1's L-BFGS-B settings:
- O: the IQP on the iqp(sigma, s) layout (also for maxent_proj). An oracle by design: a
  landscape diagnostic, not a method.
- G: step 1's generic 298-generator IQP.
- MaxEnt(3): step 1's MaxEntModel.
There is no exact-recovery gate (spec): R = G_iqp / G_maxent at the LOWEST-TRAINING-
RESIDUAL restart, always, with the training residual reported next to it.

Per-restart G values require each restart's parameters, but fit_moments keeps only the
best. So the restarts are replayed with exactly fit_moments' generic-path init draws
(default_rng(seed), one N(0, 0.05^2) vector per restart), each optimized by the production
fit_moments(..., n_restarts=1, theta0=init). src/step1 and src/step2 are imported, never
edited.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.bits import masks_up_to, parity_matrix
from src.step1.models.iqp import INIT_STD, N_RESTARTS, IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import maxent_projection
from src.step1.versions import versions
from src.step1.walsh import parity_coefficients
from src.step2.sweep import hi_order_frac, kl, sigma_target

N_BITS = 12
TARGETS = ("iqp", "maxent_proj")
SIGMAS = (0.05, 0.1, 0.2, 0.3, 0.4, 0.6)
SEEDS = (0, 1, 2, 3, 4)
ROOT = Path(__file__).resolve().parents[2]
# Budget cut (1) of the spec ("G restarts 10 -> 3"), chosen by the user on 2026-11-06 after the
# projection (1.53 h on the spec's sigma = 0.4 basis, 2.72 h with the measured sigma = 0.05
# time). Applies to the --all grid only. The 3 restarts are the first 3 of the 10 init draws.
ALL_GRID_RESTARTS = {"G": 3}


# ---------------- targets ----------------
NEWTON_STEPS = 20       # guess: max Newton steps polishing the projection (quadratic convergence)
NEWTON_TOL = 1e-14      # guess: stop when max |moment error| is below this


def refine_projection(lam: np.ndarray, f: np.ndarray, F: np.ndarray):
    """Newton steps on the convex MaxEnt dual log Z(lam) - lam.f, starting from step 1's
    L-BFGS-B solution. step 1's projection meets its 1e-10 tolerance as a SUM of squared
    moment errors; these steps also bring the max |error| below 1e-10. Returns (q, lam, steps)."""
    from scipy.special import logsumexp
    for k in range(NEWTON_STEPS + 1):
        e = F @ lam
        q = np.exp(e - logsumexp(e))
        g = F.T @ q
        err = g - f
        if np.max(np.abs(err)) < NEWTON_TOL or k == NEWTON_STEPS:
            return q, lam, k
        H = F.T @ (q[:, None] * F) - np.outer(g, g)
        lam = lam - np.linalg.solve(H, err)


def make_pair(sigma: float, seed: int, n: int = N_BITS) -> dict:
    """Both members of the pair, the shared training input, and pair diagnostics."""
    p, masks, theta, z, layout = sigma_target(sigma, seed, n)
    ops = masks_up_to(n, 3)
    q0, lam, proj_resid, msg = maxent_projection(p, n, 3)   # raises if residual > 1e-10
    f0 = parity_coefficients(q0)[ops] - parity_coefficients(p)[ops]
    q, lam, newton_steps = refine_projection(lam, parity_coefficients(p)[ops],
                                             parity_matrix(n, ops))
    q = q / q.sum()
    f_p = parity_coefficients(p)[ops]
    f_q = parity_coefficients(q)[ops]
    return {"p": {"iqp": p, "maxent_proj": q}, "masks": masks, "theta": theta, "z": z,
            "layout": layout, "ops": ops, "fhat": f_p,
            "pair_moment_residual": float(np.sum((f_q - f_p) ** 2)),
            "pair_moment_max_abs": float(np.max(np.abs(f_q - f_p))),
            "projection_message": msg, "newton_steps": newton_steps,
            "lbfgs_projection_max_abs": float(np.max(np.abs(f0))),
            "lbfgs_projection_residual": float(np.sum(f0**2)), "D3": kl(p, q)}


# ---------------- fits ----------------
def replay_inits(n_params: int, seed: int, n_restarts: int = N_RESTARTS) -> list:
    """The init vectors fit_moments(seed) draws on its generic path, in order."""
    rng = np.random.default_rng(seed)
    return [rng.normal(0.0, INIT_STD, n_params) for _ in range(n_restarts)]


def best_restart(residuals) -> int:
    """Index of the lowest-training-residual restart (first one on ties). R is taken there."""
    return int(np.argmin(np.asarray(residuals, dtype=np.float64)))


def fit_restarts(model: IQPModel, fhat, ops, seed: int, p_true, n: int,
                 n_restarts: int = N_RESTARTS) -> dict:
    """All restarts, each via the production fit_moments, with G against p_true."""
    t0 = time.time()
    rows = []
    for theta0 in replay_inits(model.n_params, seed, n_restarts):
        fit = model.fit_moments(fhat, ops, seed=seed, n_restarts=1, theta0=theta0)
        gap = M1.completion_gap(model.prob(fit.params), p_true, n)
        rows.append({"residual": float(fit.train_residual), "G": gap["G"],
                     "per_level": gap["per_level"], "nit": int(fit.nit), "message": fit.message,
                     "params": fit.params})
    i = best_restart([r["residual"] for r in rows])
    return {"rows": rows, "best": i, "seconds": time.time() - t0}


def run_instance(target: str, sigma: float, seed: int, n: int = N_BITS, fits=("O", "G"),
                 restarts: dict | None = None, pair: dict | None = None) -> dict:
    if target not in TARGETS:
        raise ValueError(target)
    restarts = restarts or {}
    t_start = time.time()
    pair = pair or make_pair(sigma, seed, n)
    p_true = pair["p"][target]
    ops, fhat = pair["ops"], pair["fhat"]

    me = MaxEntModel(n, 3)
    me_fit = me.fit_moments(fhat, ops)
    G_me = M1.completion_gap(me.prob(me_fit.params), p_true, n)
    G_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p_true, n)
    out = {"target": target, "sigma": sigma, "seed": seed, "n": n, "N": "inf",
           "versions": versions(),
           "designed_after": "step 1-2 diagnostics (notes/2026-11-06_steps1-2_findings.md)",
           "target_layout": [list(g) for g in pair["layout"]], "target_theta": pair["theta"].tolist(),
           "training_input": "exact order-<=3 moments of iqp(sigma, seed), shared by the pair",
           "pair_moment_residual": pair["pair_moment_residual"],
           "pair_moment_max_abs": pair["pair_moment_max_abs"],
           "projection_newton_steps": pair["newton_steps"],
           "projection_lbfgs_max_abs": pair["lbfgs_projection_max_abs"],
           "D3": pair["D3"],   # of the iqp target: the same number in both members of the pair
           "hi_order_frac": hi_order_frac(p_true),
           "collision_ratio_target": M1.collision_ratio(p_true),
           "clifford_dist_median_target": M1.clifford_distance(pair["theta"])["clifford_dist_median"],
           "G_maxent": G_me["G"], "G_uniform": G_uni["G"],
           "maxent_train_residual": me_fit.train_residual,
           "per_level": {"maxent": G_me["per_level"], "uniform": G_uni["per_level"]},
           "fits_run": list(fits)}
    if target == "maxent_proj":
        out["target_note"] = ("hi_order_frac and collision are of maxent_proj itself; the Clifford "
                              "median is of the paired iqp angles")

    for name in fits:
        model = IQPModel(n, gens=pair["masks"]) if name == "O" else IQPModel(n)
        r = fit_restarts(model, fhat, ops, seed, p_true, n, restarts.get(name, N_RESTARTS))
        b = r["rows"][r["best"]]
        out[f"{name}_best_restart"] = r["best"]
        out[f"{name}_train_residual"] = b["residual"]
        out[f"{name}_G"] = b["G"]
        out[f"{name}_R"] = b["G"] / G_me["G"]
        out[f"{name}_restart_residuals"] = [x["residual"] for x in r["rows"]]
        out[f"{name}_restart_G"] = [x["G"] for x in r["rows"]]
        out[f"{name}_restart_nit"] = [x["nit"] for x in r["rows"]]
        out[f"{name}_restart_message"] = [x["message"] for x in r["rows"]]
        out[f"{name}_n_params"] = int(model.n_params)
        out[f"{name}_n_restarts"] = len(r["rows"])
        out[f"{name}_best_params"] = [float(v) for v in b["params"]]
        out["per_level"][name] = b["per_level"]
        out[f"{name}_fit_seconds"] = r["seconds"]
    out["total_seconds"] = time.time() - t_start
    return out


# ---------------- report (build order item 4) ----------------
D3_ROOM = 1e-2          # carried over from step 2 (a guess, frozen in the spec)
FLOOR = 1e-30           # log-plot floor for exact-zero residuals / G (display only)


def load_grid() -> dict:
    """{(target, sigma, seed): metrics} for every metrics.json present."""
    out = {}
    for t in TARGETS:
        for sg in SIGMAS:
            for s in SEEDS:
                f = default_out(t, sg, s) / "metrics.json"
                if f.exists():
                    out[(t, sg, s)] = json.loads(f.read_text())
    return out


def iqr(x):
    x = np.asarray(x, dtype=np.float64)
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    return float(q1), float(med), float(q3)


def verdict_at(x) -> str:
    """Spec section 3: "R < 1" = IQR entirely below 1; "R >= 1" = IQR entirely at or above 1."""
    q1, _, q3 = iqr(x)
    return "<1" if q3 < 1 else (">=1" if q1 >= 1 else "undecided")


def write_table(grid: dict, path: Path):
    cols = ["target", "sigma", "seed", "D3", "G_maxent", "G_uniform", "maxent_train_residual",
            "O_R", "O_G", "O_train_residual", "O_best_restart", "O_n_restarts",
            "G_R", "G_G", "G_train_residual", "G_best_restart", "G_n_restarts",
            "paired_iqp_G_maxent", "hi_order_frac", "collision_ratio_target",
            "clifford_dist_median_target", "total_seconds"]
    lines = [",".join(cols)]
    for (t, sg, s), d in sorted(grid.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        row = dict(d)
        row["paired_iqp_G_maxent"] = grid.get(("iqp", sg, s), {}).get("G_maxent", "")
        lines.append(",".join(str(row.get(c, "")) for c in cols))
    path.write_text("\n".join(lines) + "\n")


def verdicts(grid: dict) -> dict:
    v = {"per_sigma": {}}
    for sg in SIGMAS:
        row = {}
        for t in TARGETS:
            ds = [grid[(t, sg, s)] for s in SEEDS if (t, sg, s) in grid]
            if not ds:
                continue
            for m in ("O", "G"):
                R = [d[f"{m}_R"] for d in ds]
                row[f"{t}_{m}_R_iqr"] = iqr(R)
                row[f"{t}_{m}_R_verdict"] = verdict_at(R)
                row[f"{t}_{m}_train_residual_iqr"] = iqr([d[f"{m}_train_residual"] for d in ds])
            row[f"{t}_G_maxent_iqr"] = iqr([d["G_maxent"] for d in ds])
            row[f"{t}_n_seeds"] = len(ds)
        ds_i = [grid[("iqp", sg, s)] for s in SEEDS if ("iqp", sg, s) in grid]
        row["D3_iqr"] = iqr([d["D3"] for d in ds_i])
        # K2 condition, per instance: maxent_proj's G-fit training residual <= G_maxent of the
        # paired iqp instance (same sigma, same seed).
        k2 = [s for s in SEEDS if ("maxent_proj", sg, s) in grid and ("iqp", sg, s) in grid
              and grid[("maxent_proj", sg, s)]["G_train_residual"] <= grid[("iqp", sg, s)]["G_maxent"]]
        row["K2_qualifying_seeds"] = k2
        if k2:
            Rk = [grid[("maxent_proj", sg, s)]["G_R"] for s in k2]
            row["K2_R_iqr"] = iqr(Rk)
            row["K2_verdict"] = verdict_at(Rk)
        v["per_sigma"][f"{sg:g}"] = row
    ps = v["per_sigma"]
    v["K1"] = all(ps[k]["maxent_proj_O_R_verdict"] == ">=1" for k in ps)
    v["K2"] = all(ps[k].get("K2_verdict", ">=1") == ">=1" for k in ps)
    v["K2_sigmas_constrained"] = [k for k in ps if ps[k]["K2_qualifying_seeds"]]
    v["C1"] = ps["0.05"]["iqp_O_R_verdict"] == "<1"
    medO = [ps[k]["iqp_O_R_iqr"][1] for k in ps]
    v["M1_violations"] = int(sum(b < a for a, b in zip(medO, medO[1:])))
    v["M1"] = v["M1_violations"] <= 1
    v["M2_failing_sigmas"] = [k for k in ps if ps[k]["iqp_G_R_iqr"][1] < ps[k]["iqp_O_R_iqr"][1]]
    v["M2"] = not v["M2_failing_sigmas"]
    v["W"] = [float(k) for k in ps if ps[k]["iqp_O_R_verdict"] == "<1" and ps[k]["D3_iqr"][1] >= D3_ROOM]
    v["M3"] = set(v["W"]) <= {0.1}
    return v


def residual_G_correlations(grid: dict) -> dict:
    """corr(log10 residual, log10 G) over all restarts of the iqp target, per sigma and fit."""
    out = {}
    for m in ("O", "G"):
        for sg in SIGMAS:
            r, g = [], []
            for s in SEEDS:
                d = grid.get(("iqp", sg, s))
                if d:
                    r += d[f"{m}_restart_residuals"]
                    g += d[f"{m}_restart_G"]
            lr = np.log10(np.maximum(r, FLOOR))
            lg = np.log10(np.maximum(g, FLOOR))
            out[f"{m}/{sg:g}"] = (float(np.corrcoef(lr, lg)[0, 1]) if len(r) > 2 and lr.std() > 0
                                  and lg.std() > 0 else None)
    return out


def make_figures(grid: dict, v: dict, fig_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir.mkdir(parents=True, exist_ok=True)
    sg = np.array(SIGMAS)
    ps = v["per_sigma"]

    def save(fig, name):
        for ax in fig.axes:
            if ax.get_xlabel() == "σ":       # ticks at the grid values, no minor labels
                ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(SIGMAS))
                ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter([f"{x:g}" for x in SIGMAS]))
                ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        fig.tight_layout()
        fig.savefig(fig_dir / f"{name}.png", dpi=150)
        fig.savefig(fig_dir / f"{name}.pdf")
        plt.close(fig)

    # 1. ratio_vs_sigma
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    styles = {("iqp", "O"): ("o", "-", "k"), ("iqp", "G"): ("s", "--", "0.35"),
              ("maxent_proj", "O"): ("^", ":", "k"), ("maxent_proj", "G"): ("v", "-.", "0.35")}
    for (t, m), (mk, ls, c) in styles.items():
        q = np.array([ps[f"{x:g}"][f"{t}_{m}_R_iqr"] for x in sg])
        ax.plot(sg, q[:, 1], marker=mk, ls=ls, color=c, label=f"{m} on {t}")
        ax.fill_between(sg, q[:, 0], q[:, 2], color=c, alpha=0.15, lw=0)
    ax.axhline(1.0, color="k", lw=0.8)
    for w in v["W"]:
        ax.axvspan(w / 1.15, w * 1.15, facecolor="none", hatch="//", edgecolor="0.5", lw=0)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("σ"); ax.set_ylabel("R = G_iqp / G_maxent (median, IQR band)")
    ax.set_title(f"Completion ratio vs σ (n = 12, N = ∞; W = {v['W']} hatched)", fontsize=9)
    ax.legend(fontsize=8)
    save(fig, "ratio_vs_sigma")

    # 2. room_and_proxies
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 5.6))
    panels = [("D3", "D3 of iqp target (KL to MaxEnt3)", True),
              ("hi_order_frac", "hi_order_frac of target", True),
              ("collision_ratio_target", "collision ratio of target", False),
              ("clifford_dist_median_target", "Clifford distance median (iqp angles)", False)]
    for ax, (key, lab, logy) in zip(axs.flat, panels):
        for t, mk, ls in (("iqp", "o", "-"), ("maxent_proj", "^", ":")):
            q = np.array([iqr([grid[(t, x, s)][key] for s in SEEDS if (t, x, s) in grid]) for x in sg])
            ax.plot(sg, q[:, 1], marker=mk, ls=ls, color="k", label=t)
            ax.fill_between(sg, q[:, 0], q[:, 2], color="k", alpha=0.12, lw=0)
        if key == "D3":
            ax.axhline(D3_ROOM, color="0.5", lw=0.8, ls="--")
        ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")
        ax.set_xlabel("σ"); ax.set_title(lab, fontsize=9)
    axs[0, 0].legend(fontsize=7)
    save(fig, "room_and_proxies")

    # 3. residual_vs_G
    fig, axs = plt.subplots(1, 2, figsize=(9.0, 4.2), sharey=True)
    markers = ["o", "s", "^", "v", "D", "P"]
    cmap = plt.get_cmap("viridis")
    corr = residual_G_correlations(grid)
    for ax, m in zip(axs, ("O", "G")):
        for i, x in enumerate(sg):
            r, g = [], []
            for s in SEEDS:
                d = grid.get(("iqp", x, s))
                if d:
                    r += d[f"{m}_restart_residuals"]; g += d[f"{m}_restart_G"]
            c = corr[f"{m}/{x:g}"]
            ax.scatter(np.maximum(r, FLOOR), np.maximum(g, FLOOR), marker=markers[i], s=14,
                       color=cmap(i / (len(sg) - 1)), facecolors="none" if i % 2 else None,
                       label=f"σ={x:g} (r={c:.2f})" if c is not None else f"σ={x:g}")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("training residual (all restarts)")
        ax.set_title(f"fit {m} on iqp targets", fontsize=9)
        ax.legend(fontsize=7)
    axs[0].set_ylabel(f"G_iqp (orders 4-6); values < {FLOOR:g} shown at the floor")
    save(fig, "residual_vs_G")
    return corr


def report():
    grid = load_grid()
    write_table(grid, ROOT / "results" / "step3" / "table.csv")
    v = verdicts(grid)
    v["n_instances"] = len(grid)
    v["residual_G_corr_iqp"] = make_figures(grid, v, ROOT / "figures" / "step3")
    (ROOT / "results" / "step3" / "verdicts.json").write_text(json.dumps(v, indent=1))
    print(json.dumps(v, indent=1))


# ---------------- CLI ----------------
def default_out(target: str, sigma: float, seed: int) -> Path:
    return ROOT / "results" / "step3" / target / f"sigma_{sigma:g}" / f"seed_{seed}"


def write(out: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / "metrics.json"
    f.write_text(json.dumps(out, indent=1))
    return f


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fits", default="O,G")
    ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true",
                    help="table.csv, verdicts.json and figures from the metrics.json present")
    a = ap.parse_args(argv)
    if a.report:
        report()
        return
    fits = tuple(x.strip() for x in a.fits.split(",") if x.strip())
    if any(f not in ("O", "G") for f in fits):
        ap.error("--fits takes O and/or G")

    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the grid: BUDGET_OK does not exist (only the user creates it)")
        for sg in SIGMAS:
            for s in SEEDS:
                pair = make_pair(sg, s)
                for t in TARGETS:
                    out = run_instance(t, sg, s, fits=fits, pair=pair, restarts=ALL_GRID_RESTARTS)
                    out["budget_cut"] = "G restarts 10 -> 3 (spec cut 1; user decision 2026-11-06)"
                    print(write(out, default_out(t, sg, s)), flush=True)
        return

    if a.target is None or a.sigma is None:
        ap.error("--target and --sigma are required unless --all")
    out = run_instance(a.target, a.sigma, a.seed, fits=fits)
    f = write(out, Path(a.out) if a.out else default_out(a.target, a.sigma, a.seed))
    print(f)
    print(f"  D3 = {out['D3']:.3e}  G_maxent = {out['G_maxent']:.3e}  G_uniform = {out['G_uniform']:.3e}  "
          f"pair moment residual = {out['pair_moment_residual']:.1e}  ({out['total_seconds']:.1f} s)")
    for name in fits:
        print(f"  {name}: R = {out[f'{name}_R']:.4g}  G = {out[f'{name}_G']:.3e}  "
              f"train residual = {out[f'{name}_train_residual']:.3e}  ({out[f'{name}_fit_seconds']:.1f} s)")


if __name__ == "__main__":
    main()

"""Step 7: does the iqp4 advantage come back at matched peakedness? (specs/step7_collision_matched.md)

Designed after step 6 (notes/2026-11-08_step6_findings.md).

  python -m src.step7.run --n 14 --level C --seed 0     (one instance, N = inf)
  python -m src.step7.run --projection                   (results/step7/PROJECTION.json)
  python -m src.step7.run --all                          (refuses to start without BUDGET_OK)
  python -m src.step7.run --report                       (table.csv, verdicts.json, figures/step7/*)

One instance = src/step6/run.run_instance(n, sigma, seed), imported unchanged (which is
src/step5/run.fit_instance("iqp4", sigma, N = None, seed, n): G = the generic weight-<=3 IQP,
3 restarts, MaxEnt(3) ridge 1e-8, exact moments). This module adds the matched-sigma table
(spec section 2, used verbatim), the `level` key and the IO. src/step1..6 are never edited.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from src.step5.run import write
from src.step6.run import run_instance as step6_instance

# spec section 2, the six bold numbers, used exactly (not recomputed, not re-rounded)
MATCHED_SIGMA = {
    14: {"A": 0.193, "B": 0.213, "C": 0.236},
    16: {"A": 0.231, "B": 0.251, "C": 0.274},
}
# n = 12 reference (step 5, data already seen): sigma and median target collision ratio per level
N12_LEVEL = {"A": (0.15, 561.3), "B": (0.175, 283.9), "C": (0.2, 133.9)}
LEVELS = ("A", "B", "C")
NS_BITS = (14, 16)
SEEDS = (0, 1, 2, 3, 4)
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step7"
TIMED = {14: "C", 16: "C"}          # spec section 7: the largest sigma at each n
BUDGET_HOURS = 5.0
NAMED_CUT = ((16, "A"),)            # spec section 7: the only allowed cut


def run_instance(n: int, level: str, seed: int) -> dict:
    sigma = MATCHED_SIGMA[n][level]
    out = step6_instance(n, sigma, seed)
    out["designed_after"] = "step 6 (notes/2026-11-08_step6_findings.md)"
    out["level"] = level
    out["n12_reference_sigma"], out["n12_reference_collision_ratio"] = N12_LEVEL[level]
    return out


def default_out(n: int, level: str, seed: int) -> Path:
    return RESULTS / f"n_{n}" / f"sigma_{MATCHED_SIGMA[n][level]:g}" / f"seed_{seed}"


def grid(cut=()):
    for n in NS_BITS:
        for lv in LEVELS:
            if (n, lv) in cut:
                continue
            for s in SEEDS:
                yield n, lv, s


def projection() -> dict:
    sec, per = {}, {}
    for n, lv in TIMED.items():
        d = json.loads((default_out(n, lv, 0) / "metrics.json").read_text())
        sec[n] = d["total_seconds"]
        per[f"n_{n}/sigma_{MATCHED_SIGMA[n][lv]:g}/seed_0"] = {
            "level": lv, "total_seconds": d["total_seconds"], "G_fit_seconds": d["G_fit_seconds"],
            "G_train_residual": d["G_train_residual"], "G_restart_residuals": d["G_restart_residuals"],
            "G_restart_nit": d["G_restart_nit"], "G_restart_message": d["G_restart_message"],
            "maxent_train_residual": d["maxent_train_residual"], "maxent_nit": d["maxent_nit"],
            "collision_ratio_target": d["collision_ratio_target"],
            "peak_memory_bytes_process": d.get("peak_memory_bytes_process")}

    def hours(cut):
        return sum(sec[n] for n, _, _ in grid(cut)) / 3600.0

    total = hours(())
    out = {"basis": "spec section 7: per-n time of the timed instance (largest sigma, seed 0, N = inf) x 15",
           "seconds_by_n": {f"n_{n}": sec[n] for n in NS_BITS},
           "projected_hours_by_n": {f"n_{n}": 15 * sec[n] / 3600.0 for n in NS_BITS},
           "projected_hours": total, "instances": sum(1 for _ in grid()),
           "budget_hours": BUDGET_HOURS, "over_budget": total > BUDGET_HOURS, "per_instance": per,
           "note": "one timed instance per n. In step 6, n = 16 instances took 0.8x-8x their 400 s "
                   "timing instance (sum 2.1x the projection).",
           "projected_hours_x2": 2 * total, "stop_loss_wall_clock_hours": 8.0}
    if total > BUDGET_HOURS:
        h = hours(NAMED_CUT)
        out["cut"] = {"rule": "spec section 7: the only named cut is n = 16 at level A (sigma = 0.231); "
                              "C3 then FAIL-untested at n = 16. Never seeds, restarts, n = 14 cells, "
                              "or n = 16 at levels B and C.",
                      "drop": "n = 16, level A, sigma = 0.231", "projected_hours_after": h,
                      "instances_after": sum(1 for _ in grid(NAMED_CUT)),
                      "cut_grid_within_budget": h <= BUDGET_HOURS,
                      "if_not_within_budget": None if h <= BUDGET_HOURS else "stop and report; the user decides"}
    else:
        out["cut"] = None
    return out


# ---------------- report (build order item 4) ----------------
REF_N = 12
G_MAXITER = 20000          # src/step1/models/iqp.LBFGS_OPTS (unchanged)
RES_C4 = 1e-2


def step5_ref(level: str, seed: int) -> Path:
    sg = N12_LEVEL[level][0]
    return ROOT / "results" / "step5" / "iqp4" / f"sigma_{sg:g}" / "N_inf" / f"seed_{seed}" / "metrics.json"


def load_all() -> dict:
    g = {}
    for lv in LEVELS:
        for s in SEEDS:
            f = step5_ref(lv, s)
            if f.exists():
                g[(REF_N, lv, s)] = json.loads(f.read_text())
    for n, lv, s in grid():
        f = default_out(n, lv, s) / "metrics.json"
        if f.exists():
            g[(n, lv, s)] = json.loads(f.read_text())
    return g


def sigma_of(n: int, lv: str) -> float:
    return N12_LEVEL[lv][0] if n == REF_N else MATCHED_SIGMA[n][lv]


def cell_stats(g: dict) -> dict:
    from src.step5.run import iqr, verdict_at
    st = {}
    for n in (REF_N,) + NS_BITS:
        for lv in LEVELS:
            ds = [g[(n, lv, s)] for s in SEEDS if (n, lv, s) in g]
            if not ds:
                continue
            res = [d["G_train_residual"] for d in ds]
            spread = [max(d["G_restart_residuals"]) / min(d["G_restart_residuals"]) for d in ds]
            lim = sum(1 for d in ds if any(x >= G_MAXITER for x in d["G_restart_nit"])
                      or any("LIMIT" in m.upper() for m in d["G_restart_message"]))
            st[f"n_{n}/level_{lv}"] = {
                "n": n, "level": lv, "sigma": sigma_of(n, lv), "seeds": len(ds),
                "source": "results/step5 (data already seen)" if n == REF_N else "results/step7",
                "R": [d["R"] for d in ds], "R_iqr": iqr([d["R"] for d in ds]),
                "R_verdict": verdict_at([d["R"] for d in ds]),
                "G_train_residual": res, "G_train_residual_iqr": iqr(res),
                "G_restart_spread": spread, "G_restart_spread_max": max(spread),
                "G_maxiter_seeds": lim, "R_possibly_biased_up": lim > 2,
                "collision_ratio": [d["collision_ratio_target"] for d in ds],
                "collision_ratio_iqr": iqr([d["collision_ratio_target"] for d in ds]),
                "collision_vs_n12_level": iqr([d["collision_ratio_target"] for d in ds])[1] / N12_LEVEL[lv][1],
                "D3_iqr": iqr([d["D3"] for d in ds]),
                "G_iqp_iqr": iqr([d["G_iqp"] for d in ds]), "G_maxent_iqr": iqr([d["G_maxent"] for d in ds]),
                "maxent_train_residual_max": max(d["maxent_train_residual"] for d in ds),
                "maxent_maxiter_hits": sum(1 for d in ds if d["maxent_nit"] >= 20000),
                "seconds": [d["total_seconds"] for d in ds]}
    return st


def verdicts7(st: dict) -> dict:
    c = lambda n, lv: st.get(f"n_{n}/level_{lv}")
    v = {}
    for h, lv in (("C1", "B"), ("C2", "C")):
        v[h] = {"PASS": all(c(n, lv) and c(n, lv)["R_verdict"] == "<1" for n in NS_BITS), "level": lv,
                **{f"n_{n}": (c(n, lv)["R_verdict"] if c(n, lv) else "missing") for n in NS_BITS},
                **{f"n_{n}_median_R": (c(n, lv)["R_iqr"][1] if c(n, lv) else None) for n in NS_BITS}}
    v["C3"] = {"PASS": all(c(n, "A") and c(n, "A")["R_iqr"][1] >= 1 for n in NS_BITS), "level": "A",
               **{f"n_{n}_median_R": (c(n, "A")["R_iqr"][1] if c(n, "A") else None) for n in NS_BITS}}
    meds = {lv: c(16, lv)["G_train_residual_iqr"][1] for lv in ("B", "C") if c(16, lv)}
    v["C4"] = {"PASS": len(meds) == 2 and all(m <= RES_C4 for m in meds.values()),
               **{f"n_16_level_{lv}_median_residual": m for lv, m in meds.items()}}
    c1, c2, c4 = v["C1"]["PASS"], v["C2"]["PASS"], v["C4"]["PASS"]
    fail16 = all(c(16, lv) and c(16, lv)["R_verdict"] != "<1" for lv in ("B", "C"))
    if c1 and c2:
        rule = "C1 and C2 both pass: the step-6 shrinkage is mostly a peakedness effect."
    elif fail16 and c4:
        rule = ("C1 and C2 both fail at n = 16 while C4 passes: the advantage shrinks with n even at "
                "matched peakedness, and under-training does not explain it.")
    elif fail16 and not c4:
        rule = ("C1 and C2 fail at n = 16 and C4 fails too: unresolved between under-training and a "
                "real effect.")
    else:
        rule = "none of the three reading rules of spec section 4 applies exactly (see the per-n verdicts)."
    v["reading_rule"] = rule
    return v


def write_table7(st: dict, path: Path):
    cols = ["n", "level", "sigma", "source", "seeds", "R_q1", "R_median", "R_q3", "R_verdict",
            "G_residual_q1", "G_residual_median", "G_residual_q3", "G_restart_spread_max", "G_maxiter_seeds",
            "collision_q1", "collision_median", "collision_q3", "collision_vs_n12_level",
            "D3_q1", "D3_median", "D3_q3", "G_iqp_median", "G_maxent_median", "maxent_maxiter_hits"]
    lines = [",".join(cols)]
    for k, c in st.items():
        row = [c["n"], c["level"], c["sigma"], c["source"].split()[0], c["seeds"], *c["R_iqr"], c["R_verdict"],
               *c["G_train_residual_iqr"], c["G_restart_spread_max"], c["G_maxiter_seeds"],
               *c["collision_ratio_iqr"], c["collision_vs_n12_level"], *c["D3_iqr"],
               c["G_iqp_iqr"][1], c["G_maxent_iqr"][1], c["maxent_maxiter_hits"]]
        lines.append(",".join(str(x) for x in row))
    path.write_text("\n".join(lines) + "\n")


def make_figures7(st: dict, fig_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir.mkdir(parents=True, exist_ok=True)
    style = {12: ("o", "-", "0.6"), 14: ("s", "--", "0.35"), 16: ("^", "-", "k")}

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(fig_dir / f"{name}.png", dpi=150)
        fig.savefig(fig_dir / f"{name}.pdf")
        plt.close(fig)

    # step 6 fixed-sigma points (and step 5's n = 12 at the step-6 sigma) for context
    s6 = json.loads((ROOT / "results" / "step6" / "verdicts.json").read_text())["stats"]
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for n in (REF_N,) + NS_BITS:
        m, ls, col = style[n]
        pts = sorted(((c["collision_ratio_iqr"][1], c["R_iqr"][1]) for k, c in s6.items() if c["n"] == n),
                     reverse=True)
        if pts:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], marker=m, ls=":", color=col, alpha=0.3, mfc="none",
                    label=f"n = {n}, step 6 fixed σ (context)")
        cs = [st[f"n_{n}/level_{lv}"] for lv in LEVELS if f"n_{n}/level_{lv}" in st]
        x = [c["collision_ratio_iqr"][1] for c in cs]
        q = np.array([c["R_iqr"] for c in cs])
        ax.errorbar(x, q[:, 1], yerr=[q[:, 1] - q[:, 0], q[:, 2] - q[:, 1]], marker=m, ls=ls, color=col,
                    capsize=3, label=f"n = {n}, levels {''.join(c['level'] for c in cs)}"
                    + (" (step 5, seen)" if n == REF_N else ""))
        for c, xx, yy in zip(cs, x, q[:, 1]):
            ax.annotate(c["level"], (xx, yy), textcoords="offset points", xytext=(4, 4), fontsize=7, color=col)
    ax.axhline(1.0, color="k", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.invert_xaxis()
    ax.set_xlabel("target collision ratio 2^n Σ p² (median over 5 seeds; less peaked →)")
    ax.set_ylabel("R = G_iqp / G_maxent3 (median, IQR bars)")
    ax.set_title("iqp4, N = ∞: R at matched peakedness", fontsize=9)
    ax.legend(fontsize=7)
    save(fig, "R_vs_collision_by_n")

    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    xs = np.arange(len(LEVELS))
    for ax, n in zip(axs, (REF_N,) + NS_BITS):
        for key, m, ls, col, lab in (("G_iqp_iqr", "o", "-", "k", "G_iqp (orders 4-6)"),
                                     ("G_maxent_iqr", "s", "--", "0.45", "G_maxent3 (orders 4-6)"),
                                     ("G_train_residual_iqr", "^", ":", "k", "G training residual (orders ≤3, sum)")):
            q = np.array([st[f"n_{n}/level_{lv}"][key] for lv in LEVELS])
            ax.plot(xs, q[:, 1], marker=m, ls=ls, color=col, label=lab)
            ax.fill_between(xs, q[:, 0], q[:, 2], color=col, alpha=0.12, lw=0)
        ax.axhline(RES_C4, color="k", lw=0.8, ls="-.", label="residual 1e-2 (C4)")
        ax.set_yscale("log")
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{lv}\nσ = {sigma_of(n, lv):g}" for lv in LEVELS])
        ax.set_xlabel("collision level")
        ax.set_title(f"n = {n}" + (" (step 5, seen)" if n == REF_N else ""), fontsize=9)
    axs[0].set_ylabel("median over 5 seeds (IQR band)")
    axs[0].legend(fontsize=7)
    save(fig, "G_vs_level_by_n")


def report():
    g = load_all()
    st = cell_stats(g)
    v = verdicts7(st)
    write_table7(st, RESULTS / "table.csv")
    timing = {}
    for n in NS_BITS:
        sec = [d["total_seconds"] for (nn, _, _), d in g.items() if nn == n]
        timing[f"n_{n}"] = {"instances": len(sec), "sum_seconds": sum(sec),
                            "mean_seconds": sum(sec) / len(sec) if sec else None,
                            "max_seconds": max(sec) if sec else None}
    out = {"n_instances_step7": sum(1 for k in g if k[0] != REF_N), "cut": None,
           "verdicts": v, "timing": timing, "stats": st,
           "maxent_maxiter_hits_total": sum(c["maxent_maxiter_hits"] for c in st.values() if c["n"] != REF_N),
           "G_maxiter_instances_total": sum(c["G_maxiter_seeds"] for c in st.values() if c["n"] != REF_N)}
    (RESULTS / "verdicts.json").write_text(json.dumps(out, indent=1))
    make_figures7(st, ROOT / "figures" / "step7")
    print(json.dumps({"verdicts": v, "timing": timing,
                      "maxent_maxiter_hits_total": out["maxent_maxiter_hits_total"],
                      "G_maxiter_instances_total": out["G_maxiter_instances_total"]}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, choices=NS_BITS)
    ap.add_argument("--level", choices=LEVELS)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--projection", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    if a.report:
        report()
        return
    if a.projection:
        pr = projection()
        f = RESULTS / "PROJECTION.json"
        f.write_text(json.dumps(pr, indent=1))
        print(f)
        print(json.dumps(pr, indent=1))
        return
    if a.all:
        if not (ROOT / "BUDGET_OK").exists():
            sys.exit("refusing to start the grid: BUDGET_OK does not exist (only the user creates it)")
        cells = list(grid())          # full grid, no cut (user decision 2026-11-08)
        print(f"grid: {len(cells)} instances, no cut", flush=True)
        for i, (n, lv, s) in enumerate(cells, 1):
            d = default_out(n, lv, s)
            if (d / "metrics.json").exists():
                print(f"[{i}/{len(cells)}] skip (exists) {d}", flush=True)
                continue
            out = run_instance(n, lv, s)
            write(out, d)
            print(f"[{i}/{len(cells)}] {d}  {out['total_seconds']:.1f} s  G residual "
                  f"{out['G_train_residual']:.2e}  nit {out['G_restart_nit']}", flush=True)
        print("grid done", flush=True)
        return
    if a.n is None or a.level is None:
        ap.error("--n and --level are required")
    out = run_instance(a.n, a.level, a.seed)
    f = write(out, default_out(a.n, a.level, a.seed))
    pm = out["peak_memory_bytes_process"]
    print(f)
    print(f"  n {a.n}  level {a.level}  sigma {out['sigma']}  total {out['total_seconds']:.1f} s  "
          f"G fit {out['G_fit_seconds']:.1f} s  G residual {out['G_train_residual']:.3e}  restarts "
          f"{['%.2e' % x for x in out['G_restart_residuals']]}  nit {out['G_restart_nit']}  "
          f"maxent residual {out['maxent_train_residual']:.2e} (nit {out['maxent_nit']})  "
          f"coll {out['collision_ratio_target']:.1f}  peak memory {pm / 2**20 if pm else float('nan'):.0f} MiB")


if __name__ == "__main__":
    main()

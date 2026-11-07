"""Step 6: does the iqp4 advantage window survive larger n? (specs/step6_iqp4_scaling_n.md)

Designed after step 5 (notes/2026-11-07_step5_findings.md).

  python -m src.step6.run --n 14 --sigma 0.2 --seed 0     (one instance, N = inf)
  python -m src.step6.run --projection                     (results/step6/PROJECTION.json)
  python -m src.step6.run --all                            (refuses to start without BUDGET_OK)
  python -m src.step6.run --report                         (table.csv, verdicts.json, figures/step6/*)

One instance = src/step5/run.fit_instance("iqp4", sigma, N = None, seed, n), imported unchanged:
iqp4_target (src/step4/targets) at the given n, exact order-<=3 moments, MaxEnt(3) with ridge
1e-8, G = the generic IQP with every weight-<=3 generator (469 at n = 14, 696 at n = 16), 3
restarts (src/step3/run.fit_restarts), R at G's lowest-residual restart. This module only adds
the step-6 keys (G_n_params, peak memory) and the IO. src/step1..5 are closed and never edited.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import sys
from pathlib import Path

import numpy as np

from src.step4.run import G_RESTARTS
from src.step5.run import fit_instance, write

NS_BITS = (14, 16)
SIGMAS = (0.125, 0.15, 0.175, 0.2, 0.25)
SEEDS = (0, 1, 2, 3, 4)
ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step6"
TIMED_SIGMA, TIMED_SEED = 0.2, 0
BUDGET_HOURS = 3.0
# spec section 7: cut order if the projection exceeds the budget (n = 16 cells first)
CUT_ORDER = ((16, 0.25), (16, 0.125))
# applied: user decision A (2026-11-07) on PROJECTION.json 3.13 h -> first cut only, 45 instances
APPLIED_CUT = ((16, 0.25),)


def n_generic_generators(n: int, kmax: int = 3) -> int:
    from math import comb
    return sum(comb(n, k) for k in range(1, kmax + 1))


def peak_memory_bytes() -> int | None:
    """Peak working set of this process (Windows GetProcessMemoryInfo; ru_maxrss elsewhere)."""
    if sys.platform == "win32":
        class PMC(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        c = PMC()
        c.cb = ctypes.sizeof(PMC)
        k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(PMC), ctypes.c_ulong]
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        if psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb):
            return int(c.PeakWorkingSetSize)
        return None
    try:
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    except Exception:
        return None


def run_instance(n: int, sigma: float, seed: int, g_restarts: int = G_RESTARTS) -> dict:
    out = fit_instance("iqp4", sigma, None, seed, n=n, g_restarts=g_restarts)
    out["designed_after"] = "step 5 (notes/2026-11-07_step5_findings.md)"
    out["G_n_params"] = len(out["G_best_params"])
    out["G_n_params_expected"] = n_generic_generators(n)
    out["target_n_generators"] = len(out["target_masks"])
    out["peak_memory_bytes_process"] = peak_memory_bytes()
    return out


def default_out(n: int, sigma: float, seed: int) -> Path:
    return RESULTS / f"n_{n}" / f"sigma_{sigma:g}" / f"seed_{seed}"


def grid(cut=()):
    for n in NS_BITS:
        for sg in SIGMAS:
            if (n, sg) in cut:
                continue
            for s in SEEDS:
                yield n, sg, s


def projection() -> dict:
    sec, per = {}, {}
    for n in NS_BITS:
        d = json.loads((default_out(n, TIMED_SIGMA, TIMED_SEED) / "metrics.json").read_text())
        sec[n] = d["total_seconds"]
        per[f"n_{n}/sigma_{TIMED_SIGMA:g}/seed_{TIMED_SEED}"] = {
            "total_seconds": d["total_seconds"], "G_fit_seconds": d["G_fit_seconds"],
            "G_train_residual": d["G_train_residual"], "G_restart_residuals": d["G_restart_residuals"],
            "G_restart_nit": d["G_restart_nit"], "G_n_params": d["G_n_params"],
            "peak_memory_bytes_process": d.get("peak_memory_bytes_process")}

    def hours(cut):
        return sum(sec[n] for n, _, _ in grid(cut)) / 3600.0

    per_n_hours = {f"n_{n}": 25 * sec[n] / 3600.0 for n in NS_BITS}
    total = hours(())
    out = {"basis": "spec section 7: per-n time of the timed instance (sigma = 0.2, seed 0, N = inf) x 25",
           "seconds_by_n": {f"n_{n}": sec[n] for n in NS_BITS}, "projected_hours_by_n": per_n_hours,
           "projected_hours": total, "instances": sum(1 for _ in grid()),
           "budget_hours": BUDGET_HOURS, "over_budget": total > BUDGET_HOURS, "per_instance": per,
           "note": "one timed instance per n at sigma = 0.2; other sigma may converge faster or slower. "
                   "Steps 3-4 ran 1.4x-2x slower than projected on a shared machine.",
           "projected_hours_x2_shared_machine": 2 * total}
    cut, steps = [], []
    if total > BUDGET_HOURS:
        for c in CUT_ORDER:
            cut.append(c)
            h = hours(tuple(cut))
            steps.append({"drop": f"n = {c[0]}, sigma = {c[1]:g}", "projected_hours_after": h,
                          "instances_after": sum(1 for _ in grid(tuple(cut)))})
            if h <= BUDGET_HOURS:
                break
        fits = steps[-1]["projected_hours_after"] <= BUDGET_HOURS
        out["cut"] = {"order": "spec section 7: drop n = 16 sigma = 0.25, then n = 16 sigma = 0.125; "
                               "never seeds, restarts, n = 14 cells, or n = 16 at sigma 0.15/0.175/0.2",
                      "steps": steps, "cut_grid_within_budget": fits,
                      "if_not_within_budget": None if fits else
                      "stop and report; the fallback (n = 14 only) needs a user decision"}
    else:
        out["cut"] = None
    return out


# ---------------- report (build order item 3) ----------------
S2_BAND = (0.135, 0.185)
G_MAXITER = 20000          # src/step1/models/iqp.LBFGS_OPTS (not changed)
REF_N = 12                 # step 5's iqp4 N = inf cells (data already seen; not rerun)


def step5_ref_out(sigma: float, seed: int) -> Path:
    return ROOT / "results" / "step5" / "iqp4" / f"sigma_{sigma:g}" / "N_inf" / f"seed_{seed}" / "metrics.json"


def load_all() -> dict:
    """{(n, sigma, seed): metrics} for n = 12 (step 5 files) and n = 14, 16 (this step)."""
    g = {}
    for sg in SIGMAS:
        for s in SEEDS:
            f = step5_ref_out(sg, s)
            if f.exists():
                g[(REF_N, sg, s)] = json.loads(f.read_text())
    for n, sg, s in grid():
        f = default_out(n, sg, s) / "metrics.json"
        if f.exists():
            g[(n, sg, s)] = json.loads(f.read_text())
    return g


def g_limit_hit(d: dict) -> bool:
    return any(nit >= G_MAXITER for nit in d["G_restart_nit"]) or \
        any("LIMIT" in m.upper() for m in d["G_restart_message"])


def cell_stats(g: dict) -> dict:
    from src.step5.run import iqr, verdict_at
    st = {}
    for n in (REF_N,) + NS_BITS:
        for sg in SIGMAS:
            ds = [g[(n, sg, s)] for s in SEEDS if (n, sg, s) in g]
            if not ds:
                continue
            res = [d["G_train_residual"] for d in ds]
            spread = [max(d["G_restart_residuals"]) / min(d["G_restart_residuals"]) for d in ds]
            lim = sum(1 for d in ds if g_limit_hit(d))
            st[f"n_{n}/sigma_{sg:g}"] = {
                "n": n, "sigma": sg, "seeds": len(ds),
                "R": [d["R"] for d in ds], "R_iqr": iqr([d["R"] for d in ds]),
                "R_verdict": verdict_at([d["R"] for d in ds]),
                "G_train_residual": res, "G_train_residual_iqr": iqr(res),
                "G_restart_residual_max": max(max(d["G_restart_residuals"]) for d in ds),
                "G_restart_spread_max": max(spread),
                "G_maxiter_seeds": lim, "R_possibly_biased_up": lim > 2,
                "FM2_symptom": max(max(d["G_restart_residuals"]) for d in ds) > 1e-2 or max(spread) > 10,
                "G_iqp_iqr": iqr([d["G_iqp"] for d in ds]), "G_maxent_iqr": iqr([d["G_maxent"] for d in ds]),
                "collision_ratio": [d["collision_ratio_target"] for d in ds],
                "collision_ratio_iqr": iqr([d["collision_ratio_target"] for d in ds]),
                "D3_iqr": iqr([d["D3"] for d in ds]),
                "maxent_train_residual_max": max(d["maxent_train_residual"] for d in ds),
                "maxent_maxiter_hits": sum(1 for d in ds if d["maxent_nit"] >= 20000),
                "seconds": [d["total_seconds"] for d in ds],
                "source": "results/step5 (data already seen)" if n == REF_N else "results/step6"}
    return st


def crossings6(st: dict) -> dict:
    from src.step5.run import sign_changes, sigma_star
    out = {}
    for n in (REF_N,) + NS_BITS:
        sg = [x for x in SIGMAS if f"n_{n}/sigma_{x:g}" in st and st[f"n_{n}/sigma_{x:g}"]["seeds"] == 5]
        meds = [st[f"n_{n}/sigma_{x:g}"]["R_iqr"][1] for x in sg]
        out[f"n_{n}"] = {"sigmas": sg, "median_R": meds, "sigma_star": sigma_star(sg, meds),
                         "sign_changes": sign_changes(meds)}
    s5 = json.loads((ROOT / "results" / "step5" / "verdicts.json").read_text())["crossings"]["iqp4/N_inf"]
    out[f"n_{REF_N}"]["step5_verdicts_sigma_star"] = s5["sigma_star"]
    out[f"n_{REF_N}"]["step5_verdicts_sign_changes"] = s5["sign_changes"]
    out[f"n_{REF_N}"]["note"] = ("step 5 value over its 6 sigma (incl. 0.1); sigma_star above is "
                                 "recomputed on step 6's 5 sigma")
    return out


def verdicts6(st: dict, cr: dict) -> dict:
    v = {}
    c = lambda n, sg: st.get(f"n_{n}/sigma_{sg:g}")
    v["S1"] = {"PASS": all(c(n, 0.2) and c(n, 0.2)["R_verdict"] == "<1" for n in NS_BITS),
               **{f"n_{n}": c(n, 0.2)["R_verdict"] if c(n, 0.2) else "missing" for n in NS_BITS}}
    stars = {n: cr[f"n_{n}"]["sigma_star"] for n in NS_BITS}
    v["S2"] = {"PASS": all(s is not None and S2_BAND[0] <= s <= S2_BAND[1] for s in stars.values()),
               "band": S2_BAND, **{f"sigma_star_n_{n}": stars[n] for n in NS_BITS},
               **{f"sign_changes_n_{n}": cr[f"n_{n}"]["sign_changes"] for n in NS_BITS},
               "rule": "spec section 4: both defined and in the band; undefined -> FAIL"}
    v["S3"] = {"PASS": all(c(n, 0.175) and c(n, 0.175)["R_verdict"] == "<1" for n in NS_BITS),
               **{f"n_{n}": c(n, 0.175)["R_verdict"] if c(n, 0.175) else "missing" for n in NS_BITS}}
    sg16 = [x for x in SIGMAS if c(16, x)]
    gi = [c(16, x)["G_iqp_iqr"][1] for x in sg16]
    v["S4"] = {"PASS": max(gi) / min(gi) <= 3, "G_iqp_max_over_min_n16": max(gi) / min(gi),
               "sigmas_used": sg16,
               "note": "sigma = 0.25 at n = 16 was cut (spec section 7, user decision A); "
                       "the ratio is over the 4 remaining sigma"}
    return v


def write_table6(g: dict, path: Path):
    cols = ["n", "sigma", "seed", "source", "R", "G_iqp", "G_maxent", "G_uniform", "G_train_residual",
            "G_best_restart", "G_n_restarts", "G_n_params", "G_restart_nit", "maxent_train_residual",
            "maxent_nit", "D3", "collision_ratio_target", "hi_order_frac", "total_seconds"]
    lines = [",".join(cols)]
    for (n, sg, s) in sorted(g):
        d = dict(g[(n, sg, s)])
        d["source"] = "step5" if n == REF_N else "step6"
        d.setdefault("G_n_params", len(d.get("G_best_params", [])) or None)
        d["G_restart_nit"] = ";".join(str(x) for x in d.get("G_restart_nit", []))
        lines.append(",".join("" if d.get(k) is None else str(d.get(k)) for k in cols))
    path.write_text("\n".join(lines) + "\n")


def make_figures6(st: dict, fig_dir: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
    fig_dir.mkdir(parents=True, exist_ok=True)
    NS_ALL = (REF_N,) + NS_BITS
    style = {12: ("o", "-", "0.6"), 14: ("s", "--", "0.35"), 16: ("^", "-", "k")}

    def sax(ax):
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(FixedLocator(SIGMAS))
        ax.xaxis.set_major_formatter(FixedFormatter([f"{x:g}" for x in SIGMAS]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xlabel("σ (iqp4 angle scale)")

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(fig_dir / f"{name}.png", dpi=150)
        fig.savefig(fig_dir / f"{name}.pdf")
        plt.close(fig)

    def ser(n, key):
        xs = [x for x in SIGMAS if f"n_{n}/sigma_{x:g}" in st]
        return np.array(xs), np.array([st[f"n_{n}/sigma_{x:g}"][key] for x in xs])

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.axvspan(*S2_BAND, facecolor="none", hatch="//", edgecolor="0.7", lw=0, label="S2 band [0.135, 0.185]")
    for n in NS_ALL:
        m, ls, col = style[n]
        x, q = ser(n, "R_iqr")
        ax.plot(x, q[:, 1], marker=m, ls=ls, color=col,
                label=f"n = {n}" + (" (step 5, data already seen)" if n == REF_N else ""))
        ax.fill_between(x, q[:, 0], q[:, 2], color=col, alpha=0.12, lw=0)
    ax.axhline(1.0, color="k", lw=0.8)
    ax.set_yscale("log"); sax(ax)
    ax.set_ylabel("R = G_iqp / G_maxent3 (median, IQR band; 5 seeds)")
    ax.set_title("iqp4, N = ∞ (n = 16 at σ = 0.25 cut, spec section 7)", fontsize=9)
    ax.legend(fontsize=7)
    save(fig, "R_vs_sigma_by_n")

    fig, axs = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    for ax, n in zip(axs, NS_ALL):
        for key, m, ls, col, lab in (("G_iqp_iqr", "o", "-", "k", "G_iqp (orders 4-6)"),
                                     ("G_maxent_iqr", "s", "--", "0.45", "G_maxent3 (orders 4-6)"),
                                     ("G_train_residual_iqr", "^", ":", "k", "G training residual (orders ≤3, sum)")):
            x, q = ser(n, key)
            ax.plot(x, q[:, 1], marker=m, ls=ls, color=col, label=lab)
            ax.fill_between(x, q[:, 0], q[:, 2], color=col, alpha=0.12, lw=0)
        ax.set_yscale("log"); sax(ax)
        ax.set_title(f"n = {n}" + (" (step 5)" if n == REF_N else ""), fontsize=9)
    axs[0].set_ylabel("median over 5 seeds (IQR band)")
    axs[0].legend(fontsize=7)
    save(fig, "G_vs_sigma_by_n")

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    grays = np.linspace(0.75, 0.0, len(SIGMAS))
    for sg, gr in zip(SIGMAS, grays):
        ns = [n for n in NS_ALL if f"n_{n}/sigma_{sg:g}" in st]
        q = np.array([st[f"n_{n}/sigma_{sg:g}"]["collision_ratio_iqr"] for n in ns])
        ax.errorbar(ns, q[:, 1], yerr=[q[:, 1] - q[:, 0], q[:, 2] - q[:, 1]], marker="o",
                    color=str(gr), capsize=3, label=f"σ = {sg:g}")
    ax.set_yscale("log")
    ax.set_xticks(list(NS_ALL))
    ax.set_xlabel("n (qubits)")
    ax.set_ylabel("collision ratio 2^n Σ p² of the target (median, IQR)")
    ax.set_title("iqp4 gets more peaked with n at fixed σ (spec section 2 caveat)", fontsize=9)
    ax.legend(fontsize=7)
    save(fig, "collision_vs_n")


def report():
    g = load_all()
    write_table6(g, RESULTS / "table.csv")
    st = cell_stats(g)
    cr = crossings6(st)
    v = verdicts6(st, cr)
    timing = {}
    for n in NS_BITS:
        sec = [d["total_seconds"] for (nn, _, _), d in g.items() if nn == n]
        timing[f"n_{n}"] = {"instances": len(sec), "sum_seconds": sum(sec),
                            "mean_seconds": sum(sec) / len(sec) if sec else None,
                            "max_seconds": max(sec) if sec else None}
    out = {"n_instances_step6": sum(1 for k in g if k[0] != REF_N),
           "cut": [{"n": n, "sigma": s} for n, s in APPLIED_CUT],
           "verdicts": v, "crossings": cr, "timing": timing, "stats": st,
           "maxent_maxiter_hits_total": sum(x["maxent_maxiter_hits"] for k, x in st.items()
                                            if not k.startswith(f"n_{REF_N}/")),
           "G_maxiter_instances_total": sum(x["G_maxiter_seeds"] for k, x in st.items()
                                            if not k.startswith(f"n_{REF_N}/"))}
    (RESULTS / "verdicts.json").write_text(json.dumps(out, indent=1))
    make_figures6(st, ROOT / "figures" / "step6")
    print(json.dumps({"verdicts": v, "crossings": cr, "timing": timing,
                      "maxent_maxiter_hits_total": out["maxent_maxiter_hits_total"],
                      "G_maxiter_instances_total": out["G_maxiter_instances_total"]}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, choices=(12,) + NS_BITS)
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--projection", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true", help="table.csv, verdicts.json, figures/step6/*")
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
        cells = list(grid(APPLIED_CUT))
        print(f"grid: {len(cells)} instances, cut {APPLIED_CUT}", flush=True)
        for i, (n, sg, s) in enumerate(cells, 1):
            d = default_out(n, sg, s)
            if (d / "metrics.json").exists():
                print(f"[{i}/{len(cells)}] skip (exists) {d}", flush=True)
                continue
            out = run_instance(n, sg, s)
            write(out, d)
            print(f"[{i}/{len(cells)}] {d}  {out['total_seconds']:.1f} s  G residual "
                  f"{out['G_train_residual']:.2e}  nit {out['G_restart_nit']}", flush=True)
        print("grid done", flush=True)
        return
    if a.n is None or a.sigma is None:
        ap.error("--n and --sigma are required")
    out = run_instance(a.n, a.sigma, a.seed)
    f = write(out, Path(a.out) if a.out else default_out(a.n, a.sigma, a.seed))
    pm = out["peak_memory_bytes_process"]
    print(f)
    print(f"  n {a.n}  total {out['total_seconds']:.1f} s  G fit {out['G_fit_seconds']:.1f} s  "
          f"G params {out['G_n_params']}  G residual {out['G_train_residual']:.3e}  restarts "
          f"{['%.2e' % x for x in out['G_restart_residuals']]}  nit {out['G_restart_nit']}  "
          f"maxent residual {out['maxent_train_residual']:.2e} (nit {out['maxent_nit']})  "
          f"peak memory {pm / 2**20 if pm else float('nan'):.0f} MiB")


if __name__ == "__main__":
    main()

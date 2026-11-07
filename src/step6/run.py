"""Step 6: does the iqp4 advantage window survive larger n? (specs/step6_iqp4_scaling_n.md)

Designed after step 5 (notes/2026-11-07_step5_findings.md).

  python -m src.step6.run --n 14 --sigma 0.2 --seed 0     (one instance, N = inf)
  python -m src.step6.run --projection                     (results/step6/PROJECTION.json)
  python -m src.step6.run --all                            (refuses to start without BUDGET_OK)

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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, choices=(12,) + NS_BITS)
    ap.add_argument("--sigma", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--projection", action="store_true")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(argv)
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
        for n, sg, s in grid():
            print(write(run_instance(n, sg, s), default_out(n, sg, s)), flush=True)
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

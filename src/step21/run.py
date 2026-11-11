"""Step 21: QEC resolvability diagnostic (specs/step21_qec_resolvability.md).

  python -m src.step21.run --one RUN SPLIT | --all | --report | --verify
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1.walsh import coefficients_by_order, empirical_distribution
from src.step17.pilot import LEVELS
from src.step19 import data as D19
from src.step20 import pilot as P20
from src.step20.core import fit_and_gate

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step21"
MODELS = ROOT / "data" / "derived" / "step21"
SPEC = "specs/step21_qec_resolvability.md"
CLOSED_AT = "33712d6"
RUNS = tuple(f"surface_code_b{b}_d3_r{r}_center_{c}" for r in ("03", "05")
             for c in ("3_5", "5_3", "5_7", "7_5") for b in ("X", "Z"))
SPLITS = (100, 101)
B = 400
MAX_PAR = 12
STOP_LOSS_H = 2.0  # amendment 1 (resume of the 5 killed fits); was 4.0
n = 16
SENT = ("Step 21 is a diagnostic on 16 spent QEC runs; it adds no claim; models are step 20's procedure, "
        "unchanged.")


def out(run: str, s: int) -> Path:
    return RESULTS / run / f"split_{s}.json"


def gap_terms(fm: dict, ft: dict, N: int, levels) -> float:
    return float(np.mean([np.mean((fm[l] - ft[l]) ** 2 - (1 - ft[l] ** 2) / N) for l in levels]))


def boot_ci(fa: dict, fb: dict, rows: np.ndarray, levels, seed0: int) -> dict:
    """Point estimate and 95% percentile CI of gap(a) - gap(b) over resamples of rows (models fixed)."""
    N = len(rows)
    ft = coefficients_by_order(empirical_distribution(rows, n), n, levels)
    point = gap_terms(fa, ft, N, levels) - gap_terms(fb, ft, N, levels)
    bs = []
    for b in range(B):
        rb = rows[np.random.default_rng(seed0 + b).integers(0, N, N)]
        fb_t = coefficients_by_order(empirical_distribution(rb, n), n, levels)
        bs.append(gap_terms(fa, fb_t, N, levels) - gap_terms(fb, fb_t, N, levels))
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"point": point, "lo": float(lo), "hi": float(hi), "B": B}


def one(run: str, s: int) -> dict:
    t0 = time.time()
    idx = D19.indices(P20.qec_bits(run))[np.random.default_rng(2000 + s).permutation(D19.SHOTS)]
    tr, te = idx[:P20.N_TRAIN], idx[P20.N_TRAIN:]
    q_te = empirical_distribution(te, n)
    fg = fit_and_gate(tr, n, s, q_te)
    MODELS.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(MODELS / f"{run}_split_{s}.npz", q_g=fg["q_g"], q_me=fg["q_me"])
    from src.step17.pilot import corrected_gap
    gi, gm = corrected_gap(fg["q_g"], q_te, len(te)), corrected_gap(fg["q_me"], q_te, len(te))
    fG, fM = (coefficients_by_order(q, n, LEVELS) for q in (fg["q_g"], fg["q_me"]))
    test = boot_ci(fG, fM, te, LEVELS, 21000)
    val_rows = tr[fg["N_fit"]:]
    vG, vM = (coefficients_by_order(q, n, (4,)) for q in (fg["q_g"], fg["q_me"]))
    val = boot_ci(vG, vM, val_rows, (4,), 21000)
    cls = "loss" if test["lo"] > 0 else ("win" if test["hi"] < 0 else "unresolved")
    return {"run": run, "split": s, "R": gi["G"] / gm["G"], "dG": test, "dv4": val, "class": cls,
            "picks14": fg["picks14"], "picks_val4": fg["picks_val4"], "N_fit": fg["N_fit"], "N_val": fg["N_val"],
            "N_test": len(te), "seconds": time.time() - t0}


def run_all() -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    todo = [(r, s) for s in SPLITS for r in RUNS if not out(r, s).exists()]
    t0, ps, bad = time.time(), {}, []
    while todo or ps:
        while todo and len(ps) < MAX_PAR:
            r, s = todo.pop(0)
            ps[subprocess.Popen([sys.executable, "-m", "src.step21.run", "--one", r, str(s)], cwd=ROOT, env=env)] = (r, s)
            time.sleep(20)  # stagger start-up allocations
        time.sleep(5)
        for p in [p for p in ps if p.poll() is not None]:
            a = ps.pop(p)
            print(f"done {a} rc={p.returncode} {(time.time() - t0) / 60:.1f} min", flush=True)
            bad += [a] if p.returncode else []
        if time.time() - t0 > STOP_LOSS_H * 3600:
            print("STOP-LOSS; running:", list(ps.values()), "not started:", todo, flush=True)
            for p in ps:
                p.kill()
            return 1
    return 1 if bad else 0


def reference_R(run: str):
    """R at split 100 from step 20 (r05: results/step20, r03: results/step20/pilot)."""
    base = ROOT / "results" / "step20" / ("pilot" if "_r03_" in run else "") / run / "metrics.json"
    return json.loads(base.read_text())["R"] if base.exists() else None


def compute() -> dict:
    d = {(r, s): json.loads(out(r, s).read_text()) for r in RUNS for s in SPLITS if out(r, s).exists()}
    if len(d) < len(RUNS) * len(SPLITS):
        return {"complete": False, "have": len(d)}
    rows = []
    for r in RUNS:
        a, b = d[(r, 100)], d[(r, 101)]
        rows.append({"run": r.replace("surface_code_", ""), "R100": a["R"], "R101": b["R"], "c100": a["class"],
                     "c101": b["class"], "dG100": a["dG"], "dG101": b["dG"], "dv4_100": a["dv4"],
                     "repro": abs(a["R"] / reference_R(r) - 1)})
    D1 = sum(x["c100"] == "unresolved" for x in rows)
    D2 = sum(np.sign(x["dG100"]["point"]) == np.sign(x["dG101"]["point"]) for x in rows)
    res = [(d[(r, s)]) for r in RUNS for s in SPLITS if d[(r, s)]["class"] != "unresolved"]
    D3 = (sum(np.sign(x["dv4"]["point"]) == np.sign(x["dG"]["point"]) for x in res), len(res))
    both_loss = [x["run"] for x in rows if x["c100"] == "loss" and x["c101"] == "loss"]
    both_win = [x["run"] for x in rows if x["c100"] == "win" and x["c101"] == "win"]
    return {"complete": True, "rows": rows, "D1": int(D1), "D2": int(D2), "D3": [int(D3[0]), D3[1]],
            "resolved_loss_both": both_loss, "resolved_win_both": both_win,
            "max_repro_err": float(max(x["repro"] for x in rows)),
            "counts": {s: {c: sum(d[(r, s)]["class"] == c for r in RUNS) for c in ("win", "loss", "unresolved")}
                       for s in SPLITS}}


def report() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = compute()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2, default=str))
    L = [SENT, "", f"Spec: `{SPEC}`.", ""]
    if not c["complete"]:
        L.append(f"incomplete ({c['have']}/32)")
    else:
        L += [f"Reproduction of step 20's R at split 100: max relative error {c['max_repro_err']:.1e}.", "",
              "| ID | Quantity | Value | Pre-declared reading |", "|---|---|---|---|",
              f"| D1 | unresolved runs at split 100 | {c['D1']}/16 | {'≥ 8: QEC cannot test the claim at 5e4 shots' if c['D1'] >= 8 else '< 8: outcomes mostly resolved'} |",
              f"| D2 | ΔG sign agreement, split 100 vs 101 | {c['D2']}/16 | {'≤ 11: outcome depends on the split' if c['D2'] <= 11 else '> 11: outcome stable across splits'} |",
              f"| D3 | Δv₄ sign matches ΔG among resolved (run, split) | {c['D3'][0]}/{c['D3'][1]} | reported as is |",
              "", f"Class counts: split 100 {c['counts'][100]}; split 101 {c['counts'][101]}.",
              f"Resolved loss in both splits: {', '.join(c['resolved_loss_both']) or 'none'}.",
              f"Resolved win in both splits: {', '.join(c['resolved_win_both']) or 'none'}.", "",
              "| run | R (100) | ΔG CI (100) | class | R (101) | ΔG CI (101) | class | Δv₄ CI (100) |",
              "|---|---|---|---|---|---|---|---|"]
        f = lambda x: f"{x['point']:+.1e} [{x['lo']:+.1e}, {x['hi']:+.1e}]"
        for x in c["rows"]:
            L.append(f"| {x['run']} | {x['R100']:.3g} | {f(x['dG100'])} | {x['c100']} | {x['R101']:.3g} | "
                     f"{f(x['dG101'])} | {x['c101']} | {f(x['dv4_100'])} |")
    txt = "\n".join(L) + "\n"
    (RESULTS / "SUMMARY.md").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


def verify() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 21)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..20 unchanged since {CLOSED_AT}")
    files = [out(r, s) for r in RUNS for s in SPLITS]
    chk(all(p.exists() and json.loads(p.read_text())["dG"]["B"] == B for p in files), "grid", "32 files with B = 400")
    c = compute()
    chk(c["complete"] and c["max_repro_err"] < 1e-6, "repro", "split 100 reproduces step 20's R (< 1e-6 relative)")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT) and all(f"| D{i} |" in txt for i in (1, 2, 3)), "summary", "sentence and D1–D3 present")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step21.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 21)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", nargs=2)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.one:
        r, s = a.one[0], int(a.one[1])
        assert r in RUNS and s in SPLITS
        res = one(r, s)
        out(r, s).parent.mkdir(parents=True, exist_ok=True)
        out(r, s).write_text(json.dumps(res, indent=2))
    elif a.all:
        return run_all()
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    return 0


if __name__ == "__main__":
    sys.exit(main())

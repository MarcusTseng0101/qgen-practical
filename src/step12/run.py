"""Step 12: does the completion advantage survive on non-IQP targets? (specs/step12_nonIQP_targets.md)

  python -m src.step12.run --calibrate              (results/step12/CALIBRATION.json, seeds 0-4 only)
  python -m src.step12.run --instance lcm 16 12     (one instance)
  python -m src.step12.run --all                    (80 instances, 16 workers x 1 thread, n = 16 first, stop-loss 4 h)
  python -m src.step12.run --report                 (table.csv, verdicts.json, figure, SUMMARY.md)
  python -m src.step12.run --verify                 (acceptance check; exit 0 = done)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.versions import versions
from src.step2.sweep import kl
from src.step3.run import fit_restarts, replay_inits
from src.step4.run import training_moments
from src.step5.run import write
from src.step9 import run as r9
from src.step11.bitflip import BitflipModel
from src.step12.targets import FAMILIES

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step12"
FIGS = ROOT / "figures" / "step12"
SPEC = "specs/step12_nonIQP_targets.md"
CLOSED_AT = "438fc80"
FAMS = ("lcm", "ising4")
NS_BITS = (16, 14)
SEEDS = tuple(range(10, 30))
CAL_SEEDS = (0, 1, 2, 3, 4)
REF_CR = {14: 479.1263869626298, 16: 319.06300535336834}   # step 9 iqp4 median collision ratio
RESTARTS = 3
WORKERS = 16
STOP_LOSS_H = 4.0
WIN = 15
SENT = ("Step 12 was designed after step 11; the targets are not IQPs (`lcm` is a latent-class mixture, `ising4` a "
        "Boltzmann model with weight-4 terms), with peakedness calibrated to step 9 on seeds 0–4; G is the generic IQP "
        "(no oracle); n ≤ 16 proxies are not hardness evidence.")
IDS = {("lcm", 16): ("E1", "E2"), ("ising4", 16): ("E3", "E4"), ("lcm", 14): ("E5", "E6"), ("ising4", 14): ("E7", "E8")}


# ---------------- calibration ----------------
def median_cr(fam: str, n: int, beta: float) -> float:
    return float(np.median([M1.collision_ratio(FAMILIES[fam](beta, s, n)) for s in CAL_SEEDS]))


def calibrate() -> dict:
    out = {"procedure": "bisect log beta in [0.01, 20] until median collision ratio over seeds 0-4 is within 1% of "
                        "step 9's iqp4 median at that n", "reference": {str(k): v for k, v in REF_CR.items()}, "beta": {}}
    for fam in FAMS:
        for n in NS_BITS:
            lo, hi, ref = math.log(0.01), math.log(20.0), REF_CR[n]
            assert median_cr(fam, n, math.exp(lo)) < ref < median_cr(fam, n, math.exp(hi)), (fam, n)
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                c = median_cr(fam, n, math.exp(mid))
                if abs(c / ref - 1) <= 1e-3:
                    break
                lo, hi = (mid, hi) if c < ref else (lo, mid)
            b = math.exp(mid)
            out["beta"][f"{fam}/n_{n}"] = {"beta": b, "median_collision_ratio": c, "rel_err": c / ref - 1}
            print(fam, n, b, c)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "CALIBRATION.json").write_text(json.dumps(out, indent=2))
    return out


def beta_of(fam: str, n: int) -> float:
    return json.loads((RESULTS / "CALIBRATION.json").read_text())["beta"][f"{fam}/n_{n}"]["beta"]


# ---------------- one instance ----------------
def out_dir(fam: str, n: int, seed: int) -> Path:
    return RESULTS / fam / f"n_{n}" / f"seed_{seed}"


def run_one(fam: str, n: int, seed: int) -> Path:
    t0 = time.time()
    beta = beta_of(fam, n)
    p = FAMILIES[fam](beta, seed, n)
    fhat, ops = training_moments(p, None, seed, n)
    me = MaxEntModel(n, 3)
    me_fit = me.fit_moments(fhat, ops)
    q_me = me.prob(me_fit.params)
    G_me = M1.completion_gap(q_me, p, n)["G"]
    G_uni = M1.completion_gap(np.full(2**n, 2.0**-n), p, n)["G"]
    r = fit_restarts(IQPModel(n), fhat, ops, seed, p, n, RESTARTS)
    b = r["rows"][r["best"]]
    bf = BitflipModel(n)
    rows = []
    for th0 in replay_inits(bf.n_params, seed, RESTARTS):
        fit = bf.fit_one(th0, fhat, ops)
        rows.append({**fit, "G": M1.completion_gap(bf.prob(fit["params"]), p, n)["G"]})
    rb = int(np.argmin([x["residual"] for x in rows]))
    Gq, Gb = b["G"], rows[rb]["G"]
    out = {"family": fam, "n": n, "seed": seed, "beta": beta, "N": "inf", "versions": versions(),
           "designed_after": "step 11 (notes/2026-11-10_step11_bitflip_findings.md)",
           "p_min": float(p.min()), "p_sum_err": float(abs(p.sum() - 1)),
           "collision_ratio_target": M1.collision_ratio(p), "D3": kl(p, q_me),
           "G_iqp": Gq, "G_maxent": G_me, "G_uniform": G_uni, "G_bitflip": Gb,
           "R": Gq / G_me, "Q": Gq / Gb, "R_B": Gb / G_me,
           "G_train_residual": b["residual"], "G_best_restart": r["best"], "G_n_restarts": len(r["rows"]),
           "G_restart_residuals": [x["residual"] for x in r["rows"]], "G_restart_G": [x["G"] for x in r["rows"]],
           "G_restart_nit": [x["nit"] for x in r["rows"]], "G_restart_message": [x["message"] for x in r["rows"]],
           "bitflip_train_residual": rows[rb]["residual"], "bitflip_best": rb, "bitflip_n_restarts": len(rows),
           "bitflip_restart_residuals": [x["residual"] for x in rows], "bitflip_restart_G": [x["G"] for x in rows],
           "bitflip_restart_nit": [x["nit"] for x in rows],
           "maxent_train_residual": me_fit.train_residual, "maxent_nit": me_fit.nit, "maxent_message": me_fit.message,
           "G_best_params": [float(v) for v in b["params"]],
           "blas_threads_env": os.environ.get("OMP_NUM_THREADS"), "total_seconds": time.time() - t0}
    return write(out, out_dir(fam, n, seed))


def worker_env() -> dict:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[k] = "1"
    return env


def run_all() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda m: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n"), log.flush(), print(m, flush=True))
    todo = [(f, n, s) for n in NS_BITS for s in SEEDS for f in FAMS if not (out_dir(f, n, s) / "metrics.json").exists()]
    say(f"start: {len(todo)} jobs, {WORKERS} workers x 1 thread, stop-loss {STOP_LOSS_H} h")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            f, n, s = todo.pop(0)
            err = RESULTS / f"err_{f}_{n}_{s}.log"
            pr = subprocess.Popen([sys.executable, "-m", "src.step12.run", "--instance", f, str(n), str(s)], cwd=ROOT,
                                  env=worker_env(), stdout=subprocess.DEVNULL, stderr=open(err, "w"))
            running[pr] = ((f, n, s), time.time(), err)
            say(f"launch {f} n={n} seed={s}")
        if todo and time.time() - t0 >= STOP_LOSS_H * 3600 and not running:
            say(f"STOP-LOSS: {len(todo)} jobs not started: {todo}"); break
        time.sleep(5)
        for pr in [pr for pr in running if pr.poll() is not None]:
            job, ts, err = running.pop(pr)
            say(f"done {job} rc={pr.returncode} {(time.time() - ts) / 60:.1f} min")
            if pr.returncode != 0:
                failed.append(job)
            elif err.exists() and err.stat().st_size == 0:
                err.unlink()
    say(f"end: {(time.time() - t0) / 3600:.2f} h, failed {failed}")
    return 1 if failed else 0


# ---------------- report ----------------
def load(fam: str, n: int) -> list:
    return [json.loads((out_dir(fam, n, s) / "metrics.json").read_text()) for s in SEEDS
            if (out_dir(fam, n, s) / "metrics.json").exists()]


def spearman(a, b) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    c = {"verdicts": {}, "stats": {}}
    for (fam, n), (kr, kq) in IDS.items():
        ds = load(fam, n)
        if len(ds) < len(SEEDS):
            c["stats"][f"{fam}/n_{n}"] = {"missing": len(SEEDS) - len(ds)}
            for k in (kr, kq):
                c["verdicts"][k] = {"wins": None, "PASS": None, "family": fam, "n": n, "seeds": len(ds)}
            continue
        R = np.array([d["R"] for d in ds]); Q = np.array([d["Q"] for d in ds]); RB = np.array([d["R_B"] for d in ds])
        rg = np.array([d["G_train_residual"] for d in ds]); rb = np.array([d["bitflip_train_residual"] for d in ds])
        D3 = np.array([d["D3"] for d in ds])
        c["verdicts"][kr] = {"wins": int((R < 1).sum()), "PASS": bool((R < 1).sum() >= WIN), "family": fam, "n": n,
                             "statement": "R = G_iqp / G_maxent3 < 1"}
        c["verdicts"][kq] = {"wins": int((Q < 1).sum()), "PASS": bool((Q < 1).sum() >= WIN), "family": fam, "n": n,
                             "statement": "Q = G_iqp / G_bitflip < 1"}
        gated = np.where(rg <= 1e-2, R, 1.0)
        c["stats"][f"{fam}/n_{n}"] = {
            "R": med_iqr(R), "Q": med_iqr(Q), "R_B": med_iqr(RB), "R_B_wins": int((RB < 1).sum()),
            "iqp_resid": med_iqr(rg), "iqp_resid_gt_1e-2": int((rg > 1e-2).sum()),
            "bitflip_resid_gt_1e-2": int((rb > 1e-2).sum()), "D3": med_iqr(D3),
            "collision_ratio": med_iqr([d["collision_ratio_target"] for d in ds]),
            "spearman_R_D3": spearman(R, D3),
            "gated_wins": int((gated < 1).sum()), "gated_losses": int((gated > 1).sum()),
            "minutes_median": float(np.median([d["total_seconds"] for d in ds]) / 60)}
    return c


def make_figures(c: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for ax, n in zip(axs, NS_BITS):
        ref = [json.loads((r9.out_dir(n, s) / "metrics.json").read_text())["R"] for s in SEEDS]
        groups = [("iqp4 (step 9)", ref)] + [(f, [d["R"] for d in load(f, n)]) for f in FAMS]
        for i, (lab, R) in enumerate(groups):
            x = i + np.linspace(-0.2, 0.2, len(R)) if len(R) else []
            ax.semilogy(x, R, "o", ms=4, alpha=0.8, label=lab)
            if len(R):
                ax.plot([i - 0.3, i + 0.3], [np.median(R)] * 2, "k-", lw=1.5)
        ax.axhline(1.0, color="grey", ls="--", lw=0.8)
        ax.set_xticks(range(len(groups))); ax.set_xticklabels([g[0] for g in groups], fontsize=8)
        ax.set_title(f"n = {n}"); ax.set_ylabel("R = G_iqp / G_maxent3 (below 1: IQP wins)")
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(FIGS / f"R_by_family.{e}", dpi=150)
    plt.close(fig)


def summary(c: dict) -> str:
    v, S = c["verdicts"], c["stats"]
    L = [SENT, "", f"Spec: `{SPEC}`.", "", "| ID | Family, n | Statement | Count | Verdict |", "|---|---|---|---|---|"]
    for k in [f"E{i}" for i in range(1, 9)]:
        d = v[k]
        verdict = "**PASS**" if d["PASS"] else ("**FAIL**" if d["PASS"] is False else "not run")
        L.append(f"| {k} | {d['family']}, {d['n']} | {d.get('statement', '')} | "
                 f"{d['wins'] if d['wins'] is not None else '—'}/20 (need ≥ {WIN}) | {verdict} |")
    keys = [k for k in S if "missing" not in S[k]]
    L += ["", "## Medians [IQR] and exploratory counts", "", "| | " + " | ".join(keys) + " |",
          "|---|" + "---|" * len(keys)]
    for lab, k in [("R", "R"), ("Q", "Q"), ("R_B", "R_B"), ("bitflip beats MaxEnt(3)", "R_B_wins"),
                   ("IQP training residual", "iqp_resid"), ("IQP residual > 1e-2", "iqp_resid_gt_1e-2"),
                   ("bitflip residual > 1e-2", "bitflip_resid_gt_1e-2"), ("D3", "D3"),
                   ("collision ratio", "collision_ratio"), ("Spearman(R, D3)", "spearman_R_D3"),
                   ("residual-gated: wins / losses", None), ("median minutes per instance", "minutes_median")]:
        if k is None:
            L.append(f"| {lab} | " + " | ".join(f"{S[x]['gated_wins']} / {S[x]['gated_losses']}" for x in keys) + " |")
        else:
            L.append(f"| {lab} | " + " | ".join(f"{S[x][k]:.3g}" if isinstance(S[x][k], float) else str(S[x][k]) for x in keys) + " |")
    L += ["", "Figure: `figures/step12/R_by_family.png`.", ""]
    return "\n".join(L)


def write_table():
    keys = ["family", "n", "seed", "beta", "R", "Q", "R_B", "G_iqp", "G_maxent", "G_bitflip", "G_train_residual",
            "bitflip_train_residual", "D3", "collision_ratio_target"]
    with open(RESULTS / "table.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(keys)
        for f in FAMS:
            for n in NS_BITS:
                for d in load(f, n):
                    w.writerow([d[k] for k in keys])


def report() -> int:
    c = compute()
    write_table()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2, default=str))
    make_figures(c)
    (RESULTS / "SUMMARY.md").write_text(summary(c), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(summary(c))
    return 0


def verify() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 12)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..11 unchanged since {CLOSED_AT}")
    cf = RESULTS / "CALIBRATION.json"
    cal = json.loads(cf.read_text()) if cf.exists() else {"beta": {}}
    chk(all(abs(cal["beta"].get(f"{f}/n_{n}", {"rel_err": 1})["rel_err"]) <= 0.01 for f in FAMS for n in NS_BITS),
        "calibration", "CALIBRATION.json: each median collision ratio within 1% of step 9")
    ok, pok = True, True
    for f in FAMS:
        for n in NS_BITS:
            for s in SEEDS:
                p = out_dir(f, n, s) / "metrics.json"
                if not p.exists():
                    ok = False; print(f"     missing {p.relative_to(ROOT)}"); continue
                d = json.loads(p.read_text())
                if not (d["n"] == n and d["seed"] == s and d["beta"] == cal["beta"][f"{f}/n_{n}"]["beta"]
                        and d["G_n_restarts"] == RESTARTS and d["bitflip_n_restarts"] == RESTARTS):
                    ok = False; print(f"     bad {p.relative_to(ROOT)}")
                if not (d["p_min"] >= 0 and d["p_sum_err"] <= 1e-12):
                    pok = False
    chk(ok, "grid", "80 instances, calibrated beta, 3 G and 3 bitflip restarts")
    chk(pok, "targets", "every target p >= 0 and sums to 1 within 1e-12")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| E{i} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for i in range(1, 9)), "summary", "E1–E8 marked")
    chk(all((FIGS / f"R_by_family.{e}").exists() for e in ("png", "pdf")), "figures", "figures/step12/R_by_family")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step12.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 12)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--instance", nargs=3, metavar=("FAMILY", "N", "SEED"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.calibrate:
        calibrate()
    elif a.instance:
        f, n, s = a.instance[0], int(a.instance[1]), int(a.instance[2])
        assert f in FAMS and n in NS_BITS and s in SEEDS
        print(run_one(f, n, s))
    elif a.all:
        return run_all()
    elif a.report:
        return report()
    elif a.verify:
        return verify()
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Step 11: does the completion advantage need coherence? Bitflip control (specs/step11_bitflip_control.md).

  python -m src.step11.run --instance 16 12   (one seed)
  python -m src.step11.run --all              (40 seeds, 12 workers x 1 thread, resumable, stop-loss 2 h)
  python -m src.step11.run --report           (table.csv, verdicts.json, figure, SUMMARY.md)
  python -m src.step11.run --verify           (acceptance check; exit 0 = done)

Targets and training moments are step 9's (iqp4, level B, N = inf, seeds 10-29), rebuilt with the
same unchanged functions. G_iqp and G_maxent3 are read from results/step9 (and step 10, exploratory).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step3.run import replay_inits
from src.step4.run import training_moments
from src.step5.run import write
from src.step5.targets import iqp4_target
from src.step9 import run as r9
from src.step10 import run as r10
from src.step11.bitflip import BitflipModel

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "step11"
FIGS = ROOT / "figures" / "step11"
SPEC = "specs/step11_bitflip_control.md"
CLOSED_AT = "a7dbff9"
NS_BITS = (16, 14)
SIGMA = r9.SIGMA
SEEDS = r9.SEEDS
RESTARTS = 10
PRIMARY = 3
WORKERS = 12
STOP_LOSS_H = 2.0
WIN = 15
SENT = ("Step 11 was designed after step 10; the bitflip model is a classical, decohered twin of G with the same "
        "generators, inits and optimizer; the targets are coherent IQPs, so this tests coherence on IQP-generated "
        "data only; n ≤ 16 proxies are not hardness evidence.")


def out_dir(n: int, seed: int) -> Path:
    return RESULTS / f"n_{n}" / f"seed_{seed}"


def step9(n: int, seed: int) -> dict:
    return json.loads((r9.out_dir(n, seed) / "metrics.json").read_text())


def run_one(n: int, seed: int) -> Path:
    t0 = time.time()
    p, masks, theta, _ = iqp4_target(SIGMA[n], seed, n)
    fhat, ops = training_moments(p, None, seed, n)
    old = step9(n, seed)
    cr = M1.collision_ratio(p)
    m = BitflipModel(n)
    rows = []
    for th0 in replay_inits(m.n_params, seed, RESTARTS):
        fit = m.fit_one(th0, fhat, ops)
        q = m.prob(fit["params"])
        rows.append({**fit, "G": M1.completion_gap(q, p, n)["G"], "p_min": float(q.min()),
                     "p_sum_err": float(abs(q.sum() - 1.0))})
    res = np.array([r["residual"] for r in rows])
    b3, b10 = int(np.argmin(res[:PRIMARY])), int(np.argmin(res))
    Gb, Gme, Gq = rows[b3]["G"], old["G_maxent"], old["G_iqp"]
    out = {"n": n, "sigma": SIGMA[n], "seed": seed, "level": "B", "N": "inf", "target": "iqp4",
           "designed_after": "step 10 (notes/2026-11-10_step10_findings.md)",
           "target_match": bool(abs(cr - old["collision_ratio_target"]) <= 1e-12 * old["collision_ratio_target"]),
           "collision_ratio_target": cr, "D3": old["D3"],
           "bitflip_n_params": m.n_params, "bitflip_n_restarts": len(rows),
           "bitflip_restart_residuals": res.tolist(), "bitflip_restart_G": [r["G"] for r in rows],
           "bitflip_restart_nit": [r["nit"] for r in rows], "bitflip_restart_message": [r["message"] for r in rows],
           "bitflip_p_min": min(r["p_min"] for r in rows), "bitflip_p_sum_err_max": max(r["p_sum_err"] for r in rows),
           "bitflip_best3": b3, "bitflip_best10": b10,
           "G_bitflip": Gb, "bitflip_train_residual": rows[b3]["residual"],
           "G_bitflip_10": rows[b10]["G"], "bitflip_train_residual_10": rows[b10]["residual"],
           "G_iqp": Gq, "G_maxent": Gme, "R": old["R"], "G_train_residual": old["G_train_residual"],
           "R_B": Gb / Gme, "Q": Gq / Gb, "R_B_10": rows[b10]["G"] / Gme,
           "bitflip_best_params": [float(v) for v in rows[b3]["params"]],
           "blas_threads_env": os.environ.get("OMP_NUM_THREADS")}
    if n == 14:
        s10 = json.loads((r10.out_dir(seed) / "metrics.json").read_text())
        out["G_iqp_10"] = s10["G_iqp"]
        out["Q_10"] = s10["G_iqp"] / rows[b10]["G"]
    out["total_seconds"] = time.time() - t0
    return write(out, out_dir(n, seed))


def worker_env() -> dict:
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[k] = "1"
    return env


def run_all() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    log = open(RESULTS / "grid.log", "a", encoding="utf-8")
    say = lambda msg: (log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"), log.flush(), print(msg, flush=True))
    todo = [(n, s) for n in NS_BITS for s in SEEDS if not (out_dir(n, s) / "metrics.json").exists()]
    say(f"start: {len(todo)} jobs, {WORKERS} workers x 1 thread, stop-loss {STOP_LOSS_H} h")
    t0, running, failed = time.time(), {}, []
    while todo or running:
        while todo and len(running) < WORKERS and time.time() - t0 < STOP_LOSS_H * 3600:
            n, s = todo.pop(0)
            err = RESULTS / f"err_{n}_{s}.log"
            pr = subprocess.Popen([sys.executable, "-m", "src.step11.run", "--instance", str(n), str(s)], cwd=ROOT,
                                  env=worker_env(), stdout=subprocess.DEVNULL, stderr=open(err, "w"))
            running[pr] = ((n, s), time.time(), err)
            say(f"launch n={n} seed={s}")
        if todo and time.time() - t0 >= STOP_LOSS_H * 3600 and not running:
            say(f"STOP-LOSS: {len(todo)} jobs not started"); break
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
def load(n: int) -> list:
    return [json.loads((out_dir(n, s) / "metrics.json").read_text()) for s in SEEDS]


def spearman(a, b) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def med_iqr(x) -> str:
    q = np.percentile(x, [25, 50, 75])
    return f"{q[1]:.3g} [{q[0]:.3g}, {q[2]:.3g}]"


def compute() -> dict:
    c = {"verdicts": {}, "stats": {}}
    for n, (kq, kb) in ((16, ("C1", "C2")), (14, ("C3", "C4"))):
        ds = load(n)
        Q = np.array([d["Q"] for d in ds]); RB = np.array([d["R_B"] for d in ds]); R = np.array([d["R"] for d in ds])
        rb = np.array([d["bitflip_train_residual"] for d in ds]); rg = np.array([d["G_train_residual"] for d in ds])
        ok = (rb <= 1e-2) & (rg <= 1e-2)
        c["verdicts"][kq] = {"wins": int((Q < 1).sum()), "PASS": bool((Q < 1).sum() >= WIN), "n": n,
                             "statement": "G_iqp < G_bitflip"}
        c["verdicts"][kb] = {"wins": int((RB < 1).sum()), "PASS": bool((RB < 1).sum() >= WIN), "n": n,
                             "statement": "G_bitflip < G_maxent3"}
        st = {"Q": med_iqr(Q), "R_B": med_iqr(RB), "R": med_iqr(R), "R_wins": int((R < 1).sum()),
              "bitflip_resid": med_iqr(rb), "bitflip_resid_gt_1e-2": int((rb > 1e-2).sum()),
              "iqp_resid_gt_1e-2": int((rg > 1e-2).sum()),
              "both_fit_seeds": int(ok.sum()),
              "both_fit_Q_wins": int((Q[ok] < 1).sum()), "both_fit_R_B_wins": int((RB[ok] < 1).sum()),
              "both_fit_R_wins": int((R[ok] < 1).sum()),
              "Q_10_bitflip_wins": int((np.array([d["G_iqp"] / d["G_bitflip_10"] for d in ds]) < 1).sum()),
              "R_B_10_wins": int((np.array([d["R_B_10"] for d in ds]) < 1).sum()),
              "spearman_R_RB": spearman(R, RB),
              "p_min": float(min(d["bitflip_p_min"] for d in ds)),
              "p_sum_err_max": float(max(d["bitflip_p_sum_err_max"] for d in ds)),
              "minutes_median": float(np.median([d["total_seconds"] for d in ds]) / 60)}
        if n == 14:
            st["Q_10_wins"] = int((np.array([d["Q_10"] for d in ds]) < 1).sum())
        c["stats"][n] = st
    v = c["verdicts"]
    key = (v["C1"]["PASS"], v["C2"]["PASS"])
    c["reading"] = {(True, False): "advantage needs coherence (decohered twin lacks it)",
                    (True, True): "structure alone beats MaxEnt(3); coherence adds to it",
                    (False, True): "a classical twin reproduces the advantage: IQP-shaped bias, not a quantum effect",
                    (False, False): "neither direction supported; control uninformative"}[key]
    return c


def make_figures(c: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    FIGS.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(9, 4.2))
    for ax, n in zip(axs, NS_BITS):
        ds = load(n)
        x = np.array([d["G_bitflip"] for d in ds]); y = np.array([d["G_iqp"] for d in ds])
        me = np.array([d["G_maxent"] for d in ds])
        ax.loglog(x, y, "o", color="#3b6ea5", label="seed (G_iqp vs G_bitflip)")
        ax.loglog(x, me, "x", color="#c0504d", ms=5, label="G_maxent3 (same seed)")
        lo, hi = min(x.min(), y.min(), me.min()) / 1.5, max(x.max(), y.max(), me.max()) * 1.5
        ax.plot([lo, hi], [lo, hi], "k--", lw=0.8)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel("G_bitflip (best of 3)"); ax.set_ylabel("G_iqp (step 9) / G_maxent3")
        k = "C1" if n == 16 else "C3"
        ax.set_title(f"n = {n}: Q < 1 in {c['verdicts'][k]['wins']}/20")
        ax.legend(fontsize=7, loc="upper left")
    fig.suptitle("Below the diagonal: coherent IQP completes better than its decohered twin", fontsize=9)
    fig.tight_layout()
    for e in ("png", "pdf"):
        fig.savefig(FIGS / f"G_iqp_vs_bitflip.{e}", dpi=150)
    plt.close(fig)


def summary(c: dict) -> str:
    v, S = c["verdicts"], c["stats"]
    L = [SENT, "", f"Spec: `{SPEC}`. Reading (n = 16, spec section 3): **{c['reading']}**.", "",
         "| ID | Statement | Count | Verdict |", "|---|---|---|---|"]
    for k in ("C1", "C2", "C3", "C4"):
        L.append(f"| {k} | n = {v[k]['n']}: {v[k]['statement']} | {v[k]['wins']}/20 (need ≥ {WIN}) | "
                 f"**{'PASS' if v[k]['PASS'] else 'FAIL'}** |")
    L += ["", "## Medians [IQR] and exploratory counts", "",
          "| | n = 16 | n = 14 |", "|---|---|---|"]
    rows = [("Q = G_iqp / G_bitflip", "Q"), ("R_B = G_bitflip / G_maxent3", "R_B"), ("R = G_iqp / G_maxent3 (step 9)", "R"),
            ("R < 1 (step 9)", "R_wins"), ("bitflip training residual", "bitflip_resid"),
            ("bitflip residual > 1e-2", "bitflip_resid_gt_1e-2"), ("IQP residual > 1e-2 (step 9)", "iqp_resid_gt_1e-2"),
            ("seeds where both residuals ≤ 1e-2", "both_fit_seeds"), ("… of which Q < 1", "both_fit_Q_wins"),
            ("… of which R_B < 1", "both_fit_R_B_wins"), ("… of which R < 1", "both_fit_R_wins"),
            ("best-of-10 bitflip: R_B < 1", "R_B_10_wins"), ("G_iqp (3) < G_bitflip (best of 10)", "Q_10_bitflip_wins"),
            ("Spearman(R, R_B) across seeds", "spearman_R_RB"), ("min bitflip p", "p_min"),
            ("max |Σp − 1|", "p_sum_err_max"), ("median minutes per seed", "minutes_median")]
    fmt = lambda x: f"{x:.3g}" if isinstance(x, float) else str(x)
    for lab, k in rows:
        L.append(f"| {lab} | {fmt(S[16][k])} | {fmt(S[14][k])} |")
    L.append(f"| n = 14 only: G_iqp (10, step 10) < G_bitflip (10) | — | {S[14]['Q_10_wins']} |")
    L += ["", "Figure: `figures/step11/G_iqp_vs_bitflip.png`.", ""]
    return "\n".join(L)


def write_table():
    RESULTS.mkdir(parents=True, exist_ok=True)
    keys = ["n", "seed", "G_iqp", "G_bitflip", "G_maxent", "Q", "R_B", "R", "G_train_residual",
            "bitflip_train_residual", "G_bitflip_10", "R_B_10", "bitflip_best3", "bitflip_best10", "collision_ratio_target", "D3"]
    with open(RESULTS / "table.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(keys)
        for n in NS_BITS:
            for d in load(n):
                w.writerow([d[k] for k in keys])


def report() -> int:
    c = compute()
    write_table()
    (RESULTS / "verdicts.json").write_text(json.dumps(c, indent=2, default=str))
    make_figures(c)
    (RESULTS / "SUMMARY.md").write_text(summary(c), encoding="utf-8")
    print(summary(c))
    return 0


def verify() -> int:
    bad = []
    chk = lambda ok, name, msg: (print(("ok   " if ok else "FAIL ") + f"[{name}] {msg}"), ok or bad.append(name))
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    chk(git("ls-files", "--error-unmatch", SPEC).returncode == 0 and git("diff", "--quiet", "HEAD", "--", SPEC).returncode == 0,
        "spec", f"{SPEC} committed and unchanged")
    closed = [f"src/step{i}/" for i in range(1, 11)]
    chk(git("diff", "--name-only", CLOSED_AT, "HEAD", "--", *closed).stdout.strip() == ""
        and git("diff", "--quiet", "HEAD", "--", *closed).returncode == 0, "closed", f"src/step1..10 unchanged since {CLOSED_AT}")
    ok, pok = True, True
    for n in NS_BITS:
        for s in SEEDS:
            f = out_dir(n, s) / "metrics.json"
            if not f.exists():
                ok = False; print(f"     missing {f.relative_to(ROOT)}"); continue
            d = json.loads(f.read_text())
            if not (d["n"] == n and abs(d["sigma"] - SIGMA[n]) < 1e-12 and d["seed"] == s
                    and d["bitflip_n_restarts"] == RESTARTS and d["target_match"]):
                ok = False; print(f"     bad {f.relative_to(ROOT)}")
            if not (d["bitflip_p_min"] >= -1e-12 and d["bitflip_p_sum_err_max"] <= 1e-10):
                pok = False; print(f"     bad p {f.relative_to(ROOT)}")
    chk(ok, "grid", "40 seeds, exact σ, 10 restarts, targets match step 9")
    chk(pok, "prob", "every bitflip p ≥ −1e-12 and sums to 1 within 1e-10")
    S = RESULTS / "SUMMARY.md"
    txt = S.read_text(encoding="utf-8") if S.exists() else ""
    chk(txt.startswith(SENT), "summary", "SUMMARY opens with the required sentence")
    chk(all(re.search(rf"\| {k} \|.*\| \*\*(PASS|FAIL)\*\* \|", txt) for k in ("C1", "C2", "C3", "C4")), "summary", "C1–C4 marked")
    chk(all((FIGS / f"G_iqp_vs_bitflip.{e}").exists() for e in ("png", "pdf")), "figures", "figures/step11/G_iqp_vs_bitflip")
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step11.py"], cwd=ROOT, capture_output=True, text=True)
    chk(t.returncode == 0, "tests", (t.stdout.strip().splitlines() or ["no output"])[-1])
    print("ALL CHECKS PASS (step 11)" if not bad else f"FAILED: {sorted(set(bad))}")
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", type=int, nargs=2, metavar=("N", "SEED"))
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if a.instance:
        n, s = a.instance
        assert n in NS_BITS and s in SEEDS
        print(run_one(n, s))
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

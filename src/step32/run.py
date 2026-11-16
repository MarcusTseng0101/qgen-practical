"""Step 32 (specs/step32_coherence_gate.md): a residual coherence gate. Fit FlipIQP; if its raw-floor ratio > 1.0,
use CohIQP instead. Data, arms and fits are step 31's, unchanged (src.step31.run.run_job); only the seeds and the
results directory differ.

python -m src.step32.run --all | --job COND ARM SEED | --report | --verify
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step31 import run as R31

RESULTS = Path("results/step32")
TEST = tuple(range(1100, 1114))
THRESH = 1.0          # spec section 1: a round number read off step 31's (now spent) seeds; not tuned
NEAR = (0.8, 1.25)    # spec section 3: report ratios in this band as near-threshold
WORKERS, STOP_LOSS_H = 20, 12.0
CONDS, ARMS, LAUNCH = R31.CONDS, R31.ARMS, R31.LAUNCH


def jobs():
    return [(c, a, s) for c, a in LAUNCH for s in TEST]


def out_path(c, a, s) -> Path:
    return RESULTS / c / a / f"seed_{s}" / "metrics.json"


def run_job(cond: str, arm: str, seed: int) -> dict:
    R31.RESULTS = RESULTS          # step 31's job, unchanged, written under results/step32
    return R31.run_job(cond, arm, seed)


def launch() -> int:
    todo = [j for j in jobs() if not out_path(*j).exists()]
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0, running, log = time.time(), [], []
    RESULTS.mkdir(parents=True, exist_ok=True)
    err = open(RESULTS / "errors.log", "a")
    while todo or running:
        if time.time() - t0 > STOP_LOSS_H * 3600:
            for j, pr, _ in running:
                pr.kill()
                log.append(f"KILLED {j}")
            log.append(f"STOP-LOSS after {STOP_LOSS_H} h; unstarted: {todo}")
            break
        still = []
        for j, pr, ts in running:
            if pr.poll() is None:
                still.append((j, pr, ts))
            else:
                log.append(f"done {j} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step32.run", "--job", j[0], j[1], str(j[2])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr, time.time()))
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(c, a):
    return {s: json.loads(out_path(c, a, s).read_text()) for s in TEST if out_path(c, a, s).exists()}


def gate_record(coh: dict, flip: dict) -> dict:
    pick = "coh" if flip["ratio"] > THRESH else "flip"
    G = coh["G"] if pick == "coh" else flip["G"]
    return {"pick": pick, "G_gate": G, "G_me3": flip["G_me3"], "G_flip": flip["G"], "G_coh": coh["G"],
            "ratio_flip": flip["ratio"]}


def gated(c):
    A, B = load(c, "coh"), load(c, "flip")
    return {s: gate_record(A[s], B[s]) for s in TEST if s in A and s in B}


def verdicts() -> dict:
    CF, PF = gated("cf"), gated("pf")

    def cnt(X, f):   # missing seeds count as failures
        return sum(1 for s in TEST if s in X and f(X[s]))

    z1 = cnt(CF, lambda d: d["G_gate"] < d["G_me3"])
    z2 = cnt(CF, lambda d: d["G_gate"] < d["G_flip"])          # a flip pick is a tie, so not a win
    z3 = cnt(PF, lambda d: d["pick"] == "flip")
    z4 = cnt(PF, lambda d: d["G_gate"] < d["G_me3"])
    out = {}
    for h, w, need in (("Z1", z1, 11), ("Z2", z2, 9), ("Z3", z3, 12), ("Z4", z4, 12)):
        out[h] = {"count": w, "of": 14, "need": need, "verdict": "PASS" if w >= need else "FAIL"}
    rep = {}
    for c, X in (("cf", CF), ("pf", PF)):
        if not X:
            continue
        r = {"n": len(X), "picked_coh": int(sum(d["pick"] == "coh" for d in X.values()))}
        for k in ("gate", "coh", "flip"):
            v = [d[f"G_{k}"] / d["G_me3"] for d in X.values()]
            r[f"median_R_{k}"] = float(np.median(v))
            r[f"wins_vs_me3_{k}"] = int(sum(x < 1 for x in v))
        orc = [min(d["G_coh"], d["G_flip"]) / d["G_me3"] for d in X.values()]
        r["median_R_oracle"] = float(np.median(orc))
        r["gate_matches_oracle"] = int(sum(d["G_gate"] == min(d["G_coh"], d["G_flip"]) for d in X.values()))
        r["near_threshold"] = {str(s): d["ratio_flip"] for s, d in X.items() if NEAR[0] <= d["ratio_flip"] <= NEAR[1]}
        C = load(c, "coh")
        r["coh_restarts_at_maxiter"] = int(sum(d["restarts_at_maxiter"] for d in C.values()))
        r["coh_eps_at_bound"] = int(sum(d["eps_at_bound"] for d in C.values()))
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 32 summary", "", "| ID | result | verdict |", "|---|---|---|"]
    for h in ("Z1", "Z2", "Z3", "Z4"):
        lines.append(f"| {h} | {V[h]['count']}/14 (need {V[h]['need']}) | {V[h]['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed (R = G / G_me3)", "", "| cond | seed | ratio_flip | pick | R_gate | R_coh | R_flip |",
            "|---|---|---|---|---|---|---|"]
    for c in CONDS:
        for s, d in sorted(gated(c).items()):
            g = d["G_me3"]
            rows.append(f"| {c} | {s} | {d['ratio_flip']:.2f} | {d['pick']} | {d['G_gate'] / g:.3f} | "
                        f"{d['G_coh'] / g:.3f} | {d['G_flip'] / g:.3f} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:8]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [j for j in jobs() if not out_path(*j).exists()]
    if miss and "STOP-LOSS" not in txt:
        errs.append(f"{len(miss)} jobs missing and no stop-loss recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step32.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step32.py fails:\n" + r.stdout[-800:])
    res = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(res + "\n")
    print(res)
    return 0 if not errs else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--job", nargs=3)
    a = ap.parse_args()
    if a.job:
        run_job(a.job[0], a.job[1], int(a.job[2]))
        sys.exit(0)
    sys.exit(launch() if a.all else report() if a.report else verify() if a.verify else 2)

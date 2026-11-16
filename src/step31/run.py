"""Step 31 (specs/step31_coherent_shots.md): step 30's untied CohIQP, unchanged, at N = 1e5 on coherent data (correct
graph), with a Pauli-noise control. FlipIQP (step 26) is the given-graph comparison; MaxEnt(3) the baseline.

python -m src.step31.run --all | --job COND ARM SEED | --report | --verify
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

from src.step1 import metrics as M1
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step26 import noise as N26
from src.step26.flipiqp import LAM_LO, FlipIQP
from src.step27.run import given_graph, raw_floor
from src.step29 import noise as N29
from src.step30 import cohiqp as C30

RESULTS = Path("results/step31")
TEST = tuple(range(1080, 1094))
SPENT_BELOW = 1080
N_SHOTS, ETA, EPS_STD, P_GATE = 100_000, 0.02, 0.2, 0.01
WORKERS, STOP_LOSS_H, LEVER_H = 20, 11.0, 11.0
NB = Gd.N_BITS
CONDS = ("cf", "pf")
ARMS = ("coh", "flip")
LAUNCH = (("cf", "coh"), ("pf", "coh"), ("cf", "flip"), ("pf", "flip"))   # spec section 4 launch order


def data(cond: str, seed: int) -> np.ndarray:
    if cond == "cf":
        return N29.coherent_grid_iqp(seed, EPS_STD, ETA)
    return N26.noisy_grid_iqp(seed, P_GATE, ETA)


def jobs():
    return [(c, a, s) for c, a in LAUNCH for s in TEST]


def out_path(c, a, s) -> Path:
    return RESULTS / c / a / f"seed_{s}" / "metrics.json"


class _NitLog:
    """Records nit of every L-BFGS-B call inside step 30's CohIQP.fit (reporting only; the optimizer is unchanged)."""

    def __init__(self, fn):
        self.fn, self.nit = fn, []

    def __call__(self, *a, **k):
        r = self.fn(*a, **k)
        self.nit.append(int(r.nit))
        return r


def run_job(cond: str, arm: str, seed: int) -> dict:
    t0 = time.time()
    p = data(cond, seed)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    F = raw_floor(fhat, N_SHOTS)
    gens, _ = given_graph("full", seed)
    me = MaxEntModel(NB, 3)
    G = lambda q: M1.completion_gap(q, p, NB)["G"]
    out = {"cond": cond, "arm": arm, "seed": seed, "N": N_SHOTS, "n_gens": len(gens)}
    out["G_me3"] = G(me.prob(me.fit_moments(fhat, ops).params))
    if arm == "coh":
        log = _NitLog(C30.minimize)
        C30.minimize = log
        try:
            m = C30.CohIQP(NB, gens, tied=False).fit(fhat, ops, seed=seed)
        finally:
            C30.minimize = log.fn
        eps = m._split(m.x)[1]
        out["restart_nit"] = log.nit
        out["restarts_at_maxiter"] = int(sum(n >= C30.COH_OPTS["maxiter"] for n in log.nit))
        out["eps_at_bound"] = int(np.sum(np.abs(eps) >= C30.EPS_MAX - 1e-9))
        out["lam_min"] = float(m._split(m.x)[2].min())
    else:
        m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
        lam = m.x[m.K:]
        out["lam_median"] = float(np.median(lam))
        out["pinned"] = int(np.sum(lam <= LAM_LO + 1e-9))
    out["G"] = G(m.prob())
    out["ratio"] = m.resid / F
    out["R_me3"] = out["G"] / out["G_me3"]
    out["secs"] = time.time() - t0
    path = out_path(cond, arm, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def launch() -> int:
    todo = [j for j in jobs() if not out_path(*j).exists()]
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0, running, log, durs, lever_checked = time.time(), [], [], [], False
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
                durs.append((j[1], time.time() - ts))
                log.append(f"done {j} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        if not lever_checked and len(durs) >= WORKERS:   # spec section 7: project after the first 20 finished jobs
            lever_checked = True
            allm = float(np.mean([d for _, d in durs]))
            mean = {a: float(np.mean([d for x, d in durs if x == a])) if any(x == a for x, _ in durs) else allm
                    for a in ARMS}
            left = sum(mean[j[1]] for j in todo) + sum(max(mean[j[1]] - (time.time() - ts), 0.0)
                                                       for j, _, ts in running)
            proj = (time.time() - t0) + left / WORKERS
            log.append(f"PROJECTION {proj / 3600:.2f} h")
            if proj > LEVER_H * 3600:
                dropped = [j for j in todo if j[:2] == ("pf", "coh")]
                todo = [j for j in todo if j[:2] != ("pf", "coh")]
                log.append(f"LEVER: dropped pf coh {dropped}")
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step31.run", "--job", j[0], j[1], str(j[2])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr, time.time()))
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(c, a):
    return {s: json.loads(out_path(c, a, s).read_text()) for s in TEST if out_path(c, a, s).exists()}


def verdicts() -> dict:
    CC, CF, PC = load("cf", "coh"), load("cf", "flip"), load("pf", "coh")

    def cnt(f):   # missing seeds count as failures
        return sum(1 for s in TEST if f(s))

    y1 = cnt(lambda s: s in CC and CC[s]["G"] < CC[s]["G_me3"])
    y2 = cnt(lambda s: s in CC and s in CF and CC[s]["G"] < CF[s]["G"])
    y3 = cnt(lambda s: s in PC and PC[s]["G"] < PC[s]["G_me3"])
    out = {"Y1": {"wins": y1, "of": 14, "need": 11, "verdict": "PASS" if y1 >= 11 else "FAIL"},
           "Y2": {"wins": y2, "of": 14, "need": 10, "verdict": "PASS" if y2 >= 10 else "FAIL"},
           "Y3": {"wins": y3, "of": 14, "need": 11, "verdict": "PASS" if y3 >= 11 else "FAIL"}}
    rep = {}
    for c in CONDS:
        r = {}
        for a in ARMS:
            X = load(c, a)
            if not X:
                continue
            R = [d["R_me3"] for d in X.values()]
            rt = [d["ratio"] for d in X.values()]
            r[a] = {"n": len(X), "wins_vs_me3": int(sum(x < 1 for x in R)), "median_R": float(np.median(R)),
                    "ratio_range": [float(min(rt)), float(max(rt))],
                    "ratio_over_0.75": int(sum(x > 0.75 for x in rt))}
            if a == "coh":
                r[a]["restarts_at_maxiter"] = int(sum(d["restarts_at_maxiter"] for d in X.values()))
                r[a]["eps_at_bound"] = int(sum(d["eps_at_bound"] for d in X.values()))
            else:
                r[a]["median_lam"] = float(np.median([d["lam_median"] for d in X.values()]))
                r[a]["pinned"] = int(sum(d["pinned"] for d in X.values()))
        A, B = load(c, "coh"), load(c, "flip")
        r["coh_beats_flip"] = int(sum(1 for s in TEST if s in A and s in B and A[s]["G"] < B[s]["G"]))
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 31 summary", "", "| ID | result | verdict |", "|---|---|---|"]
    for h in ("Y1", "Y2", "Y3"):
        lines.append(f"| {h} | {V[h]['wins']}/14 (need {V[h]['need']}) | {V[h]['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed (R = G / G_me3)", "", "| cond | seed | R_coh | R_flip | ratio_coh | ratio_flip |",
            "|---|---|---|---|---|---|"]
    for c in CONDS:
        A, B = load(c, "coh"), load(c, "flip")
        for s in TEST:
            def f(X, k):
                return f"{X[s][k]:.3f}" if s in X else "-"
            rows.append(f"| {c} | {s} | {f(A, 'R_me3')} | {f(B, 'R_me3')} | {f(A, 'ratio')} | {f(B, 'ratio')} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:7]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [j for j in jobs() if not out_path(*j).exists()]
    lever_ok = "LEVER" in txt and all(j[:2] == ("pf", "coh") for j in miss)
    if miss and "STOP-LOSS" not in txt and not lever_ok:
        errs.append(f"{len(miss)} jobs missing and no stop-loss or lever recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step31.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step31.py fails:\n" + r.stdout[-800:])
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

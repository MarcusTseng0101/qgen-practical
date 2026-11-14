"""Step 26 (specs/step26_gate_noise.md): FlipIQP vs step 25 pipeline vs MaxEnt on gate-noisy grid data.

python -m src.step26.run --all | --job COND SEED | --report | --verify
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
from src.step25 import run as P25
from src.step26 import noise as Nz
from src.step26.flipiqp import LAM_LO, FlipIQP

RESULTS = Path("results/step26")
TEST = tuple(range(1000, 1014))
N_SHOTS, ETA = 10_000, 0.02
WORKERS, STOP_LOSS_H, LEVER_H = 8, 6.0, 6.0
NB = Gd.N_BITS
CONDS = {"g01": 0.01, "g005": 0.005, "g02": 0.02}   # launch order: primary first, report-only last


def jobs():
    return [(c, s) for c in CONDS for s in TEST]


def out_path(c, s) -> Path:
    return RESULTS / c / f"seed_{s}" / "metrics.json"


def run_job(cond: str, seed: int) -> dict:
    t0 = time.time()
    p = Nz.noisy_grid_iqp(seed, CONDS[cond], ETA)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    out = {"cond": cond, "seed": seed, "p_gate": CONDS[cond]}
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, Gd.LOCAL_ME))):
        out[f"G_{name}"] = M1.completion_gap(mdl.prob(mdl.fit_moments(fhat, ops).params), p, NB)["G"]
    r = P25.pipeline(fhat, ops, ETA, N_SHOTS, Gd.LOCAL_GENS, seed)
    out["G_pipe"] = M1.completion_gap(r["q"], p, NB)["G"]
    out["pipe_flag"], out["pipe_ratio1"] = r["flag"], r["ratio1"]
    m = FlipIQP(NB, Gd.LOCAL_GENS).fit(fhat, ops, seed=seed)
    out["G_flip"] = M1.completion_gap(m.prob(), p, NB)["G"]
    lam = m.x[m.K:]
    out["lam"] = lam.tolist()
    out["lam_pinned"] = int(np.sum(lam <= LAM_LO + 1e-9))
    out["flip_resid_over_floor"] = m.resid / float(np.sum(1 - fhat**2) / N_SHOTS)
    for a in ("flip", "pipe"):
        out[f"R_{a}_me3"] = out[f"G_{a}"] / out["G_me3"]
        out[f"R_{a}_me_local"] = out[f"G_{a}"] / out["G_me_local"]
    out["secs"] = time.time() - t0
    path = out_path(cond, seed)
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
            for j, pr in running:
                pr.kill()
                log.append(f"KILLED {j}")
            log.append(f"STOP-LOSS after {STOP_LOSS_H} h; unstarted: {todo}")
            break
        still = []
        for j, pr, ts in running:
            if pr.poll() is None:
                still.append((j, pr, ts))
            else:
                durs.append(time.time() - ts)
                log.append(f"done {j} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        if not lever_checked and len(durs) >= WORKERS:   # spec §7: project after the first 8 jobs
            lever_checked = True
            left = len(todo) + len(running)
            proj = (time.time() - t0) + np.mean(durs) * left / WORKERS
            log.append(f"PROJECTION {proj / 3600:.2f} h")
            if proj > LEVER_H * 3600:
                dropped = [j for j in todo if j[0] == "g02"]
                todo = [j for j in todo if j[0] != "g02"]
                log.append(f"LEVER: dropped g02 {dropped}")
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step26.run", "--job", j[0], str(j[1])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr, time.time()))
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(c):
    return {s: json.loads(out_path(c, s).read_text()) for s in TEST if out_path(c, s).exists()}


def verdicts() -> dict:
    A, B = load("g01"), load("g005")

    def cnt(X, f):   # missing seeds count as failures
        return sum(1 for s in TEST if s in X and f(X[s]))

    H = {"G1": cnt(A, lambda d: d["R_flip_me3"] < 1), "G2": cnt(B, lambda d: d["R_flip_me3"] < 1),
         "G3": cnt(A, lambda d: d["G_flip"] < d["G_pipe"])}
    out = {h: {"wins": w, "of": 14, "need": 11, "verdict": "PASS" if w >= 11 else "FAIL"} for h, w in H.items()}
    rep = {}
    for c in CONDS:
        X = load(c)
        if not X:
            continue
        r = {"n": len(X)}
        for k in ("R_flip_me3", "R_pipe_me3", "R_flip_me_local", "R_pipe_me_local"):
            v = [d[k] for d in X.values()]
            r[f"median_{k}"] = float(np.median(v))
            r[f"wins_{k}"] = int(sum(x < 1 for x in v))
        r["flip_beats_pipe"] = int(sum(d["G_flip"] < d["G_pipe"] for d in X.values()))
        r["pipe_flags"] = int(sum(d["pipe_flag"] for d in X.values()))
        r["lam_pinned_total"] = int(sum(d["lam_pinned"] for d in X.values()))
        r["median_lam"] = float(np.median([np.median(d["lam"]) for d in X.values()]))
        r["median_flip_resid_over_floor"] = float(np.median([d["flip_resid_over_floor"] for d in X.values()]))
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 26 summary", "", "| ID | wins | need | verdict |", "|---|---|---|---|"]
    lines += [f"| {h} | {V[h]['wins']}/14 | 11 | {V[h]['verdict']} |" for h in ("G1", "G2", "G3")]
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed", "", "| cond | seed | R_flip_me3 | R_pipe_me3 | flag | pinned | R_flip_me_local |",
            "|---|---|---|---|---|---|---|"]
    for c, s in jobs():
        if out_path(c, s).exists():
            d = json.loads(out_path(c, s).read_text())
            rows.append(f"| {c} | {s} | {d['R_flip_me3']:.3f} | {d['R_pipe_me3']:.3f} | {d['pipe_flag']} | "
                        f"{d['lam_pinned']} | {d['R_flip_me_local']:.3f} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:7]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [j for j in jobs() if not out_path(*j).exists()]
    lever_ok = "LEVER" in txt and all(j[0] == "g02" for j in miss)
    if miss and "STOP-LOSS" not in txt and not lever_ok:
        errs.append(f"{len(miss)} jobs missing and no stop-loss or lever recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step26.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step26.py fails:\n" + r.stdout[-800:])
    res = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(res + "\n")
    print(res)
    return 0 if not errs else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--job", nargs=2)
    a = ap.parse_args()
    if a.job:
        run_job(a.job[0], int(a.job[1]))
        sys.exit(0)
    sys.exit(launch() if a.all else report() if a.report else verify() if a.verify else 2)

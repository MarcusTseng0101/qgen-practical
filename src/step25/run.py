"""Step 25 (specs/step25_pipeline.md): mitigation + residual check + geometric graph enlargement.

python -m src.step25.run --all | --job COND SEED | --report | --verify
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
from src.step1.bits import popcount
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step23.run import LOCAL_INIT, LOCAL_RESTARTS
from src.step24 import conds as C24

RESULTS = Path("results/step25")
TEST = tuple(range(980, 994))
N_SHOTS = 10_000
THRESH = 0.9                     # spec §2: chosen on spent step 24 data; a guess
WORKERS, STOP_LOSS_H = 8, 5.0
NB = Gd.N_BITS
CONDS = {"miss02": ("miss", 0.02), "full02": ("full", 0.02), "miss05": ("miss", 0.05)}
ENLARGED = np.array(sorted(set(Gd.LOCAL_GENS.tolist()) | set(C24.DIAG_MASKS.tolist())), dtype=np.int64)   # 103


def given_graph(kind: str, seed: int):
    """(iqp candidates, me_local masks) the user is given."""
    if kind == "miss":
        return C24.model_masks("miss", seed)
    return Gd.LOCAL_GENS, Gd.LOCAL_ME


def mitigated_floor(fhat, ops, eta, N) -> float:
    return float(np.sum((1 - fhat**2) / N / (1 - 2 * eta) ** (2 * popcount(np.asarray(ops, dtype=np.int64)))))


def pipeline(fhat, ops, eta, N, gens, seed, restarts=LOCAL_RESTARTS, theta0=None) -> dict:
    """Steps 1-4 of spec §2. Returns the scored q, the first-stage q and the diagnostics."""
    ft = C24.mitigate(fhat, ops, eta)
    F = mitigated_floor(fhat, ops, eta, N) if N else 0.0
    m = IQPModel(NB, gens=gens)
    f = m.fit_moments(ft, ops, seed=seed, n_restarts=restarts, init_std=LOCAL_INIT, theta0=theta0)
    q1 = C24.readout_channel(m.prob(f.params), eta)
    r1 = f.train_residual / F if F else 0.0
    out = {"resid1": f.train_residual, "floor_mitig": F, "ratio1": r1, "flag": bool(r1 > THRESH), "q1": q1, "q": q1}
    if out["flag"]:
        m2 = IQPModel(NB, gens=ENLARGED)
        f2 = m2.fit_moments(ft, ops, seed=seed, n_restarts=restarts, init_std=LOCAL_INIT)
        out["q"] = C24.readout_channel(m2.prob(f2.params), eta)
        out["resid2"] = f2.train_residual
        out["ratio2"] = f2.train_residual / F
    return out


def jobs():
    return [(c, s) for c in CONDS for s in TEST]


def out_path(c, s) -> Path:
    return RESULTS / c / f"seed_{s}" / "metrics.json"


def run_job(cond: str, seed: int) -> dict:
    t0 = time.time()
    kind, eta = CONDS[cond]
    p = C24.readout_channel(Gd.grid_iqp(seed), eta)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    gens, me_masks = given_graph(kind, seed)
    out = {"cond": cond, "seed": seed, "eta": eta, "n_gens": len(gens)}
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, me_masks))):
        f = mdl.fit_moments(fhat, ops)
        out[f"G_{name}"] = M1.completion_gap(mdl.prob(f.params), p, NB)["G"]
    r = pipeline(fhat, ops, eta, N_SHOTS, gens, seed)
    out["G_pipe"] = M1.completion_gap(r["q"], p, NB)["G"]
    out["G_stage1"] = M1.completion_gap(r["q1"], p, NB)["G"]
    out.update({k: v for k, v in r.items() if k not in ("q", "q1")})
    out["R_me3"] = out["G_pipe"] / out["G_me3"]
    out["R_me_local"] = out["G_pipe"] / out["G_me_local"]
    out["R_stage1_me3"] = out["G_stage1"] / out["G_me3"]
    out["secs"] = time.time() - t0
    path = out_path(cond, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def launch() -> int:
    todo = [j for j in jobs() if not out_path(*j).exists()]
    todo.sort(key=lambda j: j[0] == "full02")   # miss jobs (2 fits) first
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0, running, log = time.time(), [], []
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
        for j, pr in running:
            if pr.poll() is None:
                still.append((j, pr))
            else:
                log.append(f"done {j} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step25.run", "--job", j[0], str(j[1])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr))
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(c):
    return {s: json.loads(out_path(c, s).read_text()) for s in TEST if out_path(c, s).exists()}


def verdicts() -> dict:
    A, B, D = load("miss02"), load("full02"), load("miss05")

    def wins(X):   # missing seeds count as failures
        return sum(1 for s in TEST if s in X and X[s]["R_me3"] < 1)

    fa = sum(1 for s in TEST if s in A and A[s]["flag"])
    fb = sum(1 for s in TEST if s not in B or B[s]["flag"])   # missing control seeds count against P3
    out = {
        "P1": {"wins": wins(A), "need": 11},
        "P2": {"wins": wins(B), "need": 11},
        "P3": {"flag_miss02": fa, "need_miss": 12, "flag_full02": fb, "max_full": 2},
        "P4": {"wins": wins(D), "need": 11},
    }
    for h in ("P1", "P2", "P4"):
        out[h]["verdict"] = "PASS" if out[h]["wins"] >= out[h]["need"] else "FAIL"
    out["P3"]["verdict"] = "PASS" if fa >= 12 and fb <= 2 else "FAIL"
    rep = {}
    for c in CONDS:
        X = load(c)
        if not X:
            continue
        r = {"n": len(X), "flags": int(sum(d["flag"] for d in X.values()))}
        for k in ("R_me3", "R_me_local", "R_stage1_me3"):
            v = [d[k] for d in X.values()]
            r[f"median_{k}"] = float(np.median(v))
            r[f"wins_{k}"] = int(sum(x < 1 for x in v))
        r["ratio1"] = sorted(round(d["ratio1"], 3) for d in X.values())
        r["ratio2"] = sorted(round(d["ratio2"], 3) for d in X.values() if "ratio2" in d)
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 25 summary", "", "| ID | result | verdict |", "|---|---|---|"]
    for h in ("P1", "P2", "P4"):
        lines.append(f"| {h} | {V[h]['wins']}/14 (need {V[h]['need']}) | {V[h]['verdict']} |")
    lines.append(f"| P3 | flagged miss02 {V['P3']['flag_miss02']}/14 (need >=12), full02 {V['P3']['flag_full02']}/14 "
                 f"(max 2) | {V['P3']['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed", "", "| cond | seed | ratio1 | flag | R_me3 | R_stage1_me3 | R_me_local |",
            "|---|---|---|---|---|---|---|"]
    for c, s in jobs():
        if out_path(c, s).exists():
            d = json.loads(out_path(c, s).read_text())
            rows.append(f"| {c} | {s} | {d['ratio1']:.2f} | {d['flag']} | {d['R_me3']:.3f} | {d['R_stage1_me3']:.3f} "
                        f"| {d['R_me_local']:.3f} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:8]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    stop = log.exists() and "STOP-LOSS" in log.read_text()
    miss = [j for j in jobs() if not out_path(*j).exists()]
    if miss and not stop:
        errs.append(f"{len(miss)} jobs missing and no stop-loss recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step25.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step25.py fails:\n" + r.stdout[-800:])
    txt = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(txt + "\n")
    print(txt)
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

"""Step 24 (specs/step24_robustness.md): local IQP under missing couplers, extra candidates and readout noise.

python -m src.step24.run --all              launch every missing job (8 workers, 5 h stop-loss)
python -m src.step24.run --job COND SEED    one job
python -m src.step24.run --report           verdicts.json + SUMMARY.md
python -m src.step24.run --verify           definition of done (exit 0)
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
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd
from src.step23.run import LOCAL_INIT, LOCAL_RESTARTS
from src.step24 import conds as C

RESULTS = Path("results/step24")
TEST = tuple(range(960, 974))
N_SHOTS = 10_000
WORKERS, STOP_LOSS_H = 8, 5.0
NB = Gd.N_BITS
HYP = {"M1": "miss", "E1": "extra", "D1": "noise02"}


def jobs():
    return [(c, s) for c in C.CONDS for s in TEST]


def out_path(c, s) -> Path:
    return RESULTS / c / f"seed_{s}" / "metrics.json"


def run_job(cond: str, seed: int) -> dict:
    t0 = time.time()
    p = C.data_dist(cond, seed)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    gens, me_masks = C.model_masks(cond, seed)
    out = {"cond": cond, "seed": seed, "n_gens": len(gens), "n_me_local": len(me_masks)}
    if cond == "miss":
        out["dropped"] = C.dropped_edges(seed)
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, me_masks))):
        f = mdl.fit_moments(fhat, ops)
        out[f"G_{name}"] = M1.completion_gap(mdl.prob(f.params), p, NB)["G"]
        out[f"resid_{name}"] = f.train_residual
    arms = [("iqp_local", fhat, None)]
    if cond == "noise02":
        arms.append(("iqp_mitig", C.mitigate(fhat, ops, C.ETA[cond]), C.ETA[cond]))
    for name, ft, eta in arms:
        m = IQPModel(NB, gens=gens)
        f = m.fit_moments(ft, ops, seed=seed, n_restarts=LOCAL_RESTARTS, init_std=LOCAL_INIT)
        q = m.prob(f.params)
        if eta is not None:
            q = C.readout_channel(q, eta)
        out[f"G_{name}"] = M1.completion_gap(q, p, NB)["G"]
        out[f"resid_{name}"] = f.train_residual
        out[f"restart_resid_{name}"] = f.restart_residuals
    out["floor"] = float(np.sum(1 - fhat**2) / N_SHOTS)
    out["R_me3"] = out["G_iqp_local"] / out["G_me3"]
    out["R_me_local"] = out["G_iqp_local"] / out["G_me_local"]
    if "G_iqp_mitig" in out:
        out["R_mitig_me3"] = out["G_iqp_mitig"] / out["G_me3"]
    out["secs"] = time.time() - t0
    path = out_path(cond, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def launch() -> int:
    todo = [j for j in jobs() if not out_path(*j).exists()]
    todo.sort(key=lambda j: j[0] != "noise02")   # longest jobs (2 IQP fits) first
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
            pr = subprocess.Popen([sys.executable, "-m", "src.step24.run", "--job", j[0], str(j[1])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr))
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(c):
    return {s: json.loads(out_path(c, s).read_text()) for s in TEST if out_path(c, s).exists()}


def verdicts() -> dict:
    out = {}
    for h, c in HYP.items():   # missing seeds count as failures (spec §6)
        D = load(c)
        w = sum(1 for s in TEST if s in D and D[s]["R_me3"] < 1)
        out[h] = {"cond": c, "wins": w, "of": len(TEST), "need": 11, "verdict": "PASS" if w >= 11 else "FAIL"}
    rep = {}
    for c in C.CONDS:
        D = load(c)
        if not D:
            continue
        r = {"n": len(D)}
        for k in ("R_me3", "R_me_local", "R_mitig_me3"):
            v = [d[k] for d in D.values() if k in d]
            if v:
                r[f"median_{k}"] = float(np.median(v))
                r[f"wins_{k}"] = int(sum(x < 1 for x in v))
        if c == "noise02":
            v = [d["G_iqp_mitig"] / d["G_iqp_local"] for d in D.values()]
            r["median_mitig_over_local"] = float(np.median(v))
            r["wins_mitig_over_local"] = int(sum(x < 1 for x in v))
        r["median_resid_over_floor"] = float(np.median([d["resid_iqp_local"] / d["floor"] for d in D.values()]))
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 24 summary", "", "| ID | cond | wins | need | verdict |", "|---|---|---|---|---|"]
    lines += [f"| {h} | {V[h]['cond']} | {V[h]['wins']}/{V[h]['of']} | {V[h]['need']} | {V[h]['verdict']} |" for h in HYP]
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed", "", "| cond | seed | n_gens | R_me3 | R_me_local | R_mitig_me3 |", "|---|---|---|---|---|---|"]
    for c, s in jobs():
        if out_path(c, s).exists():
            d = json.loads(out_path(c, s).read_text())
            rm = f"{d['R_mitig_me3']:.3f}" if "R_mitig_me3" in d else ""
            rows.append(f"| {c} | {s} | {d['n_gens']} | {d['R_me3']:.3f} | {d['R_me_local']:.3f} | {rm} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:7]))
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
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step24.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step24.py fails:\n" + r.stdout[-800:])
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

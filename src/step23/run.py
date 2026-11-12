"""Step 23 (specs/step23_local_iqp.md): local IQP vs MaxEnt(3) and MaxEnt-on-graph on 4x4-grid data.

python -m src.step23.run --all              launch every missing job (8 workers, 5 h stop-loss)
python -m src.step23.run --job SET N SEED   one job (N = inf allowed)
python -m src.step23.run --report           verdicts.json + SUMMARY.md
python -m src.step23.run --verify           definition of done (exit 0)
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

RESULTS = Path("results/step23")
TEST = tuple(range(920, 934))
SAFE = tuple(range(940, 954))
LOCAL_RESTARTS, LOCAL_INIT = 20, 0.3   # chosen on dev seeds 900-903 (spec §2); guesses
WORKERS, STOP_LOSS_H = 8, 5.0
N_BITS = Gd.N_BITS


def jobs():
    out = []
    for N in ("10000", "100000", "inf"):
        out += [("grid_iqp", N, s) for s in TEST]
    out += [("grid_ising", "10000", s) for s in SAFE]
    return out


def out_path(st, N, s) -> Path:
    return RESULTS / st / f"N_{N}" / f"seed_{s}" / "metrics.json"


def run_job(st: str, N: str, seed: int) -> dict:
    t0 = time.time()
    p = Gd.grid_iqp(seed) if st == "grid_iqp" else Gd.grid_ising(seed)
    Nn = None if N == "inf" else int(N)
    fhat, ops = training_moments(p, Nn, seed, N_BITS)
    out = {"set": st, "N": N, "seed": seed}
    for name, mdl in (("me3", MaxEntModel(N_BITS, 3)), ("me_local", Gd.MaxEntOn(N_BITS, Gd.LOCAL_ME))):
        f = mdl.fit_moments(fhat, ops)
        out[f"G_{name}"] = M1.completion_gap(mdl.prob(f.params), p, N_BITS)["G"]
        out[f"resid_{name}"] = f.train_residual
    arms = [("iqp_local", dict(gens=Gd.LOCAL_GENS), dict(n_restarts=LOCAL_RESTARTS, init_std=LOCAL_INIT))]
    if st == "grid_iqp" and N == "10000":
        arms.append(("iqp_generic", {}, dict(n_restarts=3)))
    for name, kw, fk in arms:
        m = IQPModel(N_BITS, **kw)
        f = m.fit_moments(fhat, ops, seed=seed, **fk)
        out[f"G_{name}"] = M1.completion_gap(m.prob(f.params), p, N_BITS)["G"]
        out[f"resid_{name}"] = f.train_residual
        out[f"restart_resid_{name}"] = f.restart_residuals
        out[f"n_params_{name}"] = m.n_params
    out["floor"] = float(np.sum(1 - fhat**2) / Nn) if Nn else 0.0
    out["R_me3"] = out["G_iqp_local"] / out["G_me3"]
    out["R_me_local"] = out["G_iqp_local"] / out["G_me_local"]
    out["secs"] = time.time() - t0
    path = out_path(st, N, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def launch() -> int:
    todo = [j for j in jobs() if not out_path(*j).exists()]
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
            pr = subprocess.Popen([sys.executable, "-m", "src.step23.run", "--job", j[0], j[1], str(j[2])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr))
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def load(st, N, seeds):
    return {s: json.loads(out_path(st, N, s).read_text()) for s in seeds if out_path(st, N, s).exists()}


def verdicts() -> dict:
    a = load("grid_iqp", "10000", TEST)
    b = load("grid_iqp", "100000", TEST)

    def cnt(D, f):   # missing seeds count as failures (spec §6)
        return sum(1 for s in TEST if s in D and f(D[s]))

    H = {
        "H1": (cnt(a, lambda d: d["R_me3"] < 1), 11),
        "H2": (cnt(a, lambda d: d["R_me_local"] < 1), 13),
        "H3": (cnt(b, lambda d: d["R_me3"] < 1), 11),
        "H4": (cnt(a, lambda d: d["G_iqp_local"] < d["G_iqp_generic"]), 11),
    }
    out = {k: {"wins": w, "of": len(TEST), "need": need, "verdict": "PASS" if w >= need else "FAIL"}
           for k, (w, need) in H.items()}
    rep = {}
    for st, N, seeds in (("grid_iqp", "10000", TEST), ("grid_iqp", "100000", TEST), ("grid_iqp", "inf", TEST),
                         ("grid_ising", "10000", SAFE)):
        D = load(st, N, seeds)
        if not D:
            continue
        r = {"n": len(D)}
        for k in ("R_me3", "R_me_local"):
            v = [d[k] for d in D.values()]
            r[f"median_{k}"] = float(np.median(v))
            r[f"wins_{k}"] = int(sum(x < 1 for x in v))
        if N == "10000" and st == "grid_iqp":
            v = [d["G_iqp_generic"] / d["G_me3"] for d in D.values()]
            r["median_R_generic_me3"] = float(np.median(v))
            r["wins_generic_me3"] = int(sum(x < 1 for x in v))
        if N != "inf":
            r["median_resid_over_floor"] = float(np.median([d["resid_iqp_local"] / d["floor"] for d in D.values()]))
        rep[f"{st}/N_{N}"] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 23 summary", "", "| ID | wins | need | verdict |", "|---|---|---|---|"]
    lines += [f"| {k} | {V[k]['wins']}/{V[k]['of']} | {V[k]['need']} | {V[k]['verdict']} |" for k in ("H1", "H2", "H3", "H4")]
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed", "", "| set | N | seed | R_me3 | R_me_local | R_generic_me3 |", "|---|---|---|---|---|---|"]
    for st, N, s in jobs():
        if out_path(st, N, s).exists():
            d = json.loads(out_path(st, N, s).read_text())
            rg = f"{d['G_iqp_generic'] / d['G_me3']:.3f}" if "G_iqp_generic" in d else ""
            rows.append(f"| {st} | {N} | {s} | {d['R_me3']:.3f} | {d['R_me_local']:.3f} | {rg} |")
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
    if len(Gd.TARGET_GENS) != 49 or len(Gd.LOCAL_GENS) != 85 or len(Gd.LOCAL_ME) != 76:
        errs.append("grid mask counts wrong")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step23.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step23.py fails:\n" + r.stdout[-800:])
    txt = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(txt + "\n")
    print(txt)
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

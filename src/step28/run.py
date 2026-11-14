"""Step 28 (specs/step28_correlated.md): the unchanged step 27 recipe on correlated gate noise.

python -m src.step28.run --all | --job COND SEED | --report | --verify
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
from src.step25.run import ENLARGED
from src.step26.flipiqp import LAM_LO, FlipIQP
from src.step27.run import THRESH, flow_choice, given_graph, raw_floor   # recipe imported unchanged (spec section 2)
from src.step28 import noise as Nz

RESULTS = Path("results/step28")
TEST = tuple(range(1040, 1054))
SPENT_BELOW = 1034
N_SHOTS, ETA = 10_000, 0.02
WORKERS, STOP_LOSS_H, LEVER_H = 12, 7.0, 7.0
NB = Gd.N_BITS
CONDS = {"cm01": ("miss", 0.01), "cf01": ("full", 0.01), "cm02": ("miss", 0.02)}   # launch order


def jobs():
    return [(c, s) for c in CONDS for s in TEST]


def out_path(c, s) -> Path:
    return RESULTS / c / f"seed_{s}" / "metrics.json"


def run_job(cond: str, seed: int) -> dict:
    t0 = time.time()
    kind, pg = CONDS[cond]
    p = Nz.correlated_grid_iqp(seed, pg, ETA)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    F = raw_floor(fhat, N_SHOTS)
    gens, me_masks = given_graph(kind, seed)
    out = {"cond": cond, "seed": seed, "p_gate": pg, "n_gens": len(gens)}
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, me_masks))):
        out[f"G_{name}"] = M1.completion_gap(mdl.prob(mdl.fit_moments(fhat, ops).params), p, NB)["G"]
    for name, g in (("given", gens), ("enl", ENLARGED)):
        m = FlipIQP(NB, g).fit(fhat, ops, seed=seed)
        lam = m.x[m.K:]
        out[f"G_{name}"] = M1.completion_gap(m.prob(), p, NB)["G"]
        out[f"ratio_{name}"] = m.resid / F
        out[f"lam_{name}"] = lam.tolist()
        out[f"pinned_{name}"] = int(np.sum(lam <= LAM_LO + 1e-9))
    out["flow_pick"] = flow_choice(out["ratio_given"])
    out["flag"] = out["flow_pick"] == "enl"
    out["G_flow"] = out[f"G_{out['flow_pick']}"]
    for a in ("flow", "given", "enl"):
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
                durs.append(time.time() - ts)
                log.append(f"done {j} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        if not lever_checked and len(durs) >= WORKERS:   # spec section 7: project after the first 12 jobs
            lever_checked = True
            left = len(todo) + len(running)
            proj = (time.time() - t0) + np.mean(durs) * left / WORKERS
            log.append(f"PROJECTION {proj / 3600:.2f} h")
            if proj > LEVER_H * 3600:
                dropped = [j for j in todo if j[0] == "cm02"]
                todo = [j for j in todo if j[0] != "cm02"]
                log.append(f"LEVER: dropped cm02 {dropped}")
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step28.run", "--job", j[0], str(j[1])], env=env,
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
    M, F, M2 = load("cm01"), load("cf01"), load("cm02")

    def cnt(X, f):   # missing seeds count as failures
        return sum(1 for s in TEST if s in X and f(X[s]))

    def win(d):
        return d["G_flow"] < d["G_me3"]

    out = {}
    for h, w in (("C1", cnt(M, win)), ("C2", cnt(F, win)), ("C4", cnt(M2, win))):
        out[h] = {"wins": w, "of": 14, "need": 11, "verdict": "PASS" if w >= 11 else "FAIL"}
    fl = int(sum(d["flag"] for d in F.values()))
    out["C3"] = {"flags": fl, "of": len(F), "max": 2, "verdict": "PASS" if len(F) == 14 and fl <= 2 else "FAIL"}
    rep = {}
    for c in CONDS:
        X = load(c)
        if not X:
            continue
        r = {"n": len(X)}
        for a in ("flow", "given", "enl"):
            for b in ("me3", "me_local"):
                v = [d[f"R_{a}_{b}"] for d in X.values()]
                r[f"median_R_{a}_{b}"] = float(np.median(v))
                r[f"wins_R_{a}_{b}"] = int(sum(x < 1 for x in v))
        r["flags"] = int(sum(d["flag"] for d in X.values()))
        r["missed_alarms"] = int(sum((not d["flag"]) and d["G_given"] > d["G_me3"] for d in X.values()))
        r["flow_beats_given"] = int(sum(d["G_flow"] < d["G_given"] for d in X.values()))
        r["pinned_given"] = int(sum(d["pinned_given"] for d in X.values()))
        r["pinned_enl"] = int(sum(d["pinned_enl"] for d in X.values()))
        r["median_lam_given"] = float(np.median([np.median(d["lam_given"]) for d in X.values()]))
        rg = [d["ratio_given"] for d in X.values()]
        re_ = [d["ratio_enl"] for d in X.values()]
        r["ratio_given_range"] = [float(min(rg)), float(max(rg))]
        r["ratio_enl_range"] = [float(min(re_)), float(max(re_))]
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 28 summary", "", "| ID | result | verdict |", "|---|---|---|"]
    for h in ("C1", "C2", "C4"):
        lines.append(f"| {h} | {V[h]['wins']}/14 (need 11) | {V[h]['verdict']} |")
    lines.append(f"| C3 | flags {V['C3']['flags']}/{V['C3']['of']} (max 2) | {V['C3']['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed", "", "| cond | seed | ratio_given | flag | R_flow | R_given | R_enl |",
            "|---|---|---|---|---|---|---|"]
    for c, s in jobs():
        if out_path(c, s).exists():
            d = json.loads(out_path(c, s).read_text())
            rows.append(f"| {c} | {s} | {d['ratio_given']:.2f} | {d['flag']} | {d['R_flow_me3']:.3f} | "
                        f"{d['R_given_me3']:.3f} | {d['R_enl_me3']:.3f} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:8]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [j for j in jobs() if not out_path(*j).exists()]
    lever_ok = "LEVER" in txt and all(j[0] == "cm02" for j in miss)
    if miss and "STOP-LOSS" not in txt and not lever_ok:
        errs.append(f"{len(miss)} jobs missing and no stop-loss or lever recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step28.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step28.py fails:\n" + r.stdout[-800:])
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

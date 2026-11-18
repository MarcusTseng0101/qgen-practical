"""Step 37 (specs/step37_wrong_graph_recipe.md): a wrong-graph alarm (FlipIQP ratio drop given -> ENLARGED > 2.0)
followed by step 32b's coherence gate (FlipIQP ratio > 1.0 on the chosen graph -> CohIQP), at N = 1e5.
Data are step 31's; the fits are step 31's run_job fits with the graph as an argument.

python -m src.step37.run --all | --job COND ARM GRAPH SEED | --report | --verify
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
from src.step25.run import ENLARGED
from src.step26.flipiqp import LAM_LO, FlipIQP
from src.step27.run import given_graph, raw_floor
from src.step30 import cohiqp as C30
from src.step31 import run as R31

RESULTS = Path("results/step37")
TEST = tuple(range(1230, 1244))
DROP_T, GATE_T = 2.0, 1.0           # spec section 2; read off the spent pilot seeds, not tuned
NEAR_DROP = (1.6, 2.5)              # spec section 3
WORKERS, STOP_LOSS_H = 20, 16.0
CONDS, GIVENS, GRAPHS = ("cf", "pf"), ("full", "miss"), ("full", "miss", "enl")
NB, N_SHOTS = R31.NB, R31.N_SHOTS
data = R31.data


def out_path(c, a, g, s) -> Path:
    return RESULTS / c / f"{a}_{g}" / f"seed_{s}" / "metrics.json"


def gens_for(graph: str, seed: int):
    return ENLARGED if graph == "enl" else given_graph(graph, seed)[0]


def run_job(cond: str, arm: str, graph: str, seed: int) -> dict:
    t0 = time.time()
    p = data(cond, seed)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    F = raw_floor(fhat, N_SHOTS)
    gens = gens_for(graph, seed)
    me = MaxEntModel(NB, 3)
    G = lambda q: M1.completion_gap(q, p, NB)["G"]
    out = {"cond": cond, "arm": arm, "graph": graph, "seed": seed, "N": N_SHOTS, "n_gens": len(gens)}
    out["G_me3"] = G(me.prob(me.fit_moments(fhat, ops).params))
    if arm == "coh":
        log = R31._NitLog(C30.minimize)
        C30.minimize = log
        try:
            m = C30.CohIQP(NB, gens, tied=False).fit(fhat, ops, seed=seed)
        finally:
            C30.minimize = log.fn
        eps = m._split(m.x)[1]
        out["restart_nit"] = log.nit
        out["restarts_at_maxiter"] = int(sum(n >= C30.COH_OPTS["maxiter"] for n in log.nit))
        out["eps_at_bound"] = int(np.sum(np.abs(eps) >= C30.EPS_MAX - 1e-9))
    else:
        m = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
        lam = m.x[m.K:]
        out["lam_median"] = float(np.median(lam))
        out["pinned"] = int(np.sum(lam <= LAM_LO + 1e-9))
    out["G"] = G(m.prob())
    out["ratio"] = m.resid / F
    out["R_me3"] = out["G"] / out["G_me3"]
    out["secs"] = time.time() - t0
    path = out_path(cond, arm, graph, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def flip_jobs():
    return [(c, "flip", g, s) for s in TEST for c in CONDS for g in GRAPHS]


def load(c, a, g, s):
    f = out_path(c, a, g, s)
    return json.loads(f.read_text()) if f.exists() else None


def choose(flip_given: dict, flip_enl: dict, given: str) -> dict:
    """Recipe steps 1-3 (spec section 2) from the two FlipIQP records; returns graph* and pick."""
    drop = flip_given["ratio"] / flip_enl["ratio"]
    graph = "enl" if drop > DROP_T else given
    fl = flip_enl if graph == "enl" else flip_given
    pick = "coh" if fl["ratio"] > GATE_T else "flip"
    return {"drop": drop, "graph": graph, "pick": pick, "ratio_gate": fl["ratio"]}


def recipe(c, given, s):
    """Full recipe record, or None if a needed FlipIQP fit is missing. G_recipe is None if the needed coh fit is."""
    fg, fe = load(c, "flip", given, s), load(c, "flip", "enl", s)
    if fg is None or fe is None:
        return None
    ch = choose(fg, fe, given)
    rec = load(c, ch["pick"], ch["graph"], s)
    ch.update({"G_me3": fg["G_me3"], "G_flip_given": fg["G"], "G_recipe": rec["G"] if rec else None})
    return ch


def needed_coh():
    """Coh fits the recipe needs, given the FlipIQP fits on disk."""
    need = set()
    for s in TEST:
        for c in CONDS:
            for g in GIVENS:
                r = recipe(c, g, s)
                if r and r["pick"] == "coh":
                    need.add((c, "coh", r["graph"], s))
    return sorted(need, key=lambda j: (j[3], j[0], j[2]))


def _kill_tree(pr):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pr.pid)], capture_output=True)


def launch() -> int:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    todo = [j for j in flip_jobs() if not out_path(*j).exists()]
    queued = set(todo)
    t0, running, log = time.time(), [], []
    RESULTS.mkdir(parents=True, exist_ok=True)
    err = open(RESULTS / "errors.log", "a")
    while True:
        for j in needed_coh():                    # eligible coh fits go to the front (spec section 4)
            if j not in queued and not out_path(*j).exists():
                todo.insert(0, j)
                queued.add(j)
                log.append(f"queued {j} {time.time() - t0:.0f}s")
        if not todo and not running:
            break
        if time.time() - t0 > STOP_LOSS_H * 3600:
            for j, pr, _ in running:
                _kill_tree(pr)
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
            pr = subprocess.Popen([sys.executable, "-m", "src.step37.run", "--job", j[0], j[1], j[2], str(j[3])],
                                  env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr, time.time()))
            log.append(f"start {j} {time.time() - t0:.0f}s")
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(10)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log[-5:]))
    return 0


def verdicts() -> dict:
    R = {(c, g, s): recipe(c, g, s) for c in CONDS for g in GIVENS for s in TEST}

    def win(r):          # missing FlipIQP or coh fit -> failure (spec sections 3 and 5)
        return r is not None and r["G_recipe"] is not None and r["G_recipe"] < r["G_me3"]

    a1 = sum(win(R["cf", "miss", s]) for s in TEST)
    a2 = sum(win(R["pf", "miss", s]) for s in TEST)
    a3 = sum(R[c, "miss", s] is not None and R[c, "miss", s]["drop"] > DROP_T for c in CONDS for s in TEST)
    a4 = sum(R[c, "full", s] is not None and R[c, "full", s]["drop"] <= DROP_T for c in CONDS for s in TEST)
    a5 = sum(win(R[c, "full", s]) for c in CONDS for s in TEST)
    out = {}
    for h, w, of, need in (("A1", a1, 14, 11), ("A2", a2, 14, 12), ("A3", a3, 28, 26), ("A4", a4, 28, 24),
                           ("A5", a5, 28, 23)):
        out[h] = {"count": int(w), "of": of, "need": need, "verdict": "PASS" if w >= need else "FAIL"}
    rep = {}
    for c in CONDS:
        for g in GIVENS:
            X = {s: R[c, g, s] for s in TEST if R[c, g, s] is not None}
            Y = {s: r for s, r in X.items() if r["G_recipe"] is not None}
            rep[f"{c}_{g}"] = {
                "n": len(X), "n_with_recipe": len(Y),
                "median_R_recipe": float(np.median([r["G_recipe"] / r["G_me3"] for r in Y.values()])) if Y else None,
                "median_R_flip_given": float(np.median([r["G_flip_given"] / r["G_me3"] for r in X.values()])) if X else None,
                "recipe_beats_flip_given": int(sum(r["G_recipe"] < r["G_flip_given"] for r in Y.values())),
                "picked": {k: int(sum(f"{r['graph']}/{r['pick']}" == k for r in X.values()))
                           for k in sorted({f"{r['graph']}/{r['pick']}" for r in X.values()})},
                "drop_near_threshold": {str(s): r["drop"] for s, r in X.items() if NEAR_DROP[0] <= r["drop"] <= NEAR_DROP[1]},
                "gate_ratio_near_threshold": {str(s): r["ratio_gate"] for s, r in X.items() if 0.8 <= r["ratio_gate"] <= 1.25},
            }
    coh = [load(*j) for j in needed_coh()]
    coh = [d for d in coh if d]
    rep["coh"] = {"n_needed": len(needed_coh()), "n_done": len(coh),
                  "restarts_at_maxiter": int(sum(d["restarts_at_maxiter"] for d in coh)),
                  "eps_at_bound": int(sum(d["eps_at_bound"] for d in coh))}
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 37 summary", "", "| ID | result | verdict |", "|---|---|---|"]
    for h in ("A1", "A2", "A3", "A4", "A5"):
        lines.append(f"| {h} | {V[h]['count']}/{V[h]['of']} (need {V[h]['need']}) | {V[h]['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    rows = ["", "## Per seed (R = G / G_me3)", "",
            "| cond | given | seed | drop | graph* | gate ratio | pick | R_recipe | R_flip_given |", "|---|---|---|---|---|---|---|---|---|"]
    for c in CONDS:
        for g in GIVENS:
            for s in TEST:
                r = recipe(c, g, s)
                if r is None:
                    continue
                Rr = f"{r['G_recipe'] / r['G_me3']:.3f}" if r["G_recipe"] is not None else "missing"
                rows.append(f"| {c} | {g} | {s} | {r['drop']:.2f} | {r['graph']} | {r['ratio_gate']:.2f} | {r['pick']} | "
                            f"{Rr} | {r['G_flip_given'] / r['G_me3']:.3f} |")
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines + rows) + "\n")
    print("\n".join(lines[:9]))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [j for j in flip_jobs() + needed_coh() if not out_path(*j).exists()]
    if miss and "STOP-LOSS" not in txt:
        errs.append(f"{len(miss)} fits missing and no stop-loss recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step37.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step37.py fails:\n" + r.stdout[-800:])
    res = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(res + "\n")
    print(res)
    return 0 if not errs else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--job", nargs=4)
    a = ap.parse_args()
    if a.job:
        run_job(a.job[0], a.job[1], a.job[2], int(a.job[3]))
        sys.exit(0)
    sys.exit(launch() if a.all else report() if a.report else verify() if a.verify else 2)

"""Step 33 (specs/step33_sampling_quality.md on master): full-distribution quality of the fitted models, fresh seeds.

python -m src.step33.run --all | --job COND SEED | --report | --verify
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from math import comb
from pathlib import Path

import numpy as np

from src.step1 import metrics as M1
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step4.run import training_moments
from src.step23 import grid as Gd

RESULTS = Path("results/step33")
TEST = tuple(range(1120, 1134))
SPENT_BELOW = 1114
N_SHOTS = 10_000
SIGMAS = (0.5, 1.0, 2.0)
CONDS = ("xf02", "mg01", "g01", "id")          # launch order: slowest first
WORKERS, STOP_LOSS_H = 14, 16.0               # guess: 14 workers leaves room for another session's run
NB = Gd.N_BITS
HYP_COND = {"id": 1, "g01": 2, "mg01": 3, "xf02": 4}


# ---------------------------------------------------------------- metrics
def walsh(v):
    """f_S = sum_x v(x) (-1)^{popcount(S & x)} for every mask S (fast Walsh-Hadamard transform)."""
    a = np.array(v, float).copy()
    h = 1
    while h < a.size:
        a = a.reshape(-1, 2 * h)
        x, y = a[:, :h].copy(), a[:, h:].copy()
        a[:, :h], a[:, h:] = x + y, x - y
        a = a.reshape(-1)
        h *= 2
    return a


def mmd_from_E(E, n, s):
    """Gaussian-kernel MMD^2 = sum_k C(n,k) a^(n-k) b^k E_k, where E[k-1] is the order-k error."""
    c = np.exp(-1 / (2 * s * s))
    a, b = (1 + c) / 2, (1 - c) / 2
    return float(sum(comb(n, k) * a ** (n - k) * b ** k * E[k - 1] for k in range(1, n + 1)))


def dist_metrics(p, q, n):
    p = np.asarray(p, float)
    q = np.clip(np.asarray(q, float), 1e-300, None)
    q = q / q.sum()
    pop = np.array([bin(m).count("1") for m in range(1 << n)])
    d2 = (walsh(p) - walsh(q)) ** 2
    E = [float(d2[pop == k].mean()) for k in range(1, n + 1)]
    m = p > 0
    out = {"tvd": float(0.5 * np.abs(p - q).sum()),
           "kl": float(np.sum(p[m] * (np.log(p[m]) - np.log(q[m])))),
           "fid": float(np.sum(np.sqrt(p * q)) ** 2),
           "G": float(np.mean(E[3:6])), "G_hi": float(np.mean(E[6:])), "E": E}
    for s in SIGMAS:
        out[f"mmd_{s}"] = mmd_from_E(E, n, s)
    return out


# ---------------------------------------------------------------- data and arms
def data(cond, seed):
    """Target p, IQP candidate set and MaxEnt-on-graph masks, exactly as in the source step."""
    if cond == "id":                                         # step 23
        return Gd.grid_iqp(seed), Gd.LOCAL_GENS, Gd.LOCAL_ME
    if cond in ("g01", "mg01"):                              # steps 26, 27
        from src.step26 import noise as Nz26
        p = Nz26.noisy_grid_iqp(seed, 0.01, 0.02)
        if cond == "g01":
            return p, Gd.LOCAL_GENS, Gd.LOCAL_ME
        from src.step27.run import given_graph
        g, me = given_graph("miss", seed)
        return p, g, me
    if cond == "xf02":                                       # step 29, correct graph
        from src.step29 import noise as Nz29
        from src.step27.run import given_graph
        g, me = given_graph("full", seed)
        return Nz29.coherent_grid_iqp(seed, 0.2, 0.02), g, me
    raise ValueError(cond)


def fit_model(cond, gens, fhat, ops, seed):
    """Returns (q, info). id: local IQP (step 23); g01: FlipIQP (step 26); mg01, xf02: recipe (step 27)."""
    if cond == "id":
        m = IQPModel(NB, gens=gens)
        f = m.fit_moments(fhat, ops, seed=seed, n_restarts=20, init_std=0.3)
        return m.prob(f.params), {}
    from src.step26.flipiqp import FlipIQP
    if cond == "g01":
        return FlipIQP(NB, gens).fit(fhat, ops, seed=seed).prob(), {}
    from src.step25.run import ENLARGED
    from src.step27.run import flow_choice, raw_floor
    mg = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
    ratio = float(mg.resid / raw_floor(fhat, N_SHOTS))
    pick = flow_choice(ratio)
    m = mg if pick == "given" else FlipIQP(NB, ENLARGED).fit(fhat, ops, seed=seed)
    return m.prob(), {"ratio_given": ratio, "alarm": pick == "enl"}


def out_path(c, s) -> Path:
    return RESULTS / c / f"seed_{s}" / "metrics.json"


def jobs():
    return [(c, s) for c in CONDS for s in TEST]


def run_job(cond, seed):
    t0 = time.time()
    p, gens, me_masks = data(cond, seed)
    p = np.asarray(p, float)
    fhat, ops = training_moments(p, N_SHOTS, seed, NB)
    qs = {}
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_graph", Gd.MaxEntOn(NB, me_masks))):
        qs[name] = mdl.prob(mdl.fit_moments(fhat, ops).params)
    qs["model"], info = fit_model(cond, gens, fhat, ops, seed)
    out = {"cond": cond, "seed": seed, **info}
    for k, q in qs.items():
        out[k] = dist_metrics(p, q, NB)
        out[k]["G_check"] = float(M1.completion_gap(np.asarray(q, float), p, NB)["G"])
    out["secs"] = time.time() - t0
    path = out_path(cond, seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path.parent / "dist.npz", p=p, **{k: np.asarray(q, float) for k, q in qs.items()})  # not committed
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
            pr = subprocess.Popen([sys.executable, "-m", "src.step33.run", "--job", j[0], str(j[1])], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr, time.time()))
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(15)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    return 0


# ---------------------------------------------------------------- verdicts
def load(c):
    return {s: json.loads(out_path(c, s).read_text()) for s in TEST if out_path(c, s).exists()}


def count(X, f):
    """Seeds of TEST where f(record) holds; missing seeds count as failures."""
    return sum(1 for s in TEST if s in X and f(X[s]))


def verdicts(loader=load) -> dict:
    out = {}
    for c, i in HYP_COND.items():
        X = loader(c)
        for h, key in ((f"S{i}", "tvd"), (f"S{i + 4}", "kl")):
            w = count(X, lambda d, key=key: d["model"][key] < d["me3"][key])
            out[h] = {"cond": c, "metric": key, "count": w, "of": 14, "need": 11,
                      "verdict": "PASS" if w >= 11 else "FAIL"}
    X = loader("xf02")
    w1 = count(X, lambda d: d["model"]["E"][0] > d["me3"]["E"][0])          # losses, not wins
    w2 = count(X, lambda d: d["model"]["mmd_2.0"] > d["me3"]["mmd_2.0"])
    out["W1"] = {"cond": "xf02", "metric": "E_1 (losses)", "count": w1, "of": 14, "need": 11,
                 "verdict": "PASS" if w1 >= 11 else "FAIL"}
    out["W2"] = {"cond": "xf02", "metric": "mmd_2.0 (losses)", "count": w2, "of": 14, "need": 11,
                 "verdict": "PASS" if w2 >= 11 else "FAIL"}
    rep = {}
    for c in HYP_COND:
        X = loader(c)
        if not X or "fid" not in next(iter(X.values()))["model"]:   # synthetic test records carry no full metrics
            continue
        D = list(X.values())
        r = {"n": len(D)}
        for key in ("G", "G_hi", "tvd", "kl", "fid", "mmd_0.5", "mmd_1.0", "mmd_2.0"):
            better = (lambda a, b: a > b) if key == "fid" else (lambda a, b: a < b)
            for opp in ("me3", "me_graph"):
                r[f"{key}_wins_vs_{opp}"] = int(sum(better(d["model"][key], d[opp][key]) for d in D))
                r[f"{key}_median_ratio_vs_{opp}"] = float(np.median([d["model"][key] / d[opp][key] for d in D]))
            for m in ("model", "me3", "me_graph"):
                r[f"{key}_median_{m}"] = float(np.median([d[m][key] for d in D]))
        r["order_wins_vs_me3"] = [int(sum(d["model"]["E"][k] < d["me3"]["E"][k] for d in D)) for k in range(NB)]
        r["E_median"] = {m: np.median([d[m]["E"] for d in D], axis=0).tolist() for m in ("model", "me3", "me_graph")}
        for m in ("model", "me3"):
            r[f"sample_bound_{m}"] = float(2 * np.log(10) / -np.log(r[f"fid_median_{m}"]))
        if "alarm" in D[0]:
            r["alarms"] = int(sum(d["alarm"] for d in D))
        r["max_G_check_dev"] = float(max(abs(d[m]["G"] / d[m]["G_check"] - 1) for d in D for m in ("model", "me3")))
        rep[c] = r
    out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    lines = ["# Step 33 summary", "", "| ID | cond | metric | count | verdict |", "|---|---|---|---|---|"]
    for h in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "W1", "W2"):
        v = V[h]
        lines.append(f"| {h} | {v['cond']} | {v['metric']} | {v['count']}/14 (need 11) | {v['verdict']} |")
    lines += ["", "## Reported (no verdict)", "", "```", json.dumps(V["reported"], indent=1), "```"]
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:15]))
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
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step33.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step33.py fails:\n" + r.stdout[-800:])
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

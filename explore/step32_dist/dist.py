"""Step 32 exploration: does the high-order moment win carry over to the whole distribution?

Exploration only, on spent seeds (no pre-registered test). For each instance it refits the models
exactly as the registered runs did and compares each model's full distribution q with the exact target p:
  TVD = 0.5 * sum |p - q|,  KL(p||q) = sum p log(p/q)  (KL = held-out cross-entropy minus H(p)).
G (the paper's completion gap) is recomputed as a check that the refit reproduces the registered run.

python -m explore.step32_dist.dist --job COND SEED   |   --all   |   --summary
COND: ideal (step 23 grid_iqp N=1e4), g01 (step 26 FlipIQP), xf02 (step 29 recipe, correct graph, eps=0.2)
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

OUT = Path("explore/step32_dist/out2")   # out/ may hold files from orphaned first-launch workers
NB = Gd.N_BITS
SEEDS = {"ideal": range(920, 934), "g01": range(1000, 1014), "xf02": range(1060, 1074)}
WORKERS = 6


def dist_metrics(q, p):
    q = np.clip(np.asarray(q, float), 1e-300, None)
    q = q / q.sum()
    m = p > 0
    return {"tvd": float(0.5 * np.abs(p - q).sum()),
            "kl": float(np.sum(p[m] * (np.log(p[m]) - np.log(q[m])))),
            "G": float(M1.completion_gap(q, p, NB)["G"])}


def run_job(cond, seed):
    t0 = time.time()
    if cond == "ideal":
        p = Gd.grid_iqp(seed)
        fhat, ops = training_moments(p, 10_000, seed, NB)
        me_masks = Gd.LOCAL_ME
    elif cond == "g01":
        from src.step26 import noise as Nz26
        p = Nz26.noisy_grid_iqp(seed, 0.01, 0.02)
        fhat, ops = training_moments(p, 10_000, seed, NB)
        me_masks = Gd.LOCAL_ME
    else:
        from src.step29 import noise as Nz29
        from src.step27.run import given_graph
        p = Nz29.coherent_grid_iqp(seed, 0.2, 0.02)
        fhat, ops = training_moments(p, 10_000, seed, NB)
        gens, me_masks = given_graph("full", seed)
    p = np.asarray(p, float)
    qs = {}
    for name, mdl in (("me3", MaxEntModel(NB, 3)), ("me_local", Gd.MaxEntOn(NB, me_masks))):
        qs[name] = mdl.prob(mdl.fit_moments(fhat, ops).params)
    if cond == "ideal":
        m = IQPModel(NB, gens=Gd.LOCAL_GENS)
        f = m.fit_moments(fhat, ops, seed=seed, n_restarts=20, init_std=0.3)
        qs["model"] = m.prob(f.params)
    else:
        from src.step26.flipiqp import FlipIQP
        if cond == "g01":
            qs["model"] = FlipIQP(NB, Gd.LOCAL_GENS).fit(fhat, ops, seed=seed).prob()
        else:
            from src.step25.run import ENLARGED
            from src.step27.run import flow_choice, raw_floor
            F = raw_floor(fhat, 10_000)
            mg = FlipIQP(NB, gens).fit(fhat, ops, seed=seed)
            pick = flow_choice(mg.resid / F)
            qs["model"] = (mg if pick == "given" else FlipIQP(NB, ENLARGED).fit(fhat, ops, seed=seed)).prob()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / f"{cond}_{seed}.npz", p=p, **{k: np.asarray(q, float) for k, q in qs.items()})
    out = {"cond": cond, "seed": seed}
    for k, q in qs.items():
        for mk, v in dist_metrics(q, p).items():
            out[f"{mk}_{k}"] = v
    out["secs"] = time.time() - t0
    path = OUT / f"{cond}_{seed}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    return out


def launch():
    todo = [(c, s) for c in SEEDS for s in SEEDS[c] if not (OUT / f"{c}_{s}.npz").exists()]
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    OUT.mkdir(parents=True, exist_ok=True)
    running = []
    while todo or running:
        running = [(j, pr) for j, pr in running if pr.poll() is None]
        while todo and len(running) < WORKERS:
            j = todo.pop(0)
            err = open(OUT / f"{j[0]}_{j[1]}.err", "w")
            pr = subprocess.Popen([sys.executable, "-m", "explore.step32_dist.dist", "--job", j[0], str(j[1])],
                                  env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((j, pr))
        time.sleep(15)
    return 0


def summary():
    reg = {"ideal": ("results/step23/grid_iqp/N_10000", "G_iqp_local"),
           "g01": ("results/step26/g01", "G_flip"), "xf02": ("results/step29/xf02", "G_flow")}
    for c in SEEDS:
        D = [json.loads((OUT / f"{c}_{s}.json").read_text()) for s in SEEDS[c] if (OUT / f"{c}_{s}.json").exists()]
        if not D:
            continue
        print(f"== {c}  n={len(D)}")
        for mk in ("G", "tvd", "kl"):
            row = []
            for opp in ("me3", "me_local"):
                r = [d[f"{mk}_model"] / d[f"{mk}_{opp}"] for d in D]
                row.append(f"vs {opp}: wins {sum(x < 1 for x in r):2d}/{len(D)} median ratio {np.median(r):.3f}")
            med = {k: np.median([d[f'{mk}_{k}'] for d in D]) for k in ("model", "me3", "me_local")}
            print(f"  {mk:4s} " + " | ".join(row) + "   medians " + " ".join(f"{k}={v:.4g}" for k, v in med.items()))
        dev = []
        for d in D:
            reg_dir, key = reg[c]
            f = Path(reg_dir) / f"seed_{d['seed']}" / "metrics.json"
            if f.exists():
                dev.append(abs(d["G_model"] / json.loads(f.read_text())[key] - 1))
        if dev:
            print(f"  refit check: max |G_refit/G_registered - 1| = {max(dev):.3g}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", nargs=2)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    if a.job:
        run_job(a.job[0], int(a.job[1]))
        sys.exit(0)
    sys.exit(launch() if a.all else summary() if a.summary else 2)

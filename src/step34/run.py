"""Step 34 (specs/step34_coherent_replication.md on master): step 29's xf02 job on 28 fresh seeds.

python -m src.step34.run --all | --job SEED | --report | --verify
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

from src.step29 import run as R29   # the job function is step 29's run_job, unchanged (spec section 1)

RESULTS = Path("results/step34")
TEST = tuple(range(1140, 1168))
SPENT_BELOW = 1134
COND = "xf02"
NEED = 19
WORKERS, STOP_LOSS_H = 14, 10.0
STEP33_XF02 = Path("results/step33/xf02")


def jobs():
    return list(TEST)


def out_path(s) -> Path:
    return RESULTS / COND / f"seed_{s}" / "metrics.json"


def run_job(seed: int) -> dict:
    R29.RESULTS = RESULTS          # redirect output only; the computation is step 29's
    return R29.run_job(COND, seed)


def launch() -> int:
    todo = [s for s in jobs() if not out_path(s).exists()]
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t0, running, log = time.time(), [], []
    RESULTS.mkdir(parents=True, exist_ok=True)
    err = open(RESULTS / "errors.log", "a")
    while todo or running:
        if time.time() - t0 > STOP_LOSS_H * 3600:
            for s, pr in running:
                pr.kill()
                log.append(f"KILLED {s}")
            log.append(f"STOP-LOSS after {STOP_LOSS_H} h; unstarted: {todo}")
            break
        still = []
        for s, pr in running:
            if pr.poll() is None:
                still.append((s, pr))
            else:
                log.append(f"done {s} rc={pr.returncode} {time.time() - t0:.0f}s")
        running = still
        while todo and len(running) < WORKERS:
            s = todo.pop(0)
            pr = subprocess.Popen([sys.executable, "-m", "src.step34.run", "--job", str(s)], env=env,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=err)
            running.append((s, pr))
        (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
        time.sleep(15)
    (RESULTS / "run_log.txt").write_text("\n".join(log) + "\n")
    return 0


def load() -> dict:
    return {s: json.loads(out_path(s).read_text()) for s in TEST if out_path(s).exists()}


def sign_p(w: int, n: int) -> float:
    """One-sided sign-test p value, P(X >= w) for X ~ Bin(n, 1/2)."""
    return sum(comb(n, i) for i in range(w, n + 1)) / 2 ** n


def count(X: dict) -> int:
    """Seeds of TEST with a strict win of the recipe; missing seeds count as failures."""
    return sum(1 for s in TEST if s in X and X[s]["G_flow"] < X[s]["G_me3"])


def verdicts(loader=load) -> dict:
    X = loader()
    w = count(X)
    out = {"C1": {"cond": COND, "wins": w, "of": len(TEST), "need": NEED, "p": sign_p(w, len(TEST)),
                  "verdict": "PASS" if w >= NEED else "FAIL"}}
    if X and "R_flow_me3" in next(iter(X.values())):
        R = np.array([d["R_flow_me3"] for d in X.values()])
        rng = np.random.default_rng(0)
        boot = np.median(rng.choice(R, size=(10_000, len(R)), replace=True), axis=1)
        rep = {"n": len(X), "median_R_flow": float(np.median(R)),
               "median_R_flow_ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
               "median_R_given": float(np.median([d["R_given_me3"] for d in X.values()])),
               "median_R_enl": float(np.median([d["R_enl_me3"] for d in X.values()])),
               "alarms": int(sum(d["flag"] for d in X.values()))}
        # pooled, descriptive only: 28 of these seeds were seen before the spec
        w29 = [d["G_flow"] < d["G_me3"] for d in (json.loads(p.read_text())
                                                  for p in sorted(Path("results/step29/xf02").glob("seed_*/metrics.json")))]
        w33 = [d["model"]["G"] < d["me3"]["G"] for d in (json.loads(p.read_text())
                                                        for p in sorted(STEP33_XF02.glob("seed_*/metrics.json")))]
        w34 = [X[s]["G_flow"] < X[s]["G_me3"] for s in TEST if s in X]
        n, k = len(w29) + len(w33) + len(w34), int(sum(w29) + sum(w33) + sum(w34))
        rep["pooled"] = {"step29": [int(sum(w29)), len(w29)], "step33": [int(sum(w33)), len(w33)],
                         "step34": [int(sum(w34)), len(w34)], "wins": k, "of": n, "sign_p": sign_p(k, n)}
        out["reported"] = rep
    return out


def report() -> int:
    V = verdicts()
    (RESULTS / "verdicts.json").write_text(json.dumps(V, indent=1))
    c = V["C1"]
    lines = ["# Step 34 summary", "", f"C1: {c['wins']}/{c['of']} (need {c['need']}), p = {c['p']:.4f}: "
             f"**{c['verdict']}**", "", "## Reported (no verdict)", "", "```",
             json.dumps(V.get("reported", {}), indent=1), "```"]
    (RESULTS / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


def verify() -> int:
    errs = []
    log = RESULTS / "run_log.txt"
    txt = log.read_text() if log.exists() else ""
    miss = [s for s in jobs() if not out_path(s).exists()]
    if miss and "STOP-LOSS" not in txt:
        errs.append(f"{len(miss)} jobs missing and no stop-loss recorded")
    vf = RESULTS / "verdicts.json"
    if not vf.exists() or json.loads(vf.read_text()) != json.loads(json.dumps(verdicts())):
        errs.append("verdicts.json missing or not reproducible from metrics")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_step34.py"], capture_output=True, text=True)
    if r.returncode != 0:
        errs.append("tests/test_step34.py fails:\n" + r.stdout[-800:])
    res = "ALL PASS" if not errs else "FAIL\n" + "\n".join(errs)
    (RESULTS / "verify.txt").write_text(res + "\n")
    print(res)
    return 0 if not errs else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--job", type=int)
    a = ap.parse_args()
    if a.job is not None:
        run_job(a.job)
        sys.exit(0)
    sys.exit(launch() if a.all else report() if a.report else verify() if a.verify else 2)

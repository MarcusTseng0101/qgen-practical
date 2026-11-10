"""Step 14 pilot (before the spec is frozen): how does G's training residual behave at finite N?

Development seeds only (iqp4 seeds 10-13, lcm/ising4 seeds 10-11), n = 16, N in {1e4, 1e5}.
Records the fitted residual r_N, the sampling floor sum_a (1 - fhat_a^2) / N, the residual
against the exact moments, and R. No hypothesis is tested here.

  python -m src.step14.pilot --one FAMILY SEED N
  python -m src.step14.pilot --all
  python -m src.step14.pilot --show
"""
from __future__ import annotations

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
from src.step3.run import fit_restarts
from src.step4.run import training_moments
from src.step4.targets import iqp4_target
from src.step7.run import MATCHED_SIGMA
from src.step12.targets import FAMILIES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "step14" / "pilot"
CAL12 = ROOT / "results" / "step12" / "CALIBRATION.json"
n = 16
JOBS = [(f, s, N) for N in (10_000, 100_000) for f, ss in (("iqp4", (10, 11, 12, 13)), ("lcm", (10, 11)), ("ising4", (10, 11)))
        for s in ss]


def target(fam: str, seed: int) -> np.ndarray:
    if fam == "iqp4":
        return iqp4_target(MATCHED_SIGMA[n]["B"], seed, n)[0]
    beta = json.loads(CAL12.read_text())["beta"][f"{fam}/n_{n}"]["beta"]
    return FAMILIES[fam](beta, seed, n)


def one(fam: str, seed: int, N: int) -> None:
    t0 = time.time()
    p = target(fam, seed)
    fhat, ops = training_moments(p, N, seed, n)
    ftrue, _ = training_moments(p, None, seed, n)
    me = MaxEntModel(n, 3)
    mf = me.fit_moments(fhat, ops)
    G_me = M1.completion_gap(me.prob(mf.params), p, n)["G"]
    model = IQPModel(n)
    r = fit_restarts(model, fhat, ops, seed, p, n, 3)
    b = r["rows"][r["best"]]
    fG = model.moments(b["params"], ops)
    out = {"family": fam, "seed": seed, "N": N, "R": b["G"] / G_me, "G_iqp": b["G"], "G_maxent": G_me,
           "r_N": b["residual"], "floor": float(np.sum(1 - fhat**2) / N), "r_true": float(np.sum((fG - ftrue) ** 2)),
           "noise_true": float(np.sum((fhat - ftrue) ** 2)), "n_ops": len(ops), "seconds": time.time() - t0}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{fam}_s{seed}_N{N}.json").write_text(json.dumps(out, indent=2))


def run_all() -> None:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    ps = [subprocess.Popen([sys.executable, "-m", "src.step14.pilot", "--one", f, str(s), str(N)], cwd=ROOT, env=env)
          for f, s, N in JOBS]
    print("rc", [pr.wait() for pr in ps])


def show() -> None:
    for f in sorted(OUT.glob("*.json")):
        d = json.loads(f.read_text())
        print(f"{d['family']:6s} s{d['seed']} N={d['N']:>6} R={d['R']:8.3g} r_N={d['r_N']:.3g} floor={d['floor']:.3g} "
              f"excess={d['r_N'] - d['floor']:+.3g} r_true={d['r_true']:.3g} noise={d['noise_true']:.3g} "
              f"min={d['seconds'] / 60:.0f}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "--one":
        one(a[1], int(a[2]), int(a[3]))
    elif a[0] == "--all":
        run_all()
    else:
        show()

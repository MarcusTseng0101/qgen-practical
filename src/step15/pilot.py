"""Step 15 pilot (before the spec is frozen): a split-sample gate at finite N.

Development seeds only (iqp4 10-13, lcm/ising4 10-11), n = 16, N in {1e4, 3e4, 1e5}.
Fit G on half A of the samples; score its moments against half B:
    split_excess = ||f_G(A) - fhat_B||^2 - sum_a (1 - fhat_B,a^2) / (N/2)
which estimates G(A)'s distance to the exact moments without the in-sample noise bias.
Also fits G and MaxEnt(3) on all N (the estimator the gate would deploy). No hypothesis is tested.

  python -m src.step15.pilot --one FAMILY SEED N | --all | --show
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
from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.targets import sample_indices
from src.step1.walsh import empirical_distribution, parity_coefficients
from src.step3.run import fit_restarts
from src.step14.pilot import target

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "step15" / "pilot"
n = 16
JOBS = [(f, s, N) for N in (10_000, 30_000, 100_000) for f, ss in (("iqp4", (10, 11, 12, 13)), ("lcm", (10, 11)),
                                                                      ("ising4", (10, 11))) for s in ss]


def one(fam: str, seed: int, N: int) -> None:
    t0 = time.time()
    p = target(fam, seed)
    ops = masks_up_to(n, 3)
    idx = sample_indices(p, N, seed)
    mom = lambda ix: parity_coefficients(empirical_distribution(ix, n))[ops]
    f_all, f_A, f_B = mom(idx), mom(idx[: N // 2]), mom(idx[N // 2:])
    f_true = parity_coefficients(p)[ops]
    me = MaxEntModel(n, 3)
    G_me = M1.completion_gap(me.prob(me.fit_moments(f_all, ops).params), p, n)["G"]
    model = IQPModel(n)
    rA = fit_restarts(model, f_A, ops, seed, p, n, 3); bA = rA["rows"][rA["best"]]
    fGA = model.moments(bA["params"], ops)
    floor_B = float(np.sum(1 - f_B**2) / (N - N // 2))
    rF = fit_restarts(model, f_all, ops, seed, p, n, 3); bF = rF["rows"][rF["best"]]
    floor_all = float(np.sum(1 - f_all**2) / N)
    out = {"family": fam, "seed": seed, "N": N, "R_full": bF["G"] / G_me, "R_A": bA["G"] / G_me,
           "split_excess": float(np.sum((fGA - f_B) ** 2)) - floor_B, "r_AB": float(np.sum((fGA - f_B) ** 2)),
           "floor_B": floor_B, "r_true_A": float(np.sum((fGA - f_true) ** 2)),
           "insample_excess_full": bF["residual"] - floor_all, "seconds": time.time() - t0}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{fam}_s{seed}_N{N}.json").write_text(json.dumps(out, indent=2))


def run_all() -> None:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    todo, running, rc = list(JOBS), [], []
    while todo or running:
        while todo and len(running) < 16:
            f, s, N = todo.pop(0)
            running.append(subprocess.Popen([sys.executable, "-m", "src.step15.pilot", "--one", f, str(s), str(N)],
                                            cwd=ROOT, env=env))
        time.sleep(5)
        for pr in [pr for pr in running if pr.poll() is not None]:
            running.remove(pr); rc.append(pr.returncode)
    print("rc", rc)


def show() -> None:
    for f in sorted(OUT.glob("*.json"), key=lambda q: (json.loads(q.read_text())["N"], q.name)):
        d = json.loads(f.read_text())
        print(f"{d['family']:6s} s{d['seed']} N={d['N']:>6} R_full={d['R_full']:7.3g} R_A={d['R_A']:7.3g} "
              f"split_ex={d['split_excess']:+.3g} r_true_A={d['r_true_A']:.3g} insample_ex={d['insample_excess_full']:+.3g} "
              f"min={d['seconds'] / 60:.0f}")


if __name__ == "__main__":
    a = sys.argv[1:]
    {"--one": lambda: one(a[1], int(a[2]), int(a[3])), "--all": run_all, "--show": show}[a[0]]()

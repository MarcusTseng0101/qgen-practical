"""Step 17 pilot (before any spec): MNIST-16 through the step 14 gate.

Development splits only (split seeds 10, 11). A split is a permutation of the 70 000 rows from
default_rng(2000 + seed): the first N_TRAIN rows train, the rest test. No exact target exists, so
completion is scored against the test rows' order-4..6 moments, with the test sampling noise
removed per level:

  G_corr = mean_l mean_{|A|=l} [ (f_A(model) - fhat_A(test))^2 - (1 - fhat_A(test)^2) / N_test ]

R = G_corr(IQP) / G_corr(MaxEnt3). The gate is step 14's, unchanged, on the training moments.

  python -m src.step17.pilot --one SEED
  python -m src.step17.pilot --all
  python -m src.step17.pilot --show
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1.bits import masks_up_to
from src.step1.metrics import LEVELS
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import coefficients_by_order, empirical_distribution, parity_coefficients
from src.step2.sweep import kl
from src.step3.run import fit_restarts
from src.step13.gate import TAU
from src.step14.run import excess, floor_of
from src.step17 import data as D

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "step17" / "pilot"
n = D.n
N_TRAIN = 30_000
SEEDS = (10, 11)


def corrected_gap(q_model, q_test, N_test) -> dict:
    fm = coefficients_by_order(q_model, n, LEVELS)
    ft = coefficients_by_order(q_test, n, LEVELS)
    per = {int(l): float(np.mean((fm[l] - ft[l]) ** 2 - (1 - ft[l] ** 2) / N_test)) for l in LEVELS}
    raw = {int(l): float(np.mean((fm[l] - ft[l]) ** 2)) for l in LEVELS}
    return {"G": float(np.mean(list(per.values()))), "per_level": per, "G_raw": float(np.mean(list(raw.values())))}


def fit_split(seed: int) -> dict:
    t0 = time.time()
    idx = D.indices(D.bits())[np.random.default_rng(2000 + seed).permutation(70_000)]
    tr, te = idx[:N_TRAIN], idx[N_TRAIN:]
    q_tr, q_te = empirical_distribution(tr, n), empirical_distribution(te, n)
    ops = masks_up_to(n, 3)
    fhat = parity_coefficients(q_tr)[ops]
    me = MaxEntModel(n, 3)
    mf = me.fit_moments(fhat, ops)
    q_me = me.prob(mf.params)
    g_me = corrected_gap(q_me, q_te, len(te))
    model = IQPModel(n)
    r = fit_restarts(model, fhat, ops, seed, q_te, n, 3)
    b = r["rows"][r["best"]]
    g_iqp = corrected_gap(model.prob(b["params"]), q_te, len(te))
    fl = floor_of(fhat, N_TRAIN)
    ex = excess(b["residual"], fl)
    out = {"seed": seed, "N_train": N_TRAIN, "N_test": len(te), "R": g_iqp["G"] / g_me["G"],
           "G_iqp": g_iqp, "G_maxent": g_me, "r_N": b["residual"], "floor": fl, "excess": ex,
           "gate_picks_iqp": bool(ex <= TAU), "D3_train": kl(q_tr, q_me),
           "maxent_train_residual": mf.train_residual, "restart_residuals": [x["residual"] for x in r["rows"]],
           "n_restarts": len(r["rows"]), "data_sha256": D.fetch(), "seconds": time.time() - t0}
    return out


def one(seed: int) -> None:
    out = fit_split(seed)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"mnist16_s{seed}.json").write_text(json.dumps(out, indent=2))


def run_all() -> None:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    ps = [subprocess.Popen([sys.executable, "-m", "src.step17.pilot", "--one", str(s)], cwd=ROOT, env=env) for s in SEEDS]
    print("rc", [p.wait() for p in ps])


def show() -> None:
    for f in sorted(OUT.glob("*.json")):
        d = json.loads(f.read_text())
        print(f"s{d['seed']} R={d['R']:.3g} G_iqp={d['G_iqp']['G']:.3g} G_me={d['G_maxent']['G']:.3g} "
              f"(raw {d['G_iqp']['G_raw']:.3g}/{d['G_maxent']['G_raw']:.3g}) r_N={d['r_N']:.3g} floor={d['floor']:.3g} "
              f"excess={d['excess']:+.3g} picks={d['gate_picks_iqp']} D3={d['D3_train']:.3g} min={d['seconds'] / 60:.0f}")


if __name__ == "__main__":
    a = sys.argv[1:]
    {"--one": lambda: one(int(a[1])), "--all": run_all}.get(a[0], show)()

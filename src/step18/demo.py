"""Step 18: an adversarial family the gate cannot see (identifiability demo, not a hypothesis test).

The gate sees only order-<=3 moments. For an IQP-like target p, let m = MaxEnt3(p) (same order-<=3
moments) and q_lam = lam * p + (1 - lam) * m. Every q_lam has p's order-<=3 moments, so the fits of
G and MaxEnt(3), the training residual and the gate decision are identical for all lam. Only the
order-4..6 truth moves. With d = f_p - f_m and e = f_G - f_m on the order-4..6 parities (per-level
means as in M1.completion_gap):

  G_iqp(lam) = mean (e - lam d)^2,   G_maxent(lam) = lam^2 mean d^2,
  R(lam) = 1  at  lam* = mean(e^2) / (2 mean(e d)).

For lam < lam* the gate picks G (same as at lam = 1) and G loses. Development seeds 10-13 of
`iqp4`, n = 16, exact moments (N = inf).

  python -m src.step18.demo --one SEED | --all | --show
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from src.step1.metrics import LEVELS
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import coefficients_by_order
from src.step3.run import fit_restarts
from src.step4.run import training_moments
from src.step13.gate import TAU
from src.step14.pilot import target

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "step18"
n = 16
SEEDS = (10, 11, 12, 13)
LAMS = (0.0, 0.25, 0.5, 0.75, 1.0)


def lvl_mean(x: dict) -> float:
    return float(np.mean([np.mean(x[l]) for l in LEVELS]))


def one(seed: int) -> None:
    t0 = time.time()
    p = target("iqp4", seed)
    f, ops = training_moments(p, None, seed, n)
    me = MaxEntModel(n, 3)
    m = me.prob(me.fit_moments(f, ops).params)
    model = IQPModel(n)
    r = fit_restarts(model, f, ops, seed, p, n, 3)
    b = r["rows"][r["best"]]
    g = model.prob(b["params"])
    Fp, Fm, Fg = (coefficients_by_order(x, n, LEVELS) for x in (p, m, g))
    d = {l: Fp[l] - Fm[l] for l in LEVELS}; e = {l: Fg[l] - Fm[l] for l in LEVELS}
    ee = lvl_mean({l: e[l] ** 2 for l in LEVELS}); ed = lvl_mean({l: e[l] * d[l] for l in LEVELS})
    dd = lvl_mean({l: d[l] ** 2 for l in LEVELS})
    rows = []
    for lam in LAMS:
        q = lam * p + (1 - lam) * m
        fq, _ = training_moments(q, None, seed, n)
        Gi = lvl_mean({l: (e[l] - lam * d[l]) ** 2 for l in LEVELS}); Gm = lam**2 * dd
        rows.append({"lam": lam, "max_lowmoment_diff": float(np.abs(fq - f).max()), "G_iqp": Gi, "G_maxent": Gm,
                     "R": Gi / Gm if Gm > 0 else float("inf")})
    out = {"seed": seed, "residual": b["residual"], "gate_picks": bool(b["residual"] <= TAU),
           "maxent_moment_err": float(np.abs(training_moments(m, None, seed, n)[0] - f).max()),
           "lam_star": ee / (2 * ed) if ed > 0 else None, "R_at_1": rows[-1]["R"], "rows": rows,
           "seconds": time.time() - t0}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"iqp4_s{seed}.json").write_text(json.dumps(out, indent=2))


def run_all() -> None:
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    ps = [subprocess.Popen([sys.executable, "-m", "src.step18.demo", "--one", str(s)], cwd=ROOT, env=env) for s in SEEDS]
    print("rc", [p.wait() for p in ps])


def show() -> None:
    for f in sorted(OUT.glob("iqp4_s*.json")):
        d = json.loads(f.read_text())
        ls = d["lam_star"]
        print(f"s{d['seed']} resid={d['residual']:.2g} picks={d['gate_picks']} maxent_err={d['maxent_moment_err']:.1e} "
              f"lam*={'none' if ls is None else f'{ls:.3f}'} "
              + " ".join(f"R({r['lam']})={r['R']:.3g}[dlow={r['max_lowmoment_diff']:.0e}]" for r in d["rows"]))


if __name__ == "__main__":
    a = sys.argv[1:]
    {"--one": lambda: one(int(a[1])), "--all": run_all}.get(a[0], show)()

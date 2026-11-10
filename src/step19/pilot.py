"""Step 19 pilot: one development run (bX, centre 3_5) of the QEC detection-event data through the step 14 gate.

Same scoring as step 17: train on the first N_TRAIN shots of a permutation (default_rng(2000 + seed)), score
order-4..6 completion on the other shots with test noise removed. The other 7 runs are held back for the spec.

  python -m src.step19.pilot --one RUN SEED | --show
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import coefficients_by_order, empirical_distribution, parity_coefficients
from src.step2.sweep import kl
from src.step3.run import fit_restarts
from src.step13.gate import TAU
from src.step14.run import excess, floor_of
from src.step17.pilot import corrected_gap
from src.step19 import data as D

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "step19" / "pilot"
n = D.n
N_TRAIN = 30_000
DEV_RUN = D.RUNS[0]


def fit_run(run: str, seed: int) -> dict:
    t0 = time.time()
    idx = D.indices(D.bits(run))[np.random.default_rng(2000 + seed).permutation(D.SHOTS)]
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
    q_g = model.prob(b["params"])
    t4 = coefficients_by_order(q_tr, n, (4,))[4]
    val4 = lambda q: float(np.mean((coefficients_by_order(q, n, (4,))[4] - t4) ** 2 - (1 - t4**2) / N_TRAIN))
    fl = floor_of(fhat, N_TRAIN)
    ex = excess(b["residual"], fl)
    return {"run": run, "seed": seed, "N_train": N_TRAIN, "N_test": len(te), "R": g_iqp["G"] / g_me["G"],
            "R_raw": g_iqp["G_raw"] / g_me["G_raw"], "val4_iqp": val4(q_g), "val4_maxent": val4(q_me),
            "G_iqp": g_iqp, "G_maxent": g_me, "r_N": b["residual"], "floor": fl, "excess": ex,
            "gate_picks_iqp": bool(ex <= TAU), "D3_train": kl(q_tr, q_me), "maxent_train_residual": mf.train_residual,
            "restart_residuals": [x["residual"] for x in r["rows"]], "n_restarts": len(r["rows"]),
            "zip_md5": D.zip_md5(), "seconds": time.time() - t0}


def show() -> None:
    for f in sorted(OUT.glob("*.json")):
        d = json.loads(f.read_text())
        print(f"{d['run']} s{d['seed']} R={d['R']:.3g} G_iqp={d['G_iqp']['G']:.3g} G_me={d['G_maxent']['G']:.3g} "
              f"lv_iqp={ {k: round(v, 6) for k, v in d['G_iqp']['per_level'].items()} } "
              f"lv_me={ {k: round(v, 6) for k, v in d['G_maxent']['per_level'].items()} } r_N={d['r_N']:.3g} "
              f"floor={d['floor']:.3g} excess={d['excess']:+.3g} picks={d['gate_picks_iqp']} D3={d['D3_train']:.3g} "
              f"min={d['seconds'] / 60:.0f}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--one":
        out = fit_run(a[1], int(a[2]))
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{a[1]}_s{a[2]}.json").write_text(json.dumps(out, indent=2))
    else:
        show()

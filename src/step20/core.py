"""Step 20 core: the step 14 gate plus a held-out order-4 validation check.

The training shots are split into a fit part (first FIT_FRAC) and a validation part (the rest). MaxEnt(3)
and G (3 restarts) are fit to the fit part's order-<=3 moments only. The validation check compares each
model's order-l parities with the validation rows', with validation noise removed:

    v_l(q) = mean_{|A| = l} [(f_q(A) - f_val(A))^2 - (1 - f_val(A)^2) / N_val]

The validation rows never enter a fit, so this cannot reward over-fitting the fit sample (the step 19
train-row check did; notes/2026-11-11_step19_qec_findings.md).
"""
from __future__ import annotations

import time

import numpy as np

from src.step1.bits import masks_up_to
from src.step1.models.iqp import IQPModel
from src.step1.models.maxent import MaxEntModel
from src.step1.walsh import coefficients_by_order, empirical_distribution, parity_coefficients
from src.step2.sweep import kl
from src.step3.run import fit_restarts
from src.step13.gate import TAU
from src.step14.run import excess, floor_of

FIT_FRAC = 0.8
VAL_LEVELS = (4, 5, 6)
RESTARTS = 3


def val_gap(q, fv: dict, N_val: int, n: int) -> dict:
    fm = coefficients_by_order(q, n, VAL_LEVELS)
    return {int(l): float(np.mean((fm[l] - fv[l]) ** 2 - (1 - fv[l] ** 2) / N_val)) for l in VAL_LEVELS}


def fit_and_gate(train_idx: np.ndarray, n: int, seed: int, q_ref) -> dict:
    """Fit on the first FIT_FRAC of train_idx, validate on the rest. G of each restart is against q_ref."""
    t0 = time.time()
    n_fit = int(round(FIT_FRAC * len(train_idx)))
    fit_idx, val_idx = train_idx[:n_fit], train_idx[n_fit:]
    q_fit, q_val = empirical_distribution(fit_idx, n), empirical_distribution(val_idx, n)
    ops = masks_up_to(n, 3)
    fhat = parity_coefficients(q_fit)[ops]
    me = MaxEntModel(n, 3)
    mf = me.fit_moments(fhat, ops)
    q_me = me.prob(mf.params)
    model = IQPModel(n)
    r = fit_restarts(model, fhat, ops, seed, q_ref, n, RESTARTS)
    b = r["rows"][r["best"]]
    q_g = model.prob(b["params"])
    fv = coefficients_by_order(q_val, n, VAL_LEVELS)
    v_g, v_me = val_gap(q_g, fv, len(val_idx), n), val_gap(q_me, fv, len(val_idx), n)
    fl = floor_of(fhat, n_fit)
    ex = excess(b["residual"], fl)
    picks14 = bool(ex <= TAU)
    return {"N_fit": n_fit, "N_val": len(val_idx), "q_g": q_g, "q_me": q_me,
            "r_N": b["residual"], "floor": fl, "excess": ex, "picks14": picks14,
            "val_iqp": v_g, "val_maxent": v_me,
            "picks_val4": bool(picks14 and v_g[4] < v_me[4]),
            "D3_fit": kl(q_fit, q_me), "maxent_train_residual": mf.train_residual,
            "restart_residuals": [x["residual"] for x in r["rows"]], "n_restarts": len(r["rows"]),
            "G_rows_ref": [x["G"] for x in r["rows"]], "best": r["best"], "fit_seconds": time.time() - t0}

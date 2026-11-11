"""Classical XOR (independent-mechanism) model, the third arm of step 22.

Mechanism e (a bit mask) fires independently with probability p_e = (1 - exp(-w_e)) / 2, w_e >= 0; the
observed bits are the XOR of the fired masks. Parities: f(A) = exp(-sum_e [|e & A| odd] w_e).
Mechanisms are masks_up_to(n, 3): the IQP's own generator set, so the parameter count matches (696 at n = 16).
No circuit knowledge (e.g. Google's detector error model) is used.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize, nnls

from src.step1.bits import masks_up_to, popcount

CLIP = 1e-3  # guess: floor on f-hat before the log in the NNLS initialisation
LBFGS = {"maxiter": 20000, "maxfun": 40000, "ftol": 1e-16, "gtol": 1e-13, "maxcor": 20}  # as the IQP fit


def odd_matrix(ops, mechs) -> np.ndarray:
    return (popcount(np.asarray(ops, np.int64)[:, None] & np.asarray(mechs, np.int64)[None, :]) & 1).astype(float)


def parities(w, ops, mechs) -> np.ndarray:
    return np.exp(-odd_matrix(ops, mechs) @ np.asarray(w, float))


def prob(w, mechs, n: int) -> np.ndarray:
    """Exact distribution: sequential XOR convolutions."""
    idx = np.arange(2**n)
    p = np.zeros(2**n)
    p[0] = 1.0
    for m, wi in zip(np.asarray(mechs, np.int64), np.asarray(w, float)):
        q = (1.0 - np.exp(-wi)) / 2.0
        if q > 0:
            p = (1.0 - q) * p + q * p[idx ^ m]
    return p


def fit(fhat, ops, mechs) -> dict:
    """min sum_a (f(a) - fhat_a)^2 over w >= 0 (L-BFGS-B), initialised by NNLS on -log(max(fhat, CLIP))."""
    fhat = np.asarray(fhat, float)
    M = odd_matrix(ops, mechs)
    w0, _ = nnls(M, -np.log(np.maximum(fhat, CLIP)), maxiter=50 * M.shape[1])

    def lg(w):
        f = np.exp(-M @ w)
        r = f - fhat
        return float(r @ r), -M.T @ (2.0 * r * f)

    res = minimize(lg, w0, jac=True, method="L-BFGS-B", bounds=[(0, None)] * len(w0), options=LBFGS)
    return {"w": res.x, "residual": float(lg(res.x)[0]), "nit": int(res.nit), "message": str(res.message),
            "n_nonpos": int(np.sum(fhat <= 0))}


def fit_to(q: np.ndarray, n: int) -> dict:
    """XOR model fitted to an exact distribution's order-<=3 parities (for the non-XOR component I(q))."""
    from src.step1.walsh import parity_coefficients
    ops = masks_up_to(n, 3)
    return fit(parity_coefficients(q)[ops], ops, ops)

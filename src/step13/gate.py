"""Residual-gated estimator (specs/step13_residual_gate.md): uses training moments only."""
from __future__ import annotations

import math

import numpy as np

TAU = 1e-2   # frozen; chosen on seeds 10-29 (step 10 note)


def gated_ratio(R, resid, tau: float = TAU) -> np.ndarray:
    """R where the IQP's training residual is <= tau (inclusive), else exactly 1 (fallback to MaxEnt(3))."""
    R, resid = np.asarray(R, dtype=float), np.asarray(resid, dtype=float)
    return np.where(resid <= tau, R, 1.0)


def outcomes(R, resid, tau: float = TAU) -> dict:
    """wins (R_gate < 1), losses (picked and R >= 1), ties (fallback)."""
    resid = np.asarray(resid, dtype=float)
    picked = resid <= tau
    R = np.asarray(R, dtype=float)
    wins = int((picked & (R < 1)).sum())
    losses = int((picked & (R >= 1)).sum())
    return {"picked": int(picked.sum()), "wins": wins, "losses": losses, "ties": int((~picked).sum())}


def sign_p(wins: int, losses: int) -> float:
    """One-sided P(X >= wins), X ~ Bin(wins + losses, 1/2); 1.0 if no non-tied instance."""
    m = wins + losses
    if m == 0:
        return 1.0
    return sum(math.comb(m, k) for k in range(wins, m + 1)) / 2**m

"""Step 5 targets (specs/step5_iqp4_sigma_scan.md): iqp4 (unchanged from step 4) and iqp4f.

- iqp4(sigma, s): src/step4/targets.iqp4_target, imported unchanged.
- iqp4f(sigma, s, tau = 0.2): the same generators and the same z, z'. The weight-<=3 angles are
  sigma * z (as in iqp4); the 6 weight-4 angles are fixed at tau * z' (tau = 0.2), independent
  of sigma. The arithmetic is the same as iqp4_target with the weight-4 scale replaced by tau,
  so iqp4f(0.2, s) == iqp4(0.2, s) bit for bit (tested).

src/step1..4 are imported, never edited.
"""
from __future__ import annotations

import numpy as np

from src.step1.bits import subset_mask
from src.step1.targets import iqp_distribution
from src.step2.sweep import sigma_target
from src.step4.targets import N_BITS, iqp4_layout, iqp4_target

TAU = 0.2   # spec: the fixed weight-4 scale of iqp4f


def iqp4f_target(sigma: float, seed: int, n: int = N_BITS, tau: float = TAU):
    """(p, masks, theta, layout): iqp(sigma, seed)'s generators then the 6 weight-4 ones at tau*z'."""
    _, masks3, theta3, _, layout3 = sigma_target(sigma, seed, n)
    supports, z4 = iqp4_layout(seed, n)
    masks = np.concatenate([masks3, np.array([subset_mask(g) for g in supports], dtype=np.int64)])
    theta = np.concatenate([theta3, tau * z4])
    p = iqp_distribution(n, masks, theta)
    return p / p.sum(), masks, theta, list(layout3) + supports


__all__ = ["TAU", "iqp4_target", "iqp4f_target"]

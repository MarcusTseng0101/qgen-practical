"""The interface every step-1 model implements (so a new model is one file in models/).

A model is constructed with the number of bits n and exposes:
- name: str, used as the key in metrics.json;
- n_params: int;
- fit_moments(fhat, ops, seed) -> FitResult: fit to the target parity coefficients
  fhat[i] = f_{ops[i]} (ops are subset masks, see bits.py), minimizing or matching
  L = sum_i (f_{ops[i]}(model) - fhat[i])^2;
- prob(params=None) -> length-2^n probability vector (params=None: the fitted ones).

metrics.py never imports this package; it only sees the probability vectors and angle
arrays that run.py passes it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FitResult:
    params: np.ndarray
    train_residual: float               # sum over ops of (f_model - fhat)^2 at params
    restart_residuals: list = field(default_factory=list)
    trace: list = field(default_factory=list)  # residual per optimizer iteration, best restart
    nit: int = 0
    message: str = ""
